# Data Model: Ambientes e Registro de Erros

**Sem mudanças de esquema.** Nenhuma tabela, coluna, índice, constraint ou migration é criada ou
alterada. As duas entidades da spec não são persistidas no banco.

## Registro de erro (arquivo local)

Uma linha por ocorrência (mais o rastreamento, em linhas seguintes), em `logs/agenda-livre.log`.

| Campo | Origem | Regra |
|---|---|---|
| Horário | `asctime` | Fuso do projeto (`America/Sao_Paulo`) |
| Gravidade | `levelname` | `ERROR` ou `CRITICAL` por padrão |
| Origem | `name` | Nome do *logger* (`apps.core.exceptions`, `django.request`, `config.settings`, ...) |
| Mensagem | `message` | Texto fixo mais método e caminho; nunca *query string*, cabeçalhos, cookies ou corpo |
| Tipo da falha e rastreamento | `exc_info` | Presente nas falhas inesperadas |

Formato: `AAAA-MM-DD HH:MM:SS,mmm NÍVEL origem: mensagem`.

Invariantes:

- Nenhum valor de `DJANGO_SECRET_KEY` ou `DB_PASSWORD` aparece, em nenhum campo.
- Nenhum trecho `senha/token/cookie/autorização = valor` aparece sem mascaramento.
- O conjunto de arquivos nunca ultrapassa `LOG_MAX_BYTES * (LOG_BACKUP_COUNT + 1)`.
- Erros esperados de cliente (4xx) nunca entram.

## Configuração de ambiente

Conjunto de variáveis lidas por `config/env.py`. Estado final após esta feature:

| Variável | Obrigatória | Padrão | Validação |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | Sim | | Não vazia |
| `DJANGO_DEBUG` | Não | `False` | Booleana |
| `DJANGO_ALLOWED_HOSTS` | Não | `localhost,127.0.0.1` | Lista |
| `DJANGO_HTTPS_ONLY` | Não | `not DJANGO_DEBUG` | Booleana (nova) |
| `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD` | Sim | | `DB_PORT` entre 1 e 65535 |
| `DB_SSLMODE` | Não | `require` | Um dos modos do PostgreSQL |
| `DB_SSLROOTCERT` | Não | | Caminho |
| `CORS_ALLOWED_ORIGINS` | Não | vazio | Lista |
| `LOG_DIR` | Não | `logs` | Caminho (nova) |
| `LOG_LEVEL` | Não | `ERROR` | `WARNING`, `ERROR` ou `CRITICAL` (nova) |
| `LOG_MAX_BYTES` | Não | `1048576` | Inteiro positivo (nova) |
| `LOG_BACKUP_COUNT` | Não | `5` | Inteiro >= 0 (nova) |

## Transições

Não há estados. Comportamento por modo:

| Modo | `DEBUG` | `HTTPS_ONLY` (padrão) | Efeito |
|---|---|---|---|
| Desenvolvimento local | `True` | `False` | Sem redirecionamento nem cookies seguros |
| Restritivo | `False` | `True` | HTTPS obrigatório, cookies seguros, HSTS |
| Local sem HTTPS e `DEBUG=False` | `False` | `False` (explícito) | Usa HTTP; sem as proteções de transporte |
