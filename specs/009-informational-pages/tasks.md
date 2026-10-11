---

description: "Lista de tarefas de Páginas Informativas (Sobre e Contato)"
---

# Tasks: Páginas Informativas (Sobre e Contato)

**Input**: Documentos de design em `/specs/009-informational-pages/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Incluídos. A constituição (Princípio III) exige testes unitários com mocks, sem acesso a banco, e
cobertura total mínima de 90%. Os testes de US1 são escritos antes da correção e o caso de CSRF deve falhar
(red: 403 HTML) antes de passar (green: 404 JSON).

**Organization**: Tarefas agrupadas por história de usuário (US1 a US3 da spec). Não há models, migrations,
dependências nem rotas novas. A única mudança de código de produção é um decorador em `api_not_found`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência de tarefa incompleta)
- **[Story]**: história de usuário à qual a tarefa pertence (US1 a US3)
- Os caminhos são relativos à raiz do repositório

## Path Conventions

Projeto único com o Django na raiz: `config/`, `apps/` e `tests/unit/<área>/`. Os diretórios de teste não
têm `__init__.py`; seguir o padrão. Mensagens em português. Linha de código com no máximo 100 caracteres
(ruff). Python do projeto: `.venv/Scripts/python.exe` (`python -m pytest`).

---

## Phase 1: Setup

- [X] T001 Rodar `python -m pytest` e `python manage.py makemigrations --check --dry-run` para registrar a linha de base (suíte verde, cobertura >= 90%, "No changes detected") antes de qualquer alteração

---

## Phase 2: Foundational

Nenhuma tarefa bloqueante: não há modelos, configuração nem dependências novas. As histórias podem começar após T001.

---

## Phase 3: User Story 1 - Backend não expõe nem guarda dados de Sobre e Contato (Priority: P1) 🎯 MVP

**Goal**: nenhuma rota, modelo ou cadastro administrativo de contato/Sobre; qualquer método a caminhos
plausíveis sob `/api/` devolve `404` JSON `{"detail": "Não encontrado."}` mesmo com CSRF ativo, sem gravar
nem logar o corpo.

**Independent Test**: `python -m pytest tests/unit/core/test_no_informational_pages.py tests/unit/core/test_error_views.py`.

### Tests for User Story 1 (escrever primeiro; os de CSRF devem falhar antes de T006)

- [X] T002 [P] [US1] Criar `tests/unit/core/test_no_informational_pages.py` com testes que varrem `get_resolver()` (recursivamente, incluindo `include`) e falham se algum padrão de URL contiver, em minúsculas, `contact`, `contato`, `about`, `sobre` ou `message` (lista de exceções vazia por padrão, ver research.md D4); incluir um teste de sanidade de que a varredura encontra as rotas conhecidas (`activities`, `units`, `categories`)
- [X] T003 [P] [US1] No mesmo `tests/unit/core/test_no_informational_pages.py`, testes que percorrem `django.apps.apps.get_models()` e `django.contrib.admin.site._registry` e falham se o nome de algum modelo ou `ModelAdmin` contiver as mesmas palavras-chave (data-model.md: nenhuma entidade "Mensagem de contato" nem "Conteúdo da página Sobre"); incluir sanidade de que `Activity` aparece na varredura
- [X] T004 [P] [US1] No mesmo `tests/unit/core/test_no_informational_pages.py`, teste parametrizado com `Client(enforce_csrf_checks=True, HTTP_HOST="localhost")` e `GET`/`POST`/`PUT`/`DELETE` nos caminhos de contracts/no-informational-endpoints.md (`/api/contact/`, `/api/contato/`, `/api/v1/contact/`, `/api/v1/contato/`, `/api/about/`, `/api/sobre/`, `/api/v1/about/`, `/api/v1/sobre/`) exigindo status `404`, `Content-Type` `application/json` e corpo exatamente `{"detail": "Não encontrado."}`
- [X] T005 [P] [US1] No mesmo arquivo, teste com `caplog` (nível `DEBUG`, todos os loggers) que envia `POST /api/contato/` com corpo contendo a sentinela `sentinela-contato-123` e exige que ela não apareça em nenhum registro nem na resposta; incluir verificação de que a view não lê o corpo (`request.body` não é acessado, usando `RequestFactory` e `unittest.mock`) e de que nenhuma consulta ao banco é feita (o acesso a banco já é bloqueado pela configuração de testes)

### Implementation for User Story 1

- [X] T006 [US1] Em `apps/core/error_views.py`, importar `csrf_exempt` de `django.views.decorators.csrf` e decorar `api_not_found` com ele, atualizando a docstring para dizer que a rota coringa é isenta de CSRF porque não lê corpo nem altera estado (plan.md, research.md D1); não alterar `handler404` nem `handler500`
- [X] T007 [P] [US1] Em `tests/unit/core/test_error_views.py`, acrescentar teste de que `api_not_found.csrf_exempt is True` e um teste com `Client(enforce_csrf_checks=True)` para `POST` em `/api/v1/nada/` devolvendo `404` JSON (cobre a regressão do 403 HTML)

**Checkpoint**: T002 a T005 e T007 passam; antes de T006, T004 e T007 falham com 403 HTML.

---

## Phase 4: User Story 2 - Equipe do frontend sabe o que esperar do backend (Priority: P2)

**Goal**: três perguntas de escopo respondidas só pela documentação (endpoint? envio? origem do texto de Sobre?).

**Independent Test**: ler DOC-05, README e DOC-04 e responder às perguntas de contracts/no-informational-endpoints.md em até 2 minutos.

- [X] T008 [P] [US2] Em `docs/05-especificacao-api-rest.md`, acrescentar após a seção 3.2 a subseção "3.3. Sobre e Contato (sem endpoints)" declarando que não há endpoints de Sobre nem de Contato, que o frontend não deve chamar a API para essas páginas e que qualquer método a caminhos inexistentes sob `/api/` devolve `404` JSON `{"detail": "Não encontrado."}`; acrescentar linha ao histórico de alterações da seção 16
- [X] T009 [P] [US2] Em `README.md`, na parte que já cita Sobre e Contato (perto de "Fora do escopo"), explicitar que Sobre tem texto fixo no frontend, que Contato é demonstrativa (não envia nem armazena mensagens) e que a API responde `404` JSON a esses caminhos; manter o restante do README intacto
- [X] T010 [P] [US2] Em `docs/04-backlog-do-produto.md`, nas histórias US-035 e US-036, conferir/ajustar os critérios para constar "somente frontend", "não envia nem armazena mensagens" e "não há endpoint no backend" (já existem; apenas completar o que faltar sem reescrever)

**Checkpoint**: as três perguntas de escopo têm resposta direta em DOC-05, README e DOC-04.

---

## Phase 5: User Story 3 - Fechamento do backlog e do escopo documentados (Priority: P3)

**Goal**: todos os épicos EP-01 a EP-09 com destino documentado e nenhuma pendência de Sobre/Contato.

**Independent Test**: percorrer DOC-04 e `docs/PENDENCIAS.md` e confirmar o destino de cada épico.

- [X] T011 [P] [US3] Em `docs/04-backlog-do-produto.md`, acrescentar à tabela da seção 16 a linha `| 0.3 | Feature 009: EP-09 fechado no backend; US-035 e US-036 seguem somente frontend e uma verificação automatizada impede rotas, modelos e cadastros de contato/Sobre. |` e, na tabela de épicos (seção 3), manter EP-09 como "somente frontend"
- [X] T012 [P] [US3] Em `docs/PENDENCIAS.md`, atualizar a data/feature no cabeçalho para a feature 009, acrescentar em "Decisões já tomadas" uma linha sobre a feature 009 (EP-09 fechado: sem endpoint; rota coringa `/api/` isenta de CSRF devolve 404 JSON) e confirmar que não há item aberto de Sobre/Contato
- [X] T013 [US3] Conferir a coerência entre README, DOC-04 e `docs/PENDENCIAS.md` (lista do que o backend entrega e do que está fora do escopo coincidem; EP-01 a EP-09 com destino) e corrigir divergências encontradas

**Checkpoint**: nenhum item aberto de Sobre/Contato no backend; épicos todos com destino.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T014 Rodar `python -m pytest` e confirmar suíte verde e cobertura total >= 90% (`--cov-fail-under=90` ativo)
- [X] T015 [P] Rodar `python -m ruff check .` e `python manage.py makemigrations --check --dry-run` (esperado: sem erros e "No changes detected")
- [X] T016 Executar o quickstart em `specs/009-informational-pages/quickstart.md` (cenários 1 e 3 obrigatórios; cenário 2 com o servidor local, se possível) e marcar o `Status` da spec como `Implemented`

---

## Dependencies & Execution Order

### Phase Dependencies

- Setup (T001) → todas as histórias.
- US1, US2 e US3 são independentes entre si; recomendada a ordem de prioridade (P1 → P2 → P3).
- Polish depende de todas as histórias desejadas.

### Within User Story 1

- T002 a T005 e T007 (testes) antes de T006; T004 e T007 devem falhar antes de T006.
- T002 a T005 estão no mesmo arquivo: escrevê-las em sequência, não em paralelo de fato (o `[P]` indica apenas independência lógica).

### Within User Story 2 e 3

- T008 a T010 e T011/T012 tocam arquivos diferentes e podem ser paralelas; T010 e T011 editam o mesmo `docs/04-backlog-do-produto.md`, então devem ser feitas em sequência; T013 por último.

### Parallel Opportunities

- US1: T007 em paralelo com T002 a T005 (arquivo diferente).
- US2: T008 e T009 em paralelo.
- US3: T012 em paralelo com T011 (arquivos diferentes).
- Polish: T015 em paralelo com T014.

## Parallel Example: User Story 1

```text
Em paralelo (arquivos diferentes):
T002-T005 tests/unit/core/test_no_informational_pages.py
T007      tests/unit/core/test_error_views.py

Depois:
T006 apps/core/error_views.py
```

## Implementation Strategy

### MVP First

Phases 1 e 3 (US1): é a única mudança de código e a única parte verificável do EP-09 no backend.
Validar com `python -m pytest tests/unit/core` e o cenário 2 do quickstart antes de seguir.

### Incremental Delivery

1. Setup → linha de base verde.
2. US1 → proteção de escopo + correção do 403 HTML (MVP).
3. US2 → documentação para o frontend.
4. US3 → fechamento do backlog e das pendências.
5. Polish → cobertura, lint, quickstart.

## Notes

- Nenhuma tarefa cria modelo, migration, dependência, app ou rota.
- Os testes existentes `test_error_views.py` e `test_public_privacy.py` devem continuar passando.
- Fazer commits pequenos por tarefa ou grupo de tarefas, com revisão por pull request antes do merge em `main`.
