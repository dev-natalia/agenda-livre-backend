# Data Model: Gestão de Unidades e Categorias

Fonte: `docs/03-modelo-de-dados.md`, seções `Unit` e `Category`.

## Base abstrata `CatalogModel` (`apps/core`)

| Campo | Tipo | Obrigatório | Regras |
|---|---|---|---|
| `id` | UUID | Sim | Chave primária gerada automaticamente, não editável |
| `name` | Texto, até 150 | Sim | Sem espaços nas pontas; não pode ser só espaços |
| `slug` | Slug, até 160 | Sim (gerado se vazio) | Único; gerado de `name` quando vazio; recusado se vazio após a geração |
| `description` | Texto longo | Não | |
| `is_active` | Booleano | Sim | Padrão `true` |
| `created_at` | Data e hora | Sim | Preenchido na criação, somente leitura |
| `updated_at` | Data e hora | Sim | Atualizado a cada gravação, somente leitura |

Ordenação padrão: `name`. Representação textual: `name`.

## `Unit` (`apps/units`, herda `CatalogModel`)

| Campo | Tipo | Obrigatório | Regras |
|---|---|---|---|
| `neighborhood` | Texto, até 100 | Sim | Sem espaços nas pontas; usado depois no filtro por bairro |
| `address` | Texto longo | Não | Texto simples |

- Nome não precisa ser único; o `slug` é o identificador único (FR-003).
- Sem restrição de exclusão nesta feature (não há dependentes). A feature 004 liga atividades à
  unidade com `on_delete=PROTECT`.

## `Category` (`apps/categories`, herda `CatalogModel`)

- Restrição: `UniqueConstraint(Lower("name"))`, nome único sem diferenciar maiúsculas (FR-008).
- A feature 004 liga atividades à categoria com `on_delete=PROTECT`.

## Relacionamentos (futuros)

```text
Unit 1 ──< Activity >── 1 Category      (feature 004, ambos PROTECT)
```

## Transições de estado

```text
ativa ──desativar──▶ inativa     (vínculos preservados; deixa de ser oferecida em novos vínculos)
inativa ──reativar──▶ ativa
sem atividades vinculadas ──excluir──▶ removida
com atividades vinculadas ──excluir──▶ recusada (PROTECT)
```
