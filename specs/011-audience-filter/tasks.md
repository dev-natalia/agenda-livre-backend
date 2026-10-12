---

description: "Lista de tarefas de Filtro por Público-alvo"
---

# Tasks: Filtro por Público-alvo

**Input**: Documentos de design em `/specs/011-audience-filter/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Incluídos. A constituição (Princípio III) exige testes unitários com mocks, sem acesso a banco, e
cobertura total mínima de 90%. Em cada história, os testes são escritos antes do código e devem falhar
(red) antes de passar (green). A lógica do filtro é Python puro sobre objetos em memória (`SimpleNamespace`);
consultas ao banco são simuladas com `patch`.

**Organization**: Tarefas agrupadas por história de usuário (US1 a US6 da spec). Há uma migration aditiva
(`audiences/0002`), nenhuma dependência nova e nenhuma tabela nova. A US1 é o MVP; as demais se apoiam nela
ou nela e no campo da fase 2.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência de tarefa incompleta)
- **[Story]**: história de usuário à qual a tarefa pertence (US1 a US6)
- Os caminhos são relativos à raiz do repositório

## Path Conventions

Projeto único com o Django na raiz: `config/`, `apps/` e `tests/unit/<área>/`. Os diretórios de teste **não
têm `__init__.py`**, então o nome de cada arquivo de teste precisa ser único em toda a suíte; os nomes abaixo
já são únicos. Mensagens em português. Linha de código com no máximo 100 caracteres (ruff). Python do projeto:
`.venv/Scripts/python.exe` (`python -m pytest`). Nunca ler nem imprimir o `.env`. Os helpers de teste da consulta
estão em `tests/unit/consultation/consultation_helpers.py` (`activity`, `manager`, `unit`, `category`).

---

## Phase 1: Setup

- [X] T001 Rodar `python -m pytest`, `python -m ruff check .` e `python manage.py makemigrations --check --dry-run` para registrar a linha de base (suíte verde, cobertura >= 90%, "No changes detected") antes de qualquer alteração; conferir com `git branch --show-current` que a branch é `011-audience-filter`

---

## Phase 2: Foundational (bloqueia as histórias)

**Purpose**: o campo `includes_everyone`, usado pelo filtro (US1) e pelo cadastro (US3).

**⚠️ CRITICAL**: nenhuma história pode começar antes de esta fase terminar.

- [X] T002 [P] Em `tests/unit/audiences/test_includes_everyone.py`, escrever testes (red) do modelo `TargetAudience`: `TargetAudience._meta.get_field("includes_everyone")` é `BooleanField`, com `default is False`, rótulo `"Abrange todos os públicos"` e `help_text` que cita "Todas as idades"; uma instância nova (`TargetAudience(name="X")`) tem `includes_everyone is False`; os campos existentes (`id`, `name`, `slug`, `description`, `is_active`) continuam presentes; `clean()` do modelo continua gerando o `slug` a partir do nome sem tocar na marca
- [X] T003 Em `apps/audiences/models.py`, acrescentar a `TargetAudience` o campo `includes_everyone = models.BooleanField("Abrange todos os públicos", default=False, help_text="Marque se esta opção vale para todos os públicos (por exemplo, ‘Todas as idades’). Quem filtra por qualquer outro público também vê as atividades desta opção.")`; fazer os testes de T002 passarem
- [X] T004 Gerar a migration com `python manage.py makemigrations audiences -n targetaudience_includes_everyone` e conferir que `apps/audiences/migrations/0002_targetaudience_includes_everyone.py` só tem um `AddField` (`BooleanField`, `default=False`); `python manage.py makemigrations --check --dry-run` deve dizer "No changes detected" em seguida. **Não rodar `safe_migrate` aqui** (ver T043)

**Checkpoint**: o campo existe, testado, com migration pronta.

---

## Phase 3: User Story 1 - Visitante filtra as atividades por público-alvo (Priority: P1) 🎯 MVP

**Goal**: `GET /api/v1/activities/?audience=<uuid>` com a regra inclusiva de "Todas as idades".

**Independent Test**: com atividades publicadas de públicos diferentes (inclusive "Todas as idades"), o filtro de
cada público devolve as atividades certas, sem duplicatas; identificador malformado dá 400, inexistente ou
inativo dá lista vazia.

### Tests for User Story 1

- [X] T005 [P] [US1] Em `tests/unit/consultation/test_audience_filter.py`, escrever testes (red) da regra, com atividades de `consultation_helpers.activity(...)` cujo `target_audiences=manager([...])` recebe públicos `SimpleNamespace(pk=..., name=..., includes_everyone=...)` e com `find_audience` simulado (`patch.object(services, "find_audience")`): público específico escolhido devolve as atividades dele **e** as de um público com `includes_everyone=True`, e não as de outro público específico; escolher o público marcado devolve só as vinculadas a ele; atividade vinculada ao escolhido e ao marcado aparece **uma única vez**; atividade com vários públicos que inclui o escolhido aparece uma vez; atividade sem nenhum público nunca entra; `find_audience` devolvendo `None` (inexistente ou inativo) dá lista vazia sem examinar as atividades; mais de um público marcado: todos incluídos; público marcado **inativo** vinculado à atividade ainda conta; `Criteria()` sem `audience` não chama `find_audience` e devolve a lista inalterada; `audience` combinado com `q` e `neighborhood` aplica todos pelo critério "E"; a ordem original da lista é mantida
- [X] T006 [P] [US1] Em `tests/unit/consultation/test_audience_query_param.py`, escrever testes (red) de `ConsultationQuerySerializer` e `Criteria`: `audience` com UUID válido preenche `criteria().audience` (como `UUID`); ausente deixa `None`; `abc`, `123` e `0000` falham com `errors == {"audience": ["Informe um identificador válido."]}`, e `""` é tratado como ausente (igual a `unit=`); valor repetido (`QueryDict` com dois `audience`) usa o último; `audience` junto de `unit`, `category`, `q`, `neighborhood`, `date_from`, `date_to` é aceito e todos chegam em `criteria()`; `date` junto de `date_from` continua dando o mesmo erro em `date` (e `audience` válido não o altera); vários erros ao mesmo tempo (`audience=abc&unit=x`) vêm cada um no seu campo
- [X] T007 [P] [US1] Em `tests/unit/consultation/test_audience_filter_view.py`, escrever testes (red) ponta a ponta de `GET /api/v1/activities/?audience=...` com o catálogo simulado (mesmo padrão do fixture `catalog` de `tests/unit/consultation/test_image_field.py`, e `find_audience` simulado): resposta 200 só com as atividades esperadas e `count` batendo com a lista; `audience=abc` responde 400 `{"detail": "Parâmetros inválidos.", "errors": {"audience": ["Informe um identificador válido."]}}`; identificador inexistente responde 200 com `count 0` e `results []`; a view só consulta `published_activities` (nada fora das publicadas); sem `audience`, a resposta é idêntica à de antes (mesmos itens e ordem); `POST` continua dando 405

### Implementation for User Story 1

- [X] T008 [US1] Em `apps/consultation/services.py`: acrescentar `audience: object = None` ao dataclass `Criteria`; criar `find_audience(audience_id)` (`TargetAudience.objects.filter(pk=audience_id, is_active=True).first()`, importando `TargetAudience` de `apps.audiences.models`); criar `matches_audience(activity, audience)` seguindo a tabela de `data-model.md` ("Regra do filtro": se `audience.includes_everyone`, vínculo com ele; senão vínculo com ele **ou** com qualquer público com `includes_everyone`), lendo `activity.target_audiences.all()`; em `apply_criteria`, quando `criteria.audience` não é `None`, chamar `find_audience` uma vez e, se vier `None`, devolver `[]`, senão filtrar com `matches_audience` mantendo a ordem; em `published_activities`, trocar o prefetch por `.prefetch_related("schedules__weekdays", "target_audiences")`; fazer os testes de T005 passarem e manter verdes os de `tests/unit/consultation/test_services.py`
- [X] T009 [US1] Em `apps/consultation/serializers.py`: acrescentar a `ConsultationQuerySerializer` o campo `audience = serializers.UUIDField(required=False, error_messages=ID_ERRORS)` (junto de `unit` e `category`) e `audience=data.get("audience")` em `criteria()`; fazer os testes de T006 e T007 passarem
- [X] T010 [US1] Rodar `python -m pytest tests/unit/consultation` e ajustar apenas o necessário nos testes existentes que montam `Criteria(...)` ou conferem o encadeamento de `prefetch_related` (por exemplo `tests/unit/consultation/test_services.py`), sem enfraquecer nenhuma verificação

**Checkpoint**: o filtro funciona ponta a ponta com a regra inclusiva. MVP: Fase 2 + US1 (com a marca `includes_everyone` ainda editável só pelo banco; a US3 traz o Admin e a carga).

---

## Phase 4: User Story 2 - Frontend obtém a lista de públicos-alvo (Priority: P1)

**Goal**: `GET /api/v1/audiences/`, no padrão de `/units/` e `/categories/`.

**Independent Test**: o recurso lista só os ativos, por nome, com `id`, `name`, `slug` e `description` (ou `null`),
paginado, e recusa escrita.

### Tests for User Story 2

- [X] T011 [P] [US2] Em `tests/unit/consultation/test_audience_resource.py`, escrever testes (red), no mesmo estilo dos testes de `/categories/` em `tests/unit/consultation/test_views.py`: `AudienceItemSerializer` devolve exatamente `id`, `name`, `slug`, `description` (e `description` é `None` quando vazia); a resposta de `GET /api/v1/audiences/` (com `TargetAudience.objects` simulado) usa o envelope `{count, next, previous, results}`; só públicos ativos são pedidos (`filter(is_active=True)`) e ordenados por nome (`order_by("name")`); sem públicos devolve `count 0` e `results []`; paginação com `page_size` e `page` inválida seguem o comportamento de `/categories/`; a resposta não contém `is_active`, `includes_everyone`, `created_at`, `updated_at`; `POST`, `PUT`, `PATCH` e `DELETE` dão 405 `{"detail": "Método não permitido."}`; `GET /api/v1/audiences/<uuid>/` dá 404; credenciais inválidas são ignoradas

### Implementation for User Story 2

- [X] T012 [US2] Em `apps/consultation/serializers.py`, criar `AudienceItemSerializer` (campos `id`, `name`, `slug` e `description` como `SerializerMethodField` que devolve `audience.description or None`, igual a `CategoryItemSerializer`); em `apps/consultation/views.py`, criar `AudienceListView(PublicAPIView)` com `TargetAudience.objects.filter(is_active=True).order_by("name")` em lista e `self.paginate(request, audiences, AudienceItemSerializer)`; em `apps/consultation/urls.py`, acrescentar `path("audiences/", AudienceListView.as_view(), name="audience-list")`; fazer os testes de T011 passarem

**Checkpoint**: o frontend consegue montar o seletor.

---

## Phase 5: User Story 3 - Administrador marca qual público significa "Todas as idades" (Priority: P1)

**Goal**: a marca editável no Django Admin e carregada pela carga inicial.

**Independent Test**: o formulário do Admin tem a caixa; `seed_catalog` marca "Todas as idades" na criação e em
catálogo existente, sem desmarcar nada e sem duplicar.

### Tests for User Story 3

- [X] T013 [P] [US3] Em `tests/unit/audiences/test_target_audience.py`, ajustar `test_admin_configuration` para `list_display == ("name", "slug", "is_active", "includes_everyone")` e `list_filter == ("is_active", "includes_everyone")`, e acrescentar um teste de que o formulário do `ModelAdmin` inclui `includes_everyone` (por exemplo, `"includes_everyone" in audience_admin.get_form(request).base_fields`, com `RequestFactory` e usuário simulado) e de que o campo não está em `readonly_fields`
- [X] T014 [P] [US3] Em `tests/unit/core/test_seed_catalog.py`, acrescentar testes (red): o item `todas-as-idades` de `seed_catalog.TARGET_AUDIENCES` tem `"includes_everyone": True` e os outros quatro não declaram a marca; `get_or_create` do item recebe `defaults` com `includes_everyone=True`; depois de carregar, o comando chama `manager.filter(slug="todas-as-idades").update(includes_everyone=True)` uma vez, **só** para esse item, e nunca chama `update(includes_everyone=False)`; executar duas vezes não cria registros nem muda a saída (`Públicos-alvo: 5 criada(s), 0 já existiam.` e `0 criada(s), 5 já existiam.` continuam iguais); o `update` roda também quando o registro já existia (`get_or_create` devolvendo `created=False`); unidades e categorias não sofrem `update`

### Implementation for User Story 3

- [X] T015 [US3] Em `apps/audiences/admin.py`, ajustar `TargetAudienceAdmin` para `list_display = ("name", "slug", "is_active", "includes_everyone")` e `list_filter = ("is_active", "includes_everyone")`, sem tocar em `readonly_fields`, `prepopulated_fields` nem nas ações; fazer os testes de T013 passarem
- [X] T016 [US3] Em `apps/core/management/commands/seed_catalog.py`, acrescentar `"includes_everyone": True` ao item `{"slug": "todas-as-idades", ...}` de `TARGET_AUDIENCES`; criar `_mark_everyone(manager, items)`, que para cada item com `includes_everyone` verdadeiro faz `manager.filter(slug=item["slug"]).update(includes_everyone=True)` e nunca desmarca; chamá-la em `handle` somente para o catálogo de públicos-alvo, depois de `_load`, **sem alterar as linhas de saída existentes** (o retorno de `update` é ignorado); fazer os testes de T014 passarem e manter verdes os de `tests/unit/core/test_seed_catalog.py`

**Checkpoint**: o administrador marca "abrange todos" e a carga inicial a aplica.

---

## Phase 6: User Story 4 - Combinar o público-alvo com os outros filtros (Priority: P2)

**Goal**: garantir, por testes, a combinação com `q`, `unit`, `category`, `neighborhood` e datas.

**Independent Test**: cada combinação devolve só atividades que atendem a todos os filtros, e as combinações
inválidas existentes continuam recusadas como antes.

- [X] T017 [P] [US4] Em `tests/unit/consultation/test_audience_combinations.py`, escrever testes: `audience` + `unit` e `audience` + `category` chegam a `published_activities` como `unit_id`/`category_id` (verificar o encadeamento de `filter` com `Activity` simulada, no estilo de `tests/unit/consultation/test_services.py`) e o filtro de público ainda é aplicado ao resultado; `audience` + `q` e `audience` + `neighborhood` aplicados juntos em `apply_criteria` devolvem a interseção; `audience` + `date_from`/`date_to`/`date` mantêm a ordenação por próxima ocorrência (via `build_listing` com o relógio simulado); o endpoint `GET /api/v1/activities/?audience=<id>&date=2026-11-01&date_from=2026-11-01` continua dando o mesmo 400 de antes (erro em `date`); `?audience=abc&date_from=2026-13-40` reporta os dois erros, cada um no seu campo. Se algum teste falhar por defeito do código da US1, corrigir `apps/consultation/services.py` ou `apps/consultation/serializers.py` e registrar a correção na descrição do commit

**Checkpoint**: a combinação está coberta e fechada.

---

## Phase 7: User Story 5 - Visitante vê o público-alvo em cada resultado (Priority: P2)

**Goal**: `target_audiences` (`id` e `name`, por nome) em cada item da listagem, sem consulta extra por atividade.

**Independent Test**: cada item traz seus públicos em ordem, `[]` sem públicos, e o prefetch evita consultas por item.

### Tests for User Story 5

- [X] T018 [P] [US5] Em `tests/unit/consultation/test_audience_listing.py`, escrever testes (red): cada item de `ActivityListItemSerializer` tem a chave `target_audiences` com `[{"id": ..., "name": ...}]` **ordenada por nome** (sem acento ignorado: usar `sorted(..., key=name)` simples) e sem nenhuma outra chave; atividade sem públicos devolve `[]` (nunca `None`, nunca ausente); o detalhe (`ActivityDetailSerializer`) usa a mesma ordenação por nome; `target_audience_notes` continua só no detalhe e não aparece na listagem; `published_activities` chama `prefetch_related("schedules__weekdays", "target_audiences")` (verificar os argumentos da chamada com `Activity` simulada), o que mantém o número de consultas constante; os campos já existentes (`id`, `title`, `slug`, `summary`, `unit`, `category`, `next_occurrence`, `image`) continuam idênticos
- [X] T019 [US5] Ajustar os testes existentes que conferem a lista exata de chaves: em `tests/unit/consultation/test_serializers.py` (`test_list_item_keys_and_formats`) e em `tests/unit/consultation/test_image_field.py` (`test_existing_list_fields_are_unchanged`), incluir `"target_audiences"` na posição em que a chave sai (depois de `category`, antes de `next_occurrence`; manter a ordem que o serializer produzir)

### Implementation for User Story 5

- [X] T020 [US5] Em `apps/consultation/serializers.py`, criar `audiences_payload(activity)` que devolve `[{"id": a.id, "name": a.name} for a in sorted(activity.target_audiences.all(), key=lambda a: a.name)]`; usá-la no dicionário de `ActivityListItemSerializer.to_representation` (chave `"target_audiences"`, entre `"category"` e `"next_occurrence"`) e no detalhe (substituindo a serialização de `target_audiences` atual por `audiences_payload`, mantendo `id` e `name`); fazer os testes de T018 e T019 passarem

**Checkpoint**: o card pode mostrar o público; o detalhe fica coerente com a listagem.

---

## Phase 8: User Story 6 - Administrador filtra a lista de atividades por público-alvo (Priority: P3)

**Goal**: filtro "Público-alvo" na lista de atividades do Django Admin.

**Independent Test**: as opções são os públicos ativos mais os inativos com vínculo, e escolher uma mostra as
atividades dela uma vez cada.

### Tests for User Story 6

- [X] T021 [P] [US6] Em `tests/unit/activities/test_audience_list_filter.py`, escrever testes (red) de `AudienceListFilter` (`apps.activities.admin`) com `TargetAudience.objects` simulado e `RequestFactory`: `title == "Público-alvo"` e `parameter_name == "audience"`; `lookups` devolve pares `(str(id), name)` de `TargetAudience.objects.filter(Q(is_active=True) | Q(activity_links__isnull=False)).distinct().order_by("name")` (verificar a expressão `Q` passada a `filter`, a chamada de `distinct()` e a ordenação por nome); `queryset` sem valor devolve o queryset recebido sem filtrar; com valor chama `queryset.filter(audience_links__target_audience_id=<valor>)`; `ActivityAdmin.list_filter == ("status", "unit", "category", AudienceListFilter)` (ajustar `test_list_configuration` em `tests/unit/activities/test_activity_admin.py`); `search_fields`, `actions` e `has_delete_permission` não mudam

### Implementation for User Story 6

- [X] T022 [US6] Em `apps/activities/admin.py`, criar `AudienceListFilter(admin.SimpleListFilter)` com `title = "Público-alvo"`, `parameter_name = "audience"`, `lookups` e `queryset` conforme `research.md` seção 9 (importar `TargetAudience` de `apps.audiences.models`); acrescentá-lo ao final de `ActivityAdmin.list_filter`; fazer os testes de T021 e o `test_list_configuration` atualizado passarem

**Checkpoint**: o Admin filtra atividades por público.

---

## Phase 9: Polish & Cross-Cutting Concerns

- [X] T023 [P] Atualizar `docs/03-modelo-de-dados.md`: campo `includes_everyone` na entidade `TargetAudience` (tipo, padrão, regra da marca), seção "Público-alvo padronizado" explicando a regra inclusiva de "Todas as idades", pendência 3 marcada como resolvida para o filtro, versão e histórico
- [X] T024 [P] Atualizar `docs/05-especificacao-api-rest.md`: parâmetro `audience` e a regra inclusiva na listagem (seção 4), campo `target_audiences` nos itens, o novo recurso `GET /api/v1/audiences/` (nova seção, antes ou depois de categorias) e a linha de histórico; copiar do `contracts/public-api-audience.md`
- [X] T025 [P] Atualizar `specs/006-public-consultation/contracts/public-api.md`: parâmetro `audience` na tabela de filtros de `GET /api/v1/activities/`, `target_audiences` no exemplo do item da listagem, a nova seção `GET /api/v1/audiences/` e referência a `specs/011-audience-filter/contracts/public-api-audience.md`
- [X] T026 [P] Atualizar `README.md`: na seção "API pública de consulta", o parâmetro `audience` (com a regra de "Todas as idades"), o recurso `/api/v1/audiences/` e o campo `target_audiences`; na seção do Admin ou do catálogo, a caixa "Abrange todos os públicos" e o passo de rodar `python manage.py seed_catalog` depois de `safe_migrate`
- [X] T027 [P] Atualizar `docs/10-filtro-por-publico-alvo.md`: status "Implementado no backend (feature 011); falta a verificação no ambiente real", pendência 1 e 8 já resolvidas (conferir) e nova linha no histórico; em `docs/04-backlog-do-produto.md`, conferir que EP-11 e a US-025 já estão corretos
- [X] T028 Em `specs/011-audience-filter/research.md`, seção 8, corrigir a frase "A saída ganha uma linha só quando algum registro mudou" para "A saída não muda (o resultado do `update` é ignorado)", para refletir a decisão de T016
- [X] T029 Rodar `python -m ruff check .` e corrigir qualquer apontamento nos arquivos novos e alterados (linhas de até 100 caracteres, imports ordenados)
- [X] T030 Rodar `python -m pytest` e confirmar que a suíte inteira passa com cobertura total >= 90%, sem acesso a banco; conferir que nenhum teste novo depende de arquivos binários nem de rede
- [X] T031 Rodar `python manage.py makemigrations --check --dry-run` e confirmar "No changes detected" (a migration `0002` de `audiences` já existe); revisar `git status` para garantir que `.env` e `logs/` não aparecem
- [X] T032 Aplicar a migration e a carga com `python manage.py safe_migrate` e depois `python manage.py seed_catalog` (duas vezes, para provar a repetição), **somente depois de a pessoa responsável autorizar**, pois o RDS é compartilhado; confirmar `audiences.0002_targetaudience_includes_everyone` aplicada e "Todas as idades" marcada
- [X] T033 Verificar os cenários 1 a 16 de `quickstart.md` contra o RDS real, por script com o cliente de teste do Django (API e formulário do Admin), usando atividades e públicos de teste que o próprio script cria e apaga, e registrar o resultado no fim de `specs/011-audience-filter/quickstart.md`. Exige a autorização de T032

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sem dependências.
- **Foundational (Phase 2)**: depende do Setup. T003 depende de T002; T004 de T003. Bloqueia as histórias.
- **US1 (Phase 3)**: depende da Foundational. T008 depende de T005; T009 de T006 e T007 (e de T008, pois `criteria()` usa o campo de `Criteria`); T010 por último.
- **US2 (Phase 4)**: depende só da Foundational (o recurso não usa a marca); independente de US1.
- **US3 (Phase 5)**: depende da Foundational; independente de US1 e US2. T015 depende de T013; T016 de T014.
- **US4 (Phase 6)**: depende de US1.
- **US5 (Phase 7)**: depende de US1 (o prefetch de `target_audiences` entra em T008). T020 depende de T018 e T019.
- **US6 (Phase 8)**: depende da Foundational; independente das demais.
- **Polish (Phase 9)**: depende das histórias desejadas. T032 (migration e carga no RDS, com autorização) vem antes de qualquer verificação manual contra o ambiente real (T033), que é a última.

### User Story Dependencies

```text
Foundational ─┬─▶ US1 ─┬─▶ US4
              │        └─▶ US5
              ├─▶ US2
              ├─▶ US3
              └─▶ US6
```

### Within Each User Story

- Testes primeiro (red), depois a implementação (green).
- Dois testes na mesma história que mexem no mesmo arquivo não são paralelos entre si.

### Parallel Opportunities

- Fase 2: T002 sozinho antes de T003; nada mais é paralelo.
- Depois da Foundational: US1, US2, US3 e US6 podem andar em paralelo (arquivos diferentes, exceto `serializers.py` e `views.py`, tocados por US1 e US2: fazer T009 antes de T012 ou coordenar).
- Testes [P] de uma mesma história: T005, T006 e T007; T013 e T014.
- Fase 9: T023 a T027 em paralelo (documentos diferentes).

---

## Parallel Example: US1

```text
Task: "T005 [P] [US1] testes da regra em tests/unit/consultation/test_audience_filter.py"
Task: "T006 [P] [US1] testes do parâmetro em tests/unit/consultation/test_audience_query_param.py"
Task: "T007 [P] [US1] testes ponta a ponta em tests/unit/consultation/test_audience_filter_view.py"
```

## Parallel Example: depois da US1

```text
Task: "T011 [P] [US2] testes do recurso em tests/unit/consultation/test_audience_resource.py"
Task: "T013 [P] [US3] testes do Admin em tests/unit/audiences/test_target_audience.py"
Task: "T021 [P] [US6] testes do filtro em tests/unit/activities/test_audience_list_filter.py"
```

---

## Implementation Strategy

### MVP First (US1)

1. Setup e Foundational (T001 a T004).
2. US1: o filtro com a regra inclusiva (T005 a T010).
3. **PARAR e VALIDAR**: testes verdes e, com a autorização de T032, os cenários 4 a 9 do `quickstart.md`.

### Incremental Delivery

1. MVP acima: já dá para filtrar por `?audience=<id>`.
2. US2: o frontend ganha o seletor (`/audiences/`).
3. US3: o administrador edita a marca e a carga a aplica (necessário para a regra inclusiva funcionar em dados reais).
4. US5: o card mostra o público.
5. US4: combinações cobertas por testes.
6. US6: filtro no Admin.
7. Polish: documentos, lint, cobertura, migration no RDS e verificação final.

---

## Notes

- A US-050 (frontend) fica fora deste repositório; o contrato dela é `contracts/public-api-audience.md`.
- Nenhuma tarefa lê, imprime ou versiona o `.env` ou chaves de acesso.
- T032 e T033 tocam o RDS real e dependem de autorização da pessoa responsável.
- Sem o `seed_catalog` (T032), o filtro funciona como filtro exato: "Todas as idades" só é incluída depois de marcada.
- Commits pequenos e descritivos, um por tarefa ou por grupo coeso, na branch `011-audience-filter`.
