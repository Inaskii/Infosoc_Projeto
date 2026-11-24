"""Teste integrado do fluxo RAG com notícias da UnB."""

from __future__ import annotations

from pathlib import Path

from database import NewsDatabase
from llm_client import ask_llm
from rag import OpenRouterEmbeddingService, vector_search
from webscrape import Scrape, load_scrape_sources


MAX_ARTICLES = 10
QUESTION = "Qual foi a última celebração realizada na UnB?"


def main() -> None:
    database = NewsDatabase(Path(__file__).with_name("news.db"))

    print("1. Coletando notícias da UnB...")
    saved = 0
    for source in load_scrape_sources():
        scraper = Scrape(
            source["url"],
            max_articles=MAX_ARTICLES,
            source_name=source["name"],
        )
        saved += database.save_news(scraper.scrape_data())
    print(f"   {saved} notícias processadas e salvas no banco.")

    news = database.get_news(limit=MAX_ARTICLES)
    if not news:
        print("Nenhuma notícia foi encontrada no banco.")
        return

    embedding_service = OpenRouterEmbeddingService()
    print(f"2. Gerando embeddings com OpenRouter ({embedding_service.model})...")

    embedded = 0
    skipped = 0
    failed = 0

    for article in news:
        url = article["url"]
        content = article.get("content")
        if not isinstance(content, str) or not content.strip():
            skipped += 1
            print(f"   Pulando {url}: campo content vazio.")
            continue

        try:
            vector = embedding_service.embed(content, input_type="passage")
            database.save_embedding(url, vector, embedding_service.model)
        except Exception as error:
            failed += 1
            print(f"   Falha ao gerar embedding para {url}: {error}")
            continue

        embedded += 1
        preview = ", ".join(f"{value:.4f}" for value in vector[:5])
        if len(vector) > 5:
            preview += ", ..."
        print(
            f"Embedding salvo para {url}: [{preview}] "
            f"({len(vector)} dimensões)."
        )

    documents = database.get_embeddings()
    if not documents:
        raise RuntimeError("Nenhum embedding foi criado. Verifique a configuração do OpenRouter.")

    print(f"3. Executando busca vetorial para: {QUESTION}")
    query_vector = embedding_service.embed(QUESTION, "query")
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
