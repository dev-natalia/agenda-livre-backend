# Contrato: ausência de endpoints de Sobre e Contato

A API não publica endpoints para as páginas Sobre e Contato. O frontend deve implementá-las sem chamar o
backend.

## Respostas garantidas

Qualquer método HTTP enviado a um caminho inexistente sob `/api/`, inclusive caminhos plausíveis de contato
ou Sobre, recebe:

| Item | Valor |
|---|---|
| Status | `404` |
| Content-Type | `application/json` |
| Corpo | `{"detail": "Não encontrado."}` |
| Token CSRF | Não exigido (a resposta não depende dele) |
| Efeito colateral | Nenhum: nada é gravado no banco, nada do corpo da requisição é lido ou registrado |

### Caminhos de exemplo verificados

`/api/contact/`, `/api/contato/`, `/api/v1/contact/`, `/api/v1/contato/`, `/api/about/`, `/api/sobre/`,
`/api/v1/about/`, `/api/v1/sobre/` — com `GET` e `POST`.

## Perguntas de escopo (para o frontend)

| Pergunta | Resposta |
|---|---|
| Sobre e Contato têm endpoint? | Não. |
| O formulário de contato envia algo ao backend? | Não. É demonstrativo. |
| De onde vem o texto de Sobre? | Do próprio frontend (texto fixo). |

## Mudança de contrato

Adicionar qualquer endpoint desta família exige nova spec e emenda do DOC-05, do DOC-04 e desta nota.
