"""Geração de embeddings pelo OpenRouter para alimentação do RAG."""

from __future__ import annotations

import math
import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import requests
from dotenv import load_dotenv

from database import NewsDatabase

OPENROUTER_EMBEDDINGS_API_URL = "https://openrouter.ai/api/v1/embeddings"
DEFAULT_EMBEDDING_MODELS = (
    "nvidia/nemotron-3.5-embed-8b:free",
)

load_dotenv()


class OpenRouterEmbeddingError(Exception):
    """An API, configuration, or response error suitable for display to users."""


class OpenRouterEmbeddingService:
    def __init__(
        self,
        models: Sequence[str] | None = None,
        model: str | None = None,
        timeout: float = 60,
    ) -> None:
        selected_models = (
            list(models)
            if models is not None
            else ([model] if model is not None else list(DEFAULT_EMBEDDING_MODELS))
        )
        if not selected_models or any(not item.strip() for item in selected_models):
            raise ValueError("Informe ao menos um modelo de embedding OpenRouter válido.")

        env_model = os.getenv("OPENROUTER_EMBED_MODEL", "").strip()
        if model is None and models is None and env_model:
            selected_models = [env_model]

        self.models = tuple(selected_models)
        self.model = self.models[0]
        self.timeout = timeout

    def embed(self, content: str, input_type: str = "passage") -> list[float]:
        if not content.strip():
            raise ValueError("O conteúdo para embedding não pode estar vazio.")
        if self.timeout <= 0:
            raise ValueError("O timeout deve ser maior que zero.")

        if input_type not in ("passage", "query"):
            # "passage" é usado para textos longos, "query" para consultas curtas.
            raise ValueError("input_type deve ser 'passage' ou 'query'")

        api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        if not api_key:
            raise OpenRouterEmbeddingError(
                "Chave OpenRouter não configurada. Defina OPENROUTER_API_KEY no arquivo .env."
            )

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        last_error: OpenRouterEmbeddingError | None = None

        for selected_model in self.models:
            try:
                response = requests.post(
                    OPENROUTER_EMBEDDINGS_API_URL,
                    headers=headers,
                    json={
                        "model": selected_model,
                        "input": content,
                        "input_type": input_type,
                        "modality": "text"
                        },
                    timeout=self.timeout,
                )
            except requests.Timeout as exc:
                raise OpenRouterEmbeddingError(
                    "A solicitação ao OpenRouter excedeu o tempo limite. Tente novamente."
                ) from exc
            except requests.ConnectionError as exc:
                raise OpenRouterEmbeddingError(
                    "Não foi possível conectar ao OpenRouter. Verifique sua conexão."
                ) from exc
            except requests.RequestException as exc:
                raise OpenRouterEmbeddingError(
                    "Ocorreu um erro de rede ao consultar o OpenRouter."
                ) from exc

            if response.status_code == 401:
                raise OpenRouterEmbeddingError(
                    "A chave OpenRouter é inválida ou não foi aceita. Confira OPENROUTER_API_KEY."
                )
            if response.status_code == 429:
                last_error = OpenRouterEmbeddingError(
                    "O limite gratuito do OpenRouter foi atingido. Aguarde e tente novamente."
                )
                continue
            if response.status_code == 410:
                last_error = OpenRouterEmbeddingError(
                    f"O modelo de embedding {selected_model} foi removido pelo OpenRouter "
                    "(HTTP 410 - fim de vida)."
                )
                continue
            if not response.ok:
                last_error = OpenRouterEmbeddingError(
                    f"O modelo de embedding {selected_model} não está disponível "
                    f"(HTTP {response.status_code})."
                )
                continue

            try:
                result: Any = response.json()
            except (ValueError, requests.exceptions.JSONDecodeError) as exc:
                raise OpenRouterEmbeddingError(
                    "O OpenRouter retornou uma resposta JSON inválida."
                ) from exc

            try:
                data = result["data"]
                vector = data[0]["embedding"]
            except (KeyError, IndexError, TypeError) as exc:
                raise OpenRouterEmbeddingError(
                    "A resposta de embedding do OpenRouter veio em formato inesperado."
                ) from exc
            if not isinstance(vector, list) or not vector:
                raise OpenRouterEmbeddingError(
                    "O OpenRouter não retornou um vetor de embedding válido."
                )

            self.model = selected_model
            return [float(value) for value in vector]

        if last_error is not None:
            raise last_error
        raise OpenRouterEmbeddingError(
            "Nenhum dos modelos de embedding OpenRouter configurados está disponível."
        )


# Mantém compatibilidade com imports que ainda usam o nome antigo da classe.
OllamaEmbeddingService = OpenRouterEmbeddingService


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