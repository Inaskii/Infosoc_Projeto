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

As fontes exibidas são carregadas de `scrape_urls.json`; inclusões e remoções pela tela
de fontes são persistidas nesse arquivo. A classe `VerificationService` oferece análise
de notícias com IA via OpenRouter.

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

O RAG usa a API de embeddings do OpenRouter com os modelos
`nvidia/nemotron-3.5-embed-1b:free` e
`nvidia/nemotron-3.5-embed-8b:free`. Os modelos podem ser configurados com a
variável opcional `OPENROUTER_EMBED_MODEL`.

O método `VerificationService.verify(question)` busca notícias no banco, gera ou reutiliza
embeddings do campo `content`, compara-os com o embedding da pergunta e envia as fontes
mais relevantes ao OpenRouter para gerar uma resposta. A tela do verificador exibe essa
resposta e as fontes utilizadas. `VerificationService.analyze_claim_with_ai(claim_text,
sources_context="")` continua disponível para análise estruturada de afirmações, e
`VerificationService.summarize_news_item(article_text)` retorna um resumo em texto.

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
Ao iniciar, a aplicação lê as URLs de `scrape_urls.json` e coleta os feeds em
uma thread separada. Cada URL da lista é processada; a interface permanece
responsiva e atualiza o feed ao final da coleta.

Exemplo de uso:

```python
from database import NewsDatabase
from webscrape import Scrape, load_scrape_sources

database = NewsDatabase()
for source in load_scrape_sources():
    scraper = Scrape(
        source["url"],
        max_articles=5,
        source_name=source["name"],
    )
    database.save_news(scraper.scrape_data())

noticias = database.get_news()
```

`scrape_urls.json` deve conter uma lista de fontes com `name` e `url`:

```json
[
  {
    "name": "Portal de Notícias da UnB",
    "url": "https://noticias.unb.br/?format=feed&type=rss"
  }
]
```

## Telas

- **Feed de notícias:** cartões com resumo, selo de verificação e abertura da matéria no navegador.
- **Perguntas sobre notícias:** entrada multilinha, resposta baseada nas notícias salvas e fontes utilizadas.
- **Fontes de notícias:** links iniciais, inclusão com validação de URL e remoção confirmada.

## Estrutura do projeto

```text
Infosoc_Projeto/
├── main.py
├── services.py
├── storage.py
├── theme.py
├── requirements.txt
├── logo.png
├── logofundoazul.png
├── README.md
├── Identidade Visual – Verificador de Notícias UnB.pdf
├── Identidade Visual – Verificador de Notícias UnB.txt
└── Final_InfoSoc-2.pdf
```

## O que cada arquivo faz

| Arquivo | Responsabilidade |
|---|---|
| [`main.py`](main.py) | Ponto de entrada da aplicação. Cria a janela principal com Tkinter, monta o menu lateral e as três telas, coordena a navegação e registra os componentes de interface. |
| [`services.py`](services.py) | Contém a lógica de RAG separada da interface: `VerificationService` recupera notícias relevantes e `VerificationResult` representa a resposta e suas fontes. |
| [`storage.py`](storage.py) | Implementa persistência local de fontes em JSON em `~/.veriunb/sources.json`. Também oferece carregamento, salvamento e validação de URLs com os esquemas `http` e `https`. |
| [`theme.py`](theme.py) | Centraliza as cores, as famílias de fontes e os estilos Tkinter/ttk usados pela interface. |
| [`requirements.txt`](requirements.txt) | Lista as dependências externas do projeto. Atualmente o código utiliza apenas bibliotecas padrão do Python. |
| [`logo.png`](logo.png) | Logotipo claro exibido no cabeçalho das telas. |
| [`logofundoazul.png`](logofundoazul.png) | Versão do logotipo exibida sobre a barra lateral azul. |
| [`Identidade Visual – Verificador de Notícias UnB.pdf`](Identidade%20Visual%20%E2%80%93%20Verificador%20de%20Noti%CC%81cias%20UnB.pdf) | Guia visual da identidade da interface em formato PDF. |
| [`Identidade Visual – Verificador de Notícias UnB.txt`](Identidade%20Visual%20%E2%80%93%20Verificador%20de%20Noti%CC%81cias%20UnB.txt) | Texto auxiliar com orientações e informações da identidade visual. |
| [`Final_InfoSoc-2.pdf`](Final_InfoSoc-2.pdf) | Documento final relacionado ao projeto. |

## Organização da interface

O fluxo principal começa em `main.py`, na classe `App`, que cria uma instância de
`VerificationService` e monta as telas `FeedScreen`, `VerifierScreen` e `SourcesScreen`.
A classe `BaseScreen` define o cabeçalho comum das telas.

- **Feed:** exibe as notícias do banco `news.db`, preenchido em segundo plano a partir das fontes de `scrape_urls.json`, e abre o endereço da matéria com `webbrowser`.
- **Verificador:** envia o texto para `VerificationService` em uma thread separada e atualiza a interface com o resultado recebido.
- **Fontes:** `SourceDialog` coleta os dados, `SourceStorage.is_valid_url` valida os URLs e adições e remoções são salvas em `scrape_urls.json`.
