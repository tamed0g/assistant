"""
Сервис Qdrant — работает и локально, и в облаке.
Определяет режим по переменным окружения.
"""

from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams,
    Filter, FieldCondition, MatchValue,
)
from app.services.embedding_service import get_embedding_model
import os

# Настройки Qdrant
QDRANT_URL = os.getenv("QDRANT_URL", None)          # для облака
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)   # для облака
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")     # для локалки
COLLECTION = "documents"

_embedding_model = None


def _get_embeddings():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = get_embedding_model()
    return _embedding_model


def get_qdrant_client():
    """
    Подключение к Qdrant.
    Если есть QDRANT_URL — подключаемся к облаку.
    Если нет — к локальному Docker.
    """
    if QDRANT_URL:
        return QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
        )
    else:
        return QdrantClient(host=QDRANT_HOST, port=6333)


def get_vector_store():
    client = get_qdrant_client()
    embeddings = _get_embeddings()

    collections = [c.name for c in client.get_collections().collections]

    if COLLECTION not in collections:
        test_vector = embeddings.embed_query("тест")
        vector_size = len(test_vector)

        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE,
            ),
        )

    if QDRANT_URL:
        return QdrantVectorStore(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
            collection_name=COLLECTION,
            embedding=embeddings,
        )
    else:
        return QdrantVectorStore(
            client=client,
            collection_name=COLLECTION,
            embedding=embeddings,
        )


def add_texts_to_store(chunks: list[str], metadata: dict):
    store = get_vector_store()
    metadatas = []
    for i in range(len(chunks)):
        metadatas.append({
            "source": metadata.get("filename", "unknown"),
            "chunk_index": i,
            "total_chunks": len(chunks),
        })
    store.add_texts(texts=chunks, metadatas=metadatas)


def search_similar(question: str, top_k: int = 5):
    store = get_vector_store()
    results = store.similarity_search_with_score(question, k=top_k)
    return results


def delete_document(filename: str) -> int:
    client = get_qdrant_client()
    points = client.scroll(
        collection_name=COLLECTION,
        scroll_filter=Filter(
            must=[
                FieldCondition(
                    key="metadata.source",
                    match=MatchValue(value=filename),
                )
            ]
        ),
        limit=1000,
        with_payload=False,
    )[0]

    count = len(points)
    if count == 0:
        return 0

    client.delete(
        collection_name=COLLECTION,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="metadata.source",
                    match=MatchValue(value=filename),
                )
            ]
        ),
    )
    return count


def reset_collection():
    client = get_qdrant_client()
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION in collections:
        client.delete_collection(COLLECTION)
    get_vector_store()