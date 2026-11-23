"""Geração de embeddings locais com Ollama para alimentação do RAG."""

from __future__ import annotations

import json
import math
import os
from urllib.error import HTTPError
from urllib.request import Request, urlopen


class OllamaEmbeddingService:
    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 60,
    ) -> None:
        self.base_url = (base_url or os.getenv("OLLAMA_URL", "http://localhost:11434")).rstrip("/")
        self.model = model or os.getenv("OLLAMA_EMBED_MODEL", "nomic-embed-text")
        self.timeout = timeout

    def embed(self, content: str) -> list[float]:
        if not content.strip():
            raise ValueError("O conteúdo para embedding não pode estar vazio.")

        payload = json.dumps({"model": self.model, "input": content}).encode("utf-8")
        request = Request(
            f"{self.base_url}/api/embed",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                result = json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            if error.code != 404:
                raise
            return self._embed_legacy(content)

        embeddings = result.get("embeddings")
        if not embeddings:
            raise ValueError("O Ollama não retornou um vetor de embedding.")
        vector = embeddings[0]
        if not isinstance(vector, list):
            raise ValueError("O Ollama retornou um formato de embedding inválido.")
        return [float(value) for value in vector]

    def _embed_legacy(self, content: str) -> list[float]:
        payload = json.dumps({"model": self.model, "prompt": content}).encode("utf-8")
        request = Request(
            f"{self.base_url}/api/embeddings",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=self.timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
        vector = result.get("embedding")
        if not isinstance(vector, list):
            raise ValueError("O Ollama não retornou um vetor de embedding válido.")
        return [float(value) for value in vector]


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right) or not left:
        return -1.0
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        return -1.0
    return dot / (left_norm * right_norm)


def vector_search(
    query_vector: list[float],
    documents: list[dict],
    limit: int = 5,
) -> list[tuple[float, dict]]:
    """Ordena documentos pelo embedding mais semelhante à consulta."""
    if limit < 1:
        raise ValueError("O limite da busca vetorial deve ser maior que zero.")

    ranked = []
    for document in documents:
        vector = document.get("embedding")
        if isinstance(vector, list):
            score = cosine_similarity(query_vector, vector)
            ranked.append((score, document))

    ranked.sort(key=lambda item: item[0], reverse=True)
    return ranked[:limit]
