from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.db.utils import Error

# (trechos da mensagem do driver, descrição exibida). A mensagem original nunca é exibida.
_FAILURE_TYPES = (
    (("password authentication failed", "authentication failed"), "credenciais recusadas"),
    (("timeout", "timed out"), "tempo esgotado ao conectar"),
    (("could not translate host name", "name or service not known", "getaddrinfo"),
     "host não encontrado"),
    (("connection refused", "no route to host", "network is unreachable"),
     "conexão recusada ou rede bloqueada (verifique o Security Group do RDS)"),
    (("does not exist",), "banco inexistente"),
    (("ssl",), "falha de TLS (verifique DB_SSLMODE e DB_SSLROOTCERT)"),
)


def classify_failure(error):
    """Descreve o tipo de falha sem repassar o texto original do driver."""
    text = str(error).lower()
    for fragments, description in _FAILURE_TYPES:
        if any(fragment in text for fragment in fragments):
            return description
    return f"falha de conexão ({type(error).__name__})"


class Command(BaseCommand):
    help = "Verifica se o banco de dados configurado está acessível."

    def handle(self, *args, **options):
        db = connection.settings_dict
        target = f"{db['HOST']}:{db['PORT']}/{db['NAME']}"
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Error as error:
            raise CommandError(
                f"Não foi possível conectar ao banco {target}: {classify_failure(error)}."
            ) from None
        self.stdout.write(self.style.SUCCESS(f"Conexão com o banco {target} funcionou."))
