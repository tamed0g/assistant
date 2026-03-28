"""
Qdrant — лёгкая версия через qdrant-client напрямую.
"""
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue,
)
from app.services.embedding_service import embed_query, embed_documents
import os
import uuid

QDRANT_URL = os.getenv("QDRANT_URL", None)
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
COLLECTION = "documents"


def get_client():
    if QDRANT_URL:
        return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    return QdrantClient(host=QDRANT_HOST, port=6333)


def ensure_collection():
    client = get_client()
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION not in collections:
        test_vec = embed_query("test")
        client.create_collection(
            collection_name=COLLECTION,
            vectors_config=VectorParams(size=len(test_vec), distance=Distance.COSINE),
        )


def add_texts(chunks: list[str], filename: str):
    client = get_client()
    ensure_collection()

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


def search(question: str, top_k: int = 5) -> list[dict]:
    client = get_client()
    ensure_collection()

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


def delete_document(filename: str) -> int:
    client = get_client()
    points = client.scroll(
        collection_name=COLLECTION,
        scroll_filter=Filter(must=[
            FieldCondition(key="source", match=MatchValue(value=filename))
        ]),
        limit=1000,
        with_payload=False,
    )[0]

    count = len(points)
    if count == 0:
        return 0

    client.delete(
        collection_name=COLLECTION,
        points_selector=Filter(must=[
            FieldCondition(key="source", match=MatchValue(value=filename))
        ]),
    )
    return count


def reset_collection():
    client = get_client()
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION in collections:
        client.delete_collection(COLLECTION)
    ensure_collection()


def list_documents() -> dict:
    client = get_client()
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION not in collections:
        return {"documents": [], "total_chunks": 0}

    info = client.get_collection(COLLECTION)
    total = info.points_count

    points = client.scroll(
        collection_name=COLLECTION,
        limit=1000,
        with_payload=["source"],
    )[0]

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