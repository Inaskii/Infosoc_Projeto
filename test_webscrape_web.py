"""Tests for scraping articles discovered from a homepage."""

from __future__ import annotations

import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from webscrape import ScrapeWeb


class ScrapeWebTests(unittest.TestCase):
    def test_prefers_two_path_segments_before_three(self) -> None:
        two_segment_url = "https://unbciencia.unb.br/institucional/8923-noticia"
        category_url = "https://unbciencia.unb.br/humanidades/91-ciencia-politica"
        three_segment_url = (
            "https://unbciencia.unb.br/biologicas/26-fitopatologia/798-estudo-3"
        )
        homepage = """
            <a href="/biologicas/26-fitopatologia/798-estudo-3?utm_source=home">Three components</a>
            <a href="/biologicas/26-fitopatologia/798-estudo-3#top">Duplicate</a>
            <a href="/humanidades/91-ciencia-politica">Two-component category</a>
            <a href="/institucional/8923-noticia#top">Two components</a>
            <a href="/biologicas/26-fitopatologia/797-estudo/relacionada">Four path components</a>
            <a href="https://external.test/news">External</a>
            <a href="https://noticias.unb.br/institucional/8923-noticia">Other UnB site</a>
            <a href="https://unbciencia.unb.br.evil/humanidades/91-ciencia/1-fake">Fake host</a>
            <a href="http://unbciencia.unb.br/humanidades/91-ciencia/1-insecure">HTTP URL</a>
        """
        metadata = [
            SimpleNamespace(
                title="Notícia de dois segmentos",
                date="2026-01-01",
                sitename="Portal",
                description="Resumo de dois segmentos",
            ),
            SimpleNamespace(
                title="Notícia de três segmentos",
                date="2026-01-02",
                sitename="Portal",
                description="Resumo de três segmentos",
            ),
        ]

        with (
            patch(
                "webscrape.trafilatura.fetch_url",
                side_effect=[
                    homepage,
                    (
                        "<h2 itemprop='name'>Matéria 1</h2>"
                        "<h2 itemprop='name'>Matéria 2</h2><html>category</html>"
                    ),
                    "<h2 itemprop='name'>Notícia de dois segmentos</h2><html>article 2</html>",
                    "<h2 itemprop='name'>Notícia de três segmentos</h2><html>article 3</html>",
                ],
            ) as fetch_url,
            patch(
                "webscrape.trafilatura.extract_metadata",
                side_effect=metadata,
            ) as extract_metadata,
            patch(
                "webscrape.trafilatura.extract",
                side_effect=[
                    "Primeiro parágrafo de dois segmentos\n\nConteúdo da notícia",
                    "Primeiro parágrafo de três segmentos\n\nConteúdo da notícia",
                ],
            ) as extract,
        ):
            articles = json.loads(
                ScrapeWeb(
                    "https://unbciencia.unb.br/",
                    source_name="Fonte configurada",
                ).scrape_data()
            )

        self.assertEqual(fetch_url.call_count, 4)
        self.assertEqual(extract_metadata.call_count, 2)
        self.assertEqual(extract.call_count, 2)
        self.assertEqual(
            articles,
            [
                {
                    "title": "Notícia de dois segmentos",
                    "url": two_segment_url,
                    "published": "2026-01-01",
                    "source": "Fonte configurada",
                    "summary": "Primeiro parágrafo de dois segmentos",
                    "content": "Primeiro parágrafo de dois segmentos\n\nConteúdo da notícia",
                },
                {
                    "title": "Notícia de três segmentos",
                    "url": three_segment_url,
                    "published": "2026-01-02",
                    "source": "Fonte configurada",
                    "summary": "Primeiro parágrafo de três segmentos",
                    "content": "Primeiro parágrafo de três segmentos\n\nConteúdo da notícia",
                },
            ],
        )
        self.assertEqual(fetch_url.call_args_list[1].args[0], category_url)
        self.assertEqual(fetch_url.call_args_list[2].args[0], two_segment_url)
        self.assertEqual(fetch_url.call_args_list[3].args[0], three_segment_url)
        self.assertEqual(
            extract.call_args_list[0].kwargs,
            {
                "url": two_segment_url,
                "include_comments": False,
                "include_tables": False,
                "include_images": False,
                "include_links": False,
                "favor_precision": True,
            },
        )

    def test_leaves_published_empty_when_date_is_missing(self) -> None:
        metadata = SimpleNamespace(
            title="Notícia sem data",
            date=None,
            sitename="Portal",
            description="Resumo",
        )
        with (
            patch(
                "webscrape.trafilatura.fetch_url",
                side_effect=[
                    "<a href='/humanidades/ciencias/sem-data'>Article</a>",
                    "<h1>Notícia sem data</h1><html>article</html>",
                ],
            ),
            patch(
                "webscrape.trafilatura.extract_metadata",
                return_value=metadata,
            ),
            patch(
                "webscrape.trafilatura.extract",
                return_value="Conteúdo da notícia",
            ),
        ):
            articles = json.loads(ScrapeWeb("https://unbciencia.unb.br/").scrape_data())

        self.assertEqual(articles[0]["published"], "")

    def test_rejects_non_positive_article_limit(self) -> None:
        with self.assertRaises(ValueError):
            ScrapeWeb("https://noticias.unb.br/", max_articles=0)


if __name__ == "__main__":
    unittest.main()
