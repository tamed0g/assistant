import httpx
import os


async def ask_llm(prompt: str) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    model = os.getenv(
        "OPENROUTER_MODEL",
        "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"
    )

    if not api_key:
        return "Ошибка: OPENROUTER_API_KEY не задан"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1000,
                "temperature": 0.1,
            },
            timeout=120.0,
        )

    data = resp.json()

    # Если ошибка от OpenRouter
    if "error" in data:
        return f"OpenRouter ошибка: {data['error']}"

    # Если нет choices
    if "choices" not in data:
        return f"Неожиданный ответ: {str(data)[:500]}"

    return data["choices"][0]["message"]["content"]