# Contrato: formato de erros da API

Vale para todas as rotas sob `/api/v1/`. Resposta sempre JSON, em português, sem detalhes internos.

## Corpo

```json
{ "detail": "Parâmetros inválidos.", "errors": { "date": ["Informe uma data no formato AAAA-MM-DD."] } }
```

- `detail`: sempre presente.
- `errors`: só no 400 de validação; chave = nome do parâmetro, valor = lista de mensagens.
  Erro que não pertence a um campo usa a chave `non_field_errors`.

## Situações

| Situação | Status | `detail` | `errors` |
|---|---|---|---|
| Parâmetro malformado (data, UUID, tamanho, intervalo) | 400 | Parâmetros inválidos. | por campo |
| **Página inválida ou além da última** (novo) | 400 | Parâmetros inválidos. | `page`: "Informe uma página válida." |
| Atividade inexistente ou não publicada, ou identificador malformado | 404 | Não encontrado. | — |
| **Rota inexistente sob `/api/`** (novo: antes era página HTML) | 404 | Não encontrado. | — |
| Método de escrita em rota pública | 405 | Método não permitido. | — |
| `Accept` incompatível, corpo ou tipo de conteúdo inválidos | 4xx | mensagem da DRF em português | — |
| **Falha inesperada** (novo: antes era página HTML) | 500 | Ocorreu um erro inesperado. Tente novamente mais tarde. | — |

## Garantias

- Nenhuma resposta contém pilha de execução, caminho de arquivo, SQL, nome de variável de ambiente,
  valor de configuração ou segredo, com `DEBUG` ligado ou desligado.
- Atividade não publicada e identificador inexistente são indistinguíveis (mesmo status e corpo).
- Parâmetros de consulta desconhecidos são **ignorados** (decisão da feature 006) e não geram erro.
- Fora de `/api/` (por exemplo `/admin/`) valem as páginas padrão do Django.

## Mudança em relação à feature 006

Somente a paginação: `page` inválida passava a "404 Não encontrado."; agora é 400 com `errors.page`.
Os demais comportamentos da 006 permanecem.
