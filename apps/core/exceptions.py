import logging

from django.http import Http404
from rest_framework.exceptions import MethodNotAllowed, NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)

UNEXPECTED_ERROR_MESSAGE = "Ocorreu um erro inesperado. Tente novamente mais tarde."


def _messages(value):
    if isinstance(value, (list, tuple)):
        return [str(item) for item in value]
    return [str(value)]


def _field_errors(detail):
    if isinstance(detail, dict):
        return {field: _messages(value) for field, value in detail.items()}
    return {"non_field_errors": _messages(detail)}


def public_exception_handler(exc, context):
    """Erros JSON em formato único: `detail` e, na validação, `errors` por campo."""
    response = exception_handler(exc, context)
    if response is None:
        request = context.get("request")
        logger.error(
            "Erro inesperado em %s %s",
            getattr(request, "method", "-"),
            getattr(request, "path", "-"),
            exc_info=(type(exc), exc, exc.__traceback__),
        )
        return Response({"detail": UNEXPECTED_ERROR_MESSAGE}, status=500)
    if isinstance(exc, ValidationError):
        response.data = {"detail": "Parâmetros inválidos.", "errors": _field_errors(exc.detail)}
    elif isinstance(exc, (NotFound, Http404)):
        response.data = {"detail": "Não encontrado."}
    elif isinstance(exc, MethodNotAllowed):
        response.data = {"detail": "Método não permitido."}
    else:
        response.data = {"detail": str(getattr(exc, "detail", exc))}
    return response
