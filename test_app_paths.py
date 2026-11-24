"""Tests for per-user application data paths."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app_paths import (
    database_path,
    ensure_scrape_urls_file,
    ensure_user_env_file,
    user_data_dir,
    user_env_path,
)
from database import NewsDatabase
from webscrape import load_scrape_sources


class AppPathsTests(unittest.TestCase):
    def test_uses_xdg_data_home_for_user_files(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with patch.dict("os.environ", {"XDG_DATA_HOME": directory}):
                self.assertEqual(user_data_dir(), Path(directory) / "veriunb")
                self.assertEqual(
                    user_env_path(),
                    Path(directory) / "veriunb" / ".env",
                )

    def test_creates_private_env_file_with_placeholder_only_when_missing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "veriunb" / ".env"
            self.assertEqual(ensure_user_env_file(target), target)
            self.assertEqual(
                target.read_text(encoding="utf-8"),
                "OPENROUTER_API_KEY=insira_a_chave_aqui\n",
            )
            self.assertEqual(target.stat().st_mode & 0o777, 0o600)

            target.write_text("OPENROUTER_API_KEY=user-secret", encoding="utf-8")
            ensure_user_env_file(target)
            self.assertEqual(
                target.read_text(encoding="utf-8"),
                "OPENROUTER_API_KEY=user-secret",
            )

    def test_copies_default_sources_without_overwriting_user_changes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            template = root / "defaults.json"
            template.write_text('[{"name":"Default"}]', encoding="utf-8")
            target = root / "data" / "scrape_urls.json"
            with patch("app_paths.resource_path", return_value=template):
                self.assertEqual(ensure_scrape_urls_file(target), target)
                self.assertEqual(target.read_text(encoding="utf-8"), '[{"name":"Default"}]')

                target.write_text("[]", encoding="utf-8")
                ensure_scrape_urls_file(target)

            self.assertEqual(target.read_text(encoding="utf-8"), "[]")

    def test_default_source_loader_seeds_config_in_user_data_dir(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            template = root / "scrape_urls.json"
            template.write_text(
                '[{"name":"Portal","url":"https://example.test/"}]',
                encoding="utf-8",
            )
            with (
                patch.dict("os.environ", {"XDG_DATA_HOME": str(root / "xdg")}),
                patch("app_paths.resource_path", return_value=template),
            ):
                sources = load_scrape_sources()
                copied = root / "xdg" / "veriunb" / "scrape_urls.json"

            self.assertEqual(
                sources,
                [{"name": "Portal", "url": "https://example.test/"}],
            )
            self.assertTrue(copied.is_file())

    def test_migrates_existing_database_only_when_user_database_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = root / "legacy.db"
            legacy.write_bytes(b"existing database")
            with (
                patch.dict("os.environ", {"XDG_DATA_HOME": str(root / "xdg")}),
                patch("app_paths.resource_path", return_value=legacy),
            ):
                target = database_path()
                self.assertEqual(target.read_bytes(), b"existing database")

                target.write_bytes(b"user database")
                self.assertEqual(database_path(), target)

            self.assertEqual(target.read_bytes(), b"user database")

    def test_database_uses_the_user_data_path_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "veriunb" / "news.db"
            with patch("database.database_path", return_value=target):
                database = NewsDatabase()

            self.assertEqual(database.path, target)
            self.assertTrue(target.is_file())


if __name__ == "__main__":
    unittest.main()
