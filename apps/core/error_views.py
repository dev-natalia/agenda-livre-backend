from django.http import JsonResponse
from django.views import defaults

from apps.core.exceptions import UNEXPECTED_ERROR_MESSAGE

API_PREFIX = "/api/"


def api_not_found(request, *args, **kwargs):
    """Rota coringa sob `/api/`: com `DEBUG` ligado o Django ignora `handler404`, esta não."""
    return JsonResponse({"detail": "Não encontrado."}, status=404)


def handler404(request, exception):
    """Rota inexistente: JSON sob `/api/`; fora dela, a página padrão do Django."""
    if request.path.startswith(API_PREFIX):
        return JsonResponse({"detail": "Não encontrado."}, status=404)
    return defaults.page_not_found(request, exception)


def handler500(request):
    """Falha fora das views da API: JSON genérico sob `/api/`; fora dela, a página padrão."""
    if request.path.startswith(API_PREFIX):
        return JsonResponse({"detail": UNEXPECTED_ERROR_MESSAGE}, status=500)
    return defaults.server_error(request)
