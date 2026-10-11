# Implementation Plan: Gestão de Programações

**Branch**: `005-schedule-management` | **Date**: 2026-10-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/005-schedule-management/spec.md`

## Summary

Criar os modelos `Schedule` e `ScheduleWeekday` no app `schedules` (já existente, vazio) e registrá-los
no Django Admin. A programação tem tipo (`ONE_TIME`, `RECURRING`), período, horário de início e de
término e autoria. Os dias da semana são editados no formulário da programação como um campo de
checkboxes (segunda a domingo), sincronizado com as linhas de `ScheduleWeekday` ao salvar; isso evita
duplicidade por construção, e a restrição de unicidade do banco é a segunda barreira. As regras entre
campos (período, horário, pontual com datas iguais, recorrente com ao menos um dia, pontual sem dias)
ficam no `clean()` do modelo e do formulário, com `CheckConstraint`s equivalentes no banco. As
ocorrências são calculadas por um serviço (`apps/schedules/services.py`), sem tabela de ocorrências, e
mostradas na página da atividade junto com a lista de programações e um atalho para adicionar uma
nova. A chave estrangeira para a atividade usa `PROTECT`, o que impede excluir atividade com
programações (FR-013 da feature 004). Não há API pública nesta feature.

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: Django 6.1 (admin, ORM), Django REST Framework 3.18, django-environ. Nenhuma
dependência nova.

**Storage**: PostgreSQL no AWS RDS. Duas tabelas novas (`schedules_schedule`,
`schedules_scheduleweekday`), criadas por migrations do Django.

**Testing**: pytest, pytest-django e pytest-cov, somente testes unitários com mocks, sem acesso a
banco, cobertura total >= 90%. O cálculo de ocorrências é função pura sobre dados e relógio injetados.

**Target Platform**: execução local, sem hospedagem

**Project Type**: web-service (Django com Admin; o frontend público fica em outro repositório)

**Performance Goals**: cadastrar uma recorrência completa em menos de 2 minutos (SC-001); o cálculo das
próximas ocorrências de uma atividade usa uma consulta com `prefetch` dos dias e itera dia a dia só
dentro do período e até o limite pedido

**Constraints**: toda escrita via Django Admin, sem telas customizadas; permissões herdadas do grupo
"Administrador" (feature 002); fuso `America/Sao_Paulo` já configurado; meia-noite não suportada;
sem exceções por ocorrência; sem endpoints públicos

**Scale/Scope**: dezenas de programações por atividade no máximo; 2 modelos, 1 `ModelAdmin` com
formulário customizado, 1 inline somente leitura em `ActivityAdmin`, 1 módulo de serviço

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio / regra (v1.1.0) | Avaliação | Situação |
|---|---|---|
| I. Django Admin como interface de gestão, auth nativa, leitura pública sem login | Cadastro, edição e exclusão só pelo Admin (`ModelAdmin`, campo de formulário e inline padrão); sem telas ou autenticação customizadas; nenhuma rota pública alterada | Passa |
| II. Django ORM no PostgreSQL (RDS), credenciais por ambiente | Modelos do ORM e migrations do Django; sem novas credenciais | Passa |
| III. Testes unitários, mocks, sem banco, cobertura >= 90% | Validações, formulário, sincronização de dias, admin e cálculo de ocorrências testados com instâncias não salvas, mocks de queryset, `RequestFactory` e relógio injetado; banco bloqueado mantido | Passa |
| IV. API REST pública, só PUBLISHED; erros JSON | Não cria nem altera endpoints; o serviço de ocorrências só devolve dados para atividades em `PUBLIC_STATUSES`, pronto para a API de consulta | Passa |
| V. Acessibilidade, segurança e simplicidade (YAGNI) | Campos conforme `docs/03-modelo-de-dados.md`; sem tabela de ocorrências, exceções, conflitos de horário ou histórico; nenhum dado pessoal exposto | Passa |
| Stack e fluxo: Python 3.14, local apenas, PEP 8, README | Sem novas dependências; README ganha uma seção sobre programações | Passa |

Sem violações. A seção Complexity Tracking não se aplica.

**Re-avaliação pós-design (Phase 1)**: o design adiciona dois modelos, um formulário de admin, um
inline e um serviço. Sem dependências novas, telas customizadas ou exposição pública. Continua sem
violações.

## Project Structure

### Documentation (this feature)

```text
specs/005-schedule-management/
├── plan.md              # Este arquivo
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/           # Phase 1
│   ├── admin-schedules.md
│   └── occurrences-service.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
apps/schedules/
├── models.py                # Schedule, ScheduleWeekday, constantes de tipo e dia da semana
├── services.py              # iter_occurrences(), upcoming_occurrences(): cálculo sem armazenamento
├── forms.py                 # ScheduleAdminForm: campo de dias da semana e regras entre campos
├── admin.py                 # ScheduleAdmin (sincroniza dias em save_related, autoria, filtros)
└── migrations/0001_initial.py
apps/activities/
└── admin.py                 # + inline somente leitura de programações e campo "próximas ocorrências"
tests/unit/
├── schedules/test_schedule_model.py
├── schedules/test_schedule_form.py
├── schedules/test_occurrences_service.py
├── schedules/test_schedule_admin.py
└── activities/test_activity_admin.py        # amplia o teste existente
README.md                    # seção sobre programações e ocorrências
```

**Structure Decision**: o app `schedules` existe desde a feature 001 e recebe os modelos. O Django não
oferece inline aninhado (programação → dias), por isso os dias são um campo do formulário da
programação e o inline na atividade é somente leitura, com link para editar. O cálculo fica em
`services.py`, e não no `ModelAdmin`, para ser testável sem banco e reutilizável pela API de consulta
futura.
