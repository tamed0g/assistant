import os
import uuid
import logging
from typing import List, Dict, Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue,
    FilterSelector,
    PayloadSchemaType,
)
from app.services.embedding_service import embed_query, embed_documents

logger = logging.getLogger(__name__)

QDRANT_URL = os.getenv("QDRANT_URL", None)
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
COLLECTION = "documents"


def get_client() -> QdrantClient:
    """Инициализация клиента Qdrant."""
    if QDRANT_URL:
        return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    return QdrantClient(host=QDRANT_HOST, port=6333)


def ensure_collection(client: QdrantClient) -> None:
    """Проверка и создание коллекции в векторной БД."""
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION not in collections:
        logger.info(f"Collection '{COLLECTION}' not found. Creating it.")
        test_vec = embed_query("test")
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=len(test_vec), distance=Distance.COSINE),
        )
    _ensure_payload_indexes(client)


def _ensure_payload_indexes(client: QdrantClient) -> None:
    try:
        info = client.get_collection(COLLECTION)
        payload_schema = getattr(info, "payload_schema", None) or {}
        source_schema = payload_schema.get("source")
        if source_schema and getattr(source_schema, "data_type", None) == PayloadSchemaType.KEYWORD:
            return
    except Exception:
        pass

    try:
        logger.info("Ensuring Qdrant payload index for key 'source' (keyword).")
        client.create_payload_index(
            collection_name=COLLECTION,
            field_name="source",
            field_schema=PayloadSchemaType.KEYWORD,
        )
    except Exception as e:
        logger.warning(f"Could not create payload index for 'source': {str(e)}")


def add_texts(chunks: List[str], filename: str) -> None:
    """Векторизация текста и загрузка в Qdrant."""
    logger.info(f"Adding {len(chunks)} chunks to Qdrant from {filename}")
    
    client = get_client()
    ensure_collection(client)

    try:
        embeddings = embed_documents(chunks)

        points = []
        for i, (chunk, emb) in enumerate(zip(chunks, embeddings)):
            points.append(PointStruct(
                id=str(uuid.uuid4()),
                vector=emb,
                payload={
                    "text": chunk,
                    "source": filename,
                    "chunk_index": i,
                },
            ))

        client.upsert(collection_name=COLLECTION, points=points)
        logger.info(f"Successfully upserted {len(points)} points into Qdrant.")
        
    except Exception as e:
        logger.error(f"Failed to upsert embeddings for {filename}: {str(e)}", exc_info=True)
        raise RuntimeError(f"Vector DB upsert failed: {str(e)}")


def search(question: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """Поиск по семантическому сходству (Similarity Search)."""
    client = get_client()
    ensure_collection(client)

    try:
        query_vector = embed_query(question)

        results = client.search(
            collection_name=COLLECTION,
            query_vector=query_vector,
            limit=top_k,
        )

        return [
            {
                "text": r.payload.get("text", ""),
                "source": r.payload.get("source", "unknown"),
                "score": round(r.score, 3),
            }
            for r in results
        ]
        
    except Exception as e:
        logger.error(f"Failed to perform vector search for query: '{question}'", exc_info=True)
        return []


def delete_document(filename: str) -> int:
    """Удаление всех чанков, связанных с конкретным файлом."""
    logger.info(f"Attempting to delete document: {filename}")
    client = get_client()
    ensure_collection(client)

    try:
        scroll_filter = Filter(must=[
            FieldCondition(key="source", match=MatchValue(value=filename))
        ])
        
        # Получаем данные через scroll (возвращает кортеж)
        points, _ = client.scroll(
            collection_name=COLLECTION,
            scroll_filter=scroll_filter,
            limit=1000,
            with_payload=False,
        )

        count = len(points)
        if count == 0:
            logger.info(f"No points found for document: {filename}")
            return 0

        client.delete(
            collection_name=COLLECTION,
            points_selector=FilterSelector(filter=scroll_filter),
        )
        logger.info(f"Successfully deleted {count} points for document: {filename}")
        return count
        
    except Exception as e:
        logger.error(f"Error deleting document {filename} from Qdrant: {str(e)}", exc_info=True)
        raise RuntimeError(f"Vector DB delete failed: {str(e)}")


def reset_collection() -> None:
    """Полный сброс векторной базы (Drop Collection)."""
    logger.warning("Resetting the entire vector database collection.")
    client = get_client()
    
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION in collections:
        client.delete_collection(COLLECTION)
        
    ensure_collection(client)


def list_documents() -> Dict[str, Any]:
    """Получение списка загруженных документов."""
    client = get_client()
    collections = [c.name for c in client.get_collections().collections]
    
    if COLLECTION not in collections:
        return {"documents": [], "total_chunks": 0}

    try:
        info = client.get_collection(COLLECTION)
        total = info.points_count

        points, _ = client.scroll(
            collection_name=COLLECTION,
            limit=1000,
            with_payload=["source"],
        )

        files = {}
        for p in points:
            source = p.payload.get("source", "unknown")
            files[source] = files.get(source, 0) + 1

        return {
            "total_chunks": total,
            "documents": [
                {"filename": name, "chunks": count}
                for name, count in files.items()
            ],
        }
        
    except Exception as e:
        logger.error(f"Error listing documents: {str(e)}", exc_info=True)
        return {"documents": [], "total_chunks": 0}