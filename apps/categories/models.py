from django.db import models
from django.db.models.functions import Lower

from apps.core.models import CatalogModel


class Category(CatalogModel):
    class Meta(CatalogModel.Meta):
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        constraints = [
            models.UniqueConstraint(
                Lower("name"),
                name="category_name_ci_unique",
                violation_error_message="Já existe uma categoria com este nome.",
            )
        ]
