# Contrato: registro de erros

Interface exposta à pessoa responsável pela manutenção. Não há endpoint; o contrato é o arquivo e o
comportamento de gravação.

## Local e formato

- Arquivo: `<LOG_DIR>/agenda-livre.log` (padrão `logs/agenda-livre.log`, na raiz do repositório, fora do
  controle de versão). Codificação UTF-8.
- Linha: `2026-10-11 14:03:22,481 ERROR apps.core.exceptions: Erro inesperado em GET /api/v1/activities/`
  seguida do rastreamento técnico, quando houver.
- Rotação: ao atingir `LOG_MAX_BYTES`, o arquivo vira `agenda-livre.log.1`, `.2`, ... até
  `LOG_BACKUP_COUNT`; o mais antigo é descartado.

## O que é gravado

| Evento | Nível | Conteúdo |
|---|---|---|
| Falha inesperada em requisição (DRF) | ERROR | Método, caminho e rastreamento |
| Falha 5xx fora de view DRF (ex.: `/admin/`) | ERROR | Linha de `django.request` e rastreamento |
| Variável de ambiente ausente ou inválida na inicialização | ERROR | Mensagem com **nomes** das variáveis |
| Falha de conexão em `check_db` / `safe_migrate` | ERROR | Tipo da exceção, host e porta |

## O que nunca é gravado

- Erros esperados de cliente: validação (400), não autenticado/negado (401/403), não encontrado (404),
  método não permitido (405).
- Valores de `DJANGO_SECRET_KEY` e `DB_PASSWORD`; senhas, tokens, cookies e cabeçalhos de autorização
  (substituídos por `***`); senha dentro de endereço de conexão.
- Corpo de requisição, *query string* e dados de visitantes.

## Garantias de comportamento

- A resposta ao visitante não muda: continua `{"detail": "Ocorreu um erro inesperado. Tente novamente mais tarde."}`
  com status 500 (contrato da feature 007).
- Se o arquivo não puder ser criado ou gravado, a aplicação continua atendendo; o aviso vai para o
  terminal.
- A auditoria de conteúdo (quem alterou o quê) continua nos campos de auditoria (feature 007); este
  registro não a duplica.

## Como consultar

```bash
tail -n 50 logs/agenda-livre.log            # Git Bash / Linux / macOS
Get-Content logs\agenda-livre.log -Tail 50  # PowerShell
```
