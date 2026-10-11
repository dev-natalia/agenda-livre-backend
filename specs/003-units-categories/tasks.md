---

description: "Lista de tarefas de Gestão de Unidades e Categorias"
---

# Tasks: Gestão de Unidades e Categorias

**Input**: Documentos de design em `/specs/003-units-categories/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Incluídos. A constituição (Princípio III) exige testes unitários com mocks, sem acesso a banco, e
cobertura total mínima de 90%. Nenhum teste pode abrir conexão com banco de dados: use instâncias de modelo
não salvas, `RequestFactory`, `SimpleNamespace` e `unittest.mock`. Chamar `clean()` é permitido; chamar
`full_clean()`, `validate_unique()` ou `validate_constraints()` em modelo real consulta o banco e NÃO é.

**Organization**: Tarefas agrupadas por história de usuário (US1 a US3 da spec), para permitir
implementação e validação independentes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência de tarefa incompleta)
- **[Story]**: história de usuário à qual a tarefa pertence (US1 a US3)
- Os caminhos são relativos à raiz do repositório

## Path Conventions

Projeto único com o Django na raiz: `config/`, `apps/` (módulos por domínio) e `tests/unit/`. Os apps
`apps/units` e `apps/categories` já existem (feature 001) com `models.py` vazio. A base abstrata e o mixin
de ações ficam em `apps/core`. Não há dependências novas. Textos de interface em português.

---

## Phase 1: Setup

**Purpose**: confirmar o ponto de partida

- [X] T001 Rodar `pytest` e `ruff check .` na raiz e confirmar que a suíte das features 001 e 002 passa com cobertura >= 90%, registrando o resultado como linha de base

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: base abstrata dos dois cadastros. Bloqueia todas as histórias.

**⚠️ CRITICAL**: nenhuma história começa antes desta fase.

- [X] T002 Em `apps/core/models.py`, criar a classe abstrata `CatalogModel(models.Model)` (`Meta.abstract = True`, `ordering = ["name"]`, `__str__` devolvendo `name`) com os campos: `id` = `UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`; `name` = `CharField(max_length=150)` (Obrigatório, "Sem espaços nas pontas; não pode ser só espaços"); `slug` = `SlugField(max_length=160, unique=True, blank=True)` ("Único; gerado de `name` quando vazio; recusado se vazio após a geração"); `description` = `TextField(blank=True)`; `is_active` = `BooleanField(default=True)`; `created_at` = `DateTimeField(auto_now_add=True)`; `updated_at` = `DateTimeField(auto_now=True)`. Usar `verbose_name` em português em todos os campos: "Nome", "Identificador", "Descrição", "Ativo", "Criado em", "Atualizado em"
- [X] T003 Em `apps/core/models.py`, implementar `CatalogModel.clean()`: aplicar `strip()` em `name`; se `slug` estiver vazio, atribuir `slugify(self.name)`; se o resultado continuar vazio, levantar `ValidationError({"slug": "Não foi possível gerar o identificador a partir do nome; informe um."})`. Não consultar o banco
- [X] T004 [P] Criar `tests/unit/core/test_catalog_model.py` testando, com uma subclasse concreta mínima não salva (ou `Unit`/`Category` depois de criados): `clean()` remove espaços do nome, gera o slug a partir do nome ("Cultura e Artes" → `cultura-e-artes`), preserva um slug informado, levanta `ValidationError` com chave `slug` quando o nome só tem símbolos, `str()` devolve o nome, e `Meta.ordering == ["name"]`

**Checkpoint**: `CatalogModel` pronta; `pytest tests/unit/core/test_catalog_model.py` verde.

---

## Phase 3: User Story 1 - Cadastrar e atualizar unidades (Priority: P1) 🎯 MVP

**Goal**: administradores cadastram e editam unidades (nome e bairro obrigatórios, slug único) pelo Django Admin.

**Independent Test**: instanciar `Unit` sem salvar e conferir campos, validação e `clean()`; instanciar `UnitAdmin` e conferir lista, busca, filtro, campos somente leitura e slug sugerido.

### Tests for User Story 1

- [X] T005 [P] [US1] Criar `tests/unit/units/test_unit_model.py` testando: `Unit` herda de `CatalogModel`; `neighborhood` é `CharField(max_length=100)` obrigatório (`blank=False`); `address` é `TextField` opcional (`blank=True`); `clean()` aplica `strip()` em `neighborhood`; `slug` tem `unique=True`; `name` NÃO tem `unique`; nomes de modelo "Unidade" e "Unidades"
- [X] T006 [P] [US1] Criar `tests/unit/units/test_unit_admin.py` testando `UnitAdmin` (instanciar com `UnitAdmin(Unit, admin.site)`, sem banco): `list_display` contém nome, bairro, identificador e situação ativa; `list_filter` contém `is_active`; `search_fields` contém `name` e `neighborhood`; `readonly_fields` contém `created_at` e `updated_at`; `prepopulated_fields == {"slug": ("name",)}`; `Unit` está registrado em `admin.site`; `UnitAdmin` herda `ActiveToggleActionsMixin` (T013) e `ActiveOnlyForeignKeyMixin`

### Implementation for User Story 1

- [X] T007 [US1] Em `apps/units/models.py`, criar `Unit(CatalogModel)` com `neighborhood = CharField(max_length=100)` ("Sem espaços nas pontas; usado depois no filtro por bairro", `verbose_name="Bairro"`) e `address = TextField(blank=True, verbose_name="Endereço")`; `Meta`: `verbose_name = "Unidade"`, `verbose_name_plural = "Unidades"`. Sobrescrever `clean()` chamando `super().clean()` e aplicando `strip()` em `neighborhood`
- [X] T008 [US1] Em `apps/units/admin.py`, registrar `UnitAdmin(ActiveToggleActionsMixin, ActiveOnlyForeignKeyMixin, admin.ModelAdmin)` com `list_display = ("name", "neighborhood", "slug", "is_active")`, `list_filter = ("is_active",)`, `search_fields = ("name", "neighborhood")`, `readonly_fields = ("created_at", "updated_at")`, `prepopulated_fields = {"slug": ("name",)}`. Depende de T013
- [X] T009 [US1] Gerar a migration inicial com `python manage.py makemigrations units` (arquivo `apps/units/migrations/0001_initial.py`, com `__init__.py` em `apps/units/migrations/`), conferir que cria `Unit` com os campos de T002 e T007 e não aplicar no banco ainda
- [X] T010 [US1] Rodar `pytest tests/unit/units` e `ruff check apps/units tests/unit/units` e corrigir falhas

**Checkpoint**: unidades cadastráveis pelo Admin; testes de US1 verdes.

---

## Phase 4: User Story 2 - Cadastrar e atualizar categorias (Priority: P1)

**Goal**: administradores cadastram e editam categorias (nome obrigatório, nome e slug únicos) pelo Django Admin.

**Independent Test**: instanciar `Category` sem salvar e conferir a restrição de nome sem diferenciar maiúsculas e minúsculas e a configuração do admin.

### Tests for User Story 2

- [X] T011 [P] [US2] Criar `tests/unit/categories/test_category_model.py` testando: `Category` herda de `CatalogModel`; `Meta.constraints` contém um `UniqueConstraint` sobre `Lower("name")` (conferir `expressions` e o `name` da restrição); `slug` tem `unique=True`; nomes de modelo "Categoria" e "Categorias"; `clean()` gera slug e remove espaços do nome (herdado)
- [X] T012 [P] [US2] Criar `tests/unit/categories/test_category_admin.py` testando `CategoryAdmin` (sem banco): `list_display` contém nome, identificador e situação ativa; `list_filter` contém `is_active`; `search_fields` contém `name`; `readonly_fields` contém `created_at` e `updated_at`; `prepopulated_fields == {"slug": ("name",)}`; `Category` registrada em `admin.site`; herda `ActiveToggleActionsMixin` e `ActiveOnlyForeignKeyMixin`

### Implementation for User Story 2

- [X] T014 [US2] Em `apps/categories/models.py`, criar `Category(CatalogModel)` com `Meta`: `verbose_name = "Categoria"`, `verbose_name_plural = "Categorias"`, `constraints = [UniqueConstraint(Lower("name"), name="category_name_ci_unique", violation_error_message="Já existe uma categoria com este nome.")]`. Sem campos adicionais
- [X] T015 [US2] Em `apps/categories/admin.py`, registrar `CategoryAdmin(ActiveToggleActionsMixin, ActiveOnlyForeignKeyMixin, admin.ModelAdmin)` com `list_display = ("name", "slug", "is_active")`, `list_filter = ("is_active",)`, `search_fields = ("name",)`, `readonly_fields = ("created_at", "updated_at")`, `prepopulated_fields = {"slug": ("name",)}`. Depende de T013
- [X] T016 [US2] Gerar a migration inicial com `python manage.py makemigrations categories` (arquivo `apps/categories/migrations/0001_initial.py`, com `__init__.py` em `apps/categories/migrations/`), conferir que inclui a restrição `category_name_ci_unique` e não aplicar no banco ainda
- [X] T017 [US2] Rodar `pytest tests/unit/categories` e `ruff check apps/categories tests/unit/categories` e corrigir falhas

**Checkpoint**: categorias cadastráveis pelo Admin; testes de US2 verdes.

---

## Phase 5: User Story 3 - Desativar sem perder histórico (Priority: P1)

**Goal**: administradores desativam e reativam unidades e categorias, em lote ou pelo formulário, sem apagar nada; registros inativos não são oferecidos em novos vínculos.

**Independent Test**: chamar as ações do mixin com um queryset simulado e conferir `update(is_active=...)` e a mensagem ao usuário; conferir que as chaves estrangeiras futuras poderão usar `ActiveOnlyForeignKeyMixin` (feature 002).

**Nota**: o mixin (T013) é pré-requisito de T008 e T015; por isso T013 e T018 vêm antes dos admins na ordem de execução (ver Dependencies).

### Tests for User Story 3

- [X] T018 [P] [US3] Criar `tests/unit/core/test_active_toggle_actions.py` testando `ActiveToggleActionsMixin` com um `ModelAdmin` falso e `MagicMock` de `request` e `queryset`: `deactivate_selected` chama `queryset.update(is_active=False)` e `message_user` com a contagem; `reactivate_selected` chama `queryset.update(is_active=True)`; ambas têm `short_description` "Desativar selecionados" e "Reativar selecionados"; `actions` do mixin lista as duas; as ações usam apenas `update`, nunca `delete`

### Implementation for User Story 3

- [X] T013 [US3] Em `apps/core/admin.py`, adicionar `ActiveToggleActionsMixin` com `actions = ["deactivate_selected", "reactivate_selected"]` e os métodos decorados com `@admin.action(description=...)`: `deactivate_selected(self, request, queryset)` faz `queryset.update(is_active=False)` e `self.message_user(request, f"{n} registro(s) desativado(s).")`; `reactivate_selected` faz o inverso com "reativado(s)". Manter o `ActiveOnlyForeignKeyMixin` existente sem alteração
- [X] T019 [US3] Documentar em `apps/core/admin.py` (docstring do mixin) que os `ModelAdmin` das atividades devem herdar `ActiveOnlyForeignKeyMixin` e declarar chaves estrangeiras para `Unit` e `Category` com `on_delete=PROTECT`, conforme `specs/003-units-categories/contracts/admin-units-categories.md`
- [X] T020 [US3] Rodar `pytest tests/unit/core/test_active_toggle_actions.py` e `ruff check apps/core tests/unit/core` e corrigir falhas

**Checkpoint**: desativação e reativação em lote disponíveis nos dois cadastros.

---

## Phase 6: Carga inicial e Polish

**Purpose**: carga repetível dos dados iniciais (FR-018) e fechamento da feature

- [X] T021 [P] Criar `apps/core/management/commands/seed_catalog.py` com um `Command` que, para cada item de constantes do módulo, faz `Unit.objects.get_or_create(slug=..., defaults={...})` e `Category.objects.get_or_create(slug=..., defaults={...})` sem alterar registros existentes. Unidade: nome "CEU Navegantes", slug `ceu-navegantes`, `neighborhood="Navegantes"`, endereço vazio. Categorias (nome → slug): Cultura e Artes → `cultura-e-artes`; Cursos e Formação → `cursos-e-formacao`; Esporte e Atividade Física → `esporte-e-atividade-fisica`; Lazer e Recreação → `lazer-e-recreacao`; Saúde e Bem-estar → `saude-e-bem-estar`; Educação e Meio Ambiente → `educacao-e-meio-ambiente`; Eventos e Encontros → `eventos-e-encontros`; Participação Comunitária → `participacao-comunitaria`, cada uma com a descrição da seção 9 de `docs/01-visao-do-produto-e-requisitos.md`. Ao final, imprimir quantos foram criados e quantos já existiam
- [X] T022 [P] Criar `tests/unit/core/test_seed_catalog.py` com `Unit.objects` e `Category.objects` substituídos por mocks (`unittest.mock.patch`): 1 chamada de `get_or_create` para a unidade e 8 para as categorias; quando `get_or_create` devolve `(obj, True)` o resumo informa criados, quando devolve `(obj, False)` informa já existentes; os slugs usados são exatamente os do contrato `contracts/management-commands.md`; nenhuma chamada altera registros existentes
- [X] T023 Adicionar ao `README.md` a seção "Carga inicial de unidades e categorias" (rodar `python manage.py safe_migrate` e depois `python manage.py seed_catalog`, que é seguro repetir) e a nota de que o bairro "Navegantes" do CEU Navegantes está provisório e deve ser confirmado pela equipe
- [X] T024 Conferir o grupo "Administrador" (feature 002): confirmar em `apps/core/permissions.py` que `sync_admin_group` concede todas as permissões existentes, sem mudança necessária, e registrar a conclusão no resumo final
- [X] T025 Rodar `pytest` (cobertura total >= 90%) e `ruff check .` na raiz e corrigir qualquer falha
- [X] T026 Seguir `specs/003-units-categories/quickstart.md` (migrations com `safe_migrate`, `seed_catalog` duas vezes e verificação no painel) contra o RDS e registrar o resultado; marcar as tarefas concluídas neste arquivo

---

## Dependencies & Execution Order

- **Phase 1 → Phase 2** em sequência. Phase 2 bloqueia todas as histórias.
- **T013 (mixin de ações, US3)** deve vir antes de T008 e T015, pois os admins o herdam. Ordem prática: Phase 2 → T013 e T018 → US1 → US2 → resto de US3 → Phase 6.
- **US1 e US2** são independentes entre si (apps e arquivos diferentes) e podem rodar em paralelo depois de T002, T003 e T013.
- **T021** depende de T007 e T014 (modelos). **T026** depende de todas as outras.

## Parallel Opportunities

- Depois de T002/T003: T004, T005, T006, T011, T012 e T018 (arquivos de teste distintos) em paralelo.
- T007 (unidade) e T014 (categoria) em paralelo, assim como T008 e T015 depois de T013.
- T021 e T022 em paralelo com T023.

## Implementation Strategy

1. **MVP**: Phase 1, Phase 2, T013 e US1 (unidades). O CEU Navegantes já pode ser cadastrado.
2. **Incremento**: US2 (categorias) e depois o restante de US3 (documentação do vínculo e testes de ações).
3. **Fechamento**: carga inicial, README, cobertura >= 90% e validação pelo quickstart.
4. Migrations são geradas, mas só aplicadas no RDS na última tarefa, com `safe_migrate`.
