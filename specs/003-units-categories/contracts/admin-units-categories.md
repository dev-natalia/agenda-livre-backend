# Contrato: cadastros no Django Admin

Todas as rotas exigem conta autenticada do grupo "Administrador" (ver
`specs/002-admin-access/contracts/admin-access.md`). Sem a permissão, o Admin recusa o acesso, inclusive por
URL direta. Não há endpoints REST nesta feature.

## Rotas

| Rota | Função |
|---|---|
| `/admin/units/unit/` | Lista, busca e filtro de unidades |
| `/admin/units/unit/add/` | Cadastrar unidade |
| `/admin/units/unit/<id>/change/` | Editar ou excluir unidade |
| `/admin/categories/category/` | Lista, busca e filtro de categorias |
| `/admin/categories/category/add/` | Cadastrar categoria |
| `/admin/categories/category/<id>/change/` | Editar ou excluir categoria |

## Interface

- Nomes no menu em português: "Unidades" e "Categorias" (singular: "Unidade", "Categoria").
- Rótulos dos campos em português: Nome, Identificador (slug), Bairro, Endereço, Descrição, Ativa(o),
  Criado em, Atualizado em.
- **Lista**: colunas nome, bairro (só unidades), identificador e situação ativa; filtro por situação
  ativa; busca por nome (e bairro, nas unidades).
- **Formulário**: `slug` sugerido automaticamente a partir do nome; datas somente leitura.
- **Ações em lote**: "Desativar selecionados" e "Reativar selecionados".

## Regras de validação (mensagens de formulário)

| Situação | Resultado |
|---|---|
| Nome em branco ou só espaços | Recusado, campo marcado |
| Bairro em branco (unidade) | Recusado, campo marcado |
| Slug repetido | Recusado, mensagem de identificador já existente |
| Nome repetido ignorando maiúsculas (categoria) | Recusado, mensagem de nome já existente |
| Slug em branco | Gerado a partir do nome; recusado se o resultado for vazio |
| Excluir registro com atividades vinculadas | Recusado pelo Admin, com orientação (feature 004) |

## Vínculo com a feature 004

- As chaves estrangeiras de `Activity` para `Unit` e `Category` devem usar `on_delete=PROTECT`.
- O `ModelAdmin` de atividade deve herdar `ActiveOnlyForeignKeyMixin` (feature 002) para não oferecer
  registros inativos.
