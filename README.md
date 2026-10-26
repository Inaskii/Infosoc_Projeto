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
