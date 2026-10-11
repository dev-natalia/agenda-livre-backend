from django.http import Http404
from rest_framework.exceptions import MethodNotAllowed, NotFound, ValidationError
from rest_framework.views import exception_handler


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
        return None
    if isinstance(exc, ValidationError):
        response.data = {"detail": "Parâmetros inválidos.", "errors": _field_errors(exc.detail)}
    elif isinstance(exc, (NotFound, Http404)):
        response.data = {"detail": "Não encontrado."}
    elif isinstance(exc, MethodNotAllowed):
        response.data = {"detail": "Método não permitido."}
    else:
        response.data = {"detail": str(getattr(exc, "detail", exc))}
    return response
