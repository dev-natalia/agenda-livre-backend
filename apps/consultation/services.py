import unicodedata
from dataclasses import dataclass
from datetime import date

from apps.activities.models import PUBLIC_STATUSES, Activity
from apps.audiences.models import TargetAudience
from apps.schedules.services import activity_occurrences


@dataclass(frozen=True)
class Criteria:
    """Critérios opcionais da listagem pública; `None` significa "sem filtro"."""

    q: str | None = None
    unit: object = None
    category: object = None
    audience: object = None
    neighborhood: str | None = None
    date_from: date | None = None
    date_to: date | None = None

    @property
    def has_date_filter(self):
        return self.date_from is not None or self.date_to is not None


def normalize_text(value):
    """Texto sem acentos, sem caixa e sem espaços nas pontas, para comparações."""
    decomposed = unicodedata.normalize("NFKD", value or "")
    plain = "".join(char for char in decomposed if not unicodedata.combining(char))
    return plain.casefold().strip()


def published_activities(criteria=None):
    """Atividades públicas, já com unidade, categoria, programações e dias carregados."""
    queryset = (
        Activity.objects.filter(status__in=PUBLIC_STATUSES)
        .select_related("unit", "category")
        .prefetch_related("schedules__weekdays", "target_audiences")
    )
    if criteria is not None and criteria.unit is not None:
        queryset = queryset.filter(unit_id=criteria.unit)
    if criteria is not None and criteria.category is not None:
        queryset = queryset.filter(category_id=criteria.category)
    return queryset


def matches_search(activity, term):
    """Verdadeiro se o termo aparece no título, no resumo ou na descrição."""
    needle = normalize_text(term)
    if not needle:
        return True
    return any(
        needle in normalize_text(text)
        for text in (activity.title, activity.summary, activity.description)
    )


def find_audience(audience_id):
    """Público-alvo ativo com o identificador dado, ou `None` (inexistente ou inativo)."""
    return TargetAudience.objects.filter(pk=audience_id, is_active=True).first()


def matches_audience(activity, audience):
    """Regra do filtro de público (ver `specs/011-audience-filter/data-model.md`).

    O público escolhido entra sempre; se ele não for o "abrange todos", também entram as atividades
    ligadas a qualquer público marcado como "abrange todos".
    """
    linked = list(activity.target_audiences.all())
    if any(found.pk == audience.pk for found in linked):
        return True
    if audience.includes_everyone:
        return False
    return any(found.includes_everyone for found in linked)


def apply_criteria(activities, criteria):
    """Aplica público, busca e bairro (comparações sem acento); unidade e categoria vêm do banco."""
    result = list(activities)
    if criteria.audience is not None:
        audience = find_audience(criteria.audience)
        if audience is None:
            return []
        result = [activity for activity in result if matches_audience(activity, audience)]
    if criteria.q:
        result = [activity for activity in result if matches_search(activity, criteria.q)]
    if criteria.neighborhood:
        wanted = normalize_text(criteria.neighborhood)
        result = [
            activity for activity in result if normalize_text(activity.unit.neighborhood) == wanted
        ]
    return result


def reference_occurrence(activity, now, date_from=None, date_to=None):
    """Próxima ocorrência da atividade, ou a primeira dentro da janela pedida."""
    found = activity_occurrences(
        activity, now=now, date_from=date_from, date_to=date_to, limit=1
    )
    return found[0] if found else None


def _sort_key(pair):
    activity, occurrence = pair
    title = normalize_text(activity.title)
    if occurrence is None:
        return (1, date.max, None, title)
    return (0, occurrence.date, occurrence.start_time, title)


def build_listing(activities, now, date_from=None, date_to=None):
    """Pares (atividade, ocorrência) ordenados; com filtro de data, só quem tem ocorrência."""
    pairs = [
        (activity, reference_occurrence(activity, now, date_from, date_to))
        for activity in activities
    ]
    if date_from is not None or date_to is not None:
        pairs = [pair for pair in pairs if pair[1] is not None]
    return sorted(pairs, key=_sort_key)
