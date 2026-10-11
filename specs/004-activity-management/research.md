# Research: Gestão de Atividades

Não havia itens "NEEDS CLARIFICATION" no Technical Context. As decisões abaixo resolvem as escolhas de
desenho que a spec deixou para o plano.

## 1. Situação alterada só por ações

- **Decision**: o campo `status` fica somente leitura no formulário do Admin (valor inicial `DRAFT`).
  Três ações em lote/individuais (`Publicar`, `Cancelar`, `Encerrar`) chamam `change_status()` em
  `apps/activities/services.py`.
- **Rationale**: garante o fluxo da spec (FR-014) e a validação de publicação (FR-010) em um só lugar;
  impede pular regras editando o campo. A ação exige a permissão `change` (`allowed_permissions`),
  então a verificação de servidor da feature 002 vale também aqui (FR-015).
- **Alternatives considered**: campo `status` editável com `clean()` validando a transição, o que
  exigiria comparar com o valor anterior e permitiria publicar sem a validação do inline de públicos.

## 2. Regras de transição e publicação

- **Decision**: transições permitidas: `DRAFT→PUBLISHED`, `PUBLISHED→CANCELLED`, `PUBLISHED→FINISHED`,
  `CANCELLED→PUBLISHED`, `FINISHED→PUBLISHED`. Pedir a situação em que a atividade já está é um
  no-op sem erro. Qualquer outra transição é recusada com mensagem. Para publicar: título e descrição
  não vazios, unidade e categoria ativas e pelo menos um público-alvo ativo ou já vinculado.
- **Rationale**: reproduz as Assumptions da spec. Para a regra dos públicos, vínculos antigos a opções
  hoje inativas continuam valendo (FR-004), então basta existir ao menos um vínculo.
- **Alternatives considered**: exigir que todos os públicos estejam ativos para publicar (bloqueia
  republicação por causa de opção desativada, contra FR-004).

## 3. Autoria

- **Decision**: `created_by` e `updated_by` são `ForeignKey` para o usuário com `on_delete=PROTECT`,
  somente leitura no Admin. `save_model` define `created_by` na criação e `updated_by` sempre;
  `change_status()` define `updated_by` e salva com `update_fields`. `created_at`/`updated_at` usam
  `auto_now_add`/`auto_now` (as ações de situação incluem `updated_at` em `update_fields`).
- **Rationale**: o documento de dados pede preservar conteúdo ao desativar contas; contas são
  desativadas, não apagadas, e `PROTECT` impede a exclusão acidental de quem tem autoria. Os campos de
  autoria são obrigatórios, sem caso de rotina automatizada hoje (pendência 11 do backlog).
- **Alternatives considered**: `SET_NULL` (perde a autoria); tabela de histórico de situações (fora
  do escopo, YAGNI).

## 4. Slug da atividade

- **Decision**: gerado de `slugify(title)` quando o campo está em branco, no `clean()` ou `save()`,
  acrescentando `-2`, `-3`... se já existir. O slug não é editável depois de criado e o campo fica
  somente leitura no formulário.
- **Rationale**: atende ao Assumption (gerado automaticamente, sem colisão) e mantém URLs estáveis
  para a API pública futura. A checagem de colisão consulta o banco, então é isolada em um método
  pequeno para mockar nos testes.
- **Alternatives considered**: slug digitado pela pessoa (erro humano, colisões); UUID como slug
  (URLs pouco legíveis).

## 5. Públicos-alvo: modelo, inline e unicidade

- **Decision**: `TargetAudience` reaproveita `CatalogModel` (nome, slug, situação ativa, datas;
  mantém também o campo `description` opcional da base). `ActivityTargetAudience` é o modelo
  intermediário explícito, com `UniqueConstraint(activity, target_audience)` e uso no `ManyToManyField`
  via `through`. O formulário usa um `TabularInline` do modelo intermediário.
- **Rationale**: segue `docs/03-modelo-de-dados.md` (through explícito) e o padrão da feature 003. O
  `description` extra é opcional e custa nada; criar outra base só para omiti-lo seria mais complexo.
  A restrição de unicidade impede duplicidade mesmo com salvamentos repetidos (FR-006, SC-006) e o
  Admin mostra erro de formulário quando a mesma opção é escolhida duas vezes.
- **Alternatives considered**: `filter_horizontal` direto no M2M (não funciona com `through` que tenha
  campos extras no futuro e dá menos controle sobre opções inativas); campo de lista JSON (sem
  integridade).

## 6. Opções inativas sem quebrar a edição

- **Decision**: ampliar `ActiveOnlyForeignKeyMixin` (feature 003) para incluir, além dos registros
  ativos, o valor já gravado na instância em edição. O `ModelAdmin` guarda o objeto em edição em
  `get_form`/`get_formset` e o mixin lê o valor atual dele. Vale para unidade, categoria e público
  do inline.
- **Rationale**: hoje o mixin filtra só `is_active=True`, o que faria o Django recusar o formulário de
  uma atividade cuja unidade foi desativada depois (spec, US-003 cenário 5). Manter o valor atual
  preserva o vínculo (FR-004) sem oferecer inativos para novos vínculos.
- **Alternatives considered**: validar no `clean()` do modelo (não afeta o que a lista oferece).

## 7. Exclusão de atividades

- **Decision**: `has_delete_permission` do `ModelAdmin` retorna `True` apenas para atividades em
  `DRAFT`. As demais devem ser canceladas ou encerradas. A feature de programações (005) cria
  `Schedule.activity` com `on_delete=PROTECT`, completando FR-016 no banco.
- **Rationale**: ainda não existe programação nesta feature; limitar a exclusão a rascunhos mantém o
  histórico (SC-007) e orienta o uso de cancelar/encerrar, sem depender de modelos futuros.
- **Alternatives considered**: bloquear toda exclusão (impede limpar rascunhos criados por engano);
  `CASCADE` para programações (perde histórico).

## 8. Carga inicial de públicos-alvo

- **Decision**: estender `seed_catalog` com as opções Crianças, Adolescentes, Adultos, Pessoas idosas e
  Todas as idades, idempotente por slug, no mesmo padrão de unidades e categorias.
- **Rationale**: FR-018 pede opções na primeira carga; o comando já existe e é seguro para repetir.
  A lista é provisória (pendência 1 do backlog) e pode ser ajustada pelo Admin.
- **Alternatives considered**: migration de dados (acopla a lista ao esquema e não é editável depois
  sem nova migration).

## 9. Filtros e busca no Admin

- **Decision**: `list_filter` por situação, unidade e categoria; `search_fields` por título e resumo;
  `list_display` com título, unidade, categoria, situação e data de atualização;
  `list_select_related` para unidade e categoria.
- **Rationale**: FR-017, sem custo de consultas por linha.
- **Alternatives considered**: nenhuma relevante.

## 10. Estratégia de testes sem banco

- **Decision**: testes com instâncias não salvas e `unittest.mock` para queryset, `save` e consulta de
  colisão de slug; admin com `RequestFactory` e usuários simulados; o serviço `change_status` recebe a
  atividade e o usuário e é testado com mocks de `save` e do contador de públicos.
- **Rationale**: Constituição III (sem banco). A verificação real contra o RDS fica no quickstart.
- **Alternatives considered**: `django_db` (proibido pela constituição).
