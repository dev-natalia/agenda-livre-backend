# Data Model: Imagens das Atividades

**Feature**: 010-activity-images | **Date**: 2026-10-12

Nenhuma entidade nova. A feature amplia a entidade existente **Atividade** (`activities.Activity`) com três
campos. As demais tabelas (unidades, categorias, públicos, programações) não mudam.

## Atividade (campos novos)

| Campo | Tipo | Obrigatório | Padrão | Observações |
|-------|------|-------------|--------|-------------|
| `image` | arquivo de imagem (`ImageField`), até 255 caracteres de caminho | não | vazio | Guarda só o nome do objeto no armazenamento (por exemplo `activities/3f2a....webp`). O arquivo não está no banco. |
| `image_alt` | texto, até 200 caracteres | não | vazio | Texto alternativo. Obrigatório quando há imagem e a imagem não é decorativa. |
| `image_decorative` | booleano | não | falso | Indica imagem decorativa (sem texto alternativo). |

Rótulos em português para o Admin: "Imagem", "Texto alternativo da imagem", "Imagem decorativa".

### Regras de validação (em `Activity.clean()` e no formulário do Admin)

1. Com imagem:
   - `image_alt` (após `strip()`) preenchido **e** `image_decorative` verdadeiro → erro em
     `image_decorative`: "Informe o texto alternativo ou marque a imagem como decorativa, não os dois.";
   - `image_alt` vazio **e** `image_decorative` falso → erro em `image_alt`: "Informe o texto
     alternativo da imagem ou marque-a como decorativa.";
   - `image_alt` com mais de 200 caracteres → erro padrão de tamanho do campo.
2. Sem imagem: `image_alt` passa a `""` e `image_decorative` a `False` (normalização, sem erro).
3. O texto alternativo só com espaços conta como vazio.
4. A imagem enviada passa por `process_image` (formato, tamanho, dimensões, tratamento); falhas viram erro
   em `image` com a mensagem do contrato [admin-image-upload.md](contracts/admin-image-upload.md).

Os campos de auditoria (`updated_by`, `updated_at`) já são atualizados em `save_model` e `save()`; trocar ou
remover a imagem passa por esse mesmo caminho (FR-014).

### Nome do arquivo guardado

`activities/<uuid4 sem hífens>.<ext>`, com `ext` em `jpg`, `png` ou `webp` conforme o formato **detectado**
após o tratamento. O nome enviado pela pessoa nunca é usado (FR-008). Dois envios da mesma imagem geram dois
nomes diferentes.

## Migration

`apps/activities/migrations/0002_activity_image.py`: três `AddField` (`image` com `blank=True` e
`upload_to` apontando para a função do modelo, `image_alt` com `blank=True` e `default=""`,
`image_decorative` com `default=False`). É aditiva: as linhas existentes ficam com imagem vazia, alt vazio e
decorativa falsa, e a API devolve `image: null` para elas. Não requer migração de dados. Aplicar com
`safe_migrate`, que já protege o banco compartilhado.

## Ciclo de vida do arquivo

```text
sem imagem ──envio válido──▶ com imagem ──troca válida──▶ com imagem (arquivo novo)
     ▲                            │                              │
     │                            ├─ remoção ─────────────────────┤
     └────────────────────────────┴──────────────◀───────────────┘
                                  │
                           exclusão da atividade
```

| Evento | Banco | Armazenamento |
|--------|-------|---------------|
| Envio inicial | grava a referência | grava o arquivo tratado |
| Troca | grava a nova referência | grava o novo; **depois do commit** apaga o antigo |
| Remoção (marcar "limpar") | zera a referência, o alt e a marca | **depois do commit** apaga o antigo |
| Exclusão da atividade (só rascunho no Admin) | apaga a linha | **depois do commit** apaga o arquivo |
| Só o alt ou a marca mudam | atualiza o campo | nada |
| Falha ao apagar | operação principal concluída | arquivo permanece; erro no log local, sem credenciais |

## Visibilidade

A imagem acompanha a atividade: só atividades `PUBLISHED` aparecem na API pública, e portanto só delas o
endereço da imagem é divulgado (FR-012). Nada novo é exposto: não saem o nome interno do objeto separado da
URL, o nome original do arquivo nem dados de quem enviou.
