import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree

SCRAPE_URLS_PATH = Path(__file__).resolve().with_name("scrape_urls.json")


def load_scrape_sources(path: str | Path = SCRAPE_URLS_PATH) -> list[dict[str, str]]:
    """Load and validate source names and RSS/Atom feed URLs from JSON."""
    with Path(path).open(encoding="utf-8") as file:
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


class _ArticleContentParser(HTMLParser):
    """Extrai texto de parágrafos da área principal de uma página HTML."""

    _CONTENT_TAGS = {"article", "main"}
    _IGNORED_TAGS = {"script", "style", "noscript", "svg", "nav", "footer", "header"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._ignored_depth = 0
        self._paragraph: list[str] | None = None
        self.paragraphs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in self._IGNORED_TAGS:
            self._ignored_depth += 1
        elif tag == "p" and not self._ignored_depth:
            self._paragraph = []

    def handle_endtag(self, tag: str) -> None:
        if tag in self._IGNORED_TAGS and self._ignored_depth:
            self._ignored_depth -= 1
        elif tag == "p" and self._paragraph is not None:
            text = self._normalize(" ".join(self._paragraph))
            if text:
                self.paragraphs.append(text)
            self._paragraph = None

    def handle_data(self, data: str) -> None:
        if self._paragraph is not None and not self._ignored_depth:
            self._paragraph.append(data)

    @staticmethod
    def _normalize(text: str) -> str:
        text = re.sub(r"\s+", " ", text).strip()
        return re.sub(r"\s+([,.;:!?])", r"\1", text)


class Scrape:
    def __init__(
        self,
        url: str,
        max_articles: int = 20,
        *,
        source_name: str | None = None,
    ):
        if max_articles < 1:
            raise ValueError("O limite de notícias deve ser maior que zero.")
        self.url = url
        self.max_articles = max_articles
        self.source_name = source_name

    def scrape_data(self) -> str:
        """Coleta todas as notícias do feed e retorna um JSON."""
        if not self.url:
            print("URL não fornecida. Nenhum dado será raspado.")
            return "[]"

        request = Request(self.url, headers={"User-Agent": "VeriUnB/1.0"})
        with urlopen(request, timeout=15) as response:
            feed = ElementTree.fromstring(response.read())

        channel = self._find_element(feed, "channel")
        feed_source = self.source_name or (
            self._find_text(channel, "title") if channel is not None else ""
        ) or self._find_text(feed, "title") or self.url
        articles = []
        for item in self._entries(feed)[: self.max_articles]:
            article_url = self._find_text(item, "link")
            if not article_url:
                # Atom stores the URL as an attribute on the link element.
                link = self._find_element(item, "link")
                article_url = link.get("href", "") if link is not None else ""

            if not article_url:
                continue

            content = self._fetch_article_content(article_url)
            articles.append(
                {
                    "title": self._find_text(item, "title") or "Sem título",
                    "url": article_url,
                    "published": (
                        self._find_text(item, "pubDate")
                        or self._find_text(item, "published")
                        or self._find_text(item, "updated")
                        or datetime.now(timezone.utc).isoformat()
                    ),
                    "source": feed_source,
                    "summary": (
                        self._find_text(item, "description")
                        or self._find_text(item, "summary")
                        or ""
                    ),
                    "content": content,
                }
            )

        return json.dumps(articles, ensure_ascii=False, indent=2)

    @staticmethod
    def _fetch_article_content(article_url: str) -> str:
        request = Request(article_url, headers={"User-Agent": "VeriUnB/1.0"})
        try:
            with urlopen(request, timeout=15) as response:
                parser = _ArticleContentParser()
                charset = response.headers.get_content_charset() or "utf-8"
                parser.feed(response.read().decode(charset, errors="replace"))
        except (HTTPError, URLError, TimeoutError, ValueError) as error:
            print(f"Não foi possível coletar o conteúdo de {article_url}: {error}")
            return ""

        return "\n\n".join(parser.paragraphs)

    @staticmethod
    def _entries(feed: ElementTree.Element) -> list[ElementTree.Element]:
        """Retorna itens RSS ou entradas Atom, independentemente do namespace."""
        return [
            element
            for element in feed.iter()
            if Scrape._local_name(element.tag) in {"item", "entry"}
        ]

    @staticmethod
    def _find_element(
        parent: ElementTree.Element, name: str
    ) -> ElementTree.Element | None:
        for element in parent.iter():
            if Scrape._local_name(element.tag) == name:
                return element
        return None

    @staticmethod
    def _find_text(parent: ElementTree.Element, name: str) -> str:
        element = Scrape._find_element(parent, name)
        return "".join(element.itertext()).strip() if element is not None else ""

    @staticmethod
    def _local_name(tag: str) -> str:
        return tag.rsplit("}", 1)[-1]


if __name__ == "__main__":
    for source in load_scrape_sources():
        scraper = Scrape(source["url"], max_articles=5, source_name=source["name"])
        print(scraper.scrape_data())
