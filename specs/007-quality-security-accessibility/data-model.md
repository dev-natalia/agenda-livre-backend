# Data Model: Qualidade, Segurança e Acessibilidade

**Sem mudanças de esquema.** Nenhuma tabela, coluna, índice, constraint ou migration é criada ou
alterada. Esta feature fixa invariantes sobre entidades existentes e define um objeto de resposta.

## Invariantes de auditoria (Activity e Schedule)

| Campo | Tipo | Regra |
|---|---|---|
| `created_by` | FK usuário, `PROTECT`, `editable=False` | Preenchido uma vez, na criação, com o usuário da requisição. Nunca muda. |
| `updated_by` | FK usuário, `PROTECT`, `editable=False` | Preenchido em toda escrita administrativa com o usuário da requisição. |
| `created_at` | datetime, `auto_now_add` | Definido na criação; nunca muda. |
| `updated_at` | datetime, `auto_now` | Avança em toda gravação. Em `save(update_fields=...)`, o campo precisa constar na lista. |

### Caminhos de escrita que devem cumprir a regra

| Caminho | Onde está | Cobre |
|---|---|---|
| Formulário da atividade | `ActivityAdmin.save_model` | `created_by` (só se novo), `updated_by` |
| Programação dentro da atividade | `ActivityAdmin.save_formset` | `created_by` (só se nova), `updated_by`, para cada programação salva |
| Programação isolada | `ScheduleAdmin.save_model` | idem |
| Mudança de situação (ação em massa) | `change_status` via `ActivityAdmin._apply_status` | `updated_by`, `updated_at` |

Todos os campos de auditoria aparecem como somente leitura na administração.

### Transição de estado e autoria

`DRAFT → PUBLISHED → CANCELLED | FINISHED` (conforme `ALLOWED_TRANSITIONS`): cada transição aceita
atualiza `updated_by` e `updated_at`; uma transição recusada **não** altera nenhum campo.

## Autores removidos

`on_delete=PROTECT` em `created_by` e `updated_by` de `Activity` e `Schedule`: remover um usuário que
é autor falha. Política completa em [contracts/audit-policy.md](contracts/audit-policy.md).

## Objeto de resposta de erro (não persistido)

| Campo | Tipo | Quando |
|---|---|---|
| `detail` | texto em português | Sempre |
| `errors` | mapa nome-do-campo → lista de textos | Só em erro de validação (400). Erros sem campo usam a chave `non_field_errors`. |

Contrato em [contracts/error-format.md](contracts/error-format.md).

## Campos proibidos em respostas públicas

`created_by`, `updated_by`, `created_at`, `updated_at`, `status`, qualquer dado de conta (`username`,
`email`, `is_staff`, `is_superuser`, `password`) e qualquer valor de configuração ou segredo.
