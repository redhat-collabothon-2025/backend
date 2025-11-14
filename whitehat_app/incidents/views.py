from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from whitehat_app.models import Incident, User
from whitehat_app.serializers import IncidentSerializer, IncidentCreateSerializer, IncidentUpdateSerializer


class IncidentViewSet(viewsets.ModelViewSet):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Incident.objects.select_related('user').all()
        severity = self.request.query_params.get('severity')
        
        if severity:
            queryset = queryset.filter(severity=severity)
        
        return queryset.order_by('-created_at')

    @extend_schema(
        responses={200: IncidentSerializer(many=True)}
    )
    def list(self, request):
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(
        request=IncidentCreateSerializer,
        responses={201: IncidentSerializer}
    )
    def create(self, request):
        user_id = request.data.get('user_id')
        incident_type = request.data.get('incident_type')
        severity = request.data.get('severity')
        
        user = get_object_or_404(User, pk=user_id)
        
        incident = Incident.objects.create(
            user=user,
            incident_type=incident_type,
            severity=severity
        )
        
        serializer = self.get_serializer(incident)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        responses={200: IncidentSerializer}
    )
    def retrieve(self, request, pk=None):
        incident = get_object_or_404(Incident.objects.select_related('user'), pk=pk)
        serializer = self.get_serializer(incident)
        return Response(serializer.data)

    @extend_schema(
        request=IncidentUpdateSerializer,
        responses={200: IncidentSerializer}
    )
    def partial_update(self, request, pk=None):
        incident = get_object_or_404(Incident, pk=pk)
        
        if 'incident_type' in request.data:
            incident.incident_type = request.data['incident_type']
        if 'severity' in request.data:
            incident.severity = request.data['severity']
        
        incident.save()
        serializer = self.get_serializer(incident)
        return Response(serializer.data)

    @extend_schema(
        responses={204: None}
    )
    def destroy(self, request, pk=None):
        incident = get_object_or_404(Incident, pk=pk)
        incident.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}}
    )
    @action(detail=True, methods=['post'])
    def resolve(self, request, pk=None):
        incident = get_object_or_404(Incident, pk=pk)
        return Response({'message': f'Incident {incident.id} marked as resolved'})