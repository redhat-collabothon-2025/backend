from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema
from whitehat_app.models import Log
from whitehat_app.serializers import LogSerializer


class LogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Log.objects.all()
    serializer_class = LogSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get']

    def get_queryset(self):
        queryset = Log.objects.all()
        employee_id = self.request.query_params.get('employee_id')
        action_type = self.request.query_params.get('action_type')
        request_status = self.request.query_params.get('request_status')

        if employee_id:
            queryset = queryset.filter(employee_id=employee_id)
        if action_type:
            queryset = queryset.filter(action_type=action_type)
        if request_status:
            queryset = queryset.filter(request_status=request_status)

        return queryset.order_by('-timestamp')

    @extend_schema(
        responses={200: LogSerializer(many=True)}
    )
    def list(self, request):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
