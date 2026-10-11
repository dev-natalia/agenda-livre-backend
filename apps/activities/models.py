import uuid
from urllib.parse import urlparse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


class Activity(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Rascunho"
        PUBLISHED = "PUBLISHED", "Publicada"
        FINISHED = "FINISHED", "Encerrada"
        CANCELLED = "CANCELLED", "Cancelada"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    unit = models.ForeignKey(
        "units.Unit",
        verbose_name="Unidade",
        on_delete=models.PROTECT,
        related_name="activities",
    )
    category = models.ForeignKey(
        "categories.Category",
        verbose_name="Categoria",
        on_delete=models.PROTECT,
        related_name="activities",
    )
    title = models.CharField("Título", max_length=200)
    slug = models.SlugField(
        "Identificador", max_length=220, unique=True, blank=True, editable=False
    )
    summary = models.CharField("Resumo", max_length=300, blank=True)
    description = models.TextField("Descrição")
    target_audience_notes = models.TextField("Observações sobre o público", blank=True)
    external_registration_url = models.URLField("Link externo", blank=True)
    status = models.CharField(
        "Situação",
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        editable=False,
    )
    target_audiences = models.ManyToManyField(
        "audiences.TargetAudience",
        verbose_name="Públicos-alvo",
        through="ActivityTargetAudience",
        related_name="activities",
        blank=True,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Criada por",
        on_delete=models.PROTECT,
        related_name="+",
        editable=False,
    )
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Atualizada por",
        on_delete=models.PROTECT,
        related_name="+",
        editable=False,
    )
    created_at = models.DateTimeField("Criada em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizada em", auto_now=True)

    class Meta:
        verbose_name = "Atividade"
        verbose_name_plural = "Atividades"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["status"], name="activity_status_idx"),
            models.Index(fields=["unit", "status"], name="activity_unit_status_idx"),
            models.Index(fields=["category", "status"], name="activity_category_status_idx"),
        ]

    def __str__(self):
        return self.title

    def clean(self):
        super().clean()
        self.title = self.title.strip()
        self.description = self.description.strip()
        self.summary = self.summary.strip()
        self.external_registration_url = self.external_registration_url.strip()
        errors = {}
        if not self.title:
            errors["title"] = "Informe o título da atividade."
        if not self.description:
            errors["description"] = "Informe a descrição da atividade."
        url = self.external_registration_url
        if url and urlparse(url).scheme not in ("http", "https"):
            errors["external_registration_url"] = "Informe um endereço que comece com http:// ou https://."
        if errors:
            raise ValidationError(errors)
        if not self.slug:
            self.slug = self._build_slug()

    def _build_slug(self):
        base = slugify(self.title) or "atividade"
        candidate, number = base, 1
        while self._slug_taken(candidate):
            number += 1
            candidate = f"{base}-{number}"
        return candidate

    def _slug_taken(self, slug):
        return Activity.objects.filter(slug=slug).exclude(pk=self.pk).exists()


PUBLIC_STATUSES = {Activity.Status.PUBLISHED}


class ActivityTargetAudience(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    activity = models.ForeignKey(
        Activity,
        verbose_name="Atividade",
        on_delete=models.CASCADE,
        related_name="audience_links",
    )
    target_audience = models.ForeignKey(
        "audiences.TargetAudience",
        verbose_name="Público-alvo",
        on_delete=models.PROTECT,
        related_name="activity_links",
    )

    class Meta:
        verbose_name = "Público-alvo da atividade"
        verbose_name_plural = "Públicos-alvo da atividade"
        constraints = [
            models.UniqueConstraint(
                fields=["activity", "target_audience"],
                name="unique_activity_target_audience",
            )
        ]
