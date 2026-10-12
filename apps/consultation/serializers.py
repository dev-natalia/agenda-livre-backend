from urllib.parse import urlparse

from rest_framework import serializers

from apps.consultation.services import Criteria
from apps.schedules.models import ScheduleWeekday
from apps.schedules.services import activity_occurrences

MAX_RANGE_DAYS = 366
NEXT_OCCURRENCES_IN_DETAIL = 5
DATE_FORMAT_MESSAGE = "Informe uma data no formato AAAA-MM-DD."
DATE_ERRORS = {"invalid": DATE_FORMAT_MESSAGE, "date": DATE_FORMAT_MESSAGE}
ID_ERRORS = {"invalid": "Informe um identificador válido."}


class ConsultationQuerySerializer(serializers.Serializer):
    """Valida os parâmetros de consulta da listagem; parâmetros desconhecidos são ignorados."""

    q = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100,
        error_messages={"max_length": "Informe no máximo 100 caracteres."},
    )
    unit = serializers.UUIDField(required=False, error_messages=ID_ERRORS)
    category = serializers.UUIDField(required=False, error_messages=ID_ERRORS)
    audience = serializers.UUIDField(required=False, error_messages=ID_ERRORS)
    neighborhood = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=100,
        error_messages={"max_length": "Informe no máximo 100 caracteres."},
    )
    date = serializers.DateField(required=False, error_messages=DATE_ERRORS)
    date_from = serializers.DateField(required=False, error_messages=DATE_ERRORS)
    date_to = serializers.DateField(required=False, error_messages=DATE_ERRORS)

    def validate(self, attrs):
        if "date" in attrs and ("date_from" in attrs or "date_to" in attrs):
            raise serializers.ValidationError(
                {"date": ["Use date ou date_from/date_to, não os dois."]}
            )
        start, end = attrs.get("date_from"), attrs.get("date_to")
        if start and end:
            if start > end:
                raise serializers.ValidationError(
                    {"date_from": ["A data inicial não pode ser posterior à data final."]}
                )
            if (end - start).days > MAX_RANGE_DAYS:
                raise serializers.ValidationError(
                    {"date_to": [f"O intervalo máximo é de {MAX_RANGE_DAYS} dias."]}
                )
        return attrs

    def criteria(self):
        data = self.validated_data
        day = data.get("date")
        return Criteria(
            q=data.get("q") or None,
            unit=data.get("unit"),
            category=data.get("category"),
            audience=data.get("audience"),
            neighborhood=data.get("neighborhood") or None,
            date_from=day or data.get("date_from"),
            date_to=day or data.get("date_to"),
        )


class OccurrenceSerializer(serializers.Serializer):
    date = serializers.DateField()
    start_time = serializers.TimeField(format="%H:%M")
    end_time = serializers.TimeField(format="%H:%M")


class UnitSummarySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    slug = serializers.CharField()
    neighborhood = serializers.CharField()


class UnitDetailSerializer(UnitSummarySerializer):
    address = serializers.CharField()


class CategorySummarySerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    slug = serializers.CharField()


class AudienceSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()


def audiences_payload(activity):
    """Públicos-alvo da atividade (id e nome), por nome; lista vazia se não houver nenhum."""
    audiences = sorted(activity.target_audiences.all(), key=lambda audience: audience.name)
    return [{"id": audience.id, "name": audience.name} for audience in audiences]


def image_payload(activity):
    """Dados públicos da imagem da atividade, ou `None` quando ela não tem imagem."""
    if not activity.image:
        return None
    return {
        "url": activity.image.url,
        "alt": activity.image_alt,
        "decorative": activity.image_decorative,
    }


class ActivityListItemSerializer(serializers.Serializer):
    """Recebe o par (atividade, próxima ocorrência) montado por `build_listing`."""

    def to_representation(self, pair):
        activity, occurrence = pair
        return {
            "id": activity.id,
            "title": activity.title,
            "slug": activity.slug,
            "summary": activity.summary,
            "unit": UnitSummarySerializer(activity.unit).data,
            "category": CategorySummarySerializer(activity.category).data,
            "target_audiences": audiences_payload(activity),
            "next_occurrence": OccurrenceSerializer(occurrence).data if occurrence else None,
            "image": image_payload(activity),
        }


class ScheduleSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    schedule_type = serializers.CharField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    start_time = serializers.TimeField(format="%H:%M")
    end_time = serializers.TimeField(format="%H:%M")
    weekdays = serializers.SerializerMethodField()
    weekday_names = serializers.SerializerMethodField()

    def get_weekdays(self, schedule):
        return sorted(item.weekday for item in schedule.weekdays.all())

    def get_weekday_names(self, schedule):
        return [ScheduleWeekday.Weekday(day).label for day in self.get_weekdays(schedule)]


class ActivityDetailSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    slug = serializers.CharField()
    summary = serializers.CharField()
    description = serializers.CharField()
    target_audience_notes = serializers.CharField()
    unit = UnitDetailSerializer()
    category = CategorySummarySerializer()
    target_audiences = serializers.SerializerMethodField()
    external_registration_url = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField()
    schedules = serializers.SerializerMethodField()
    next_occurrences = serializers.SerializerMethodField()

    def get_target_audiences(self, activity):
        return audiences_payload(activity)

    def get_image(self, activity):
        return image_payload(activity)

    def get_external_registration_url(self, activity):
        url = (activity.external_registration_url or "").strip()
        parts = urlparse(url)
        return url if parts.scheme in ("http", "https") and parts.netloc else None

    def get_schedules(self, activity):
        ordered = sorted(activity.schedules.all(), key=lambda item: item.start_date)
        return ScheduleSerializer(ordered, many=True).data

    def get_next_occurrences(self, activity):
        found = activity_occurrences(activity, limit=NEXT_OCCURRENCES_IN_DETAIL)
        return OccurrenceSerializer(found, many=True).data


class UnitItemSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    slug = serializers.CharField()
    neighborhood = serializers.CharField()
    address = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    def get_address(self, unit):
        return unit.address or None

    def get_description(self, unit):
        return unit.description or None


class AudienceItemSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    slug = serializers.CharField()
    description = serializers.SerializerMethodField()

    def get_description(self, audience):
        return audience.description or None


class CategoryItemSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    name = serializers.CharField()
    slug = serializers.CharField()
    description = serializers.SerializerMethodField()

    def get_description(self, category):
        return category.description or None
