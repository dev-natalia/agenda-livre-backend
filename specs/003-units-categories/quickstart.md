# Quickstart: validar Gestão de Unidades e Categorias

Pré-requisitos: features 001 e 002 funcionando (`.env` preenchido, conta de administrador criada com
`create_admin`).

## 1. Testes e estilo

```bash
pytest          # sem banco, cobertura >= 90%
ruff check .
```

Esperado: todos os testes passam e a cobertura fica em 90% ou mais.

## 2. Conferir e aplicar as migrations

```bash
python manage.py makemigrations --check --dry-run   # confirma que as migrations versionadas estão completas
python manage.py safe_migrate
```

Esperado: `safe_migrate` mostra o banco de destino e aplica as migrations de `units` e `categories`.
O grupo "Administrador" é sincronizado e passa a incluir as permissões dos dois modelos.

## 3. Carga inicial

```bash
python manage.py seed_catalog
python manage.py seed_catalog
```

Esperado: a primeira execução cria 1 unidade e 8 categorias; a segunda informa que todos já existiam e
não cria nada.

## 4. Verificar no painel

Com `DJANGO_DEBUG=true`, rode `python manage.py runserver` e entre em `/admin/` com a conta de
administrador.

1. Em "Unidades", abra o CEU Navegantes, altere a descrição e salve. A data de atualização muda.
2. Tente cadastrar uma unidade sem nome e outra com o slug `ceu-navegantes`. Ambas são recusadas com
   mensagem no campo.
3. Em "Categorias", tente criar "cultura e artes". É recusada por nome repetido.
4. Cadastre uma categoria nova deixando o slug em branco. O identificador é gerado do nome.
5. Selecione uma categoria e use "Desativar selecionados". A coluna de situação muda e o filtro por
   situação a separa das ativas. Use "Reativar selecionados" para voltar.
6. Entre com uma conta sem o grupo (ou saia) e abra `/admin/units/unit/`. O acesso é negado.

## 5. Pendência para a feature 004

As regras de vínculo (inativos fora das listas, exclusão recusada com atividades) são exercitadas
ponta a ponta quando as atividades existirem, conforme `contracts/admin-units-categories.md`.
