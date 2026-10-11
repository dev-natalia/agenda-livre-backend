# Quickstart: validar Consulta Pública de Atividades

Pré-requisitos: features 001 a 005 funcionando (`.env` preenchido, `create_admin` e `seed_catalog`
executados, migrations aplicadas). Esta feature não cria migrations.

## 1. Testes e estilo

```bash
pytest          # sem banco, cobertura >= 90%
ruff check .
python manage.py makemigrations --check --dry-run
```

Esperado: todos os testes passam, cobertura de 90% ou mais, nenhum aviso do `ruff` e nenhuma migration
pendente.

## 2. Preparar dados no painel

Com `DJANGO_DEBUG=true` e `CORS_ALLOWED_ORIGINS` contendo a origem do frontend (por exemplo
`http://localhost:5500`), rode `python manage.py runserver`. Em `/admin/` crie, em duas unidades e
categorias diferentes:

1. Uma atividade **publicada** com programação **recorrente** (terça e quinta, período que cubra hoje) e
   link externo `https://exemplo.org/inscricao`.
2. Uma atividade **publicada** com programação **pontual** em data futura.
3. Uma atividade **publicada sem programações**.
4. Uma atividade em **rascunho**, uma **cancelada** e uma **encerrada**, cada uma com o termo "dança" no
   título e programações futuras.

## 3. Conferir a API (sem login)

Use `curl` ou o navegador. Contrato em `contracts/public-api.md`.

| # | Requisição | Esperado |
|---|---|---|
| 1 | `GET /api/v1/activities/` | Só as 3 publicadas; as com ocorrência primeiro (mais cedo antes), a sem programação por último; `next_occurrence` preenchida ou `null`; nenhum campo de auditoria |
| 2 | `GET /api/v1/activities/?page_size=1` e `?page=2&page_size=1` | `count: 3`, `next`/`previous` coerentes; `page_size=500` é limitado a 50 |
| 3 | `GET /api/v1/activities/?q=danca` (e `?q=DANÇA`) | Só publicadas com o termo; nenhuma de rascunho, cancelada ou encerrada |
| 4 | `GET /api/v1/activities/?q=` | Mesma lista do item 1 |
| 5 | `GET /api/v1/activities/?q=` + 101 caracteres | `400` com `errors.q` |
| 6 | `?unit=<id>`, `?category=<id>`, `?neighborhood=grajau` | Só as atividades correspondentes |
| 7 | `?unit=abc` e `?unit=<uuid inexistente>` | `400` com `errors.unit`; lista vazia |
| 8 | `?date=<próxima terça>` | A recorrente; não a pontual (a menos que a data coincida) |
| 9 | `?date=<quarta>` e `?date=<ontem>` | Lista vazia |
| 10 | `?date_from=<hoje>&date_to=<hoje+30d>` | Atividades com ocorrência na janela; `next_occurrence` é a primeira dentro dela |
| 11 | `?date_from=2026-12-31&date_to=2026-12-01`; `?date=2026-12-01&date_to=2026-12-05`; `?date_from=2026-01-01&date_to=2027-12-31` | `400` com mensagem de cada regra |
| 12 | Combinar `q` + `unit` + `category` + `date` | Só atividades que atendem a todos; remover um critério amplia o resultado |
| 13 | `GET /api/v1/activities/<id da publicada recorrente>/` | Detalhe completo: unidade com endereço, públicos, link externo, `schedules` com `weekday_names`, até 5 `next_occurrences` |
| 14 | Detalhe de rascunho, cancelada, encerrada, UUID inexistente e `abc` | O mesmo `404` `{"detail": "Não encontrado."}` nos cinco casos |
| 15 | Detalhe da atividade sem link ou com valor sem `http(s)` | `external_registration_url: null` |
| 16 | `GET /api/v1/units/` e `/api/v1/categories/` | Só os ativos, em ordem alfabética; desative uma categoria com atividade publicada: some da lista, mas a atividade continua com ela no detalhe |
| 17 | `POST`, `PUT`, `PATCH`, `DELETE` em `/api/v1/activities/` | `405`, nenhum dado alterado |
| 18 | Qualquer `GET` com `Authorization: Basic inválido` | Resposta normal (anônima) |
| 19 | `GET /api/v1/activities/` com `Origin: http://localhost:5500` | Cabeçalho `Access-Control-Allow-Origin` presente; origem não listada, ausente |
| 20 | Comparar `next_occurrence` do item 1 com "Próximas ocorrências" da atividade no `/admin/` | Idênticas |

## 4. Desempenho (SC-006)

Com cerca de 1.000 atividades publicadas (por exemplo, criadas por um *script* local no Admin ou
shell), `GET /api/v1/activities/?q=…&date_from=…&date_to=…` deve responder em menos de 2 s na máquina
local; conferir também que o número de consultas ao banco não cresce com o tamanho da página (3
consultas de atividades, mais 1 de contagem se aplicável).

## Resultado da validação automatizada

2026-10-11: `pytest` com 421 testes passando e cobertura de 100%; `ruff check .` sem avisos; `makemigrations --check --dry-run` sem pendências. 

Roteiro manual (2026-10-11, servidor local contra o RDS, com dados `[TESTE-006]` criados e removidos depois): as 20 linhas da seção 3 deram o resultado esperado. Desempenho (seção 4): 3 consultas ao banco por requisição, independente do tamanho da página; resposta em cerca de 0,3 s com poucos registros. A carga de 1.000 atividades não foi testada.
