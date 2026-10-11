from django.http import JsonResponse
from django.views import defaults
from django.views.decorators.csrf import csrf_exempt

from apps.core.exceptions import UNEXPECTED_ERROR_MESSAGE

API_PREFIX = "/api/"


@csrf_exempt
def api_not_found(request, *args, **kwargs):
    """Rota coringa sob `/api/`: com `DEBUG` ligado o Django ignora `handler404`, esta não.

    Isenta de CSRF: não lê o corpo nem altera estado, e sem isso um POST a uma rota inexistente
    (por exemplo, um formulário de contato) receberia 403 em HTML em vez do 404 em JSON.
    """
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
