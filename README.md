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

## Telas

- **Feed de notícias:** cartões com resumo, selo de verificação e abertura da matéria no navegador.
- **Verificador de boatos:** entrada multilinha, validação, processamento em thread, resultado e fontes.
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
| [`services.py`](services.py) | Contém a lógica de demonstração separada da interface: `VerificationService` executa a verificação, `VerificationResult` representa o resultado e os dados de `DEMO_NEWS` e `DEMO_SOURCES` fornecem notícias e fontes de exemplo. |
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

- **Feed:** usa os dados demonstrativos de `DEMO_NEWS` e abre o endereço da matéria com `webbrowser`.
- **Verificador:** envia o texto para `VerificationService` em uma thread separada e atualiza a interface com o resultado recebido.
- **Fontes:** permite adicionar e remover fontes na sessão. `SourceDialog` coleta os dados e `SourceStorage.is_valid_url` valida os URLs.

O módulo `storage.py` contém a infraestrutura de persistência em JSON, mas a versão atual
da tela de fontes mantém os dados em memória e não chama `load()` ou `save()` durante a
execução. As alterações feitas na lista são perdidas ao fechar a aplicação.
