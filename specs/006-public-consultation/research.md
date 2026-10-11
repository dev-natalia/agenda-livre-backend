# Research: Consulta Pública de Atividades

Não havia itens "NEEDS CLARIFICATION" no Technical Context. As decisões abaixo resolvem as escolhas de
desenho que a spec deixou para o plano.

## 1. Busca e bairro sem acento e sem caixa

- **Decision**: o banco filtra apenas por situação `PUBLISHED`, unidade e categoria (igualdade). A
  busca por palavra-chave (título, resumo, descrição) e o filtro de bairro comparam textos
  normalizados em Python: `unicodedata.normalize("NFKD")`, remoção de marcas combinantes e
  `casefold()`. Busca por substring no texto normalizado.
- **Rationale**: "danca" deve achar "dança" (spec, US4/US5). No PostgreSQL isso exige a extensão
  `unaccent` (`CREATE EXTENSION` no RDS, permissões e migration), e os testes não podem usar banco
  (constituição III). Com no máximo algumas centenas de atividades publicadas em instância local, ler
  o conjunto filtrado e comparar em memória é suficiente e totalmente testável.
- **Alternatives considered**: `unaccent` + `icontains` (melhor em escala, mas exige extensão e
  dependência de banco nos testes); `SearchVector` do PostgreSQL (busca por radicais, fora do
  escopo); `icontains` simples (falha em acentos, viola a spec).

## 2. Ordenação e paginação em memória

- **Decision**: depois de filtrar, calcula-se para cada atividade a ocorrência de referência (a
  próxima, ou a primeira dentro da janela de datas) e ordena-se por (`tem ocorrência`, data, horário
  de início, título normalizado). A lista ordenada é paginada com o `PageNumberPagination` do DRF
  (funciona sobre listas). Só a página pedida é serializada.
- **Rationale**: a ordem depende de datas calculadas (recorrência), que não existem como coluna; fazê-la
  no banco exigiria materializar ocorrências, o que a spec e o DOC-05 descartam. A ordem estável por
  título garante páginas consistentes (spec, edge cases).
- **Alternatives considered**: tabela/coluna de próxima ocorrência desnormalizada (precisa ser
  recalculada com o passar do tempo, e foge de YAGNI); ordenar no SQL com `generate_series` (SQL cru,
  não testável sem banco).

## 3. Reuso do cálculo de ocorrências

- **Decision**: estender `apps/schedules/services.py`, sem mudar o comportamento existente:
  - `first_occurrence(schedule, weekdays, from_date, to_date=None)`: primeira ocorrência na janela,
    saltando direto ao próximo dia da semana válido (no máximo 7 passos).
  - `activity_occurrences(activity, now=None, date_from=None, date_to=None, limit=None)`: ocorrências
    ainda não encerradas na janela, em ordem; usa `prefetch_related_objects` para não repetir consultas
    quando a atividade já veio com `schedules__weekdays` pré-carregados. `upcoming_occurrences`
    passa a delegar a ela.
  - Descartar ocorrência de hoje com `end_time <= agora` continua valendo em todos os usos.
- **Rationale**: FR-018 pede uma só regra para a próxima ocorrência, os detalhes e o filtro; hoje
  `upcoming_occurrences` consulta o banco por atividade (N+1), inviável na listagem.
- **Alternatives considered**: reimplementar o cálculo em `consultation` (duas regras que podem
  divergir); manter `iter_occurrences` dia a dia para a listagem (custo proporcional ao tamanho do
  período por atividade).

## 4. Janela do filtro de data

- **Decision**: parâmetros `date` (um dia) **ou** `date_from`/`date_to` (extremos inclusive); pedir `date`
  junto com `date_from`/`date_to` é 400. `date_from` sozinho = dessa data em diante; `date_to` sozinho =
  de hoje até essa data. Com os dois, o intervalo máximo é de 366 dias (de `date_from` a `date_to`);
  `date_from > date_to` é 400. O início efetivo da janela é `max(date_from, hoje)`; janela inteira no
  passado devolve lista vazia, não erro. Datas em `YYYY-MM-DD`.
- **Rationale**: segue o DOC-05 ("rejeitar combinações ambíguas") e a spec. O limite de 366 dias da
  spec só faz sentido quando há dois extremos; com extremo aberto, `first_occurrence` não varre o
  período, então o custo já é limitado.
- **Alternatives considered**: exigir sempre os dois extremos (mais rígido que o necessário para a
  interface); limitar também janelas abertas (sem ganho, o custo é constante).

## 5. Parâmetros de consulta e validação

- **Decision**: um `ConsultationQuerySerializer` (DRF) valida e normaliza: `q` (até 100 caracteres
  após `strip`; vazio vira ausente), `unit` e `category` (UUID), `neighborhood` (texto, até 100),
  `date`, `date_from`, `date_to`. Parâmetros desconhecidos são ignorados. `page_size` e `page` ficam
  com o paginador: `page_size` inválido ou menor que 1 usa o padrão (12), acima de 50 é limitado a 50
  (comportamento do DRF); página inexistente é 404 JSON.
- **Rationale**: erros de campo vêm no formato padrão do DRF e passam pelo *exception handler* (item
  6); termos sempre tratados como texto, nunca interpolados em consulta (ORM parametrizado e busca em
  Python).
- **Alternatives considered**: `django-filter` (dependência nova para 6 parâmetros); validar à mão
  nas views (mensagens inconsistentes).

## 6. Formato único de erro

- **Decision**: `apps/core/exceptions.py` com `public_exception_handler`, configurado em
  `REST_FRAMEWORK["EXCEPTION_HANDLER"]`. Resposta de erro: `{"detail": "<mensagem>", "errors":
  {"campo": ["mensagem", ...]}}`; `errors` só aparece em 400 de validação. 404 usa mensagem genérica
  ("Não encontrado."), igual para atividade inexistente, malformada ou não publicada. Exceções não
  tratadas continuam sendo 500 do Django sem corpo detalhado (`DEBUG` desligado).
- **Rationale**: FR-019 e constituição IV (erros JSON consistentes, códigos corretos). O handler
  global também cobre o `HealthView` sem mudar seu contrato de sucesso.
- **Alternatives considered**: manter os formatos padrão do DRF (4xx com formas diferentes: dict de
  campos em 400, `detail` em 404/405); adotar problem+json (fora do que o DOC-05 propõe).

## 7. Somente leitura e sem autenticação

- **Decision**: uma classe base `PublicAPIView` com `authentication_classes = []`,
  `permission_classes = [AllowAny]` e apenas `get`; as views usam `APIView`/`GenericAPIView` sem mixins
  de escrita, então `POST`, `PUT`, `PATCH` e `DELETE` retornam 405. Credenciais inválidas enviadas por
  engano não são lidas e a consulta segue anônima (spec, edge case).
- **Rationale**: FR-001, FR-017, SC-008; mesma abordagem do `HealthView`.
- **Alternatives considered**: `ReadOnlyModelViewSet` com autenticação padrão (credenciais inválidas
  quebrariam a consulta pública com 401/403).

## 8. Detalhe: 404 uniforme, UUID, link e programações

- **Decision**: `GET /api/v1/activities/{id}/` aceita o segmento como texto; se não for UUID válido,
  ou se a atividade não existir ou não estiver `PUBLISHED`, responde o mesmo 404 JSON. O link externo
  é entregue só se começar com `http://` ou `https://` (revalida o valor gravado), senão `null`.
  `schedules` traz todas as programações da atividade ordenadas por data inicial, com `weekdays` (1 a
  7, DOC-03) e `weekday_names` (por extenso, para acessibilidade); `next_occurrences` traz até 5
  ocorrências futuras.
- **Rationale**: FR-006, FR-007, FR-016, DOC-05 §5. Um parâmetro de rota `<uuid:pk>` faria o Django
  devolver 404 em HTML para identificador malformado, quebrando o formato único.
- **Alternatives considered**: devolver 400 para UUID malformado (revelaria a diferença entre "mal
  formado" e "inexistente"; a spec pede resposta indistinguível); ocultar programações já encerradas
  (a spec não pede; o frontend pode ocultar usando `next_occurrences`).

## 9. Unidades e categorias

- **Decision**: `GET /api/v1/units/` e `GET /api/v1/categories/` listam apenas `is_active=True`,
  ordenados por nome, no mesmo envelope paginado. Campos: `id`, `name`, `slug`, `description` e, para
  unidades, `neighborhood` e `address`. Sem endpoints de detalhe nesta versão.
- **Rationale**: DOC-05 §3.1 marca o detalhe como opcional; o frontend só precisa das listas para os
  filtros (YAGNI). Atividade já publicada continua mostrando a unidade e a categoria mesmo se
  inativas, pois o serializer da atividade lê direto o vínculo.
- **Alternatives considered**: sem paginação nas listas (inconsistente com o DOC-05 e sem proteção
  contra crescimento); implementar os detalhes agora (sem necessidade comprovada).

## 10. CORS

- **Decision**: nenhuma mudança; o `CorsMiddleware` e `CORS_ALLOWED_ORIGINS` (feature 001) já cobrem
  respostas `GET` das novas rotas. Adicionar um teste de que a listagem recebe o cabeçalho para a
  origem autorizada.
- **Rationale**: FR-020; a configuração é global, não por rota.
