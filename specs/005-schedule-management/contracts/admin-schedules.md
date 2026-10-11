# Contrato: programações no Django Admin

Todas as rotas exigem conta autenticada do grupo "Administrador" (ver
`specs/002-admin-access/contracts/admin-access.md`). Sem a permissão, o Admin recusa o acesso, inclusive
por URL direta. Não há endpoints REST nesta feature.

## Rotas

| Rota | Função |
|---|---|
| `/admin/schedules/schedule/` | Lista, filtros e busca de programações |
| `/admin/schedules/schedule/add/` | Cadastrar programação (aceita `?activity=<id>` para preencher a atividade; também é possível cadastrar direto na página da atividade) |
| `/admin/schedules/schedule/<id>/change/` | Editar ou excluir programação |
| `/admin/activities/activity/<id>/change/` | Mostra as programações e as próximas ocorrências da atividade |

## Formulário da programação

- Campos: atividade, tipo, data inicial, data final, horário de início, horário de término e dias da
  semana (checkboxes de segunda a domingo). Somente leitura: criada por, atualizada por, datas.
- A lista de atividades mostra todas as situações; atividade cancelada ou encerrada também pode
  receber programações.
- Ajuda do campo "dias da semana": "Obrigatório para programações recorrentes. Deve ficar vazio nas
  pontuais."

### Mensagens de validação

| Situação | Campo | Mensagem |
|---|---|---|
| Data inicial posterior à final | Data final | "A data final não pode ser anterior à data inicial." |
| Término não posterior ao início | Horário de término | "O horário de término deve ser posterior ao de início." |
| Pontual com datas diferentes | Data final | "Em programação pontual, a data final deve ser igual à inicial." |
| Recorrente sem dia | Dias da semana | "Selecione ao menos um dia da semana." |
| Pontual com dias | Dias da semana | "Programação pontual não usa dias da semana." |

## Lista de programações

- Colunas: atividade, tipo, período, horário, dias da semana (nomes abreviados), atualizada em.
- Filtros: tipo, atividade (lista de busca por título), período (data inicial e final).
- Busca por título da atividade.

## Página da atividade

- Inline "Programações" editável, também na tela de cadastro da atividade: tipo, datas, horários e dias
  da semana (checkboxes). Permite adicionar, editar e remover programações; autoria e regras de
  validação são as mesmas do formulário da programação.
- Campo "Próximas ocorrências" (na criação mostra "Salve a atividade para ver as próximas ocorrências."): até 10 datas com horário, em ordem, para atividade publicada; para as
  demais situações, o texto "Sem ocorrências: a atividade não está publicada."; sem datas futuras,
  "Sem próximas ocorrências."
- A exclusão de atividade com programações é recusada pelo Admin (objetos protegidos).

## Ações

Sem ações em lote nesta feature. Excluir programação usa a exclusão padrão do Admin, com confirmação.
