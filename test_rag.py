"""Teste integrado do fluxo RAG com notícias da UnB."""

from __future__ import annotations

from pathlib import Path

from database import NewsDatabase
from llm_client import ask_llm
from rag import OllamaEmbeddingService, vector_search
from webscrape import Scrape


NEWS_FEED_URL = "https://noticias.unb.br/?format=feed&type=rss"
MAX_ARTICLES = 10
QUESTION = "Qual foi a última celebração realizada na UnB?"


def main() -> None:
    database = NewsDatabase(Path(__file__).with_name("news.db"))
    scraper = Scrape(NEWS_FEED_URL, max_articles=MAX_ARTICLES)

    print("1. Coletando notícias da UnB...")
    news_json = scraper.scrape_data()
    saved = database.save_news(news_json)
    print(f"   {saved} notícias processadas e salvas no banco.")

    news = database.get_news(limit=MAX_ARTICLES)
    if not news:
        print("Nenhuma notícia foi encontrada no banco.")
        return

    embedding_service = OllamaEmbeddingService()
    print(f"2. Gerando embeddings com Ollama ({embedding_service.model})...")

    for article in news:
        url = article["url"]
        content = "\n".join(
            part
            for part in (
                str(article.get("title") or "").strip(),
                str(article.get("summary") or "").strip(),
                str(article.get("content") or "").strip(),
            )
            if part
        )
        if not content:
            continue

        try:
            vector = embedding_service.embed(content)
            database.save_embedding(url, vector, embedding_service.model)
        except Exception as error:
            print(f"   Falha ao gerar embedding para {article['url']}: {error}")

    documents = database.get_embeddings()
    if not documents:
        raise RuntimeError("Nenhum embedding foi criado. Verifique se o Ollama está em execução.")

    print(f"3. Executando busca vetorial para: {QUESTION}")
    query_vector = embedding_service.embed(QUESTION)
    results = vector_search(query_vector, documents, limit=5)

    context_parts = []
    for rank, (score, article) in enumerate(results, start=1):
        text = str(article.get("content") or "").strip()
        if not text:
            text = str(article.get("summary") or "").strip()
        context_parts.append(
            f"[Fonte {rank}] {article['title']}\n"
            f"Data: {article['published']}\n"
            f"URL: {article['url']}\n"
            f"Conteúdo: {text}"
        )
        print(f"   {rank}. {article['title']} (similaridade: {score:.4f})")

    context = "\n\n".join(context_parts)
    prompt = (
        "Responda à pergunta usando exclusivamente as fontes fornecidas abaixo. "
        "Informe a fonte ou URL usada e diga claramente se a informação não estiver "
        "disponível nas fontes.\n\n"
        f"Pergunta: {QUESTION}\n\n"
        f"Fontes:\n{context}"
    )

    print("4. Gerando resposta com OpenRouter...")
    answer = ask_llm(prompt, temperature=0.2)
    print(f"\nResposta:\n{answer}")


if __name__ == "__main__":
    main()
