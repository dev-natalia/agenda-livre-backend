from django.core.management.base import BaseCommand

from apps.audiences.models import TargetAudience
from apps.categories.models import Category
from apps.units.models import Unit

# O bairro do CEU Navegantes é provisório e deve ser confirmado pela equipe.
UNITS = [
    {"slug": "ceu-navegantes", "name": "CEU Navegantes", "neighborhood": "Cantinho do Céu"},
]

# Categorias iniciais propostas em docs/01-visao-do-produto-e-requisitos.md (seção 9).
CATEGORIES = [
    {
        "slug": "cultura-e-artes",
        "name": "Cultura e Artes",
        "description": "Teatro, dança, música, cinema, biblioteca, exposições e artesanato.",
    },
    {
        "slug": "cursos-e-formacao",
        "name": "Cursos e Formação",
        "description": "Cursos, oficinas, palestras, seminários e encontros formativos.",
    },
    {
        "slug": "esporte-e-atividade-fisica",
        "name": "Esporte e Atividade Física",
        "description": "Ginástica, lutas, esportes coletivos e condicionamento físico.",
    },
    {
        "slug": "lazer-e-recreacao",
        "name": "Lazer e Recreação",
        "description": "Jogos, brincadeiras e atividades recreativas.",
    },
    {
        "slug": "saude-e-bem-estar",
        "name": "Saúde e Bem-estar",
        "description": "Alongamento e atividades de promoção do bem-estar.",
    },
    {
        "slug": "educacao-e-meio-ambiente",
        "name": "Educação e Meio Ambiente",
        "description": "Educação ambiental e atividades educativas.",
    },
    {
        "slug": "eventos-e-encontros",
        "name": "Eventos e Encontros",
        "description": "Festivais, apresentações e encontros comunitários.",
    },
    {
        "slug": "participacao-comunitaria",
        "name": "Participação Comunitária",
        "description": "Reuniões, conselhos e atividades de participação da comunidade.",
    },
]


# Opções iniciais de público-alvo; a lista é provisória e pode ser mantida pelo Admin.
TARGET_AUDIENCES = [
    {"slug": "criancas", "name": "Crianças"},
    {"slug": "adolescentes", "name": "Adolescentes"},
    {"slug": "adultos", "name": "Adultos"},
    {"slug": "pessoas-idosas", "name": "Pessoas idosas"},
    {"slug": "todas-as-idades", "name": "Todas as idades"},
]


def _load(manager, items):
    created = 0
    for item in items:
        defaults = {key: value for key, value in item.items() if key != "slug"}
        _, was_created = manager.get_or_create(slug=item["slug"], defaults=defaults)
        created += was_created
    return created, len(items) - created


class Command(BaseCommand):
    help = "Carrega a unidade e as categorias iniciais (seguro para repetir)."

    def handle(self, *args, **options):
        for label, manager, items in (
            ("Unidades", Unit.objects, UNITS),
            ("Categorias", Category.objects, CATEGORIES),
            ("Públicos-alvo", TargetAudience.objects, TARGET_AUDIENCES),
        ):
            created, existing = _load(manager, items)
            self.stdout.write(f"{label}: {created} criada(s), {existing} já existiam.")
