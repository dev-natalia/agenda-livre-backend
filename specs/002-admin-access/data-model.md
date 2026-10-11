# Data Model: Administração e Acesso

Nenhuma tabela nova é definida pelo projeto. A feature usa as tabelas nativas do Django, criadas pelas
migrations de `django.contrib.auth`, `admin`, `sessions` e `contenttypes`.

## Conta administrativa (`auth.User`)

| Campo | Uso nesta feature |
|---|---|
| `username` | Identificador de login, único |
| `password` | Hash da senha (nunca texto simples) |
| `is_active` | `false` desativa a conta sem apagar seus registros |
| `is_staff` | Necessário para entrar no Admin |
| `groups` | Pertencer ao grupo "Administrador" concede o perfil |
| `is_superuser` | Não usado como perfil; se verdadeiro, ignora o grupo (evitar nas contas comuns) |

Uma conta é **administradora** quando `is_active` e `is_staff` são verdadeiros e ela pertence ao grupo
"Administrador". Uma conta sem o grupo não tem permissões. A desativação preserva o registro (os
registros de auditoria das próximas features continuam referenciando a conta).

## Perfil de administrador (`auth.Group` chamado "Administrador")

- Criado e sincronizado após cada migração (idempotente).
- Contém todas as permissões existentes (`view`, `add`, `change`, `delete` de todos os modelos,
  incluindo `User` e `Group`).

## Permissão (`auth.Permission`)

Criadas pelo Django para cada modelo. Não há permissões personalizadas.

## Transições de estado da conta

```text
criada (ativa, sem grupo) ──atribuir grupo──▶ administradora
administradora ──retirar grupo──▶ sem acesso
qualquer estado ──desativar──▶ inativa (login recusado)
inativa ──reativar──▶ estado anterior ao desativar
```
