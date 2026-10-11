from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = "Aplica as migrations mostrando antes qual banco será modificado."

    def add_arguments(self, parser):
        parser.add_argument(
            "--noinput",
            "--no-input",
            action="store_false",
            dest="interactive",
            help="Não pede confirmação antes de aplicar as migrations.",
        )

    def handle(self, *args, **options):
        db = connection.settings_dict
        self.stdout.write(
            f"Banco de destino: {db['HOST']}:{db['PORT']}/{db['NAME']} (usuário {db['USER']})"
        )
        if options["interactive"]:
            answer = input("Aplicar as migrations neste banco? [s/N] ")
            if answer.strip().lower() != "s":
                raise CommandError("Operação cancelada. Nenhuma alteração foi feita no banco.")
        call_command("migrate", interactive=False, verbosity=options["verbosity"])
