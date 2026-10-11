# Contrato: comandos de gerenciamento

Ambos são executados com `python manage.py <comando>` e usam a configuração de execução (variáveis de
ambiente). Nenhum deles imprime senha ou chave secreta.

## `check_db`

Verifica se o banco está acessível.

- **Ação**: abre a conexão configurada e executa uma consulta simples.
- **Saída em sucesso** (código de saída 0): host, porta e nome do banco, e a mensagem de que a conexão
  funcionou.
- **Saída em falha** (código de saída diferente de 0): host, porta e nome do banco, o tipo de falha (por
  exemplo, credenciais recusadas, tempo esgotado, host inacessível) e uma dica de correção. Sem senha.
- **Tempo limite**: a tentativa de conexão é interrompida em até 15 segundos.

## `safe_migrate`

Aplica as migrations mostrando antes qual banco será modificado.

- **Ação**:
  1. Exibe host, porta, nome do banco e usuário de destino (sem senha).
  2. Pede confirmação (`s/N`), a menos que `--noinput` seja informado.
  3. Se confirmado, executa o `migrate` padrão do Django.
- **Recusa**: qualquer resposta diferente de `s` encerra sem alterar o banco (código de saída diferente
  de 0).
- **Opções**: aceita `--noinput` para execução sem interação.
