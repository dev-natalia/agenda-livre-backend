# Research: Fundação do Backend

Todos os pontos desconhecidos do Technical Context foram resolvidos. Não restam `NEEDS CLARIFICATION`.

## R1. Compatibilidade das dependências com Python 3.14

- **Decision**: usar Django 6.1.2, Django REST Framework 3.18.3, psycopg 3.3.6 com `binary`, pytest 9.1.1,
  pytest-django 4.14.0, pytest-cov 7.1.0 (coverage 7.16.2), django-cors-headers 4.9.0, django-environ 0.14.0 e
  ruff 0.17.0.
- **Rationale**: em 2026-10-11, uma instalação simulada (`pip install --dry-run`) de todas essas
  bibliotecas no Python 3.14.5 resolveu com sucesso, incluindo as rodas compiladas para `cp314`
  (`psycopg-binary` e `coverage`). As versões exatas serão fixadas em `requirements*.txt` e reavaliadas
  na instalação real.
- **Alternatives considered**: `psycopg2-binary` (rejeitado: biblioteca legada; psycopg 3 é o
  recomendado pelo Django); Python 3.13 (rejeitado: a constituição exige 3.14).

## R2. Leitura e validação das variáveis de ambiente

- **Decision**: usar django-environ para carregar o arquivo `.env` e converter tipos, mais uma função própria
  em `config/env.py` que coleta todas as variáveis obrigatórias ausentes e lança um único erro listando-as.
- **Rationale**: o spec exige falha clara na inicialização indicando o que está faltando (FR-005). A
  função própria permite reportar todas de uma vez, sem expor valores.
- **Alternatives considered**: python-decouple (sem conversão para listas e bancos), `os.environ` puro (mais
  código repetido de conversão), pydantic-settings (dependência pesada para esta necessidade).

## R3. Garantir que testes não acessem banco

- **Decision**: duas camadas. (1) Configuração `config/settings_test.py` com `DATABASES` usando o backend
  `config.blocked_db`, baseado no `dummy` do Django, que levanta erro explícito ("Acesso a banco de dados
  proibido nos testes") em qualquer uso. O `dummy` puro foi descartado porque sua mensagem ("supply the
  ENGINE value") não deixa claro que o acesso é proibido. (2) O bloqueio padrão do pytest-django, que falha
  testes sem a marca `django_db`. Testes de proteção confirmam a falha explícita, inclusive em testes marcados com `django_db`.
- **Rationale**: atende FR-010 sem depender de disciplina da equipe. A configuração de teste também não exige
  nenhuma variável de ambiente, então os testes rodam sem RDS e sem `.env`.
- **Alternatives considered**: apenas bloqueio do pytest-django (rejeitado: um teste com a marca
  `django_db` ainda tentaria conectar); SQLite em memória (rejeitado: seria "banco" e contraria a decisão).

## R4. Cobertura mínima de 90%

- **Decision**: pytest-cov com `--cov=apps --cov=config --cov-fail-under=90` configurado em `pyproject.toml`,
  excluindo `manage.py`, `wsgi.py` e `asgi.py`.
- **Rationale**: a execução simples do comando de testes já falha abaixo do limite (FR-011). Arquivos
  `wsgi.py` e `asgi.py` são código de inicialização do servidor, sem lógica a testar.
- **Alternatives considered**: `coverage run` separado (mais passos para a equipe); limite configurado só em
  CI (não há CI de deploy e a verificação deve valer localmente).

## R5. Verificação de estilo PEP 8

- **Decision**: ruff com as regras `E`, `W` (pycodestyle), `F` (pyflakes) e `I` (ordenação de imports),
  limite de 100 colunas.
- **Rationale**: ruff é rápido, é uma única ferramenta e cobre PEP 8. O limite de 100 colunas é comum em
  projetos Django e já é usado nas outras documentações do projeto.
- **Alternatives considered**: flake8 + isort + black (3 ferramentas para o mesmo resultado).

## R6. Modelo de usuário

- **Decision**: usar o modelo de usuário padrão do Django (`django.contrib.auth.User`).
- **Rationale**: o DOC-02 pede definir isso antes da primeira migration. Só existirão administradores, sem
  campos extras previstos, então o modelo padrão atende. Trocar depois é caro, mas não há requisito que
  o justifique (YAGNI).
- **Alternatives considered**: modelo personalizado com `AbstractUser` (adiado até existir necessidade).

## R7. Verificação de conexão e migrações com destino claro

- **Decision**: dois comandos de gerenciamento no módulo `core`. `check_db` executa uma consulta simples e
  informa host, porta e nome do banco, sem a senha, e o tipo de falha. `safe_migrate` mostra o destino, pede
  confirmação (ignorada com `--noinput`) e então chama o `migrate` padrão.
- **Rationale**: o banco do RDS é único e compartilhado entre desenvolvimento e demonstração, então aplicar
  migrations no destino errado é um risco real (FR-007 e FR-008; DOC-08 seção 3).
- **Alternatives considered**: apenas o `migrate` padrão (não informa o destino); sobrescrever o `migrate`
  (mais invasivo e confuso).

## R8. Conexão criptografada com o RDS

- **Decision**: `DB_SSLMODE` configurável com padrão `require`, e `DB_SSLROOTCERT` opcional para validação de
  certificado (`verify-full`).
- **Rationale**: cumpre o requisito de conexão criptografada (FR-006) sem obrigar a equipe a baixar o pacote
  de certificados da AWS no primeiro dia. Quem quiser validação completa informa o caminho do certificado.
- **Alternatives considered**: sempre `verify-full` (exige o certificado, atrapalha a primeira execução);
  sem TLS (rejeitado por segurança).

## R9. Estrutura de módulos

- **Decision**: pacote `apps/` com `core` e os cinco módulos de domínio (`units`, `categories`, `activities`,
  `schedules`, `audiences`), cada um com `apps.py` e `models.py` vazio. Os nomes seguem o DOC-02.
- **Rationale**: atende FR-002 e deixa as próximas features apenas adicionarem modelos. O `core` abriga a
  verificação de funcionamento e os comandos, que não pertencem a um domínio.
- **Alternatives considered**: apps na raiz (menos organizado); um único app (contraria o DOC-02).

## R10. Endpoint de verificação de funcionamento

- **Decision**: `GET /api/v1/health/` retorna `{"status": "ok"}` com status 200 e não consulta o banco.
- **Rationale**: o objetivo é confirmar que a aplicação está em execução (FR-016). Verificar o banco é papel do
  comando `check_db`, o que mantém o endpoint rápido e utilizável mesmo sem rede para o RDS.
- **Alternatives considered**: incluir o estado do banco no endpoint (acopla a resposta à rede da AWS e
  expõe informação interna).

## R11. CORS

- **Decision**: `django-cors-headers` com a lista `CORS_ALLOWED_ORIGINS` lida de `CORS_ALLOWED_ORIGINS`
  (separada por vírgula). Vazia por padrão, ou seja, nenhuma origem autorizada até a equipe configurar.
- **Rationale**: o frontend é outro repositório em outra origem local (FR-014). Padrão restritivo é mais seguro
  e a lista é só configuração (sem alterar código).
- **Alternatives considered**: `CORS_ALLOW_ALL_ORIGINS` (inseguro, mesmo local); origem fixa no código
  (viola o cenário de configuração sem mudar código).
