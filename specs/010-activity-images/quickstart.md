# Quickstart: validar as imagens das atividades

**Feature**: 010-activity-images | Roteiro para provar, de ponta a ponta, que a feature funciona. Contratos:
[public-api-image.md](contracts/public-api-image.md) e [admin-image-upload.md](contracts/admin-image-upload.md).
Campos e regras: [data-model.md](data-model.md).

## Pré-requisitos

- Dependências instaladas: `pip install -r requirements-dev.txt` (inclui Pillow, django-storages e boto3).
- `.env` com as variáveis `DB_*` e as quatro `AWS_*` (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`,
  `AWS_STORAGE_BUCKET_NAME=agenda-livre-imagens`, `AWS_S3_REGION_NAME=sa-east-1`). Veja `.env.example`.
- Bucket `agenda-livre-imagens` com leitura pública só de objetos (política `s3:GetObject`, sem
  `s3:ListBucket` para o público) e usuário IAM da aplicação com `PutObject`, `GetObject`, `DeleteObject` no
  bucket e `ListBucket`. Detalhes em `docs/09-adicao-de-imagens.md`.
- Um administrador existente (`python manage.py create_admin <usuario>`).

## 1. Testes automatizados (sem banco, sem AWS)

```bash
python -m pytest
python -m ruff check .
python manage.py makemigrations --check --dry-run   # deve listar só a migration 0002 antes de aplicá-la
```

Esperado: todos os testes passam, a cobertura total é de pelo menos 90% e o linter não aponta problemas.

## 2. Aplicar a migration

```bash
python manage.py safe_migrate
```

Esperado: `activities.0002_activity_image` aplicada; as atividades existentes continuam intactas.

## 3. Cenários manuais (Django Admin e API)

Suba o servidor com `python manage.py runserver` e entre em `/admin/`.

| # | Passo | Resultado esperado |
|---|-------|--------------------|
| 1 | Editar uma atividade, enviar um JPEG de 3 MB com 3000×2000 px e texto alternativo; salvar | Salva. Ao reabrir, a pré-visualização aparece. |
| 2 | Consultar `GET /api/v1/activities/<id>/` da atividade publicada | `image.url` absoluta (`https://agenda-livre-imagens.s3.sa-east-1.amazonaws.com/activities/<uuid>.jpg`), `alt` e `decorative: false`. |
| 3 | Abrir `image.url` em janela anônima | A imagem carrega; o maior lado tem 1600 px; sem metadados. |
| 4 | Abrir `https://agenda-livre-imagens.s3.sa-east-1.amazonaws.com/` | `AccessDenied` (sem listagem). |
| 5 | Enviar um `.txt` renomeado para `.jpg` | Erro em "Imagem": "Envie uma imagem JPEG, PNG ou WebP." |
| 6 | Enviar uma imagem de 6 MB | Erro: "A imagem deve ter no máximo 5 MB." |
| 7 | Enviar uma imagem de 300×200 px | Erro: "A imagem deve ter pelo menos 400×300 pixels." |
| 8 | Enviar imagem sem texto alternativo e sem marcar decorativa | Erro em "Texto alternativo da imagem". |
| 9 | Preencher o texto alternativo **e** marcar decorativa | Erro em "Imagem decorativa". |
| 10 | Marcar só "Imagem decorativa" | Salva; a API devolve `alt: ""` e `decorative: true`. |
| 11 | Trocar a imagem por outra | A API mostra a nova URL; a URL antiga passa a dar erro (arquivo apagado). |
| 12 | Marcar "Limpar" e salvar | A API devolve `image: null`; o arquivo é apagado; alt e marca ficam vazios. |
| 13 | Consultar `GET /api/v1/activities/` | Todo item tem a chave `image` (objeto ou `null`); os campos antigos não mudaram. |
| 14 | Cancelar a atividade com imagem e consultar a listagem e o detalhe | Ela não aparece; nenhuma resposta traz a URL da imagem. |
| 15 | Atividade criada antes da feature | `image: null`, sem erro. |
| 16 | Excluir um rascunho com imagem | O arquivo é apagado do bucket. |

## 4. Dados de demonstração

```bash
python manage.py seed_demo
python manage.py seed_demo   # segunda execução
```

Esperado na primeira execução: parte das atividades recebe imagem fictícia (algumas decorativas, as demais
com texto alternativo) e outras ficam sem imagem. Na segunda: nenhuma atividade nova, nenhum arquivo novo
no bucket.

## 5. Verificação de segredos e logs

- `git status` não mostra `.env`; `.env.example` só tem valores de exemplo.
- Forçar uma falha de remoção (por exemplo, revogando temporariamente `DeleteObject`) e trocar uma imagem:
  a atividade é salva, e `logs/agenda-livre.log` registra o erro **sem** a chave de acesso.

## Critérios de pronto

Todos os cenários acima passam e os itens SC-001 a SC-010 da [spec](spec.md) estão atendidos.

## Resultado da verificação no ambiente real (2026-10-12)

Executada contra o RDS e o bucket `agenda-livre-imagens` (`sa-east-1`) reais, por script usando o cliente
de teste do Django (formulários do Admin e API pública) e `urllib` para as URLs do S3. Não foi feita pelo
navegador. Os dados de teste foram criados e apagados no próprio script.

- **Migration:** `activities.0002_activity_image` aplicada com `safe_migrate` (T041).
- **S3 (T024):** URL pública abre sem login com `image/jpeg` (200); a listagem do bucket é negada (403);
  depois de apagado, o arquivo deixa de abrir. As URLs saem no endereço regional
  (`https://agenda-livre-imagens.s3.sa-east-1.amazonaws.com/activities/<uuid>.<ext>`).
- **Cenários 1 a 16 (T042):** 28 de 28 verificações passaram, incluindo: rejeição de arquivo falso, grande,
  pequeno, sem alt e com alt + decorativa (nada é gravado); nome aleatório; lado maior 1600 px e sem EXIF;
  `image` no detalhe e na listagem; `image: null` sem imagem; decorativa com `alt: ""`; troca e limpeza
  apagando o arquivo antigo; alterar só o alt sem trocar o arquivo; atividade cancelada fora da API sem expor
  a URL; exclusão de rascunho apagando o arquivo.
- **`seed_demo`:** 1ª execução anexou 10 imagens; a 2ª anexou 0 (10 já existiam). Banco e bucket ficaram
  com 10 registros e 10 arquivos.
- **Correção encontrada na verificação:** a validação padrão do Django para `ImageField` barrava arquivos
  falsos com outra mensagem; o formulário passou a usar `FileField`, e agora só `process_image` valida. As
  URLs também passaram a usar o endereço regional do bucket (`custom_domain`).
- **Não verificado:** o cenário "falha do armazenamento no envio" (seção 5, revogar `DeleteObject`) só tem
  teste automatizado; a falha real do S3 não foi provocada.
