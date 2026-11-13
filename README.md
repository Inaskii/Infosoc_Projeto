# VeriUnB

Aplicação desktop do **VeriUnB — Verificador de Notícias da UnB**, criada
com Tkinter e baseada na identidade visual fornecida.

## Requisitos

- Python 3.10 ou superior
- Tkinter (em distribuições Debian/Ubuntu: `sudo apt install python3-tk`)

As fontes Montserrat e Inter são usadas quando instaladas no sistema. Caso não estejam
disponíveis, o Tkinter utiliza automaticamente uma fonte substituta, sem impedir a execução.

## Executar

```bash
python3 main.py
```

As fontes exibidas são carregadas temporariamente para a sessão, permitindo demonstrar
a inclusão e remoção de links sem depender de um serviço externo. A classe
`VerificationService` concentra a lógica de verificação e pode ser conectada a uma API
ou modelo de IA.

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
