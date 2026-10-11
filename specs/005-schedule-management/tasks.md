---

description: "Lista de tarefas de Gestão de Programações"
---

# Tasks: Gestão de Programações

**Input**: Documentos de design em `/specs/005-schedule-management/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Incluídos. A constituição (Princípio III) exige testes unitários com mocks, sem acesso a banco, e
cobertura total mínima de 90%. Nenhum teste pode abrir conexão com banco de dados: use instâncias de modelo
não salvas, `RequestFactory`, `SimpleNamespace` e `unittest.mock`. Chamar `clean()` é permitido; chamar
`full_clean()`, `validate_unique()` ou `validate_constraints()` em modelo real consulta o banco e NÃO é.

**Organization**: Tarefas agrupadas por história de usuário (US1 a US4 da spec), para permitir
implementação e validação independentes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência de tarefa incompleta)
- **[Story]**: história de usuário à qual a tarefa pertence (US1 a US4)
- Os caminhos são relativos à raiz do repositório

## Path Conventions

Projeto único com o Django na raiz: `config/`, `apps/` (módulos por domínio) e `tests/unit/`. O app
`apps/schedules` já existe (feature 001) com `models.py` vazio e `SchedulesConfig`. `Activity` e
`PUBLIC_STATUSES` ficam em `apps/activities/models.py` (feature 004). `TIME_ZONE = "America/Sao_Paulo"` e
`USE_TZ = True` já estão em `config/settings.py`. Não há dependências novas. Textos de interface em
português. Os diretórios de teste existentes não têm `__init__.py`; seguir o padrão do repositório.

---

## Phase 1: Setup

**Purpose**: confirmar o ponto de partida

- [X] T001 Rodar `pytest` e `ruff check .` na raiz e confirmar que a suíte das features 001 a 004 passa com cobertura >= 90%, registrando o resultado como linha de base

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: modelos e migration, usados por todas as histórias. Bloqueia todas elas.

**⚠️ CRITICAL**: nenhuma história começa antes desta fase.

- [X] T002 Em `apps/schedules/models.py`, criar `Schedule(models.Model)` com `verbose_name = "Programação"` / `"Programações"` e `ordering = ["start_date", "start_time"]`. Declarar `class Type(models.TextChoices)` com `ONE_TIME = "ONE_TIME", "Pontual"` e `RECURRING = "RECURRING", "Recorrente"`. Campos: `id` = `UUIDField(primary_key=True, default=uuid.uuid4, editable=False)`; `activity` = `ForeignKey("activities.Activity", on_delete=PROTECT, related_name="schedules")` (obrigatório); `schedule_type` = `CharField(max_length=20, choices=Type.choices)` (obrigatório); `start_date` = `DateField()` ("Obrigatório; primeiro dia do período (inclusive)"); `end_date` = `DateField()` ("Obrigatório; último dia do período (inclusive)"); `start_time` = `TimeField()` (obrigatório); `end_time` = `TimeField()` ("Obrigatório; posterior a `start_time`"); `created_by` e `updated_by` = `ForeignKey(settings.AUTH_USER_MODEL, on_delete=PROTECT, related_name="+", editable=False)`; `created_at` = `DateTimeField(auto_now_add=True)`; `updated_at` = `DateTimeField(auto_now=True)`. Usar `verbose_name` em português (Atividade, Tipo, Data inicial, Data final, Horário de início, Horário de término, Criada por, Atualizada por, Criada em, Atualizada em). Em `Meta.constraints`, três `CheckConstraint`s: `start_date <= end_date` (nome `schedule_dates_ordered`), `start_time < end_time` (nome `schedule_times_ordered`) e `~Q(schedule_type="ONE_TIME") | Q(start_date=F("end_date"))` (nome `schedule_one_time_single_date`). Em `Meta.indexes`: (`activity`) e (`start_date`, `end_date`). `__str__` devolve `f"{activity} ({get_schedule_type_display()})"`
- [X] T003 Em `apps/schedules/models.py`, criar `ScheduleWeekday(models.Model)` com `id` UUID (PK), `schedule` = `ForeignKey(Schedule, on_delete=CASCADE, related_name="weekdays")` e `weekday` = `PositiveSmallIntegerField(choices=Weekday.choices)` ("1 a 7 (1 = segunda-feira ... 7 = domingo), com `choices` e nomes em português"). Declarar `class Weekday(models.IntegerChoices)` com `MONDAY = 1, "Segunda-feira"`, `TUESDAY = 2, "Terça-feira"`, `WEDNESDAY = 3, "Quarta-feira"`, `THURSDAY = 4, "Quinta-feira"`, `FRIDAY = 5, "Sexta-feira"`, `SATURDAY = 6, "Sábado"`, `SUNDAY = 7, "Domingo"`. `Meta`: `verbose_name = "Dia da semana"` / `"Dias da semana"`, `ordering = ["weekday"]`, `UniqueConstraint(fields=["schedule", "weekday"], name="unique_schedule_weekday")` e `CheckConstraint` `weekday` entre 1 e 7 (nome `schedule_weekday_range`)
- [X] T004 Em `apps/schedules/models.py`, implementar `Schedule.clean()` seguindo `data-model.md` ("Validações"): se `start_date`, `end_date`, `start_time` e `end_time` estiverem todos preenchidos (campos já recusados pelo formulário não geram erro duplicado), levantar `ValidationError` com dicionário de erros por campo: `{"end_date": "A data final não pode ser anterior à data inicial."}` quando `start_date > end_date`; `{"end_time": "O horário de término deve ser posterior ao de início."}` quando `start_time >= end_time`; `{"end_date": "Em programação pontual, a data final deve ser igual à inicial."}` quando `schedule_type == ONE_TIME` e `start_date != end_date` e o período não estiver já invertido. Reunir todos os erros num só `ValidationError`
- [X] T005 Gerar a migration com `python manage.py makemigrations schedules` (nome `0001_initial`), conferir que depende de `activities` e `AUTH_USER_MODEL` e que `python manage.py makemigrations --check --dry-run` não acusa pendências. Não aplicar no banco aqui
- [X] T006 [P] Criar `tests/unit/schedules/test_schedule_model.py` testando com instâncias não salvas: `str()`; `Type` tem os dois valores com rótulos "Pontual" e "Recorrente"; `Meta.ordering`, `verbose_name` e `verbose_name_plural`; as três `CheckConstraint`s e os dois índices existem com os nomes de T002; `activity` usa `on_delete=PROTECT` e `related_name="schedules"`; `clean()` aceita programação válida; recusa período invertido (erro em `end_date`), término igual ou anterior ao início, incluindo `23:00` → `01:00` (erro em `end_time`), e pontual com datas diferentes (erro em `end_date`); aceita recorrente com datas diferentes; relata mais de um erro ao mesmo tempo; não levanta erro quando algum campo é `None`
- [X] T007 [P] Criar `tests/unit/schedules/test_schedule_weekday_model.py` testando: `Weekday` tem sete valores de 1 a 7 na ordem segunda a domingo com rótulos em português; `UniqueConstraint` `unique_schedule_weekday`, `CheckConstraint` `schedule_weekday_range`, `related_name="weekdays"`, `on_delete=CASCADE`, `ordering` e nomes `verbose_name`

**Checkpoint**: modelos e migration prontos; `pytest tests/unit/schedules` verde.

---

## Phase 3: User Story 1 - Cadastrar programação pontual (Priority: P1) 🎯 MVP

**Goal**: administradores cadastram pelo Admin uma programação para uma única data, com autoria registrada e as regras de período e horário aplicadas.

**Independent Test**: instanciar `ScheduleAdmin` e conferir lista, filtros, busca, campos somente leitura, preenchimento inicial da atividade por `?activity=` e `save_model` preenchendo autoria.

- [X] T008 [US1] Em `apps/schedules/forms.py`, criar `ScheduleAdminForm(forms.ModelForm)` com `Meta.model = Schedule` e `fields = ("activity", "schedule_type", "start_date", "end_date", "start_time", "end_time")`. Nesta etapa o formulário só precisa existir e herdar `Schedule.clean()` (a validação do modelo roda no `_post_clean`); o campo dos dias da semana entra na US2
- [X] T009 [US1] Em `apps/schedules/admin.py`, criar `ScheduleAdmin(admin.ModelAdmin)` registrado para `Schedule`, com: `form = ScheduleAdminForm`; `list_display = ("activity", "schedule_type", "start_date", "end_date", "start_time", "end_time", "updated_at")`; `list_filter = ("schedule_type", "start_date", "end_date")`; `search_fields = ("activity__title",)`; `list_select_related = ("activity",)`; `autocomplete_fields = ("activity",)`; `readonly_fields = ("created_by", "updated_by", "created_at", "updated_at")`; `fields` na ordem: `activity`, `schedule_type`, `start_date`, `end_date`, `start_time`, `end_time`, `created_by`, `updated_by`, `created_at`, `updated_at`. Para o `autocomplete_fields` funcionar, o `ActivityAdmin` já tem `search_fields` (feature 004); confirmar. Os filtros usam `admin.DateFieldListFilter` por padrão para datas
- [X] T010 [US1] Em `ScheduleAdmin.save_model(request, obj, form, change)`, definir `obj.created_by = request.user` quando `not change`, `obj.updated_by = request.user` sempre, e então `super().save_model(...)`. O Admin preenche `activity` a partir do parâmetro `?activity=<id>` da URL de adição por padrão (nenhum código extra), mas conferir no teste que `activity` está em `fields`
- [X] T011 [P] [US1] Criar `tests/unit/schedules/test_schedule_admin.py` testando: `Schedule` registrada com `ScheduleAdmin`; `list_display`, `list_filter`, `search_fields`, `list_select_related`, `autocomplete_fields`, `readonly_fields` e `fields` conforme T009; `form is ScheduleAdminForm`; `save_model` em criação define `created_by` e `updated_by` com o usuário (com `super().save_model` mockado via `patch.object(admin.ModelAdmin, "save_model")`); em edição só `updated_by` muda
- [X] T012 [P] [US1] Criar `tests/unit/schedules/test_schedule_form.py` testando `ScheduleAdminForm` sem banco: `Meta.model` e `Meta.fields`; os rótulos dos campos vêm do modelo (em português); um formulário instanciado com dados de uma programação pontual válida (com `activity` substituída por mock, via `patch` no `clean_fields`/queryset do campo ou chamando `instance.clean()` diretamente) não acusa erro de período e horário, e com término anterior ao início acusa o erro em `end_time`

**Checkpoint**: programação pontual cadastrável pelo Admin; `pytest tests/unit/schedules` verde.

---

## Phase 4: User Story 2 - Cadastrar programação recorrente (Priority: P1)

**Goal**: administradores cadastram programações recorrentes com dias da semana, sem dias repetidos, e a pontual não aceita dias.

**Independent Test**: testar o formulário com `cleaned_data` simulado (recorrente sem dia, pontual com dia, dias repetidos tratados) e `save_related` com `ScheduleWeekday.objects` mockado.

- [X] T013 [US2] Em `apps/schedules/forms.py`, adicionar a `ScheduleAdminForm` o campo `weekdays = forms.TypedMultipleChoiceField(label="Dias da semana", choices=ScheduleWeekday.Weekday.choices, coerce=int, required=False, widget=forms.CheckboxSelectMultiple, help_text="Obrigatório para programações recorrentes. Deve ficar vazio nas pontuais.")` e incluí-lo no `__init__` como valor inicial dos dias já gravados quando `self.instance.pk` existir (`list(self.instance.weekdays.values_list("weekday", flat=True))`; em instância sem `pk`, vazio). Duplicados são impossíveis por serem checkboxes; ainda assim usar `set(...)` ao ler
- [X] T014 [US2] Em `ScheduleAdminForm.clean()` (chamar `super().clean()` primeiro), aplicar as regras entre tabelas: com `schedule_type == RECURRING` e nenhum dia, `add_error("weekdays", "Selecione ao menos um dia da semana.")`; com `schedule_type == ONE_TIME` e algum dia, `add_error("weekdays", "Programação pontual não usa dias da semana.")`. Não validar quando `schedule_type` estiver ausente do `cleaned_data` (já tem erro de campo obrigatório)
- [X] T015 [US2] Em `ScheduleAdmin` (`apps/schedules/admin.py`), incluir `weekdays` em `fields` (depois de `end_time`) e implementar `save_related(request, form, formsets, change)`: chamar `super().save_related(...)`; ler `chosen = set(form.cleaned_data.get("weekdays") or [])`; `current = set(form.instance.weekdays.values_list("weekday", flat=True))`; remover as linhas de `current - chosen` (`form.instance.weekdays.filter(weekday__in=...).delete()`) e criar as de `chosen - current` com `ScheduleWeekday.objects.bulk_create([...])`. Sem alterações quando os conjuntos já coincidem (nenhuma consulta de escrita)
- [X] T016 [US2] Em `ScheduleAdmin`, adicionar a coluna `weekday_names` em `list_display` (antes de `updated_at`): método com `@admin.display(description="Dias da semana")` que devolve os nomes abreviados dos dias da programação em ordem, separados por vírgula ("Ter, Qui"), ou "—" quando não houver (pontual). O método chama `format_weekdays(obj)` (definida em `apps/schedules/services.py`, T022). Em `get_queryset`, `prefetch_related("weekdays")` para evitar uma consulta por linha
- [X] T017 [P] [US2] Ampliar `tests/unit/schedules/test_schedule_form.py` testando: o campo `weekdays` tem as sete opções na ordem, `required=False`, widget de checkboxes e a ajuda do contrato; `clean()` com recorrente sem dias adiciona o erro "Selecione ao menos um dia da semana." em `weekdays`; com pontual e dias adiciona "Programação pontual não usa dias da semana."; recorrente com dias e pontual sem dias não adicionam erro; `schedule_type` ausente não adiciona erro de dias; o valor inicial lê os dias gravados (mock de `instance.weekdays.values_list`) e é vazio para instância sem `pk`
- [X] T018 [P] [US2] Ampliar `tests/unit/schedules/test_schedule_admin.py` testando `save_related` com `super().save_related` mockado e `ScheduleWeekday.objects.bulk_create` mockado: cria só os dias que faltam, apaga só os que sobraram, não escreve nada quando os conjuntos coincidem, trata `cleaned_data["weekdays"]` ausente ou vazio como conjunto vazio; `weekday_names` devolve "Ter, Qui" para os dias 2 e 4, "—" sem dias; `get_queryset` aplica `prefetch_related("weekdays")` (mock de `super().get_queryset`)

**Checkpoint**: recorrência cadastrável sem dias duplicados; `pytest` verde.

---

## Phase 5: User Story 3 - Editar uma programação (Priority: P1)

**Goal**: administradores editam datas, horários, tipo e dias, com validações reaplicadas, autoria atualizada e exclusão que preserva a atividade.

**Independent Test**: com mocks, conferir que a edição mantém `created_by`, atualiza `updated_by`, troca o conjunto de dias e que a exclusão da programação não toca a atividade.

- [X] T019 [US3] Em `ScheduleAdmin`, conferir (sem código novo, se T010 e T015 já cobrem) que a edição: reaplica as validações do modelo e do formulário (herdadas), mantém `created_by` e o `id` (T010), atualiza `updated_by` mesmo quando só os dias mudam (o Admin sempre chama `save_model`), e converge o conjunto de dias para exatamente o escolhido, inclusive ao mudar de recorrente para pontual com todos os dias desmarcados (T015 remove os antigos). Registrar qualquer ajuste necessário
- [X] T020 [P] [US3] Ampliar `tests/unit/schedules/test_schedule_admin.py` testando o fluxo de edição: `save_model` com `change=True` não altera `created_by`; `save_related` ao mudar de recorrente (dias 2 e 4) para pontual (conjunto vazio) apaga os dois dias; ao trocar os dias de {2, 4} para {4, 6} apaga o 2 e cria o 6; o `id` da instância não muda; `Schedule._meta.get_field("activity").remote_field.on_delete` é `PROTECT` e `ScheduleWeekday` usa `CASCADE` (a exclusão da programação remove os dias e não a atividade)
- [X] T021 [P] [US3] Ampliar `tests/unit/schedules/test_schedule_form.py` testando a edição: instância existente recorrente trocada para pontual com os dias ainda marcados gera o erro "Programação pontual não usa dias da semana."; trocada para pontual sem dias é aceita; período invertido e término não posterior ao início em edição geram os erros do modelo

**Checkpoint**: edição segura de programações; `pytest` verde.

---

## Phase 6: User Story 4 - Consultar as próximas ocorrências (Priority: P2)

**Goal**: o sistema calcula as próximas ocorrências de uma atividade a partir de suas programações, e a administração as vê na página da atividade, junto com a lista de programações e um atalho para adicionar uma nova.

**Independent Test**: testar `iter_occurrences` e `upcoming_occurrences` com programações simuladas e relógio injetado (casos de `contracts/occurrences-service.md`), e o `ActivityAdmin` com mocks.

- [X] T022 [US4] Criar `apps/schedules/services.py` com `@dataclass(frozen=True) class Occurrence` (`date`, `start_time`, `end_time`, `schedule_id`) e `iter_occurrences(schedule, weekdays, from_date)` conforme `contracts/occurrences-service.md`: `ONE_TIME` gera uma ocorrência em `start_date` se `start_date >= from_date`; `RECURRING` percorre cada data de `max(start_date, from_date)` até `end_date` inclusive e gera as cujo `isoweekday()` está em `weekdays`; período sem dia coincidente gera nada. Gerador em ordem crescente de data. Criar também `format_weekdays(schedule)`: devolve os nomes abreviados ("Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom") dos dias de `schedule.weekdays.all()` em ordem de dia, separados por ", ", ou "—" quando não houver
- [X] T023 [US4] Em `apps/schedules/services.py`, criar `upcoming_occurrences(activity, now=None, limit=10)`: devolver `[]` se `activity.status not in PUBLIC_STATUSES` (importar de `apps.activities.models`); `now = timezone.localtime(now or timezone.now())`; obter as programações com `activity.schedules.prefetch_related("weekdays")`; para cada uma, `weekdays = {w.weekday for w in schedule.weekdays.all()}` e iterar `iter_occurrences(schedule, weekdays, now.date())`; descartar a ocorrência cuja `date == now.date()` e `end_time <= now.time()`; juntar tudo, ordenar por (`date`, `start_time`) e devolver os primeiros `limit` itens (levantar `ValueError` se `limit < 1`)
- [X] T024 [P] [US4] Criar `tests/unit/schedules/test_occurrences_service.py` com `SimpleNamespace` no lugar das programações e `weekdays` como conjunto, cobrindo cada linha da tabela "Casos de referência" de `contracts/occurrences-service.md` (pontual de hoje ainda não terminada aparece e já terminada não; recorrente terça e quinta de novembro devolve 10, 12, 17, 19, 24 e 26; período sem dia coincidente é vazio; atividade `DRAFT`, `CANCELLED` e `FINISHED` devolvem vazio) e ainda: datas inicial e final são inclusivas; `from_date` no meio do período corta as anteriores; programação no passado não gera; `ONE_TIME` ignora `weekdays`; ordenação por data e depois por horário entre duas programações; `limit` corta o resultado; `limit=0` levanta `ValueError`; `now` recebido em UTC é convertido para o fuso `America/Sao_Paulo` (ex.: 2026-11-10 02:00 UTC é 2026-11-09 23:00 local); `now=None` usa `timezone.now` (mock); atividade sem programações devolve vazio. O queryset é simulado com `MagicMock` (`activity.schedules.prefetch_related.return_value = [...]`)
- [X] T025 [US4] Em `apps/activities/admin.py`, criar `ScheduleReadOnlyInline(admin.TabularInline)` com `model = Schedule`, `extra = 0`, `can_delete = False`, `show_change_link = True`, `fields` e `readonly_fields = ("schedule_type", "start_date", "end_date", "start_time", "end_time", "weekday_names")`, `has_add_permission` devolvendo `False`, `verbose_name_plural = "Programações"`. `weekday_names` é método do inline com os nomes abreviados dos dias (mesma regra do T016; reaproveitar a função `format_weekdays(schedule)` definida em `apps/schedules/services.py` (criar no T022; T016 deve importá-la de lá, em vez de duplicar a lógica))
- [X] T026 [US4] Em `ActivityAdmin` (`apps/activities/admin.py`), incluir `ScheduleReadOnlyInline` em `inlines` (depois do inline de públicos) e adicionar o campo somente leitura `upcoming_occurrences_display` (rótulo "Próximas ocorrências") em `readonly_fields` e `fields`, depois de `updated_at`. O método: sem `obj.pk`, devolve "Salve a atividade para adicionar programações."; com `obj.status` fora de `PUBLIC_STATUSES`, devolve "Sem ocorrências: a atividade não está publicada."; caso contrário chama `upcoming_occurrences(obj)`, devolve "Sem próximas ocorrências." se vazio ou uma lista HTML (`format_html_join`) com "dd/mm/aaaa, HH:MM–HH:MM"; em todos os casos com `obj.pk`, acrescentar o link "Adicionar programação" para `reverse("admin:schedules_schedule_add") + f"?activity={obj.pk}"` (`format_html`). Usar `django.utils.html` para evitar injeção de HTML
- [X] T027 [P] [US4] Ampliar `tests/unit/activities/test_activity_admin.py` testando: `ScheduleReadOnlyInline` não permite adicionar (`has_add_permission` é `False`), `can_delete` é `False`, `extra == 0`, `show_change_link` é `True` e os campos são somente leitura; `ActivityAdmin.inlines` inclui os dois inlines na ordem; `upcoming_occurrences_display` devolve a mensagem de "Salve a atividade" sem `pk`, a de "não está publicada" para rascunho, cancelada e encerrada (sem chamar o serviço, `patch` do serviço verificado como não chamado), "Sem próximas ocorrências." com serviço mockado devolvendo vazio, a lista formatada com duas ocorrências mockadas e o link de adição com o `pk` da atividade (`reverse` mockado ou rota real do `admin.site`); a saída escapa HTML de títulos (não há títulos na saída; basta verificar `format_html` usado, conferindo a string)
- [X] T028 [P] [US4] Ampliar `tests/unit/schedules/test_schedule_admin.py` testando `format_weekdays` de `apps/schedules/services.py` (dias 2 e 4 → "Ter, Qui"; todos os sete dias; vazio → "—"; ordem independe da ordem de entrada)

**Checkpoint**: ocorrências calculadas e visíveis na atividade; `pytest` verde.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: documentação, verificação final e validação real contra o banco.

- [X] T029 [P] Atualizar `README.md` com a seção "Programações e ocorrências": tipos pontual e recorrente, dias da semana (1 = segunda a 7 = domingo), regra de meia-noite não suportada, cálculo de ocorrências sem armazenamento e fuso `America/Sao_Paulo`, e que o cadastro é feito em "Programações" ou pelo atalho na página da atividade
- [X] T030 Rodar `pytest` (cobertura total >= 90%) e `ruff check .`; corrigir qualquer falha ou aviso. Rodar `python manage.py makemigrations --check --dry-run` e confirmar que não há migrations pendentes
- [X] T031 Aplicar a migration no RDS com `python manage.py safe_migrate` e executar o roteiro manual de `specs/005-schedule-management/quickstart.md` (seção 3, passos 1 a 8) com uma conta do grupo "Administrador" e uma conta sem o grupo. Esta tarefa precisa do `.env` real e das credenciais do banco, e é executada pela pessoa responsável (não por testes automatizados)
- [X] T032 Marcar as tarefas concluídas neste arquivo e registrar no fim do `quickstart.md` o resultado da validação do T031

---

## Dependencies & Execution Order

- **Phase 1** (T001) antes de tudo.
- **Phase 2** bloqueia todas as histórias. Dentro dela: T002 → T003 → T004 (mesmo arquivo, em sequência) → T005 (migration); T006 e T007 em paralelo depois dos respectivos modelos.
- **US1** (T008 a T012) depende da Phase 2. É o MVP. T008 → T009 → T010 em sequência; T011 e T012 em paralelo.
- **US2** (T013 a T018) depende de US1 (`ScheduleAdminForm` e `ScheduleAdmin` existem). T013 → T014 no mesmo arquivo; T015 e T016 no mesmo arquivo, em sequência.
- **US3** (T019 a T021) depende de US2 (a edição converge os dias em `save_related`).
- **US4** (T022 a T028) depende só da Phase 2 para o serviço (T022, T023, T024 podem começar logo após a fase 2, em paralelo com US1 a US3); T025 a T028 dependem de T022/T023 e da `format_weekdays` (T016/T025).
- **Polish** (T029 a T032) depois das histórias; T031 depende de T030.

### Parallel opportunities

- Phase 2: T006 e T007 (testes) em paralelo, em arquivos diferentes.
- US1: T011 e T012 em paralelo.
- US2: T017 e T018 em paralelo.
- US3: T020 e T021 em paralelo.
- US4: o serviço (T022 a T024, arquivos `apps/schedules/services.py` e seu teste) em paralelo com US1 a US3, se houver mais de uma pessoa; T027 e T028 em paralelo.

## Implementation Strategy

1. **MVP**: Phase 1, Phase 2 e US1 — cadastrar programação pontual pelo Admin, com autoria e validações.
2. **Incremento 1**: US2 — recorrência com dias da semana sem duplicidade.
3. **Incremento 2**: US3 — edição segura, convergência dos dias e exclusão que preserva a atividade.
4. **Incremento 3**: US4 — próximas ocorrências na página da atividade (entrega o serviço que a API pública reaproveitará).
5. **Fechamento**: Polish, com validação real no RDS (T031).

Cada incremento termina com `pytest` e `ruff check .` verdes.
