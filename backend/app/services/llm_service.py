"""
Сервис для работы с LLM через OpenRouter.

OpenRouter — это "прокси" к разным моделям.
Его API совместим с OpenAI, поэтому мы используем
LangChain модуль ChatOpenAI, но указываем адрес OpenRouter.

Без LangChain:
    resp = await httpx.post("https://openrouter.ai/api/v1/...", json={...})
    answer = resp.json()["choices"][0]["message"]["content"]

С LangChain:
    llm = ChatOpenAI(...)
    answer = llm.invoke("Привет")

Плюс: легко сменить на любую другую модель одной строкой.
"""

from langchain_openai import ChatOpenAI
import os


def get_llm():
    """
    Создаёт объект LLM через OpenRouter.

    ChatOpenAI работает с любым OpenAI-совместимым API.
    Мы просто меняем base_url на OpenRouter.
    """
    return ChatOpenAI(
        # Адрес OpenRouter (вместо api.openai.com)
        base_url="https://openrouter.ai/api/v1",

        # Наш API ключ
        api_key=os.getenv("OPENROUTER_API_KEY"),

        # Какая модель
        model=os.getenv(
            "OPENROUTER_MODEL",
            "cognitivecomputations/dolphin-mistral-24b-venice-edition:free"
        ),

        # Температура: 0 = точный, 1 = творческий
        temperature=0.1,

        # Максимум токенов в ответе
        max_tokens=1000,
    )