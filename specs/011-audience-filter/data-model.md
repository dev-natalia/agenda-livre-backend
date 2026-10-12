# Data Model: Filtro por Público-alvo

**Feature**: 011-audience-filter | **Date**: 2026-10-12

Nenhuma entidade nova. A feature amplia a entidade existente **Público-alvo** (`audiences.TargetAudience`)
com um campo. As demais tabelas, inclusive a de vínculo `ActivityTargetAudience`, não mudam.

## Público-alvo (campo novo)

| Campo | Tipo | Obrigatório | Padrão | Observações |
|-------|------|-------------|--------|-------------|
| `includes_everyone` | `BooleanField` | Sim | `False` | Rótulo “Abrange todos os públicos”. Indica que o público vale para qualquer pessoa (a opção “Todas as idades”). É o **único** critério da regra inclusiva do filtro. Nunca sai na API pública. |

`help_text` (Admin): “Marque se esta opção vale para todos os públicos (por exemplo, ‘Todas as idades’).
Quem filtra por qualquer outro público também vê as atividades desta opção.”

Campos que já existem e continuam iguais: `id`, `name`, `slug`, `description`, `is_active`, `created_at`,
`updated_at`.

### Regras

1. A marca começa desligada em todos os públicos existentes (padrão do campo).
2. Pode haver zero, um ou vários públicos marcados; nada impede mais de um e todos são tratados da mesma forma.
3. A marca vale mesmo que o público marcado esteja inativo: desativar preserva os vínculos (DOC-03), e a regra
   do filtro usa a marca dos públicos **vinculados** à atividade, ativos ou não.
4. Só um público **ativo** pode ser escolhido no filtro. Escolher um inativo (ou inexistente) devolve lista vazia.
5. Alterar a marca não altera nenhum vínculo nem nenhuma atividade.

## Regra do filtro (comportamento, não dado)

Entrada: o público escolhido `E` (ativo) e, para cada atividade publicada, o conjunto `P` dos seus públicos.

| Caso | A atividade entra quando |
|------|---------------------------|
| `E` não existe, ou está inativo | nunca (lista vazia) |
| `E.includes_everyone` é verdadeiro | `E ∈ P` |
| `E.includes_everyone` é falso | `E ∈ P` **ou** existe `p ∈ P` com `p.includes_everyone` verdadeiro |

- A atividade é examinada uma vez, então aparece no máximo uma vez, mesmo que `E ∈ P` e também haja um
  público marcado em `P`.
- Atividade sem nenhum público (`P` vazio) nunca entra em um filtro por público.
- O filtro se soma, pelo critério “E”, aos demais (`q`, `unit`, `category`, `neighborhood`, datas). A
  ordenação por próxima ocorrência e a paginação não mudam.

## Migration

`apps/audiences/migrations/0002_targetaudience_includes_everyone.py`: um único `AddField` (`BooleanField`,
`default=False`). Aditiva: as linhas existentes ficam com a marca desligada, sem perda de dados. Não há
migration de dados. Aplicar com `safe_migrate`. Depois, rodar `seed_catalog` marca “Todas as idades”.

## Carga inicial (`seed_catalog`)

| Situação do banco | Efeito |
|-------------------|--------|
| Sem os públicos | cria os cinco; “Todas as idades” já nasce com `includes_everyone=True` |
| Com os públicos, sem a marca | `update` marca “Todas as idades”; nada mais muda |
| Com a marca (própria ou do administrador em outro público) | nada muda; nenhuma marca é removida |

## Dados que a API devolve

| Recurso | Públicos-alvo |
|---------|----------------|
| `GET /activities/` (novo) | `target_audiences`: `[{"id", "name"}]`, ordenados por nome; `[]` sem públicos |
| `GET /activities/{id}/` (já existia) | `target_audiences`: igual; o texto livre `target_audience_notes` continua só aqui |
| `GET /audiences/` (novo) | `id`, `name`, `slug`, `description` (ou `null`), só dos ativos, por nome |

A marca `includes_everyone` e a situação `is_active` **não** são expostas.

## Visibilidade

Nada de novo é exposto: o filtro só enxerga atividades `PUBLISHED`, e o recurso de públicos só lista os
ativos. O Admin continua exigindo login e permissão.
