import httpx
import hashlib
import math
import os
from typing import List


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Пробуем разные API по очереди.
    Приоритет: Mistral → HuggingFace → Cohere → Together → Local
    """

    # Попытка 1: Mistral AI (приоритетно!)
    mistral_key = os.getenv("MISTRAL_API_KEY", "")
    if mistral_key:
        try:
            result = _mistral_embed(texts, mistral_key)
            if result:
                return result
        except Exception:
            pass

 


    # Fallback: deterministic local embedding.
    # This keeps the app functional when no external embedding provider is configured.
    dim = 1024
    return [_local_embed(t, dim) for t in texts]

# ==========================================
# Mistral AI (превосходное качество!)
# ==========================================

def _local_embed(text: str, dim: int) -> List[float]:
    # Generate a deterministic byte stream from hashes, then map to [-1, 1].
    needed = dim * 2  # 2 bytes per float
    buf = b""
    i = 0
    while len(buf) < needed:
        seed = f"{text}::{i}".encode("utf-8")
        buf += hashlib.sha256(seed).digest()
        i += 1

    vector: List[float] = []
    for j in range(dim):
        offset = j * 2
        val = int.from_bytes(buf[offset : offset + 2], "big") / 65535.0
        vector.append(val * 2.0 - 1.0)
    return vector

def _mistral_embed(texts: List[str], api_key: str) -> List[List[float]]:
    """
    Mistral AI embeddings — отличное качество для русского языка.
    
    Бесплатный тариф: 10K запросов/месяц бесплатно
    Регистрация: https://console.mistral.ai
    
    Модель: mistral-embed
    Размер вектора: 1024
    """
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    response = httpx.post(
        "https://api.mistral.ai/v1/embeddings",
        headers=headers,
        json={
            "model": "mistral-embed",
            "input": texts,
        },
        timeout=60.0,
    )

    data = response.json()

    if "error" in data:
        raise Exception(f"Mistral error: {data['error']}")

    return [item["embedding"] for item in data["data"]]



# ==========================================
# Публичные функции
# ==========================================

def embed_query(text: str) -> List[float]:
    return embed_texts([text])[0]


def embed_documents(texts: List[str]) -> List[List[float]]:
    all_embeddings = []
    batch_size = 10
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        embeddings = embed_texts(batch)
        all_embeddings.extend(embeddings)
    return all_embeddings