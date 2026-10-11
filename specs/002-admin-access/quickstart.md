# Quickstart: validar Administração e Acesso

Pré-requisitos: feature 001 funcionando (`.env` preenchido, `check_db` com sucesso).

## 1. Testes e estilo

```bash
pytest          # sem banco, cobertura >= 90%
ruff check .
```

Esperado: todos os testes passam e a cobertura fica em 90% ou mais.

## 2. Aplicar migrations e criar a primeira conta

```bash
python manage.py safe_migrate
python manage.py create_admin maria
```

Esperado: `safe_migrate` mostra o banco de destino e aplica as migrations nativas. O grupo
"Administrador" passa a existir. `create_admin` pede a senha e confirma a criação.

## 3. Verificar o acesso

Com `DJANGO_DEBUG=true` no `.env`:

```bash
python manage.py runserver
```

1. Abrir `http://localhost:8000/admin/` sem login: deve redirecionar para a tela de entrada (US1).
2. Entrar com senha errada: mensagem genérica, sem acesso (US1).
3. Entrar com `maria`: o painel abre com Usuários e Grupos em português (US1, US3).
4. Criar uma segunda conta pelo painel, sem grupo, e entrar com ela: o painel não lista cadastros e a URL
   direta `/admin/auth/user/` responde 403 (US2).
5. Adicionar a segunda conta ao grupo "Administrador": ela passa a ver e editar os cadastros (US2, US4).
6. Desativar a segunda conta e tentar entrar: o acesso é recusado (US4).
7. `GET /api/v1/health/` continua respondendo sem login (FR-016).

## 4. Conferir a segurança

- Nenhuma senha em texto simples no banco, no log do servidor ou nas mensagens de erro.
- O repositório não contém senhas reais.
