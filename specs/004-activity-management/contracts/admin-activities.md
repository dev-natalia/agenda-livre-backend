# Contrato: atividades e públicos-alvo no Django Admin

Todas as rotas exigem conta autenticada do grupo "Administrador" (ver
`specs/002-admin-access/contracts/admin-access.md`). Sem a permissão, o Admin recusa o acesso, inclusive por
URL direta. Não há endpoints REST nesta feature.

## Rotas

| Rota | Função |
|---|---|
| `/admin/activities/activity/` | Lista, busca, filtros e ações de situação |
| `/admin/activities/activity/add/` | Cadastrar atividade (nasce como rascunho) |
| `/admin/activities/activity/<id>/change/` | Editar atividade; excluir só se for rascunho |
| `/admin/audiences/targetaudience/` | Lista e filtro de públicos-alvo |
| `/admin/audiences/targetaudience/add/` | Cadastrar opção de público |
| `/admin/audiences/targetaudience/<id>/change/` | Editar opção de público |

## Interface

- Menu em português: "Atividades" e "Públicos-alvo".
- **Lista de atividades**: colunas título, unidade, categoria, situação (rótulo em português) e
  atualizada em; filtros por situação, unidade e categoria; busca por título e resumo.
- **Formulário**: título, resumo, descrição, unidade, categoria, observações sobre o público, link
  externo e o inline "Públicos-alvo". Somente leitura: situação, identificador, criada por, atualizada
  por, datas.
- **Inline de públicos**: oferece opções ativas e o que já estiver vinculado.
- **Ações**: "Publicar selecionadas", "Cancelar selecionadas", "Encerrar selecionadas". Exigem a
  permissão de alteração.
- **Lista de públicos-alvo**: nome, identificador, situação; filtro por situação; ações em lote
  "Desativar selecionados" e "Reativar selecionados".

## Rótulos de situação

| Valor | Rótulo |
|---|---|
| `DRAFT` | Rascunho |
| `PUBLISHED` | Publicada |
| `FINISHED` | Encerrada |
| `CANCELLED` | Cancelada |

## Regras de validação (mensagens de formulário)

| Situação | Resultado |
|---|---|
| Título, descrição, unidade ou categoria em branco | Recusa com mensagem no campo |
| Título ou descrição só com espaços | Tratado como em branco |
| Link externo malformado ou sem `http`/`https` | Recusa com mensagem no campo |
| Mesma opção de público duas vezes | Recusa com mensagem no inline |
| Salvar atividade `PUBLISHED` sem nenhum público | Recusa com mensagem no inline |
| Unidade ou categoria inativa em novo vínculo | Não aparece na lista; valor forçado é recusado |
| Editar atividade cuja unidade foi desativada, sem trocá-la | Aceita; vínculo mantido |

## Regras das ações de situação

| Ação | Aceita atividades em | Resultado |
|---|---|---|
| Publicar | `DRAFT`, `CANCELLED`, `FINISHED` | Passa a `PUBLISHED` se as regras de publicação passam |
| Cancelar | `PUBLISHED` | Passa a `CANCELLED` |
| Encerrar | `PUBLISHED` | Passa a `FINISHED` |

- Em lote, cada atividade é tratada separadamente; a mensagem final informa quantas mudaram e lista as
  que foram recusadas com o motivo (por exemplo, "falta ao menos um público-alvo").
- Atividade já na situação pedida é ignorada sem erro.
- Toda mudança grava `updated_by` e `updated_at`.

## Exclusão

- O botão e a ação de excluir só estão disponíveis para atividades em rascunho.
- A exclusão de unidade, categoria ou público-alvo vinculados a atividades é recusada pelo Admin com
  a lista de registros que a impedem.

## Permissões

- Cadastrar, editar, publicar, cancelar, encerrar e excluir exigem as permissões `add`, `change` e
  `delete` do modelo, concedidas ao grupo "Administrador" pela sincronização da feature 002.
