from django.db import models

from apps.core.models import CatalogModel


class Unit(CatalogModel):
    neighborhood = models.CharField("Bairro", max_length=100)
    address = models.TextField("Endereço", blank=True)

    class Meta(CatalogModel.Meta):
        verbose_name = "Unidade"
        verbose_name_plural = "Unidades"

    def clean(self):
        super().clean()
        self.neighborhood = self.neighborhood.strip()
