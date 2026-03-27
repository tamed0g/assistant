"""
RAG Chain с ПАМЯТЬЮ разговора.

Было:   каждый вопрос отдельно, ассистент не помнит контекст
Стало:  ассистент помнит последние 10 сообщений

Как работает память:
    Пользователь: "Кто директор?"
    Ассистент: "Алексей Смирнов"
    Пользователь: "А какая у него должность?"
                   ↑ без памяти ассистент не поймёт кто "у него"
                   ↑ с памятью — знает что речь о Смирнове
"""

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from app.services.llm_service import get_llm
from app.services.vector_service import search_similar


# ==========================================
# Хранилище разговоров (в памяти)
# ==========================================

# Словарь: {conversation_id: [сообщения]}
# В продакшене это хранится в Redis или PostgreSQL
conversations = {}


def get_conversation(conv_id: str) -> list[dict]:
    """Получить историю разговора"""
    if conv_id not in conversations:
        conversations[conv_id] = []
    return conversations[conv_id]


def add_to_conversation(conv_id: str, role: str, content: str):
    """
    Добавить сообщение в историю.
    role: "user" или "assistant"
    content: текст сообщения
    """
    if conv_id not in conversations:
        conversations[conv_id] = []

    conversations[conv_id].append({
        "role": role,
        "content": content,
    })

    # Храним максимум 20 сообщений (10 пар вопрос-ответ)
    if len(conversations[conv_id]) > 20:
        conversations[conv_id] = conversations[conv_id][-20:]


def clear_conversation(conv_id: str):
    """Очистить историю разговора"""
    conversations[conv_id] = []


def list_conversations() -> list[str]:
    """Список всех разговоров"""
    return list(conversations.keys())


# ==========================================
# Промпт с памятью
# ==========================================

PROMPT_WITH_DOCS = """Ты — умный корпоративный ассистент.

ПРАВИЛА:
1. У тебя есть контекст из загруженных документов — используй его В ПЕРВУЮ ОЧЕРЕДЬ.
2. Если ответ есть в документах — отвечай по ним и указывай из какого файла.
3. Если в документах есть ЧАСТИЧНЫЙ ответ — дай его и дополни своими знаниями.
   При этом чётко разделяй: что из документов, а что из общих знаний.
4. Если вопрос вообще НЕ связан с документами (например "Какая погода?" или "Что такое Python?")
   — отвечай из своих знаний, но упомяни что это не из документов.
5. Отвечай на русском языке, кратко и по делу.

Формат ответа:
- Если из документов: начни с 📄 и укажи файл
- Если из общих знаний: начни с 💡
- Если смешанный ответ: используй оба значка

Контекст из документов:
{context}

{history_block}

Вопрос пользователя: {question}

Ответ:"""

# Промпт когда документов НЕТ ВООБЩЕ (ничего не загружено)
PROMPT_NO_DOCS = """Ты — умный ассистент.

У пользователя пока не загружены документы.
Отвечай на вопросы из своих общих знаний.
Напоминай что можно загрузить документы для более точных ответов.
Отвечай на русском языке.

{history_block}

Вопрос пользователя: {question}

Ответ:"""


def _format_history(history: list[dict]) -> str:
    """Форматирует историю разговора для промпта"""
    if not history:
        return ""

    recent = history[-6:]
    lines = ["Предыдущий разговор:"]
    for msg in recent:
        role = "Пользователь" if msg["role"] == "user" else "Ассистент"
        content = msg["content"][:300]
        lines.append(f"{role}: {content}")

    return "\n".join(lines)


# ==========================================
# Определяем релевантность
# ==========================================

def _is_relevant(results, threshold: float = 0.3) -> bool:
    """
    Проверяет нашлось ли что-то действительно похожее.

    score > 0.5 = очень похоже (ответ точно в документах)
    score 0.3-0.5 = может быть связано
    score < 0.3 = не связано с документами

    threshold = 0.3 — минимальный порог
    """
    if not results:
        return False

    best_score = max(float(score) for _, score in results)
    return best_score >= threshold


# ==========================================
# Главная функция
# ==========================================

def ask_with_rag(question: str, conversation_id: str = None) -> dict:
    """
    Гибридный RAG:
    - Есть документы + вопрос по теме → ответ из документов
    - Есть документы + вопрос не по теме → ответ из знаний
    - Нет документов → ответ из знаний + напоминание загрузить
    """

    # Получаем историю
    history = []
    if conversation_id:
        history = get_conversation(conversation_id)

    history_block = _format_history(history)

    # Пробуем найти в документах
    try:
        results = search_similar(question, top_k=5)
    except Exception:
        results = []

    llm = get_llm()
    parser = StrOutputParser()

    # Определяем сценарий
    has_relevant_docs = _is_relevant(results)

    if has_relevant_docs:
        # === СЦЕНАРИЙ 1: Нашли релевантные документы ===
        context_parts = []
        sources = []

        for doc, score in results:
            source = doc.metadata.get("source", "unknown")
            context_parts.append(
                f"[Из файла '{source}', релевантность {float(score):.0%}]:\n{doc.page_content}"
            )
            sources.append({
                "file": source,
                "score": round(float(score), 3),
            })

        context = "\n\n---\n\n".join(context_parts)

        prompt = ChatPromptTemplate.from_template(PROMPT_WITH_DOCS)
        chain = prompt | llm | parser

        answer = chain.invoke({
            "question": question,
            "context": context,
            "history_block": history_block,
        })

        answer_type = "documents"

    elif results:
        # === СЦЕНАРИЙ 2: Документы есть но не по теме ===
        context_parts = []
        sources = []

        for doc, score in results:
            source = doc.metadata.get("source", "unknown")
            context_parts.append(
                f"[Из файла '{source}', релевантность {float(score):.0%}]:\n{doc.page_content}"
            )
            sources.append({
                "file": source,
                "score": round(float(score), 3),
            })

        context = "\n\n---\n\n".join(context_parts)

        prompt = ChatPromptTemplate.from_template(PROMPT_WITH_DOCS)
        chain = prompt | llm | parser

        answer = chain.invoke({
            "question": question,
            "context": context,
            "history_block": history_block,
        })

        answer_type = "mixed"

    else:
        # === СЦЕНАРИЙ 3: Документов вообще нет ===
        sources = []

        prompt = ChatPromptTemplate.from_template(PROMPT_NO_DOCS)
        chain = prompt | llm | parser

        answer = chain.invoke({
            "question": question,
            "history_block": history_block,
        })

        answer_type = "general"

    # Сохраняем в историю
    if conversation_id:
        add_to_conversation(conversation_id, "user", question)
        add_to_conversation(conversation_id, "assistant", answer)

    return {
        "answer": answer,
        "sources": sources,
        "answer_type": answer_type,
    }