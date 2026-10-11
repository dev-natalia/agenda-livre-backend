# Data Model: Gestão de Atividades

Referência: `docs/03-modelo-de-dados.md` (seções 6 a 8 e 11 a 14). Chaves primárias são UUID.

## TargetAudience (`apps/audiences`, herda `CatalogModel`)

| Campo | Tipo | Regras |
|---|---|---|
| `id` | UUID | PK, gerado |
| `name` | texto (150) | obrigatório, sem espaços nas pontas |
| `slug` | slug (160) | único; gerado do nome se em branco |
| `description` | texto | opcional (vem da base) |
| `is_active` | booleano | padrão verdadeiro; inativa não é oferecida a novos vínculos |
| `created_at`, `updated_at` | data/hora | automáticos |

Nome no Admin: "Público-alvo" / "Públicos-alvo". Ordenação por nome.

## Activity (`apps/activities`)

| Campo | Tipo | Regras |
|---|---|---|
| `id` | UUID | PK, gerado |
| `unit` | FK `Unit` | obrigatório, `PROTECT` |
| `category` | FK `Category` | obrigatório, `PROTECT` |
| `title` | texto (200) | obrigatório, sem espaços nas pontas, não vazio |
| `slug` | slug (220) | único; gerado do título com sufixo `-2`, `-3`... em colisão; somente leitura |
| `summary` | texto (300) | opcional |
| `description` | texto | obrigatório, não vazio |
| `target_audience_notes` | texto | opcional |
| `external_registration_url` | URL | opcional; esquema `http` ou `https` |
| `status` | texto com opções | padrão `DRAFT`; somente leitura no formulário |
| `target_audiences` | M2M `TargetAudience` via `ActivityTargetAudience` | zero ou mais; ver regras |
| `created_by` | FK usuário | `PROTECT`, preenchido na criação, somente leitura |
| `updated_by` | FK usuário | `PROTECT`, preenchido a cada alteração, somente leitura |
| `created_at`, `updated_at` | data/hora | automáticos |

Nome no Admin: "Atividade" / "Atividades". Ordenação: mais recentemente atualizadas primeiro.

Índices: `slug` (único), `status`, (`unit`, `status`), (`category`, `status`).

Constante `PUBLIC_STATUSES = {PUBLISHED}` documenta a regra pública para a feature de consulta.

## ActivityTargetAudience (`apps/activities`)

| Campo | Tipo | Regras |
|---|---|---|
| `id` | UUID | PK |
| `activity` | FK `Activity` | `CASCADE` (a exclusão só ocorre para rascunhos) |
| `target_audience` | FK `TargetAudience` | `PROTECT` (desative a opção em vez de excluir) |

Restrição de unicidade: (`activity`, `target_audience`).

## Situações e transições

```text
        publicar              cancelar
DRAFT ───────────► PUBLISHED ───────────► CANCELLED
                     │  ▲                    │
            encerrar │  │ publicar           │ publicar
                     ▼  │                    │
                   FINISHED ◄────────────────┘ (via PUBLISHED)
```

| De | Para | Condição |
|---|---|---|
| `DRAFT` | `PUBLISHED` | regras de publicação (abaixo) |
| `PUBLISHED` | `CANCELLED` | nenhuma |
| `PUBLISHED` | `FINISHED` | nenhuma |
| `CANCELLED` | `PUBLISHED` | regras de publicação |
| `FINISHED` | `PUBLISHED` | regras de publicação |

Mesma situação pedida: sem efeito e sem erro. Demais transições: recusadas.

**Regras de publicação**: título e descrição não vazios; unidade e categoria ativas; ao menos um
vínculo de público-alvo.

Toda transição atualiza `status`, `updated_by` e `updated_at`.

## Integridade e exclusão

| Situação | Comportamento |
|---|---|
| Excluir unidade ou categoria com atividades | recusada (`PROTECT`); desativar |
| Excluir opção de público usada | recusada (`PROTECT`); desativar |
| Desativar unidade, categoria ou público | vínculos existentes preservados |
| Excluir atividade | permitida só em `DRAFT`; vínculos de público saem em cascata |
| Excluir conta com autoria | recusada (`PROTECT`); desativar a conta |
| Cancelar ou encerrar | dados preservados, só muda a situação |

## Validações

- `Activity.clean()`: remove espaços de título e descrição; recusa vazios; valida a URL.
- Inline de públicos: recusa a mesma opção duas vezes; se a atividade está `PUBLISHED`, recusa salvar sem
  nenhum público.
- Opções inativas ficam fora das listas, exceto o valor já vinculado à instância em edição (research 6).
