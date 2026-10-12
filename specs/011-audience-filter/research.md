# Research: Filtro por Público-alvo

**Feature**: 011-audience-filter | **Date**: 2026-10-12

Não restou nenhum `NEEDS CLARIFICATION` no Technical Context. Esta pesquisa registra as decisões de
desenho, a razão de cada uma e as alternativas descartadas, a partir do código existente (listagem em
`apps/consultation`, catálogo em `apps/audiences`, Admin e `seed_catalog`) e do `docs/10-filtro-por-publico-alvo.md`.

## 1. Onde aplicar o filtro: Python ou SQL

- **Decision**: filtrar **em Python**, dentro de `apply_criteria`, sobre a lista que a view já carrega. Cada
  atividade é examinada uma vez, usando `activity.target_audiences.all()` já carregado por
  `prefetch_related`.
- **Rationale**: a listagem pública já carrega todas as atividades publicadas (unidade e categoria vêm do
  banco; busca por texto e bairro são feitas em Python por causa da comparação sem acento) e ordena por
  próxima ocorrência em memória. Um filtro a mais em Python segue o mesmo caminho, **não pode duplicar
  atividades** (FR-004) e é testável com objetos em memória, sem banco (Princípio III). Como a relação de
  públicos precisa ser carregada de qualquer forma para o campo `target_audiences` (US-048), o filtro não
  custa nenhuma consulta a mais.
- **Alternatives considered**: `Q`/`Exists` no queryset (evita carregar atividades que não servem, mas o
  conjunto é pequeno e já é carregado inteiro; a lógica ficaria só verificável contra o banco real e a
  junção com a tabela de vínculo exigiria `distinct()` para impedir duplicatas); filtrar por `id` em
  subconsulta (mais uma consulta e o mesmo problema de teste).

## 2. Regra inclusiva de “Todas as idades”

- **Decision**: com `chosen` o público escolhido (ativo) e `links` os públicos da atividade:
  - se `chosen.includes_everyone`: a atividade entra quando algum vínculo é `chosen`;
  - senão: entra quando algum vínculo é `chosen` **ou** algum vínculo tem `includes_everyone`.
  A marca vale mesmo que o público marcado esteja inativo (os vínculos de um público desativado são
  preservados, DOC-03); já o público **escolhido** precisa estar ativo.
- **Rationale**: implementa exatamente as quatro regras da spec (US1, FR-002 a FR-004) e dispensa tratar
  `slug` ou nome. Mais de um público marcado funciona sem regra extra.
- **Alternatives considered**: comparar o `slug` `todas-as-idades` (rejeitado: acopla o código a um valor de
  cadastro; decisão do DOC-10, pendência 8); exigir que apenas um público seja marcado (restrição sem
  necessidade, sem como garanti-la sem uma constraint extra).

## 3. Como obter o público escolhido

- **Decision**: uma função `find_audience(audience_id)` em `services.py` faz
  `TargetAudience.objects.filter(pk=audience_id, is_active=True).first()`. `apply_criteria` a chama **só
  quando** `criteria.audience` foi informado; se devolve `None`, o resultado é a lista vazia (FR-006).
- **Rationale**: uma consulta de uma linha, só quando o filtro é usado; resolve em um passo “não existe” e
  “está inativo”, que têm o mesmo comportamento. A consulta é simulada nos testes unitários.
- **Alternatives considered**: carregar todos os públicos sempre (consulta desnecessária sem o filtro);
  descobrir a marca pelos vínculos das atividades (não serve quando nenhuma atividade usa o público).

## 4. Validação do parâmetro `audience`

- **Decision**: `audience = serializers.UUIDField(required=False, error_messages=ID_ERRORS)` em
  `ConsultationQuerySerializer`, igual a `unit` e `category`. `Criteria` ganha o campo `audience` e
  `criteria()` o preenche. Identificador vazio (`audience=`) é tratado como ausente, como acontece com `unit` e
  `category` (comportamento do DRF para campos não obrigatórios); valor repetido usa o último (comportamento do `QueryDict`).
- **Rationale**: reaproveita a mensagem “Informe um identificador válido.” e o formato de erro por campo
  (`errors.audience`) sem código novo de erro. Nenhuma regra de combinação muda.
- **Alternatives considered**: aceitar também o `slug` (inconsistente com `unit` e `category`); aceitar
  vários valores (fora do escopo, DOC-10 pendência 2).

## 5. Recurso `GET /api/v1/audiences/`

- **Decision**: `AudienceListView` (igual a `CategoryListView`): `TargetAudience.objects.filter(is_active=True)
  .order_by("name")`, paginado por `PublicAPIView.paginate`, com `AudienceItemSerializer` (`id`, `name`,
  `slug`, `description` ou `null`). Rota `audiences/` em `urls.py`. Não expõe `is_active` nem
  `includes_everyone`.
- **Rationale**: o frontend não precisa saber qual público é “abrange todos”, porque a regra roda no
  servidor; menos campos, menos risco. `405` para escrita vem de `PublicAPIView`.
- **Alternatives considered**: expor `includes_everyone` para o frontend destacar a opção (a spec o deixa
  de fora; pode ser acrescentado depois sem quebrar nada).

## 6. Campo `target_audiences` na listagem

- **Decision**: `published_activities` passa a usar `.prefetch_related("schedules__weekdays",
  "target_audiences")`. O serializer da listagem acrescenta `"target_audiences"` ao dicionário do item, com a
  lista `[{"id", "name"}]` **ordenada por nome em Python**. O detalhe já tinha o campo; ele passa a usar a mesma
  função de ordenação para os dois ficarem iguais. Atividade sem públicos devolve `[]`.
- **Rationale**: o prefetch soma uma consulta ao total (SC-007) e não uma por atividade; ordenar em Python
  não depende da ordenação do modelo na relação intermediária. O `AudienceSerializer` (id e nome) já existe.
- **Alternatives considered**: depender de `Meta.ordering` do modelo (não é garantido para relações
  muitos-para-muitos com tabela intermediária); novo serializer (duplicaria o existente).

## 7. Campo e migration

- **Decision**: `includes_everyone = models.BooleanField("Abrange todos os públicos", default=False,
  help_text=...)` em `TargetAudience`; migration `audiences/0002_targetaudience_includes_everyone.py`
  gerada por `makemigrations`. Nenhuma migration de dados.
- **Rationale**: aditiva e segura no banco compartilhado. A marca em “Todas as idades” é feita pelo
  `seed_catalog` (decisão da spec, FR-017), não por uma migration que citasse o `slug` — que é justamente o
  acoplamento que o campo veio evitar.
- **Alternatives considered**: data migration que marca o `slug` `todas-as-idades` (resolveria sozinha o
  banco compartilhado, mas reintroduz o `slug` no código); `CheckConstraint` ou unicidade da marca (sem uso,
  YAGNI).

## 8. `seed_catalog` e catálogo já existente

- **Decision**: o item `todas-as-idades` de `TARGET_AUDIENCES` ganha `"includes_everyone": True`, o que cobre
  a criação. Para um catálogo que já existia sem a marca, um passo extra, `_mark_everyone(manager, items)`,
  faz `manager.filter(slug=item["slug"]).update(includes_everyone=True)` apenas para os itens que declaram
  a marca. Nunca desmarca nada. A saída não muda (o resultado do `update` é ignorado).
- **Rationale**: `get_or_create` não atualiza o que já existe, então só `defaults` não bastaria no RDS atual;
  `update` apenas na marca é idempotente e respeita outras marcas feitas pelo administrador.
- **Alternatives considered**: `update_or_create` (sobrescreveria nome e descrição editados no Admin).

## 9. Admin

- **Decision**:
  - `TargetAudienceAdmin`: `includes_everyone` em `list_display` e em `list_filter`; o campo aparece no
    formulário automaticamente, com `help_text` claro.
  - `ActivityAdmin`: novo `AudienceListFilter(admin.SimpleListFilter)` em `list_filter`, com
    `title = "Público-alvo"` e `parameter_name = "audience"`. `lookups()` devolve os públicos ativos mais os
    inativos que têm vínculo (`Q(is_active=True) | Q(activity_links__isnull=False)`, `distinct()`, por nome);
    `queryset()` filtra por `audience_links__target_audience_id`. Como a atividade só se liga uma vez a cada
    público (restrição única existente), o filtro não duplica linhas.
- **Rationale**: atende o FR-018 sem alterar permissões nem ações em lote.
- **Alternatives considered**: `list_filter = ("audience_links__target_audience",)` simples (mostraria todos
  os públicos, inclusive inativos sem vínculo, e usaria o `__str__` sem ordem controlada).

## 10. Estratégia de testes

- **Decision**: testes unitários, sem banco:
  - `apply_criteria`/`matches_audience`: atividades `SimpleNamespace` com `target_audiences` simulado,
    cobrindo as quatro regras, duplicatas, sem público, marca em mais de um, público escolhido inexistente ou
    inativo, e combinação com `q` e bairro; `find_audience` com `TargetAudience.objects` simulado;
  - serializer: `audience` válido, vazio, malformado, repetido e combinado; `Criteria.audience`;
  - views: `/audiences/` (só ativos, ordem, campos, 405, sem campos administrativos) e `/activities/?audience=`
    ponta a ponta com o catálogo simulado; contagem de consultas simulada com `prefetch_related`;
  - listagem: `target_audiences` ordenado, lista vazia, campos existentes inalterados;
  - Admin: `AudienceListFilter.lookups` e `queryset`; `TargetAudienceAdmin` com o campo;
  - modelo: padrão falso; `seed_catalog`: marca na criação, marca em catálogo existente, nada desmarcado,
    repetição segura.
- **Rationale**: Princípio III; o mesmo estilo dos testes de consulta e de Admin existentes.

## 11. Pendências do DOC-10 que o plano fecha

| Pendência | Resolução |
|-----------|-----------|
| 2. Um ou vários valores | Um único valor, como `unit` e `category`. |
| 3. Forma do novo recurso | `GET /audiences/` com `id`, `name`, `slug`, `description` ou `null`. |
| 4. Nome do parâmetro | `audience`. |
| 5. Nome do campo na listagem | `target_audiences`, igual ao detalhe. |
| 6. Ampliação de escopo | Aprovada; constituição v1.2.0 e DOC-04 v0.5 atualizados. |
| 7. Filtro do Admin | Entra nesta entrega (P3). |
