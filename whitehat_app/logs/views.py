from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from whitehat_app.models import Log
from whitehat_app.serializers import LogSerializer


class LogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Log.objects.all()
    serializer_class = LogSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']

    def get_queryset(self):
        queryset = Log.objects.all()

        # Filter by employee_id if provided
        employee_id = self.request.query_params.get('employee_id')
        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)

        # Filter by action_type if provided
        action_type = self.request.query_params.get('action_type')
        if action_type:
            queryset = queryset.filter(action_type__icontains=action_type)

        # Filter by request_status if provided
        request_status = self.request.query_params.get('request_status')
        if request_status:
            queryset = queryset.filter(request_status=request_status)

        return queryset.order_by('-timestamp')
