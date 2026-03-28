"""
Эмбеддинги через HuggingFace Inference API.
Бесплатно, без ключа, без регистрации.
Поддерживает русский язык.
"""

from langchain_core.embeddings import Embeddings
import httpx
from typing import List


class HuggingFaceAPIEmbeddings(Embeddings):
    """
    Бесплатные эмбеддинги через HuggingFace API.
    Не нужен API ключ!
    Модель: sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
    Поддерживает русский язык.
    """

    def __init__(self):
        self.api_url = (
            "https://api-inference.huggingface.co/pipeline/feature-extraction/"
            "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        )

    def _embed(self, texts: List[str]) -> List[List[float]]:
        """Отправляет тексты в HuggingFace API"""
        response = httpx.post(
            self.api_url,
            json={"inputs": texts, "options": {"wait_for_model": True}},
            timeout=120.0,
        )

        if response.status_code != 200:
            raise Exception(
                f"HuggingFace API error: {response.status_code} {response.text[:200]}"
            )

        return response.json()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Эмбеддинги для документов (батчами)"""
        all_embeddings = []
        batch_size = 20

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            embeddings = self._embed(batch)
            all_embeddings.extend(embeddings)

        return all_embeddings

    def embed_query(self, text: str) -> List[float]:
        """Эмбеддинг для одного запроса"""
        result = self._embed([text])
        return result[0]


def get_embedding_model():
    return HuggingFaceAPIEmbeddings()