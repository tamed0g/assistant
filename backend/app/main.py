import logging
import os
from typing import List
from urllib.parse import unquote
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi import FastAPI, UploadFile, File, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import (
    AskRequest,
    AskResponse,
    DocumentUploadResponse,
    HealthResponse,
    DocumentsListResponse,
    DeleteDocumentResponse,
    ConversationsListResponse,
    ConversationHistoryResponse,
    DeleteConversationResponse,
)
from app.services.document_service import extract_text, split_into_chunks
from app.services.vector_service import add_texts, list_documents, delete_document
from app.services.rag_chain import (
    ask_with_rag,
    list_conversation_ids,
    get_conversation_history,
    delete_conversation,
)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Enterprise Assistant",
    description="Production-ready Backend for AI Assistant with context retrieval",
    version="1.0.0",
)

# Настройка CORS для работы с Railway и локальным React-фронтендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Проверка доступности API (Health Check)"""
    return HealthResponse(status="healthy", version="1.0.0")

@app.post("/upload", response_model=DocumentUploadResponse, tags=["Documents"])
async def upload_document(file: UploadFile = File(...)):
    """Загрузка и векторизация документа в базу знаний"""
    filename = file.filename.lower()
    
    #проверка формата
    if not filename.endswith((".txt", ".pdf", ".md")):
        logger.warning(f"Attempted to upload unsupported file type: {filename}")
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Unsupported file format. Please use .txt, .pdf, or .md"
        )

    try:
        logger.info(f"Starting processing for file: {filename}")
        content = await file.read()
        
        # Извлечение и чанкинг
        text = extract_text(content, file.filename)
        if not text or not text.strip():
            raise ValueError("File is empty or text could not be extracted.")

        chunks = split_into_chunks(text)
        
        # Сохранение в векторную БД (Qdrant)
        add_texts(chunks, file.filename)

        logger.info(f"Successfully processed {filename} into {len(chunks)} chunks.")
        
        return DocumentUploadResponse(
            message="Document processed and stored successfully",
            filename=file.filename,
            chunks_count=len(chunks)
        )
        
    except ValueError as ve:
        logger.error(f"Validation error for {filename}: {str(ve)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(ve))
    except Exception as e:
        logger.error(f"Internal error processing {filename}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="An error occurred while processing the document."
        )


@app.get("/documents", response_model=DocumentsListResponse, tags=["Documents"])
async def get_documents():
    """Список загруженных документов (по данным из Qdrant)."""
    data = list_documents()
    return DocumentsListResponse(**data)


@app.delete("/documents/{filename}", response_model=DeleteDocumentResponse, tags=["Documents"])
async def remove_document(filename: str):
    """Удалить документ (все чанки) из векторной базы."""
    safe_name = unquote(filename)
    try:
        deleted = delete_document(safe_name)
        return DeleteDocumentResponse(filename=safe_name, deleted_chunks=deleted)
    except Exception as e:
        logger.error(f"Failed to delete document {safe_name}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}",
        )

@app.post("/ask", response_model=AskResponse, tags=["AI Chat"])
async def ask_question(request: AskRequest):
    """
    Основной эндпоинт для генерации ответа. 
    Принимает JSON с вопросом и ID сессии.
    """
    logger.info(f"Received question in session '{request.conversation_id}': {request.question}")
    
    try:
        # Вызов RAG пайплайна
        result = await ask_with_rag(request.question, conversation_id=request.conversation_id)
        
        return AskResponse(
            question=request.question,
            answer=result.get("answer", "I couldn't generate an answer."),
            sources=result.get("sources", []),
            conversation_id=request.conversation_id,
        )
    except Exception as e:
        logger.error(f"Error generating answer for session {request.conversation_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail="AI Generation service is currently unavailable."
        )


@app.get("/conversations", response_model=ConversationsListResponse, tags=["AI Chat"])
async def get_conversations():
    """Список сохранённых диалогов (in-memory)."""
    return ConversationsListResponse(conversations=list_conversation_ids())


@app.get("/conversations/{conversation_id}", response_model=ConversationHistoryResponse, tags=["AI Chat"])
async def get_conversation(conversation_id: str):
    """История конкретного диалога."""
    conv = unquote(conversation_id)
    msgs = get_conversation_history(conv)
    return ConversationHistoryResponse(conversation_id=conv, messages=msgs)


@app.delete("/conversations/{conversation_id}", response_model=DeleteConversationResponse, tags=["AI Chat"])
async def remove_conversation(conversation_id: str):
    """Удалить диалог целиком."""
    conv = unquote(conversation_id)
    deleted = delete_conversation(conv)
    return DeleteConversationResponse(conversation_id=conv, deleted=deleted)
    
# ==========================================
# Раздача фронтенда (React SPA)
# ==========================================
if os.path.exists("static"):
    # Монтируем assets только если они реально существуют (защита от краша)
    if os.path.exists("static/assets"):
        app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_react_app(full_path: str):
        # Если путь пустой (корень сайта)
        if not full_path or full_path == "/":
            return FileResponse("static/index.html")
            
        file_path = os.path.join("static", full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
            
        # Во всех остальных случаях (для React Router) отдаем index.html
        return FileResponse("static/index.html")
else:
    logger.warning("Папка 'static' не найдена. UI не будет отображаться.")