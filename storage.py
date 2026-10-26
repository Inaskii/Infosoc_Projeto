"""Local persistence for registered news sources."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from urllib.parse import urlparse


class SourceStorage:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or Path.home() / ".veriunb" / "sources.json"

    def load(self) -> list[dict[str, str]]:
        if not self.path.exists():
            return []
        try:
            data: Any = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        if not isinstance(data, list):
            return []
        return [
            {"name": str(item["name"]), "url": str(item["url"])}
            for item in data
            if isinstance(item, dict)
            and isinstance(item.get("name"), str)
            and isinstance(item.get("url"), str)
            and self.is_valid_url(item["url"])
        ]

    def save(self, sources: list[dict[str, str]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(sources, ensure_ascii=False, indent=2), encoding="utf-8")
        temporary.replace(self.path)

    @staticmethod
    def is_valid_url(value: str) -> bool:
        parsed = urlparse(value.strip())
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
