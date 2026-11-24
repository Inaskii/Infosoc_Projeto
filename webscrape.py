import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlparse

import trafilatura

from app_paths import ensure_scrape_urls_file


def load_scrape_sources(path: str | Path | None = None) -> list[dict[str, str]]:
    """Load and validate source names and homepage URLs from JSON."""
    source_path = (
        ensure_scrape_urls_file() if path is None else Path(path)
    )
    with source_path.open(encoding="utf-8") as file:
        sources = json.load(file)

    if not isinstance(sources, list):
        raise ValueError("scrape_urls.json deve conter uma lista de fontes.")

    validated_sources = []
    names = set()
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("Cada fonte deve ser um objeto com name e url.")
        name = source.get("name")
        url = source.get("url")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Cada fonte deve ter um name não vazio.")
        if not isinstance(url, str) or not url.strip():
            raise ValueError("Cada fonte deve ter uma URL não vazia.")
        name = name.strip()
        url = url.strip()
        if name in names:
            raise ValueError(f"O nome da fonte está duplicado: {name}")
        parsed_url = urlparse(url)
        if parsed_url.scheme not in {"http", "https"} or not parsed_url.netloc:
            raise ValueError(f"URL de scraping inválida: {url}")
        names.add(name)
        validated_sources.append({"name": name, "url": url})

    return validated_sources


class _LinkParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag != "a":
            return
        href = next((value for name, value in attrs if name == "href"), None)
        if href:
            self.links.append(href)


class _ArticleTitleParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._active_tag: str | None = None
        self._active_rank = 0
        self._parts: list[str] = []
        self._title_rank = 0
        self.semantic_title_count = 0
        self.title = ""

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if self._active_tag or tag not in {"h1", "h2"}:
            return
        attributes = dict(attrs)
        self._active_tag = tag
        if tag == "h2" and "name" in (attributes.get("itemprop") or "").split():
            self._active_rank = 3
        else:
            self._active_rank = 2 if tag == "h1" else 1

    def handle_endtag(self, tag: str) -> None:
        if tag != self._active_tag:
            return
        title = " ".join(" ".join(self._parts).split())
        if title and self._active_rank == 3:
            self.semantic_title_count += 1
        if title and self._active_rank > self._title_rank:
            self.title = title
            self._title_rank = self._active_rank
        self._active_tag = None
        self._parts.clear()

    def handle_data(self, data: str) -> None:
        if self._active_tag:
            self._parts.append(data)


class ScrapeWeb:
    def __init__(
        self,
        url: str,
        max_articles: int = 10,
        *,
        source_name: str | None = None,
    ) -> None:
        if max_articles < 1:
            raise ValueError("O limite de notícias deve ser maior que zero.")
        self.url = url
        self.max_articles = max_articles
        self.source_name = source_name

    def scrape_data(self) -> str:
        """Coleta notícias encontradas na homepage e retorna um JSON."""
        if not self.url:
            print("URL não fornecida. Nenhum dado será raspado.")
            return "[]"

        homepage = trafilatura.fetch_url(self.url)
        if not homepage:
            print(f"Não foi possível acessar a homepage: {self.url}")
            return "[]"

        parser = _LinkParser()
        parser.feed(homepage)
        base_url = urlparse(self.url)
        site_host = base_url.hostname
        article_urls: dict[int, list[str]] = {2: [], 3: []}
        seen_urls = {urldefrag(self.url).url}
        for href in parser.links:
            article_url = urldefrag(urljoin(self.url, href)).url
            if not self._is_article_url(article_url, site_host):
                continue
            parsed_url = urlparse(article_url)
            article_url = f"https://{site_host}{parsed_url.path.rstrip('/')}"
            if article_url in seen_urls:
                continue
            seen_urls.add(article_url)
            segment_count = len(parsed_url.path.strip("/").split("/"))
            article_urls[segment_count].append(article_url)

        articles = []
        for segment_count in (2, 3):
            for article_url in article_urls[segment_count]:
                if len(articles) >= self.max_articles:
                    break

                downloaded = trafilatura.fetch_url(article_url)
                if not downloaded:
                    continue

                title_parser = _ArticleTitleParser()
                title_parser.feed(downloaded)
                if title_parser.semantic_title_count > 1:
                    continue

                metadata = trafilatura.extract_metadata(
                    downloaded,
                    default_url=article_url,
                )
                content = trafilatura.extract(
                    downloaded,
                    url=article_url,
                    include_comments=False,
                    include_tables=False,
                    include_images=False,
                    include_links=False,
                    favor_precision=True,
                )
                if not content:
                    continue

                paragraphs = content.strip().splitlines()
                title = (
                    title_parser.title
                    or getattr(metadata, "title", None)
                    or "Sem título"
                )
                articles.append(
                    {
                        "title": title,
                        "url": article_url,
                        "published": getattr(metadata, "date", None) or "",
                        "source": (
                            self.source_name
                            or getattr(metadata, "sitename", None)
                            or base_url.netloc
                        ),
                        "summary": paragraphs[0] if paragraphs else "",
                        "content": content,
                    }
                )

        return json.dumps(articles, ensure_ascii=False, indent=2)

    @staticmethod
    def _is_article_url(url: str, site_host: str | None) -> bool:
        parsed_url = urlparse(url)
        host = parsed_url.hostname
        path = parsed_url.path.strip("/")
        path_parts = path.split("/") if path else []
        is_unb_host = bool(host and (host == "unb.br" or host.endswith(".unb.br")))
        return (
            parsed_url.scheme == "https"
            and host == site_host
            and is_unb_host
            and host is not None
            and parsed_url.netloc.lower() in {host, f"{host}:443"}
            and len(path_parts) in {2, 3}
            and all(path_parts)
        )


if __name__ == "__main__":
    scraper = ScrapeWeb(
        "https://unbciencia.unb.br/",
        max_articles=20,
        source_name="UnB Ciência",
    )
    print(scraper.scrape_data())