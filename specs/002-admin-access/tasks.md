---

description: "Lista de tarefas de Administração e Acesso"
---

# Tasks: Administração e Acesso

**Input**: Documentos de design em `/specs/002-admin-access/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Incluídos. A constituição (Princípio III) exige testes unitários com mocks, sem acesso a banco, e
cobertura total mínima de 90%. Nenhum teste pode abrir conexão com banco de dados (use `RequestFactory`,
`SimpleNamespace` e `unittest.mock`).

**Organization**: Tarefas agrupadas por história de usuário (US1 a US4 da spec), para permitir
implementação e validação independentes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência de tarefa incompleta)
- **[Story]**: história de usuário à qual a tarefa pertence (US1 a US4)
- Os caminhos são relativos à raiz do repositório

## Path Conventions

Projeto único com o Django na raiz: `config/` (projeto), `apps/` (módulos por domínio) e `tests/`. Toda
a lógica nova fica em `apps/core`. Não há dependências novas nem modelos novos (usuário padrão do Django).

---

## Phase 1: Setup

**Purpose**: confirmar o ponto de partida antes de alterar a configuração

- [X] T001 Rodar `pytest` e `ruff check .` na raiz e confirmar que a suíte da feature 001 passa com cobertura >= 90%, registrando o resultado como linha de base

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: ativar o Django Admin e a autenticação por sessão. Bloqueia todas as histórias.

**⚠️ CRITICAL**: nenhuma história começa antes desta fase.

- [X] T002 Em `config/settings.py`, adicionar a `INSTALLED_APPS` (antes de `corsheaders`) `django.contrib.admin`, `django.contrib.messages` e `django.contrib.staticfiles`, mantendo `apps.core` depois de `django.contrib.auth` e dos demais apps nativos
- [X] T003 Em `config/settings.py`, deixar `MIDDLEWARE` exatamente nesta ordem: `SecurityMiddleware`, `CorsMiddleware`, `django.contrib.sessions.middleware.SessionMiddleware`, `CommonMiddleware`, `django.middleware.csrf.CsrfViewMiddleware`, `django.contrib.auth.middleware.AuthenticationMiddleware`, `django.contrib.messages.middleware.MessageMiddleware`
- [X] T004 Em `config/settings.py`, definir `TEMPLATES` com `DjangoTemplates`, `APP_DIRS=True` e os context processors `request`, `auth` e `messages`, e definir `AUTH_PASSWORD_VALIDATORS` com os quatro validadores padrão do Django (`UserAttributeSimilarityValidator`, `MinimumLengthValidator`, `CommonPasswordValidator`, `NumericPasswordValidator`)
- [X] T005 Em `config/urls.py`, adicionar `path("admin/", admin.site.urls)` mantendo `path("api/v1/", include("apps.core.urls"))` inalterado
- [X] T006 Rodar `pytest` e ajustar, em `tests/unit/config/test_settings.py` e `tests/unit/config/test_structure.py`, qualquer teste da feature 001 que compare listas de apps ou middlewares de forma exata e passe a falhar com a nova configuração

**Checkpoint**: o projeto inicia com o Admin ativo e a suíte da feature 001 continua verde.

---

## Phase 3: User Story 1 - Entrar na área administrativa (Priority: P1) 🎯 MVP

**Goal**: quem não está autenticado, tem credenciais inválidas, conta inativa ou conta sem acesso administrativo não entra no painel, e uma conta ativa com acesso entra.

**Independent Test**: sem login, `/admin/` redireciona para `/admin/login/`; conta ativa e `is_staff` passa em `admin.site.has_permission`; anônimo, inativo e sem `is_staff` não passam.

### Tests for User Story 1

- [X] T007 [P] [US1] Criar `tests/unit/core/test_admin_access.py` testando `admin.site.has_permission` com `RequestFactory` e usuários simulados (`SimpleNamespace`): anônimo, `is_active=False`, `is_staff=False` e ativo com `is_staff=True`, onde só o último retorna `True` (FR-001, FR-003, FR-005)
- [X] T008 [P] [US1] Em `tests/unit/core/test_admin_access.py`, testar sem banco que `resolve("/admin/")` e `resolve("/admin/login/")` apontam para o Admin e que `resolve("/api/v1/health/")` continua resolvendo (FR-016)
- [X] T009 [P] [US1] Em `tests/unit/config/test_settings.py`, testar que `AUTH_PASSWORD_VALIDATORS` contém os quatro validadores, que `SessionMiddleware` vem antes de `AuthenticationMiddleware`, que `CsrfViewMiddleware` está ativo e que `PASSWORD_HASHERS` não foi sobrescrito (senhas só com hash, FR-004)
- [X] T010 [P] [US1] Em `tests/unit/config/test_settings.py`, testar que não existe backend ou middleware de bloqueio por tentativas: `AUTHENTICATION_BACKENDS` é o padrão e `MIDDLEWARE` não contém nada de limite de login (FR-015)

### Implementation for User Story 1

- [X] T011 [US1] Criar `apps/core/admin.py` definindo `admin.site.site_header`, `admin.site.site_title` e `admin.site.index_title` em português (por exemplo "Agenda Livre — Administração")
- [X] T012 [US1] Rodar `pytest tests/unit/core/test_admin_access.py tests/unit/config/test_settings.py` e confirmar que passam sem acesso a banco

**Checkpoint**: US1 verificável de forma independente; o painel exige login.

---

## Phase 4: User Story 2 - Limitar operações por permissão (Priority: P1)

**Goal**: existe um único perfil, o grupo "Administrador", com todas as permissões. Uma conta sem o grupo não executa nenhuma operação.

**Independent Test**: `sync_admin_group` cria o grupo e define todas as permissões de forma idempotente; o sinal só age no último app; um usuário sem permissão recebe `False` em `has_perm`.

### Tests for User Story 2

- [X] T013 [P] [US2] Criar `tests/unit/core/test_permissions.py` testando `sync_admin_group()` com `Group` e `Permission` simulados (`unittest.mock.patch`): cria o grupo "Administrador" via `get_or_create`, chama `permissions.set` com todas as permissões existentes e retorna o grupo (FR-007)
- [X] T014 [P] [US2] Em `tests/unit/core/test_permissions.py`, testar a idempotência: duas chamadas seguidas usam `get_or_create` e `set` sem duplicar nada
- [X] T015 [P] [US2] Em `tests/unit/core/test_permissions.py`, testar o receptor `post_migrate`: age quando `sender` é o último `AppConfig` de `apps.get_app_configs()` e não age nos demais, e repassa `using` (R3)
- [X] T016 [P] [US2] Em `tests/unit/core/test_permissions.py`, testar `is_admin_account(user)`: verdadeiro só para conta ativa, `is_staff` e com o grupo "Administrador"; falso para anônimo, inativa, sem `is_staff` ou sem o grupo (FR-008)

### Implementation for User Story 2

- [X] T017 [US2] Criar `apps/core/permissions.py` com `ADMIN_GROUP_NAME = "Administrador"`, `sync_admin_group(using="default")` (cria o grupo com `Group.objects.using(using).get_or_create` e define `group.permissions.set(Permission.objects.using(using).all())`), `is_admin_account(user)` e o receptor `sync_admin_group_after_migrate(sender, using, **kwargs)` que só chama `sync_admin_group` quando `sender` é o último `AppConfig`
- [X] T018 [US2] Em `apps/core/apps.py`, adicionar `ready()` em `CoreConfig` conectando o receptor de T017 ao sinal `post_migrate` com `dispatch_uid="core.sync_admin_group"`, sem passar `sender` (para rodar depois das permissões de todos os apps)
- [X] T019 [US2] Em `tests/unit/core/test_permissions.py`, testar que `CoreConfig.ready()` conecta o receptor ao sinal `post_migrate` (verificar a conexão com `post_migrate.has_listeners` ou patch de `connect`)
- [X] T020 [US2] Rodar `pytest tests/unit/core/test_permissions.py` e confirmar que passam sem acesso a banco

**Checkpoint**: US1 e US2 funcionam; o perfil e a regra de acesso estão definidos.

---

## Phase 5: User Story 3 - Gerenciar o conteúdo pela interface administrativa (Priority: P2)

**Goal**: o painel apresenta rótulos em português e relacionamentos selecionáveis sem oferecer registros inativos.

**Independent Test**: com um modelo relacionado simulado que tem `is_active`, `formfield_for_foreignkey` filtra `is_active=True`; sem o campo, não filtra.

### Tests for User Story 3

- [X] T021 [P] [US3] Criar `tests/unit/core/test_admin_mixin.py` testando `ActiveOnlyForeignKeyMixin.formfield_for_foreignkey` com `db_field` simulado cujo `remote_field.model` tem o campo `is_active`: o `queryset` entregue ao `super()` é filtrado com `is_active=True` (FR-012)
- [X] T022 [P] [US3] Em `tests/unit/core/test_admin_mixin.py`, testar que, se o modelo relacionado não tem `is_active`, o `queryset` não é alterado e que um `queryset` já informado em `kwargs` é respeitado e também filtrado quando há `is_active`

### Implementation for User Story 3

- [X] T023 [US3] Em `apps/core/admin.py`, criar `ActiveOnlyForeignKeyMixin` com `formfield_for_foreignkey(self, db_field, request, **kwargs)`: se o modelo relacionado tiver o campo `is_active`, usar `kwargs["queryset"]` (ou `db_field.remote_field.model._default_manager.all()`) filtrado por `is_active=True` e delegar a `super()`. Documentar em docstring que os cadastros das próximas features devem herdar o mixin
- [X] T024 [US3] Rodar `pytest tests/unit/core/test_admin_mixin.py` e confirmar que passam sem acesso a banco

**Checkpoint**: US1 a US3 funcionam; o painel está pronto para receber os cadastros das próximas features.

---

## Phase 6: User Story 4 - Conceder e retirar acessos (Priority: P2)

**Goal**: criar a primeira conta de administrador por comando e as demais pelo painel, e desativar contas sem apagar registros.

**Independent Test**: `create_admin` cria conta ativa, `is_staff` e no grupo, com senha validada e sem eco; falha para usuário existente, senhas diferentes ou senha fraca.

### Tests for User Story 4

- [X] T025 [P] [US4] Criar `tests/unit/core/test_create_admin.py` testando o caminho feliz com `getpass.getpass` simulado e `User.objects` simulado: cria a conta com `is_staff=True`, `is_active=True`, define a senha com `set_password`, adiciona o grupo devolvido por `sync_admin_group` e imprime a confirmação sem a senha (FR-013)
- [X] T026 [P] [US4] Em `tests/unit/core/test_create_admin.py`, testar as falhas com `CommandError` e sem criar a conta: usuário já existente, duas senhas diferentes e senha rejeitada por `validate_password` (mensagem do validador incluída)
- [X] T027 [P] [US4] Em `tests/unit/core/test_create_admin.py`, testar que a senha nunca aparece em `stdout`, `stderr` nem nas mensagens de erro, e que o comando não aceita a senha como argumento (SC-004)

### Implementation for User Story 4

- [X] T028 [US4] Criar `apps/core/management/commands/create_admin.py` com `Command(BaseCommand)`: argumento posicional `username`; verifica se o usuário existe (`CommandError` se sim); pede a senha duas vezes com `getpass.getpass`; valida com `django.contrib.auth.password_validation.validate_password` convertendo `ValidationError` em `CommandError`; cria o usuário com `User.objects.create_user(username, password=...)`, `is_staff=True`; adiciona o grupo retornado por `sync_admin_group()`; imprime só a confirmação. Seguir o estilo de `check_db.py` e `safe_migrate.py`
- [X] T029 [US4] Rodar `pytest tests/unit/core/test_create_admin.py` e confirmar que passam sem acesso a banco

**Checkpoint**: todas as histórias funcionam de forma independente.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T030 [P] Atualizar `README.md` com a seção "Acesso administrativo": `safe_migrate`, `create_admin`, `DJANGO_DEBUG=true` para os estáticos do Admin, entrada em `/admin/`, perfil único "Administrador" e o que ele permite, como criar e desativar contas pelo painel, e a ausência de bloqueio de login e de recuperação de senha por e-mail (FR-013, FR-014, FR-017)
- [X] T031 [P] Atualizar `.env.example` somente se alguma variável nova for necessária (esperado: nenhuma), e confirmar que nenhuma senha real está versionada (`git grep -i "password"` não encontra valores reais)
- [X] T032 Rodar `ruff check .` e corrigir qualquer violação em todos os arquivos novos e alterados
- [X] T033 Rodar `pytest` completo e confirmar que todos os testes passam, sem acesso a banco, com cobertura total >= 90%
- [X] T034 Executar o `quickstart.md` contra o banco RDS: `safe_migrate`, `create_admin`, `runserver` e os passos de 1 a 7 da seção 3; registrar o resultado
  - Resultado (2026-10-11): `check_db` e `safe_migrate` OK no RDS; grupo "Administrador" criado com 24/24 permissões; passos 1, 2, 3, 4, 6 e 7 verificados com contas temporárias (já removidas). `create_admin` interativo e o passo 5 no navegador confirmados manualmente pela equipe.
- [X] T035 Marcar as tarefas concluídas neste arquivo e atualizar `docs/PENDENCIAS.md` (itens "Perfis e permissões do admin" e "usuário padrão ou personalizado" resolvidos)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sem dependências.
- **Foundational (Phase 2)**: depende da Setup e bloqueia todas as histórias.
- **User Stories (Phase 3 a 6)**: dependem da Foundational.
  - US1 e US2 (P1) são independentes entre si e podem ser feitas em paralelo, mas ambas tocam `apps/core`: US1 em `admin.py` e US2 em `permissions.py` e `apps.py`.
  - US3 (P2) estende `apps/core/admin.py` criado na US1, então vem depois dela.
  - US4 (P2) usa `sync_admin_group` da US2, então vem depois dela.
- **Polish (Phase 7)**: depende das histórias desejadas.

### Within Each User Story

- Os testes são escritos antes da implementação e devem falhar primeiro.
- Implementação, depois a execução dos testes da história.

### Parallel Opportunities

- T007 a T010 (testes da US1) em paralelo.
- T013 a T016 (testes da US2) em paralelo.
- T021 e T022 (testes da US3) em paralelo, e T025 a T027 (testes da US4) em paralelo.
- T030 e T031 em paralelo na fase final.
- US1 e US2 por pessoas diferentes após a Foundational.

---

## Parallel Example: User Story 2

```text
Task: "Criar tests/unit/core/test_permissions.py com os testes de sync_admin_group (T013, T014)"
Task: "Adicionar em tests/unit/core/test_permissions.py os testes do receptor e de is_admin_account (T015, T016)"
```

---

## Implementation Strategy

### MVP First (User Story 1)

1. Fase 1 e Fase 2.
2. Fase 3 (US1): o painel exige login.
3. Validar: `/admin/` redireciona sem login.

### Incremental Delivery

1. US1: acesso protegido.
2. US2: perfil único e permissões.
3. US3: painel preparado para os cadastros (mixin).
4. US4: criação e desativação de contas.
5. Polish: README, estilo, cobertura e validação no RDS.

---

## Notes

- [P] = arquivos diferentes, sem dependências.
- [Story] mapeia a tarefa à história para rastreabilidade.
- Nenhum teste acessa banco: `config/settings_test.py` já bloqueia o acesso.
- O comportamento interno do login do Django não é retestado; testamos a nossa configuração e o nosso código.
- Commits pequenos e descritivos, após cada tarefa ou grupo lógico.
