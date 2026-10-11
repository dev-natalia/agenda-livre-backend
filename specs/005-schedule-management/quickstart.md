# Quickstart: validar Gestão de Programações

Pré-requisitos: features 001 a 004 funcionando (`.env` preenchido, conta de administrador criada com
`create_admin`, `seed_catalog` executado e ao menos uma atividade publicada com público-alvo).

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

Esperado: nenhuma migration pendente na verificação; `safe_migrate` aplica a migration de `schedules`,
e o grupo "Administrador" passa a incluir as permissões dos novos modelos.

## 3. Verificar no painel

Com `DJANGO_DEBUG=true`, rode `python manage.py runserver` e entre em `/admin/`. Detalhes em
`contracts/admin-schedules.md`.

1. Abra uma atividade publicada e clique em "Adicionar programação". A atividade vem preenchida.
2. Cadastre uma programação **pontual** com data futura e horários válidos. Ela aparece na lista da
   atividade e em "Próximas ocorrências".
3. Tente salvar com término anterior ao início, com data final diferente da inicial (pontual) e
   marcando um dia da semana na pontual. Cada tentativa é recusada com a mensagem do contrato.
4. Cadastre uma programação **recorrente** com período de um mês, terça e quinta, 14:00-15:00. Tente
   antes sem dia: recusada. As próximas ocorrências listam só terças e quintas dentro do período.
5. Edite a recorrente trocando para sábado e salve duas vezes. Os dias não se repetem; "atualizada por"
   e a data refletem a edição (também quando só os dias mudam).
6. Cancele a atividade pela ação da lista. A lista de programações continua intacta, e "Próximas
   ocorrências" passa a mostrar o texto de atividade não publicada.
7. Tente excluir a atividade com programações: o Admin recusa. Exclua uma programação: a atividade
   permanece.
8. Entre com uma conta sem o grupo "Administrador": a rota de programações é recusada.

## Resultado da validação automatizada

2026-10-11: `pytest` com 275 testes passando e cobertura de 100%; `ruff check .` sem avisos;
`makemigrations --check --dry-run` sem pendências. A migration `schedules.0001_initial` foi aplicada no RDS com `safe_migrate`.

O roteiro da seção 3 (passos 1 a 8) foi executado contra o RDS pelo cliente de teste do Django, em uma
transação revertida ao final (sem dados residuais): 15 de 15 verificações passaram, incluindo atividade
pré-preenchida, as cinco recusas de validação, edição sem dias duplicados, autoria, atividade cancelada
com programações preservadas, exclusão de atividade com programações recusada e conta sem o grupo
"Administrador" recusada (403). A conferência visual no navegador não foi feita.
