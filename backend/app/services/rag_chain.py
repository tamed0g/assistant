import logging
from typing import Dict, Any, List, Optional

from app.services.llm_service import ask_llm
from app.services.vector_service import search

logger = logging.getLogger(__name__)

# In-memory хранилище сессий (в проде заменяется на Redis)
conversations: Dict[str, List[Dict[str, str]]] = {}

def get_conversation(conv_id: str) -> List[Dict[str, str]]:
    if conv_id not in conversations:
        conversations[conv_id] = []
    return conversations[conv_id]

def add_to_conversation(conv_id: str, role: str, content: str) -> None:
    if conv_id not in conversations:
        conversations[conv_id] = []
        
    conversations[conv_id].append({"role": role, "content": content})
    
    # Сохраняем только последние 20 сообщений, чтобы не переполнить контекст (Sliding Window)
    if len(conversations[conv_id]) > 20:
        conversations[conv_id] = conversations[conv_id][-20:]

def format_history(history: List[Dict[str, str]]) -> str:
    if not history:
        return ""
    
    recent = history[-6:]
    lines = ["Предыдущий разговор:"]
    for msg in recent:
        role = "Пользователь" if msg["role"] == "user" else "Ассистент"
        lines.append(f"{role}: {msg['content'][:300]}")
    return "\n".join(lines)

async def ask_with_rag(question: str, conversation_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Основной пайплайн RAG: Поиск контекста + Генерация ответа.
    """
    logger.info(f"Processing RAG request. Session: {conversation_id}")
    
    history = get_conversation(conversation_id) if conversation_id else []
    history_block = format_history(history)

    # 1. Поиск в векторной БД (Retrieval)
    try:
        results = search(question, top_k=5)
        logger.info(f"Retrieved {len(results)} context chunks from Qdrant.")
    except Exception as e:
        logger.error(f"Vector search failed: {str(e)}", exc_info=True)
        results = []

    # 2. Оценка релевантности документов
    has_relevant_docs = len(results) > 0 and results[0].get("score", 0) > 0.5
    has_some_docs = len(results) > 0 and results[0].get("score", 0) > 0.3

    context_parts = []
    sources = []
    
    for r in results:
        context_parts.append(f"[Из файла '{r['source']}']:\n{r['text']}")
        sources.append({"file": r["source"], "score": r["score"]})
        
    context_text = "\n\n---\n\n".join(context_parts) if context_parts else ""

    # 3. Динамическая генерация промпта (Augmentation)
    if has_relevant_docs:
        logger.info("Strategy: High relevance documents found (Exact match).")
        prompt = f"""Ты — умный корпоративный ассистент.

ПРАВИЛА:
1. Используй контекст из документов ниже.
2. Если ответ есть в документах — отвечай по ним и указывай файл (используй эмодзи 📄).
3. Если документы дают частичный ответ — дополни своими знаниями (эмодзи 💡).
4. Отвечай профессионально и по делу.

Контекст из документов:
{context_text}

{history_block}

Вопрос: {question}
Ответ:"""
        answer_type = "documents"

    elif has_some_docs:
        logger.info("Strategy: Low relevance documents found (Mixed match).")
        prompt = f"""Ты — умный корпоративный ассистент.

ПРАВИЛА:
1. Контекст ниже может быть лишь частично связан с вопросом.
2. Если связан — используй его (эмодзи 📄).
3. Если не связан — опирайся на свои общие знания (эмодзи 💡).

Контекст:
{context_text}

{history_block}

Вопрос: {question}
Ответ:"""
        answer_type = "mixed"

    else:
        logger.info("Strategy: No relevant documents. Using general knowledge fallback.")
        prompt = f"""Ты — дружелюбный ИИ-ассистент.

Отвечай на вопрос из своих общих знаний. Начни ответ с 💡.
Если пользователь спрашивает корпоративные данные, напомни, что можно загрузить файлы.

{history_block}

Вопрос: {question}
Ответ:"""
        answer_type = "general"

    # 4. Вызов LLM (Generation)
    try:
        answer = await ask_llm(prompt)
    except Exception as e:
        logger.error(f"LLM Generation failed: {str(e)}")
        answer = "Извините, сервис генерации ответов временно недоступен. Попробуйте позже."

    # 5. Обновление памяти (Memory Update)
    if conversation_id and "Извините, сервис" not in answer:
        add_to_conversation(conversation_id, "user", question)
        add_to_conversation(conversation_id, "assistant", answer)

    return {
        "answer": answer,
        "sources": sources,
        "answer_type": answer_type
    }