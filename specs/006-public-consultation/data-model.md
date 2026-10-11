# Modelo de dados: Consulta Pública de Atividades

Esta feature **não cria nem altera tabelas**: não há migration. Ela lê modelos existentes e define
*visões de leitura* (serializers) e um objeto de critérios de consulta, ambos em memória.

## Fontes de dados (somente leitura)

| Modelo | App | Uso na consulta pública |
|---|---|---|
| `Activity` | `activities` | Só `status = PUBLISHED` (`PUBLIC_STATUSES`). Campos lidos: `id`, `title`, `slug`, `summary`, `description`, `target_audience_notes`, `external_registration_url`, `unit`, `category`, `target_audiences`. |
| `Unit` | `units` | Atividades: `id`, `name`, `slug`, `neighborhood`, `address` (detalhe). Lista de apoio: só `is_active = True`. |
| `Category` | `categories` | Atividades: `id`, `name`, `slug`. Lista de apoio: só `is_active = True`. |
| `TargetAudience` | `audiences` | Detalhe: `id`, `name` dos públicos vinculados (via `ActivityTargetAudience`). |
| `Schedule` / `ScheduleWeekday` | `schedules` | Regras de programação e dias da semana; base do cálculo de ocorrências (feature 005). |

**Nunca expostos**: `created_by`, `updated_by`, `created_at`, `updated_at`, `status`, `is_active`, contas
de usuário e qualquer campo de auditoria.

## Consultas ao banco por requisição

| Rota | Consultas |
|---|---|
| Listagem de atividades | 1 (atividades `PUBLISHED`, com `select_related("unit", "category")` e filtros de unidade/categoria) + 1 `prefetch` de `schedules` + 1 de `schedules__weekdays` |
| Detalhe | 1 (atividade) + `prefetch` de `target_audiences`, `schedules` e `schedules__weekdays` |
| Unidades / categorias | 1 contagem + 1 página (`is_active = True`, ordem por nome) |

## Critérios de consulta (objeto em memória)

Resultado da validação dos parâmetros de `GET /api/v1/activities/`.

| Campo | Tipo | Regra |
|---|---|---|
| `q` | texto ou ausente | `strip`; vazio vira ausente; máx. 100 caracteres (senão 400) |
| `unit` | UUID ou ausente | formato inválido: 400; sem correspondência: lista vazia |
| `category` | UUID ou ausente | idem |
| `neighborhood` | texto ou ausente | `strip`; vazio vira ausente; máx. 100; comparado sem acento e sem caixa |
| `date_from`, `date_to` | data ou ausente | `date` do parâmetro vira `date_from = date_to = date`; `date` junto com `date_from`/`date_to`: 400; `date_from > date_to`: 400; com os dois, máx. 366 dias entre eles |
| `page`, `page_size` | inteiros | tratados pelo paginador (padrão 12, máx. 50) |

Janela efetiva de ocorrências: início = `max(date_from, hoje)`, fim = `date_to` (ou aberto). Sem
nenhum dos dois, não há janela: vale "de hoje em diante" e a ordenação usa a próxima ocorrência.

## Visões de leitura

**ActivityListItem** (`results[]` da listagem)

| Campo | Origem |
|---|---|
| `id`, `title`, `slug`, `summary` | `Activity` |
| `unit` | `{ id, name, slug, neighborhood }` |
| `category` | `{ id, name, slug }` |
| `next_occurrence` | `{ date, start_time, end_time }` ou `null`; com filtro de data, é a primeira ocorrência dentro da janela |

**ActivityDetail**

| Campo | Origem |
|---|---|
| `id`, `title`, `slug`, `summary`, `description`, `target_audience_notes` | `Activity` |
| `unit` | `{ id, name, slug, address, neighborhood }` |
| `category` | `{ id, name, slug }` |
| `target_audiences` | `[{ id, name }]` |
| `external_registration_url` | URL `http`/`https` ou `null` |
| `schedules` | `[{ id, schedule_type, start_date, end_date, start_time, end_time, weekdays, weekday_names }]` por `start_date` |
| `next_occurrences` | até 5 `{ date, start_time, end_time }` em ordem cronológica |

**UnitItem**: `id`, `name`, `slug`, `neighborhood`, `address`, `description`.
**CategoryItem**: `id`, `name`, `slug`, `description`.

Formatos: datas `YYYY-MM-DD`, horários `HH:MM`, dias da semana 1 (segunda) a 7 (domingo), conforme
DOC-03 e DOC-05. `description` vazio vira `null` nas listas de apoio, como no exemplo do DOC-05.

## Regras de elegibilidade e ordem

- Elegível = `PUBLISHED`. Rascunho, cancelada e encerrada: ausentes de qualquer resposta; no detalhe,
  mesmo 404 de um identificador inexistente.
- Ordem da listagem: atividades com ocorrência de referência primeiro, por (data, horário de início,
  título normalizado); depois as sem ocorrência, por título normalizado.
- Ocorrência de referência = primeira ocorrência na janela (ou a próxima, sem janela), descartando a de
  hoje cujo término já passou.
