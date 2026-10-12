# Contrato: filtro por público-alvo na API pública

Base: `/api/v1/`. Este contrato **acrescenta** itens a `specs/006-public-consultation/contracts/public-api.md`
(e ao `specs/010-activity-images/contracts/public-api-image.md`); nenhum campo, parâmetro ou comportamento
existente muda. Erros seguem `specs/007-quality-security-accessibility/contracts/error-format.md`. Somente
`GET`; sem autenticação.

## 1. Parâmetro `audience` em `GET /api/v1/activities/`

| Parâmetro | Tipo | Regra |
|-----------|------|-------|
| `audience` | UUID | Opcional. Identificador de um público-alvo (de `GET /audiences/`). Um único valor. |

Exemplo: `GET /api/v1/activities/?audience=7c9e6679-7425-40de-944b-e07fc1f90ae7&unit=…&date_from=2026-11-01`

### Quais atividades voltam

| Público escolhido | Atividade entra quando |
|-------------------|------------------------|
| Um público específico (por exemplo, “Adultos”) | está associada a ele **ou** a um público marcado como “abrange todos” (por exemplo, “Todas as idades”) |
| Um público marcado como “abrange todos” | está associada a ele |
| Inexistente ou inativo | nunca: `200` com lista vazia |

- Cada atividade aparece **uma única vez**, e `count` e a paginação contam atividades distintas.
- Só atividades `PUBLISHED` entram; rascunho, cancelada e encerrada nunca aparecem.
- Atividade sem nenhum público-alvo nunca aparece em um filtro por público.
- A ordenação por próxima ocorrência e o envelope paginado não mudam.

### Combinação com outros filtros

`audience` se combina pelo critério “E” com `q`, `unit`, `category`, `neighborhood`, `date`, `date_from` e
`date_to`. As validações existentes (por exemplo, `date` junto de `date_from`) não mudam, e vários erros
continuam sendo reportados, cada um no seu campo.

### Erros

Identificador malformado:

```json
{ "detail": "Parâmetros inválidos.", "errors": { "audience": ["Informe um identificador válido."] } }
```

Status `400`. Identificador bem formado que não existe ou está inativo: `200` com
`{ "count": 0, "next": null, "previous": null, "results": [] }`. `audience=` vazio é tratado como
ausente (sem filtro), como `unit=` e `category=`. Parâmetro repetido (`audience=a&audience=b`): vale o
último valor, sem erro.

## 2. Campo `target_audiences` nos itens da listagem

Cada item de `results` de `GET /api/v1/activities/` passa a trazer:

```json
{
  "id": "…", "title": "Oficina de dança",
  "target_audiences": [
    { "id": "…", "name": "Adolescentes" },
    { "id": "…", "name": "Adultos" }
  ]
}
```

- Lista de objetos `{id, name}`, **ordenada por nome**; `[]` quando a atividade não tem público-alvo. O campo
  está sempre presente, nunca `null`.
- É o mesmo formato do detalhe (`GET /activities/{id}/`), que já trazia `target_audiences`. O detalhe passa a
  usar a mesma ordenação por nome.
- O texto livre `target_audience_notes` continua **somente** no detalhe.
- Mudança aditiva: `id`, `title`, `slug`, `summary`, `unit`, `category`, `next_occurrence` e `image` seguem
  como estão.

## 3. `GET /api/v1/audiences/`

Lista os públicos-alvo **ativos**, ordenados por nome, no mesmo envelope paginado de `/units/` e
`/categories/` (`page`, `page_size` com os mesmos padrão e limite).

```json
{
  "count": 5, "next": null, "previous": null,
  "results": [
    { "id": "…", "name": "Adolescentes", "slug": "adolescentes", "description": null },
    { "id": "…", "name": "Todas as idades", "slug": "todas-as-idades", "description": null }
  ]
}
```

| Campo | Tipo | Regra |
|-------|------|-------|
| `id` | UUID | Valor a enviar em `audience`. |
| `name` | texto | Nome para exibir. |
| `slug` | texto | Identificador textual. |
| `description` | texto ou `null` | `null` quando vazia. |

- Sem públicos ativos: `200` com `results: []`.
- Métodos de escrita (`POST`, `PUT`, `PATCH`, `DELETE`): `405` com `{"detail": "Método não permitido."}`.
- Não há `GET /audiences/{id}/` (como em `/units/` e `/categories/`).
- A resposta não traz `is_active`, a marca “abrange todos” nem dados de auditoria. O frontend não precisa saber
  qual opção é “Todas as idades”: a regra é aplicada no servidor.

## Garantias

- Nenhuma resposta contém atividade não publicada, dados de auditoria, contas ou informações pessoais.
- Sem `audience`, os resultados, a ordenação e a paginação são idênticos aos anteriores, exceto pela chave nova
  `target_audiences` em cada item.
- O número de consultas ao banco para montar a listagem não cresce com o número de atividades.

## Uso esperado pelo frontend

```text
1. GET /audiences/                       → montar o seletor (id para enviar, name para exibir)
2. escolher um público                   → GET /activities/?audience=<id> (+ demais filtros)
3. limpar o filtro                       → GET /activities/ sem audience
4. card: exibir item.target_audiences    → lista de nomes; vazia = não exibir
5. erro 400 em errors.audience           → o seletor enviou um valor que não vem de /audiences/
```

O tratamento no frontend (US-050) é feito no repositório do frontend.

## Compatibilidade

Mudança aditiva: um parâmetro opcional, uma chave nova nos itens da listagem e um recurso novo. Clientes que
ignoram o que não conhecem continuam funcionando.
