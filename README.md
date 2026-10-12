# Agenda Livre — Backend

Backend da plataforma **Agenda Livre**, que centraliza a divulgação de cursos, eventos e atividades do
polo UniCEU Navegantes. É uma API REST em Django. O frontend fica em outro repositório e consome esta API.

> Projeto acadêmico (UNIVESP). O sistema roda **apenas localmente**; não há hospedagem nem deploy.

## Requisitos

- **Python 3.14**
- Uma instância **PostgreSQL no AWS RDS**, com acesso de rede liberado para a sua máquina, e o usuário e a
  senha do banco.
- Um **bucket do Amazon S3** para as imagens das atividades e um usuário IAM com acesso a ele (ver
  [Imagens das atividades](#imagens-das-atividades-amazon-s3)).

## Instalação

```bash
python -m venv .venv
# Windows (PowerShell): .venv\Scripts\Activate.ps1
# Windows (Git Bash):   source .venv/Scripts/activate
# macOS / Linux:        source .venv/bin/activate
pip install -r requirements-dev.txt
```

As versões das dependências estão fixadas em `requirements.txt` (execução) e `requirements-dev.txt`
(execução + testes e estilo).

## Configuração

Copie o arquivo de exemplo e preencha os valores:

```bash
cp .env.example .env
```

O arquivo `.env` não é versionado. Nunca registre senhas ou chaves no repositório.

| Variável | Obrigatória | Padrão | Descrição |
|---|---|---|---|
| `DJANGO_SECRET_KEY` | Sim | | Chave secreta do Django |
| `DJANGO_DEBUG` | Não | `False` | Modo de depuração (`True` ou `False`) |
| `DJANGO_ALLOWED_HOSTS` | Não | `localhost,127.0.0.1` | Hosts aceitos, separados por vírgula |
| `DJANGO_HTTPS_ONLY` | Não | `True` se `DJANGO_DEBUG=False` | Redireciona para HTTPS, usa cookies seguros e HSTS |
| `DB_HOST` | Sim | | Endpoint do PostgreSQL no RDS |
| `DB_PORT` | Sim | | Porta do PostgreSQL (normalmente `5432`) |
| `DB_NAME` | Sim | | Nome do banco |
| `DB_USER` | Sim | | Usuário do banco |
| `DB_PASSWORD` | Sim | | Senha do usuário |
| `AWS_ACCESS_KEY_ID` | Sim | | Chave de acesso do usuário IAM da aplicação (imagens no S3) |
| `AWS_SECRET_ACCESS_KEY` | Sim | | Chave secreta do usuário IAM (nunca versionar nem registrar em log) |
| `AWS_STORAGE_BUCKET_NAME` | Sim | | Nome do bucket S3 das imagens (`agenda-livre-imagens`) |
| `AWS_S3_REGION_NAME` | Sim | | Região do bucket (`sa-east-1`) |
| `DB_SSLMODE` | Não | `require` | Modo TLS do PostgreSQL |
| `DB_SSLROOTCERT` | Não | | Caminho do certificado raiz (com `verify-ca` ou `verify-full`) |
| `CORS_ALLOWED_ORIGINS` | Não | vazio | Origens do frontend, separadas por vírgula |
| `LOG_DIR` | Não | `logs` | Pasta dos registros de erro (relativa à raiz do repositório ou absoluta) |
| `LOG_LEVEL` | Não | `ERROR` | Nível mínimo gravado: `WARNING`, `ERROR` ou `CRITICAL` |
| `LOG_MAX_BYTES` | Não | `1048576` | Tamanho máximo de cada arquivo de registro, em bytes |
| `LOG_BACKUP_COUNT` | Não | `5` | Quantos arquivos antigos de registro manter |

**Modo restritivo:** com `DJANGO_DEBUG=False`, `DJANGO_HTTPS_ONLY` liga por padrão o redirecionamento
para HTTPS, os cookies seguros e o HSTS. Como o sistema roda apenas localmente, em HTTP, quem usar
`DJANGO_DEBUG=False` sem HTTPS deve definir `DJANGO_HTTPS_ONLY=False`; senão o navegador é redirecionado
a HTTPS e o login do painel não persiste. Em qualquer modo valem `nosniff`, `X-Frame-Options: DENY` e
cookie de sessão `HttpOnly`.

Se alguma variável obrigatória faltar, a aplicação não inicia e informa o nome de todas as que faltam
(sem mostrar valores).

## Executando o backend

```bash
python manage.py runserver
```

Verifique o funcionamento em <http://127.0.0.1:8000/api/v1/health/>, que deve responder
`{"status": "ok"}`.

## Banco de dados (AWS RDS)

O backend usa o PostgreSQL no AWS RDS, configurado só por variáveis de ambiente. Esse banco é **único e
compartilhado**: confira sempre o destino antes de aplicar alterações.

Verifique a conexão (mostra host, porta e nome do banco, nunca a senha; em caso de falha informa o tipo,
como credenciais recusadas, tempo esgotado ou rede bloqueada):

```bash
python manage.py check_db
```

Aplique as migrations. O comando mostra o banco de destino e pede confirmação (`s` para continuar):

```bash
python manage.py safe_migrate
# sem pergunta: python manage.py safe_migrate --noinput
```

Se a conexão falhar por rede, confira o Security Group do RDS (a sua máquina precisa estar autorizada). Por
padrão a conexão usa TLS (`DB_SSLMODE=require`).

## Acesso administrativo

Todo o conteúdo é gerenciado pelo Django Admin, em `http://localhost:8000/admin/`. Para o painel carregar
estilos e imagens no `runserver`, defina `DJANGO_DEBUG=true` no `.env` (uso local apenas).

1. Aplique as migrations (`python manage.py safe_migrate`). Isso cria o grupo **Administrador**.
2. Crie a primeira conta: `python manage.py create_admin <usuario>` (a senha é pedida sem eco e validada).
3. Entre em `/admin/` com essa conta.

**Perfil único:** o grupo **Administrador** recebe automaticamente todas as permissões (ver, criar, alterar e
excluir todos os cadastros e gerenciar contas). Uma conta só opera o painel se estiver ativa, tiver
"Membro da equipe" marcado e pertencer a esse grupo. Contas sem o grupo não veem cadastros e recebem
403 em endereços diretos. Evite superusuários nas contas comuns, pois eles ignoram o grupo.

**Outras contas:** crie pelo painel (Usuários), marque "Membro da equipe" e adicione ao grupo
**Administrador**. Para retirar o acesso, desmarque "Ativo" (os registros da conta são preservados).

**Limitações desta versão:** não há bloqueio por tentativas de login nem recuperação de senha por e-mail.
Se alguém perder a senha, outro administrador a redefine pelo painel. A consulta pública não exige login.

## Carga inicial de unidades e categorias

Unidades e categorias são gerenciadas em `/admin/` ("Unidades" e "Categorias"). Para preparar o ambiente
com o CEU Navegantes e as oito categorias iniciais:

```bash
python manage.py safe_migrate
python manage.py seed_catalog
```

O comando é seguro para repetir: só cria o que não existe (pelo identificador) e não altera registros
editados no painel. O bairro "Cantinho do Céu" do CEU Navegantes é provisório e deve ser confirmado pela equipe.
Para retirar uma unidade ou categoria de uso, desative-a (ação "Desativar selecionados" ou desmarque
"Ativo"); os vínculos existentes são preservados.

## Dados de demonstração

Para popular o ambiente de desenvolvimento com unidades, atividades e programações **fictícias** (depois de `seed_catalog`):

```bash
python manage.py seed_demo
```

O comando cria os CEUs Cidade Dutra, Vila Rubi e Vila do Sol e 15 atividades (publicadas, rascunhos, cancelada e encerradas) com datas relativas ao dia da execução. Também anexa **imagens fictícias** (ilustrações geométricas geradas na hora, sem pessoas nem marcas) a 10 delas, com texto alternativo ou marcadas como decorativas, e deixa as demais sem imagem para mostrar o visual alternativo; as imagens vão para o bucket S3 (exige as variáveis `AWS_*`) e reexecutar o comando não as duplica. Usa o primeiro administrador ativo como autor, **não cria usuários** e é seguro para repetir (ignora o que já existe pelo título e unidade). O telefone de cada unidade fica no campo descrição, pois o modelo não tem campo próprio.

## Carga inicial de públicos-alvo e atividades

O mesmo `seed_catalog` carrega as opções de público-alvo (Crianças, Adolescentes, Adultos, Pessoas idosas
e Todas as idades). A lista é provisória e pode ser mantida em `/admin/` ("Públicos-alvo").

As atividades são gerenciadas em "Atividades". Toda atividade nasce como rascunho e a situação só muda
pelas ações da lista: "Publicar selecionadas" (exige título, descrição, unidade e categoria ativas e ao
menos um público-alvo), "Cancelar selecionadas" e "Encerrar selecionadas" (só para publicadas). Atividades
canceladas ou encerradas podem ser publicadas de novo. Só as publicadas são públicas, e só rascunhos podem
ser excluídos; as demais devem ser canceladas ou encerradas.

## Programações e ocorrências

As datas e horários das atividades são cadastrados na própria página da atividade (bloco "Programações", inclusive ao criar a atividade) ou
em "Programações", que lista e filtra todas. Há dois tipos:

- **Pontual**: uma única data (data final igual à inicial) e nenhum dia da semana.
- **Recorrente**: período de validade (datas inclusivas) e ao menos um dia da semana (segunda a domingo).

O horário de término precisa ser posterior ao de início; horários que atravessam a meia-noite não são
suportados. Não há exceções por ocorrência: para mudar uma data, edite a programação. As ocorrências não
são gravadas; são calculadas a partir da programação, no fuso `America/Sao_Paulo`. A página da atividade
mostra as próximas ocorrências (só para atividades publicadas). Uma atividade com programações não pode ser
excluída; excluir uma programação não afeta a atividade.

## API pública de consulta

Leitura sem login, somente `GET` (os demais métodos respondem 405), sob `/api/v1/`. Só atividades
publicadas aparecem; nenhum dado de auditoria ou de conta é exposto. Contrato completo em
`specs/006-public-consultation/contracts/public-api.md`.

| Rota | Descrição |
|---|---|
| `GET /api/v1/activities/` | Lista paginada, com busca e filtros |
| `GET /api/v1/activities/{id}/` | Detalhe (404 igual para inexistente, malformado ou não publicada) |
| `GET /api/v1/units/` | Unidades ativas, por nome |
| `GET /api/v1/categories/` | Categorias ativas, por nome |
| `GET /api/v1/audiences/` | Públicos-alvo ativos, por nome (para montar o filtro `audience`) |

Parâmetros da listagem (todos opcionais, combináveis): `q` (título, resumo e descrição, sem acento e sem
caixa, até 100 caracteres), `unit`, `category` e `audience` (UUID), `neighborhood`, `date` ou `date_from`/`date_to`
(`AAAA-MM-DD`, intervalo de até 366 dias), `page` e `page_size` (padrão 12, máximo 50). A ordem é pela
próxima ocorrência (com filtro de data, a primeira dentro do período); atividades sem datas futuras vêm
por último. Erros saem como `{"detail": "...", "errors": {"campo": ["..."]}}`. Página inválida responde
400 com `errors.page`; rota inexistente e falha inesperada sob `/api/` também respondem JSON, sem
detalhes internos (ver `specs/007-quality-security-accessibility/contracts/error-format.md`).

```bash
curl "http://localhost:8000/api/v1/activities/?q=danca&date_from=2026-11-01&date_to=2026-11-30"
```

**Filtro por público-alvo.** `audience=<id>` (um único valor, obtido em `/api/v1/audiences/`) devolve as
atividades daquele público **e** as de “Todas as idades”; escolher “Todas as idades” devolve só as dela.
Cada item da listagem traz `target_audiences` (`[{id, name}]`, por nome). No Django Admin, o cadastro de
públicos-alvo tem a caixa **Abrange todos os públicos**, que é o que identifica “Todas as idades” (o
`seed_catalog` a marca). **Depois de `safe_migrate`, rode `python manage.py seed_catalog`**; sem isso, a
opção “Todas as idades” de um catálogo já existente fica sem a marca e o filtro vira exato. A lista de
atividades do Admin também filtra por público-alvo. Contrato em
`specs/011-audience-filter/contracts/public-api-audience.md`.

## Imagens das atividades (Amazon S3)

Cada atividade pode ter **uma imagem**, enviada pelo Django Admin. O arquivo fica no Amazon S3 (bucket
`agenda-livre-imagens`, região `sa-east-1`); o PostgreSQL guarda só o nome do objeto. As dependências
`Pillow`, `django-storages[s3]` e `boto3` estão fixadas em `requirements.txt`.

- **Validação:** JPEG, PNG ou WebP (verificados pelo conteúdo), até 5 MB, de 400×300 a 6000×6000 px.
- **Tratamento:** o lado maior é reduzido a 1600 px, a imagem é regravada **sem metadados** (EXIF, GPS) e
  guardada com um nome aleatório (`activities/<uuid>.<ext>`); o nome enviado nunca é usado.
- **Acessibilidade:** com imagem, informe o **texto alternativo** (até 200 caracteres) **ou** marque
  **imagem decorativa**, nunca os dois.
- **API:** `GET /api/v1/activities/` e `/{id}/` trazem `image` (`{url, alt, decorative}` ou `null`);
  veja `specs/010-activity-images/contracts/public-api-image.md`.
- **Limpeza:** trocar ou remover a imagem, ou excluir a atividade, apaga o arquivo antigo do bucket.

### Configuração da AWS

Defina no `.env` as variáveis `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME` e
`AWS_S3_REGION_NAME` (tabela acima). As chaves **nunca** vão para o repositório nem para os logs.

**Leitura pública apenas dos objetos, sem listagem** (Permissions → Block public access: desmarque as duas
opções sobre *políticas*; depois Bucket policy):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "PublicReadGetObject",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::agenda-livre-imagens/*"
    }
  ]
}
```

**Usuário IAM da aplicação** (`agenda-livre-app`, sem acesso ao console), com a política de menor privilégio:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ObjetosDoBucket",
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::agenda-livre-imagens/*"
    },
    {
      "Sid": "ChecarExistencia",
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::agenda-livre-imagens"
    }
  ]
}
```

O `<img>` do frontend não precisa de CORS no bucket; só seria necessário se ele buscasse a imagem por
`fetch` ou `canvas`. Os testes automatizados **não** acessam o S3 (usam armazenamento em memória).

## Acessibilidade

A interface é do repositório do frontend (meta proposta: WCAG 2.2 nível AA). O backend entrega nomes
legíveis (unidade, categoria, públicos-alvo, dias da semana), datas `AAAA-MM-DD`, horários `HH:MM`,
campos opcionais vazios como `null` e erros por campo para o frontend associar a cada campo. Rótulos,
teclado, foco, contraste e responsividade cabem ao frontend. Detalhes em
`specs/007-quality-security-accessibility/contracts/accessibility-handoff.md`.

## Frontend (CORS)

O frontend fica em **outro repositório** e roda em outra origem local. O navegador só permite que ele chame
esta API se a origem estiver autorizada em `CORS_ALLOWED_ORIGINS` (separadas por vírgula):

```env
CORS_ALLOWED_ORIGINS=http://localhost:5500
```

Por padrão a lista é vazia: nenhuma origem é autorizada. Alterar a lista não exige mudar o código; basta
reiniciar o backend.

## Registro de erros

As falhas inesperadas ficam em **`logs/agenda-livre.log`** (na raiz do repositório; pasta configurável por
`LOG_DIR`, fora do Git). O arquivo gira ao atingir `LOG_MAX_BYTES`, mantendo `LOG_BACKUP_COUNT` arquivos
antigos (`agenda-livre.log.1`, `.2`, ...), o que limita o espaço total.

- **Gravado:** falhas inesperadas de requisição (horário, método, caminho, tipo da falha e rastreamento),
  variável de ambiente ausente ou inválida na inicialização e falhas de conexão em `check_db` e
  `safe_migrate` (tipo, host e porta).
- **Nunca gravado:** erros esperados de cliente (400, 401, 403, 404, 405), corpo e parâmetros de
  requisição, e segredos. Senhas, chaves, tokens, cookies, autorização e credenciais em endereços de
  conexão são trocados por `***`.
- A resposta ao visitante continua sendo só a mensagem genérica de erro. Se o arquivo não puder ser
  gravado, a aplicação segue funcionando e o aviso vai para o terminal.

```bash
tail -n 50 logs/agenda-livre.log            # Git Bash / Linux / macOS
# PowerShell: Get-Content logs\agenda-livre.log -Tail 50
```

**Fora do escopo:** implantação, backup e restauração, monitoramento e hospedagem. As páginas Sobre e
Contato existem só no frontend, sem endpoint no backend: Sobre tem texto fixo e Contato é
demonstrativa (não envia nem armazena mensagens). Qualquer requisição da API a caminhos como
`/api/contato/` ou `/api/sobre/` recebe `404` em JSON, sem registrar o corpo.

## Testes e cobertura

```bash
pytest
```

- Os testes são **somente unitários, com mocks**, e **não acessam nenhum banco de dados** (nem o RDS). Um
  teste que tente acessar o banco falha com a mensagem "Acesso a banco de dados proibido nos testes".
- A suíte roda sem o arquivo `.env` e sem rede.
- A cobertura é medida em `apps/` e `config/` e a execução **falha se a cobertura total ficar abaixo de
  90%**.

## Estilo de código

```bash
ruff check .
```

Verifica o padrão PEP 8 (regras `E`, `W`), erros comuns (`F`) e a ordem dos imports (`I`), com limite de 100
colunas. A configuração está em `pyproject.toml`. Use `ruff check --fix .` para corrigir o que for possível.

## Estrutura

```text
config/   configuração do projeto (ambiente, settings, urls)
apps/     módulos por domínio: core, units, categories, activities, schedules, audiences, consultation
tests/    testes unitários
```
