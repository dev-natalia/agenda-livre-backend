"""Configuração ASGI do backend."""

import os

from django.core.asgi import get_asgi_application

from config.env import load_dotenv

load_dotenv()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

application = get_asgi_application()
