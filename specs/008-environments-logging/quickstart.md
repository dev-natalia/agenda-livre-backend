# Quickstart: validar Ambientes e Registro de Erros

## Pré-requisitos

- Ambiente virtual com `requirements-dev.txt` instalado e `.env` conforme o README.
- Os testes não acessam banco nem escrevem em `logs/`; só os cenários 2 a 4 precisam do servidor local.

## 1. Suíte automatizada (principal)

```bash
python -m pytest
```

Esperado: todos os testes passam e a cobertura total fica em 90% ou mais. Filtros úteis:
`tests/unit/config` e `tests/unit/core`.

```bash
python manage.py makemigrations --check --dry-run   # esperado: "No changes detected"
python -m ruff check .                               # esperado: sem erros
```

## 2. Falha inesperada chega ao arquivo (servidor local)

Com `DJANGO_DEBUG=False` e `DJANGO_HTTPS_ONLY=False`, provoque uma falha (por exemplo, derrubando o
acesso de rede ao banco) e chame a API:

```bash
curl -i http://localhost:8000/api/v1/activities/
tail -n 30 logs/agenda-livre.log
```

Esperado: a resposta traz só a mensagem genérica (500); o arquivo mostra uma linha `ERROR` com método,
caminho e rastreamento, sem senha do banco nem chave secreta.

## 3. Erros de cliente não entram

```bash
curl -i http://localhost:8000/api/v1/activities/?page=abc   # 400
curl -i http://localhost:8000/api/v1/rota-inexistente        # 404
```

Esperado: nenhuma linha nova em `logs/agenda-livre.log`.

## 4. Inicialização com variável ausente

Remova `DB_HOST` do ambiente e rode `python manage.py check`.

Esperado: o comando falha informando `DB_HOST`; o arquivo de registro ganha uma linha `ERROR` com o
nome da variável e nenhum valor. Restaure `DB_HOST`.

## 5. Modo restritivo

Com `DJANGO_DEBUG=False` e sem `DJANGO_HTTPS_ONLY`:

```bash
python manage.py check --deploy
```

Esperado: sem avisos de redirecionamento HTTPS, cookies seguros ou HSTS. Com `DJANGO_DEBUG=True`, as
proteções de transporte ficam desligadas e o painel funciona em HTTP.

## 6. Documentação e escopo

- README: variáveis novas, local dos registros e lista do que está fora do escopo.
- DOC-04: US-032 e US-033 fora do escopo, US-034 "registro básico local", EP-09 só frontend.
- `git ls-files | grep -E "^\.env$|^logs/"` não devolve nada.
