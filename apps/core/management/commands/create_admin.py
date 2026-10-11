from getpass import getpass

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError

from apps.core.permissions import sync_admin_group


class Command(BaseCommand):
    help = "Cria uma conta de administrador (a senha é pedida sem eco)."

    def add_arguments(self, parser):
        parser.add_argument("username", help="Nome de usuário da nova conta.")

    def handle(self, *args, **options):
        User = get_user_model()
        username = options["username"]
        if User.objects.filter(username=username).exists():
            raise CommandError(f"O usuário '{username}' já existe.")

        password = getpass("Senha: ")
        if password != getpass("Senha (novamente): "):
            raise CommandError("As senhas informadas não são iguais.")
        try:
            validate_password(password, User(username=username))
        except ValidationError as error:
            raise CommandError("Senha rejeitada: " + " ".join(error.messages)) from None

        user = User.objects.create_user(username, password=password, is_staff=True)
        user.groups.add(sync_admin_group())
        self.stdout.write(self.style.SUCCESS(f"Conta de administrador '{username}' criada."))
