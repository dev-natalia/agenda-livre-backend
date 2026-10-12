# Quickstart: validar o filtro por público-alvo

**Feature**: 011-audience-filter | Roteiro para provar, de ponta a ponta, que a feature funciona. Contratos:
[public-api-audience.md](contracts/public-api-audience.md) e [admin-audience.md](contracts/admin-audience.md).
Campo e regra: [data-model.md](data-model.md).

## Pré-requisitos

- `.env` completo (banco e `AWS_*`); `pip install -r requirements-dev.txt`.
- Um administrador existente (`python manage.py create_admin <usuario>`).
- Catálogo e dados de demonstração carregados (`seed_catalog` e `seed_demo`), pois o roteiro usa os cinco
  públicos e as 15 atividades fictícias.

## 1. Testes automatizados (sem banco, sem AWS)

```bash
python -m pytest
python -m ruff check .
python manage.py makemigrations --check --dry-run   # só a migration 0002 de audiences antes de aplicá-la
```

Esperado: tudo passa, cobertura total de pelo menos 90% e linter limpo.

## 2. Aplicar a migration e marcar “Todas as idades”

```bash
python manage.py safe_migrate
python manage.py seed_catalog
python manage.py seed_catalog   # segunda execução
```

Esperado: `audiences.0002_targetaudience_includes_everyone` aplicada; a 1ª execução do `seed_catalog` marca
“Todas as idades” (e só ela); a 2ª não muda nada e não cria registros.

## 3. Cenários manuais (API e Admin)

Suba o servidor com `python manage.py runserver`.

| # | Passo | Resultado esperado |
|---|-------|--------------------|
| 1 | `GET /api/v1/audiences/` | 5 públicos ativos, por nome, com `id`, `name`, `slug`, `description`; sem `is_active` nem a marca |
| 2 | Desativar um público no Admin e repetir o passo 1 | o público sai da lista; reativar o traz de volta |
| 3 | `POST /api/v1/audiences/` | `405` `{"detail": "Método não permitido."}` |
| 4 | `GET /api/v1/activities/?audience=<Adultos>` | atividades de “Adultos” **e** de “Todas as idades”, nenhuma só de “Crianças” |
| 5 | `GET /api/v1/activities/?audience=<Todas as idades>` | somente as atividades vinculadas a “Todas as idades” |
| 6 | Atividade com “Adultos” e “Todas as idades” | aparece uma única vez; `count` bate com a lista |
| 7 | `?audience=abc` | `400` com `errors.audience` = “Informe um identificador válido.”; `?audience=` (vazio) é ignorado e devolve a listagem completa |
| 8 | `?audience=<UUID válido inexistente>` e `?audience=<UUID de público inativo>` | `200`, `count: 0` |
| 9 | `?audience=<Adultos>&unit=<uma unidade>` e `&category=…`, `&q=…`, `&date_from=…` | só atividades que atendem a todos os filtros |
| 10 | `?audience=<id>&date=2026-11-01&date_from=2026-11-01` | o mesmo `400` de antes (erro em `date`); `audience` não muda essa validação |
| 11 | Atividade em rascunho, cancelada e encerrada vinculadas ao público | nunca aparecem, com ou sem filtro |
| 12 | `GET /api/v1/activities/` sem `audience` | mesmos itens e ordem de antes; cada item traz `target_audiences` (por nome; `[]` sem público) |
| 13 | Desmarcar “Abrange todos os públicos” em “Todas as idades” (Admin) e repetir o passo 4 | as atividades de “Todas as idades” deixam de entrar; remarcar as traz de volta |
| 14 | Marcar outro público como “abrange todos” e filtrar por um terceiro | as atividades do público marcado entram; desfazer a marca no fim |
| 15 | Admin → Atividades → filtro “Público-alvo” | lista os ativos e os inativos com vínculo; escolher um mostra as atividades dele, uma vez cada |
| 16 | Contar consultas ao banco da listagem com 5 e com 15 atividades | o mesmo número nos dois casos |

## 4. Verificação de segredos

- `git status` não mostra `.env`; nenhuma resposta pública traz `is_active`, `includes_everyone`, `created_by`
  nem `updated_by`.

## Critérios de pronto

Todos os cenários acima passam e os itens SC-001 a SC-011 da [spec](spec.md) estão atendidos. Os cenários 13
e 14 alteram dados do cadastro; desfaça-os ao terminar (ou rode-os em atividades e públicos de teste).

## Resultado da verificação no ambiente real (2026-10-12)

Executada contra o RDS real, por script usando o cliente de teste do Django (API pública e páginas do Admin).
Não foi feita pelo navegador. As atividades e o público de teste (`ZZ Teste …`) foram criados e apagados no
próprio script, e as marcas alteradas durante o teste foram restauradas.

- **Migration e carga:** `audiences.0002_targetaudience_includes_everyone` aplicada com `safe_migrate`;
  `seed_catalog` marcou apenas “Todas as idades”; a 2ª execução não mudou nada.
- **Cenários 1 a 16:** 41 de 41 verificações passaram. Para cada um dos cinco públicos, o resultado da API foi
  comparado com um cálculo independente feito pelo ORM (mesmos ids, sem duplicatas, `count` igual ao tamanho
  da lista). Também passaram: `audience=abc` (400 em `errors.audience`), `audience=` vazio (ignorado), UUID
  inexistente e público inativo (lista vazia), combinação com `unit`, `category`, `q` e `date_from`, o 400 de
  `date` + `date_from` inalterado, atividades em rascunho/canceladas/encerradas nunca aparecendo,
  `target_audiences` por nome (e `[]` sem público), desmarcar e remarcar a marca, marcar outro público,
  o filtro do Admin e a caixa “Abrange todos os públicos”, e 5 consultas ao banco antes e depois de criar
  mais atividades (constante).
- **Verificações mais fracas** (não provam sozinhas): o item “Admin: filtro mostra só as vinculadas” confere a
  ausência de atividades de teste não vinculadas, e “‘Adultos’ inclui atividades de ‘Todas as idades’” aceita
  o caso sem atividades dessa opção; a comprovação forte dessas regras é a comparação com o ORM (cenários 4 a 6)
  e os cenários 13 e 14.
- **Não verificado:** uso pelo navegador.
