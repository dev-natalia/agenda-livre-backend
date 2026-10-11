# Implementation Plan: Gestão de Atividades

**Branch**: `004-activity-management` | **Date**: 2026-10-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/004-activity-management/spec.md`

## Summary

Criar os modelos `Activity`, `TargetAudience` e o vínculo explícito `ActivityTargetAudience` e
registrá-los no Django Admin, já protegido pela feature 002. A atividade tem situação (`DRAFT`,
`PUBLISHED`, `FINISHED`, `CANCELLED`) que **não é editável no formulário**: muda somente por ações do
Admin (publicar, cancelar, encerrar), que passam por uma função de serviço única com as regras de
transição e de publicação. A autoria (`created_by`, `updated_by`) é preenchida pelo Admin e pelas
ações. O slug é gerado do título com sufixo para evitar colisão. Os públicos-alvo são escolhidos em
um inline com opções ativas (mantendo as já vinculadas); `seed_catalog` passa a carregar as opções
iniciais. Chaves estrangeiras para unidade e categoria usam `PROTECT`. Não há API pública nesta
feature.

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: Django 6.1 (admin, ORM), Django REST Framework 3.18, django-environ. Nenhuma
dependência nova.

**Storage**: PostgreSQL no AWS RDS. Três tabelas novas (`activities_activity`,
`audiences_targetaudience`, `activities_activitytargetaudience`), criadas por migrations do Django.

**Testing**: pytest, pytest-django e pytest-cov, somente testes unitários com mocks, sem acesso a
banco, cobertura total >= 90%

**Target Platform**: execução local, sem hospedagem

**Project Type**: web-service (Django com Admin; o frontend público fica em outro repositório)

**Performance Goals**: cadastrar uma atividade completa em menos de 3 minutos (SC-001); sem metas de
carga

**Constraints**: toda escrita via Django Admin, sem telas customizadas; permissões herdadas do grupo
"Administrador" (feature 002); migrations aplicadas por `safe_migrate`; sem endpoints públicos; mudança
de situação apenas por ações do Admin

**Scale/Scope**: centenas de atividades; 3 modelos, 1 `ModelAdmin` com inline, 1 `ModelAdmin` de
público-alvo, 1 módulo de serviço de situação, extensão do comando de carga

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio / regra (v1.1.0) | Avaliação | Situação |
|---|---|---|
| I. Django Admin como interface de gestão, auth nativa, leitura pública sem login | Cadastro, edição e mudança de situação só pelo Admin (`ModelAdmin`, inline e ações padrão); sem telas ou autenticação customizadas; nenhuma rota pública alterada | Passa |
| II. Django ORM no PostgreSQL (RDS), credenciais por ambiente | Modelos do ORM e migrations do Django; sem novas credenciais | Passa |
| III. Testes unitários, mocks, sem banco, cobertura >= 90% | Regras de transição, validação, slug, admin, inline e comando testados com instâncias não salvas, mocks de queryset e `RequestFactory`; banco bloqueado mantido | Passa |
| IV. API REST pública, só PUBLISHED; erros JSON | Não cria nem altera endpoints; a regra "só PUBLISHED é pública" fica codificada no modelo (`PUBLIC_STATUSES`) para a feature de consulta usar | Passa |
| V. Acessibilidade, segurança e simplicidade (YAGNI) | Campos conforme `docs/03-modelo-de-dados.md`; sem imagens, histórico de situações ou tabela de auditoria; nenhum dado pessoal exposto | Passa |
| Stack e fluxo: Python 3.14, local apenas, PEP 8, README | Sem novas dependências; README ganha a seção das opções iniciais de público-alvo | Passa |

Sem violações. A seção Complexity Tracking não se aplica.

**Re-avaliação pós-design (Phase 1)**: o design adiciona modelos, admin, um serviço e extensão de um
comando. Sem dependências novas, telas customizadas ou exposição pública. Continua sem violações.

## Project Structure

### Documentation (this feature)

```text
specs/004-activity-management/
├── plan.md              # Este arquivo
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/           # Phase 1
│   ├── admin-activities.md
│   └── management-commands.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
apps/core/
├── admin.py                 # ActiveOnlyForeignKeyMixin passa a manter o valor já vinculado ao editar
└── management/commands/
    └── seed_catalog.py      # + opções iniciais de público-alvo
apps/audiences/
├── models.py                # TargetAudience (reusa CatalogModel)
├── admin.py                 # TargetAudienceAdmin
└── migrations/0001_initial.py
apps/activities/
├── models.py                # Activity, ActivityTargetAudience, constantes de situação
├── services.py              # change_status(): regras de transição e de publicação, auditoria
├── admin.py                 # ActivityAdmin, inline de públicos, ações publicar/cancelar/encerrar
└── migrations/0001_initial.py
tests/unit/
├── activities/test_activity_model.py
├── activities/test_status_service.py
├── activities/test_activity_admin.py
├── audiences/test_target_audience_model.py
├── audiences/test_target_audience_admin.py
├── core/test_active_only_fk_mixin.py       # amplia o teste existente do mixin
└── core/test_seed_catalog.py              # amplia o teste existente
README.md                    # seção das opções iniciais de público-alvo
```

**Structure Decision**: os apps `activities` e `audiences` já existem desde a feature 001 e recebem os
modelos. As regras de situação ficam em `services.py`, e não no `ModelAdmin`, para serem testáveis
sem banco e reutilizáveis pela API futura. A base `CatalogModel` e os mixins de `apps/core` (feature
003) são reaproveitados.
