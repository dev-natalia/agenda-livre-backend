# Implementation Plan: Páginas Informativas (Sobre e Contato)

**Branch**: `009-informational-pages` | **Date**: 2026-10-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/009-informational-pages/spec.md`

## Summary

Fechar o EP-09 no backend **sem criar funcionalidade**: Sobre e Contato são só frontend. A investigação
(ver [research.md](research.md)) mostrou que a ausência de rotas, modelos e cadastros já é verdadeira,
mas há **uma lacuna de código**: a rota coringa `^api/` devolve 404 em JSON, porém um `POST` real (com a
checagem de CSRF ativa) é barrado antes pelo `CsrfViewMiddleware` com **403 em HTML**. Um formulário de
contato do frontend que apontasse para a API receberia essa resposta em vez do erro padronizado. O plano
tem três partes:

1. **Correção mínima**: marcar `api_not_found` como isenta de CSRF. A view não lê o corpo nem tem efeito
   colateral, então a isenção é segura e faz todo método sob `/api/` inexistente devolver 404 em JSON.
2. **Testes de proteção de escopo**: verificar que nenhuma rota, modelo ou `ModelAdmin` trata contato ou
   Sobre; que `POST` a caminhos plausíveis (com CSRF ativo) devolve 404 JSON sem gravar nem logar o corpo.
3. **Documentação**: DOC-05 (seção "sem endpoints de Sobre e Contato"), README, DOC-04 (US-035/US-036 e
   histórico) e `docs/PENDENCIAS.md`.

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: Django 6.1, Django REST Framework 3.18, django-cors-headers, django-environ.
Nenhuma dependência nova.

**Storage**: PostgreSQL no AWS RDS. **Nenhuma tabela, coluna ou migration nova**
(`makemigrations --check` continua sem mudanças).

**Testing**: pytest, pytest-django, pytest-cov; somente testes unitários, sem banco, cobertura total >= 90%.
Rotas inspecionadas com `get_resolver()`; modelos com `django.apps`; admin com `admin.site._registry`;
`Client(enforce_csrf_checks=True)` para o caso de CSRF; `caplog` para provar que nada é logado.

**Target Platform**: execução local, sem hospedagem

**Project Type**: web-service (API do Django + Django Admin; o frontend fica em outro repositório)

**Performance Goals**: sem meta nova.

**Constraints**: nenhuma rota, modelo ou cadastro administrativo de contato/Sobre; resposta padronizada
`{"detail": "Não encontrado."}` com status 404; nenhum corpo de requisição gravado ou logado; resposta ao
visitante das demais rotas inalterada.

**Scale/Scope**: 1 arquivo de código alterado (`apps/core/error_views.py`, um decorador), 1 módulo de teste
novo e 1 teste ampliado, 4 documentos.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio / regra (v1.1.0) | Avaliação | Situação |
|---|---|---|
| I. Django Admin como interface de gestão | Nenhuma tela, rota ou autenticação nova; o admin não ganha cadastro de contato/Sobre. | OK |
| II. Django ORM no PostgreSQL | Sem persistência nova; nenhuma migration. | OK |
| III. Código testado, cobertura >= 90% | Cada FR tem teste unitário sem banco; `--cov-fail-under=90` segue ativo. | OK |
| IV. API REST pública e filtrável | Contratos existentes inalterados; erros continuam em JSON padronizado, agora também para `POST` sem token CSRF sob `/api/`. | OK |
| V. Acessibilidade, segurança e simplicidade | Impede coleta não prevista de dados pessoais (contato); YAGNI: sem endpoint de contato nem de Sobre, como a constituição determina (Contato e Sobre só no frontend). | OK |
| Stack e restrições | Local apenas; nenhuma dependência nova. | OK |
| Fluxo e portões | specify → plan → tasks → implement; PR com revisão; README atualizado. | OK |

Sem violações; a tabela de complexidade não se aplica.

**Reavaliação pós-design**: mantida. O design não adiciona app, modelo, dependência, rota ou migration.
A isenção de CSRF vale só para a rota coringa que nunca lê o corpo nem altera estado.

## Project Structure

### Documentation (this feature)

```text
specs/009-informational-pages/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── no-informational-endpoints.md
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit-tasks (não criado aqui)
```

### Source Code (repository root)

```text
apps/core/error_views.py                      # alterado: api_not_found isenta de CSRF
tests/unit/core/test_error_views.py           # ampliado: POST com CSRF ativo -> 404 JSON
tests/unit/core/test_no_informational_pages.py  # novo: rotas, modelos, admin e logs
docs/04-backlog-do-produto.md                 # US-035/US-036 e histórico
docs/05-especificacao-api-rest.md             # seção "sem endpoints de Sobre e Contato"
docs/PENDENCIAS.md                            # sem item aberto de Sobre/Contato
README.md                                     # Sobre/Contato só frontend
```

**Structure Decision**: estrutura existente mantida (projeto Django único em `apps/` + `config/`). Nenhum
app novo: criar um app só para "provar a ausência" violaria YAGNI.

## Complexity Tracking

Sem violações a justificar.
