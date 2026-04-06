from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class AskRequest(BaseModel):
    """Схема входящего запроса для вопроса к ИИ"""
    question: str = Field(..., description="Текст вопроса пользователя", example="Какие правила отпуска в компании?")
    conversation_id: str = Field(default="default", description="ID сессии для сохранения контекста диалога")

class AskResponse(BaseModel):
    """Схема ответа от ИИ"""
    question: str
    answer: str
    sources: List[str] = Field(default_factory=list, description="Список документов, откуда взята информация")
    conversation_id: str

class DocumentUploadResponse(BaseModel):
    """Схема ответа при загрузке документа"""
    message: str
    filename: str
    chunks_count: int = 0

class HealthResponse(BaseModel):
    """Схема ответа для проверки статуса API"""
    status: str
    version: str


class DocumentInfo(BaseModel):
    filename: str
    chunks: int = 0


class DocumentsListResponse(BaseModel):
    total_chunks: int = 0
    documents: List[DocumentInfo] = Field(default_factory=list)


class DeleteDocumentResponse(BaseModel):
    filename: str
    deleted_chunks: int = 0


class ConversationMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ConversationsListResponse(BaseModel):
    conversations: List[str] = Field(default_factory=list)


class ConversationHistoryResponse(BaseModel):
    conversation_id: str
    messages: List[ConversationMessage] = Field(default_factory=list)


class DeleteConversationResponse(BaseModel):
    conversation_id: str
    deleted: bool