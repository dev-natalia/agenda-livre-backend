from django.apps import AppConfig
from django.db.models.signals import post_migrate


class CoreConfig(AppConfig):
    name = "apps.core"

    def ready(self):
        from apps.core.permissions import sync_admin_group_after_migrate

        post_migrate.connect(
            sync_admin_group_after_migrate, dispatch_uid="core.sync_admin_group"
        )
