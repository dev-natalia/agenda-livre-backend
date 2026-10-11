# Research: Gestão de Unidades e Categorias

## R1. Base compartilhada entre Unit e Category

- **Decision**: classe abstrata `CatalogModel` em `apps/core/models.py` com `id` (UUID), `name`,
  `slug`, `description`, `is_active`, `created_at`, `updated_at`. `Unit` acrescenta `address` e
  `neighborhood`; `Category` não acrescenta campos.
- **Rationale**: as duas entidades têm os mesmos sete campos em `docs/03-modelo-de-dados.md`. Uma base
  evita duplicar regras de slug e validação.
- **Alternatives**: dois modelos independentes (duplica código); modelo concreto único com tipo
  (mistura entidades distintas e complica as chaves estrangeiras).

## R2. Geração e unicidade do identificador (slug)

- **Decision**: `slug` é `SlugField(unique=True, blank=True)`. Em `clean()`, se estiver vazio, é gerado
  com `slugify(name)`. Como `full_clean()` roda `clean()` antes de `validate_unique()`, um slug
  repetido (informado ou gerado) vira erro de formulário, sem sufixos automáticos. O `ModelAdmin`
  usa `prepopulated_fields` para sugerir o slug ao digitar o nome. Se `slugify` resultar em texto
  vazio (nome só com símbolos), o formulário recusa com mensagem.
- **Rationale**: cumpre FR-003, FR-008 e FR-012. Recusar em vez de renomear em silêncio evita slugs
  inesperados, que serão usados em URLs públicas.
- **Alternatives**: sufixo numérico automático (esconde a duplicidade); slug somente gerado e não
  editável (a spec permite ajuste pela pessoa administradora).

## R3. Unicidade do nome da categoria sem diferenciar maiúsculas

- **Decision**: `UniqueConstraint(Lower("name"))` em `Category`. O Django valida restrições com
  expressão em `full_clean()` (`validate_constraints`), então o Admin mostra erro de formulário. O
  banco também garante a regra. `Unit` não tem restrição de nome (a spec exige só slug único).
- **Rationale**: atende o caso de borda "Cultura e Artes" x "cultura e artes". Acentos são tratados
  como diferentes; o slug (sem acentos) já barra a maioria das colisões práticas.
- **Alternatives**: `unique=True` em `name` (diferencia maiúsculas); extensão `citext` do PostgreSQL
  (exige extensão e foge do ORM puro).

## R4. Espaços nos nomes

- **Decision**: o campo de formulário do Django já remove espaços nas pontas e recusa valores só com
  espaços. `clean()` também aplica `strip()` em `name` e `neighborhood` para cobrir gravações que não
  passem pelo formulário.
- **Rationale**: cobre o caso de borda sem lógica extra.
- **Alternatives**: confiar só no formulário (deixa o dado sujo se entrar por outro caminho).

## R5. Desativar, reativar e proteger vínculos

- **Decision**: a desativação é `is_active=False`, pelo formulário ou por ações em lote
  "Desativar selecionados" e "Reativar selecionados" (`ActiveToggleActionsMixin`). Lista com filtro e
  coluna de situação. A feature 004 DEVE declarar as chaves estrangeiras de atividade para unidade e
  categoria com `on_delete=PROTECT`; assim o Admin já impede a exclusão e mostra a explicação padrão
  do Django. O `ActiveOnlyForeignKeyMixin` da feature 002 oculta inativos nos novos vínculos.
- **Rationale**: nenhum código extra de exclusão: o PROTECT nativo cumpre FR-011. Sem as atividades
  ainda não há o que proteger, então o vínculo fica registrado no contrato para a feature 004.
- **Alternatives**: bloquear exclusão no `ModelAdmin` sempre (impede apagar cadastro errado sem uso);
  `delete()` sobrescrito (frágil em exclusões em lote).

## R6. Datas de criação e atualização

- **Decision**: `created_at` com `auto_now_add` e `updated_at` com `auto_now`, ambos somente leitura no
  Admin.
- **Rationale**: FR-013, mecanismo nativo.
- **Alternatives**: preencher no `save()` (reimplementa o nativo).

## R7. Carga inicial de dados

- **Decision**: comando `seed_catalog`, idempotente (`get_or_create` por slug, sem sobrescrever o que
  já existe). Carrega o CEU Navegantes e as oito categorias do documento de visão. Os valores ficam
  como constantes no comando.
- **Rationale**: FR-018 e SC-007; reexecutar é seguro e não duplica. Não usa migration de dados porque
  a lista de categorias ainda será validada e migrations não devem carregar dados de negócio ajustáveis.
- **Alternatives**: fixture JSON com `loaddata` (UUIDs fixos e sobrescrita de edições); migration de
  dados (difícil de ajustar depois); digitar tudo pelo Admin (lento e sujeito a erro).
- **Dado a confirmar**: o bairro do CEU Navegantes não consta nos documentos. A carga usa
  `neighborhood="Navegantes"` e deixa o endereço em branco; confirmar com a equipe antes da
  demonstração.

## R8. Permissões do novo cadastro

- **Decision**: nada a fazer. As permissões `view/add/change/delete` dos novos modelos são criadas pelo
  Django e entram no grupo "Administrador" pelo sinal `post_migrate` da feature 002.
- **Rationale**: reaproveita a feature 002 (FR-016).
- **Alternatives**: atribuir permissões manualmente (esquecível).

## R9. Edição simultânea

- **Decision**: vale a última gravação; sem bloqueio otimista.
- **Rationale**: equipe pequena, sistema local; YAGNI. Registrado como limitação conhecida.
- **Alternatives**: campo de versão e comparação ao salvar (complexidade sem necessidade concreta).
