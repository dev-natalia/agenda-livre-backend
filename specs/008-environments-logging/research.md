# Research: Ambientes e Registro de Erros

Resultado da leitura do código existente (features 001 a 007) contra os FR da spec. Não restou nenhum
`NEEDS CLARIFICATION`.

## Estado atual por requisito

| FR | Estado hoje | Ação |
|---|---|---|
| FR-001 | `apps/core/exceptions.py` chama `logger.error(..., exc_info=...)`, mas não há `LOGGING`: o Django usa só o console. Nada persiste. | Arquivo rotativo |
| FR-002 | Nenhum mascaramento. Mensagens de exceção podem conter `password=...` ou `postgres://usuario:senha@host`. | `RedactingFormatter` |
| FR-003 | Variável ausente levanta `ImproperlyConfigured` em `settings.py` antes de qualquer log; `check_db` mostra a falha só no terminal. | Registrar antes de relançar |
| FR-004/005 | Inexistente. | Variáveis `LOG_*`; rotação |
| FR-006 | `django.request` registra 4xx em WARNING e 5xx em ERROR. | Nível mínimo do arquivo = ERROR |
| FR-007 | `logging` não levanta exceção ao falhar a gravação (imprime em `stderr`), mas criar o arquivo na inicialização pode falhar. | `delay=True` e fallback sem arquivo |
| FR-008 | Só `DJANGO_DEBUG` e `ALLOWED_HOSTS` variam. Não há `SECURE_*`, cookies seguros nem HSTS. | `DJANGO_HTTPS_ONLY` |
| FR-009 | `.env.example` e README já documentam as variáveis da feature 001; `.env` está no `.gitignore`. | Atualizar com as novas; teste de documentação |
| FR-010 | `settings_test.py` define variáveis fictícias e bloqueia o banco. Não há `LOGGING` nos testes. | Logs de teste só em `tmp_path` |
| FR-011 | DOC-04 já marca US-032/033 fora do escopo e US-034 "logging básico local apenas". DOC-08 seção 10 ainda descreve logs de forma genérica. | Ajustar texto |

## Decisões

### D1. `LOGGING` por função, em `config/logging_config.py`
- **Decision**: `build_logging(log_dir, level, max_bytes, backup_count, secrets)` devolve o dicionário
  `LOGGING`; `settings.py` apenas o chama com valores lidos do ambiente.
- **Rationale**: função pura é fácil de testar sem importar `settings` e sem tocar o disco.
- **Alternatives**: dicionário literal em `settings.py` (difícil de testar variações); biblioteca de
  logging estruturado (dependência nova, YAGNI).

### D2. Arquivo rotativo, nível ERROR, destino `logs/`
- **Decision**: `logging.handlers.RotatingFileHandler`, `delay=True`, `encoding="utf-8"`,
  padrões `LOG_MAX_BYTES=1048576` (1 MiB) e `LOG_BACKUP_COUNT=5`, nível `ERROR`, arquivo
  `logs/agenda-livre.log`. O diretório padrão `logs/` fica no `.gitignore`.
- **Rationale**: o teto de espaço é `max_bytes * (backups + 1)` = 6 MiB, o que atende SC-004; `ERROR`
  exclui os 4xx (que o Django registra em WARNING) e deixa só falhas inesperadas.
- **Alternatives**: `TimedRotatingFileHandler` (retenção por dias não limita o espaço); registrar
  WARNING também (polui com erros de cliente, contra FR-006).

### D3. Mascaramento no *formatter*, não no *filter*
- **Decision**: `RedactingFormatter(logging.Formatter)` formata o registro completo (mensagem e
  rastreamento) e só então aplica o mascaramento ao texto final.
- **Rationale**: um *filter* só vê `record.msg`/`args` e perderia o texto do rastreamento
  (`exc_text`), onde estão as mensagens de exceção. Mascarar a saída final cobre tudo.
- **O que é mascarado** (substituído por `***`):
  1. os **valores reais** de `DJANGO_SECRET_KEY` e `DB_PASSWORD` (passados a `build_logging`; ignora
     valores vazios ou com menos de 4 caracteres, para não mascarar texto comum);
  2. padrões `chave=valor` e `chave: valor` para `password`, `passwd`, `pwd`, `secret`, `token`,
     `api_key`, `authorization`, `cookie`, `set-cookie`, `sessionid`, `csrftoken` (sem diferenciar
     maiúsculas);
  3. credenciais em endereços (`esquema://usuario:senha@host` vira `esquema://usuario:***@host`).
- **Alternatives**: filtrar por nome de logger (não impede o vazamento em mensagens); desligar o
  rastreamento (perde o detalhe técnico exigido por FR-001).

### D4. Contexto da requisição: só método e caminho
- **Decision**: `apps/core/exceptions.py` já registra método e caminho, sem *query string*, cabeçalhos,
  cookies ou corpo. Mantém-se assim; o registro de erro não ganha novos campos de requisição.
- **Rationale**: *query string* pode carregar dados de busca; o caminho basta para investigar (SC-001).

### D5. Sem duplicidade desnecessária
- **Decision**: o arquivo é ligado aos *loggers* `apps`, `config` e `django.request`. Uma falha 500 de
  view DRF pode gerar duas linhas (a do handler, com rastreamento, e a do `django.request`, com o
  caminho). Aceito: a segunda é curta, e `django.request` é o único que registra falhas fora de views
  DRF (por exemplo, no `/admin/`).
- **Alternatives**: remover `django.request` (perderia erros do painel administrativo).

### D6. Falha ao gravar não afeta a requisição
- **Decision**: o `logging` da biblioteca padrão trata exceções de `emit()` com `handleError`, que
  escreve em `stderr` e não propaga. Para a criação do diretório e do arquivo na inicialização, o
  `build_logging` testa `os.makedirs(..., exist_ok=True)` e, se falhar, devolve a configuração só com
  o console e emite um aviso em `stderr`. `delay=True` adia a abertura do arquivo para o primeiro erro.
- **Rationale**: atende FR-007 sem tratamento extra em cada view.

### D7. Registro de falhas de inicialização
- **Decision**: em `settings.py`, `require_env` é envolvido por `try/except ImproperlyConfigured` que
  chama `log_startup_failure(exc)` e relança. Como o `LOGGING` ainda não existe nesse ponto,
  `log_startup_failure` abre o mesmo arquivo com `LOG_DIR` lido direto do ambiente (padrão `logs/`) e
  grava uma linha `ERROR` com a mensagem, que já contém só **nomes** de variáveis. Falhas de conexão:
  `check_db` e `safe_migrate` chamam `logger.error` com o tipo da exceção, `host` e `port`.
- **Rationale**: é a forma mais simples de cumprir FR-003; o erro de configuração acontece antes de o
  Django montar o `LOGGING`.
- **Alternatives**: aceitar que falha de inicialização só apareça no terminal (descumpre FR-003).

### D8. `DJANGO_HTTPS_ONLY` para as proteções do modo restritivo
- **Decision**: nova variável opcional, padrão `not DEBUG`. Quando verdadeira:
  `SECURE_SSL_REDIRECT=True`, `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`,
  `SECURE_HSTS_SECONDS=3600`. Sempre (qualquer modo): `SECURE_CONTENT_TYPE_NOSNIFF=True`,
  `X_FRAME_OPTIONS="DENY"`, `SESSION_COOKIE_HTTPONLY=True`, `SECURE_REFERRER_POLICY="same-origin"`.
- **Rationale**: com `DEBUG=False` por padrão, ligar as proteções por padrão é o comportamento seguro
  que o backlog pede ("variam de forma apropriada"). A variável existe porque o sistema roda apenas
  localmente, em HTTP: quem usar `DEBUG=False` sem HTTPS local precisa de `DJANGO_HTTPS_ONLY=False`,
  senão o login do painel não persiste (cookie seguro) e o navegador é redirecionado a HTTPS.
  O README documenta esse caso.
- **Alternatives**: ligar só quando `DEBUG=False` sem chave (quebra o uso local sem HTTPS, sem saída);
  nunca ligar (descumpre FR-008). `SECURE_PROXY_SSL_HEADER` não é definido: não há proxy e confiar
  num cabeçalho sem proxy seria inseguro.

### D9. Novas variáveis
| Variável | Obrigatória | Padrão | Descrição |
|---|---|---|---|
| `DJANGO_HTTPS_ONLY` | Não | `True` se `DJANGO_DEBUG=False`, senão `False` | Liga redirecionamento HTTPS, cookies seguros e HSTS |
| `LOG_DIR` | Não | `logs` (relativo à raiz do repositório) | Pasta dos registros de erro |
| `LOG_LEVEL` | Não | `ERROR` | Nível mínimo gravado (`WARNING`, `ERROR` ou `CRITICAL`) |
| `LOG_MAX_BYTES` | Não | `1048576` | Tamanho máximo de cada arquivo |
| `LOG_BACKUP_COUNT` | Não | `5` | Quantos arquivos antigos manter |

Valores inválidos (nível desconhecido, número não positivo) falham na inicialização com
`ImproperlyConfigured`, no mesmo estilo de `DB_PORT`, sem mostrar o valor recebido.

### D10. Teste de documentação das variáveis
- **Decision**: um teste confere que cada nome em `ALL_VARS` aparece no README e no `.env.example`.
- **Rationale**: transforma "toda variável documentada" (SC-005) em verificação automática.

### D11. Ambiente de testes
- **Decision**: `settings_test.py` define `LOG_DIR` para um diretório temporário do sistema antes de
  importar as settings, e os testes de logging usam `tmp_path`. Nenhum teste grava em `logs/`.
- **Rationale**: FR-010 e a borda "sem resíduos no repositório".
