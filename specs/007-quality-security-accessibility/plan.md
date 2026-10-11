# Implementation Plan: Qualidade, Segurança e Acessibilidade

**Branch**: `007-quality-security-accessibility` | **Date**: 2026-10-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/007-quality-security-accessibility/spec.md`

## Summary

Consolidar os requisitos transversais do EP-07 sobre o código das features 002 a 006, sem modelos,
migrations nem rotas públicas novas. A auditoria (US-030), a validação de formulários e de serviço
(US-029) e a consulta anônima (US-027) já existem; a investigação (ver [research.md](research.md))
achou **três lacunas reais** e um conjunto de garantias que hoje não têm teste de regressão:

1. **Erros inesperados**: o *exception handler* devolve `None` para exceções que não são da DRF, o que
   deixa o Django responder 500 (página HTML, com rastreamento de pilha se `DEBUG=True`). Passa a
   devolver JSON genérico e a registrar o erro só no log do servidor.
2. **Rotas inexistentes e 500 fora das views DRF**: `handler404`/`handler500` JSON para caminhos sob
   `/api/`, mantendo as páginas padrão do Django no `/admin/`.
3. **Página inválida**: `?page=abc` ou fora do intervalo hoje vira "Não encontrado."; passa a ser erro
   de validação em `errors.page`, com mensagem que diz o que corrigir.

O restante é **protegê-lo com testes** (matriz FR → teste): varredura de campos proibidos em todas as
respostas públicas, somente-leitura/405 em todo método de escrita, auditoria por todos os caminhos
(formulário, inline, ação em massa, `change_status`), `on_delete=PROTECT` nos autores, e validações de
entrada. Entram também dois documentos: política de auditoria (contas removidas e rotinas automáticas)
e a divisão backend/frontend para acessibilidade ([contracts/](contracts/)).

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: Django 6.1, Django REST Framework 3.18, django-cors-headers. Nenhuma
dependência nova.

**Storage**: PostgreSQL no AWS RDS. **Nenhuma tabela, coluna ou migration nova**; a suíte deve
continuar passando em `makemigrations --check` (verificação de que o estado dos modelos não mudou).

**Testing**: pytest, pytest-django, pytest-cov; somente testes unitários com mocks, sem banco, cobertura
total >= 90% (hoje 100%, 421 testes). Views e handlers com `APIRequestFactory`/`RequestFactory`;
admin com `RequestFactory` e objetos simulados; modelos e `on_delete` por introspecção de `_meta`.

**Target Platform**: execução local, sem hospedagem

**Project Type**: web-service (API do Django + Django Admin; o frontend fica em outro repositório)

**Performance Goals**: sem meta nova. O tratamento de erro não adiciona consultas ao banco.

**Constraints**: nenhuma resposta, em qualquer `DEBUG`, contém pilha, caminho, SQL, configuração ou
segredo; erros em JSON único (`detail` + `errors` por campo); mensagens em português; logs sem
credenciais; `/admin/` mantém as páginas do Django.

**Scale/Scope**: 3 pontos de código novos ou alterados (`apps/core/exceptions.py`, `config/urls.py` +
views de erro em `apps/core`, `apps/consultation/pagination.py`), ~6 módulos de teste novos, 3
documentos.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio / regra (v1.1.0) | Avaliação | Situação |
|---|---|---|
| I. Django Admin como interface de gestão | Nenhuma tela nova; auditoria e validação ficam na administração e nos serviços existentes. Leitura pública continua sem login; toda escrita exige admin. | OK |
| II. Django ORM no PostgreSQL | Nenhuma persistência nova; sem migrations. | OK |
| III. Código testado, cobertura >= 90% | Cada FR tem teste unitário com mocks, sem banco; `--cov-fail-under=90` segue ativo. | OK |
| IV. API REST pública e filtrável | Só `PUBLISHED` público (verificado por teste); erros em JSON consistente com status corretos — esta feature fecha as lacunas de 404/500/página. | OK |
| V. Acessibilidade, segurança e simplicidade | Dados textuais e erros por campo garantidos por teste; sem segredos em resposta ou log; YAGNI: nada além do EP-07. | OK |
| Stack e restrições | Local apenas; nenhuma dependência nova; hospedagem fora do escopo. | OK |
| Fluxo e portões | specify → plan → tasks → implement; PR com revisão. | OK |

Sem violações; a tabela de complexidade não se aplica.

**Reavaliação pós-design**: mantida. O design não adiciona app, modelo, dependência ou rota pública.

## Project Structure

### Documentation (this feature)

```text
specs/007-quality-security-accessibility/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── error-format.md
│   ├── audit-policy.md
│   └── accessibility-handoff.md
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit-tasks (não criado aqui)
```

### Source Code (repository root)

```text
apps/core/
├── exceptions.py        # handler: 500 genérico + log; mensagens por campo (alterado)
├── error_views.py       # handler404/handler500 JSON para /api/ (novo)
apps/consultation/
└── pagination.py        # página inválida vira ValidationError em `page` (alterado)
config/
└── urls.py              # handler404 / handler500 (alterado)

tests/unit/
├── core/
│   ├── test_exception_handler.py     # 500 genérico, sem vazamento, log sem segredo
│   ├── test_error_views.py           # 404/500 JSON em /api/, padrão fora dela
│   └── test_error_messages.py        # formato único, português, por campo
├── consultation/
│   ├── test_public_privacy.py        # varredura de campos proibidos; 405 de escrita; anônimo
│   └── test_pagination_errors.py     # página inválida
├── activities/ , schedules/
│   └── test_audit_paths.py           # criador/atualizador/horários por todos os caminhos
└── config/
    └── test_author_protection.py     # on_delete=PROTECT em created_by/updated_by
```

**Structure Decision**: sem app novo. O comportamento de erro é transversal e já mora em `apps/core`
(`exceptions.py`); as views de erro entram ali. A paginação continua em `consultation`, onde está a
classe. Testes seguem a árvore `tests/unit/<app>` existente.

## Complexity Tracking

Sem violações a justificar.
