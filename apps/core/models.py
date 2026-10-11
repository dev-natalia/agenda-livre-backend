import uuid

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


class CatalogModel(models.Model):
    """Base dos cadastros de apoio (unidades e categorias)."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("Nome", max_length=150)
    slug = models.SlugField(
        "Identificador",
        max_length=160,
        unique=True,
        blank=True,
        help_text="Deixe em branco para gerar a partir do nome.",
    )
    description = models.TextField("Descrição", blank=True)
    is_active = models.BooleanField("Ativo", default=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        abstract = True
        ordering = ["name"]

    def __str__(self):
        return self.name

    def clean(self):
        super().clean()
        self.name = self.name.strip()
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.slug:
            raise ValidationError(
                {"slug": "Não foi possível gerar o identificador a partir do nome; informe um."}
            )
