# Contrato: API pública de consulta

Base: `/api/v1/`. Somente `GET`; sem autenticação (credenciais enviadas são ignoradas). Qualquer outro
método responde `405`. JSON em UTF-8. Datas `YYYY-MM-DD`, horários `HH:MM`, dias da semana 1 (segunda) a
7 (domingo). Nenhuma resposta traz dados de auditoria ou de contas.

## Paginação (listas)

Parâmetros: `page` (inteiro >= 1, padrão 1) e `page_size` (padrão 12, máximo 50; inválido ou < 1 usa o
padrão, acima do máximo é limitado a 50). Envelope:

```json
{ "count": 27, "next": "http://host/api/v1/activities/?page=2", "previous": null, "results": [] }
```

Página fora do intervalo: `404` com o erro padrão. Lista vazia: `200` com `count: 0`.

## Erros

```json
{ "detail": "Parâmetros inválidos.", "errors": { "date_from": ["Informe uma data no formato AAAA-MM-DD."] } }
```

`errors` só aparece em `400`. Outros erros trazem só `detail` (`404`: "Não encontrado."; `405`: "Método
não permitido."). Nunca incluem rastros, caminhos ou consultas.

## `GET /api/v1/activities/`

Atividades `PUBLISHED`, com busca e filtros combináveis (todos opcionais, critério "E").

| Parâmetro | Tipo | Regra |
|---|---|---|
| `q` | texto | Busca em título, resumo e descrição, sem caixa e sem acento. Vazio ou só espaços é ignorado. Mais de 100 caracteres: `400`. |
| `unit` | UUID | Atividades da unidade. UUID malformado: `400`; inexistente: lista vazia. |
| `neighborhood` | texto | Bairro da unidade, igualdade sem caixa e sem acento. Máx. 100 caracteres. |
| `category` | UUID | Idem `unit`. |
| `date` | data | Atividades com ocorrência nesse dia. Não combina com `date_from`/`date_to` (`400`). |
| `date_from` | data | Início da janela (inclusive). Sozinho: dessa data em diante. |
| `date_to` | data | Fim da janela (inclusive). Sozinho: de hoje até essa data. |
| `page`, `page_size` | inteiros | Ver paginação. |

Regras de data: apenas ocorrências ainda não encerradas, de hoje em diante, no fuso `America/Sao_Paulo`.
Janela inteira no passado: lista vazia. `date_from` > `date_to` ou intervalo (com os dois) acima de 366
dias: `400`. Parâmetros desconhecidos são ignorados.

Ordem: por data da próxima ocorrência (com filtro de data, da primeira ocorrência na janela), depois
horário de início e título; atividades sem ocorrência ficam ao final, por título.

Item de `results`:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440001",
  "title": "Oficina de dança",
  "slug": "oficina-de-danca",
  "summary": "Atividade aberta à comunidade.",
  "unit": { "id": "…", "name": "CEU Navegantes", "slug": "ceu-navegantes", "neighborhood": "Grajaú" },
  "category": { "id": "…", "name": "Cultura e Artes", "slug": "cultura-e-artes" },
  "next_occurrence": { "date": "2026-11-20", "start_time": "14:00", "end_time": "15:00" }
}
```

`next_occurrence` é `null` quando não há ocorrência futura (ou, com filtro de data, na janela).

## `GET /api/v1/activities/{id}/`

`{id}` é o UUID da atividade. Atividade inexistente, identificador malformado ou atividade que não esteja
`PUBLISHED`: o mesmo `404` (`{"detail": "Não encontrado."}`).

```json
{
  "id": "…", "title": "Oficina de dança", "slug": "oficina-de-danca",
  "summary": "…", "description": "Descrição completa.", "target_audience_notes": "Iniciantes são bem-vindos.",
  "unit": { "id": "…", "name": "CEU Navegantes", "slug": "ceu-navegantes", "address": "…", "neighborhood": "Grajaú" },
  "category": { "id": "…", "name": "Cultura e Artes", "slug": "cultura-e-artes" },
  "target_audiences": [{ "id": "…", "name": "Adultos" }],
  "external_registration_url": null,
  "schedules": [
    {
      "id": "…", "schedule_type": "RECURRING",
      "start_date": "2026-11-01", "end_date": "2026-12-31",
      "start_time": "14:00", "end_time": "15:00",
      "weekdays": [2, 4], "weekday_names": ["Terça-feira", "Quinta-feira"]
    }
  ],
  "next_occurrences": [{ "date": "2026-11-03", "start_time": "14:00", "end_time": "15:00" }]
}
```

- `external_registration_url`: o valor só quando for `http://` ou `https://`; senão `null`. O link leva
  para fora do Agenda Livre, que não coleta nem processa inscrições; o frontend deve indicar a saída.
- `schedule_type`: `ONE_TIME` ou `RECURRING`. Em `ONE_TIME`, `weekdays` e `weekday_names` são listas
  vazias e `start_date` = `end_date`.
- `schedules` ordenadas por `start_date`; `next_occurrences` traz até 5, em ordem cronológica, vazia sem
  datas futuras.

## `GET /api/v1/units/` e `GET /api/v1/categories/`

Apenas registros ativos, ordenados por nome, no envelope paginado.

Unidade: `{ "id", "name", "slug", "neighborhood", "address", "description" }`.
Categoria: `{ "id", "name", "slug", "description" }`.
`description` vazio é `null`. Sem endpoints de detalhe nesta versão.

## CORS

As rotas seguem a configuração global (`CORS_ALLOWED_ORIGINS`): origem autorizada recebe
`Access-Control-Allow-Origin`; as demais, não.

## Mapa spec → contrato

| Requisito | Onde |
|---|---|
| FR-001, FR-017 | Somente `GET`, sem autenticação, `405` nos demais métodos |
| FR-002, FR-007 | Filtro `PUBLISHED`; `404` uniforme no detalhe |
| FR-003, FR-005 | Item da listagem; ordem |
| FR-004 | Paginação |
| FR-006, FR-016 | Detalhe; `external_registration_url` |
| FR-008 | Nenhum campo de auditoria ou de conta |
| FR-009 | Unidades e categorias ativas |
| FR-010, FR-011 | `q` |
| FR-012, FR-015 | `unit`, `neighborhood`, `category`; critério "E" |
| FR-013, FR-014 | `date`, `date_from`, `date_to` |
| FR-018 | Mesmo serviço de ocorrências (ver `occurrences-service.md`) |
| FR-019 | Formato de erro |
| FR-020 | CORS |
