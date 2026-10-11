# Implementation Plan: Consulta Pública de Atividades

**Branch**: `006-public-consultation` | **Date**: 2026-10-11 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/006-public-consultation/spec.md`

## Summary

Expor, em um app novo `consultation`, a API pública de leitura sob `/api/v1/`: listagem de atividades
publicadas (com busca, filtros e paginação), detalhe de atividade, e listas de unidades e categorias
ativas. Não há modelos nem migrations novos. Cada view é fina e só lê: sem autenticação, sem sessão,
apenas `GET`. A lógica fica em funções puras (`services.py`): normalização de texto (sem acento e sem
caixa), busca e filtro de bairro em Python sobre o conjunto já filtrado no banco por situação
`PUBLISHED`, unidade e categoria; cálculo da próxima ocorrência e do filtro de data reaproveitando o
serviço de ocorrências da feature 005, estendido com janela de datas (`from_date`/`to_date`) e com
suporte a atividades já com programações pré-carregadas. A ordenação (próxima ocorrência, horário,
título) e a paginação (`page`, `page_size`) são aplicadas em memória sobre a lista resultante, o que é
adequado à escala do projeto (centenas de atividades, uma instância local) e mantém tudo testável sem
banco. Os parâmetros de consulta são validados por um serializer; erros saem em JSON consistente por
um *exception handler* único.

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: Django 6.1, Django REST Framework 3.18 (views, serializers, paginação),
django-cors-headers (já configurado). Nenhuma dependência nova.

**Storage**: PostgreSQL no AWS RDS, somente leitura nesta feature. Nenhuma tabela, índice ou migration
nova (os índices por situação, unidade e categoria da feature 004 já cobrem as consultas).

**Testing**: pytest, pytest-django e pytest-cov, somente testes unitários com mocks, sem acesso a
banco, cobertura total >= 90%. Regras (normalização, busca, filtros, janela de datas, ordenação) são
funções puras testadas com objetos em memória e relógio injetado; views e serializers são testados
com `APIRequestFactory` e os serviços simulados.

**Target Platform**: execução local, sem hospedagem

**Project Type**: web-service (API pública do Django; o frontend fica em outro repositório)

**Performance Goals**: 95% das consultas em menos de 2 s com até 1.000 atividades publicadas (SC-006).
Estratégia: 1 consulta de atividades (`select_related` unidade e categoria) + 2 de `prefetch`
(programações e dias) por requisição, independente do tamanho da página; a próxima ocorrência de cada
atividade é achada saltando para o próximo dia da semana válido (no máximo 7 passos por programação),
não varrendo o período dia a dia.

**Constraints**: somente `GET`; sem autenticação e sem leitura de cabeçalhos de credenciais; só
`PUBLISHED` (constante `PUBLIC_STATUSES`); nenhum campo de auditoria ou de conta na resposta; erros
JSON sem detalhes internos; fuso `America/Sao_Paulo`; sem cache, limitação de taxa nem ordenação
escolhida pela pessoa visitante.

**Scale/Scope**: 1 app novo, 4 rotas (atividades, detalhe, unidades, categorias), ~5 serializers, 1
módulo de serviço, 1 *exception handler*, 1 classe de paginação.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio / regra (v1.1.0) | Avaliação | Situação |
|---|---|---|
| I. Django Admin como interface de gestão; leitura pública sem login; escrita exige admin | Sem telas novas; endpoints só de leitura e sem login; escrita continua só no Admin (métodos diferentes de `GET` retornam 405) | Passa |
| II. Django ORM no PostgreSQL (RDS) | Apenas consultas do ORM em modelos existentes; sem SQL cru, sem extensão (`unaccent`) nem migration | Passa |
| III. Testes unitários, mocks, sem banco, cobertura >= 90% | Lógica em funções puras; views com serviços simulados; banco bloqueado mantido; toda user story e endpoint com teste | Passa |
| IV. API REST pública e filtrável; só PUBLISHED; erros JSON consistentes; contratos documentados antes | Listagem, busca e filtros por unidade, categoria e data; `PUBLIC_STATUSES` aplicado em todas as rotas; handler único de erros; contrato em `contracts/public-api.md` | Passa |
| V. Acessibilidade, segurança e simplicidade (YAGNI) | Campos estruturados (dias da semana também por extenso, horários `HH:MM`); sem dados de auditoria; sem endpoints de detalhe de unidade/categoria, sem ordenação escolhida, sem cache | Passa |
| Stack e fluxo: Python 3.14, local apenas, PEP 8, CORS para o frontend, README | CORS já configurado (middleware e `CORS_ALLOWED_ORIGINS`); README ganha seção da API pública | Passa |

Sem violações. A seção Complexity Tracking não se aplica.

**Re-avaliação pós-design (Phase 1)**: o design adiciona um app sem modelos, leitura em memória sobre o
conjunto filtrado e extensão retrocompatível do serviço de ocorrências. Sem dependências novas, sem
escrita, sem exposição de dados privados. Continua sem violações.

## Project Structure

### Documentation (this feature)

```text
specs/006-public-consultation/
├── plan.md              # Este arquivo
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/           # Phase 1
│   ├── public-api.md
│   └── occurrences-service.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
apps/consultation/
├── __init__.py
├── apps.py                  # ConsultationConfig
├── services.py              # normalize_text(), parse de critérios, search/filtros, ordenação, listagem
├── serializers.py           # ConsultationQuerySerializer + serializers de leitura (lista, detalhe, unidade, categoria)
├── pagination.py            # PublicPagination (page_size 12, máx. 50)
├── views.py                 # PublicAPIView base; ActivityListView, ActivityDetailView, UnitListView, CategoryListView
└── urls.py                  # rotas sob /api/v1/
apps/core/exceptions.py      # public_exception_handler: formato único de erro JSON
apps/schedules/services.py   # + first_occurrence() e janela de datas em iter_occurrences/upcoming_occurrences
config/settings.py           # + "apps.consultation" em INSTALLED_APPS; EXCEPTION_HANDLER
config/urls.py               # + include("apps.consultation.urls")
tests/unit/
├── consultation/test_services.py
├── consultation/test_serializers.py
├── consultation/test_views.py
├── consultation/test_pagination.py
├── core/test_exceptions.py
├── schedules/test_occurrences_service.py    # amplia o teste existente
└── config/test_structure.py                 # + apps.consultation
README.md                    # seção sobre a API pública
```

**Structure Decision**: um app próprio (`consultation`) separa a leitura pública dos apps de dados, que
continuam com modelos e Admin, e evita que `core` cresça. O cálculo de ocorrências permanece em
`schedules.services` (uma só regra, FR-018) e ganha apenas parâmetros opcionais de janela. Busca e
filtro de bairro sem acento ficam em Python (ver pesquisa, item 1) para não exigir a extensão
`unaccent` no RDS nem testes com banco.
