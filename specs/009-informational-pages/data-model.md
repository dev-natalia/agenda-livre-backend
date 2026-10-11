# Data Model: Páginas Informativas (Sobre e Contato)

**Esta feature não altera o modelo de dados.** Nenhuma tabela, coluna, índice ou migration é criada.

## Entidades que NÃO existem (por decisão de escopo)

| Entidade | Motivo da ausência |
|---|---|
| Mensagem de contato | A página de contato é demonstrativa: não envia nem armazena mensagens (US-035). Armazená-las coletaria dados pessoais de visitantes sem previsão no escopo. |
| Conteúdo da página Sobre | O texto é fixo no frontend (US-036). |

## Verificação

- `python manage.py makemigrations --check --dry-run` deve responder "No changes detected".
- O teste `tests/unit/core/test_no_informational_pages.py` percorre `django.apps.apps.get_models()` e falha
  se algum modelo tiver nome ligado a contato, Sobre ou mensagem.
