---

description: "Lista de tarefas de Imagens das Atividades"
---

# Tasks: Imagens das Atividades

**Input**: Documentos de design em `/specs/010-activity-images/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/, quickstart.md

**Tests**: Incluídos. A constituição (Princípio III) exige testes unitários com mocks, sem acesso a banco, e
cobertura total mínima de 90%. Em cada história, os testes são escritos antes do código e devem falhar
(red) antes de passar (green). Nenhum teste fala com a AWS: o armazenamento é `InMemoryStorage`, e as
imagens de teste são geradas em memória com Pillow.

**Organization**: Tarefas agrupadas por história de usuário (US1 a US6 da spec). A **US2 (validação e
tratamento) vem antes da US1 (anexar pelo Admin)** porque o formulário da US1 chama o tratamento da US2;
as duas são P1. Há uma migration aditiva (`0002`), três dependências novas e nenhuma rota nova.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: pode rodar em paralelo (arquivos diferentes, sem dependência de tarefa incompleta)
- **[Story]**: história de usuário à qual a tarefa pertence (US1 a US6)
- Os caminhos são relativos à raiz do repositório

## Path Conventions

Projeto único com o Django na raiz: `config/`, `apps/` e `tests/unit/<área>/`. Os diretórios de teste **não
têm `__init__.py`**, então o nome de cada arquivo de teste precisa ser único em toda a suíte; os nomes
abaixo já são únicos. Mensagens em português. Linha de código com no máximo 100 caracteres (ruff). Python do
projeto: `.venv/Scripts/python.exe` (`python -m pytest`). Nunca ler nem imprimir o `.env`.

---

## Phase 1: Setup

- [X] T001 Rodar `python -m pytest`, `python -m ruff check .` e `python manage.py makemigrations --check --dry-run` para registrar a linha de base (suíte verde, cobertura >= 90%, "No changes detected") antes de qualquer alteração
- [X] T002 Em `requirements.txt`, acrescentar as dependências fixadas `Pillow==12.3.0`, `django-storages[s3]==1.14.6` e `boto3==1.43.111`, mantendo a ordem e o estilo das linhas existentes
- [X] T003 Instalar com `pip install -r requirements-dev.txt` e confirmar que `python -c "import PIL, storages, boto3"` funciona sem erro

---

## Phase 2: Foundational (bloqueia todas as histórias)

**Purpose**: configuração do armazenamento e campos do modelo, usados por todas as histórias.

**⚠️ CRITICAL**: nenhuma história pode começar antes de esta fase terminar.

### Variáveis de ambiente e armazenamento

- [X] T004 [P] Em `tests/unit/config/test_storage_settings.py`, escrever testes (red) de `config.storage.build_storages(options)`: o backend padrão é `storages.backends.s3.S3Storage`; `OPTIONS` tem `bucket_name`, `region_name`, `access_key`, `secret_key` vindos do argumento; `querystring_auth` é `False`; `file_overwrite` é `True`; `default_acl` é `None`; não há `custom_domain`; o backend `staticfiles` continua `django.contrib.staticfiles.storage.StaticFilesStorage`; o teste não importa `boto3`
- [X] T005 Criar `config/storage.py` com `build_storages(options)` conforme research.md seção 1 (recebe um dicionário com as quatro variáveis, devolve o dicionário `STORAGES`); fazer os testes de T004 passarem
- [X] T006 Em `config/env.py`, acrescentar `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME` e `AWS_S3_REGION_NAME` a `REQUIRED_VARS` (a mensagem de `require_env` não pode mostrar valores)
- [X] T006a Em `README.md`, documentar cada variável `AWS_*` entre crases (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME`) na tabela de variáveis de ambiente, e conferir que `.env.example` tem cada uma como `NOME=`; sem isso `tests/unit/config/test_env_documentation.py` fica vermelho assim que T006 for feito
- [X] T007 [P] Em `tests/conftest.py`, acrescentar as quatro variáveis `AWS_*` fictícias à fixture `valid_env`; em `tests/unit/config/test_env.py`, ajustar os testes que enumeram as variáveis ausentes e acrescentar um caso com `AWS_STORAGE_BUCKET_NAME` em branco tratado como ausente
- [X] T008 Em `config/settings.py`, definir `STORAGES = build_storages({...})` com as quatro variáveis lidas de `_required` e passar `_required["AWS_SECRET_ACCESS_KEY"]` na tupla de segredos de `build_logging` (mascaramento no log)
- [X] T009 Em `config/settings_test.py`, acrescentar as quatro variáveis `AWS_*` fictícias em `_FAKE_ENV` e, depois do `import *`, definir `STORAGES["default"] = {"BACKEND": "django.core.files.storage.InMemoryStorage"}` e `MEDIA_URL = "http://testserver/media/"`; confirmar que `python -m pytest` continua verde

### Modelo e migration

- [X] T010 [P] Em `tests/unit/activities/test_activity_image_model.py`, escrever testes (red) com instâncias sem salvar: `upload_to` devolve `activities/<32 hex>.<ext>` ignorando o nome enviado (com `../x.jpg` e acentos), dois resultados para o mesmo nome diferem; com imagem e `image_alt` preenchido, `clean()` passa; com imagem sem alt e sem decorativa, `clean()` levanta erro em `image_alt` ("Informe o texto alternativo da imagem ou marque-a como decorativa."); com imagem, alt e decorativa juntos, erro em `image_decorative` ("Informe o texto alternativo ou marque a imagem como decorativa, não os dois."); alt só com espaços conta como vazio; com imagem e `image_decorative=True`, `clean()` passa e `image_alt` fica `""`; sem imagem, `clean()` zera `image_alt` e `image_decorative` sem erro; `image_alt` com 201 caracteres falha em `full_clean` (limite de `max_length=200`)
- [X] T011 Em `apps/activities/models.py`, acrescentar a função `activity_image_path(instance, filename)` (devolve `activities/<uuid4().hex>.<extensão em minúsculas da última parte do nome, restrita a jpg, jpeg, png ou webp; qualquer outra vira jpg>`) e os campos `image = models.ImageField("Imagem", upload_to=activity_image_path, max_length=255, blank=True)`, `image_alt = models.CharField("Texto alternativo da imagem", max_length=200, blank=True)` e `image_decorative = models.BooleanField("Imagem decorativa", default=False)`; estender `Activity.clean()` com as regras de data-model.md (validar antes de gerar o slug, na mesma estrutura de `errors`); fazer os testes de T010 passarem
- [X] T012 Gerar a migration com `python manage.py makemigrations activities -n activity_image` e conferir que `apps/activities/migrations/0002_activity_image.py` só tem três `AddField` (`image`, `image_alt`, `image_decorative`); `python manage.py makemigrations --check --dry-run` deve dizer "No changes detected" em seguida. **Não rodar `safe_migrate` aqui** (ver T052)

**Checkpoint**: configuração de armazenamento, campos e regras do modelo prontos e testados.

---

## Phase 3: User Story 2 - Somente imagens válidas e acessíveis são aceitas (Priority: P1) 🎯

**Goal**: validar e tratar o arquivo enviado (formato, tamanho, dimensões, redução, sem metadados).

**Independent Test**: chamar `process_image` com arquivos de tipo errado, corrompidos, grandes, pequenos e
uma imagem válida com EXIF; só a última passa, e a saída não tem EXIF.

### Tests for User Story 2

- [X] T013 [P] [US2] Em `tests/unit/activities/test_image_processing.py`, escrever testes (red) de `apps.activities.images.process_image(uploaded)` com imagens geradas em memória pelo Pillow: JPEG, PNG e WebP válidos passam e mantêm o formato; arquivo de texto com extensão `.jpg` falha com "Envie uma imagem JPEG, PNG ou WebP."; GIF e BMP falham com a mesma mensagem; bytes truncados falham com "Não foi possível ler a imagem. Envie outro arquivo."; arquivo de 5 MB exatos passa e 5 MB + 1 byte falha com "A imagem deve ter no máximo 5 MB." (sem abrir o arquivo); 400×300 passa e 399×300 e 400×299 falham com "A imagem deve ter pelo menos 400×300 pixels."; 6000×6000 passa e 6001×6000 falha com "A imagem deve ter no máximo 6000×6000 pixels." (checar pelo cabeçalho, sem decodificar tudo: usar `patch` em `Image.Image.load` para provar); imagem 3200×2000 sai com lado maior 1600 e proporção mantida; imagem 1000×700 sai sem ampliação; imagem de 1600 px exatos não muda de tamanho; JPEG com EXIF (GPS e orientação 6) sai sem nenhum EXIF e com a orientação visual aplicada (largura e altura trocadas); PNG com transparência mantém o canal alfa; `Image.DecompressionBombError` vira a mensagem de arquivo ilegível; a função devolve `(ContentFile, extensão)` com extensão `jpg`, `png` ou `webp`

### Implementation for User Story 2

- [X] T014 [US2] Criar `apps/activities/images.py` com as constantes `MAX_BYTES = 5 * 1024 * 1024`, `MIN_SIZE = (400, 300)`, `MAX_SIZE = (6000, 6000)`, `OUTPUT_MAX_SIDE = 1600` e `ALLOWED_FORMATS = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}`, e a função `process_image(uploaded)` seguindo research.md seção 3 (tamanho do arquivo, abrir, formato, dimensões pelo cabeçalho, decodificar, `ImageOps.exif_transpose`, `thumbnail((1600, 1600))`, regravar sem EXIF: JPEG qualidade 85 com `optimize`, PNG com `optimize`, WebP qualidade 85); levanta `django.core.exceptions.ValidationError` com as mensagens do contrato `contracts/admin-image-upload.md`; fazer os testes de T013 passarem

**Checkpoint**: o tratamento de imagem funciona sozinho, sem Admin e sem armazenamento.

---

## Phase 4: User Story 1 - Administrador anexa uma imagem à atividade (Priority: P1) 🎯 MVP

**Goal**: enviar, trocar e remover a imagem no formulário da atividade do Admin, com pré-visualização.

**Independent Test**: o formulário aceita uma imagem válida com alt, rejeita as combinações inválidas e a
atividade sem imagem continua válida; o Admin mostra os campos e a pré-visualização.

**Depende de**: US2 (T014).

### Tests for User Story 1

- [X] T015 [P] [US1] Em `tests/unit/activities/test_image_admin_form.py`, escrever testes (red) de `ActivityAdminForm`: `clean_image` chama `process_image` apenas quando o valor é um `UploadedFile` novo (não reprocessa quando só o alt muda nem quando o valor é o arquivo atual) e devolve o arquivo tratado; erro de `process_image` aparece em `form.errors["image"]`; o formulário expõe `image`, `image_alt` e `image_decorative`; sem imagem, o formulário é válido; o `ClearableFileInput` de `image` tem a caixa "Limpar" (campo não obrigatório)
- [X] T016 [P] [US1] Em `tests/unit/activities/test_image_admin.py`, escrever testes (red) de `ActivityAdmin`: `fields` contém `image`, `image_preview`, `image_alt`, `image_decorative` depois de `external_registration_url` e antes de `status`; `image_preview` está em `readonly_fields`; `image_preview(obj)` devolve HTML com `<img>` limitado a uma largura máxima e `alt` correto quando há imagem, e "Sem imagem." quando não há ou quando `obj` é novo; `form` é `ActivityAdminForm`; `save_model` continua gravando `created_by`/`updated_by` ao enviar a imagem; `changeform_view` com falha do armazenamento simulada (a view base levanta `botocore.exceptions.ClientError`, e também um `OSError`, em testes separados) em requisição `POST` com `image` em `request.FILES` registra o erro no log, exibe a mensagem "Não foi possível guardar a imagem agora. Tente novamente." e redireciona de volta, sem expor detalhes; sem `image` em `request.FILES`, a exceção propaga normalmente; um `ValidationError` levantado pela view base não é capturado; trocar a imagem e limpar a imagem (`"image" in form.changed_data`) atualizam `updated_by` e `updated_at` da atividade (FR-014)

### Implementation for User Story 1

- [X] T017 [US1] Criar `apps/activities/forms.py` com `ActivityAdminForm(forms.ModelForm)`: `Meta.model = Activity`, `fields = "__all__"`; `clean_image` chama `images.process_image` somente quando o valor é `UploadedFile`, devolve um `ContentFile` com o nome `"imagem." + extensão` (o nome definitivo vem de `upload_to`) e converte `ValidationError` em erro do campo; fazer os testes de T015 passarem
- [X] T018 [US1] Em `apps/activities/admin.py`, usar `form = ActivityAdminForm`, incluir `image`, `image_preview`, `image_alt` e `image_decorative` em `fields` (posição de T016) e `image_preview` em `readonly_fields`; implementar `image_preview` com `format_html` (`<img src="{}" alt="" style="max-width:240px;height:auto">`); sobrescrever `changeform_view` conforme T016: capturar `Exception` somente quando `request.method == "POST"` e `"image" in request.FILES`, deixando passar `ValidationError`, `PermissionDenied` e `Http404`, usando um `logger = logging.getLogger(__name__)` e `logger.error(...)` sem credenciais e sem `exc_info`; fazer os testes de T016 passarem e manter os de `tests/unit/activities/test_activity_admin.py` verdes (ajustar a lista esperada de `fields` ali)

**Checkpoint**: um administrador consegue anexar, trocar e remover a imagem (a limpeza do arquivo antigo vem
na US5). MVP: US2 + US1.

---

## Phase 5: User Story 3 - Visitante recebe os dados da imagem na consulta pública (Priority: P1)

**Goal**: o campo `image` nas respostas públicas de listagem e detalhe.

**Independent Test**: serializar atividades com e sem imagem e conferir o formato do contrato
`contracts/public-api-image.md`.

### Tests for User Story 3

- [X] T019 [P] [US3] Em `tests/unit/consultation/test_image_field.py`, escrever testes (red) de `image_payload(activity)` e dos dois serializers: sem imagem devolve `None` e a chave `image` existe com valor `None` na listagem e no detalhe; com imagem devolve `{"url": ..., "alt": ..., "decorative": False}` com `url` absoluta (`InMemoryStorage` com `MEDIA_URL = "http://testserver/media/"` de T009) e sem nenhuma chave extra; decorativa devolve `alt == ""` e `decorative is True`; a resposta não contém `name` nem o caminho do campo; os campos já existentes da listagem e do detalhe continuam idênticos (comparar o conjunto de chaves anterior mais `image`); a view de detalhe e a de listagem existentes continuam respondendo 404/200 como antes (reaproveitar as fixtures de `tests/unit/consultation/test_views.py`); o detalhe de uma atividade em rascunho, cancelada ou encerrada que tem imagem continua devolvendo 404 sem a URL, e a listagem não a inclui (FR-012)

### Implementation for User Story 3

- [X] T020 [US3] Em `apps/consultation/serializers.py`, criar `image_payload(activity)` (research.md seção 6), incluir `"image": image_payload(activity)` no dicionário de `ActivityListItemSerializer.to_representation` e `image = serializers.SerializerMethodField()` com `get_image` no `ActivityDetailSerializer`; fazer os testes de T019 passarem
- [X] T021 [US3] Em `specs/006-public-consultation/contracts/public-api.md`, acrescentar nas seções da listagem e do detalhe a linha do campo `image` com referência a `specs/010-activity-images/contracts/public-api-image.md`

**Checkpoint**: a API pública entrega o campo `image`; US1 + US2 + US3 completam o fluxo ponta a ponta.

---

## Phase 6: User Story 4 - A imagem carrega de forma confiável para qualquer visitante (Priority: P2)

**Goal**: URLs públicas, permanentes, não previsíveis e sem listagem do bucket.

**Independent Test**: a configuração gera URLs sem assinatura; o nome do arquivo é aleatório; o bucket
nega listagem (verificação manual).

### Tests for User Story 4

- [X] T022 [P] [US4] Em `tests/unit/config/test_storage_settings.py` (arquivo de T004), acrescentar testes: nenhuma opção de `build_storages` ativa URL assinada (`querystring_auth` é `False`); `STORAGES["default"]["OPTIONS"]` não contém `custom_domain`; e, em `tests/unit/activities/test_activity_image_model.py` (arquivo de T010), um teste que gera 1000 nomes com `activity_image_path` e confirma que todos são distintos, sem relação com o nome enviado nem com o `id` da atividade

### Implementation for User Story 4

- [X] T023 [US4] Em `README.md`, documentar a política de bucket de leitura pública (`s3:GetObject` em `arn:aws:s3:::agenda-livre-imagens/*`, sem `s3:ListBucket` público) e o usuário IAM da aplicação (`PutObject`, `GetObject`, `DeleteObject` em `agenda-livre-imagens/*` e `ListBucket` no bucket), copiando os JSON de `docs/09-adicao-de-imagens.md`; documentar também as dependências novas (Pillow, django-storages, boto3). As variáveis `AWS_*` já foram documentadas no T006a
- [X] T024 [US4] (depois do T041, que aplica a migration no RDS) Executar manualmente os cenários 3 e 4 de `quickstart.md` contra o bucket real (URL da imagem abre em janela anônima; a URL do bucket sem arquivo dá `AccessDenied`) e registrar o resultado no fim de `specs/010-activity-images/quickstart.md`. Exige as credenciais da pessoa responsável: **não executar sem ela**

**Checkpoint**: o acesso público e a ausência de listagem estão configurados, documentados e verificados.

---

## Phase 7: User Story 5 - Arquivos não ficam órfãos (Priority: P2)

**Goal**: apagar o arquivo antigo na troca, na remoção e na exclusão, sem quebrar a operação principal.

**Independent Test**: com armazenamento simulado, trocar, remover e excluir; o arquivo antigo é apagado só
após o commit, e uma falha do armazenamento vira log sem impedir o salvamento.

### Tests for User Story 5

- [X] T025 [P] [US5] Em `tests/unit/activities/test_image_cleanup.py`, escrever testes (red): `delete_stored_file(name)` chama `default_storage.delete(name)` e ignora nome vazio; quando o armazenamento levanta qualquer exceção, a função não propaga, registra `logger.error` (usar `caplog`) com o nome do arquivo e sem credenciais, e o texto do log não contém a chave secreta; o `RedactingFormatter` configurado em `config/settings.py` mascara `AWS_SECRET_ACCESS_KEY` (estender `tests/unit/core/test_no_secret_in_logs.py` com esse caso); `ActivityAdmin.save_model` com `form.changed_data` contendo `image` e arquivo anterior agenda a remoção do antigo com `transaction.on_commit` (executar o callback no teste) tanto na troca quanto na remoção; sem `image` em `changed_data` nada é agendado; atividade nova (sem arquivo anterior) não agenda nada; o sinal `post_delete` agenda a remoção do arquivo da atividade excluída e não faz nada quando não havia imagem; `ActivitiesConfig.ready` registra os sinais (importar `apps.activities.signals`)

### Implementation for User Story 5

- [X] T026 [US5] Em `apps/activities/images.py`, acrescentar `delete_stored_file(name)` (research.md seção 5) usando `logging.getLogger(__name__)`; fazer os testes de T025 de `delete_stored_file` passarem
- [X] T027 [US5] Criar `apps/activities/signals.py` com `post_delete` de `Activity` que agenda `delete_stored_file(instance.image.name)` via `transaction.on_commit`; em `apps/activities/apps.py`, importar o módulo em `ready()`
- [X] T028 [US5] Em `apps/activities/admin.py`, em `ActivityAdmin.save_model`, depois de gravar, quando `"image" in form.changed_data` e o valor inicial do formulário (`form.initial.get("image")`) tiver nome, agendar `delete_stored_file` do nome antigo com `transaction.on_commit`; fazer todos os testes de T025 passarem

**Checkpoint**: nenhum arquivo substituído, removido ou de atividade excluída permanece no bucket (salvo falha registrada).

---

## Phase 8: User Story 6 - Dados de demonstração incluem imagens (Priority: P3)

**Goal**: `seed_demo` associa imagens fictícias a parte das atividades, sem duplicar.

**Independent Test**: com ORM e armazenamento simulados, rodar o comando duas vezes; as imagens são anexadas
uma vez, algumas atividades ficam sem imagem.

### Tests for User Story 6

- [X] T029 [P] [US6] Em `tests/unit/core/test_seed_demo_images.py`, escrever testes (red) e **ler antes `tests/unit/core/test_seed_demo.py` (já existente)**, que também precisa continuar verde: `build_demo_image(seed)` devolve bytes de uma imagem válida 1200×800 que passa em `process_image`, é determinística para o mesmo `seed` e diferente para `seed` diferente; o plano `IMAGE_PLAN` (mapa título → `{"alt": ...}` ou `{"decorative": True}`) cobre cerca de dois terços das atividades de `ACTIVITIES`, tem pelo menos uma decorativa e deixa pelo menos uma atividade publicada sem imagem; todo item com imagem tem alt não vazio ou decorativa; os alts não citam marcas nem pessoas; `_attach_image(activity, plan)` só anexa quando `activity.image` está vazio (segunda chamada não chama `save`), grava `image_alt`/`image_decorative` e usa `activity.image.save(..., save=False)` seguido de `save(update_fields=[...])` incluindo `updated_at`; o `handle` executa o passo de imagens também para atividades que já existiam

### Implementation for User Story 6

- [X] T030 [US6] Em `apps/core/management/commands/seed_demo.py`, acrescentar `build_demo_image(seed)` (Pillow: degradê e formas geométricas, sem texto, 1200×800, JPEG, cores derivadas do `seed`), o dicionário `IMAGE_PLAN` por título, `_attach_image(activity, plan)` (passa a imagem por `images.process_image` antes de salvar) e o passo final em `handle` que percorre todas as atividades de `ACTIVITIES` já existentes no banco e anexa a imagem quando faltar; atualizar `help` e a saída (`Imagens: N anexada(s), M já existiam.`); ajustar em `tests/unit/core/test_seed_demo.py` as simulações do ORM e do armazenamento e a saída esperada para o novo passo, sem enfraquecer as verificações existentes; fazer os testes de T029 e todos os de `test_seed_demo.py` passarem

**Checkpoint**: a demonstração mostra atividades com e sem imagem; reexecutar não duplica nada.

---

## Phase 9: Polish & Cross-Cutting Concerns

- [X] T031 [P] Atualizar `docs/03-modelo-de-dados.md` com os campos `image`, `image_alt` e `image_decorative` de `Activity` e remover a pendência 10 (imagens), referenciando `docs/09-adicao-de-imagens.md`
- [X] T032 [P] Atualizar `docs/04-backlog-do-produto.md`: incluir EP-10 na tabela de épicos, as histórias US-037 a US-044 apontando para `docs/09-adicao-de-imagens.md`, marcar a pendência 8 (imagens) como resolvida, acrescentar a linha ao histórico de alterações e atualizar a data
- [X] T033 [P] Atualizar `docs/05-especificacao-api-rest.md` com o campo `image` (formato, `null`, garantias) na listagem e no detalhe, igual a `contracts/public-api-image.md`
- [X] T034 [P] Atualizar `docs/08-estrategia-infraestrutura-deploy.md` com o bucket `agenda-livre-imagens` (`sa-east-1`), a política de leitura pública, o usuário IAM de menor privilégio, e as variáveis `AWS_*`, ao lado da seção do RDS; o custo da conta AWS é só uma observação, pois controle de custo está fora do escopo da constituição
- [X] T035 [P] Atualizar `docs/09-adicao-de-imagens.md`: Status "Implementado" quando tudo estiver verde, pendências 4, 7, 8 e 10 (CORS) marcadas como resolvidas conforme `research.md` seção 10, nova linha no histórico
- [X] T036 [P] Atualizar `docs/PENDENCIAS-BACKEND.md`: mover o item "Atividades não têm imagem no backend" para "Resolvidas", com data e referência a `specs/010-activity-images/`; atualizar "Atualizado em"
- [X] T037 Ajustar `.env.example` somente se faltar algo (as quatro `AWS_*` já existem): trocar o comentário "Acesso ao S3" por uma explicação curta de cada variável, sem valores reais
- [X] T038 Rodar `python -m ruff check .` e corrigir qualquer apontamento nos arquivos novos e alterados (linhas de até 100 caracteres, imports ordenados)
- [X] T039 Rodar `python -m pytest` e confirmar que a suíte inteira passa com cobertura total >= 90%, sem acesso a banco nem à AWS; conferir que nenhum teste novo depende de arquivos binários no repositório
- [X] T040 Rodar `python manage.py makemigrations --check --dry-run` e confirmar "No changes detected" (a migration `0002` já existe); revisar `git status` para garantir que `.env` e `logs/` não aparecem e que nada com credenciais foi gravado
- [X] T041 Aplicar a migration com `python manage.py safe_migrate` **somente depois de a pessoa responsável autorizar**, pois o RDS é compartilhado; confirmar `activities.0002_activity_image` aplicada
- [X] T042 Percorrer os cenários 1 a 16 e a seção 4 de `quickstart.md` contra o ambiente real (Admin, API, bucket e `seed_demo`) com a pessoa responsável, e anotar o resultado no fim do `quickstart.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sem dependências; T002 antes de T003.
- **Foundational (Phase 2)**: depende do Setup. T005 depende de T004; T006a logo após T006 (senão `test_env_documentation.py` falha); T008 de T005 e T006; T009 de T008; T011 de T010; T012 de T011. Bloqueia todas as histórias.
- **US2 (Phase 3)**: depende da Foundational.
- **US1 (Phase 4)**: depende da US2 (T014) e da Foundational.
- **US3 (Phase 5)**: depende da Foundational; independente de US1 e US2 no código (o serializer só lê os campos), mas o teste de ponta a ponta usa as duas.
- **US4 (Phase 6)**: depende da Foundational (T005, T011).
- **US5 (Phase 7)**: depende da US1 (T018) para o `save_model` e da Foundational.
- **US6 (Phase 8)**: depende da US2 (T014) e da Foundational.
- **Polish (Phase 9)**: depende das histórias desejadas. T041 (migration no RDS, com autorização) deve vir antes de qualquer verificação manual contra o ambiente real (T024, T042), pois a API e o Admin leem as colunas novas; T042 é o último.

### User Story Dependencies

```text
Foundational ─┬─▶ US2 ─┬─▶ US1 ──▶ US5
              │        └─▶ US6
              ├─▶ US3
              └─▶ US4
```

### Within Each User Story

- Testes primeiro (red), depois a implementação (green).
- Dois testes na mesma história que mexem no mesmo arquivo não são paralelos entre si.

### Parallel Opportunities

- Fase 2: T004, T007 e T010 em paralelo (arquivos diferentes).
- Depois da Foundational: US2, US3 e US4 podem andar em paralelo; US1 e US6 começam quando T014 terminar.
- Testes marcados [P] de uma mesma história (T015 e T016) em paralelo.
- Fase 9: T031 a T036 em paralelo (documentos diferentes).

---

## Parallel Example: Foundational

```text
Task: "T004 [P] testes de config/storage.py em tests/unit/config/test_storage_settings.py"
Task: "T007 [P] ajustar tests/conftest.py e tests/unit/config/test_env.py"
Task: "T010 [P] testes do modelo em tests/unit/activities/test_activity_image_model.py"
```

## Parallel Example: depois da Foundational

```text
Task: "T013 [P] [US2] testes de process_image em tests/unit/activities/test_image_processing.py"
Task: "T019 [P] [US3] testes do campo image em tests/unit/consultation/test_image_field.py"
Task: "T022 [P] [US4] testes de URL pública em tests/unit/config/test_storage_settings.py"
```

---

## Implementation Strategy

### MVP First (US2 + US1)

1. Setup e Foundational (T001 a T012).
2. US2: tratamento e validação (T013, T014).
3. US1: anexar pelo Admin (T015 a T018).
4. **PARAR e VALIDAR**: enviar uma imagem pelo Admin (cenários 1, 5 a 10 do `quickstart.md`).

### Incremental Delivery

1. MVP acima: o administrador já guarda imagens tratadas.
2. US3: a API entrega o campo `image` e o frontend pode consumir.
3. US5: limpeza dos arquivos antigos.
4. US4: documentação e verificação do acesso público.
5. US6: demonstração com imagens.
6. Polish: documentos, lint, cobertura, migration no RDS e verificação final.

---

## Notes

- A US-043 (frontend) fica fora deste repositório; o contrato dela é `contracts/public-api-image.md`.
- Nenhuma tarefa lê, imprime ou versiona o `.env` ou chaves de acesso.
- T024, T041 e T042 tocam serviços reais (S3 e RDS) e dependem de autorização da pessoa responsável.
- Commits pequenos e descritivos, um por tarefa ou por grupo coeso; manter `main` protegida e trabalhar na
  branch `010-activity-images`.
