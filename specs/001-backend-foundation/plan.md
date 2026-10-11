# Implementation Plan: Fundação do Backend

**Branch**: `001-backend-foundation` | **Date**: 2026-10-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-backend-foundation/spec.md`

## Summary

Criar a base do backend Agenda Livre: um projeto Django com Django REST Framework, módulos por domínio
vazios, configuração lida de variáveis de ambiente com validação na inicialização, conexão com o
PostgreSQL no AWS RDS, comandos de verificação de conexão e de migração com confirmação do banco de
destino, uma suíte de testes unitários com mocks (sem nenhum acesso a banco) com cobertura mínima de
90%, verificação de estilo PEP 8, CORS para o frontend separado, dependências fixadas e um README.
Nenhuma entidade de negócio é criada nesta feature.

## Technical Context

**Language/Version**: Python 3.14 (validado: 3.14.5 instalado na máquina da equipe)

**Primary Dependencies**: Django 6.1, Django REST Framework 3.18, psycopg 3 (binary), django-cors-headers,
django-environ

**Storage**: PostgreSQL no AWS RDS (único banco do projeto; sem Docker)

**Testing**: pytest, pytest-django e pytest-cov (coverage.py), somente testes unitários com mocks, sem
acesso a banco

**Target Platform**: execução local (Windows/macOS/Linux), sem hospedagem

**Project Type**: web-service (API REST de backend; o frontend fica em outro repositório)

**Performance Goals**: sem metas de desempenho nesta feature. Metas operacionais estão nos critérios de
sucesso (inicialização, verificação de conexão e suíte de testes em segundos)

**Constraints**: sem segredos no repositório; testes sem banco; cobertura total >= 90%; fora do escopo:
hospedagem, deploy, backup, monitoramento e CI de deploy

**Scale/Scope**: 1 projeto, 6 módulos Django (`core` e 5 de domínio vazios), 2 comandos de gerenciamento
e 1 endpoint de verificação de funcionamento

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio / regra (v1.1.0) | Avaliação | Situação |
|---|---|---|
| I. Django Admin como interface de gestão | O Admin não é entregue aqui (feature 2). Não há escritas anônimas nem telas administrativas próprias | Passa |
| II. Django ORM no PostgreSQL (RDS), sem SQLAlchemy, credenciais por variáveis de ambiente | Banco via Django ORM com psycopg, configuração só por ambiente, `.env.example` sem valores reais | Passa |
| III. Testes unitários, mocks, sem banco, cobertura >= 90% | Banco `dummy` nas configurações de teste e acesso bloqueado pelo pytest-django; `--cov-fail-under=90` | Passa |
| IV. API REST (DRF), frontend separado com CORS | CORS configurado por lista de origens; endpoint de verificação em `/api/v1/health/` | Passa |
| V. Acessibilidade, segurança e simplicidade (YAGNI) | Sem funcionalidades além do escopo; segredos nunca registrados em log ou mensagens | Passa |
| Stack: Python 3.14, local apenas, dependências fixadas | Versões fixadas em `requirements*.txt`; sem artefatos de deploy | Passa |
| Fluxo: PEP 8 com linter, README com instalação, variáveis e testes | Ruff configurado; README é entregável desta feature | Passa |

Sem violações. A seção Complexity Tracking não se aplica.

**Re-avaliação pós-design (Phase 1)**: os artefatos de design não introduziram entidades, escritas anônimas,
acesso a banco nos testes nem componentes fora da stack. Continua sem violações.

## Project Structure

### Documentation (this feature)

```text
specs/001-backend-foundation/
├── plan.md              # Este arquivo
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/           # Phase 1
│   ├── health-endpoint.md
│   ├── management-commands.md
│   └── environment-variables.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
manage.py
config/
├── __init__.py
├── env.py               # leitura e validação das variáveis de ambiente
├── settings.py          # configuração de execução (lê o ambiente)
├── settings_test.py     # configuração dos testes (banco dummy, sem variáveis obrigatórias)
├── urls.py
├── asgi.py
└── wsgi.py
apps/
├── __init__.py
├── core/                # verificação de funcionamento e comandos de gerenciamento
│   ├── apps.py
│   ├── urls.py
│   ├── views.py
│   └── management/commands/
│       ├── check_db.py
│       └── safe_migrate.py
├── units/               # módulos de domínio, vazios nesta feature
├── categories/
├── activities/
├── schedules/
└── audiences/
tests/
├── conftest.py
└── unit/
    ├── config/          # env.py e settings
    └── core/            # view de saúde e comandos, com mocks
pyproject.toml           # pytest, coverage e ruff
requirements.txt         # dependências de execução, versões fixadas
requirements-dev.txt     # inclui requirements.txt + ferramentas de teste e lint
.env.example
README.md
```

**Structure Decision**: projeto único com o Django na raiz do repositório (`config/` para o projeto e
`apps/` para os módulos por domínio), seguindo a organização sugerida no DOC-02. O frontend é outro
repositório, então não há diretório `frontend/`. Os módulos de domínio são criados vazios para que as
próximas features apenas adicionem modelos neles.

## Complexity Tracking

Sem violações da constituição; nada a justificar.
