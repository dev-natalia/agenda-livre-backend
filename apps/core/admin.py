from django.contrib import admin

admin.site.site_header = "Agenda Livre — Administração"
admin.site.site_title = "Agenda Livre"
admin.site.index_title = "Gestão de conteúdo"


class ActiveOnlyForeignKeyMixin:
    """Não oferece registros inativos nas listas de relacionamento do Django Admin.

    Os `ModelAdmin` dos cadastros das próximas features devem herdar este mixin.
    """

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        related_model = db_field.remote_field.model
        if any(field.name == "is_active" for field in related_model._meta.get_fields()):
            queryset = kwargs.get("queryset")
            if queryset is None:
                queryset = related_model._default_manager.all()
            kwargs["queryset"] = queryset.filter(is_active=True)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
