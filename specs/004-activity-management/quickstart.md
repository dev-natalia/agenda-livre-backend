# Quickstart: validar Gestão de Atividades

Pré-requisitos: features 001, 002 e 003 funcionando (`.env` preenchido, conta de administrador criada
com `create_admin`, unidade e categorias carregadas com `seed_catalog`).

## 1. Testes e estilo

```bash
pytest          # sem banco, cobertura >= 90%
ruff check .
```

Esperado: todos os testes passam e a cobertura fica em 90% ou mais.

## 2. Conferir e aplicar as migrations

```bash
python manage.py makemigrations --check --dry-run
python manage.py safe_migrate
```

Esperado: nenhuma migration pendente na verificação; `safe_migrate` aplica as migrations de `audiences`
e `activities`, e o grupo "Administrador" passa a incluir as permissões dos novos modelos.

## 3. Carga inicial

```bash
python manage.py seed_catalog
python manage.py seed_catalog
```

Esperado: a primeira execução cria as 5 opções de público (as demais já existiam); a segunda não cria
nada. Ver `contracts/management-commands.md`.

## 4. Verificar no painel

Com `DJANGO_DEBUG=true`, rode `python manage.py runserver` e entre em `/admin/`. Detalhes em
`contracts/admin-activities.md`.

1. Em "Atividades", cadastre uma atividade só com título, descrição, unidade e categoria. Ela nasce
   como "Rascunho", com "criada por" e "atualizada por" preenchidos e o identificador gerado.
2. Tente salvar sem título, e com link externo `ftp://x`. Ambos são recusados com mensagem no campo.
3. Adicione dois públicos no inline e repita um deles. O repetido é recusado. Salve com os dois.
4. Selecione a atividade e use "Publicar selecionadas" sem público (crie outra rascunho sem público
   para testar). A publicação é recusada com o motivo; a com públicos passa a "Publicada".
5. Cancele a atividade publicada ("Cancelar selecionadas") e depois publique de novo. As situações
   mudam e "atualizada por" e a data refletem cada ação.
6. Marque outra como encerrada. O registro continua na lista, filtrável por situação.
7. Em "Públicos-alvo", desative uma opção já usada. A atividade vinculada continua com o vínculo; ao
   editar uma atividade nova, a opção não aparece.
8. Desative a unidade de uma atividade e edite o título dela. A edição é aceita.
9. Tente excluir uma atividade publicada. A exclusão não está disponível; em rascunho, está.
10. Entre com uma conta sem o grupo (ou saia) e abra `/admin/activities/activity/`. O acesso é negado.

## Resultado da validação

Em 2026-10-11: `safe_migrate` aplicado no RDS, `seed_catalog` executado duas vezes (5 públicos-alvo criados na primeira, nada na segunda) e roteiro manual do painel (seção 4, passos 1 a 10) concluído pela equipe.
