import httpx
from typing import List


API_URL = (
    "https://api-inference.huggingface.co/pipeline/feature-extraction/"
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)


def embed_texts(texts: List[str]) -> List[List[float]]:
    response = httpx.post(
        API_URL,
        json={"inputs": texts, "options": {"wait_for_model": True}},
        timeout=120.0,
    )
    if response.status_code != 200:
        raise Exception(f"HuggingFace error: {response.status_code}")
    return response.json()


def embed_query(text: str) -> List[float]:
    return embed_texts([text])[0]


def embed_documents(texts: List[str]) -> List[List[float]]:
    all_embeddings = []
    batch_size = 20
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        embeddings = embed_texts(batch)
        all_embeddings.extend(embeddings)
    return all_embeddings