# Contrato: variáveis de ambiente

As variáveis são lidas do ambiente do processo e, se existir, do arquivo `.env` na raiz do repositório.
O arquivo `.env` **não** é versionado. O arquivo `.env.example` é versionado e lista todos os nomes, sem
valores reais.

| Variável | Obrigatória | Padrão | Descrição |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | Sim | | Chave secreta do Django |
| `DJANGO_DEBUG` | Não | `False` | Modo de depuração (`True` ou `False`) |
| `DJANGO_ALLOWED_HOSTS` | Não | `localhost,127.0.0.1` | Hosts aceitos, separados por vírgula |
| `DB_HOST` | Sim | | Endpoint do PostgreSQL no RDS |
| `DB_PORT` | Sim | | Porta do PostgreSQL (normalmente `5432`) |
| `DB_NAME` | Sim | | Nome do banco |
| `DB_USER` | Sim | | Usuário do banco |
| `DB_PASSWORD` | Sim | | Senha do usuário |
| `DB_SSLMODE` | Não | `require` | Modo TLS do PostgreSQL |
| `DB_SSLROOTCERT` | Não | | Caminho do certificado raiz, usado com `verify-ca` ou `verify-full` |
| `CORS_ALLOWED_ORIGINS` | Não | vazio | Origens do frontend, separadas por vírgula (ex.: `http://localhost:5500`) |

## Comportamento em caso de erro

Se alguma variável obrigatória estiver ausente ou vazia, a aplicação não inicia e exibe uma única mensagem
com o nome de **todas** as variáveis que faltam, por exemplo:

```text
Configuração incompleta. Defina as variáveis de ambiente: DB_HOST, DB_PASSWORD
```

Se um valor tiver formato inválido, a mensagem cita o nome da variável e a regra violada, sem imprimir o
valor.

## Configuração de testes

Os testes usam `config/settings_test.py`, que não exige nenhuma dessas variáveis e usa um banco `dummy`
que recusa qualquer conexão.
