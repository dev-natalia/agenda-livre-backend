from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.pagination import PageNumberPagination


class PublicPagination(PageNumberPagination):
    page_size = 12
    page_size_query_param = "page_size"
    max_page_size = 50

    def paginate_queryset(self, queryset, request, view=None):
        try:
            return super().paginate_queryset(queryset, request, view=view)
        except NotFound:
            raise ValidationError({"page": ["Informe uma página válida."]}) from None
