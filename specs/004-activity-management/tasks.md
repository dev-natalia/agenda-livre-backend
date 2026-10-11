---

description: "Lista de tarefas de Gestão de Atividades"
---

# Tasks: Gestão de Atividades

**Input**: Documentos de design em `/specs/004-activity-management/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Incluídos. A constituição (Princípio III) exige testes unitários com mocks, sem acesso a banco, e
cobertura total mínima de 90%. Nenhum teste pode abrir conexão com banco de dados: use instâncias de modelo
não salvas, `RequestFactory`, `SimpleNamespace` e `unittest.mock`. Chamar `clean()` é permitido; chamar
`full_clean()`, `validate_unique()` ou `validate_constraints()` em modelo real consulta o banco e NÃO é.

**Organization**: Tarefas agrupadas por história de usuário (US1 a US6 da spec), para permitir
implementação e validação independentes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência de tarefa incompleta)
- **[Story]**: história de usuário à qual a tarefa pertence (US1 a US6)
- Os caminhos são relativos à raiz do repositório

## Path Conventions

Projeto único com o Django na raiz: `config/`, `apps/` (módulos por domínio) e `tests/unit/`. Os apps
`apps/activities` e `apps/audiences` já existem (feature 001) com `models.py` vazio. `CatalogModel`,
`ActiveToggleActionsMixin` e `ActiveOnlyForeignKeyMixin` ficam em `apps/core` (feature 003). Não há
dependências novas. Textos de interface em português.

---

## Phase 1: Setup

**Purpose**: confirmar o ponto de partida

- [X] T001 Rodar `pytest` e `ruff check .` na raiz e confirmar que a suíte das features 001 a 003 passa com cobertura >= 90%, registrando o resultado como linha de base

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: modelos, migrations e ajuste do mixin, usados por todas as histórias. Bloqueia todas elas.

**⚠️ CRITICAL**: nenhuma história começa antes desta fase.

- [X] T002 Em `apps/audiences/models.py`, criar `TargetAudience(CatalogModel)` com `Meta(CatalogModel.Meta)`, `verbose_name = "Público-alvo"` e `verbose_name_plural = "Públicos-alvo"`. Herda `name` (150, obrigatório, sem espaços nas pontas), `slug` (único, gerado do nome), `description` (opcional), `is_active` (padrão verdadeiro) e as datas
- [X] T003 Em `apps/activities/models.py`, criar a classe `Activity(models.Model)` com `verbose_name = "Atividade"` / `"Atividades"`, `ordering = ["-updated_at"]` e `__str__` devolvendo `title`. Campos: `id` = `UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`; `unit` = `ForeignKey("units.Unit", on_delete=PROTECT, related_name="activities")` (Obrigatório); `category` = `ForeignKey("categories.Category", on_delete=PROTECT, related_name="activities")` (Obrigatório); `title` = `CharField(max_length=200)` ("Obrigatório, sem espaços nas pontas, não vazio"); `slug` = `SlugField(max_length=220, unique=True, blank=True, editable=False)`; `summary` = `CharField(max_length=300, blank=True)`; `description` = `TextField()` ("Obrigatório, não vazio"); `target_audience_notes` = `TextField(blank=True)`; `external_registration_url` = `URLField(blank=True)`; `status` = `CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, editable=False)`; `target_audiences` = `ManyToManyField("audiences.TargetAudience", through="ActivityTargetAudience", related_name="activities", blank=True)`; `created_by` e `updated_by` = `ForeignKey(settings.AUTH_USER_MODEL, on_delete=PROTECT, related_name="+", editable=False)`; `created_at` = `DateTimeField(auto_now_add=True)`; `updated_at` = `DateTimeField(auto_now=True)`. Usar `verbose_name` em português (Título, Resumo, Descrição, Observações sobre o público, Link externo, Situação, Públicos-alvo, Criada por, Atualizada por, Criada em, Atualizada em, Unidade, Categoria). Declarar `class Status(models.TextChoices)` com `DRAFT = "DRAFT", "Rascunho"`, `PUBLISHED = "PUBLISHED", "Publicada"`, `FINISHED = "FINISHED", "Encerrada"`, `CANCELLED = "CANCELLED", "Cancelada"`, e a constante de módulo `PUBLIC_STATUSES = {Status.PUBLISHED}`. Em `Meta.indexes`, criar índices em `status`, (`unit`, `status`) e (`category`, `status`)
- [X] T004 Em `apps/activities/models.py`, criar `ActivityTargetAudience(models.Model)` com `id` UUID (PK), `activity` = `ForeignKey(Activity, on_delete=CASCADE, related_name="audience_links")`, `target_audience` = `ForeignKey("audiences.TargetAudience", on_delete=PROTECT, related_name="activity_links")`, `verbose_name = "Público-alvo da atividade"` e `UniqueConstraint(fields=["activity", "target_audience"], name="unique_activity_target_audience")`
- [X] T005 Em `apps/activities/models.py`, implementar `Activity.clean()`: aplicar `strip()` em `title`, `description`, `summary` e `external_registration_url`; levantar `ValidationError({"title": ...})` e `ValidationError({"description": ...})` quando ficarem vazios; levantar `ValidationError({"external_registration_url": "Informe um endereço que comece com http:// ou https://."})` quando o link informado não tiver esquema `http`/`https`; quando `slug` estiver vazio, atribuir o resultado do novo método `_build_slug()`. Implementar `_build_slug()` com `slugify(self.title)` (se vazio, `"atividade"`) e, em colisão, sufixos `-2`, `-3`..., consultando a existência por um método separado `_slug_taken(slug)` (que usa `Activity.objects.filter(slug=slug).exclude(pk=self.pk).exists()`) para poder ser mockado
- [X] T006 Gerar as migrations com `python manage.py makemigrations audiences activities` (nomes `0001_initial`), conferir que a de `activities` depende de `units`, `categories`, `audiences` e `AUTH_USER_MODEL`, e que `python manage.py makemigrations --check --dry-run` não acusa pendências. Não aplicar no banco aqui
- [X] T007 [P] Criar `tests/unit/audiences/test_target_audience_model.py` (criar `tests/unit/audiences/__init__.py` se o padrão do repositório exigir) testando: `str()` devolve o nome; `Meta.ordering == ["name"]`; `verbose_name`/`verbose_name_plural` em português; `clean()` gera o slug de "Pessoas idosas" (`pessoas-idosas`)
- [X] T008 [P] Criar `tests/unit/activities/test_activity_model.py` (criar `tests/unit/activities/__init__.py` se necessário) testando com instâncias não salvas: situação padrão `DRAFT`; `Status` tem os quatro valores e rótulos em português; `PUBLIC_STATUSES == {Status.PUBLISHED}`; `clean()` remove espaços de título e descrição, recusa título e descrição vazios ou só com espaços, recusa link `ftp://x` e aceita `https://exemplo.org`, gera o slug do título; com `_slug_taken` mockado, devolve `titulo-2` e `titulo-3` em colisões sucessivas; título só com símbolos gera `atividade`; `Meta.indexes` contém os três índices; `ActivityTargetAudience` tem a `UniqueConstraint` de nome `unique_activity_target_audience`; as FKs `unit` e `category` usam `on_delete=PROTECT`
- [X] T009 Em `apps/core/admin.py`, alterar `ActiveOnlyForeignKeyMixin.formfield_for_foreignkey` para, além de `is_active=True`, incluir o valor já gravado na instância em edição: ler o objeto de `getattr(request, "_editing_obj", None)`, obter o id atual com `getattr(obj, f"{db_field.name}_id", None)` e filtrar com `Q(is_active=True) | Q(pk=current_id)` quando houver id atual. Atualizar a docstring explicando que `ModelAdmin` e inlines definem `request._editing_obj` em `get_form`/`get_formset`
- [X] T010 Ampliar `tests/unit/core/test_admin_mixin.py` com casos: sem `_editing_obj`, o queryset filtra só ativos; com objeto em edição cujo `unit_id` está definido, o filtro inclui esse id (conferir os argumentos de `queryset.filter` com mock); com objeto em edição sem valor atual (id `None`), filtra só ativos; modelos relacionados sem `is_active` não são filtrados

**Checkpoint**: modelos e migrations prontos; `pytest tests/unit/audiences tests/unit/activities tests/unit/core/test_admin_mixin.py` verde.

---

## Phase 3: User Story 1 - Cadastrar uma atividade como rascunho (Priority: P1) 🎯 MVP

**Goal**: administradores cadastram atividades pelo Admin, que nascem como rascunho, com autoria registrada e unidade e categoria ativas.

**Independent Test**: instanciar `ActivityAdmin` e conferir lista, filtros, busca, campos somente leitura, `save_model` preenchendo autoria e a permissão de exclusão.

- [X] T011 [US1] Em `apps/activities/admin.py`, criar `ActivityAdmin(ActiveOnlyForeignKeyMixin, admin.ModelAdmin)` registrado para `Activity`, com: `list_display = ("title", "unit", "category", "status", "updated_at")`; `list_filter = ("status", "unit", "category")`; `search_fields = ("title", "summary")`; `list_select_related = ("unit", "category")`; `readonly_fields = ("status", "slug", "created_by", "updated_by", "created_at", "updated_at")`; `fields` na ordem: `title`, `summary`, `description`, `unit`, `category`, `target_audience_notes`, `external_registration_url`, `status`, `slug`, `created_by`, `updated_by`, `created_at`, `updated_at`
- [X] T012 [US1] Em `ActivityAdmin.save_model(request, obj, form, change)`, definir `obj.created_by = request.user` quando `not change`, `obj.updated_by = request.user` sempre, e então `super().save_model(...)`
- [X] T013 [US1] Em `ActivityAdmin`, implementar `has_delete_permission(request, obj=None)`: com `obj` definido, devolver `super().has_delete_permission(...)` e `obj.status == Activity.Status.DRAFT`; sem `obj` (lista), devolver o valor do `super()`. Sobrescrever `get_actions` removendo `delete_selected` da lista (a exclusão em lote não respeita a regra por objeto)
- [X] T014 [P] [US1] Criar `tests/unit/activities/test_activity_admin.py` testando: `Activity` registrada com `ActivityAdmin`; `list_display`, `list_filter`, `search_fields`, `list_select_related` e `readonly_fields` conforme T011; herda `ActiveOnlyForeignKeyMixin`; `save_model` em criação define `created_by` e `updated_by` com o usuário (com `super().save_model` mockado); em edição só `updated_by` muda e `created_by` permanece; `has_delete_permission` devolve verdadeiro para `DRAFT` e falso para `PUBLISHED`, `FINISHED` e `CANCELLED` (com o `super()` mockado devolvendo `True`); `get_actions` não contém `delete_selected`

**Checkpoint**: cadastro como rascunho funcional pelo Admin; `pytest tests/unit/activities` verde.

---

## Phase 4: User Story 2 - Selecionar públicos-alvo (Priority: P1)

**Goal**: administradores cadastram opções de público e as vinculam às atividades por um inline, sem duplicidade e sem oferecer inativas.

**Independent Test**: conferir `TargetAudienceAdmin`, o inline e o formset (duplicidade) com mocks, e o comando de carga com `get_or_create` mockado.

- [X] T015 [US2] Em `apps/audiences/admin.py`, criar `TargetAudienceAdmin(ActiveToggleActionsMixin, admin.ModelAdmin)` registrado para `TargetAudience`, com `list_display = ("name", "slug", "is_active")`, `list_filter = ("is_active",)`, `search_fields = ("name",)`, `readonly_fields = ("created_at", "updated_at")` e `prepopulated_fields = {"slug": ("name",)}`
- [X] T016 [US2] Em `apps/activities/admin.py`, criar `ActivityTargetAudienceFormSet(BaseInlineFormSet)` cujo `clean()` (a) levanta `ValidationError("A mesma opção de público-alvo não pode ser escolhida duas vezes.")` quando duas formas não removidas apontam para o mesmo `target_audience`; (b) quando `self.instance.status == Activity.Status.PUBLISHED` e não restar nenhuma forma não removida com `target_audience`, levanta `ValidationError("Uma atividade publicada precisa de ao menos um público-alvo.")`. Ignorar formas com erros de campo (`form.errors`) no passo (a)
- [X] T017 [US2] Em `apps/activities/admin.py`, criar `ActivityTargetAudienceInline(admin.TabularInline)` com `model = ActivityTargetAudience`, `formset = ActivityTargetAudienceFormSet`, `extra = 1` e `verbose_name`/`verbose_name_plural` "Público-alvo"/"Públicos-alvo". Sobrescrever `formfield_for_foreignkey` para o campo `target_audience`, filtrando `Q(is_active=True) | Q(pk__in=<ids já vinculados>)`, onde os ids vêm de `self._linked_ids` (definido em `get_formset(request, obj=None, **kwargs)` como `obj.audience_links.values_list("target_audience_id", flat=True)` quando `obj` existe, ou lista vazia). Adicionar `inlines = [ActivityTargetAudienceInline]` ao `ActivityAdmin`
- [X] T018 [US2] Em `apps/core/management/commands/seed_catalog.py`, adicionar a lista `TARGET_AUDIENCES` com os slugs e nomes: `criancas` / "Crianças", `adolescentes` / "Adolescentes", `adultos` / "Adultos", `pessoas-idosas` / "Pessoas idosas", `todas-as-idades` / "Todas as idades"; incluir `("Públicos-alvo", TargetAudience.objects, TARGET_AUDIENCES)` no laço de `handle`, mantendo a saída `Públicos-alvo: N criada(s), M já existiam.` e a idempotência por `slug`
- [X] T019 [P] [US2] Criar `tests/unit/audiences/test_target_audience_admin.py` testando: registro com `TargetAudienceAdmin`; `list_display`, `list_filter`, `search_fields`, `readonly_fields`, `prepopulated_fields`; herda `ActiveToggleActionsMixin`
- [X] T020 [P] [US2] Ampliar `tests/unit/activities/test_activity_admin.py` com o formset e o inline: duas formas com a mesma opção levantam `ValidationError`; formas marcadas para remoção são ignoradas; atividade `PUBLISHED` sem nenhuma forma com público levanta `ValidationError`; atividade `DRAFT` sem público é aceita; o inline filtra públicos por `Q(is_active=True) | Q(pk__in=...)` (conferir com mocks do queryset e de `obj.audience_links`); `ActivityAdmin.inlines` contém o inline
- [X] T021 [P] [US2] Ampliar `tests/unit/core/test_seed_catalog.py` testando que o comando consulta `TargetAudience.objects` com os cinco slugs, que opções já existentes não são recriadas (mock de `get_or_create` devolvendo `(obj, False)`) e que a saída traz a linha `Públicos-alvo:`

**Checkpoint**: públicos-alvo vinculáveis sem duplicidade; `pytest` verde.

---

## Phase 5: User Story 3 - Editar uma atividade (Priority: P1)

**Goal**: administradores editam atividades mantendo identificador, autoria correta e vínculos já existentes com registros desativados.

**Independent Test**: com mocks, conferir que `get_form` registra o objeto em edição, que `save_model` em edição preserva `created_by` e que o mixin mantém unidade e categoria atuais.

- [X] T022 [US3] Em `ActivityAdmin` (`apps/activities/admin.py`), sobrescrever `get_form(request, obj=None, **kwargs)` para definir `request._editing_obj = obj` antes de chamar `super().get_form(...)`, de modo que o mixin (T009) mantenha unidade e categoria já gravadas ao editar uma atividade cujo vínculo foi desativado
- [X] T023 [US3] Em `ActivityAdmin.save_model` e `Activity.clean`, garantir que editar o título não altera o `slug` já gravado (o `clean()` só gera o slug quando vazio) e que o `id` é mantido; nenhuma mudança de código esperada além de conferir pelos testes de T024
- [X] T024 [P] [US3] Ampliar `tests/unit/activities/test_activity_admin.py` testando: `get_form` define `request._editing_obj` com o objeto recebido (mock de `super().get_form`); `get_form` sem objeto define `None`; `save_model` em edição não toca `created_by` nem o `id`; com `clean()` chamado duas vezes, o slug já preenchido não é regerado (cenário de edição do título)
- [X] T025 [P] [US3] Ampliar `tests/unit/core/test_admin_mixin.py` com o cenário de edição: `request._editing_obj` com `unit_id`/`category_id` definidos faz o filtro de `unit` e `category` incluir o id atual, mesmo que a unidade esteja inativa (valida a User Story 3, cenário 5)

**Checkpoint**: edição preserva identidade, autoria e vínculos; `pytest` verde.

---

## Phase 6: User Story 4 - Publicar uma atividade (Priority: P1)

**Goal**: administradores publicam atividades completas, e a publicação de atividades incompletas é recusada com o motivo.

**Independent Test**: testar `change_status` com atividade e usuário simulados (mocks de `save` e da contagem de públicos) e a ação `Publicar` com `RequestFactory`.

- [X] T026 [US4] Criar `apps/activities/services.py` com `class StatusChangeError(Exception)` e a função `change_status(activity, new_status, user)`. Regras: se `activity.status == new_status`, devolver `False` sem alterar nada; consultar o mapa `ALLOWED_TRANSITIONS` (`DRAFT→{PUBLISHED}`, `PUBLISHED→{CANCELLED, FINISHED}`, `CANCELLED→{PUBLISHED}`, `FINISHED→{PUBLISHED}`) e levantar `StatusChangeError` com mensagem em português ("Não é possível passar de {situação atual} para {nova situação}.") se a transição não estiver permitida; ao publicar, chamar `validate_publication(activity)`, que levanta `StatusChangeError` quando: título ou descrição vazios; `activity.unit.is_active` falso ("A unidade está inativa."); `activity.category.is_active` falso ("A categoria está inativa."); `activity.audience_links.exists()` falso ("Falta ao menos um público-alvo."). Em caso de sucesso, definir `status`, `updated_by = user` e chamar `activity.save(update_fields=["status", "updated_by", "updated_at"])`, devolvendo `True`
- [X] T027 [US4] Em `ActivityAdmin`, criar a ação `publish_selected` (`@admin.action(description="Publicar selecionadas", permissions=["change"])`) que percorre o queryset chamando `change_status(activity, Activity.Status.PUBLISHED, request.user)` para cada atividade; conta as alteradas, ignora as já publicadas, captura `StatusChangeError` por atividade e, ao final, usa `self.message_user` com o total publicado (`messages.SUCCESS`) e, separadamente, uma mensagem de erro por atividade recusada com `"{título}: {motivo}"` (`messages.ERROR`). Registrar a ação em `actions`
- [X] T028 [P] [US4] Criar `tests/unit/activities/test_status_service.py` testando `change_status` com atividade simulada (`SimpleNamespace` ou instância não salva com `save` mockado): publicar rascunho completo devolve `True`, define `status`, `updated_by` e salva com `update_fields=["status", "updated_by", "updated_at"]`; publicar com título vazio, unidade inativa, categoria inativa ou sem público levanta `StatusChangeError` com a mensagem esperada e não chama `save`; publicar atividade já publicada devolve `False` sem salvar; republicar `CANCELLED` e `FINISHED` com dados válidos funciona; `DRAFT→CANCELLED` e `DRAFT→FINISHED` levantam `StatusChangeError`
- [X] T029 [P] [US4] Ampliar `tests/unit/activities/test_activity_admin.py` testando `publish_selected` com `RequestFactory`, `message_user` mockado e `change_status` mockado: contagem de publicadas na mensagem de sucesso, uma mensagem de erro por atividade recusada com o motivo, atividades já publicadas ignoradas; a ação exige a permissão `change` (`permissions=["change"]` / `allowed_permissions`)

**Checkpoint**: publicação com validação e auditoria; `pytest` verde.

---

## Phase 7: User Story 5 - Cancelar uma atividade (Priority: P1)

**Goal**: administradores cancelam atividades publicadas, preservando todos os dados.

**Independent Test**: testar a ação `Cancelar` com `RequestFactory` e `change_status` mockado, e o caminho `PUBLISHED→CANCELLED` do serviço.

- [X] T030 [US5] Em `ActivityAdmin`, criar a ação `cancel_selected` (`description="Cancelar selecionadas"`, `permissions=["change"]`) que usa a mesma lógica de resumo da `publish_selected`, chamando `change_status(..., Activity.Status.CANCELLED, request.user)`. Extrair a lógica comum para um método privado `_apply_status(request, queryset, new_status, success_label)` usado pelas ações de publicar, cancelar e encerrar, e refatorar `publish_selected` (T027) para usá-lo. Registrar a ação em `actions`
- [X] T031 [P] [US5] Ampliar `tests/unit/activities/test_status_service.py` com `PUBLISHED→CANCELLED` (devolve `True`, salva com `update_fields`, não exige validação de publicação), `CANCELLED→CANCELLED` (`False`) e `DRAFT→CANCELLED` (recusada, já coberta em T028, só conferir que continua passando)
- [X] T032 [P] [US5] Ampliar `tests/unit/activities/test_activity_admin.py` testando `cancel_selected`: chama `change_status` com `CANCELLED` e o usuário da requisição, mensagem de sucesso com a contagem, erros por atividade recusada; e que `publish_selected` continua funcionando após a refatoração para `_apply_status`

**Checkpoint**: cancelamento funcional; `pytest` verde.

---

## Phase 8: User Story 6 - Marcar uma atividade como encerrada (Priority: P2)

**Goal**: administradores marcam atividades publicadas como encerradas, preservando todos os dados.

**Independent Test**: testar a ação `Encerrar` com `RequestFactory` e o caminho `PUBLISHED→FINISHED` do serviço.

- [X] T033 [US6] Em `ActivityAdmin`, criar a ação `finish_selected` (`description="Encerrar selecionadas"`, `permissions=["change"]`) que usa `_apply_status(..., Activity.Status.FINISHED, ...)`. Registrar a ação em `actions`, na ordem: publicar, cancelar, encerrar
- [X] T034 [P] [US6] Ampliar `tests/unit/activities/test_status_service.py` com `PUBLISHED→FINISHED` (devolve `True`, salva com `update_fields`), `FINISHED→FINISHED` (`False`) e `FINISHED→CANCELLED` (`StatusChangeError`)
- [X] T035 [P] [US6] Ampliar `tests/unit/activities/test_activity_admin.py` testando `finish_selected` e a ordem e os rótulos das três ações em `ActivityAdmin.actions` ("Publicar selecionadas", "Cancelar selecionadas", "Encerrar selecionadas")

**Checkpoint**: ciclo de vida completo; `pytest` verde.

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: documentação, verificação final e validação real contra o banco.

- [X] T036 [P] Atualizar `README.md` com a seção "Carga inicial de públicos-alvo" (comando `python manage.py seed_catalog`, as cinco opções e a nota de que a lista é provisória e editável pelo Admin) e uma nota curta sobre o ciclo de vida das atividades (situações e ações do Admin)
- [X] T037 Rodar `pytest` (cobertura total >= 90%) e `ruff check .`; corrigir qualquer falha ou aviso. Rodar `python manage.py makemigrations --check --dry-run` e confirmar que não há migrations pendentes
- [X] T038 Aplicar as migrations no RDS com `python manage.py safe_migrate`, rodar `python manage.py seed_catalog` duas vezes (a segunda não cria nada) e executar o roteiro manual de `specs/004-activity-management/quickstart.md` (seção 4, passos 1 a 10) com uma conta do grupo "Administrador" e uma conta sem o grupo. Esta tarefa precisa do `.env` real e das credenciais do banco, e é executada pela pessoa responsável
- [X] T039 Marcar as tarefas concluídas neste arquivo e registrar no fim do `quickstart.md` o resultado da validação do T038

---

## Dependencies & Execution Order

- **Phase 1** (T001) antes de tudo.
- **Phase 2** bloqueia todas as histórias. Dentro dela: T002 → T003 → T004 → T005 (mesmo arquivo para T003 a T005, em sequência) → T006 (migrations); T007, T008 e T010 em paralelo depois dos respectivos modelos; T009 independente dos modelos.
- **US1** (T011 a T014) depende da Phase 2. É o MVP.
- **US2** (T015 a T021) depende de US1 (`ActivityAdmin` existe); T015, T018 e T019 não tocam o `ActivityAdmin`.
- **US3** (T022 a T025) depende de US1 e do T009. Pode ser feita junto de US2.
- **US4** (T026 a T029) depende de US1; a validação de publicação usa os vínculos de público de US2 (T004).
- **US5** (T030 a T032) depende de US4 (`change_status`, e refatora `publish_selected`).
- **US6** (T033 a T035) depende de US5 (`_apply_status`).
- **Polish** (T036 a T039) depois das histórias; T038 depende de T037.

### Parallel opportunities

- Phase 2: T007, T008 e T010 (testes) em paralelo, em arquivos diferentes.
- US2: T015, T018, T019, T021 em paralelo (arquivos diferentes), T016/T017 em sequência no mesmo arquivo.
- US4/US5/US6: as tarefas de teste de `test_status_service.py` e `test_activity_admin.py` marcadas [P] podem ser escritas em paralelo com a implementação da ação correspondente.

## Implementation Strategy

1. **MVP**: Phase 1, Phase 2 e US1 — cadastrar atividade como rascunho pelo Admin, com autoria.
2. **Incremento 1**: US2 e US3 — públicos-alvo e edição segura.
3. **Incremento 2**: US4 — publicar com validação (entrega o valor central ao produto).
4. **Incremento 3**: US5 e US6 — cancelar e encerrar.
5. **Fechamento**: Polish, com validação real no RDS (T038).

Cada incremento termina com `pytest` e `ruff check .` verdes.
