import hashlib
import os
from typing import List

import httpx

EMBED_DIM = 1024


def embed_texts(texts: List[str]) -> List[List[float]]:
    key = os.getenv("MISTRAL_API_KEY", "")
    if key:
        try:
            out = _mistral_embed(texts, key)
            if out:
                return out
        except Exception:
            pass

    return [_local_embed(t, EMBED_DIM) for t in texts]


def _local_embed(text: str, dim: int) -> List[float]:
    """Детерминированный вектор без внешнего API (для dev и fallback)."""
    need = dim * 2
    buf = b""
    n = 0
    while len(buf) < need:
        buf += hashlib.sha256(f"{text}::{n}".encode("utf-8")).digest()
        n += 1
    vec: List[float] = []
    for j in range(dim):
        off = j * 2
        x = int.from_bytes(buf[off : off + 2], "big") / 65535.0
        vec.append(x * 2.0 - 1.0)
    return vec


def _mistral_embed(texts: List[str], api_key: str) -> List[List[float]]:
    r = httpx.post(
        "https://api.mistral.ai/v1/embeddings",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        json={"model": "mistral-embed", "input": texts},
        timeout=60.0,
    )
    data = r.json()
    if "error" in data:
        raise RuntimeError(str(data["error"]))
    return [row["embedding"] for row in data["data"]]


def embed_query(text: str) -> List[float]:
    return embed_texts([text])[0]


def embed_documents(texts: List[str]) -> List[List[float]]:
    out: List[List[float]] = []
    step = 10
    for i in range(0, len(texts), step):
        out.extend(embed_texts(texts[i : i + step]))
    return out
