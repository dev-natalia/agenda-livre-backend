# Research: Imagens das Atividades

**Feature**: 010-activity-images | **Date**: 2026-10-12

Não restou nenhum `NEEDS CLARIFICATION` no Technical Context. Esta pesquisa registra as decisões de
desenho, a razão de cada uma e as alternativas descartadas, a partir do código existente e das decisões do
`docs/09-adicao-de-imagens.md`.

## 1. Integração com o S3

- **Decision**: `django-storages` com o backend `S3Storage`, configurado em `STORAGES["default"]` por uma
  função `build_storages()` em `config/storage.py`. Opções: `bucket_name` e `region_name` das variáveis de
  ambiente; `querystring_auth=False` (URLs públicas e permanentes); `file_overwrite=True`;
  `default_acl=None`; `custom_domain` com o endereço regional do bucket (`<bucket>.s3.<região>.amazonaws.com`, não é domínio próprio). As credenciais são lidas das variáveis `AWS_ACCESS_KEY_ID` e
  `AWS_SECRET_ACCESS_KEY` e passadas como opções explícitas.
- **Rationale**: o `ImageField` do Django funciona sem mudar o restante do código, e `storage.url()` devolve
  o endereço absoluto do objeto. `file_overwrite=True` evita a checagem de existência a cada gravação (o
  nome é um UUID, então não há colisão). Sem ACL por objeto, a leitura pública vem da política do bucket,
  como a AWS recomenda para buckets novos (ACLs desativadas).
- **Alternatives considered**: cliente `boto3` direto (reimplementa o que o `FileField` já faz e perde a
  integração com o Admin); URLs assinadas (descartadas no DOC-09, pendência 9); armazenar no PostgreSQL
  (infla banco e backups, sem cache); MinIO/Docker (descartado: o projeto não usa Docker).

## 2. Variáveis de ambiente obrigatórias

- **Decision**: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME` e
  `AWS_S3_REGION_NAME` entram em `REQUIRED_VARS` (como as do banco). Os testes definem valores fictícios em
  `config/settings_test.py` e usam armazenamento em memória. O valor da chave secreta entra no
  mascaramento do log (`build_logging`).
- **Rationale**: o armazenamento em nuvem é requisito do projeto, e falhar na partida com a lista das
  variáveis ausentes é o padrão já adotado (`require_env`). Uma configuração parcial produziria erro só no
  primeiro envio de imagem.
- **Alternatives considered**: variáveis opcionais com fallback para o disco local (esconde configuração
  errada e cria um segundo caminho de armazenamento para manter).

## 3. Validação e tratamento da imagem

- **Decision**: módulo `apps/activities/images.py` com uma função `process_image(uploaded)` que:
  1. rejeita arquivo maior que 5 MB antes de abrir;
  2. abre com Pillow, aceita só `JPEG`, `PNG` e `WEBP` pelo formato detectado (não pela extensão);
  3. confere as dimensões pelo cabeçalho (400×300 a 6000×6000), antes de decodificar o arquivo todo;
  4. decodifica, aplica `ImageOps.exif_transpose`, reduz com `thumbnail((1600, 1600))` (nunca amplia) e
     regrava no mesmo formato sem EXIF (JPEG qualidade 85 com `optimize`; PNG com `optimize`; WebP
     qualidade 85);
  5. devolve um `ContentFile` e a extensão, ou levanta `ValidationError` com mensagem em português.
- **Rationale**: ler o formato e o tamanho pelo cabeçalho barra arquivos enormes antes de gastarem memória;
  regravar do zero é o jeito confiável de descartar todos os metadados; a transposição por EXIF preserva a
  orientação visual antes de o EXIF sumir. `Image.DecompressionBombError` e `UnidentifiedImageError` viram
  a mesma mensagem de arquivo inválido.
- **Alternatives considered**: `ImageField` com validação padrão do Django (só confirma que é imagem,
  não limita dimensões nem remove EXIF); remover EXIF só dos blocos de metadados (deixa lixo em formatos
  diferentes); converter tudo para WebP (muda o formato escolhido pela pessoa e complica a comparação nos
  testes).

## 4. Onde ficam as regras

- **Decision**:
  - `Activity.clean()` (já existe e é chamado pelo Admin e pelo `seed_demo`): exige texto alternativo
    **ou** `image_decorative` quando há imagem; rejeita os dois juntos; normaliza o alt com `strip()`;
    limita o alt a 200 caracteres; quando **não há** imagem, zera `image_alt` e `image_decorative`
    (em vez de erro, para a remoção de imagem não travar quando o alt antigo ainda está no formulário).
  - `ActivityAdminForm.clean_image()`: só processa quando o valor é um arquivo recém-enviado
    (`UploadedFile`); trocar apenas o alt não reprocessa a imagem.
  - `upload_to` é uma função do módulo do modelo que devolve `activities/<uuid4>.<ext>` ignorando o nome
    enviado.
- **Rationale**: a regra de dados vale para qualquer caminho de gravação; o tratamento de arquivo só faz
  sentido quando há arquivo novo. Ficar no modelo e no formulário mantém a regra testável sem banco.
- **Alternatives considered**: `CheckConstraint` no banco (a mensagem em português por campo fica pior e a
  suíte não acessa banco para exercitá-la); sinal `pre_save` para tratar o arquivo (esconde a validação e
  não consegue devolver erro ao formulário).

## 5. Arquivos órfãos

- **Decision**: o arquivo é apagado **depois do commit**, com `transaction.on_commit`, em três casos:
  - troca ou remoção pelo Admin: `ActivityAdmin.save_model` compara o valor inicial do formulário com o
    novo (`"image" in form.changed_data`) e agenda a remoção do arquivo antigo;
  - exclusão da atividade: sinal `post_delete` agenda a remoção do arquivo.
  `delete_stored_file(name)` captura qualquer exceção, registra um erro no log local (sem credenciais) e
  segue.
- **Rationale**: apagar só depois do commit evita perder o arquivo se a gravação do banco falhar; capturar a
  exceção garante que a falha do S3 não impeça salvar a atividade (FR-013). Na exclusão pelo Admin só
  rascunhos podem ser apagados (regra existente), e o sinal cobre também qualquer exclusão programática.
- **Alternatives considered**: `django-cleanup` (dependência a mais para dois casos simples); varredura
  agendada (sem agendador no projeto, YAGNI); apagar antes do commit (arriscado).
- **Risco residual aceito**: se o envio ao S3 acontecer e o banco falhar em seguida, sobra um arquivo
  órfão; é raro e removível manualmente (já previsto nas Assumptions da spec).

## 6. Campo `image` na API

- **Decision**: uma função `image_payload(activity)` em `serializers.py` devolve `None` sem imagem ou
  `{"url": activity.image.url, "alt": ..., "decorative": ...}`. É usada pelo serializer da listagem (que
  monta um dicionário à mão) e pelo do detalhe (`SerializerMethodField`). Para imagem decorativa o `alt`
  é `""`.
- **Rationale**: o mesmo formato nos dois endpoints, sem duplicar. Só atividades `PUBLISHED` chegam às
  respostas públicas, então a regra de visibilidade existente garante o FR-012 sem código novo. A URL é
  calculada sem rede, e as colunas já vêm na consulta da atividade (sem consulta extra).
- **Alternatives considered**: `ImageSerializer` aninhado do DRF (o DRF montaria a URL com `request`,
  mas o `storage.url()` já devolve a URL absoluta do S3); expor o nome do objeto (vaza detalhe interno).

## 7. Dados de demonstração

- **Decision**: `seed_demo` gera imagens fictícias com Pillow (degradês e formas geométricas, 1200×800,
  determinísticas por título), passa pelo mesmo `process_image` e anexa a imagem a cerca de dois terços
  das atividades; algumas recebem `image_decorative=True` e as demais um texto alternativo; as restantes
  ficam sem imagem. Idempotência: o passo de imagens roda para atividades já existentes e só anexa quando
  `activity.image` está vazio.
- **Rationale**: nenhuma imagem de terceiros, sem pessoas nem marcas, sem rede para baixar arquivos e sem
  binários no repositório. Rodar de novo não duplica nada.
- **Alternatives considered**: baixar fotos de bancos livres (depende de rede, de licença e de política de
  atribuição); versionar JPEGs no repositório (binários grandes sem necessidade).

## 8. CORS do bucket

- **Decision**: **não configurar CORS** no bucket por enquanto.
- **Rationale**: o navegador carrega `<img src>` entre origens sem CORS. Só seria necessário se o frontend
  buscasse a imagem com `fetch` ou a desenhasse em `canvas`. Se isso acontecer, adicionar uma regra
  `GET` para `http://localhost:5500`. Fecha a parte de CORS da pendência 10 do DOC-09.
- **Alternatives considered**: liberar CORS para `*` desde já (superfície maior sem necessidade).

## 9. Estratégia de testes (fecha a pendência 7 do DOC-09)

- **Decision**: testes unitários, sem banco e sem rede:
  - `process_image`: imagens geradas em memória com Pillow, cobrindo formatos, limites exatos e +1, arquivo
    corrompido, extensão enganosa, redução a 1600 px, imagem pequena sem ampliar, remoção de EXIF,
    orientação, PNG com transparência;
  - modelo: regra de alt/decorativa com instâncias sem salvar;
  - formulário e Admin: `ModelAdmin` com `RequestFactory` e objetos simulados, como já é feito em
    `test_activity_admin.py`;
  - limpeza: `delete_stored_file` com armazenamento simulado (sucesso e falha) e `on_commit` executado
    pelo teste;
  - API: serializers com `SimpleNamespace`/`Mock` e `InMemoryStorage`;
  - configuração: `build_storages()` como função pura, e variáveis ausentes em `require_env`;
  - `seed_demo`: com ORM e armazenamento simulados.
- **Rationale**: segue o Princípio III. `boto3` nunca é importado nos testes, pois `build_storages` só
  devolve um dicionário e o backend em memória substitui o S3.

## 10. Pendências do DOC-09 que o plano fecha

| Pendência | Resolução |
|-----------|-----------|
| 4. Arquivos órfãos | Remover no commit da troca/remoção/exclusão; falha só vai para o log. |
| 7. Testes do upload | Itens da seção 9. |
| 8. Texto alternativo padrão | Nenhum; o administrador sempre escreve o texto ou marca decorativa. |
| 10. CORS do bucket | Não configurar agora (seção 8). Custo segue acompanhado fora do código. |
