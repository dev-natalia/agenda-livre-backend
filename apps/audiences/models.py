from django.db import models

from apps.core.models import CatalogModel


class TargetAudience(CatalogModel):
    includes_everyone = models.BooleanField(
        "Abrange todos os públicos",
        default=False,
        help_text=(
            "Marque se esta opção vale para todos os públicos (por exemplo, ‘Todas as idades’). "
            "Quem filtra por qualquer outro público também vê as atividades desta opção."
        ),
    )

    class Meta(CatalogModel.Meta):
        verbose_name = "Público-alvo"
        verbose_name_plural = "Públicos-alvo"
