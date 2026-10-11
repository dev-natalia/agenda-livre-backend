# Implementation Plan: Administração e Acesso

**Branch**: `002-admin-access` | **Date**: 2026-10-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/002-admin-access/spec.md`

## Summary

Ativar o Django Admin como única interface de gestão, protegida pela autenticação nativa do Django.
Existe um único perfil, o grupo "Administrador", que recebe automaticamente todas as permissões de
todos os modelos e de contas. Quem não tem o perfil não executa nenhuma operação, nem pelo painel nem
por URL direta. Um comando de gerenciamento cria contas de administrador, o painel é configurado em
português, e um auxiliar reutilizável oculta registros inativos nas listas de relacionamento. Não há
bloqueio por tentativas de login nem recuperação de senha por e-mail. Nenhuma entidade de negócio é
criada: usa-se o usuário padrão do Django.

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: Django 6.1 (admin, auth, sessions, messages), Django REST Framework 3.18,
django-environ. Nenhuma dependência nova.

**Storage**: PostgreSQL no AWS RDS. Esta feature só aplica as migrations nativas (admin, auth,
sessions, contenttypes) e cria o grupo "Administrador" via sinal pós-migração.

**Testing**: pytest, pytest-django e pytest-cov, somente testes unitários com mocks, sem acesso a
banco, cobertura total >= 90%

**Target Platform**: execução local, sem hospedagem

**Project Type**: web-service (Django com Admin; o frontend público fica em outro repositório)

**Performance Goals**: login e abertura do painel em menos de 1 minuto (SC-003); sem metas de carga

**Constraints**: toda escrita via Django Admin; senhas só com hash; nenhuma senha em log; consulta
pública continua sem login; sem bloqueio de login; sem e-mail

**Scale/Scope**: poucas contas de administrador; 1 comando de gerenciamento, 1 módulo de permissões,
1 auxiliar de admin, configuração do painel

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio / regra (v1.1.0) | Avaliação | Situação |
|---|---|---|
| I. Django Admin como interface de gestão, auth nativa, leitura pública sem login | Esta feature entrega o Admin com `django.contrib.auth`; sem telas ou autenticação customizadas; rotas públicas inalteradas | Passa |
| II. Django ORM no PostgreSQL (RDS), credenciais por ambiente | Grupo e permissões pelo ORM e migrations nativas; sem novas credenciais | Passa |
| III. Testes unitários, mocks, sem banco, cobertura >= 90% | Testes com `RequestFactory`, mocks de usuário, grupo e permissões; banco bloqueado mantido | Passa |
| IV. API REST pública, só PUBLISHED; erros JSON | Não altera a API; o painel usa a sessão do Django, separada do frontend (sem cookies entre origens) | Passa |
| V. Acessibilidade, segurança e simplicidade (YAGNI) | Perfil único, usuário padrão, sem bloqueio de login nem e-mail; senhas com hash e validadores | Passa |
| Stack e fluxo: Python 3.14, local apenas, PEP 8, README | Sem novas dependências; README ganha seção de acesso administrativo | Passa |

Sem violações. A seção Complexity Tracking não se aplica.

**Re-avaliação pós-design (Phase 1)**: o design não adiciona dependências, entidades próprias, telas
customizadas nem exposição pública. Continua sem violações.

## Project Structure

### Documentation (this feature)

```text
specs/002-admin-access/
├── plan.md              # Este arquivo
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/           # Phase 1
│   ├── admin-access.md
│   └── management-commands.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
config/
├── settings.py              # + admin, messages, staticfiles, sessão, templates, validadores de senha
├── settings_test.py         # sem mudança
└── urls.py                  # + rota admin/
apps/core/
├── apps.py                  # conecta o sinal post_migrate
├── permissions.py           # ADMIN_GROUP_NAME e sync_admin_group()
├── admin.py                 # título do painel e ActiveOnlyForeignKeyMixin
└── management/commands/
    └── create_admin.py      # cria conta de administrador
tests/unit/core/
├── test_permissions.py
├── test_admin.py
└── test_create_admin.py
README.md                    # seção "Acesso administrativo"
```

**Structure Decision**: tudo fica em `apps/core`, que já abriga os comandos de gerenciamento da
feature 001. Um app `accounts` seria complexidade sem ganho, já que não há modelo novo. As migrations
nativas do Django cobrem as tabelas necessárias.
