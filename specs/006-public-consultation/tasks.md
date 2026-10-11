---

description: "Lista de tarefas de Consulta Pública de Atividades"
---

# Tasks: Consulta Pública de Atividades

**Input**: Documentos de design em `/specs/006-public-consultation/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Incluídos. A constituição (Princípio III) exige testes unitários com mocks, sem acesso a banco, e
cobertura total mínima de 90%. Nenhum teste pode abrir conexão com banco de dados: use objetos em memória
(`SimpleNamespace`, instâncias de modelo não salvas), `APIRequestFactory`, `unittest.mock` e relógio
injetado (`now=`). Montar querysets reais e executá-los NÃO é permitido; nas views, simule a função de
serviço que monta a lista e verifique os argumentos recebidos.

**Organization**: Tarefas agrupadas por história de usuário (US1 a US8 da spec), para permitir
implementação e validação independentes.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência de tarefa incompleta)
- **[Story]**: história de usuário à qual a tarefa pertence (US1 a US8)
- Os caminhos são relativos à raiz do repositório

## Path Conventions

Projeto único com o Django na raiz: `config/`, `apps/` (módulos por domínio) e `tests/unit/`. O novo app é
`apps/consultation` (sem modelos e sem migrations). `Activity` e `PUBLIC_STATUSES` ficam em
`apps/activities/models.py`; `Schedule`/`ScheduleWeekday` e o cálculo de ocorrências em `apps/schedules/`;
`Unit` em `apps/units/models.py`, `Category` em `apps/categories/models.py`, `TargetAudience` em
`apps/audiences/models.py`. `TIME_ZONE = "America/Sao_Paulo"` e `USE_TZ = True` já estão em
`config/settings.py`; o CORS já está configurado. Não há dependências novas. Mensagens de erro em
português. Os diretórios de teste existentes não têm `__init__.py`; seguir o padrão do repositório. Linha
de código com no máximo 100 caracteres (`ruff`).

Os arquivos `apps/consultation/services.py`, `serializers.py` e `views.py` crescem ao longo das histórias;
por isso as tarefas de histórias diferentes que os editam não são marcadas `[P]` entre si.

---

## Phase 1: Setup

**Purpose**: confirmar o ponto de partida

- [X] T001 Rodar `pytest` e `ruff check .` na raiz, na branch `006-public-consultation`, e confirmar que a suíte das features 001 a 005 passa com cobertura >= 90%, registrando o resultado como linha de base

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: extensão do serviço de ocorrências, app novo, formato de erro, paginação e view base. Bloqueia todas as histórias.

**⚠️ CRITICAL**: nenhuma história começa antes desta fase.

- [X] T002 (**substituída**: `iter_occurrences` ganhou `to_date` e `activity_occurrences` usa `islice`, sem função `first_occurrence` separada, que seria código morto) ~~Em `apps/schedules/services.py`, acrescentar `first_occurrence(schedule, weekdays, from_date, to_date=None)` conforme `contracts/occurrences-service.md`: `ONE_TIME` devolve `_occurrence(schedule, schedule.start_date)` se `from_date <= start_date` e (`to_date is None` ou `start_date <= to_date`); `RECURRING` usa início = `max(start_date, from_date)` e fim = `min(end_date, to_date)` (ou `end_date` se `to_date is None`), avança direto ao próximo dia cujo `isoweekday()` esteja em `weekdays` (no máximo 7 dias de avanço, sem laço dia a dia) e devolve `None` se passar do fim ou se `weekdays` estiver vazio. Não filtra pelo horário de hoje~~
- [X] T003 Em `apps/schedules/services.py`, acrescentar `activity_occurrences(activity, now=None, date_from=None, date_to=None, limit=None)`: devolve `[]` se `activity.status not in PUBLIC_STATUSES`; converte `now` (padrão `timezone.now()`) com `timezone.localtime`; início efetivo = `max(date_from, hoje)` (ou `hoje` se `date_from is None`); retorna `[]` se `date_to` não for `None` e `date_to < início efetivo`; chama `prefetch_related_objects([activity], "schedules__weekdays")` (importar de `django.db.models`) e itera `activity.schedules.all()` com `{item.weekday for item in schedule.weekdays.all()}`; para cada programação reúne as ocorrências da janela (usar `iter_occurrences` quando `limit` não for `None`, e `first_occurrence` não basta se `limit > 1`), descartando a de hoje cujo `end_time <= horário local atual`; ordena por (`date`, `start_time`) e corta em `limit`; `limit` não positivo (`limit is not None and limit < 1`) levanta `ValueError("limit deve ser positivo.")`. Para `limit=1` pode usar `first_occurrence` por programação e, se a de hoje já terminou, recalcular a partir de `hoje + 1 dia`
- [X] T004 Em `apps/schedules/services.py`, trocar `upcoming_occurrences(activity, now=None, limit=10)` por uma chamada a `activity_occurrences(activity, now=now, limit=limit)`, mantendo assinatura, validação `limit < 1` e resultados; estender `iter_occurrences` com parâmetro opcional `to_date=None` (para na menor entre `end_date` e `to_date`). Rodar `pytest tests/unit/schedules` e confirmar que os testes da feature 005 continuam passando sem alteração
- [X] T005 [P] Em `tests/unit/schedules/test_occurrences_service.py`, acrescentar testes dos casos de referência da tabela de `contracts/occurrences-service.md`: `first_occurrence` (recorrente salta ao próximo dia válido; janela em quinta devolve quinta; janela em quarta devolve `None`; janela fora do período devolve `None`; `weekdays` vazio devolve `None`; pontual dentro e fora da janela) e `activity_occurrences` (janela aberta e fechada; janela no passado vazia; ocorrência de hoje já terminada descartada; `limit`; `limit=0` levanta `ValueError`; atividade `DRAFT`/`CANCELLED`/`FINISHED` vazia; uso de dados pré-carregados com `prefetch_related_objects` simulado via `unittest.mock.patch`). Incluir um teste que garante que `upcoming_occurrences` e `activity_occurrences` com janela aberta devolvem o mesmo resultado (FR-018)
- [X] T006 Criar o app `apps/consultation/` com `__init__.py` e `apps.py` (`ConsultationConfig`, `name = "apps.consultation"`, `default_auto_field` conforme os outros apps); registrar `"apps.consultation"` em `INSTALLED_APPS` de `config/settings.py` e na lista de módulos de `tests/unit/config/test_structure.py`
- [X] T007 [P] Criar `apps/core/exceptions.py` com `public_exception_handler(exc, context)`: chama `rest_framework.views.exception_handler`; se a resposta for `None`, devolve `None` (500 do Django); caso contrário reescreve `response.data` para `{"detail": "<mensagem>"}`, sendo: para `ValidationError` (400) `{"detail": "Parâmetros inválidos.", "errors": {campo: [mensagens, ...]}}` (aceitando `dict` de listas, `list` e texto); para `NotFound`/`Http404` `{"detail": "Não encontrado."}`; para `MethodNotAllowed` `{"detail": "Método não permitido."}`; demais exceções do DRF mantêm `str(exc.detail)` como `detail`. Registrar em `config/settings.py`: `REST_FRAMEWORK["EXCEPTION_HANDLER"] = "apps.core.exceptions.public_exception_handler"`
- [X] T008 [P] Criar `tests/unit/core/test_exceptions.py` testando o handler: `ValidationError` com dict de campos, com lista e com texto; `NotFound` e `Http404` viram "Não encontrado." sem vazar o texto original; `MethodNotAllowed`; `Throttled`/`PermissionDenied` mantêm `detail` como texto; exceção que não é do DRF devolve `None`; `errors` só aparece em 400; o corpo nunca contém `traceback`
- [X] T009 [P] Criar `apps/consultation/pagination.py` com `PublicPagination(PageNumberPagination)`: `page_size = 12`, `page_size_query_param = "page_size"`, `max_page_size = 50`. Criar `tests/unit/consultation/test_pagination.py` testando: padrão 12, `page_size=500` limitado a 50, `page_size=0`, `page_size=-3` e `page_size=abc` usam 12, página 2 de uma lista simples de 30 itens com `count`, `next` e `previous` corretos, página 99 levanta `NotFound`, lista vazia devolve `count: 0` e `results: []`
- [X] T010 Criar `apps/consultation/views.py` com `PublicAPIView(APIView)`: `authentication_classes = []`, `permission_classes = [AllowAny]`, `http_method_names = ["get", "head", "options"]`, `pagination_class = PublicPagination` e o método auxiliar `paginate(self, request, items, serializer_class, context=None)` que devolve `Response` paginada (instancia o paginador, `paginate_queryset` sobre a lista, serializa só a página, `get_paginated_response`)
- [X] T011 Criar `apps/consultation/urls.py` com `urlpatterns = []` (preenchida pelas histórias) e incluir em `config/urls.py` com `path("api/v1/", include("apps.consultation.urls"))`, depois da inclusão de `apps.core.urls`. Criar `tests/unit/consultation/test_views.py` com um teste base: `PublicAPIView` rejeita `POST`, `PUT`, `PATCH` e `DELETE` com 405 e corpo `{"detail": "Método não permitido."}`, e ignora um cabeçalho `Authorization` inválido (resposta 200 numa view de teste mínima)

**Checkpoint**: `pytest` verde; `PublicAPIView`, paginação, handler de erros e serviço de ocorrências estendido prontos.

---

## Phase 3: User Story 1 - Listar atividades publicadas (Priority: P1) 🎯 MVP

**Goal**: `GET /api/v1/activities/` devolve as atividades `PUBLISHED`, com dados resumidos, próxima ocorrência, ordem definida e paginação, sem autenticação e sem dados administrativos.

**Independent Test**: com atividades em rascunho, publicadas, canceladas e encerradas, a listagem traz só as publicadas, as com ocorrência primeiro (mais cedo antes), as sem ocorrência ao final por título, paginadas e sem campos de auditoria.

- [X] T012 [US1] Em `apps/consultation/services.py`, criar `normalize_text(value)` (NFKD com `unicodedata`, remove marcas combinantes, `casefold()`, `strip()`; `None` vira `""`) e `reference_occurrence(activity, now, date_from=None, date_to=None)` que devolve `(activity_occurrences(activity, now=now, date_from=date_from, date_to=date_to, limit=1) or [None])[0]`
- [X] T013 [US1] Em `apps/consultation/services.py`, criar `sort_key(item)` e `build_listing(activities, now, date_from=None, date_to=None)` que recebe um iterável de atividades já filtradas e devolve a lista de pares `(activity, occurrence)` ordenada por: atividades com ocorrência primeiro (`occurrence is None` por último), depois `occurrence.date`, `occurrence.start_time` e `normalize_text(activity.title)`; as sem ocorrência ordenam só por `normalize_text(activity.title)`. Criar também `published_activities()` que devolve `Activity.objects.filter(status__in=PUBLIC_STATUSES).select_related("unit", "category").prefetch_related("schedules__weekdays")` (importar `Activity` e `PUBLIC_STATUSES` de `apps.activities.models`)
- [X] T014 [P] [US1] Em `apps/consultation/serializers.py`, criar `UnitSummarySerializer` (`id`, `name`, `slug`, `neighborhood`), `CategorySummarySerializer` (`id`, `name`, `slug`), `OccurrenceSerializer` (serializer simples com `date` = `DateField()`, `start_time` e `end_time` = `TimeField(format="%H:%M")`, lendo o `Occurrence` do serviço) e `ActivityListItemSerializer` (`id`, `title`, `slug`, `summary`, `unit`, `category`, `next_occurrence`), onde cada elemento recebido é o par `(activity, occurrence)` (usar `to_representation` explícito ou `SerializerMethodField` sobre um objeto `SimpleNamespace(activity, occurrence)`); `next_occurrence` é `None` quando não há ocorrência. Nenhum campo de auditoria (`created_by`, `updated_by`, `created_at`, `updated_at`, `status`)
- [X] T015 [US1] Em `apps/consultation/views.py`, criar `ActivityListView(PublicAPIView)` com `get(self, request)` que chama `build_listing(published_activities(), timezone.now())` e responde com `self.paginate(request, items, ActivityListItemSerializer)`. Registrar em `apps/consultation/urls.py` `path("activities/", ActivityListView.as_view(), name="activity-list")`
- [X] T016 [P] [US1] Criar `tests/unit/consultation/test_services.py` testando com objetos em memória: `normalize_text` ("Dança" == "danca", "  Ação " vira "acao", `None` vira vazio); `build_listing` ordena por data, depois horário, depois título (desempate estável), coloca as sem ocorrência ao final em ordem alfabética sem acento, aceita lista vazia, e passa `date_from`/`date_to` para `activity_occurrences` (simulado com `unittest.mock.patch`); `reference_occurrence` devolve `None` sem ocorrência
- [X] T017 [P] [US1] Criar `tests/unit/consultation/test_serializers.py` testando `ActivityListItemSerializer`: campos exatos do item de `contracts/public-api.md`; horários `HH:MM`; `next_occurrence` `null` sem ocorrência; nenhum campo de auditoria nem de conta na saída (comparar o conjunto de chaves, incluindo `unit` e `category`)
- [X] T018 [US1] Em `tests/unit/consultation/test_views.py`, testar `ActivityListView` com `APIRequestFactory`, `published_activities` e `build_listing` simulados: 200 anônimo; envelope `count`/`next`/`previous`/`results` com 12 por página; `page_size=1` e `page=2`; `page_size=500` limitado a 50; página inexistente devolve 404 `{"detail": "Não encontrado."}`; lista vazia devolve 200 com `count: 0`; `POST` devolve 405; cabeçalho `Authorization` inválido não altera o resultado. Em `tests/unit/consultation/test_views.py` ou `tests/unit/config/test_cors.py`, acrescentar teste de CORS: a listagem com `Origin` autorizado recebe `Access-Control-Allow-Origin` (FR-020)

**Checkpoint**: US1 independente e testável (MVP). `pytest` verde.

---

## Phase 4: User Story 2 - Consultar detalhes de uma atividade (Priority: P1)

**Goal**: `GET /api/v1/activities/{id}/` devolve o detalhe completo de uma atividade publicada; qualquer outro caso é o mesmo 404.

**Independent Test**: detalhe de publicada com programações pontual e recorrente, públicos e link mostra o conteúdo do contrato; rascunho, cancelada, encerrada, UUID inexistente e malformado dão o mesmo 404.

- [X] T019 [P] [US2] Em `apps/consultation/serializers.py`, criar `UnitDetailSerializer` (`id`, `name`, `slug`, `address`, `neighborhood`), `AudienceSerializer` (`id`, `name`), `ScheduleSerializer` (`id`, `schedule_type`, `start_date`, `end_date`, `start_time`, `end_time` com `format="%H:%M"`, `weekdays` = lista ordenada de inteiros 1 a 7 e `weekday_names` = nomes por extenso de `ScheduleWeekday.Weekday(...).label`; ambas listas vazias para `ONE_TIME`, lendo `schedule.weekdays.all()` sem nova consulta) e `ActivityDetailSerializer` (`id`, `title`, `slug`, `summary`, `description`, `target_audience_notes`, `unit`, `category`, `target_audiences` via `activity.target_audiences.all()`, `external_registration_url` provisório igual ao campo do modelo, `schedules` ordenadas por `start_date` e `next_occurrences` vindo do contexto ou de `activity_occurrences(activity, limit=5)`)
- [X] T020 [US2] Em `apps/consultation/views.py`, criar `ActivityDetailView(PublicAPIView)` com `get(self, request, pk)`: tenta `uuid.UUID(pk)` e levanta `NotFound` se falhar; busca com `published_activities().prefetch_related("target_audiences").filter(pk=...).first()` (nunca `get_object_or_404`, para o 404 sair do handler) e levanta `NotFound` se não existir; responde `Response(ActivityDetailSerializer(activity).data)`. Registrar `path("activities/<str:pk>/", ActivityDetailView.as_view(), name="activity-detail")` em `apps/consultation/urls.py` depois da rota da listagem
- [X] T021 [P] [US2] Em `tests/unit/consultation/test_serializers.py`, testar `ActivityDetailSerializer`/`ScheduleSerializer`: chaves exatas do contrato; `weekday_names` por extenso na ordem dos dias ("Terça-feira", "Quinta-feira"); pontual com `weekdays` e `weekday_names` vazios; `schedules` ordenadas por `start_date`; `next_occurrences` limitada a 5 e vazia sem datas futuras; nenhum campo de auditoria; unidade e categoria exibidas mesmo quando `is_active` é falso
- [X] T022 [US2] Em `tests/unit/consultation/test_views.py`, testar `ActivityDetailView` (consulta simulada): 200 para atividade publicada; o mesmo corpo e status 404 `{"detail": "Não encontrado."}` quando a consulta devolve `None` (rascunho/cancelada/encerrada/inexistente, já que o filtro é `PUBLIC_STATUSES`) e quando o `pk` é `abc` ou `123`; verificar que a consulta é feita sempre a partir de `published_activities()`; `POST` devolve 405

**Checkpoint**: US1 e US2 funcionam. `pytest` verde.

---

## Phase 5: User Story 3 - Apoios de consulta: unidades e categorias (Priority: P1)

**Goal**: `GET /api/v1/units/` e `GET /api/v1/categories/` devolvem só os registros ativos, em ordem alfabética, paginados.

**Independent Test**: com ativos e inativos, as listas só trazem os ativos, ordenados por nome, sem campos administrativos.

- [X] T023 [P] [US3] Em `apps/consultation/serializers.py`, criar `UnitItemSerializer` (`id`, `name`, `slug`, `neighborhood`, `address`, `description`) e `CategoryItemSerializer` (`id`, `name`, `slug`, `description`), ambos com `description` vazio devolvido como `null` (`to_representation` ou `SerializerMethodField`) e `address` vazio como `null`
- [X] T024 [US3] Em `apps/consultation/views.py`, criar `UnitListView` (queryset `Unit.objects.filter(is_active=True).order_by("name")`) e `CategoryListView` (`Category.objects.filter(is_active=True).order_by("name")`), ambos `PublicAPIView` usando `self.paginate(...)` com `UnitItemSerializer`/`CategoryItemSerializer`. Registrar `path("units/", ..., name="unit-list")` e `path("categories/", ..., name="category-list")` em `apps/consultation/urls.py`. Não criar rotas de detalhe
- [X] T025 [P] [US3] Em `tests/unit/consultation/test_serializers.py`, testar os dois serializers: chaves exatas, `description` e `address` vazios viram `null`, nenhum campo `is_active`, `created_at` ou `updated_at`
- [X] T026 [US3] Em `tests/unit/consultation/test_views.py`, testar `UnitListView` e `CategoryListView` com o queryset simulado: filtro `is_active=True` e ordem por nome aplicados (verificar chamadas no mock), envelope paginado, lista vazia, 405 para escrita, e que `/api/v1/units/<id>/` e `/api/v1/categories/<id>/` não existem (404)

**Checkpoint**: US1 a US3 funcionam; o frontend já consegue montar as opções de filtro.

---

## Phase 6: User Story 4 - Buscar por palavra-chave (Priority: P2)

**Goal**: o parâmetro `q` filtra a listagem por título, resumo e descrição, sem caixa e sem acento; vazio é ignorado; mais de 100 caracteres é 400.

**Independent Test**: termos presentes em título, resumo e descrição retornam só publicadas; "danca" acha "dança"; termo vazio devolve a lista geral; termo longo demais devolve 400 com `errors.q`.

- [X] T027 [US4] Em `apps/consultation/serializers.py`, criar `ConsultationQuerySerializer(serializers.Serializer)` com `q = CharField(required=False, allow_blank=True, max_length=100, trim_whitespace=True)` e mensagens em português ("Informe no máximo 100 caracteres."); método `criteria()` que devolve um `SimpleNamespace`/dataclass `Criteria` com `q` (ou `None` quando vazio) e os demais campos ainda como `None`. Parâmetros desconhecidos são ignorados
- [X] T028 [US4] Em `apps/consultation/services.py`, criar `matches_search(activity, term)` (verdadeiro se o termo normalizado estiver contido em `normalize_text(title)`, `normalize_text(summary)` ou `normalize_text(description)`; termo `None` ou vazio é sempre verdadeiro) e `apply_criteria(activities, criteria)` que aplica os filtros da `Criteria` em sequência (por enquanto só `q`) e devolve a lista filtrada. Em `ActivityListView.get`, validar `ConsultationQuerySerializer(data=request.query_params)` com `is_valid(raise_exception=True)` e usar `build_listing(apply_criteria(published_activities(), criteria), now)`
- [X] T029 [P] [US4] Em `tests/unit/consultation/test_services.py`, testar `matches_search`: termo no título, no resumo e na descrição; "danca" encontra "Oficina de dança"; "DANÇA" encontra "danca"; termo ausente em todos os campos; termo `None`, vazio e só espaços; caracteres especiais (`%`, `'`, `"`, `;`, `\`) tratados como texto; e `apply_criteria` com `q`
- [X] T030 [P] [US4] Em `tests/unit/consultation/test_serializers.py` e `tests/unit/consultation/test_views.py`, testar `ConsultationQuerySerializer` e a view: `q` vazio ou só espaços vira `None` e a view devolve a lista geral; `q` com 100 caracteres é aceito e com 101 devolve 400 `{"detail": "Parâmetros inválidos.", "errors": {"q": [...]}}`; `q` com acento e maiúsculas chega normalizado à busca; resultado sem correspondência devolve 200 com `count: 0`

**Checkpoint**: busca por palavra-chave funcionando sobre a listagem.

---

## Phase 7: User Story 5 - Filtrar por unidade, bairro e categoria (Priority: P2)

**Goal**: `unit`, `neighborhood` e `category` filtram a listagem; UUID malformado é 400; inexistente é lista vazia.

**Independent Test**: com atividades em duas unidades, bairros e categorias, cada filtro isolado devolve só as correspondentes publicadas; remover o filtro volta à lista geral.

- [X] T031 [US5] Em `ConsultationQuerySerializer` (`apps/consultation/serializers.py`), acrescentar `unit = UUIDField(required=False)`, `category = UUIDField(required=False)` (mensagem "Informe um identificador válido.") e `neighborhood = CharField(required=False, allow_blank=True, max_length=100, trim_whitespace=True)` (vazio vira `None`); incluir os três na `Criteria`
- [X] T032 [US5] Em `apps/consultation/services.py`, estender `published_activities(criteria=None)` para aplicar `.filter(unit_id=criteria.unit)` e `.filter(category_id=criteria.category)` quando informados (filtros de igualdade no banco, cobertos pelos índices existentes), e `apply_criteria` para filtrar por bairro em Python: `normalize_text(activity.unit.neighborhood) == normalize_text(criteria.neighborhood)`. Ajustar `ActivityListView.get` para passar `criteria` a `published_activities`
- [X] T033 [P] [US5] Em `tests/unit/consultation/test_services.py`, testar o filtro de bairro ("grajau" == "Grajaú", bairro diferente exclui, ausente não filtra) e que `published_activities(criteria)` encadeia `filter(unit_id=...)` e `filter(category_id=...)` (verificar com `unittest.mock.patch` em `Activity.objects`, sem executar consulta)
- [X] T034 [P] [US5] Em `tests/unit/consultation/test_serializers.py` e `tests/unit/consultation/test_views.py`, testar: `unit=abc` e `category=abc` devolvem 400 com `errors.unit`/`errors.category`; UUID válido é repassado à consulta; `neighborhood` vazio é ignorado e acima de 100 caracteres devolve 400; filtros isolados e sem filtro devolvem a lista geral; resultado vazio é 200

**Checkpoint**: filtros por lugar e interesse funcionando.

---

## Phase 8: User Story 6 - Filtrar por data ou período (Priority: P2)

**Goal**: `date`, `date_from` e `date_to` filtram por ocorrências reais; a ordem e o `next_occurrence` usam a primeira ocorrência na janela.

**Independent Test**: pontual em 20/11, recorrente às terças e quintas de 01/11 a 31/12 e uma com período sem o dia da semana escolhido: filtro por dia e por intervalo devolve exatamente as correspondentes; datas inválidas devolvem 400; dia passado devolve lista vazia.

- [X] T035 [US6] Em `ConsultationQuerySerializer`, acrescentar `date`, `date_from` e `date_to` (`DateField(required=False)`, formato `YYYY-MM-DD`, mensagem "Informe uma data no formato AAAA-MM-DD.") e um `validate()` que: rejeita `date` junto com `date_from` ou `date_to` ("Use `date` ou `date_from`/`date_to`, não os dois."), rejeita `date_from > date_to` ("A data inicial não pode ser posterior à data final.") e, com os dois informados, rejeita intervalo superior a 366 dias ("O intervalo máximo é de 366 dias."). `criteria()` converte `date` em `date_from = date_to = date`
- [X] T036 [US6] Em `apps/consultation/services.py`, fazer `build_listing` descartar atividades sem ocorrência quando `date_from` ou `date_to` forem informados (filtro de data ativo), e em `ActivityListView.get` passar `criteria.date_from`/`criteria.date_to` a `build_listing`. Janela inteira no passado já resulta em lista vazia por `activity_occurrences` (US6, cenário 7)
- [X] T037 [P] [US6] Em `tests/unit/consultation/test_serializers.py`, testar as regras de data: `date` válido vira janela de um dia; `date` com `date_from` ou `date_to` é 400; `date_from > date_to` é 400; intervalo de 366 dias aceito e de 367 recusado; `date_from` sozinho e `date_to` sozinho aceitos; formato `2026-13-40` e `20/11/2026` recusados com a mensagem de formato; mensagens em `errors` do campo correto
- [X] T038 [P] [US6] Em `tests/unit/consultation/test_services.py`, testar `build_listing` com filtro de data usando atividades em memória e relógio injetado (programações e `weekdays` como `SimpleNamespace`): pontual na data pedida entra e em outra data não; recorrente (terças e quintas, 01/11 a 31/12) entra numa terça dentro do período e fica fora numa quarta ou fora do período; intervalo com extremos inclusivos; ocorrência de hoje já terminada não conta; dia no passado devolve vazio; `next_occurrence` é a primeira dentro da janela; ordem segue essa data; sem filtro de data, atividades sem ocorrência continuam na lista (ao final)
- [X] T039 [P] [US6] Em `tests/unit/consultation/test_views.py`, testar que a view repassa `date_from`/`date_to` calculados a partir de `date`, de `date_from`/`date_to` e de `date_from` sozinho, e que combinações inválidas devolvem 400 sem chamar o serviço de listagem

**Checkpoint**: filtro por data funcionando e coerente com o cálculo da administração.

---

## Phase 9: User Story 7 - Combinar filtros e busca (Priority: P3)

**Goal**: busca e todos os filtros combinam em "E"; remover critérios amplia o resultado; páginas ficam consistentes.

**Independent Test**: `q` + `unit` + `category` + `date` devolvem só atividades que satisfazem todos; remover um critério nunca reduz o resultado; páginas mantêm total e ordem.

- [X] T040 [US7] Em `tests/unit/consultation/test_services.py`, testar `apply_criteria` + `build_listing` combinados (atividades em memória): todas as combinações de `q`, bairro e data; combinação sem correspondência devolve lista vazia; remover um critério produz um conjunto igual ou maior (propriedade verificada com pelo menos 4 critérios); atividades não `PUBLISHED` nunca entram mesmo que a lista de entrada as contenha (usar `activity_occurrences` real para garantir que `DRAFT`/`CANCELLED`/`FINISHED` ficam sem ocorrência e fora de qualquer filtro de data)
- [X] T041 [US7] Em `tests/unit/consultation/test_views.py`, testar `ActivityListView` com todos os parâmetros ao mesmo tempo (`q`, `unit`, `neighborhood`, `category`, `date_from`, `date_to`, `page`, `page_size`): os critérios chegam completos ao serviço; `count` e a ordem se mantêm entre as páginas 1 e 2 para a mesma consulta; parâmetros desconhecidos (`foo=1`) são ignorados. Corrigir qualquer ordem de aplicação em `apply_criteria` que torne o resultado dependente da ordem dos parâmetros

**Checkpoint**: filtros combináveis; sem código novo esperado além de ajustes encontrados pelos testes.

---

## Phase 10: User Story 8 - Abrir o link externo de uma atividade (Priority: P3)

**Goal**: o detalhe entrega o link externo só quando for `http`/`https`; senão `null`.

**Independent Test**: detalhe com link válido, sem link e com valor sem `http(s)` entrega o link só no primeiro caso.

- [X] T042 [US8] Em `apps/consultation/serializers.py`, trocar o campo provisório de `ActivityDetailSerializer.external_registration_url` por um `SerializerMethodField` (ou `to_representation`) que devolve o valor com `strip()` se `urlparse(valor).scheme in ("http", "https")` e `netloc` não vazio, e `None` caso contrário (vazio, `javascript:`, `ftp://`, `//exemplo.org`, texto solto)
- [X] T043 [P] [US8] Em `tests/unit/consultation/test_serializers.py`, testar o link externo: `https://exemplo.org/inscricao` e `http://exemplo.org` são entregues; vazio, só espaços, `javascript:alert(1)`, `ftp://exemplo.org`, `exemplo.org` e `//exemplo.org` viram `null`; a chave está sempre presente

**Checkpoint**: todas as histórias implementadas.

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: documentação, verificação final e fechamento

- [X] T044 [P] Em `README.md`, acrescentar a seção "API pública de consulta": rotas, parâmetros (`q`, `unit`, `neighborhood`, `category`, `date`, `date_from`, `date_to`, `page`, `page_size`), limites (12/50 por página, 100 caracteres de busca, 366 dias), formato de erro e um exemplo de `curl`, apontando para `specs/006-public-consultation/contracts/public-api.md`
- [X] T045 [P] Em `tests/unit/consultation/test_views.py`, acrescentar um teste de não vazamento: percorrer as respostas simuladas da listagem, do detalhe e das listas de apoio e afirmar que nenhuma chave nem valor serializado contém `created_by`, `updated_by`, `created_at`, `updated_at`, `status` ou `is_active` (SC-003)
- [X] T046 Rodar `pytest` e `ruff check .` e corrigir o que falhar; confirmar cobertura total >= 90% e que `apps/consultation` e as novas funções de `apps/schedules/services.py` estão cobertas; rodar `python manage.py makemigrations --check --dry-run` e confirmar que não há migrations pendentes
- [X] T047 Executar o roteiro de `quickstart.md` (seções 2 e 3) contra o servidor local com dados reais do Admin, conferindo cada linha da tabela de requisições, e a seção 4 (desempenho, número de consultas por requisição), e preencher a seção "Resultado da validação automatizada" do `quickstart.md` com a data, o total de testes e a cobertura

---

## Dependencies & Execution Order

- **Phase 1** → **Phase 2** (bloqueia tudo) → histórias.
- **US1** (listagem) é pré-requisito de US4, US5, US6 e US7, pois estendem a mesma view e o mesmo serviço.
- **US2** (detalhe) e **US3** (unidades/categorias) dependem só da Phase 2 e são independentes entre si e de US1; **US8** estende o serializer de US2 (depois de T019).
- **US4 → US5 → US6** estendem `ConsultationQuerySerializer` e `apply_criteria`; fazer em sequência para evitar conflitos. **US7** depois de US4 a US6.
- **Phase 11** por último.

Ordem sugerida de entrega: US1 (MVP) → US2 → US3 → US4 → US5 → US6 → US7 → US8.

### Dentro da Phase 2

T002 → T003 → T004 (mesmo arquivo). T005 depende de T002–T004. T006 antes de T010/T011. T007, T008 e T009 são independentes entre si (`[P]`). T010 depende de T009; T011 depende de T006 e T010.

## Parallel Example: após a Phase 2

```text
Desenvolvedor A: T012–T018 (US1), depois T027–T043 (US4 a US8, em sequência)
Desenvolvedor B: T019–T022 (US2) e T023–T026 (US3), em paralelo com A
```

Dentro de uma história, as tarefas `[P]` (por exemplo T014, T016 e T017 em US1) editam arquivos diferentes
ou trechos independentes de testes e podem ser feitas ao mesmo tempo.

## Implementation Strategy

- **MVP**: Phase 1 + Phase 2 + US1. A listagem pública já entrega valor ao frontend.
- **Incremento 2**: US2 e US3 (detalhe e opções de filtro) completam o fluxo mínimo de descoberta.
- **Incremento 3**: US4 a US6 (busca e filtros), em sequência.
- **Fechamento**: US7 (verificação de combinações), US8 (link externo) e Polish.
- Fazer commits pequenos por história, com a suíte verde (`pytest` e `ruff check .`) antes de cada um.
