# Implementation Plan: Ambientes e Registro de Erros

**Branch**: `008-environments-logging` | **Date**: 2026-10-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/008-environments-logging/spec.md`

## Summary

Fechar o EP-08 no escopo local, sem modelos, migrations nem rotas novas. A investigação (ver
[research.md](research.md)) mostrou que US-031 já está quase toda entregue (feature 001) e que US-034
é a única lacuna de código: **não existe configuração de `LOGGING`**, então as falhas inesperadas só
vão para o terminal. O plano tem três partes:

1. **Registro de erros em arquivo** (US-034): `LOGGING` montado em `config/logging_config.py`, com
   arquivo rotativo (`RotatingFileHandler`) em `logs/`, nível mínimo `ERROR`, e um *formatter* que
   mascara segredos em todo o texto gravado, inclusive no rastreamento. Falhas de gravação nunca
   derrubam a requisição, e erros esperados de cliente (4xx) não entram.
2. **Falhas de inicialização e de conexão** (FR-003): variável ausente em `settings.py` e falha em
   `check_db`/`safe_migrate` passam a ser registradas (tipo e nomes de variáveis, nunca valores).
3. **Segurança por ambiente** (US-031): uma chave `DJANGO_HTTPS_ONLY` (padrão: ligada quando
   `DEBUG=False`) controla redirecionamento HTTPS, cookies seguros e HSTS; cabeçalhos sempre seguros
   (nosniff, `X-Frame-Options`, cookie HttpOnly) valem em qualquer modo.

Documentação: README (variáveis, onde ficam os logs, escopo), `.env.example`, DOC-04, DOC-08 e
`docs/PENDENCIAS.md`.

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: Django 6.1, Django REST Framework 3.18, django-cors-headers, django-environ.
Módulo `logging` da biblioteca padrão. Nenhuma dependência nova.

**Storage**: PostgreSQL no AWS RDS. **Nenhuma tabela, coluna ou migration nova**
(`makemigrations --check` continua sem mudanças). Os registros ficam em arquivo local, não no banco.

**Testing**: pytest, pytest-django, pytest-cov; somente testes unitários com mocks, sem banco, cobertura
total >= 90%. Logging testado com `tmp_path`, `caplog` e instâncias de `logging.LogRecord`; settings
recarregadas pela fixture `load_settings` existente.

**Target Platform**: execução local, sem hospedagem

**Project Type**: web-service (API do Django + Django Admin; o frontend fica em outro repositório)

**Performance Goals**: sem meta nova; gravação só em erros (nível ERROR), sem efeito no caminho feliz.

**Constraints**: sem segredos nos registros; resposta ao visitante inalterada (genérica, feature 007);
falha de gravação não interrompe o atendimento; espaço total dos registros limitado por
`LOG_MAX_BYTES * (LOG_BACKUP_COUNT + 1)`; testes não escrevem fora de diretório temporário.

**Scale/Scope**: 1 módulo novo (`config/logging_config.py`), 3 arquivos de código alterados
(`config/settings.py`, `config/env.py`, `apps/core/management/commands/check_db.py` e `safe_migrate.py`),
~5 módulos de teste, 5 documentos.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio / regra (v1.1.0) | Avaliação | Situação |
|---|---|---|
| I. Django Admin como interface de gestão | Nenhuma tela, rota ou autenticação nova. | OK |
| II. Django ORM no PostgreSQL | Sem persistência nova; segredos continuam só em variáveis de ambiente, nada versionado. | OK |
| III. Código testado, cobertura >= 90% | Cada FR tem teste unitário sem banco; `--cov-fail-under=90` segue ativo; arquivos de log só em `tmp_path`. | OK |
| IV. API REST pública e filtrável | Respostas da API não mudam; erros continuam em JSON genérico. | OK |
| V. Acessibilidade, segurança e simplicidade | Mascaramento de segredos nos logs (princípio "não logar segredos"); YAGNI: sem monitoramento, alertas ou serviço externo. | OK |
| Stack e restrições | Local apenas; HTTPS/HSTS ficam como configuração do modo restritivo e **não** exigem hospedagem; nenhuma dependência nova. | OK |
| Fluxo e portões | specify → plan → tasks → implement; PR com revisão; README atualizado (variáveis). | OK |

Sem violações; a tabela de complexidade não se aplica.

**Reavaliação pós-design**: mantida. O design não adiciona app, modelo, dependência, rota ou migration.

## Project Structure

### Documentation (this feature)

```text
specs/008-environments-logging/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── logging.md
│   └── environment.md
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit-tasks (não criado aqui)
```

### Source Code (repository root)

```text
config/
├── logging_config.py    # build_logging(), RedactingFormatter, log_startup_failure() (novo)
├── env.py               # novas variáveis opcionais + get_int() (alterado)
└── settings.py          # LOGGING, flags de segurança, registro de falha de inicialização (alterado)
apps/core/management/commands/
├── check_db.py          # registra falha de conexão (tipo, host, porta) (alterado)
└── safe_migrate.py      # registra falha de migração/conexão (alterado)
.env.example             # novas variáveis (alterado)
.gitignore               # logs/ (alterado)
README.md                # variáveis, logs, escopo (alterado)
docs/04-*.md, docs/08-*.md, docs/PENDENCIAS.md   # escopo EP-08/EP-09 (alterados)

tests/unit/config/
├── test_logging_config.py       # arquivo rotativo, nível, rotação, diretório inválido
├── test_log_redaction.py        # senha/chave/cookie/autorização mascarados, inclusive em traceback
├── test_startup_logging.py      # variável ausente e falha de conexão registradas sem valores
├── test_security_settings.py    # DJANGO_HTTPS_ONLY, padrão por DEBUG, cabeçalhos sempre ativos
└── test_env_documentation.py    # toda variável de ALL_VARS está no README e no .env.example
tests/unit/core/
└── test_exception_logging.py    # 500 gera registro e resposta continua genérica; 4xx não gera
```

**Structure Decision**: sem app novo. Logging é configuração transversal, então mora em `config/` ao
lado de `env.py` (que já concentra a leitura de ambiente). O ponto de captura continua sendo
`apps/core/exceptions.py` (feature 007), que já usa `logging.getLogger(__name__)`; ele não muda, só passa
a ter destino persistente.

## Complexity Tracking

Sem violações a justificar.
