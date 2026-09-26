from django.db.models import Q
from rest_framework import generics

from core.permissions import IsExecutiveRead

from .models import AuditLog, PriorityChange
from .serializers import AuditLogSerializer, PriorityChangeSerializer


class AuditLogList(generics.ListAPIView):
    """Filterable audit history (role-restricted to management/operations)."""

    serializer_class = AuditLogSerializer
    permission_classes = [IsExecutiveRead]

    def get_queryset(self):
        qs = AuditLog.objects.select_related("actor")
        params = self.request.query_params
        if params.get("entity_type"):
            qs = qs.filter(entity_type=params["entity_type"])
        if params.get("entity_id"):
            qs = qs.filter(entity_id=params["entity_id"])
        if params.get("action"):
            qs = qs.filter(action=params["action"])
        if params.get("search"):
            term = params["search"]
            qs = qs.filter(Q(entity_label__icontains=term) | Q(note__icontains=term))
        return qs


class PriorityChangeList(generics.ListAPIView):
    serializer_class = PriorityChangeSerializer
    permission_classes = [IsExecutiveRead]

    def get_queryset(self):
        qs = PriorityChange.objects.select_related("project", "changed_by")
        params = self.request.query_params
        if params.get("project"):
            qs = qs.filter(project_id=params["project"])
        return qs
