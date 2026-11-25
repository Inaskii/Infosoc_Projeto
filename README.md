# VeriUnB

Aplicação desktop do **VeriUnB — Verificador de Notícias da UnB**, criada
com Tkinter e baseada na identidade visual fornecida.

## Instalação no Debian/Ubuntu

1. Baixe o pacote `veriunb_1.0.0_amd64.deb`.
2. Abra um terminal na pasta em que o arquivo foi baixado.
3. Execute o comando:

   ```bash
   sudo apt install ./veriunb_1.0.0_amd64.deb
   ```

4. Crie a pasta de dados do usuário e abra o arquivo `.env`:

   ```bash
   mkdir -p ~/.local/share/veriunb
   nano ~/.local/share/veriunb/.env
   ```

5. Adicione a linha abaixo, substituindo o valor de exemplo por uma chave
   válida da OpenRouter. Salve e feche o editor:

   ```dotenv
   OPENROUTER_API_KEY=sk-or-v1-sua-chave
   ```

6. Abra o VeriUnB pelo menu de aplicativos. A configuração das fontes é criada
   na primeira execução. Se o app já estiver aberto quando você editar o `.env`,
   o aviso vermelho sobre a chave desaparecerá automaticamente, sem fechar ou
   reiniciar o aplicativo. Não compartilhe sua chave.

Se `XDG_DATA_HOME` estiver definido no seu ambiente, os arquivos ficam em
`$XDG_DATA_HOME/veriunb/` em vez de `~/.local/share/veriunb/`.

## Uso

O aplicativo tem três telas:

- **Feed de notícias:** apresenta as 20 notícias mais recentes coletadas das
  fontes cadastradas. Use **Abrir matéria** para acessar a publicação no site
  de origem.
- **Perguntas sobre notícias (verificador de boatos):** digite uma pergunta ou
  afirmação e clique em **Perguntar**. O aplicativo consulta as notícias
  coletadas e apresenta uma resposta gerada por IA com as fontes utilizadas.
  A resposta pode ser inconclusiva se não houver evidências suficientes;
  confira as fontes antes de concluir se algo é fato ou fake.
- **Fontes de notícias:** adicione as homepages de sites oficiais de notícias da
  UnB ou remova fontes cadastradas. As fontes são usadas para coletar as
  notícias exibidas no feed.

Ao abrir o aplicativo, a coleta das notícias começa em segundo plano. É
necessário ter acesso à internet para atualizar o feed e consultar a OpenRouter.

## Arquivos de dados e chave da API

No primeiro início, o aplicativo cria `scrape_urls.json` em
`~/.local/share/veriunb/`. Se o `.env` ainda não existir, ele também cria o
arquivo com um valor de exemplo:

```dotenv
OPENROUTER_API_KEY=insira_a_chave_aqui
```

Substitua o valor de exemplo por sua chave da OpenRouter. O banco SQLite
`news.db` também é armazenado nessa pasta. Se `XDG_DATA_HOME` estiver definido,
os arquivos ficam em `$XDG_DATA_HOME/veriunb/`. O aplicativo não sobrescreve
os arquivos de configuração já existentes.

O `.env` é ignorado pelo Git. Nunca compartilhe nem versione a chave.

## Desenvolvimento

Para executar a partir do código-fonte, é necessário Python 3.10 ou superior e
Tkinter (em Debian/Ubuntu: `sudo apt install python3-tk`). Crie um ambiente
virtual e instale as dependências:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python3 main.py
```

As fontes Montserrat e Inter são usadas quando instaladas no sistema. Caso não
estejam disponíveis, o Tkinter utiliza uma fonte substituta.

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
`~/.local/share/veriunb/news.db`, criado automaticamente por `NewsDatabase`.

A tabela `news` possui os seguintes campos:

| Campo | Descrição |
| --- | --- |
| `id` | Identificador numérico da notícia |
| `url` | Endereço da notícia, único no banco |
| `title` | Título da notícia |
| `published` | Data de publicação |
| `source` | Nome da fonte de origem |
| `summary` | Resumo da notícia |
| `content` | Conteúdo completo extraído |
| `created_at` | Data de inserção no banco |
| `updated_at` | Data da última atualização |

A URL possui uma restrição de unicidade. Ao salvar uma notícia já existente, o
registro é atualizado em vez de duplicado.
Ao iniciar, a aplicação lê as homepages de `scrape_urls.json` e procura links
internos para notícias em uma thread separada. Cada homepage é processada; a
interface permanece responsiva e atualiza o feed ao final da coleta.

Exemplo de uso:

```python
from database import NewsDatabase
from webscrape import ScrapeWeb, load_scrape_sources

database = NewsDatabase()
for source in load_scrape_sources():
    scraper = ScrapeWeb(
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
    "name": "Portal UnB",
    "url": "https://noticias.unb.br/"
  },
  {
    "name": "UnB Ciência",
    "url": "https://unbciencia.unb.br/"
  }
]
```

## Telas

- **Feed de notícias:** cartões das 20 notícias mais recentes, com resumo e abertura da matéria no navegador.
- **Perguntas sobre notícias:** resposta baseada nas notícias coletadas, com indicação das fontes utilizadas.
- **Fontes de notícias:** homepages de fontes oficiais da UnB, com inclusão e remoção pelo aplicativo.

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
| [`storage.py`](storage.py) | Implementa persistência das fontes de notícias em JSON e valida URLs com os esquemas `http` e `https`. |
| [`theme.py`](theme.py) | Centraliza as cores, as famílias de fontes e os estilos Tkinter/ttk usados pela interface. |
| [`requirements.txt`](requirements.txt) | Lista as dependências externas do projeto, incluindo Trafilatura para extração de notícias. |
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
