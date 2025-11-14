from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from whitehat_app.models import Event, User
from whitehat_app.serializers import EventSerializer


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post']

    def get_queryset(self):
        queryset = Event.objects.all()
        user_id = self.request.query_params.get('user_id')
        event_type = self.request.query_params.get('event_type')
        
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        return queryset.order_by('-created_at')

    @extend_schema(
        responses={200: EventSerializer(many=True)}
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
        request={
            'type': 'object',
            'properties': {
                'user_id': {'type': 'string', 'format': 'uuid'},
                'event_type': {
                    'type': 'string',
                    'enum': ['phishing_click', 'bulk_export', 'usb_connect']
                },
                'event_data': {'type': 'object'}
            },
            'required': ['user_id', 'event_type', 'event_data']
        },
        responses={201: EventSerializer}
    )
    def create(self, request):
        user_id = request.data.get('user_id')
        event_type = request.data.get('event_type')
        event_data = request.data.get('event_data', {})
        
        user = get_object_or_404(User, pk=user_id)
        
        event = Event.objects.create(
            user=user,
            event_type=event_type,
            event_data=event_data
        )
        
        serializer = self.get_serializer(event)
        return Response(serializer.data, status=status.HTTP_201_CREATED)