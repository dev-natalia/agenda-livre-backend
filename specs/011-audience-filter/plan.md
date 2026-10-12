# Implementation Plan: Filtro por Público-alvo

**Branch**: `011-audience-filter` | **Date**: 2026-10-12 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/011-audience-filter/spec.md`

## Summary

Filtrar a consulta pública de atividades por público-alvo, com a regra inclusiva de “Todas as idades”,
listar os públicos para o frontend e mostrá-los em cada item da listagem. A investigação (ver
[research.md](research.md)) fixou o desenho em seis partes:

1. **Catálogo**: campo `includes_everyone` (booleano, padrão falso) em `TargetAudience`, com uma migration
   aditiva em `audiences`. A regra inclusiva usa só essa marca, nunca o nome nem o `slug`.
2. **Filtro** (`apps/consultation/services.py`): `Criteria` ganha `audience`; `apply_criteria` filtra em
   Python sobre a lista já carregada, como já faz com busca e bairro. Cada atividade é examinada uma vez,
   então não há duplicatas. Uma única consulta busca o público escolhido (ativo) para saber se ele é o
   “abrange todos”; público inexistente ou inativo devolve lista vazia sem outra consulta.
3. **Parâmetro** (`ConsultationQuerySerializer`): `audience` como UUID opcional, com a mesma mensagem de
   erro de `unit` e `category`.
4. **Recurso novo**: `GET /api/v1/audiences/`, no mesmo padrão de `/units/` e `/categories/`.
5. **Listagem**: cada item traz `target_audiences` (id e nome, ordenados por nome). A relação passa a ser
   carregada junto com as demais (`prefetch_related`), então o número de consultas não cresce por item.
6. **Admin e carga**: `includes_everyone` editável no cadastro de públicos; filtro por público na lista de
   atividades (opções ativas mais inativas com vínculo); `seed_catalog` marca “Todas as idades”, também em
   catálogo que já existia. DOC-03, DOC-05, contrato público e README são atualizados.

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: Django 6.1, Django REST Framework 3.18, django-cors-headers, django-environ,
Pillow, django-storages, boto3. **Nenhuma dependência nova.**

**Storage**: PostgreSQL no AWS RDS. Uma migration aditiva em `audiences` (uma coluna booleana com padrão
falso; nenhuma linha existente é alterada). Nenhuma tabela nova.

**Testing**: pytest, pytest-django, pytest-cov; somente testes unitários, sem banco, cobertura total >= 90%.
A lógica do filtro é Python puro sobre objetos em memória (`SimpleNamespace`), a consulta do público escolhido
é simulada, e o filtro do Admin é testado com `RequestFactory` e dublês, como os testes de consulta e de Admin
existentes. A verificação com SQL real fica para o roteiro do `quickstart.md`, contra o RDS.

**Target Platform**: execução local, sem hospedagem

**Project Type**: web-service (API do Django + Django Admin; o frontend fica em outro repositório)

**Performance Goals**: sem meta nova. A listagem mantém o mesmo número de consultas independentemente da
quantidade de atividades: a relação de públicos entra no `prefetch_related` (uma consulta a mais no total) e
o público escolhido exige no máximo uma consulta, apenas quando o filtro é usado.

**Constraints**: mudança aditiva (nenhum campo, parâmetro ou comportamento existente muda); um único valor
em `audience`; mensagens em português; nenhum dado administrativo nas respostas; a marca `includes_everyone`
nunca sai na API pública.

**Scale/Scope**: 1 migration, 1 view e 1 serializer novos, alterações em 7 arquivos existentes (modelo de
público-alvo, serviço e serializers de consulta, views e URLs, Admin de públicos e de atividades,
`seed_catalog`), testes novos e ampliados, 4 documentos.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Avaliação |
|-----------|-----------|
| I. Django Admin como interface de gestão | **Passa.** A marca “abrange todos” e o filtro de atividades são do Django Admin; nenhuma tela nova. A API continua só de leitura. |
| II. Django ORM no PostgreSQL (RDS) | **Passa.** Campo e migration pelo ORM; nenhuma credencial nova. |
| III. Testes, cobertura de 90% | **Passa.** Tudo é testável com dublês e sem banco; a lógica do filtro é Python puro. O SQL real é conferido manualmente no roteiro, não nos testes. |
| IV. API REST pública e filtrável | **Passa.** O Princípio IV foi atualizado (v1.2.0, 2026-10-12) para citar o público-alvo entre os filtros. Os contratos estão em [contracts/](contracts/) antes da implementação; só `PUBLISHED` é público; erros seguem o formato JSON existente. |
| V. Acessibilidade, segurança e simplicidade | **Passa.** Nada de dado administrativo ou pessoal exposto; filtro simples, sem lógica no cliente; YAGNI: um único público por consulta, sem contagens nem ordenação por público. |
| Stack e restrições | **Passa.** Sem dependência nem serviço novo. |

Nenhuma violação; a tabela de complexidade não se aplica.

**Reavaliação após o design (Fase 1)**: sem mudança. O desenho adiciona uma view e um serializer, um campo e
algumas linhas de serviço, e nenhuma camada nova.

## Project Structure

### Documentation (this feature)

```text
specs/011-audience-filter/
├── plan.md              # Este arquivo
├── research.md          # Fase 0: decisões e alternativas
├── data-model.md        # Fase 1: campo novo, regra do filtro e fluxo de dados
├── quickstart.md        # Fase 1: roteiro de verificação
├── contracts/
│   ├── public-api-audience.md   # Parâmetro `audience`, recurso `/audiences/` e campo `target_audiences`
│   └── admin-audience.md        # Marca “abrange todos” e filtro da lista de atividades
├── checklists/
│   └── requirements.md
└── tasks.md             # Fase 2 (/speckit-tasks), não criado aqui
```

### Source Code (repository root)

```text
apps/
├── audiences/
│   ├── models.py            # + includes_everyone (booleano, padrão falso)
│   ├── admin.py             # + includes_everyone na lista e no filtro lateral
│   └── migrations/0002_targetaudience_includes_everyone.py   # NOVA (aditiva)
├── activities/
│   └── admin.py             # + AudienceListFilter em list_filter
├── consultation/
│   ├── services.py          # Criteria.audience; find_audience(); filtro em apply_criteria;
│   │                        # prefetch de target_audiences em published_activities
│   ├── serializers.py       # audience em ConsultationQuerySerializer; target_audiences na listagem;
│   │                        # AudienceItemSerializer (recurso novo)
│   ├── views.py             # AudienceListView
│   └── urls.py              # path("audiences/", ...)
└── core/management/commands/
    └── seed_catalog.py      # "Todas as idades" com includes_everyone=True; marca também no que já existe
tests/unit/
├── audiences/               # test_includes_everyone.py (novo)
├── activities/              # test_audience_list_filter.py (novo); test_activity_admin.py ajustado
├── consultation/            # test_audience_filter.py, test_audience_resource.py (novos);
│                            # test_serializers.py, test_image_field.py ajustados
└── core/                    # test_seed_catalog.py ajustado
docs/                        # DOC-03, DOC-05, DOC-10 (status)
specs/006-public-consultation/contracts/public-api.md   # contrato público atualizado
README.md                    # parâmetro, recurso e marca no Admin
```

**Structure Decision**: mantém o layout por aplicativos Django existente. O filtro mora onde os outros já
moram (`consultation/services.py`), o campo mora no modelo que descreve o público (`audiences`), e a
apresentação fica nos serializers. Nenhum aplicativo novo.

## Complexity Tracking

Sem violações a justificar.
