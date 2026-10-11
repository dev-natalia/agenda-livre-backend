# Agenda Livre — Backend

Backend da plataforma **Agenda Livre**, que centraliza a divulgação de cursos, eventos e atividades do
polo UniCEU Navegantes. É uma API REST em Django. O frontend fica em outro repositório e consome esta API.

> Projeto acadêmico (UNIVESP). O sistema roda **apenas localmente**; não há hospedagem nem deploy.

## Requisitos

- **Python 3.14**
- Uma instância **PostgreSQL no AWS RDS**, com acesso de rede liberado para a sua máquina, e o usuário e a
  senha do banco.

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
| `DB_HOST` | Sim | | Endpoint do PostgreSQL no RDS |
| `DB_PORT` | Sim | | Porta do PostgreSQL (normalmente `5432`) |
| `DB_NAME` | Sim | | Nome do banco |
| `DB_USER` | Sim | | Usuário do banco |
| `DB_PASSWORD` | Sim | | Senha do usuário |
| `DB_SSLMODE` | Não | `require` | Modo TLS do PostgreSQL |
| `DB_SSLROOTCERT` | Não | | Caminho do certificado raiz (com `verify-ca` ou `verify-full`) |
| `CORS_ALLOWED_ORIGINS` | Não | vazio | Origens do frontend, separadas por vírgula |

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

Parâmetros da listagem (todos opcionais, combináveis): `q` (título, resumo e descrição, sem acento e sem
caixa, até 100 caracteres), `unit` e `category` (UUID), `neighborhood`, `date` ou `date_from`/`date_to`
(`AAAA-MM-DD`, intervalo de até 366 dias), `page` e `page_size` (padrão 12, máximo 50). A ordem é pela
próxima ocorrência (com filtro de data, a primeira dentro do período); atividades sem datas futuras vêm
por último. Erros saem como `{"detail": "...", "errors": {"campo": ["..."]}}`. Página inválida responde
400 com `errors.page`; rota inexistente e falha inesperada sob `/api/` também respondem JSON, sem
detalhes internos (ver `specs/007-quality-security-accessibility/contracts/error-format.md`).

```bash
curl "http://localhost:8000/api/v1/activities/?q=danca&date_from=2026-11-01&date_to=2026-11-30"
```

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
