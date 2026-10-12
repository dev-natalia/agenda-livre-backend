import importlib

from django.apps import AppConfig


class ActivitiesConfig(AppConfig):
    name = "apps.activities"

    def ready(self):
        importlib.import_module("apps.activities.signals")
