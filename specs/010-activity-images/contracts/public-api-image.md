# Contrato: campo `image` na API pública

Base: `/api/v1/`. Este contrato **acrescenta** um campo às respostas de
`specs/006-public-consultation/contracts/public-api.md`; nenhum campo existente muda de nome, tipo ou
significado, e nenhum parâmetro novo é aceito. O formato de erros é o de
`specs/007-quality-security-accessibility/contracts/error-format.md`.

## Onde aparece

- `GET /api/v1/activities/`: em cada item de `results`.
- `GET /api/v1/activities/{id}/`: no objeto da atividade.

Somente atividades `PUBLISHED` são devolvidas por esses endpoints; portanto, só delas o endereço da imagem
é divulgado.

## Formato

Com imagem:

```json
{
  "id": "6b0f2a3e-...",
  "title": "Capoeira para todas as idades",
  "image": {
    "url": "https://agenda-livre-imagens.s3.sa-east-1.amazonaws.com/activities/3f2a9c1e5b7d4e0f8a6b2c4d1e9f7a30.webp",
    "alt": "Roda de capoeira com instrumentos ao centro",
    "decorative": false
  }
}
```

Imagem decorativa:

```json
{ "image": { "url": "https://.../activities/....jpg", "alt": "", "decorative": true } }
```

Sem imagem:

```json
{ "image": null }
```

## Campos de `image`

| Campo | Tipo | Regra |
|-------|------|-------|
| `url` | texto | Endereço absoluto, público e permanente da imagem tratada (lado maior até 1600 px, sem metadados). Nunca é caminho de arquivo do servidor. |
| `alt` | texto | Texto alternativo, até 200 caracteres. `""` quando `decorative` é `true`. |
| `decorative` | booleano | `true` quando a imagem é puramente decorativa; o frontend deve exibi-la com `alt=""`. |

`image` é `null` quando a atividade não tem imagem. O campo está sempre presente (nunca omitido).

## Garantias

- `alt` e `decorative` nunca são ambos preenchidos: ou há texto alternativo, ou a imagem é decorativa.
- A resposta não contém o nome original do arquivo, o caminho interno do armazenamento, o bucket
  separado da URL nem dados de quem enviou a imagem.
- A URL não é previsível nem relacionada ao título ou ao identificador da atividade, e o armazenamento não
  permite listar os arquivos.
- Atividades `DRAFT`, `CANCELLED` ou `FINISHED` não aparecem na API pública; logo, a URL da imagem delas
  não é divulgada.
- Indisponibilidade do armazenamento não afeta estas respostas: a API só devolve o endereço e não acessa
  o arquivo.
- Limitação conhecida: quem já conhecia a URL de uma imagem continua a acessá-la enquanto o arquivo
  existir, mesmo que a atividade deixe de estar publicada. O arquivo é removido quando a imagem é trocada
  ou removida ou quando a atividade é excluída.

## Uso esperado pelo frontend

```text
se atividade.image é null  → exibir o fallback visual
senão se image.decorative  → <img src=url alt="">
senão                      → <img src=url alt=image.alt>
se a imagem falhar ao carregar → exibir o fallback visual
```

O tratamento no frontend (US-043) é feito no repositório do frontend.

## Compatibilidade

Mudança aditiva. Clientes que ignoram campos desconhecidos continuam funcionando; os campos `id`, `title`,
`slug`, `summary`, `unit`, `category`, `next_occurrence` (listagem) e todos os do detalhe permanecem como
estão.
