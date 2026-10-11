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
apps/     módulos por domínio: core, units, categories, activities, schedules, audiences
tests/    testes unitários
```
