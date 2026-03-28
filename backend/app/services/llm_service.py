"""
LLM через OpenRouter — лёгкая версия без langchain-openai.
"""
import httpx
import os


async def ask_llm(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json={
                "model": os.getenv(
                    "OPENROUTER_MODEL",
                    "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"
                ),
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 5000,
                "temperature": 0.1,
            },
            timeout=120.0,
        )

    data = resp.json()
    return data["choices"][0]["message"]["content"]