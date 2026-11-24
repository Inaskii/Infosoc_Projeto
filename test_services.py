"""Focused tests for question answering with the RAG service."""

from __future__ import annotations

import unittest
from unittest.mock import Mock, call, patch

from services import VerificationService


class VerificationServiceTests(unittest.TestCase):
    def test_verify_embeds_article_content_and_question_then_returns_answer(self) -> None:
        database = Mock()
        database.get_news.return_value = [
            {
                "url": "https://example.test/a",
                "title": "Notícia A",
                "published": "2026-01-01",
                "content": "Conteúdo A",
            },
            {
                "url": "https://example.test/b",
                "title": "Notícia B",
                "published": "2026-01-02",
                "content": "Conteúdo B",
            },
            {"url": "https://example.test/empty", "content": "  "},
        ]
        database.get_embeddings.return_value = []
        embedding_service = Mock()
        embedding_service.model = "test-embedding-model"
        embedding_service.embed.side_effect = [
            [1.0, 0.0],
            [0.0, 1.0],
            [0.0, 1.0],
        ]
        service = VerificationService(database, embedding_service)

        with patch("services.ask_llm", return_value="Resposta gerada") as ask_llm:
            result = service.verify("Qual é a notícia mais recente?")

        self.assertIsNone(result.verdict)
        self.assertEqual(result.explanation, "Resposta gerada")
        self.assertEqual(
            result.sources,
            (
                "Notícia B — https://example.test/b",
                "Notícia A — https://example.test/a",
            ),
        )
        self.assertEqual(
            embedding_service.embed.call_args_list,
            [
                call("Conteúdo A", input_type="passage"),
                call("Conteúdo B", input_type="passage"),
                call("Qual é a notícia mais recente?", input_type="query"),
            ],
        )
        database.save_embedding.assert_has_calls(
            [
                call("https://example.test/a", [1.0, 0.0], "test-embedding-model"),
                call("https://example.test/b", [0.0, 1.0], "test-embedding-model"),
            ]
        )
        prompt = ask_llm.call_args.args[0]
        self.assertIn("Qual é a notícia mais recente?", prompt)
        self.assertIn("[Fonte 1] Notícia B", prompt)
        self.assertNotIn("https://example.test/empty", prompt)

    def test_verify_reuses_saved_embeddings_when_content_and_model_match(self) -> None:
        article = {
            "url": "https://example.test/a",
            "title": "Notícia A",
            "published": "2026-01-01",
            "content": "Conteúdo A",
        }
        database = Mock()
        database.get_news.return_value = [article]
        database.get_embeddings.return_value = [
            {
                **article,
                "embedding": [1.0, 0.0],
                "model": "test-embedding-model",
            }
        ]
        embedding_service = Mock()
        embedding_service.model = "test-embedding-model"
        embedding_service.embed.return_value = [1.0, 0.0]
        service = VerificationService(database, embedding_service)

        with patch("services.ask_llm", return_value="Resposta gerada"):
            result = service.verify("Pergunta")

        self.assertEqual(result.explanation, "Resposta gerada")
        embedding_service.embed.assert_called_once_with("Pergunta", input_type="query")
        database.save_embedding.assert_not_called()


if __name__ == "__main__":
    unittest.main()
