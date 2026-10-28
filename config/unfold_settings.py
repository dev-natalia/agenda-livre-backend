"""Aparência do Django Admin (tema Unfold): título, cores e menu lateral."""

from django.urls import reverse_lazy


def _can_view(permission):
    def check(request):
        return request.user.has_perm(permission)

    return check


def _section(title, entries):
    items = [
        {
            "title": label,
            "icon": icon,
            "link": reverse_lazy(f"admin:{app}_{model}_changelist"),
            "permission": _can_view(f"{app}.view_{model}"),
        }
        for label, icon, app, model in entries
    ]
    return {"title": title, "separator": True, "items": items}


UNFOLD = {
    "SITE_TITLE": "Agenda Livre",
    "SITE_HEADER": "Agenda Livre",
    "SITE_SUBHEADER": "Administração",
    "SITE_SYMBOL": "event_available",
    "BORDER_RADIUS": "10px",
    "COLORS": {
        "primary": {
            "50": "238 242 255",
            "100": "224 231 255",
            "200": "199 210 254",
            "300": "165 180 252",
            "400": "129 140 248",
            "500": "99 102 241",
            "600": "79 70 229",
            "700": "67 56 202",
            "800": "55 48 163",
            "900": "49 46 129",
            "950": "30 27 75",
        },
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            _section(
                "Programação",
                [
                    ("Atividades", "event", "activities", "activity"),
                    ("Horários", "schedule", "schedules", "schedule"),
                ],
            ),
            _section(
                "Cadastros",
                [
                    ("Unidades", "location_on", "units", "unit"),
                    ("Categorias", "category", "categories", "category"),
                    ("Públicos-alvo", "groups", "audiences", "targetaudience"),
                ],
            ),
            _section(
                "Acesso",
                [
                    ("Usuários", "person", "auth", "user"),
                    ("Grupos", "shield_person", "auth", "group"),
                ],
            ),
        ],
    },
}
