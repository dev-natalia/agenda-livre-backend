from django.contrib import admin
from django.db.models import Q

admin.site.site_header = "Agenda Livre — Administração"
admin.site.site_title = "Agenda Livre"
admin.site.index_title = "Gestão de conteúdo"


class ActiveOnlyForeignKeyMixin:
    """Não oferece registros inativos nas listas de relacionamento do Django Admin.

    Ao editar um registro, o valor já gravado continua na lista mesmo se estiver inativo, para não
    quebrar o formulário. O `ModelAdmin` define `request._editing_obj` em `get_form` com o objeto em
    edição. As chaves estrangeiras de atividade para `Unit` e `Category` usam `on_delete=PROTECT`,
    então a exclusão de registros vinculados é recusada (o registro deve ser desativado).
    """

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        related_model = db_field.remote_field.model
        if any(field.name == "is_active" for field in related_model._meta.get_fields()):
            queryset = kwargs.get("queryset")
            if queryset is None:
                queryset = related_model._default_manager.all()
            editing = getattr(request, "_editing_obj", None)
            current_id = getattr(editing, f"{db_field.name}_id", None)
            if current_id is None:
                kwargs["queryset"] = queryset.filter(is_active=True)
            else:
                kwargs["queryset"] = queryset.filter(Q(is_active=True) | Q(pk=current_id))
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class ActiveToggleActionsMixin:
    """Ações em lote para desativar e reativar registros sem apagá-los."""

    actions = ["deactivate_selected", "reactivate_selected"]

    @admin.action(description="Desativar selecionados")
    def deactivate_selected(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} registro(s) desativado(s).")

    @admin.action(description="Reativar selecionados")
    def reactivate_selected(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"{count} registro(s) reativado(s).")
