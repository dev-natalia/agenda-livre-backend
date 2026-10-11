# Research: Qualidade, Segurança e Acessibilidade

Resultado da leitura do código existente (features 002 a 006) contra os FR da spec. Não restou nenhum
`NEEDS CLARIFICATION`.

## Estado atual por requisito

| FR | Estado hoje | Ação |
|---|---|---|
| FR-001 | Views públicas: `authentication_classes = []`, `AllowAny`, `http_method_names = [get, head, options]`. `HealthView` só define `get`. | Teste de regressão |
| FR-002/003 | Serializers públicos listam campos explicitamente (sem `created_by`/`updated_by`); `published_activities()` filtra `PUBLIC_STATUSES`; detalhe não publicado → `NotFound`. | Teste de varredura de campos proibidos |
| FR-004 a 006 | `Activity.clean`, `Schedule.clean`, `ScheduleAdminForm`/`WeekdaysFormMixin`, `ActivityTargetAudienceFormSet`, `validate_publication` e `change_status`. Check constraints no banco. | Matriz de testes por categoria de entrada inválida |
| FR-007 | `Activity.clean` recusa esquema fora de `http/https`; o serializer público ainda devolve `None` para URL fora disso. | Teste de regressão |
| FR-008 | `ConsultationQuerySerializer` valida datas, UUIDs, tamanhos e intervalo. **Parâmetros desconhecidos são ignorados** (decisão da 006). | Teste; spec ajustada |
| FR-009 | `public_exception_handler` cobre `ValidationError`, `NotFound`, `MethodNotAllowed` e o resto com `detail`. | Manter e testar |
| FR-010 | **Lacuna.** Para exceções que não são da DRF, `exception_handler` devolve `None` e o Django responde 500 em HTML (com pilha se `DEBUG=True`). | Corrigir |
| FR-010 (404) | **Lacuna.** Rota inexistente sob `/api/` devolve a página 404 do Django. | `handler404` JSON em `/api/` |
| FR-011 | Mensagens já em português. **Lacuna**: `?page=abc` vira "Não encontrado." (a DRF levanta `NotFound`). | Pagination → `ValidationError` em `page` |
| FR-012 | Serializers expõem `schedule_type` como código e `weekday_names`/`name` textuais; datas ISO, horas `HH:MM`. Situação não aparece (só `PUBLISHED`). | Documentar no contrato; teste dos campos textuais |
| FR-013 a 016 | `created_by`/`updated_by` (FK `PROTECT`, `editable=False`), `created_at` (`auto_now_add`), `updated_at` (`auto_now`). Gravados em `save_model`, `save_formset`, `ScheduleAdmin.save_model` e `change_status`. Campos `readonly` na administração. Nenhum caminho de escrita sem autoria encontrado. | Teste por caminho |
| FR-017 | `on_delete=PROTECT` impede remover autor. Política escrita ainda não existe. | Documentar e testar por introspecção |
| FR-018 | Não há `LOGGING` próprio; o log padrão do Django registra 5xx com pilha só no servidor. | Registrar erro com tipo e caminho; sem corpo, sem parâmetros, sem cabeçalhos |
| FR-020 | Não há documento. | Contrato de acessibilidade |

## Decisões

### D1. Resposta 500 genérica dentro do handler da DRF
- **Decision**: `public_exception_handler` trata qualquer `Exception` não prevista: registra com
  `logger.exception("Erro inesperado em %s %s", método, caminho)` e devolve
  `{"detail": "Ocorreu um erro inesperado. Tente novamente mais tarde."}` com status 500.
- **Rationale**: é o ponto único por onde passam todas as views DRF; funciona igual com
  `DEBUG=True` e `False`, porque a DRF só relança quando o handler devolve `None`.
- **Alternatives**: middleware de captura (mais código, duplica o handler); confiar em `DEBUG=False`
  (a spec exige independência do ambiente).

### D2. `handler404`/`handler500` restritos a `/api/`
- **Decision**: funções em `apps/core/error_views.py` que respondem JSON se o caminho começa com
  `/api/` e delegam a `django.views.defaults.page_not_found` / `server_error` nos demais casos.
- **Rationale**: cobre falhas fora de views DRF sem mudar o `/admin/`. Com `DEBUG=True` o Django
  mostra a página técnica de 404 antes de consultar `handler404`; por isso `config/urls.py` ganhou
  uma rota coringa `^api/` (`api_not_found`) ao final, que mantém o JSON em qualquer ambiente.
- **Alternatives**: JSON para o site todo (quebra as páginas do Admin); não tratar (deixa HTML na API).

### D3. Página inválida como erro de validação
- **Decision**: `PublicPagination.paginate_queryset` captura o `NotFound` da DRF e levanta
  `ValidationError({"page": ["Informe uma página válida."]})`. HTTP 400 com `errors.page`.
- **Rationale**: o frontend associa o erro ao campo e a mensagem diz o que corrigir. Vale também
  para página além da última.
- **Alternatives**: manter 404 (mensagem sem ação); renderizar página vazia (esconde erro de cliente).
- **Impacto**: muda o contrato da 006 de "404 Não encontrado" para "400 com `errors.page`" apenas
  em paginação inválida; os testes da 006 que cobrem isso são atualizados.

### D4. Parâmetros desconhecidos continuam ignorados
- **Decision**: manter a decisão da 006 e registrá-la no contrato de erros.
- **Rationale**: o frontend pode acrescentar parâmetros sem quebrar; recusar seria mudança de escopo.

### D5. Política de autoria
- **Decision**: manter `PROTECT`; contas que saem da equipe são desativadas (`is_active=False`), nunca
  removidas. Não há rotinas automáticas que alterem atividade ou programação; qualquer rotina futura
  deve receber um usuário-ator explícito antes de entrar. Fecha a pendência de `PENDENCIAS.md`.
- **Rationale**: nenhuma migration, nenhuma coluna anulável, nenhuma autoria órfã.
- **Alternatives**: `SET_NULL` com autor anônimo (perde rastreabilidade e exige migration).

### D6. Estratégia de teste da privacidade pública
- **Decision**: um teste de varredura percorre todas as respostas públicas geradas com objetos
  simulados e falha se qualquer chave, em qualquer profundidade, estiver em
  `{created_by, updated_by, created_at, updated_at, status, password, secret, is_staff, is_superuser, email, username}`.
  Outro teste percorre as rotas de `apps.consultation.urls` e `apps.core.urls` e exige 405 para
  `POST/PUT/PATCH/DELETE`.
- **Rationale**: pega vazamento em campo novo de serializer futuro, sem repetir testes por endpoint.

### D7. Acessibilidade é entrega do frontend
- **Decision**: o backend garante dados textuais, erros por campo e formato estável; a verificação
  WCAG 2.2 AA (rótulos, teclado, foco, contraste) fica registrada como responsabilidade do frontend em
  [contracts/accessibility-handoff.md](contracts/accessibility-handoff.md).
- **Rationale**: a interface está em outro repositório; a meta ainda será confirmada (DOC-06).

## Fora do escopo desta feature

- Limitação de taxa, cache e CAPTCHA (YAGNI).
- Imagens e texto alternativo (imagens fora da primeira versão).
- Auditoria de unidades e categorias (o backlog pede só atividades e programações).
- `LOGGING` estruturado ou envio de logs para serviço externo (execução local).
