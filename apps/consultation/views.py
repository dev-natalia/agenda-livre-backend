import uuid

from django.utils import timezone
from rest_framework.exceptions import NotFound
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.audiences.models import TargetAudience
from apps.categories.models import Category
from apps.consultation.pagination import PublicPagination
from apps.consultation.serializers import (
    ActivityDetailSerializer,
    ActivityListItemSerializer,
    AudienceItemSerializer,
    CategoryItemSerializer,
    ConsultationQuerySerializer,
    UnitItemSerializer,
)
from apps.consultation.services import apply_criteria, build_listing, published_activities
from apps.units.models import Unit


class PublicAPIView(APIView):
    """Base das consultas públicas: anônima e somente leitura."""

    authentication_classes = []
    permission_classes = [AllowAny]
    http_method_names = ["get", "head", "options"]
    pagination_class = PublicPagination

    def paginate(self, request, items, serializer_class):
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(items, request, view=self)
        return paginator.get_paginated_response(serializer_class(page, many=True).data)


class ActivityListView(PublicAPIView):
    def get(self, request):
        query = ConsultationQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        criteria = query.criteria()
        activities = apply_criteria(published_activities(criteria), criteria)
        items = build_listing(activities, timezone.now(), criteria.date_from, criteria.date_to)
        return self.paginate(request, items, ActivityListItemSerializer)


class ActivityDetailView(PublicAPIView):
    def get(self, request, pk):
        try:
            activity_id = uuid.UUID(pk)
        except ValueError:
            raise NotFound() from None
        activity = (
            published_activities().prefetch_related("target_audiences").filter(pk=activity_id)
        ).first()
        if activity is None:
            raise NotFound()
        return Response(ActivityDetailSerializer(activity).data)


class UnitListView(PublicAPIView):
    def get(self, request):
        units = list(Unit.objects.filter(is_active=True).order_by("name"))
        return self.paginate(request, units, UnitItemSerializer)


class CategoryListView(PublicAPIView):
    def get(self, request):
        categories = list(Category.objects.filter(is_active=True).order_by("name"))
        return self.paginate(request, categories, CategoryItemSerializer)


class AudienceListView(PublicAPIView):
    def get(self, request):
        audiences = list(TargetAudience.objects.filter(is_active=True).order_by("name"))
        return self.paginate(request, audiences, AudienceItemSerializer)
