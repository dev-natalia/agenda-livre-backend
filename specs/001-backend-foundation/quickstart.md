# Quickstart: validar a fundação do backend

Roteiro para provar, ponta a ponta, que a feature funciona. Os detalhes de contrato estão em
[contracts/](contracts/).

## Pré-requisitos

- Python 3.14 instalado.
- Instância PostgreSQL no AWS RDS criada, com acesso de rede liberado para a sua máquina.
- Usuário e senha do banco.

## 1. Instalar

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate   |   macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
```

**Esperado**: instalação sem erros, nas versões fixadas.

## 2. Configurar o ambiente

```bash
cp .env.example .env
# edite .env com os valores reais (o arquivo não é versionado)
```

Variáveis em [contracts/environment-variables.md](contracts/environment-variables.md).

**Esperado**: `git status` não mostra `.env`.

## 3. Validar a configuração obrigatória

Remova temporariamente `DB_HOST` do `.env` e execute:

```bash
python manage.py check
```

**Esperado**: falha com mensagem que cita `DB_HOST` e não imprime nenhum valor sensível. Restaure a
variável depois.

## 4. Verificar a conexão com o banco

```bash
python manage.py check_db
```

**Esperado**: mensagem de sucesso com host, porta e nome do banco. Com senha errada, falha em até 15
segundos com o motivo e sem imprimir a senha.

## 5. Aplicar as migrations

```bash
python manage.py safe_migrate
```

**Esperado**: mostra o banco de destino, pede confirmação e aplica as migrations ao responder `s`.

## 6. Subir o backend e verificar o funcionamento

```bash
python manage.py runserver
curl http://127.0.0.1:8000/api/v1/health/
```

**Esperado**: `{"status": "ok"}` com status 200.

## 7. Verificar o CORS

Defina `CORS_ALLOWED_ORIGINS=http://localhost:5500`, reinicie e execute:

```bash
curl -i -H "Origin: http://localhost:5500" http://127.0.0.1:8000/api/v1/health/
curl -i -H "Origin: http://outro.exemplo" http://127.0.0.1:8000/api/v1/health/
```

**Esperado**: a primeira resposta inclui o cabeçalho `Access-Control-Allow-Origin` e a segunda não.

## 8. Rodar os testes e a cobertura

```bash
pytest
```

**Esperado**: todos passam, sem conexão com banco, e a cobertura total é de 90% ou mais (abaixo disso o
comando falha). A suíte roda sem o arquivo `.env`.

## 9. Verificar o estilo

```bash
ruff check .
```

**Esperado**: sem erros.
