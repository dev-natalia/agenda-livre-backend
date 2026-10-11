from django.apps import apps
from django.contrib.auth.models import Group, Permission

ADMIN_GROUP_NAME = "Administrador"


def sync_admin_group(using="default"):
    """Cria o grupo de administradores e concede a ele todas as permissões existentes."""
    group, _ = Group.objects.using(using).get_or_create(name=ADMIN_GROUP_NAME)
    group.permissions.set(Permission.objects.using(using).all())
    return group


def is_admin_account(user):
    """Conta ativa, com acesso ao painel e membro do grupo de administradores."""
    if not (user.is_authenticated and user.is_active and user.is_staff):
        return False
    return user.groups.filter(name=ADMIN_GROUP_NAME).exists()


def sync_admin_group_after_migrate(sender, using="default", **kwargs):
    """Sincroniza o grupo só após o último app, quando todas as permissões já existem."""
    if sender is list(apps.get_app_configs())[-1]:
        sync_admin_group(using=using)
