# Implementation Plan: Gestão de Unidades e Categorias

**Branch**: `003-units-categories` | **Date**: 2026-10-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/003-units-categories/spec.md`

## Summary

Criar os modelos `Unit` e `Category` e registrá-los no Django Admin, que já está protegido pela
feature 002. Os dois compartilham uma base abstrata em `apps/core` (id UUID, nome, slug, descrição,
situação ativa, datas), e o slug é gerado a partir do nome quando fica em branco. O nome da categoria
é único sem diferenciar maiúsculas e minúsculas. A desativação é por `is_active` (com ações em lote
para desativar e reativar), e a exclusão de registros vinculados será impedida pelas atividades da
feature 004 com `on_delete=PROTECT`. Um comando idempotente carrega o CEU Navegantes e as oito
categorias iniciais. Não há API pública nesta feature.

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: Django 6.1 (admin, ORM), Django REST Framework 3.18, django-environ. Nenhuma
dependência nova.

**Storage**: PostgreSQL no AWS RDS. Duas tabelas novas (`units_unit`, `categories_category`), criadas
por migrations do Django.

**Testing**: pytest, pytest-django e pytest-cov, somente testes unitários com mocks, sem acesso a
banco, cobertura total >= 90%

**Target Platform**: execução local, sem hospedagem

**Project Type**: web-service (Django com Admin; o frontend público fica em outro repositório)

**Performance Goals**: cadastrar uma unidade ou categoria em menos de 2 minutos (SC-001); sem metas de
carga

**Constraints**: toda escrita via Django Admin, sem telas customizadas; permissões herdadas do grupo
"Administrador" (feature 002); migrations aplicadas por `safe_migrate`; sem endpoints públicos

**Scale/Scope**: dezenas de registros; 2 modelos, 1 base abstrata, 2 `ModelAdmin`, 1 comando de carga

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio / regra (v1.1.0) | Avaliação | Situação |
|---|---|---|
| I. Django Admin como interface de gestão, auth nativa, leitura pública sem login | Cadastros só pelo Admin com `ModelAdmin` padrão; sem telas ou autenticação customizadas; nenhuma rota pública alterada | Passa |
| II. Django ORM no PostgreSQL (RDS), credenciais por ambiente | Modelos do ORM e migrations do Django; sem novas credenciais | Passa |
| III. Testes unitários, mocks, sem banco, cobertura >= 90% | Validação, `clean`, admin e comando testados com instâncias não salvas, mocks de queryset e `RequestFactory`; banco bloqueado mantido | Passa |
| IV. API REST pública, só PUBLISHED; erros JSON | Não cria nem altera endpoints; a exposição pública de unidades e categorias fica para a feature de consulta (spec, FR-017) | Passa |
| V. Acessibilidade, segurança e simplicidade (YAGNI) | Sem campos além de `docs/03-modelo-de-dados.md`; sem hierarquia, imagem ou contato; nenhum dado pessoal | Passa |
| Stack e fluxo: Python 3.14, local apenas, PEP 8, README | Sem novas dependências; README ganha a seção de carga inicial | Passa |

Sem violações. A seção Complexity Tracking não se aplica.

**Re-avaliação pós-design (Phase 1)**: o design adiciona apenas modelos, admin e um comando. Sem
dependências novas, telas customizadas ou exposição pública. Continua sem violações.

## Project Structure

### Documentation (this feature)

```text
specs/003-units-categories/
├── plan.md              # Este arquivo
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/           # Phase 1
│   ├── admin-units-categories.md
│   └── management-commands.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
apps/core/
├── models.py                # + CatalogModel (base abstrata)
├── admin.py                 # + ActiveToggleActionsMixin (ações ativar/desativar)
└── management/commands/
    └── seed_catalog.py      # carga idempotente de unidade e categorias iniciais
apps/units/
├── models.py                # Unit
├── admin.py                 # UnitAdmin
└── migrations/0001_initial.py
apps/categories/
├── models.py                # Category
├── admin.py                 # CategoryAdmin
└── migrations/0001_initial.py
tests/unit/
├── core/test_catalog_model.py
├── core/test_active_toggle_actions.py
├── core/test_seed_catalog.py
├── units/test_unit_model.py
├── units/test_unit_admin.py
├── categories/test_category_model.py
└── categories/test_category_admin.py
README.md                    # seção "Carga inicial de unidades e categorias"
```

**Structure Decision**: os apps `units` e `categories` já existem desde a feature 001 e recebem os
modelos. A base abstrata e o mixin de ações ficam em `apps/core`, junto do mixin da feature 002, para
reuso por atividades (feature 004). O comando de carga fica em `apps/core`, onde estão os demais
comandos.
