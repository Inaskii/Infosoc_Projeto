"""Persistência SQLite das notícias coletadas pelo scraper."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app_paths import database_path


class NewsDatabase:
    """Armazena notícias em SQLite, usando a URL como identificador único."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path is not None else database_path()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._create_table()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _create_table(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS news (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    published TEXT NOT NULL,
                    source TEXT NOT NULL,
                    summary TEXT NOT NULL DEFAULT '',
                    content TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS news_embeddings (
                    url TEXT PRIMARY KEY,
                    embedding TEXT NOT NULL,
                    model TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(url) REFERENCES news(url) ON DELETE CASCADE
                )
                """
            )
            columns = {
                row[1]
                for row in connection.execute("PRAGMA table_info(news_embeddings)")
            }
            if "created_at" not in columns:
                connection.execute(
                    "ALTER TABLE news_embeddings "
                    "ADD COLUMN created_at TEXT"
                )

    def save_news(self, news: str | Iterable[Mapping[str, Any]]) -> int:
        """Insere ou atualiza notícias e retorna a quantidade processada.

        ``news`` pode ser o JSON retornado por ``ScrapeWeb.scrape_data()`` ou
        uma coleção de dicionários de notícias.
        """
        articles = self._parse_news(news)
        now = datetime.now(timezone.utc).isoformat()

        with self._connect() as connection:
            connection.executemany(
                """
                INSERT INTO news (
                    url, title, published, source, summary, content,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    title = excluded.title,
                    published = excluded.published,
                    source = excluded.source,
                    summary = excluded.summary,
                    content = excluded.content,
                    updated_at = excluded.updated_at
                """,
                [
                    (
                        article["url"],
                        article.get("title", "Sem título"),
                        article.get("published", ""),
                        article.get("source", ""),
                        article.get("summary", ""),
                        article.get("content", ""),
                        now,
                        now,
                    )
                    for article in articles
                ],
            )
        return len(articles)

    def get_news(self, limit: int | None = None) -> list[dict[str, Any]]:
        """Retorna notícias armazenadas, da mais recente para a mais antiga."""
        if limit is not None and limit < 1:
            raise ValueError("O limite de notícias deve ser maior que zero.")

        query = "SELECT * FROM news ORDER BY published DESC, id DESC"
        parameters: tuple[int, ...] = ()
        if limit is not None:
            query += " LIMIT ?"
            parameters = (limit,)

        with self._connect() as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [dict(row) for row in rows]

    def save_embedding(
        self,
        url: str,
        embedding: list[float],
        model: str,
    ) -> None:
        """Salva ou atualiza o embedding vetorial associado a uma notícia."""
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO news_embeddings (
                    url, embedding, model, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(url) DO UPDATE SET
                    embedding = excluded.embedding,
                    model = excluded.model,
                    updated_at = excluded.updated_at
                """,
                (url, json.dumps(embedding), model, now, now),
            )

    def get_embeddings(self) -> list[dict[str, Any]]:
        """Retorna notícias que possuem embeddings persistidos."""
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT n.url, n.title, n.published, n.summary, n.content,
                       e.embedding, e.model
                FROM news_embeddings AS e
                JOIN news AS n ON n.url = e.url
                """
            ).fetchall()

        results = []
        for row in rows:
            article = dict(row)
            article["embedding"] = json.loads(article["embedding"])
            results.append(article)
        return results

    @staticmethod
    def _parse_news(news: str | Iterable[Mapping[str, Any]]) -> list[Mapping[str, Any]]:
        if isinstance(news, str):
            parsed = json.loads(news)
        else:
            parsed = list(news)

        if not isinstance(parsed, list):
            raise ValueError("As notícias devem ser uma lista JSON.")

        for article in parsed:
            if not isinstance(article, Mapping) or not article.get("url"):
                raise ValueError("Cada notícia deve ser um objeto com uma URL.")
        return parsed


if __name__ == "__main__":
    from webscrape import ScrapeWeb, load_scrape_sources

    database = NewsDatabase()
    saved = 0
    for source in load_scrape_sources():
        scraper = ScrapeWeb(
            source["url"],
            max_articles=5,
            source_name=source["name"],
        )
        saved += database.save_news(scraper.scrape_data())
    print(f"{saved} notícias salvas em {database.path}.\n")
    for article in database.get_news():
        print(f"{article['published']} - {article['title']} ({article['url']})")
        print(f"Conteúdo: {article['content'][:100]}...\n")
