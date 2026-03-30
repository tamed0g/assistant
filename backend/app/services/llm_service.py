import os
import logging
import httpx

logger = logging.getLogger(__name__)

async def ask_llm(prompt: str) -> str:
    """
    Отправляет промпт к LLM через OpenRouter API.
    """
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    model = os.getenv(
        "OPENROUTER_MODEL", 
        "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"
    )

    if not api_key:
        logger.error("OPENROUTER_API_KEY is not set in environment variables.")
        raise ValueError("OPENROUTER_API_KEY is missing")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
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
            resp.raise_for_status()
            data = resp.json()

            if "error" in data:
                logger.error(f"OpenRouter API Error: {data['error']}")
                raise RuntimeError(f"LLM API Error: {data['error']}")

            if "choices" not in data or not data["choices"]:
                logger.error(f"Unexpected LLM response format: {data}")
                raise RuntimeError("Invalid response from LLM provider")

            return data["choices"][0]["message"]["content"]
            
    except httpx.HTTPError as e:
        logger.error(f"HTTP Exception for LLM request: {str(e)}")
        raise RuntimeError(f"Failed to communicate with LLM provider: {str(e)}")