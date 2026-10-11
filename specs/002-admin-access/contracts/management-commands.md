# Contrato: comandos de gerenciamento

## `create_admin <username>`

Cria uma conta de administrador.

- **Entrada**: nome de usuário como argumento. A senha é pedida sem eco, duas vezes. Não existe opção
  para passar a senha pela linha de comando.
- **Ação**: valida a senha com os validadores configurados, cria a conta ativa, `is_staff`, e a adiciona
  ao grupo "Administrador" (criando o grupo e sincronizando as permissões se faltar).
- **Sucesso** (código 0): informa que a conta foi criada. Não imprime a senha.
- **Falhas** (código diferente de 0): usuário já existe, senhas diferentes ou senha rejeitada pelos
  validadores, com a mensagem do motivo.
- **Pré-requisito**: migrations aplicadas (`safe_migrate`), pois o comando grava no banco.

## Sincronização do perfil (automática)

Após cada `migrate`/`safe_migrate`, o grupo "Administrador" é criado se necessário e recebe todas as
permissões existentes. Não há comando separado; rodar a migração de novo é seguro (idempotente).

## Desativar e reativar contas

Feito pelo painel (`/admin/auth/user/`): desmarcar ou marcar "Ativo". Não há comando.
