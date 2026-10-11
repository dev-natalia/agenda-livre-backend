---

description: "Lista de tarefas de Ambientes e Registro de Erros"
---

# Tasks: Ambientes e Registro de Erros

**Input**: Documentos de design em `/specs/008-environments-logging/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Incluídos. A constituição (Princípio III) exige testes unitários com mocks, sem acesso a banco, e
cobertura total mínima de 90%. Nenhum teste abre conexão com banco nem grava em `logs/`: use `tmp_path`,
`caplog`, `logging.LogRecord`, `RequestFactory`/`APIRequestFactory` e `unittest.mock`. Os testes de cada
história são escritos antes da implementação e devem falhar (red) antes de passar (green).

**Organization**: Tarefas agrupadas por história de usuário (US1 a US3 da spec). Não há models,
migrations, dependências nem rotas novas.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência de tarefa incompleta)
- **[Story]**: história de usuário à qual a tarefa pertence (US1 a US3)
- Os caminhos são relativos à raiz do repositório

## Path Conventions

Projeto único com o Django na raiz: `config/`, `apps/` e `tests/unit/<área>/`. Os diretórios de teste não
têm `__init__.py`; seguir o padrão. Mensagens em português. Linha de código com no máximo 100 caracteres
(ruff). Testes de logging escrevem só em `tmp_path`.

---

## Phase 1: Setup

- [X] T001 Adicionar `logs/` ao `.gitignore`
- [X] T002 [P] Em `config/env.py`, acrescentar a `OPTIONAL_VARS` os nomes `DJANGO_HTTPS_ONLY`, `LOG_DIR`, `LOG_LEVEL`, `LOG_MAX_BYTES` e `LOG_BACKUP_COUNT` (a fixture `clean_env` de `tests/conftest.py` usa `ALL_VARS`)

---

## Phase 2: Foundational (bloqueia todas as histórias)

**Objetivo**: leitura validada das novas variáveis, usada por US1 e US2.

- [X] T003 [P] Escrever em `tests/unit/config/test_env.py` testes de `get_int` (padrão quando vazio; valor inválido ou abaixo do mínimo levanta `ImproperlyConfigured` citando o nome da variável e **não** o valor) e de `get_log_level` (padrão `ERROR`; aceita `WARNING`, `ERROR`, `CRITICAL` sem diferenciar maiúsculas; outro valor levanta `ImproperlyConfigured`)
- [X] T004 Implementar em `config/env.py` `get_int(name, default, minimum)` e `get_log_level()` conforme T003, no estilo de `parse_port` e `get_ssl_mode`

**Checkpoint**: `python -m pytest tests/unit/config/test_env.py` passa.

---

## Phase 3: User Story 1 — Investigar uma falha pelos registros locais (Priority: P1) 🎯 MVP

**Goal**: falhas inesperadas e de infraestrutura ficam em arquivo rotativo, sem segredos, sem alterar a resposta ao visitante.

**Independent Test**: provocar uma falha inesperada e uma falha de conexão e verificar o registro persistente com tipo e contexto, sem senha, chave nem cookie ([contracts/logging.md](contracts/logging.md)).

### Tests for User Story 1

- [X] T005 [P] [US1] Criar `tests/unit/config/test_log_redaction.py`: `RedactingFormatter` troca por `***` (a) os valores reais de `DJANGO_SECRET_KEY` e `DB_PASSWORD` informados, ignorando segredos vazios ou com menos de 4 caracteres, (b) pares `password`, `passwd`, `pwd`, `secret`, `token`, `api_key`, `authorization`, `cookie`, `set-cookie`, `sessionid`, `csrftoken` nas formas `chave=valor` e `chave: valor`, sem diferenciar maiúsculas, (c) `esquema://usuario:senha@host` vira `esquema://usuario:***@host`; o mascaramento vale também para o rastreamento de uma exceção cuja mensagem contém o segredo (FR-002, SC-002)
- [X] T006 [P] [US1] Criar `tests/unit/config/test_logging_config.py`: `build_logging(log_dir, level, max_bytes, backup_count, secrets)` devolve dicionário aceito por `logging.config.dictConfig`; handler de arquivo é `RotatingFileHandler` com `delay=True`, `encoding="utf-8"`, `maxBytes` e `backupCount` informados e arquivo `agenda-livre.log`; nível do handler vem do parâmetro; loggers `apps`, `config` e `django.request` usam o arquivo; com `tmp_path`, gravar acima de `max_bytes` rotaciona e o total de arquivos nunca passa de `max_bytes * (backup_count + 1)` (FR-004, SC-004); registro `WARNING` e 4xx não vão ao arquivo com nível `ERROR` (FR-006)
- [X] T007 [P] [US1] Em `tests/unit/config/test_logging_config.py`, acrescentar testes de diretório inválido: quando `os.makedirs` falha (mock `OSError`), `build_logging` devolve configuração só com console, sem handler de arquivo, e avisa em `stderr` sem levantar exceção (FR-007); e de falha em `emit()` (mock `OSError`) que não propaga exceção
- [X] T008 [P] [US1] Criar `tests/unit/core/test_exception_logging.py`: com `LOGGING` montado sobre `tmp_path`, uma exceção inesperada em `public_exception_handler` grava uma linha `ERROR` com método, caminho e tipo da exceção, e **sem** *query string*, cabeçalhos, cookies nem corpo; a resposta continua 500 com apenas `{"detail": "Ocorreu um erro inesperado. Tente novamente mais tarde."}` (SC-003); `ValidationError`, `NotFound`, `MethodNotAllowed` e `PermissionDenied` não geram linha no arquivo; uma exceção cuja mensagem contém a senha do banco chega mascarada ao arquivo
- [X] T009 [P] [US1] Criar `tests/unit/config/test_startup_logging.py`: `log_startup_failure` grava no arquivo de `LOG_DIR` (de `os.environ`, padrão `logs`, usar `monkeypatch`/`tmp_path`) uma linha `ERROR` com a mensagem de `ImproperlyConfigured` contendo só **nomes** de variáveis; recarregar `config.settings` com `DB_HOST` ausente levanta `ImproperlyConfigured`, chama `log_startup_failure` e não registra nenhum valor de variável (FR-003)
- [X] T010 [P] [US1] Em `tests/unit/core/test_check_db.py` e `tests/unit/core/test_safe_migrate.py`, acrescentar testes (conexão simulada com mock): falha de conexão em `check_db` registra via `caplog` uma linha `ERROR` com o tipo da falha (de `classify_failure`), host e porta, sem a senha e sem o texto bruto do driver; falha em `call_command("migrate")` dentro de `safe_migrate` registra o tipo da exceção e relança

### Implementation for User Story 1

- [X] T011 [US1] Criar `config/logging_config.py` com `RedactingFormatter(logging.Formatter)` que formata o registro completo (mensagem e rastreamento) e só então mascara o texto final conforme [research.md](research.md) D3 (T005)
- [X] T012 [US1] Em `config/logging_config.py`, implementar `build_logging(log_dir, level, max_bytes, backup_count, secrets)` conforme [research.md](research.md) D1, D2 e D6: formato `%(asctime)s %(levelname)s %(name)s: %(message)s`, handler `RotatingFileHandler` em `<log_dir>/agenda-livre.log` com `delay=True`, console como alternativa quando `os.makedirs(log_dir, exist_ok=True)` falha (T006, T007)
- [X] T013 [US1] Em `config/logging_config.py`, implementar `log_startup_failure(error)`: monta o mesmo formatter e handler com `LOG_DIR` lido direto de `os.environ` (padrão `logs`, relativo à raiz do repositório), grava uma linha `ERROR` e nunca levanta exceção (T009)
- [X] T014 [US1] Em `config/settings.py`, envolver a leitura de `env.require_env(env.REQUIRED_VARS)` em `try/except ImproperlyConfigured` que chama `log_startup_failure(exc)` e relança; definir `LOGGING = build_logging(...)` com `LOG_DIR` (relativo à raiz do repositório), `env.get_log_level()`, `env.get_int("LOG_MAX_BYTES", 1048576, 1)`, `env.get_int("LOG_BACKUP_COUNT", 5, 0)` e `secrets=(SECRET_KEY, DATABASES password)` (T008, T009)
- [X] T015 [P] [US1] Em `config/settings_test.py`, definir `LOG_DIR` num diretório temporário do sistema (por exemplo `tempfile.mkdtemp`) antes de importar `config.settings`, para que nenhum teste grave em `logs/` (FR-010)
- [X] T016 [P] [US1] Em `apps/core/management/commands/check_db.py`, registrar com `logging.getLogger(__name__).error` a falha de conexão: tipo (`classify_failure`), host e porta; manter a mensagem ao terminal e o `CommandError` como estão (T010)
- [X] T017 [P] [US1] Em `apps/core/management/commands/safe_migrate.py`, envolver `call_command("migrate", ...)` em `try/except Exception`, registrar `type(exc).__name__` e o banco de destino (host e porta) e relançar (T010)

**Checkpoint**: T005 a T010 passam; o arquivo é criado em `tmp_path` e a resposta ao visitante não muda.

---

## Phase 4: User Story 2 — Configurar o sistema por ambiente com segurança apropriada (Priority: P1)

**Goal**: proteções de transporte e cookies variam com o modo, e toda variável está documentada.

**Independent Test**: carregar as settings com `DJANGO_DEBUG` verdadeiro e falso e conferir as proteções; conferir que toda variável de `ALL_VARS` está no README e no `.env.example` ([contracts/environment.md](contracts/environment.md)).

### Tests for User Story 2

- [X] T018 [P] [US2] Criar `tests/unit/config/test_security_settings.py` usando a fixture `load_settings`: com `DJANGO_DEBUG=False` e sem `DJANGO_HTTPS_ONLY` → `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE` e `CSRF_COOKIE_SECURE` verdadeiros e `SECURE_HSTS_SECONDS == 3600`; com `DJANGO_DEBUG=True` → todos desligados e `SECURE_HSTS_SECONDS == 0`; `DJANGO_DEBUG=False` com `DJANGO_HTTPS_ONLY=False` → desligados; `DJANGO_DEBUG=True` com `DJANGO_HTTPS_ONLY=True` → ligados; valor inválido de `DJANGO_HTTPS_ONLY` levanta `ImproperlyConfigured`; em qualquer modo, `SECURE_CONTENT_TYPE_NOSNIFF` verdadeiro, `X_FRAME_OPTIONS == "DENY"`, `SESSION_COOKIE_HTTPONLY` verdadeiro, `SECURE_REFERRER_POLICY == "same-origin"` e `SECURE_PROXY_SSL_HEADER` não definido (FR-008)
- [X] T019 [P] [US2] Em `tests/unit/config/test_settings.py`, acrescentar testes das novas variáveis: padrões (`LOG_DIR` terminando em `logs`, nível `ERROR`, 1048576 bytes, 5 backups) e valores personalizados refletidos em `LOGGING`; `LOG_LEVEL`, `LOG_MAX_BYTES` e `LOG_BACKUP_COUNT` inválidos impedem a inicialização com mensagem sem o valor recebido (FR-005)
- [X] T020 [P] [US2] Criar `tests/unit/config/test_env_documentation.py`: cada nome em `config.env.ALL_VARS` aparece em `README.md` e em `.env.example` (lendo os arquivos pela raiz do repositório); o `.env.example` não contém `.rds.amazonaws.com` real nem chave aparentemente real (apenas os valores fictícios atuais) e nenhum arquivo `.env` está versionado (verificar `.gitignore` contendo `.env` e `logs/`) (FR-009, SC-005, SC-006)

### Implementation for User Story 2

- [X] T021 [US2] Em `config/settings.py`, definir `HTTPS_ONLY = env.get_bool("DJANGO_HTTPS_ONLY", not DEBUG)` e, a partir dele, `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE` e `SECURE_HSTS_SECONDS` (3600 quando verdadeiro, 0 caso contrário); sempre definir `SECURE_CONTENT_TYPE_NOSNIFF = True`, `X_FRAME_OPTIONS = "DENY"`, `SESSION_COOKIE_HTTPONLY = True` e `SECURE_REFERRER_POLICY = "same-origin"`; **não** definir `SECURE_PROXY_SSL_HEADER` ([research.md](research.md) D8) (T018, T019)
- [X] T022 [P] [US2] Atualizar `.env.example` com `DJANGO_HTTPS_ONLY`, `LOG_DIR`, `LOG_LEVEL`, `LOG_MAX_BYTES` e `LOG_BACKUP_COUNT`, com comentário e valor fictício ou padrão, sem segredos (T020)
- [X] T023 [P] [US2] Atualizar a tabela de variáveis em `README.md` com as cinco novas (obrigatoriedade, padrão e descrição, como em [data-model.md](data-model.md)) e acrescentar o aviso: com `DJANGO_DEBUG=False` em HTTP local é preciso `DJANGO_HTTPS_ONLY=False`, senão o login do painel não persiste (T020)

**Checkpoint**: T018 a T020 passam; `python manage.py check --deploy` sem avisos de HTTPS/cookies/HSTS com `DEBUG=False`.

---

## Phase 5: User Story 3 — Escopo de entrega e operação documentado (Priority: P3)

**Goal**: a documentação registra onde ficam os registros e o que está fora do escopo.

**Independent Test**: ler README, DOC-04, DOC-08 e `docs/PENDENCIAS.md` e confirmar o conteúdo dos cenários da US3.

- [X] T024 [P] [US3] Acrescentar ao `README.md` a seção "Registro de erros": local (`logs/agenda-livre.log`, configurável por `LOG_DIR`), rotação, o que é e o que nunca é gravado, como consultar (Git Bash e PowerShell) e a lista do que está fora do escopo (implantação, backup, monitoramento; Sobre e Contato são só frontend), conforme [contracts/logging.md](contracts/logging.md)
- [X] T025 [P] [US3] Em `docs/04-backlog-do-produto.md`, ajustar US-034 para "registro básico em arquivo local, com rotação e sem dados sensíveis" e registrar no histórico de alterações a feature 008 (US-032, US-033 e monitoramento permanecem fora do escopo; EP-09 só frontend)
- [X] T026 [P] [US3] Em `docs/08-estrategia-infraestrutura-deploy.md`, na seção 10 (logs), registrar a solução local (arquivo rotativo, nível `ERROR`, mascaramento, variáveis `LOG_*`) e que monitoramento e alertas seguem fora do escopo
- [X] T027 [P] [US3] Em `docs/PENDENCIAS.md`, atualizar a data, marcar a feature 008 no fluxo Spec Kit e registrar `DJANGO_HTTPS_ONLY` e os logs locais entre as decisões tomadas

---

## Phase 6: Polish & Cross-Cutting

- [X] T028 Executar `python -m pytest` e confirmar que toda a suíte passa sem acesso a banco e com cobertura total >= 90% (SC-007); corrigir lacunas de cobertura em `config/logging_config.py`
- [X] T029 [P] Executar `python -m ruff check .` e `python manage.py makemigrations --check --dry-run` (esperado: sem erros e "No changes detected")
- [X] T030 [P] Executar `git status --short` e confirmar que nenhum arquivo em `logs/` nem `.env` aparece como novo; remover resíduos
- [X] T031 Percorrer [quickstart.md](quickstart.md) (cenários 2 a 6) com o servidor local e conferir a resposta genérica, o conteúdo de `logs/agenda-livre.log` e a ausência de segredos
- [X] T032 Revisar [spec.md](spec.md): conferir que cada FR-001 a FR-012 e cada SC têm ao menos uma tarefa de teste ou de documentação coberta, e marcar o status da spec como pronto para revisão

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sem dependências.
- **Foundational (Phase 2)**: depende de T002; bloqueia US1 e US2 (T014, T019 e T021 usam `get_int`/`get_log_level`/`get_bool`).
- **US1 (Phase 3)** e **US2 (Phase 4)**: independentes entre si depois da Phase 2, mas ambas editam `config/settings.py` (T014 e T021): fazer em sequência, não em paralelo.
- **US3 (Phase 5)**: depende de US1 e US2 apenas para o texto final (variáveis e comportamento); pode ser escrita a qualquer momento.
- **Polish (Phase 6)**: depende de todas as histórias.

### Within Each Story

- Testes primeiro (red), depois implementação (green).
- US1: T011 → T012 → T013 → T014; T015, T016 e T017 em paralelo após T012.
- US2: T021 antes de rodar T018/T019; T022 e T023 antes de T020 passar.

### Parallel Opportunities

- Phase 1: T002 em paralelo com T001.
- US1: T005 a T010 em paralelo (arquivos diferentes); T015, T016 e T017 em paralelo.
- US2: T018, T019 e T020 em paralelo; T022 e T023 em paralelo.
- US3: T024 a T027 em paralelo.

## Parallel Example: User Story 1

```text
Em paralelo (testes):
T005 tests/unit/config/test_log_redaction.py
T006 tests/unit/config/test_logging_config.py
T008 tests/unit/core/test_exception_logging.py
T009 tests/unit/config/test_startup_logging.py
T010 tests/unit/core/test_check_db.py + test_safe_migrate.py

Depois, em paralelo (código):
T015 config/settings_test.py
T016 apps/core/management/commands/check_db.py
T017 apps/core/management/commands/safe_migrate.py
```

## Implementation Strategy

### MVP First

Phases 1, 2 e 3 (US1): é a única lacuna de código do EP-08 (registro persistente e sem segredos).
Validar com o cenário 2 do quickstart antes de seguir.

### Incremental Delivery

1. Setup + Foundational → variáveis lidas e validadas.
2. US1 → registros em arquivo (MVP).
3. US2 → proteções por modo e documentação das variáveis.
4. US3 → documentação de escopo.
5. Polish → cobertura, lint, quickstart.

## Notes

- Nenhuma tarefa cria modelo, migration, dependência ou rota.
- O teste existente `tests/unit/core/test_no_secret_in_logs.py` (feature 007) deve continuar passando; se algum caso colidir com o novo `LOGGING`, ajustar o teste sem enfraquecer a verificação.
- Fazer commits pequenos por tarefa ou grupo de tarefas, com revisão por pull request antes do merge em `main`.
