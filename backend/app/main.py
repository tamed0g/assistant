from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import traceback

app = FastAPI(title="RAG Assistant", version="0.5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.get("/")
async def root():
    return FileResponse("app/static/index.html")


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "0.5.0",
        "llm": "OpenRouter",
        "embeddings": "HuggingFace API (multilingual)",
    }


@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    filename = file.filename.lower()
    if not filename.endswith((".txt", ".pdf", ".md")):
        return {"status": "error", "detail": "Поддерживаются: .txt, .pdf, .md"}

    content = await file.read()

    try:
        from app.services.document_service import extract_text, split_into_chunks
        from app.services.vector_service import add_texts

        text = extract_text(content, file.filename)
        if not text.strip():
            return {"status": "error", "detail": "Файл пустой"}

        chunks = split_into_chunks(text)
        add_texts(chunks, file.filename)

        return {
            "status": "ok",
            "filename": file.filename,
            "chunks": len(chunks),
            "message": f"'{file.filename}' загружен! {len(chunks)} фрагментов.",
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.get("/documents")
async def get_documents():
    try:
        from app.services.vector_service import list_documents
        return list_documents()
    except Exception as e:
        return {"documents": [], "error": str(e)}


@app.delete("/documents/{filename}")
async def delete_doc(filename: str):
    try:
        from app.services.vector_service import delete_document
        count = delete_document(filename)
        if count == 0:
            return {"status": "error", "detail": f"'{filename}' не найден"}
        return {"status": "ok", "message": f"'{filename}' удалён ({count} фрагментов)"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.delete("/documents")
async def delete_all():
    try:
        from app.services.vector_service import reset_collection
        reset_collection()
        return {"status": "ok", "message": "Все документы удалены"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.post("/ask")
async def ask_question(
    question: str = Form(...),
    conversation_id: str = Form(default="default"),
):
    try:
        from app.services.rag_chain import ask_with_rag
        result = await ask_with_rag(question, conversation_id=conversation_id)
        return {
            "question": question,
            "answer": result["answer"],
            "sources": result["sources"],
            "answer_type": result.get("answer_type", "general"),
            "conversation_id": conversation_id,
        }
    except Exception as e:
        return {
            "question": question,
            "answer": f"Ошибка: {str(e)}",
            "sources": [],
            "answer_type": "general",
            "trace": traceback.format_exc(),
        }


@app.get("/test-llm")
async def test_llm():
    try:
        from app.services.llm_service import ask_llm
        answer = await ask_llm("Скажи привет одним предложением по-русски")
        return {"status": "ok", "answer": answer}
    except Exception as e:
        return {"status": "error", "detail": str(e)}