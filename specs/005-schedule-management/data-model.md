# Data Model: Gestão de Programações

Referência: `docs/03-modelo-de-dados.md` (seções 9, 10 e 11). Chaves primárias são UUID.

## Schedule (`apps/schedules`)

| Campo | Tipo | Regras |
|---|---|---|
| `id` | UUID | PK, gerado |
| `activity` | FK `Activity` | obrigatório, `PROTECT`, `related_name="schedules"` |
| `schedule_type` | texto com opções | `ONE_TIME` ("Pontual") ou `RECURRING` ("Recorrente"); obrigatório |
| `start_date` | data | obrigatório; primeiro dia do período (inclusive) |
| `end_date` | data | obrigatório; último dia do período (inclusive) |
| `start_time` | hora | obrigatório |
| `end_time` | hora | obrigatório; posterior a `start_time` |
| `created_by` | FK usuário | `PROTECT`, preenchido na criação, somente leitura |
| `updated_by` | FK usuário | `PROTECT`, preenchido a cada alteração, somente leitura |
| `created_at`, `updated_at` | data/hora | automáticos |

Nome no Admin: "Programação" / "Programações". Ordenação: `start_date`, `start_time`.

Restrições de banco (`CheckConstraint`):

- `start_date <= end_date`
- `start_time < end_time`
- `schedule_type <> 'ONE_TIME' OR start_date = end_date`

Índices: (`activity`), (`start_date`, `end_date`).

### Validações (`clean()` do modelo)

- Período invertido, término não posterior ao início e pontual com datas diferentes geram erro no
  campo correspondente (`end_date` ou `end_time`), com mensagem em português.
- Os mesmos erros são recusados pelo banco se alguém contornar o `clean()`.

## ScheduleWeekday (`apps/schedules`)

| Campo | Tipo | Regras |
|---|---|---|
| `id` | UUID | PK, gerado |
| `schedule` | FK `Schedule` | obrigatório, `CASCADE`, `related_name="weekdays"` |
| `weekday` | inteiro pequeno positivo | 1 a 7 (1 = segunda-feira ... 7 = domingo), com `choices` e nomes em português |

Restrições: `UniqueConstraint(schedule, weekday)`; `CheckConstraint` 1 <= `weekday` <= 7.

### Regras entre tabelas (formulário do Admin)

- `RECURRING` exige ao menos um dia da semana.
- `ONE_TIME` não pode ter dias da semana. Ao mudar uma recorrente para pontual, a pessoa precisa
  desmarcar os dias; com dias marcados, a edição é recusada. Ao salvar, as linhas de `ScheduleWeekday`
  passam a ser exatamente os dias escolhidos.

## Ocorrência (não persistida)

Estrutura imutável devolvida pelo serviço:

| Campo | Descrição |
|---|---|
| `date` | data da ocorrência |
| `start_time`, `end_time` | horários da programação |
| `schedule_id` | programação de origem |

## Relacionamentos

```text
Activity (1) ──── (N) Schedule (1) ──── (N) ScheduleWeekday
User     (1) ──── (N) Schedule     (criador e atualizador, sem exclusão em cascata)
```

## Transições e efeitos

Programações não têm situação própria. A situação da atividade (feature 004) afeta apenas o cálculo de
próximas ocorrências: só atividades `PUBLISHED` produzem resultado. Cancelar ou encerrar a atividade
não altera nem exclui programações.
