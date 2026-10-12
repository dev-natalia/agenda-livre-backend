import hashlib
import io
from datetime import date, datetime, timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from PIL import Image, ImageDraw

from apps.activities.images import process_image
from apps.activities.models import Activity, ActivityTargetAudience
from apps.audiences.models import TargetAudience
from apps.categories.models import Category
from apps.core.management.commands.seed_catalog import _load
from apps.schedules.models import Schedule, ScheduleWeekday
from apps.units.models import Unit

# Dados fictícios de demonstração. A unidade não tem campo de telefone; ele vai na descrição.
UNITS = [
    {
        "slug": "ceu-cidade-dutra",
        "name": "CEU Cidade Dutra",
        "neighborhood": "Interlagos",
        "address": "Av. Interlagos, 7350 - Interlagos, São Paulo - SP, 04777-000",
        "description": "Telefone: (11) 5668-1935",
    },
    {
        "slug": "ceu-vila-rubi",
        "name": "CEU Vila Rubi",
        "neighborhood": "Vila Rubi",
        "address": "R. Domingos Tarroso, 101 - Vila Rubi, São Paulo - SP, 04823-090",
        "description": "Telefone: (11) 5662-9400",
    },
    {
        "slug": "ceu-vila-do-sol",
        "name": "CEU Vila do Sol",
        "neighborhood": "Vila do Sol",
        "address": "Av. dos Funcionários Públicos, 369 - Vila do Sol, São Paulo - SP, 04962-000",
        "description": "Telefone: (11) 3397-9800",
    },
]

DRAFT, PUBLISHED, FINISHED, CANCELLED = "DRAFT", "PUBLISHED", "FINISHED", "CANCELLED"
SEG, TER, QUA, QUI, SEX, SAB, DOM = 1, 2, 3, 4, 5, 6, 7


def one_time(days, start, end):
    """Programação pontual, `days` dias a partir de hoje (negativo = passado)."""
    return {"type": "ONE_TIME", "from_days": days, "to_days": days, "start": start, "end": end}


def recurring(from_days, to_days, weekdays, start, end):
    """Programação recorrente entre `from_days` e `to_days` dias a partir de hoje."""
    return {
        "type": "RECURRING",
        "from_days": from_days,
        "to_days": to_days,
        "weekdays": weekdays,
        "start": start,
        "end": end,
    }


ACTIVITIES = [
    # CEU Navegantes (carregado por seed_catalog)
    {
        "title": "Capoeira para todas as idades",
        "unit": "ceu-navegantes",
        "category": "esporte-e-atividade-fisica",
        "audiences": ["todas-as-idades"],
        "summary": "Aulas de capoeira com roda aberta ao final de cada encontro.",
        "description": "Aulas conduzidas por mestre de capoeira, com ginga, golpes básicos, "
        "musicalidade e história da capoeira. Traga roupa confortável.",
        "status": PUBLISHED,
        "schedules": [recurring(-14, 90, [TER, QUI], "18:30", "20:00")],
    },
    {
        "title": "Hora do conto na biblioteca",
        "unit": "ceu-navegantes",
        "category": "cultura-e-artes",
        "audiences": ["criancas"],
        "summary": "Contação de histórias e brincadeiras com livros para crianças.",
        "description": "Encontro semanal de leitura em voz alta, com histórias, fantoches e "
        "empréstimo de livros infantis. Crianças menores devem vir acompanhadas.",
        "status": PUBLISHED,
        "schedules": [recurring(-7, 60, [SAB], "10:00", "11:00")],
    },
    {
        "title": "Curso de informática básica",
        "unit": "ceu-navegantes",
        "category": "cursos-e-formacao",
        "audiences": ["adultos", "pessoas-idosas"],
        "summary": "Primeiros passos com computador, internet e e-mail.",
        "description": "Curso introdutório de 8 semanas: uso do mouse e do teclado, navegação "
        "na internet, criação de e-mail e segurança básica. Vagas limitadas.",
        "external": "https://exemplo.org/inscricao/informatica-basica",
        "status": DRAFT,
        "schedules": [recurring(14, 70, [SEG, QUA], "14:00", "16:00")],
    },
    # CEU Cidade Dutra
    {
        "title": "Hidroginástica",
        "unit": "ceu-cidade-dutra",
        "category": "esporte-e-atividade-fisica",
        "audiences": ["adultos", "pessoas-idosas"],
        "summary": "Exercícios na piscina com baixo impacto para as articulações.",
        "description": "Aula coletiva na piscina com orientação de professor de educação física. "
        "É necessário apresentar atestado médico e usar touca e roupa de banho.",
        "status": PUBLISHED,
        "schedules": [recurring(-21, 80, [SEG, QUA, SEX], "08:00", "09:00")],
    },
    {
        "title": "Oficina de teatro para adolescentes",
        "unit": "ceu-cidade-dutra",
        "category": "cultura-e-artes",
        "audiences": ["adolescentes"],
        "summary": "Jogos teatrais, improvisação e montagem de uma pequena peça.",
        "description": "Oficina com jogos teatrais, expressão corporal e voz, que termina com uma "
        "apresentação aberta à comunidade no teatro do CEU.",
        "status": PUBLISHED,
        "schedules": [
            recurring(-10, 49, [QUA], "15:30", "17:30"),
            one_time(56, "19:00", "20:30"),
        ],
    },
    {
        "title": "Cine CEU: sessão de curtas brasileiros",
        "unit": "ceu-cidade-dutra",
        "category": "eventos-e-encontros",
        "audiences": ["todas-as-idades"],
        "summary": "Sessão gratuita de curtas-metragens seguida de conversa.",
        "description": "Exibição de curtas-metragens nacionais com classificação livre e bate-papo "
        "com a equipe de mediação ao final. Entrada gratuita, por ordem de chegada.",
        "status": PUBLISHED,
        "schedules": [one_time(6, "19:00", "21:00"), one_time(27, "19:00", "21:00")],
    },
    {
        "title": "Torneio de futsal comunitário",
        "unit": "ceu-cidade-dutra",
        "category": "esporte-e-atividade-fisica",
        "audiences": ["adolescentes", "adultos"],
        "summary": "Torneio entre equipes da região no ginásio do CEU.",
        "description": "Competição de futsal em grupos e mata-mata. "
        "Inscrição de equipes com até 10 jogadores.",
        "status": FINISHED,
        "schedules": [one_time(-12, "09:00", "17:00"), one_time(-11, "09:00", "17:00")],
    },
    # CEU Vila Rubi
    {
        "title": "Yoga e alongamento",
        "unit": "ceu-vila-rubi",
        "category": "saude-e-bem-estar",
        "audiences": ["adultos", "pessoas-idosas"],
        "summary": "Posturas, respiração e alongamento para o bem-estar.",
        "description": "Aula acessível a iniciantes, com foco em flexibilidade, respiração e "
        "relaxamento. Leve um tapete ou toalha.",
        "status": PUBLISHED,
        "schedules": [recurring(-30, 75, [TER, QUI], "07:30", "08:30")],
    },
    {
        "title": "Horta comunitária e compostagem",
        "unit": "ceu-vila-rubi",
        "category": "educacao-e-meio-ambiente",
        "audiences": ["todas-as-idades"],
        "summary": "Cultivo de hortaliças e reaproveitamento de resíduos orgânicos.",
        "description": "Mutirão quinzenal na horta do CEU: preparo dos canteiros, plantio, "
        "compostagem e troca de mudas. As crianças participam com acompanhamento.",
        "status": PUBLISHED,
        "schedules": [one_time(9, "09:00", "11:30"), one_time(23, "09:00", "11:30")],
    },
    {
        "title": "Oficina de violão",
        "unit": "ceu-vila-rubi",
        "category": "cursos-e-formacao",
        "audiences": ["adolescentes", "adultos"],
        "summary": "Aprenda acordes e ritmos da música popular brasileira.",
        "description": "Turma para iniciantes, com violões emprestados durante as aulas. "
        "Conteúdo: afinação, acordes básicos, batidas e as primeiras músicas.",
        "status": PUBLISHED,
        "schedules": [recurring(-5, 84, [SEG], "19:00", "20:30")],
    },
    {
        "title": "Reunião aberta do conselho gestor",
        "unit": "ceu-vila-rubi",
        "category": "participacao-comunitaria",
        "audiences": ["adultos"],
        "summary": "Prestação de contas e escuta da comunidade sobre a programação.",
        "description": "Reunião aberta para apresentar a programação do trimestre e ouvir "
        "sugestões de moradores e frequentadores do CEU.",
        "status": CANCELLED,
        "schedules": [one_time(12, "19:00", "21:00")],
    },
    # CEU Vila do Sol
    {
        "title": "Zumba",
        "unit": "ceu-vila-do-sol",
        "category": "esporte-e-atividade-fisica",
        "audiences": ["adultos"],
        "summary": "Aula de dança aeróbica com ritmos latinos.",
        "description": "Coreografias animadas que combinam dança e exercício aeróbico, para todos "
        "os níveis. Use tênis e roupa leve.",
        "status": PUBLISHED,
        "schedules": [recurring(-20, 70, [TER, QUI], "19:30", "20:30")],
    },
    {
        "title": "Jogos de tabuleiro e xadrez",
        "unit": "ceu-vila-do-sol",
        "category": "lazer-e-recreacao",
        "audiences": ["criancas", "adolescentes", "pessoas-idosas"],
        "summary": "Tarde de jogos de estratégia para diferentes idades.",
        "description": "Espaço livre com xadrez, damas e jogos de tabuleiro cooperativos, com "
        "monitores para ensinar as regras a quem está começando.",
        "status": PUBLISHED,
        "schedules": [recurring(-3, 63, [SEX], "14:00", "17:00")],
    },
    {
        "title": "Festival de talentos da comunidade",
        "unit": "ceu-vila-do-sol",
        "category": "eventos-e-encontros",
        "audiences": ["todas-as-idades"],
        "summary": "Apresentações de música, dança e poesia de moradores da região.",
        "description": "Palco aberto para apresentações de até 5 minutos. Inscrições na recepção "
        "do CEU até uma semana antes do evento.",
        "external": "https://exemplo.org/inscricao/festival-de-talentos",
        "status": PUBLISHED,
        "schedules": [one_time(34, "14:00", "18:00")],
    },
    {
        "title": "Oficina de percussão",
        "unit": "ceu-vila-do-sol",
        "category": "cultura-e-artes",
        "audiences": ["adolescentes", "adultos"],
        "summary": "Ritmos brasileiros em grupo, com instrumentos de percussão.",
        "description": "Oficina em formato de bateria coletiva: surdo, caixa, tamborim e "
        "ganzá, com repertório de samba e maracatu.",
        "status": DRAFT,
        "schedules": [recurring(21, 100, [SAB], "10:00", "12:00")],
    },
]


# Imagens fictícias: ilustrações geométricas geradas aqui mesmo, sem pessoas, marcas nem arquivos de
# terceiros. Atividades fora deste mapa ficam sem imagem (para mostrar o visual alternativo).
DEMO_ALT = "Ilustração geométrica fictícia de demonstração"
IMAGE_PLAN = {
    "Capoeira para todas as idades": {"alt": f"{DEMO_ALT}, em tons de laranja e azul."},
    "Hora do conto na biblioteca": {"alt": f"{DEMO_ALT}, em tons de verde e amarelo."},
    "Hidroginástica": {"alt": f"{DEMO_ALT}, em tons de azul."},
    "Oficina de teatro para adolescentes": {"decorative": True},
    "Cine CEU: sessão de curtas brasileiros": {"alt": f"{DEMO_ALT}, em tons de roxo."},
    "Yoga e alongamento": {"alt": f"{DEMO_ALT}, em tons de rosa e lilás."},
    "Horta comunitária e compostagem": {"decorative": True},
    "Oficina de violão": {"alt": f"{DEMO_ALT}, em tons de marrom e dourado."},
    "Zumba": {"alt": f"{DEMO_ALT}, em tons de vermelho e magenta."},
    "Festival de talentos da comunidade": {"alt": f"{DEMO_ALT}, em tons de turquesa."},
}
DEMO_IMAGE_SIZE = (1200, 800)


def build_demo_image(seed):
    """Ilustração JPEG determinística: o mesmo `seed` sempre gera os mesmos bytes."""
    digest = hashlib.sha256(seed.encode("utf-8")).digest()
    width, height = DEMO_IMAGE_SIZE
    top = tuple(60 + digest[i] % 150 for i in range(3))
    bottom = tuple(60 + digest[3 + i] % 150 for i in range(3))
    image = Image.new("RGB", DEMO_IMAGE_SIZE)
    draw = ImageDraw.Draw(image)
    for y in range(height):
        ratio = y / (height - 1)
        color = tuple(round(top[i] + (bottom[i] - top[i]) * ratio) for i in range(3))
        draw.line([(0, y), (width, y)], fill=color)
    for index in range(3):
        x = digest[6 + index * 3] * width // 255
        y = digest[7 + index * 3] * height // 255
        radius = 90 + digest[8 + index * 3] % 140
        light = tuple(min(255, value + 70) for value in bottom)
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=light)
    draw.rectangle([width // 6, height * 3 // 4, width * 5 // 6, height * 7 // 8], fill=top)
    buffer = io.BytesIO()
    image.save(buffer, "JPEG", quality=85)
    return buffer.getvalue()


def _attach_image(activity, plan):
    """Anexa a imagem fictícia. Devolve False se a atividade já tinha imagem."""
    if activity.image:
        return False
    upload = SimpleUploadedFile("demo.jpg", build_demo_image(activity.title))
    processed, extension = process_image(upload)
    activity.image.save(f"demo.{extension}", processed, save=False)
    activity.image_alt = plan.get("alt", "")
    activity.image_decorative = plan.get("decorative", False)
    activity.save(update_fields=["image", "image_alt", "image_decorative", "updated_at"])
    return True


def _attach_demo_images(units):
    """Anexa imagens às atividades de demonstração sem imagem. Devolve (anexadas, já tinham)."""
    attached = existing = 0
    for item in ACTIVITIES:
        plan = IMAGE_PLAN.get(item["title"])
        if plan is None:
            continue
        activity = Activity.objects.filter(title=item["title"], unit=units[item["unit"]]).first()
        if activity is None:
            continue
        if _attach_image(activity, plan):
            attached += 1
        else:
            existing += 1
    return attached, existing


def _time(text):
    return datetime.strptime(text, "%H:%M").time()


def _admin_user():
    user = (
        get_user_model()
        .objects.filter(is_staff=True, is_active=True)
        .order_by("date_joined")
        .first()
    )
    if user is None:
        raise CommandError("Nenhum administrador ativo encontrado. Rode `create_admin <usuario>`.")
    return user


def _by_slug(model, slugs, label):
    found = {item.slug: item for item in model.objects.filter(slug__in=slugs)}
    missing = sorted(set(slugs) - set(found))
    if missing:
        raise CommandError(f"{label} ausente(s): {', '.join(missing)}. Rode `seed_catalog` antes.")
    return found


def _create_schedules(activity, plan, today, user):
    for item in plan:
        schedule = Schedule.objects.create(
            activity=activity,
            schedule_type=item["type"],
            start_date=today + timedelta(days=item["from_days"]),
            end_date=today + timedelta(days=item["to_days"]),
            start_time=_time(item["start"]),
            end_time=_time(item["end"]),
            created_by=user,
            updated_by=user,
        )
        ScheduleWeekday.objects.bulk_create(
            ScheduleWeekday(schedule=schedule, weekday=day) for day in item.get("weekdays", [])
        )


def _create_activity(item, units, categories, audiences, today, user):
    activity = Activity(
        unit=units[item["unit"]],
        category=categories[item["category"]],
        title=item["title"],
        summary=item["summary"],
        description=item["description"],
        external_registration_url=item.get("external", ""),
        status=item["status"],
        created_by=user,
        updated_by=user,
    )
    activity.clean()
    activity.save()
    for slug in item["audiences"]:
        ActivityTargetAudience.objects.create(activity=activity, target_audience=audiences[slug])
    _create_schedules(activity, item["schedules"], today, user)


class Command(BaseCommand):
    help = (
        "Carrega unidades, atividades, programações e imagens FICTÍCIAS para demonstração "
        "(seguro para repetir; não cria usuários)."
    )

    def handle(self, *args, **options):
        user = _admin_user()
        created, existing = _load(Unit.objects, UNITS)
        self.stdout.write(f"Unidades: {created} criada(s), {existing} já existiam.")

        units = _by_slug(Unit, {a["unit"] for a in ACTIVITIES}, "Unidade")
        categories = _by_slug(Category, {a["category"] for a in ACTIVITIES}, "Categoria")
        audience_slugs = {slug for a in ACTIVITIES for slug in a["audiences"]}
        audiences = _by_slug(TargetAudience, audience_slugs, "Público-alvo")

        today = date.today()
        made = skipped = 0
        for item in ACTIVITIES:
            if Activity.objects.filter(title=item["title"], unit=units[item["unit"]]).exists():
                skipped += 1
                continue
            with transaction.atomic():
                _create_activity(item, units, categories, audiences, today, user)
            made += 1
        self.stdout.write(f"Atividades: {made} criada(s), {skipped} já existiam.")
        try:
            attached, had_image = _attach_demo_images(units)
        except Exception as error:
            raise CommandError(
                f"Não foi possível guardar as imagens de demonstração ({type(error).__name__}). "
                "Confira as variáveis AWS_* e rode `seed_demo` de novo."
            ) from None
        self.stdout.write(f"Imagens: {attached} anexada(s), {had_image} já existiam.")
