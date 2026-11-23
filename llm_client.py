"""HTTP client for the OpenRouter chat completions API."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Sequence

import requests
from dotenv import load_dotenv

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
BASE_URL = "https://openrouter.ai/api/v1"
DEFAULT_MODELS = (
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3.5-lightning:free",
    "openrouter/free",
)

HEADERS = {
    "Authorization": "",
    "Content-Type": "application/json",
}

load_dotenv()


class OpenRouterError(Exception):
    """An API, configuration, or response error suitable for display to users."""

def get_openrouter_models(model_type: str) -> list[dict[str, Any]]:
    """
    Retorna os modelos disponíveis de acordo com o tipo:
    - embedding
    - text-only
    - multimodal
    """

    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()

    if not api_key:
        raise OpenRouterError(
            "Chave OpenRouter não configurada. Defina OPENROUTER_API_KEY no arquivo .env."
        )

    if model_type == "embedding":
        url = f"{BASE_URL}/embeddings/models"

    elif model_type in ("text-only", "multimodal"):
        url = f"{BASE_URL}/models"

    else:
        raise ValueError("Tipo de modelo inválido.")

    params = {
        "sort": "pricing-low-to-high"
    }
    headers = {
        **HEADERS,
        "Authorization": f"Bearer {api_key}",
    }

    if model_type == "text-only":
        params["output_modalities"] = "text"
        params["endpoints"] = "/api/v1/chat/completions"

    elif model_type == "multimodal":
        params["output_modalities"] = "text"
        params["endpoints"] = "/api/v1/chat/completions"

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=20
    )

    response.raise_for_status()

    models = response.json().get("data", [])

    # Classificação dos modelos
    if model_type == "text-only":
        models = [
            model for model in models
            if model.get("architecture", {}).get("input_modalities", []) == ["text"]
        ]

    elif model_type == "multimodal":
        models = [
            model for model in models
            if any(
                modality != "text"
                for modality in model.get("architecture", {}).get("input_modalities", [])
            )
        ]

    # Embeddings já vêm filtrados pelo endpoint
    return models

def get_cheapest_model(model_type: str) -> str:
    """
    Retorna o modelo mais barato disponível no catálogo.
    """

    models = get_openrouter_models(model_type)

    if not models:
        return DEFAULT_MODELS[0]

    return models[0]["id"]



def ask_llm(
    prompt: str,
    *,
    models: Sequence[str] | None = None,
    temperature: float = 0.2,
    timeout: float = 30,
) -> str:
    """Send a prompt to OpenRouter, returning the first generated message."""
    if not prompt.strip():
        raise ValueError("O prompt para a análise não pode estar vazio.")
    if not 0 <= temperature <= 2:
        raise ValueError("A temperatura deve estar entre 0 e 2.")
    if timeout <= 0:
        raise ValueError("O timeout deve ser maior que zero.")

    selected_models = (
        [get_cheapest_model("text-only")]
        if models is None
        else list(models)
    )
    if not selected_models or any(not model.strip() for model in selected_models):
        raise ValueError("Informe ao menos um modelo OpenRouter válido.")

    #debug
    print(f"\nModelos selecionados: {selected_models}\n")

    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise OpenRouterError(
            "Chave OpenRouter não configurada. Defina OPENROUTER_API_KEY no arquivo .env."
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Inaskii/Infosoc_Projeto",
        "X-Title": "VeriUnB",
    }
    payload = {
        "models": selected_models,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
    }

    try:
        response = requests.post(
            OPENROUTER_API_URL,
            headers=headers,
            json=payload,
            timeout=timeout,
        )
    except requests.Timeout as exc:
        raise OpenRouterError(
            "A solicitação ao OpenRouter excedeu o tempo limite. Tente novamente."
        ) from exc
    except requests.ConnectionError as exc:
        raise OpenRouterError(
            "Não foi possível conectar ao OpenRouter. Verifique sua conexão."
        ) from exc
    except requests.RequestException as exc:
        raise OpenRouterError(
            "Ocorreu um erro de rede ao consultar o OpenRouter."
        ) from exc

    if response.status_code == 401:
        raise OpenRouterError(
            "A chave OpenRouter é inválida ou não foi aceita. Confira OPENROUTER_API_KEY."
        )
    if response.status_code == 429:
        raise OpenRouterError(
            "O limite gratuito do OpenRouter foi atingido. Aguarde e tente novamente."
        )
    if not response.ok:
        raise OpenRouterError(
            f"O OpenRouter não conseguiu processar a solicitação (HTTP {response.status_code})."
        )

    try:
        data: Any = response.json()
    except (ValueError, requests.exceptions.JSONDecodeError) as exc:
        raise OpenRouterError("O OpenRouter retornou uma resposta JSON inválida.") from exc

    try:
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise OpenRouterError(
            "A resposta do OpenRouter veio em um formato inesperado."
        ) from exc
    if not isinstance(content, str) or not content.strip():
        raise OpenRouterError("O OpenRouter retornou uma resposta vazia ou malformada.")
    return content.strip()


def ask_llm_json(
    prompt: str,
    *,
    models: Sequence[str] | None = None,
    temperature: float = 0.2,
    timeout: float = 30,
) -> dict[str, Any]:
    """Ask the model for JSON and parse a JSON object from its response."""
    content = ask_llm(
        prompt,
        models=models,
        temperature=temperature,
        timeout=timeout,
    )
    fenced_json = re.search(
        r"```(?:[a-zA-Z0-9_-]+)?\s*(.*?)```",
        content,
        re.DOTALL,
    )
    if fenced_json:
        content = fenced_json.group(1).strip()

    try:
        data: Any = json.loads(content)
    except json.JSONDecodeError as exc:
        raise OpenRouterError(
            "A resposta do OpenRouter não contém um JSON válido."
        ) from exc
    if not isinstance(data, dict):
        raise OpenRouterError("A resposta JSON do OpenRouter deve ser um objeto.")
    return data
