"""Tests for the shared web scraping URL configuration."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from webscrape import Scrape, load_scrape_sources


class LoadScrapeUrlsTests(unittest.TestCase):
    def test_loads_all_configured_feed_urls(self) -> None:
        sources = [
            {"name": "Portal UnB", "url": "https://noticias.unb.br/?format=feed&type=rss"},
            {"name": "Outro portal", "url": "https://example.test/feed.xml"},
        ]
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "scrape_urls.json"
            config_path.write_text(json.dumps(sources), encoding="utf-8")

            self.assertEqual(load_scrape_sources(config_path), sources)

    def test_rejects_non_http_urls(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config_path = Path(directory) / "scrape_urls.json"
            config_path.write_text(
                json.dumps([{"name": "Arquivo local", "url": "file:///etc/passwd"}]),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                load_scrape_sources(config_path)

    def test_scraper_uses_the_configured_source_name(self) -> None:
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            @staticmethod
            def read() -> bytes:
                return (
                    b"<rss><channel><title>Feed title</title><item>"
                    b"<title>Article</title><link>https://example.test/article</link>"
                    b"</item></channel></rss>"
                )

        with patch("webscrape.urlopen", return_value=FakeResponse()), patch.object(
            Scrape, "_fetch_article_content", return_value="Article content"
        ):
            articles = json.loads(
                Scrape(
                    "https://example.test/feed",
                    source_name="Configured source",
                ).scrape_data()
            )

        self.assertEqual(articles[0]["source"], "Configured source")


if __name__ == "__main__":
    unittest.main()
