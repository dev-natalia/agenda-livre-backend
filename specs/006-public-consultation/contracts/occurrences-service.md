# Contrato: extensão do serviço de ocorrências (interno)

Altera `apps/schedules/services.py` (feature 005). Nada que já existe muda de comportamento: os novos
parâmetros são opcionais e `upcoming_occurrences(activity, now=None, limit=10)` mantém a assinatura e os
resultados (os testes atuais continuam valendo).

## `iter_occurrences(schedule, weekdays, from_date, to_date=None)`

Passa a aceitar `to_date` opcional (inclusive): gera as ocorrências em [`from_date`, `to_date`]. Sem `to_date`,
o comportamento anterior. (A função `first_occurrence` prevista no plano não foi criada: `activity_occurrences`
consome `iter_occurrences` de forma preguiçosa com `islice`, o que dá o mesmo resultado sem código extra.)

## `activity_occurrences(activity, now=None, date_from=None, date_to=None, limit=None)`

Ocorrências ainda não encerradas da atividade, em ordem (`date`, `start_time`).

| Parâmetro | Descrição |
|---|---|
| `now` | Padrão `timezone.now()`; convertido ao fuso configurado. A data local é "hoje". |
| `date_from` / `date_to` | Janela inclusiva. O início efetivo é `max(date_from, hoje)`. `None` = aberto. |
| `limit` | Positivo ou `None` (sem corte). |

Regras:

- Lista vazia se `activity.status` não está em `PUBLIC_STATUSES`.
- Descarta a ocorrência de hoje cujo `end_time <= horário local atual`.
- Usa `prefetch_related_objects([activity], "schedules__weekdays")`: sem custo extra se já estiver
  pré-carregado; ao menos 2 consultas, no total, se não estiver.
- Janela vazia (`date_to < início efetivo`): lista vazia, sem erro.
- `limit` não positivo: `ValueError`.

`upcoming_occurrences(activity, now=None, limit=10)` passa a chamar `activity_occurrences` com janela
aberta.

## Uso na consulta pública

- Listagem: para cada atividade elegível, `first` da lista de `activity_occurrences(…, limit=1)` com a
  janela do filtro de data (ou aberta).
- Detalhe: `activity_occurrences(activity, limit=5)`.
- Administração (feature 005): continua usando `upcoming_occurrences`; por usar o mesmo núcleo, o que a
  administração vê coincide com o que a consulta pública mostra (FR-018, SC-010).

## Casos de referência (acrescentar aos testes)

| Programação | Agora (local) | Janela | Resultado |
|---|---|---|---|
| Recorrente 2026-11-01..2026-12-31, terça(2) e quinta(4), 14:00-15:00 | 2026-11-09 | aberta | primeira: 2026-11-10 |
| Mesma | 2026-11-09 | 2026-11-12..2026-11-12 (quinta) | 2026-11-12 |
| Mesma | 2026-11-09 | 2026-11-11..2026-11-11 (quarta) | vazia |
| Mesma | 2026-11-09 | 2027-01-05..2027-01-10 | vazia (fora do período) |
| Pontual 2026-11-10, 14:00-15:00 | 2026-11-10 15:00 | 2026-11-10..2026-11-10 | vazia (já terminou) |
| Qualquer | 2026-11-09 | 2026-11-01..2026-11-05 | vazia (janela no passado) |
| Recorrente com `weekdays` vazio | qualquer | qualquer | vazia |
| Atividade `DRAFT`, `CANCELLED` ou `FINISHED` | qualquer | qualquer | vazia |
