# Data Model: Fundação do Backend

Esta feature **não cria entidades de negócio nem tabelas próprias**. As entidades do domínio (unidade,
categoria, atividade, programação e público-alvo) são modeladas nas features seguintes, de acordo com
`docs/03-modelo-de-dados.md`.

As únicas tabelas criadas ao aplicar as migrations são as do próprio Django para os recursos habilitados
agora (usuários, grupos, permissões, tipos de conteúdo e sessões). O modelo de usuário é o padrão do Django
(ver `research.md`, R6).

## Entidade de configuração: Configuração de ambiente

Não é persistida no banco. É o conjunto de valores externos ao código que definem como o backend roda em
cada máquina. Os detalhes completos estão em
[contracts/environment-variables.md](contracts/environment-variables.md).

| Grupo | Variáveis | Obrigatória |
|---|---|---|
| Aplicação | `DJANGO_SECRET_KEY` | Sim |
| Aplicação | `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS` | Não (têm padrão seguro) |
| Banco de dados | `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Sim |
| Banco de dados | `DB_SSLMODE`, `DB_SSLROOTCERT` | Não |
| Frontend | `CORS_ALLOWED_ORIGINS` | Não (vazia por padrão) |

### Regras de validação

- Toda variável obrigatória ausente ou vazia é reportada de uma vez, em uma única mensagem de erro, na
  inicialização.
- `DB_PORT` deve ser um número inteiro entre 1 e 65535.
- `DJANGO_DEBUG` aceita apenas valores booleanos; o padrão é desligado.
- `DB_SSLMODE` aceita os modos do PostgreSQL (`disable`, `allow`, `prefer`, `require`, `verify-ca`,
  `verify-full`); o padrão é `require`.
- Valores sensíveis (`DJANGO_SECRET_KEY`, `DB_PASSWORD`) nunca aparecem em mensagens de erro, logs ou saída
  de comandos.
