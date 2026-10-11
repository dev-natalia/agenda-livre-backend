from apps.core.models import CatalogModel


class TargetAudience(CatalogModel):
    class Meta(CatalogModel.Meta):
        verbose_name = "Público-alvo"
        verbose_name_plural = "Públicos-alvo"
