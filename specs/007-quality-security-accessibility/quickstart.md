# Quickstart: validar Qualidade, Segurança e Acessibilidade

## Pré-requisitos

- Ambiente virtual com `requirements-dev.txt` instalado e variáveis do `.env` conforme o README.
- Os testes não acessam banco; só os cenários manuais 2 a 4 precisam do servidor local e do banco.

## 1. Suíte automatizada (principal)

```bash
python -m pytest
```

Esperado: todos os testes passam e a cobertura total fica em 90% ou mais (o `pyproject.toml` falha a
execução abaixo disso). Filtros úteis: `tests/unit/core`, `tests/unit/consultation`, `tests/unit/activities`,
`tests/unit/schedules`.

Também:

```bash
python manage.py makemigrations --check --dry-run   # esperado: "No changes detected"
python -m ruff check .                               # linter do projeto (esperado: sem erros)
```

## 2. Erros sem vazamento (servidor local)

Com `DJANGO_DEBUG=True` e depois `False`:

```bash
curl -i http://localhost:8000/api/v1/rota-que-nao-existe
curl -i "http://localhost:8000/api/v1/activities/?date=ontem"
curl -i "http://localhost:8000/api/v1/activities/?page=abc"
curl -i -X POST http://localhost:8000/api/v1/activities/
```

Esperado: JSON em todas; 404 `Não encontrado.`; 400 com `errors.date`; 400 com `errors.page`;
405 `Método não permitido.`. Nenhuma contém pilha, caminho ou configuração.

## 3. Privacidade pública

```bash
curl -s http://localhost:8000/api/v1/activities/ | python -m json.tool
```

Esperado: nenhum campo `created_by`, `updated_by`, `status`, `created_at`, `updated_at` ou de conta.
Uma atividade em rascunho consultada por identificador responde igual a um identificador inexistente.

## 4. Auditoria (administração)

1. Entre no `/admin/` com a conta A e crie uma atividade com uma programação.
2. Entre com a conta B e altere a atividade e a programação; depois publique pela ação em massa.
3. Esperado: "Criada por" = A em ambos; "Atualizada por" = B; "Atualizada em" posterior.
4. Tente remover a conta A: o sistema recusa (autoria protegida). Desative-a em vez disso.

## Referências

[spec.md](spec.md) · [plan.md](plan.md) · [data-model.md](data-model.md) ·
[contracts/error-format.md](contracts/error-format.md) · [contracts/audit-policy.md](contracts/audit-policy.md) ·
[contracts/accessibility-handoff.md](contracts/accessibility-handoff.md)
