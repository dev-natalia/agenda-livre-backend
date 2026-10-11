# Contrato: serviço de ocorrências (interno)

Interface Python em `apps/schedules/services.py`, usada pelo Admin nesta feature e pela API de
consulta pública nas próximas. Não é um endpoint.

## `Occurrence`

Dataclass imutável: `date`, `start_time`, `end_time`, `schedule_id`.

## `iter_occurrences(schedule, weekdays, from_date)`

Gera, em ordem crescente de data, as ocorrências de uma programação com data >= `from_date`.

| Parâmetro | Descrição |
|---|---|
| `schedule` | objeto com `schedule_type`, `start_date`, `end_date`, `start_time`, `end_time`, `id` |
| `weekdays` | conjunto de inteiros 1 a 7 (ignorado para `ONE_TIME`) |
| `from_date` | primeira data considerada |

Regras:

- `ONE_TIME`: uma ocorrência em `start_date`, se `start_date >= from_date`.
- `RECURRING`: cada data entre `max(start_date, from_date)` e `end_date` (inclusive) cujo
  `isoweekday()` esteja em `weekdays`.
- Período sem dia coincidente: gera nada, sem erro.

## `upcoming_occurrences(activity, now=None, limit=10)`

Devolve lista de `Occurrence` da atividade, ordenada por (`date`, `start_time`).

Regras:

- Lista vazia se `activity.status` não está em `PUBLIC_STATUSES`.
- `now` (padrão `timezone.now()`) é convertido para o fuso configurado; a data de referência é a data
  local.
- Descarta a ocorrência cuja data é hoje e `end_time` <= horário local atual; descarta datas passadas.
- Considera todas as programações da atividade (consulta única com dias pré-carregados).
- Corta o resultado em `limit` itens (`limit` positivo).
- Atividade sem programações ou sem datas futuras: lista vazia.

## Casos de referência (para os testes)

| Programação | Agora (local) | Resultado |
|---|---|---|
| Pontual 2026-11-10, 14:00-15:00 | 2026-11-10 14:30 | uma ocorrência (término 15:00 ainda não passou) |
| Pontual 2026-11-10, 14:00-15:00 | 2026-11-10 15:00 | vazia |
| Recorrente 2026-11-01..2026-11-30, terça(2) e quinta(4), 14:00-15:00 | 2026-11-09 | 10, 12, 17, 19, 24, 26 de novembro |
| Recorrente 2026-11-02..2026-11-04 (seg a qua), só sábado(6) | qualquer | vazia |
| Qualquer programação, atividade `DRAFT`, `CANCELLED` ou `FINISHED` | qualquer | vazia |
