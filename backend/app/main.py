"""
Главный файл — API эндпоинты.
Версия 0.4: память разговора, удаление документов, русские эмбеддинги.
"""

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import traceback

app = FastAPI(title="RAG Assistant", version="0.4.0")

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
        "version": "0.4.0",
        "llm": "OpenRouter",
        "model": os.getenv("OPENROUTER_MODEL", "dolphin-mistral"),
        "embeddings": "multilingual-MiniLM-L12-v2 (русский)",
    }


# ==========================================
# Загрузка документов
# ==========================================

@app.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    """Загрузка документа"""
    filename = file.filename.lower()
    if not filename.endswith((".txt", ".pdf", ".md")):
        return {"status": "error", "detail": "Поддерживаются: .txt, .pdf, .md"}

    content = await file.read()

    try:
        from app.services.document_service import extract_text, split_into_chunks
        from app.services.vector_service import add_texts_to_store

        text = extract_text(content, file.filename)
        if not text.strip():
            return {"status": "error", "detail": "Файл пустой"}

        chunks = split_into_chunks(text)
        add_texts_to_store(chunks, {"filename": file.filename})

        return {
            "status": "ok",
            "filename": file.filename,
            "chunks": len(chunks),
            "message": f"'{file.filename}' загружен! {len(chunks)} фрагментов.",
        }

    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.get("/documents")
async def list_documents():
    """Список загруженных документов"""
    try:
        from app.services.vector_service import get_qdrant_client
        client = get_qdrant_client()

        collections = [c.name for c in client.get_collections().collections]
        if "documents" not in collections:
            return {"documents": [], "total_chunks": 0}

        info = client.get_collection("documents")
        total = info.points_count

        points = client.scroll(
            collection_name="documents",
            limit=1000,
            with_payload=True,
        )[0]

        files = {}
        for p in points:
            meta = p.payload.get("metadata", {})
            source = meta.get("source", p.payload.get("source", "unknown"))
            files[source] = files.get(source, 0) + 1

        return {
            "total_chunks": total,
            "documents": [
                {"filename": name, "chunks": count}
                for name, count in files.items()
            ],
        }

    except Exception as e:
        return {"documents": [], "error": str(e)}


@app.delete("/documents/{filename}")
async def delete_document(filename: str):
    """
    Удаление документа по имени.
    Пример: DELETE /documents/company_info.txt
    """
    try:
        from app.services.vector_service import delete_document as del_doc
        count = del_doc(filename)

        if count == 0:
            return {"status": "error", "detail": f"Документ '{filename}' не найден"}

        return {
            "status": "ok",
            "message": f"Документ '{filename}' удалён ({count} фрагментов)",
        }

    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.delete("/documents")
async def delete_all_documents():
    """Удаление ВСЕХ документов"""
    try:
        from app.services.vector_service import reset_collection
        reset_collection()
        return {"status": "ok", "message": "Все документы удалены"}

    except Exception as e:
        return {"status": "error", "detail": str(e)}


# ==========================================
# Чат с памятью
# ==========================================

@app.post("/ask")
async def ask_question(
    question: str = Form(...),
    conversation_id: str = Form(default="default"),
):
    """Гибридный RAG с памятью"""
    try:
        from app.services.rag_chain import ask_with_rag
        result = ask_with_rag(question, conversation_id=conversation_id)
        return {
            "question": question,
            "answer": result["answer"],
            "sources": result["sources"],
            "answer_type": result.get("answer_type", "unknown"),
            "conversation_id": conversation_id,
        }
    except Exception as e:
        return {
            "question": question,
            "answer": f"Ошибка: {str(e)}",
            "sources": [],
            "trace": traceback.format_exc(),
        }

@app.get("/conversations")
async def list_conversations():
    """Список активных разговоров"""
    from app.services.rag_chain import list_conversations as list_conv
    return {"conversations": list_conv()}


@app.delete("/conversations/{conv_id}")
async def clear_conversation(conv_id: str):
    """Очистить историю разговора"""
    from app.services.rag_chain import clear_conversation as clear_conv
    clear_conv(conv_id)
    return {"status": "ok", "message": f"История разговора '{conv_id}' очищена"}


# ==========================================
# Тесты
# ==========================================

@app.get("/test-llm")
async def test_llm():
    """Проверка LLM"""
    try:
        from app.services.llm_service import get_llm
        llm = get_llm()
        response = llm.invoke("Скажи привет одним предложением по-русски")
        return {
            "status": "ok",
            "model": os.getenv("OPENROUTER_MODEL"),
            "answer": response.content,
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@app.get("/test-embeddings")
async def test_embeddings():
    """Проверка эмбеддингов — показывает что русская модель работает лучше"""
    try:
        from app.services.embedding_service import get_embedding_model
        model = get_embedding_model()

        # Генерируем эмбеддинг
        vector = model.embed_query("Кто директор компании?")

        return {
            "status": "ok",
            "model": "multilingual-MiniLM-L12-v2",
            "vector_size": len(vector),
            "first_5_values": [round(v, 4) for v in vector[:5]],
        }
    except Exception as e:
        return {"status": "error", "detail": str(e)}