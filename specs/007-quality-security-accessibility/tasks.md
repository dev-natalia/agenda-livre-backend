---

description: "Lista de tarefas de Qualidade, Segurança e Acessibilidade"
---

# Tasks: Qualidade, Segurança e Acessibilidade

**Input**: Documentos de design em `/specs/007-quality-security-accessibility/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Incluídos. A constituição (Princípio III) exige testes unitários com mocks, sem acesso a banco, e
cobertura total mínima de 90%. Nenhum teste pode abrir conexão com banco: use objetos em memória
(`SimpleNamespace`, instâncias de modelo não salvas), `APIRequestFactory`/`RequestFactory`,
`unittest.mock` e relógio injetado. Os testes escritos para lacunas (US1) devem falhar antes da
correção (red) e passar depois (green).

**Organization**: Tarefas agrupadas por história de usuário (US1 a US4 da spec). Não há models,
migrations, dependências nem rotas públicas novas.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência de tarefa incompleta)
- **[Story]**: história de usuário à qual a tarefa pertence (US1 a US4)
- Os caminhos são relativos à raiz do repositório

## Path Conventions

Projeto único com o Django na raiz: `config/`, `apps/` e `tests/unit/<app>/`. Os diretórios de teste não
têm `__init__.py`; seguir o padrão. Mensagens de erro em português. Linha de código com no máximo 100
caracteres (`ruff`). Arquivos de teste novos devem ter nomes únicos na árvore (sem `__init__.py`, o
pytest exige basenames distintos).

---

## Phase 1: Setup

**Purpose**: confirmar a linha de base antes de mexer.

- [X] T001 Rodar `python -m pytest` e `python -m ruff check .` na raiz e anotar a contagem de testes e a cobertura atuais (esperado: 421 testes, 100%); rodar `python manage.py makemigrations --check --dry-run` (esperado: "No changes detected")

---

## Phase 2: Foundational

**Purpose**: utilitário de teste compartilhado pelas varreduras de privacidade e de rotas.

**⚠️ CRITICAL**: US2 depende de T002.

- [X] T002 Criar `tests/unit/core/error_helpers.py` com `FORBIDDEN_KEYS = {"created_by", "updated_by", "created_at", "updated_at", "status", "password", "secret", "is_staff", "is_superuser", "email", "username"}` e a função `find_forbidden_keys(value)` que percorre dicts e listas em qualquer profundidade e devolve o conjunto de chaves proibidas encontradas

**Checkpoint**: base pronta.

---

## Phase 3: User Story 1 — Entradas inválidas rejeitadas com segurança (Priority: P1) 🎯 MVP

**Goal**: erro inesperado, rota inexistente sob `/api/` e página inválida respondem JSON seguro e útil; as validações existentes ganham regressão por categoria de entrada.

**Independent Test**: `python -m pytest tests/unit/core tests/unit/consultation tests/unit/activities tests/unit/schedules` passa; com `DJANGO_DEBUG=True` e `False`, os `curl` do passo 2 do quickstart devolvem JSON sem pilha.

### Tests for User Story 1 (escrever primeiro; devem falhar)

- [X] T003 [US1] Em `tests/unit/core/test_exceptions.py`, substituir `test_non_api_exception_is_left_to_django` por testes de que `public_exception_handler(RuntimeError("segredo"), contexto)` devolve status 500 e corpo exatamente `{"detail": "Ocorreu um erro inesperado. Tente novamente mais tarde."}` (sem a mensagem original) e que `logger.exception` é chamado uma vez com método e caminho da requisição, sem corpo, parâmetros nem cabeçalhos (usar `caplog` ou `mock.patch`)
- [X] T004 [P] [US1] Criar `tests/unit/core/test_error_views.py`: com `RequestFactory`, `handler404` em `/api/v1/nada/` devolve JSON 404 `{"detail": "Não encontrado."}`; `handler500` em `/api/v1/x/` devolve JSON 500 com a mensagem genérica; em `/admin/x/` ambos delegam a `django.views.defaults.page_not_found` / `server_error` (simulados com `mock.patch`); `config.urls.handler404` e `handler500` apontam para as novas funções
- [X] T005 [P] [US1] Em `tests/unit/consultation/test_pagination.py`, trocar `test_page_out_of_range_is_not_found` por testes de que `?page=99` e `?page=abc` levantam `ValidationError` com `{"page": ["Informe uma página válida."]}` e de que, passando por `public_exception_handler`, resultam em 400 com `errors.page`
- [X] T006 [P] [US1] Criar `tests/unit/consultation/test_invalid_input_matrix.py`, parametrizado com `ConsultationQuerySerializer`: data fora do formato, `date` junto de `date_from`, `date_from` > `date_to`, intervalo > 366 dias, UUID inválido em `unit` e `category`, `q` e `neighborhood` com mais de 100 caracteres; cada caso deve ser inválido e a mensagem deve estar em português e citar o campo; incluir caso com parâmetros desconhecidos, repetidos e vazios, que continua válido (ignorados)
- [X] T007 [P] [US1] Criar `tests/unit/activities/test_activity_validation_matrix.py` com instâncias não salvas de `Activity`: `clean()` recusa título e descrição em branco (com espaços), `external_registration_url` com `ftp://`, `javascript:alert(1)` e texto sem esquema, e aceita `http://` e `https://`; `change_status` recusa transição inválida citando as duas situações e não altera `updated_by` nem salva (mock de `save`)
- [X] T008 [P] [US1] Criar `tests/unit/schedules/test_schedule_validation_matrix.py`: `Schedule.clean()` e `ScheduleAdminForm` recusam fim antes do início (datas e horários), tipo inválido, recorrente sem dias, pontual com dias e dia fora de 0 a 6; as mensagens estão em português e apontam o campo

### Implementation for User Story 1

- [X] T009 [US1] Em `apps/core/exceptions.py`, adicionar `logger = logging.getLogger(__name__)` e, em `public_exception_handler`, quando `exception_handler` devolver `None`, registrar `logger.exception("Erro inesperado em %s %s", request.method, request.path)` e devolver `Response({"detail": "Ocorreu um erro inesperado. Tente novamente mais tarde."}, status=500)`; a requisição vem de `context["request"]` (tolerar ausência)
- [X] T010 [US1] Criar `apps/core/error_views.py` com `handler404(request, exception)` e `handler500(request)`: se `request.path.startswith("/api/")` devolver `JsonResponse` ({"detail": "Não encontrado."} 404; mensagem genérica 500); senão delegar a `django.views.defaults.page_not_found(request, exception)` e `server_error(request)`
- [X] T011 [US1] Em `config/urls.py`, além de `apps.core.error_views.api_not_found` como rota coringa `^api/` (com `DEBUG` ligado o Django ignora `handler404`), registrar `handler404 = "apps.core.error_views.handler404"` e `handler500 = "apps.core.error_views.handler500"`
- [X] T012 [US1] Em `apps/consultation/pagination.py`, sobrescrever `paginate_queryset` para capturar o `NotFound` da DRF e levantar `rest_framework.exceptions.ValidationError({"page": ["Informe uma página válida."]})`
- [X] T013 [US1] Rodar `python -m pytest tests/unit/core tests/unit/consultation tests/unit/activities tests/unit/schedules` e corrigir o que falhar; qualquer teste da feature 006 que dependa do 404 de página inválida deve ser atualizado para o novo contrato (`specs/007-quality-security-accessibility/contracts/error-format.md`)

**Checkpoint**: US1 completa e testável sozinha (MVP).

---

## Phase 4: User Story 2 — Área pública aberta e sem vazamento (Priority: P1)

**Goal**: garantia automatizada de acesso anônimo, somente leitura e ausência de dados internos.

**Independent Test**: `python -m pytest tests/unit/consultation/test_public_privacy.py` passa.

- [X] T014 [US2] Criar `tests/unit/consultation/test_public_privacy.py`: montar atividade, unidade, categoria, programação e públicos-alvo em memória (reaproveitar `tests/unit/consultation/consultation_helpers.py`) e afirmar, com `find_forbidden_keys` (T002), que a resposta de cada serializer público (`ActivityListItemSerializer`, `ActivityDetailSerializer`, `UnitItemSerializer`, `CategoryItemSerializer`) e de cada erro do contrato (400, 404, 405, 500) não contém nenhuma chave proibida
- [X] T015 [P] [US2] No mesmo arquivo, parametrizar sobre todas as rotas de `apps.consultation.urls` e `apps.core.urls`: `POST`, `PUT`, `PATCH` e `DELETE` (autenticados e anônimos, via `APIRequestFactory` e `force_authenticate`) respondem 405 `{"detail": "Método não permitido."}` e nenhuma função de serviço é chamada; `GET` anônimo é aceito (serviços simulados)
- [X] T016 [P] [US2] No mesmo arquivo, afirmar que `PublicAPIView.authentication_classes == []`, `permission_classes == [AllowAny]` e `http_method_names == ["get", "head", "options"]`, e que atividade não publicada e identificador inexistente produzem exatamente o mesmo status e corpo no detalhe
- [X] T017 [P] [US2] Criar `tests/unit/core/test_admin_area_protected.py`: `admin.site.has_permission` recusa anônimo, usuário inativo e usuário sem `is_staff`; confirmar que a resolução de `/admin/` exige login (a view `admin.site.index` envolta em `admin_view` redireciona anônimo)

**Checkpoint**: US1 e US2 funcionam de forma independente.

---

## Phase 5: User Story 3 — Auditoria consistente (Priority: P1)

**Goal**: criador, atualizador e horários corretos por todos os caminhos; autoria protegida; política documentada.

**Independent Test**: `python -m pytest tests/unit/activities/test_audit_paths.py tests/unit/schedules/test_audit_paths.py tests/unit/core/test_author_protection.py` passa.

- [X] T018 [P] [US3] Criar `tests/unit/activities/test_audit_paths.py` (usuários simulados A e B, `save` simulado): `ActivityAdmin.save_model` na criação grava `created_by` e `updated_by` = A; na edição por B mantém `created_by` e muda `updated_by`; `save_formset` com programações novas e existentes grava `created_by` só nas novas e `updated_by` = B em todas, inclusive as com `schedule_form.instance in saved`; `change_status` bem-sucedido grava `updated_by` e inclui `"updated_at"` em `update_fields`; `change_status` recusado ou sem mudança não altera `updated_by` nem chama `save`
- [X] T019 [P] [US3] Criar `tests/unit/schedules/test_audit_paths.py`: `ScheduleAdmin.save_model` na criação e na edição, com A e B, com as mesmas garantias de T018
- [X] T020 [P] [US3] Criar `tests/unit/core/test_author_protection.py`: por introspecção de `Activity._meta` e `Schedule._meta`, `created_by` e `updated_by` têm `remote_field.on_delete is models.PROTECT` e `editable is False`; `created_at` tem `auto_now_add=True` e `updated_at` tem `auto_now=True`
- [X] T021 [P] [US3] Em `tests/unit/core/test_author_protection.py`, afirmar que `ActivityAdmin` e `ScheduleAdmin` listam `created_by`, `updated_by`, `created_at` e `updated_at` em `readonly_fields`
- [X] T022 [US3] Se algum teste de T018 a T021 falhar por lacuna real, corrigir o caminho em `apps/activities/admin.py`, `apps/activities/services.py` ou `apps/schedules/admin.py` com a menor mudança possível, sem alterar o esquema; senão registrar na descrição do PR que a auditoria já estava correta
- [X] T023 [US3] Atualizar `docs/PENDENCIAS.md`: marcar a pendência "Política de exclusão (`on_delete`) e de auditoria" como resolvida, apontando para `specs/007-quality-security-accessibility/contracts/audit-policy.md`

**Checkpoint**: US1 a US3 independentes.

---

## Phase 6: User Story 4 — Dados e erros que sustentam um frontend acessível (Priority: P2)

**Goal**: garantir por teste que a API entrega texto legível e erros por campo; documentar a divisão backend/frontend.

**Independent Test**: `python -m pytest tests/unit/consultation/test_accessibility_data.py tests/unit/core/test_error_messages.py` passa.

- [X] T024 [P] [US4] Criar `tests/unit/consultation/test_accessibility_data.py`: o detalhe devolve `unit.name`, `category.name`, `target_audiences[].name` e `weekday_names` como textos não vazios; horários no formato `HH:MM` e datas `AAAA-MM-DD`; `address`, `description` (listas de unidades e categorias) e `external_registration_url` vazios saem como `null`, nunca `""`
- [X] T025 [P] [US4] Criar `tests/unit/core/test_error_messages.py`: percorrer todas as mensagens de validação definidas em `apps/consultation/serializers.py`, `apps/consultation/pagination.py` e `apps/core/exceptions.py` e afirmar que são texto em português (não vazio, termina em ponto, sem as palavras `Traceback`, `Exception`, `None`) e que `public_exception_handler` sempre devolve `errors` com o nome do campo quando o erro é de validação e `non_field_errors` quando não há campo
- [X] T026 [P] [US4] Em `README.md`, acrescentar uma seção curta "Acessibilidade" que resume `specs/007-quality-security-accessibility/contracts/accessibility-handoff.md` (o que o backend entrega e o que cabe ao frontend) e um link para esse contrato

**Checkpoint**: todas as histórias independentes.

---

## Phase 7: Polish & Cross-Cutting

- [X] T027 Criar `tests/unit/core/test_no_secret_in_logs.py`: com `caplog` e `monkeypatch` de variáveis de ambiente com valores sentinela (`DJANGO_SECRET_KEY`, `DB_PASSWORD`), disparar o handler com uma exceção cuja mensagem contém o sentinela e afirmar que o corpo da resposta não o contém (o log do servidor pode conter a pilha, mas nunca parâmetros nem cabeçalhos da requisição)
- [X] T028 Rodar `python -m pytest` completo e confirmar: todos os testes passam, cobertura total >= 90% (`--cov-fail-under=90` ativo) e nenhum teste acessa banco
- [X] T029 [P] Rodar `python -m ruff check .` e `python manage.py makemigrations --check --dry-run`; ambos devem passar sem mudanças
- [X] T030 Executar os passos 2 e 3 de `specs/007-quality-security-accessibility/quickstart.md` com `DJANGO_DEBUG=True` e `False` e conferir que nenhuma resposta contém pilha, caminho ou configuração
- [X] T031 Marcar o checklist `specs/007-quality-security-accessibility/checklists/requirements.md` como verificado e registrar na descrição do PR a mudança de contrato da paginação (404 → 400 com `errors.page`)

---

## Dependencies & Execution Order

- Phase 1 → Phase 2 → histórias. T002 bloqueia T014 e T015.
- **US1** é o MVP e não depende das demais. T003 a T008 antes de T009 a T012; T013 fecha a história.
- **US2**, **US3** e **US4** são independentes entre si; começam após a Fase 2. US2 usa a resposta 500 de US1 apenas no T014 (erros do contrato); fazer T014 depois de T013.
- T022 só existe se os testes de T018 a T021 revelarem lacuna.
- Polish depois de todas as histórias desejadas.

### Conflitos de arquivo (sem `[P]` entre si)

- `apps/core/exceptions.py`: T009 apenas.
- `tests/unit/core/test_exceptions.py`: T003 apenas.
- `tests/unit/consultation/test_public_privacy.py`: T014, T015, T016 (mesmo arquivo; T015 e T016 marcadas `[P]` só se escritas em arquivos separados — aqui seguem em sequência após T014).
- `tests/unit/core/test_author_protection.py`: T020 e T021.

## Parallel Examples

```text
US1 (testes):  T004, T005, T006, T007, T008 em paralelo (T003 edita um arquivo existente: antes dos demais não é obrigatório)
US3:           T018, T019, T020 em paralelo
US4:           T024, T025, T026 em paralelo
Histórias:     US2, US3 e US4 em paralelo depois de US1
```

## Implementation Strategy

**MVP (US1)**: T001 → T002 → T003 a T013. Entrega as três correções reais (500 genérico, 404 JSON, página inválida) com regressão das validações. Parar, validar com o quickstart (passo 2) e abrir PR.

**Incremental**: US2 (privacidade) → US3 (auditoria e política) → US4 (acessibilidade e README) → Polish. Cada história fecha com `python -m pytest` verde e cobertura >= 90%.

## Notes

- Mudar um teste da feature 006 só é permitido para o contrato de página inválida (T005, T013).
- Nenhuma tarefa cria migration; se `makemigrations --check` acusar mudança, reverter o que a causou.
- Commits pequenos e descritivos, um por grupo lógico (por exemplo, um por história).
