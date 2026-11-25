"""Application resource and per-user data paths."""

from __future__ import annotations

import os
import re
import shutil
import sys
from pathlib import Path

from dotenv import dotenv_values

APP_DIRECTORY_NAME = "veriunb"
_OPENROUTER_KEY_PATTERN = re.compile(r"sk-or-v1-[A-Za-z0-9_-]{8,}\Z")


def user_data_dir() -> Path:
    """Return the XDG data directory for this user."""
    data_home = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    if not data_home.is_absolute():
        data_home = Path.home() / ".local" / "share"
    return data_home / APP_DIRECTORY_NAME


def user_env_path() -> Path:
    """Return the path to the user's private environment file."""
    return user_data_dir() / ".env"


def ensure_user_env_file(path: str | Path | None = None) -> Path:
    """Create the user's environment file with a placeholder key if missing."""
    target = Path(path) if path is not None else user_env_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if not target.is_file():
            raise IsADirectoryError(f"O caminho do arquivo .env não é um arquivo: {target}")
        return target

    try:
        descriptor = os.open(
            target,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL,
            0o600,
        )
    except FileExistsError:
        if target.is_file():
            return target
        raise

    with os.fdopen(descriptor, "w", encoding="utf-8") as env_file:
        env_file.write("OPENROUTER_API_KEY=insira_a_chave_aqui\n")
    return target


def _is_valid_openrouter_key(value: object) -> bool:
    return isinstance(value, str) and _OPENROUTER_KEY_PATTERN.fullmatch(value.strip()) is not None


def user_env_api_key(path: str | Path | None = None) -> str:
    """Return a valid API key from the user's .env, without exposing it."""
    env_file = Path(path) if path is not None else user_env_path()
    if not env_file.is_file():
        return ""
    value = dotenv_values(env_file).get("OPENROUTER_API_KEY")
    return value.strip() if _is_valid_openrouter_key(value) else ""


def has_user_api_key() -> bool:
    """Check whether the user's .env contains a valid OpenRouter key."""
    return bool(user_env_api_key())


def get_openrouter_api_key() -> str:
    """Return a valid environment key or the current key stored in the user's .env."""
    value = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if _is_valid_openrouter_key(value):
        return value
    return user_env_api_key()


SCRAPE_URLS_PATH = user_data_dir() / "scrape_urls.json"


def resource_path(name: str) -> Path:
    """Find a bundled resource in development and PyInstaller builds."""
    bundle_dir = Path(
        getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)
    )
    return bundle_dir / name


def database_path() -> Path:
    """Return the writable database path, migrating the project database once."""
    directory = user_data_dir()
    directory.mkdir(parents=True, exist_ok=True)
    target = directory / "news.db"
    legacy_database = resource_path("news.db")
    if not target.exists() and legacy_database.is_file():
        shutil.copy2(legacy_database, target)
    return target


def ensure_scrape_urls_file(path: str | Path | None = None) -> Path:
    """Create the user's source file from the bundled defaults when needed."""
    target = Path(path) if path is not None else user_data_dir() / "scrape_urls.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        default_file = resource_path("scrape_urls.json")
        if not default_file.is_file():
            raise FileNotFoundError(
                f"Arquivo padrão de fontes não encontrado: {default_file}"
            )
        shutil.copy2(default_file, target)
    return target
