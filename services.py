"""Business services kept separate from the Tkinter user interface."""

from dataclasses import dataclass
from typing import Literal

Verdict = Literal["Verdadeiro", "Falso", "Inconclusivo", "Erro"]


@dataclass(frozen=True)
class VerificationResult:
    verdict: Verdict
    explanation: str
    sources: tuple[str, ...] = ()


class VerificationService:
    """Demonstration adapter ready to be replaced by an API-backed verifier."""

    def verify(self, claim: str) -> VerificationResult:
        if not claim.strip():
            return VerificationResult("Erro", "Não foi possível verificar um texto vazio.")
        return VerificationResult(
            "Inconclusivo",
            "Não há evidências suficientes disponíveis para confirmar ou negar "
            "esta afirmação com segurança.",
            ("A análise precisa de fontes verificáveis para apresentar um veredito.",),
        )


DEMO_NEWS = [
    {
        "title": "Universidade de Brasília amplia ações de extensão no campus",
        "summary": "Projetos aproximam a comunidade acadêmica de iniciativas sociais e educacionais.",
        "source": "Portal UnB",
        "date": "Hoje",
        "url": "https://noticias.unb.br/",
    },
    {
        "title": "Pesquisa da UnB apresenta novos dados sobre ciência e sociedade",
        "summary": "Estudo reúne pesquisadores de diferentes áreas e destaca a importância da divulgação científica.",
        "source": "UnB Notícias",
        "date": "25 de outubro de 2026",
        "url": "https://noticias.unb.br/",
    },
    {
        "title": "Bibliotecas da UnB divulgam programação para a comunidade",
        "summary": "Confira atividades, horários e serviços disponíveis para estudantes e servidores.",
        "source": "Biblioteca Central",
        "date": "23 de outubro de 2026",
        "url": "https://bce.unb.br/",
    },
]

DEMO_SOURCES = [
    {"name": "Portal UnB", "url": "https://noticias.unb.br/"},
    {"name": "Biblioteca Central da UnB", "url": "https://bce.unb.br/"},
    {"name": "UnB Ciência", "url": "https://unbciencia.unb.br/"},
]
