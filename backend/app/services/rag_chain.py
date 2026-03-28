"""
RAG Chain — лёгкая версия без тяжёлого LangChain.
"""
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


async def ask_with_rag(question: str, conversation_id: str = None) -> dict:
    history = []
    if conversation_id:
        history = get_conversation(conversation_id)

    history_block = _format_history(history)

    try:
        results = search(question, top_k=5)
    except Exception:
        results = []

    has_docs = len(results) > 0 and results[0]["score"] > 0.3

    if has_docs:
        context_parts = []
        sources = []
        for r in results:
            context_parts.append(f"[Из файла '{r['source']}']:\n{r['text']}")
            sources.append({"file": r["source"], "score": r["score"]})

        context = "\n\n---\n\n".join(context_parts)

        prompt = f"""Ты — полезный корпоративный ассистент.
Отвечай на вопрос на основе контекста из документов.
Если в контексте нет ответа — скажи об этом.
Указывай из какого файла взята информация.
Отвечай на русском языке.

Контекст из документов:
{context}

{history_block}

Вопрос: {question}

Ответ:"""
        answer_type = "documents"

    else:
        sources = []
        prompt = f"""Ты — умный ассистент.
Отвечай на вопросы из своих знаний.
Отвечай на русском языке.

{history_block}

Вопрос: {question}

Ответ:"""
        answer_type = "general"

    answer = await ask_llm(prompt)

    if conversation_id:
        add_to_conversation(conversation_id, "user", question)
        add_to_conversation(conversation_id, "assistant", answer)

    return {
        "answer": answer,
        "sources": sources,
        "answer_type": answer_type,
    }