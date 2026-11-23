# VeriUnB

Aplicação desktop do **VeriUnB — Verificador de Notícias da UnB**, criada
com Tkinter e baseada na identidade visual fornecida.

## Requisitos

- Python 3.10 ou superior
- Tkinter (em distribuições Debian/Ubuntu: `sudo apt install python3-tk`)

As fontes Montserrat e Inter são usadas quando instaladas no sistema. Caso não estejam
disponíveis, o Tkinter utiliza automaticamente uma fonte substituta, sem impedir a execução.

## Inicialização

Na pasta do projeto, crie e ative um ambiente virtual para isolar as dependências:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Atualize o gerenciador de pacotes e instale as dependências listadas em
`requirements.txt`:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Depois, execute a aplicação:

```bash
python3 main.py
```

Para desativar o ambiente virtual ao terminar:

```bash
deactivate
```

As fontes exibidas são carregadas temporariamente para a sessão, permitindo demonstrar
a inclusão e remoção de links sem depender de um serviço externo. A classe
`VerificationService` mantém o fluxo demonstrativo da tela e também oferece métodos
para análise e resumo com IA via OpenRouter.

## OpenRouter

Instale as dependências (`pip install -r requirements.txt`), copie `.env.example` para
`.env` e preencha `OPENROUTER_API_KEY` com sua chave. O arquivo `.env` é ignorado pelo
Git; nunca compartilhe nem versione a chave.

O cliente está disponível em `llm_client.py`:

```python
from llm_client import ask_llm, ask_llm_json

texto = ask_llm("Resuma este texto: ...", temperature=0.2)
dados = ask_llm_json("Retorne um objeto JSON com uma chave resumo: ...")
```

O grupo também pode usar `VerificationService.analyze_claim_with_ai(claim_text, sources_context="")`,
que retorna um `VerificationResult`, e `VerificationService.summarize_news_item(article_text)`,
que retorna um resumo em texto. A análise de afirmações é limitada às fontes passadas:
sem evidências suficientes, o resultado é inconclusivo e recomenda verificação humana.
O método existente `verify(claim)` e o fluxo atual da tela permanecem inalterados.

## Banco de dados

As notícias coletadas pelo scraper são armazenadas em um banco SQLite no arquivo
`news.db`, criado automaticamente por `NewsDatabase`.

A tabela `news` possui os seguintes campos:

| Campo | Descrição |
| --- | --- |
| `id` | Identificador numérico da notícia |
| `url` | Endereço da notícia, único no banco |
| `title` | Título da notícia |
| `published` | Data de publicação |
| `source` | Fonte ou feed de origem |
| `summary` | Resumo da notícia |
| `content` | Conteúdo completo extraído |
| `created_at` | Data de inserção no banco |
| `updated_at` | Data da última atualização |

A URL possui uma restrição de unicidade. Ao salvar uma notícia já existente, o
registro é atualizado em vez de duplicado.
O feed da aplicação carrega os registros dessa tabela; quando ela está vazia,
a tela exibe `0 notícias coletadas`.

Exemplo de uso:

```python
from database import NewsDatabase
from webscrape import Scrape

scraper = Scrape("https://noticias.unb.br/?format=feed&type=rss", max_articles=5)
database = NewsDatabase()
database.save_news(scraper.scrape_data())

noticias = database.get_news()
```

## Telas

- **Feed de notícias:** cartões com resumo, selo de verificação e abertura da matéria no navegador.
- **Verificador de boatos:** entrada multilinha, validação, processamento em thread, resultado e fontes.
- **Fontes de notícias:** links iniciais, inclusão com validação de URL e remoção confirmada.
