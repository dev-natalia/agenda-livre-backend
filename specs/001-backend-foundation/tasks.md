---

description: "Lista de tarefas da fundação do backend"
---

# Tasks: Fundação do Backend

**Input**: Documentos de design em `/specs/001-backend-foundation/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Incluídos. A constituição (Princípio III) exige testes unitários com mocks, sem acesso a banco, e
cobertura total mínima de 90%. Nenhum teste pode abrir conexão com banco de dados.

**Organization**: Tarefas agrupadas por história de usuário (US1 a US5 da spec), para permitir
implementação e validação independentes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência de tarefa incompleta)
- **[Story]**: história de usuário à qual a tarefa pertence (US1 a US5)
- Os caminhos são relativos à raiz do repositório

## Path Conventions

Projeto único com o Django na raiz: `config/` (projeto), `apps/` (módulos por domínio) e `tests/`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: dependências, ambiente virtual e ignorados do Git

- [ ] T001 Atualizar `.gitignore` adicionando `.env`, `.venv/`, `__pycache__/`, `*.pyc`, `.coverage`, `htmlcov/`, `.pytest_cache/` e `.ruff_cache/`, mantendo as entradas existentes (`.claude/skills` e `docs`)
- [ ] T002 [P] Criar `requirements.txt` com as versões fixadas: `Django==6.1.2`, `djangorestframework==3.18.3`, `psycopg[binary]==3.3.6`, `django-cors-headers==4.9.0`, `django-environ==0.14.0`
- [ ] T003 [P] Criar `requirements-dev.txt` iniciando com `-r requirements.txt` e fixando `pytest==9.1.1`, `pytest-django==4.14.0`, `pytest-cov==7.1.0`, `coverage==7.16.2` e `ruff==0.17.0`
- [ ] T004 Criar o ambiente virtual `.venv` com Python 3.14 e instalar `requirements-dev.txt`, confirmando que a instalação termina sem erros

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: esqueleto do projeto, leitura de configuração e configuração de testes. Bloqueia todas as histórias.

**⚠️ CRITICAL**: nenhuma história começa antes desta fase terminar.

- [ ] T005 Criar `config/__init__.py`, `apps/__init__.py` e, em `apps/`, os módulos `core`, `units`, `categories`, `activities`, `schedules` e `audiences`, cada um com `__init__.py`, `apps.py` (classe `AppConfig` com `name = "apps.<modulo>"`) e `models.py` vazio (sem modelos de negócio)
- [ ] T006 Criar `config/env.py` com a função `require_env(names)` que lê o ambiente e levanta `ImproperlyConfigured` com uma única mensagem `Configuração incompleta. Defina as variáveis de ambiente: A, B` listando **todas** as obrigatórias ausentes ou vazias, nunca imprimindo valores; e funções de leitura tipada de `DB_PORT` (inteiro entre 1 e 65535), `DJANGO_DEBUG` (booleano, padrão `False`) e `DB_SSLMODE` (um de `disable`, `allow`, `prefer`, `require`, `verify-ca`, `verify-full`; padrão `require`)
- [ ] T007 Criar `config/settings.py` carregando `.env` com django-environ e lendo `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS` (padrão `localhost,127.0.0.1`) e `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` via `config/env.py`; `DATABASES["default"]` com engine PostgreSQL e `OPTIONS` contendo `sslmode`, `connect_timeout` igual a 15 e `sslrootcert` somente quando `DB_SSLROOTCERT` estiver definida; `INSTALLED_APPS` com `django.contrib.contenttypes`, `django.contrib.auth`, `django.contrib.sessions`, `rest_framework` e os 6 módulos de `apps/`; `LANGUAGE_CODE = "pt-br"`, `TIME_ZONE = "America/Sao_Paulo"`, `USE_TZ = True`, `ROOT_URLCONF = "config.urls"` e `DEFAULT_AUTO_FIELD`
- [ ] T008 [P] Criar `config/settings_test.py` que define valores falsos para as variáveis obrigatórias com `os.environ.setdefault`, importa `from config.settings import *` e sobrescreve `DATABASES` com `{"default": {"ENGINE": "django.db.backends.dummy"}}`, de forma que os testes não exijam `.env` nem RDS
- [ ] T009 [P] Criar `manage.py` (padrão `config.settings`), `config/wsgi.py` e `config/asgi.py`
- [ ] T010 [P] Criar `config/urls.py` incluindo `apps.core.urls` sob o prefixo `api/v1/`
- [ ] T011 Criar `pyproject.toml` com `[tool.pytest.ini_options]` (`DJANGO_SETTINGS_MODULE = "config.settings_test"`, `testpaths = ["tests"]`, `addopts = "--cov=apps --cov=config --cov-report=term-missing --cov-fail-under=90"`), `[tool.coverage.run]` com `omit` de `manage.py`, `config/wsgi.py` e `config/asgi.py`, e `[tool.ruff]` com `line-length = 100`, `exclude = [".venv"]` e `[tool.ruff.lint] select = ["E", "W", "F", "I"]`
- [ ] T012 Criar `tests/conftest.py` com a fixture `valid_env` (dicionário de variáveis obrigatórias válidas) e a fixture `clean_env` que remove do ambiente, com `monkeypatch`, todas as variáveis da aplicação, para testes de configuração

**Checkpoint**: esqueleto pronto. As histórias podem começar.

---

## Phase 3: User Story 1 - Rodar o projeto em uma máquina nova (Priority: P1) 🎯 MVP

**Goal**: clonar, seguir o README, instalar, configurar o ambiente e iniciar o backend, com falha clara quando faltar configuração.

**Independent Test**: em uma máquina limpa, seguir apenas o README até `python manage.py runserver` e obter `{"status": "ok"}` em `/api/v1/health/`; removendo uma variável obrigatória, a inicialização falha citando o nome dela.

### Tests for User Story 1

- [ ] T013 [P] [US1] Criar `tests/unit/config/test_env.py` cobrindo: várias variáveis ausentes listadas numa única mensagem, variável vazia tratada como ausente, valores sensíveis ausentes da mensagem, `DB_PORT` não numérico ou fora de 1 a 65535 rejeitado, `DJANGO_DEBUG` padrão `False`, `DB_SSLMODE` padrão `require` e valor inválido rejeitado
- [ ] T014 [P] [US1] Criar `tests/unit/core/test_health.py` verificando que `GET /api/v1/health/` retorna 200 com `{"status": "ok"}` e que `POST` retorna 405, usando `APIClient` sem acesso a banco
- [ ] T015 [P] [US1] Criar `tests/unit/config/test_structure.py` verificando que `INSTALLED_APPS` contém `apps.core`, `apps.units`, `apps.categories`, `apps.activities`, `apps.schedules` e `apps.audiences`

### Implementation for User Story 1

- [ ] T016 [US1] Criar `apps/core/views.py` (view de DRF `GET` que devolve `{"status": "ok"}` sem consultar o banco) e `apps/core/urls.py` com a rota `health/` (contrato em `contracts/health-endpoint.md`)
- [ ] T017 [P] [US1] Criar `.env.example` com todas as variáveis de `contracts/environment-variables.md` (`DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_SSLMODE`, `DB_SSLROOTCERT`, `CORS_ALLOWED_ORIGINS`), apenas com valores de exemplo e sem segredos reais
- [ ] T018 [US1] Criar `README.md` com: visão geral, requisito de Python 3.14, criação do `.venv` e instalação de `requirements-dev.txt`, cópia de `.env.example` para `.env`, tabela das variáveis de ambiente e como iniciar o backend com `python manage.py runserver`

**Checkpoint**: o backend inicia com configuração válida e falha de forma clara sem ela.

---

## Phase 4: User Story 2 - Conectar ao banco de dados e aplicar a estrutura (Priority: P1)

**Goal**: verificar a conexão com o RDS e aplicar as migrations vendo qual banco será alterado.

**Independent Test**: com credenciais válidas, `python manage.py check_db` informa sucesso e `python manage.py safe_migrate` mostra o destino e aplica ao confirmar; com credenciais inválidas, `check_db` falha em até 15 segundos sem imprimir a senha.

### Tests for User Story 2

- [ ] T019 [P] [US2] Criar `tests/unit/config/test_settings.py` que, com `monkeypatch` e `importlib.reload(config.settings)`, verifica engine PostgreSQL, `sslmode` padrão `require`, `connect_timeout` igual a 15, `sslrootcert` presente só quando `DB_SSLROOTCERT` estiver definida e `ALLOWED_HOSTS` padrão
- [ ] T020 [P] [US2] Criar `tests/unit/core/test_check_db.py` com `unittest.mock` no objeto de conexão: sucesso (saída com host, porta e nome do banco e código 0), falha de conexão (saída com o tipo de falha, código diferente de 0) e verificação de que a senha nunca aparece na saída
- [ ] T021 [P] [US2] Criar `tests/unit/core/test_safe_migrate.py` com `unittest.mock` em `call_command`: exibe host, porta, banco e usuário sem senha, confirmação `s` executa o `migrate`, qualquer outra resposta não executa e termina com erro, e `--noinput` executa sem perguntar

### Implementation for User Story 2

- [ ] T022 [US2] Criar `apps/core/management/__init__.py`, `apps/core/management/commands/__init__.py` e `apps/core/management/commands/check_db.py`, que abre a conexão configurada, executa `SELECT 1` e imprime host, porta e nome do banco com a mensagem de sucesso, ou o tipo de falha com dica de correção e código de saída diferente de 0, nunca imprimindo a senha (contrato em `contracts/management-commands.md`)
- [ ] T023 [US2] Criar `apps/core/management/commands/safe_migrate.py`, que exibe host, porta, nome do banco e usuário de destino sem senha, pede confirmação `s/N` (ignorada com `--noinput`) e então chama o `migrate` padrão; qualquer resposta diferente de `s` encerra sem alterar o banco
- [ ] T024 [US2] Atualizar `README.md` com a seção de banco de dados: pré-requisito do RDS e acesso de rede, `python manage.py check_db`, `python manage.py safe_migrate` e o aviso de que o banco RDS é único e compartilhado

**Checkpoint**: conexão verificada e migrations aplicáveis com destino explícito.

---

## Phase 5: User Story 3 - Executar testes unitários e medir a cobertura (Priority: P1)

**Goal**: um comando único roda a suíte sem banco, mede a cobertura e falha abaixo de 90%.

**Independent Test**: `pytest` roda sem `.env` e sem rede, informa a cobertura e falha ao ficar abaixo de 90%; um teste que acesse o banco falha de forma explícita.

### Tests for User Story 3

- [ ] T025 [P] [US3] Criar `tests/unit/test_db_guard.py` verificando que o engine em uso nos testes é `django.db.backends.dummy`, que abrir uma conexão levanta erro e que uma consulta do ORM (por exemplo `User.objects.count()` de `django.contrib.auth`) em um teste sem a marca `django_db` falha com a mensagem de acesso proibido do pytest-django

### Implementation for User Story 3

- [ ] T026 [US3] Verificar o gate de cobertura: executar `pytest` e confirmar que a cobertura total é de 90% ou mais; executar `pytest --cov-fail-under=101` e confirmar que o comando termina com código diferente de 0 informando a porcentagem atual
- [ ] T027 [US3] Verificar o isolamento: remover temporariamente o `.env` (se existir) e executar `pytest`, confirmando que a suíte passa sem variáveis de ambiente reais e sem conexão de rede
- [ ] T028 [US3] Atualizar `README.md` com a seção de testes: comando `pytest`, relatório de cobertura, regra de 90% mínimo, a política de testes sem banco com mocks e a execução sem `.env`

**Checkpoint**: suíte e gate de cobertura funcionando e documentados.

---

## Phase 6: User Story 4 - Padronizar o estilo do código (Priority: P2)

**Goal**: verificação PEP 8 por um comando documentado.

**Independent Test**: `ruff check .` termina sem erros no código da feature e lista arquivo e linha em um código fora do padrão.

### Implementation for User Story 4

- [ ] T029 [US4] Executar `ruff check .` (configuração em `pyproject.toml`) e corrigir todos os problemas encontrados em `config/`, `apps/` e `tests/`
- [ ] T030 [US4] Verificar que a ferramenta detecta violações: criar temporariamente `config/_lint_probe.py` com um import não utilizado e uma linha acima de 100 colunas, confirmar que `ruff check .` falha listando arquivo e linha, e remover o arquivo em seguida
- [ ] T031 [US4] Atualizar `README.md` com a seção de estilo: `ruff check .`, regras ativas (E, W, F, I) e limite de 100 colunas

**Checkpoint**: estilo verificável e documentado.

---

## Phase 7: User Story 5 - Permitir o consumo por um frontend separado (Priority: P2)

**Goal**: o navegador consegue chamar a API a partir das origens configuradas e é bloqueado nas demais.

**Independent Test**: com `CORS_ALLOWED_ORIGINS=http://localhost:5500`, uma requisição com essa origem recebe `Access-Control-Allow-Origin` e uma com outra origem não recebe.

### Tests for User Story 5

- [ ] T032 [P] [US5] Criar `tests/unit/config/test_cors.py` com `override_settings`: origem permitida recebe o cabeçalho `Access-Control-Allow-Origin`, origem não listada não recebe, lista vazia por padrão não autoriza ninguém e a lista é lida de `CORS_ALLOWED_ORIGINS` separada por vírgula

### Implementation for User Story 5

- [ ] T033 [US5] Atualizar `config/settings.py` adicionando `corsheaders` a `INSTALLED_APPS`, `corsheaders.middleware.CorsMiddleware` ao início de `MIDDLEWARE` (antes de `django.middleware.common.CommonMiddleware`) e `CORS_ALLOWED_ORIGINS` lido da variável `CORS_ALLOWED_ORIGINS` (lista separada por vírgula, padrão vazia)
- [ ] T034 [US5] Atualizar `README.md` com a seção de CORS: variável `CORS_ALLOWED_ORIGINS`, exemplo para o frontend em `http://localhost:5500` e a nota de que o frontend fica em repositório separado

**Checkpoint**: frontend separado consegue consumir a API.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: fechamento da feature

- [ ] T035 Revisar o `README.md` contra o FR-015: versão do Python, instalação, variáveis de ambiente, verificação de conexão, migrations, execução, testes e verificação de estilo, todos presentes
- [ ] T036 Verificar a ausência de segredos: buscar no repositório (fora de `.venv`) por senhas, chaves e endpoints reais e confirmar que `.env` não está rastreado pelo Git
- [ ] T037 Executar `pytest` e `ruff check .` na árvore final e confirmar cobertura total de 90% ou mais e nenhum erro de estilo
- [ ] T038 Executar a validação do `specs/001-backend-foundation/quickstart.md` (passos 1 a 9) com o RDS real, confirmando os resultados esperados de cada passo

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sem dependências
- **Foundational (Phase 2)**: depende do Setup e **bloqueia todas as histórias**
- **User Stories (Phase 3 a 7)**: dependem da Foundational
  - US1, US2 e US3 são P1; US4 e US5 são P2
  - Podem seguir em paralelo (com equipe) ou em ordem de prioridade
- **Polish (Phase 8)**: depende das histórias desejadas concluídas

### User Story Dependencies

- **US1 (P1)**: depende só da Foundational
- **US2 (P1)**: depende só da Foundational (usa a configuração de banco de `config/settings.py`)
- **US3 (P1)**: depende só da Foundational (a configuração do pytest está em T011); T026 só é conclusivo quando US1 e US2 tiverem testes
- **US4 (P2)**: depende de existir código a verificar (após US1 ao menos)
- **US5 (P2)**: depende da Foundational; T033 edita `config/settings.py`, então não deve rodar junto com outra edição do mesmo arquivo

### Within Each User Story

- Testes antes da implementação, confirmando que falham
- `README.md` é editado por várias histórias; as edições devem ser sequenciais (sem `[P]`)

### Parallel Opportunities

- Setup: T002 e T003 em paralelo
- Foundational: T008, T009 e T010 em paralelo após T007
- US1: T013, T014 e T015 em paralelo; T017 em paralelo com T016
- US2: T019, T020 e T021 em paralelo
- US1, US2 e US3 podem ser tocadas por pessoas diferentes após a Foundational

---

## Parallel Example: User Story 2

```text
# Testes da US2 juntos:
Task: "Criar tests/unit/config/test_settings.py"
Task: "Criar tests/unit/core/test_check_db.py"
Task: "Criar tests/unit/core/test_safe_migrate.py"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1: Setup
2. Phase 2: Foundational (bloqueia tudo)
3. Phase 3: US1
4. **PARAR e validar**: o backend inicia e `/api/v1/health/` responde
5. Seguir para US2 e US3 (também P1) antes de considerar a fundação utilizável

### Incremental Delivery

1. Setup + Foundational → esqueleto pronto
2. US1 → backend iniciando (MVP)
3. US2 → conexão e migrations no RDS
4. US3 → gate de testes e cobertura
5. US4 → estilo
6. US5 → CORS para o frontend
7. Polish → validação final

---

## Notes

- Tarefas `[P]` = arquivos diferentes e sem dependências
- Nenhum teste pode acessar banco de dados; usar `unittest.mock` para a conexão e o ORM
- Nenhuma tarefa cria entidades de negócio; os módulos de domínio ficam vazios
- Fora do escopo: hospedagem, deploy, backup, monitoramento e CI de deploy
- Fazer commit após cada tarefa ou grupo lógico
