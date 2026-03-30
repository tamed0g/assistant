from pydantic import BaseModel, Field
from typing import List, Optional

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