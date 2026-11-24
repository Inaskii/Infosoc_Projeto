"""Tests for persisting sources added through the app."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from main import App
from webscrape import load_scrape_sources


def make_app(scrape_sources: list[dict[str, str]]) -> SimpleNamespace:
    verifier = SimpleNamespace(scrape_sources=[source.copy() for source in scrape_sources])
    app = SimpleNamespace(
        scrape_sources=[source.copy() for source in scrape_sources],
        sources=[source.copy() for source in scrape_sources],
        verifier=verifier,
        scrape_config_error=None,
    )
    app._save_scrape_sources = lambda sources: App._save_scrape_sources(app, sources)
    return app


class AppSourceTests(unittest.TestCase):
    def test_add_first_source_creates_the_config_file(self) -> None:
        source = {
            "name": "First portal",
            "url": "https://example.test/",
        }
        app = make_app([])
        app.scrape_config_error = "missing config"

        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "scrape_urls.json"
            with patch("main.SCRAPE_URLS_PATH", config_path):
                App.add_scrape_source(app, source)

            self.assertEqual(load_scrape_sources(config_path), [source])
            self.assertIsNone(app.scrape_config_error)

    def test_add_scrape_source_persists_and_updates_app_state(self) -> None:
        initial_source = {
            "name": "Portal UnB",
            "url": "https://noticias.unb.br/",
        }
        added_source = {
            "name": "Outro portal",
            "url": "https://example.test/",
        }
        app = make_app([initial_source])
        verifier = app.verifier
        app.scrape_config_error = "previous config error"

        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "scrape_urls.json"
            config_path.write_text(json.dumps([initial_source]), encoding="utf-8")
            with patch("main.SCRAPE_URLS_PATH", config_path):
                App.add_scrape_source(app, added_source)

            expected_sources = [initial_source, added_source]
            self.assertEqual(load_scrape_sources(config_path), expected_sources)
            self.assertEqual(app.sources, expected_sources)
            self.assertEqual(app.scrape_sources, expected_sources)
            self.assertEqual(verifier.scrape_sources, expected_sources)
            self.assertIsNone(app.scrape_config_error)

    def test_add_scrape_source_rejects_duplicate_url(self) -> None:
        existing_source = {
            "name": "Portal UnB",
            "url": "https://noticias.unb.br/",
        }
        app = make_app([existing_source])

        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "scrape_urls.json"
            config_path.write_text(json.dumps([existing_source]), encoding="utf-8")
            with patch("main.SCRAPE_URLS_PATH", config_path):
                with self.assertRaises(ValueError):
                    App.add_scrape_source(
                        app,
                        {"name": "Second name", "url": existing_source["url"]},
                    )

            self.assertEqual(load_scrape_sources(config_path), [existing_source])

    def test_remove_scrape_source_persists_and_updates_app_state(self) -> None:
        first_source = {
            "name": "Portal UnB",
            "url": "https://noticias.unb.br/",
        }
        source_to_remove = {
            "name": "Outro portal",
            "url": "https://example.test/",
        }
        app = make_app([first_source, source_to_remove])

        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "scrape_urls.json"
            config_path.write_text(
                json.dumps([first_source, source_to_remove]),
                encoding="utf-8",
            )
            with patch("main.SCRAPE_URLS_PATH", config_path):
                App.remove_scrape_source(app, source_to_remove)

            self.assertEqual(load_scrape_sources(config_path), [first_source])
            self.assertEqual(app.sources, [first_source])
            self.assertEqual(app.scrape_sources, [first_source])
            self.assertEqual(app.verifier.scrape_sources, [first_source])

    def test_removing_last_source_saves_an_empty_list(self) -> None:
        source = {
            "name": "Portal UnB",
            "url": "https://noticias.unb.br/",
        }
        app = make_app([source])

        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "scrape_urls.json"
            config_path.write_text(json.dumps([source]), encoding="utf-8")
            with patch("main.SCRAPE_URLS_PATH", config_path):
                App.remove_scrape_source(app, source)

            self.assertEqual(load_scrape_sources(config_path), [])
            self.assertEqual(app.sources, [])


if __name__ == "__main__":
    unittest.main()
