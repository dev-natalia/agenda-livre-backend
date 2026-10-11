# Contrato: configuração por ambiente

Interface exposta à pessoa desenvolvedora: variáveis de ambiente (arquivo `.env`, não versionado) e o
efeito de cada uma. A tabela completa e os valores padrão estão em [data-model.md](../data-model.md).

## Regras

1. Valores sensíveis só vêm do ambiente; nada sensível é versionado. `.env.example` traz só valores
   fictícios.
2. Variável obrigatória ausente: a aplicação não inicia e a mensagem lista os **nomes** ausentes
   (sem valores). O evento é registrado em `logs/` (ver [logging.md](logging.md)).
3. Variável opcional inválida: a aplicação não inicia, com mensagem que cita o nome da variável e a
   regra, nunca o valor recebido.
4. Toda variável lida pelo código consta no README e no `.env.example` (verificado por teste).

## Segurança por modo

| Configuração | Desenvolvimento (`DJANGO_DEBUG=True`) | Restritivo (`DJANGO_DEBUG=False`) |
|---|---|---|
| `DJANGO_HTTPS_ONLY` (padrão) | `False` | `True` |
| Redirecionar HTTP para HTTPS | Não | Sim |
| Cookies de sessão e CSRF só por HTTPS | Não | Sim |
| HSTS | Não | `3600` segundos |
| `nosniff`, `X-Frame-Options: DENY`, cookie de sessão HttpOnly, política de referência | Sim | Sim |

**Uso local sem HTTPS com `DEBUG=False`:** defina `DJANGO_HTTPS_ONLY=False`. Sem isso, o navegador é
redirecionado a HTTPS e o login do painel não persiste, porque o cookie seguro não é enviado por HTTP.

## Ambiente de testes

- `config/settings_test.py` define variáveis fictícias, bloqueia o banco e aponta `LOG_DIR` para um
  diretório temporário.
- Nenhum dado real e nenhuma conexão de rede ou de banco são usados.
