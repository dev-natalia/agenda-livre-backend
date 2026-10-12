# Implementation Plan: Imagens das Atividades

**Branch**: `010-activity-images` | **Date**: 2026-10-12 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/010-activity-images/spec.md`

## Summary

Permitir uma imagem opcional por atividade, guardada no Amazon S3 (bucket `agenda-livre-imagens`,
`sa-east-1`) e exposta na API pública como `image: {url, alt, decorative}` ou `null`. A investigação
(ver [research.md](research.md)) fixou o desenho em seis partes:

1. **Modelo**: três campos novos em `Activity` (`image`, `image_alt`, `image_decorative`) e uma migration
   aditiva. O nome do arquivo guardado é um UUID gerado, nunca o nome enviado.
2. **Validação e tratamento** (`apps/activities/images.py`): confere o conteúdo com Pillow (JPEG, PNG,
   WebP), os limites de 5 MB e de 400×300 a 6000×6000 px, corrige a orientação, reduz o lado maior a
   1600 px, recodifica e descarta os metadados. A regra do texto alternativo fica em `Activity.clean()`.
3. **Armazenamento**: `django-storages` (S3) em `STORAGES["default"]`, montado por `config/storage.py` a
   partir de variáveis de ambiente obrigatórias. Os testes trocam o armazenamento por memória.
4. **Admin**: o formulário da atividade trata e valida o envio; trocar, remover ou excluir apaga o arquivo
   antigo depois da transação, e a falha vai para o log local sem derrubar a operação.
5. **API pública**: o campo `image` entra na listagem e no detalhe. Como só atividades `PUBLISHED` chegam
   a essas respostas, a regra de visibilidade já existente cobre o FR-012.
6. **Demonstração e documentação**: `seed_demo` gera imagens fictícias com Pillow (sem rede e sem direitos
   de terceiros) e é idempotente; DOC-03, 04, 05, 08, contrato público, README e `PENDENCIAS-BACKEND.md`
   são atualizados.

## Technical Context

**Language/Version**: Python 3.14

**Primary Dependencies**: Django 6.1, Django REST Framework 3.18, django-cors-headers, django-environ.
**Novas (fixadas em `requirements.txt`)**: Pillow 12.3.0, django-storages 1.14.6 (extra S3) e boto3 1.43.111.

**Storage**: PostgreSQL no AWS RDS guarda só a referência (nome do objeto). Os arquivos ficam no Amazon S3.
Uma migration aditiva em `activities` (três colunas com valor padrão; nenhuma linha existente é alterada).

**Testing**: pytest, pytest-django, pytest-cov; somente testes unitários, sem banco, cobertura total >= 90%.
Armazenamento trocado por `InMemoryStorage` em `config/settings_test.py`; nenhum teste fala com a AWS. As
imagens de teste são geradas em memória com Pillow (sem arquivos binários no repositório).

**Target Platform**: execução local, sem hospedagem; o S3 é serviço de nuvem usado pelo desenvolvimento,
como já ocorre com o RDS.

**Project Type**: web-service (API do Django + Django Admin; o frontend fica em outro repositório)

**Performance Goals**: sem meta nova. O campo `image` não adiciona consultas, pois as colunas estão na
mesma linha da atividade já carregada; gerar a URL não acessa a rede.

**Constraints**: JPEG, PNG e WebP; 5 MB; 400×300 a 6000×6000 px; lado maior final de até 1600 px; sem EXIF;
nome do arquivo guardado aleatório; bucket com leitura pública só de objetos e sem listagem; credenciais
só em variáveis de ambiente e fora dos logs.

**Scale/Scope**: 1 migration, 1 módulo novo de imagens, 1 módulo novo de configuração de armazenamento,
alterações em 6 arquivos existentes (modelo, admin, serializers, `seed_demo`, `settings`, `env`), testes
novos e ampliados, 6 documentos.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Princípio | Avaliação |
|-----------|-----------|
| I. Django Admin como interface de gestão | **Passa.** O envio, a troca e a remoção acontecem no Django Admin com `ImageField`; nenhuma tela ou autenticação paralela. A API continua só de leitura. |
| II. Django ORM no PostgreSQL (RDS) | **Passa.** Campos e migration pelo ORM; credenciais por variável de ambiente; o banco guarda só a referência. |
| III. Testes, cobertura de 90% | **Passa, com atenção.** Armazenamento em nuvem é dependência externa e é trocado por dublê em memória; sem acesso a banco. Pillow roda de verdade nos testes porque é processamento puro em memória, não dependência externa. A montagem das opções do S3 é testada como função pura, sem importar `boto3`. |
| IV. API REST pública e filtrável | **Passa.** O contrato do campo novo está em [contracts/public-api-image.md](contracts/public-api-image.md), antes da implementação; só `PUBLISHED` é público; erros seguem o formato JSON existente; campos antigos não mudam. |
| V. Acessibilidade, segurança e simplicidade | **Passa.** O texto alternativo (ou a marcação de decorativa) é obrigatório quando há imagem; EXIF é removido; nome original nunca é usado; segredos ficam fora dos logs. YAGNI: uma imagem por atividade, sem miniaturas, sem galeria, sem CDN. |
| Stack e restrições | **Passa.** Dependências novas fixadas; nada de hospedagem. O S3 é armazenamento de arquivos, não implantação, e atende à exigência de uso de nuvem registrada no DOC-09. |

Nenhuma violação; a tabela de complexidade não se aplica.

**Reavaliação após o design (Fase 1)**: sem mudança. O desenho adiciona 2 módulos pequenos e nenhuma
camada nova (sem repositório, sem serviço de domínio além do módulo de imagens).

## Project Structure

### Documentation (this feature)

```text
specs/010-activity-images/
├── plan.md              # Este arquivo
├── research.md          # Fase 0: decisões e alternativas
├── data-model.md        # Fase 1: campos, regras e ciclo de vida do arquivo
├── quickstart.md        # Fase 1: roteiro de verificação
├── contracts/
│   ├── public-api-image.md   # Campo `image` nas respostas públicas
│   └── admin-image-upload.md # Regras e mensagens do envio pelo Admin
├── checklists/
│   └── requirements.md
└── tasks.md             # Fase 2 (/speckit-tasks), não criado aqui
```

### Source Code (repository root)

```text
apps/
├── activities/
│   ├── models.py            # + image, image_alt, image_decorative; regra em clean(); upload_to
│   ├── images.py            # NOVO: validar/tratar imagem, nome aleatório, remoção segura de arquivo
│   ├── forms.py             # NOVO: ActivityAdminForm (clean_image chama images.py)
│   ├── admin.py             # usa o formulário, preview, apaga o arquivo antigo na troca/remoção
│   ├── signals.py           # NOVO: post_delete remove o arquivo da atividade excluída
│   ├── apps.py              # ready() registra os sinais
│   └── migrations/0002_activity_image.py   # NOVA (aditiva)
├── consultation/
│   └── serializers.py       # + campo `image` na listagem e no detalhe
└── core/management/commands/
    └── seed_demo.py         # + imagens fictícias geradas com Pillow, idempotente
config/
├── storage.py               # NOVO: build_storages(env) -> dict STORAGES
├── env.py                   # + variáveis AWS_* obrigatórias
├── settings.py              # STORAGES via build_storages; segredo AWS no mascaramento de logs
└── settings_test.py         # armazenamento em memória e variáveis AWS fictícias
requirements.txt             # + Pillow, django-storages[s3], boto3
tests/unit/
├── activities/              # test_image_processing.py, test_image_admin_form.py, test_image_admin.py,
│                            # test_image_cleanup.py, test_activity_image_model.py (novos)
├── consultation/            # test_image_field.py (novo)
├── config/                  # test_storage_settings.py (novo); test_env/conftest ajustados
└── core/                    # test_seed_demo_images.py (novo)
docs/                        # DOC-03, DOC-04, DOC-05, DOC-08, 09, PENDENCIAS-BACKEND.md
README.md                    # variáveis AWS_* e dependências novas
.env.example                 # já atualizado
```

**Structure Decision**: mantém o layout por aplicativos Django existente. O código novo fica onde cada
responsabilidade já mora: regras de dados no modelo, tratamento de arquivo em `images.py` (puro e testável
sem o Django), apresentação no serializer, configuração em `config/`. Nenhum aplicativo novo é criado.

## Complexity Tracking

Sem violações a justificar.
