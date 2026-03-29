from app.services.llm_service import ask_llm
from app.services.vector_service import search

conversations = {}


def get_conversation(conv_id):
    if conv_id not in conversations:
        conversations[conv_id] = []
    return conversations[conv_id]


def add_to_conversation(conv_id, role, content):
    if conv_id not in conversations:
        conversations[conv_id] = []
    conversations[conv_id].append({"role": role, "content": content})
    if len(conversations[conv_id]) > 20:
        conversations[conv_id] = conversations[conv_id][-20:]


def clear_conversation(conv_id):
    conversations[conv_id] = []


def list_conversations():
    return list(conversations.keys())


def _format_history(history):
    if not history:
        return ""
    recent = history[-6:]
    lines = ["Предыдущий разговор:"]
    for msg in recent:
        role = "Пользователь" if msg["role"] == "user" else "Ассистент"
        lines.append(f"{role}: {msg['content'][:300]}")
    return "\n".join(lines)


async def ask_with_rag(question, conversation_id=None):
    history = []
    if conversation_id:
        history = get_conversation(conversation_id)
    history_block = _format_history(history)

    # Пробуем найти в документах
    try:
        results = search(question, top_k=5)
    except Exception:
        results = []

    # Определяем: есть ли релевантные документы?
    has_relevant_docs = len(results) > 0 and results[0]["score"] > 0.5
    has_some_docs = len(results) > 0 and results[0]["score"] > 0.3

    if has_relevant_docs:
        # === СЦЕНАРИЙ 1: Ответ ТОЧНО есть в документах ===
        context_parts = []
        sources = []
        for r in results:
            context_parts.append(f"[Из файла '{r['source']}']:\n{r['text']}")
            sources.append({"file": r["source"], "score": r["score"]})
        context = "\n\n---\n\n".join(context_parts)

        prompt = f"""Ты — умный корпоративный ассистент.

ПРАВИЛА:
1. У тебя есть контекст из загруженных документов — используй его.
2. Если ответ есть в документах — отвечай по ним и указывай файл.
3. Если в документах есть ЧАСТИЧНЫЙ ответ — дай его и дополни своими знаниями.
4. Отвечай на русском языке, кратко и по делу.

Формат ответа:
- Информация из документов: начни с 📄
- Дополнение из общих знаний: начни с 💡

Контекст из документов:
{context}

{history_block}

Вопрос: {question}

Ответ:"""
        answer_type = "documents"

    elif has_some_docs:
        # === СЦЕНАРИЙ 2: Документы ЧАСТИЧНО связаны ===
        context_parts = []
        sources = []
        for r in results:
            context_parts.append(f"[Из файла '{r['source']}']:\n{r['text']}")
            sources.append({"file": r["source"], "score": r["score"]})
        context = "\n\n---\n\n".join(context_parts)

        prompt = f"""Ты — умный ассистент.

ПРАВИЛА:
1. У тебя есть контекст из документов — но он может быть НЕ связан с вопросом.
2. Если вопрос связан с документами — используй их и укажи файл.
3. Если вопрос НЕ связан с документами — отвечай из своих общих знаний.
4. Чётко разделяй: что из документов (📄), а что из знаний (💡).
5. Отвечай на русском языке.

Контекст из документов (может быть не связан с вопросом):
{context}

{history_block}

Вопрос: {question}

Ответ:"""
        answer_type = "mixed"

    else:
        # === СЦЕНАРИЙ 3: Документы НЕ найдены или НЕ связаны ===
        sources = []

        prompt = f"""Ты — умный и дружелюбный ассистент.

Отвечай на любые вопросы из своих общих знаний.
Начни ответ с 💡 чтобы показать что это из общих знаний.
Отвечай на русском языке, подробно и интересно.
Если пользователь спрашивает о документах — напомни что можно загрузить файлы.

{history_block}

Вопрос: {question}

Ответ:"""
        answer_type = "general"

    answer = await ask_llm(prompt)

    if conversation_id:
        add_to_conversation(conversation_id, "user", question)
        add_to_conversation(conversation_id, "assistant", answer)

    return {"answer": answer, "sources": sources, "answer_type": answer_type}