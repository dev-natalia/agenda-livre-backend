# Quickstart: validar Páginas Informativas (Sobre e Contato)

## Pré-requisitos

- Ambiente virtual (`.venv`) com `requirements-dev.txt` instalado e `.env` conforme o README.
- Os testes não acessam banco; só o cenário 2 precisa do servidor local.

## 1. Suíte automatizada (principal)

```bash
python -m pytest
```

Esperado: todos os testes passam e a cobertura total fica em 90% ou mais. Filtros úteis:
`tests/unit/core/test_no_informational_pages.py` e `tests/unit/core/test_error_views.py`.

```bash
python manage.py makemigrations --check --dry-run   # esperado: "No changes detected"
python -m ruff check .                               # esperado: sem erros
```

## 2. Envio de contato à API (servidor local)

```bash
curl -i -X POST http://localhost:8000/api/contato/ -d "mensagem=teste"
curl -i http://localhost:8000/api/sobre/
```

Esperado: `404`, `Content-Type: application/json`, corpo `{"detail": "Não encontrado."}` (e **não** 403 HTML
de CSRF). Conferir que `logs/agenda-livre.log` não ganhou linha com "teste".

## 3. Documentação

Conferir que o DOC-05, o README e o DOC-04 respondem às três perguntas de escopo de
[contracts/no-informational-endpoints.md](contracts/no-informational-endpoints.md) e que
`docs/PENDENCIAS.md` não tem item aberto de Sobre/Contato.
