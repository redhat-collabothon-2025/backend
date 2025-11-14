from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Count, Max
from drf_spectacular.utils import extend_schema
from whitehat_app.models import User, RiskHistory, Incident, Event
from whitehat_app.serializers import UserSerializer, RiskHistorySerializer


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = User.objects.all()
        risk_level = self.request.query_params.get('risk_level')
        if risk_level:
            queryset = queryset.filter(risk_level=risk_level)
        return queryset.order_by('-created_at')

    @extend_schema(
        request=UserSerializer,
        responses={201: UserSerializer}
    )
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.create_user(
            email=serializer.validated_data['email'],
            password=serializer.validated_data.get('password', 'defaultPassword123'),
            name=serializer.validated_data['name'],
            risk_score=serializer.validated_data.get('risk_score', 0.0),
            risk_level=serializer.validated_data.get('risk_level', 'LOW')
        )
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        responses={200: {
            'type': 'object',
            'properties': {
                'id': {'type': 'string', 'format': 'uuid'},
                'email': {'type': 'string'},
                'name': {'type': 'string'},
                'risk_score': {'type': 'number'},
                'risk_level': {'type': 'string'},
                'created_at': {'type': 'string', 'format': 'date-time'},
                'incident_count': {'type': 'integer'},
                'last_incident': {'type': 'string', 'format': 'date-time', 'nullable': True}
            }
        }}
    )
    def retrieve(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)
        serializer = self.get_serializer(user)
        data = serializer.data
        
        incident_count = Incident.objects.filter(user=user).count()
        last_incident = Incident.objects.filter(user=user).order_by('-created_at').first()
        
        data['incident_count'] = incident_count
        data['last_incident'] = last_incident.created_at if last_incident else None
        
        return Response(data)

    @extend_schema(
        request=UserSerializer,
        responses={200: UserSerializer}
    )
    def partial_update(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(
        responses={204: None}
    )
    def destroy(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        responses={200: RiskHistorySerializer(many=True)}
    )
    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)
        risk_history = RiskHistory.objects.filter(user=user).order_by('-created_at')
        serializer = RiskHistorySerializer(risk_history, many=True)
        return Response(serializer.data)

    @extend_schema(
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}}
    )
    @action(detail=False, methods=['post'])
    def recalculate(self, request):
        users = User.objects.all()
        recalculated_count = 0
        
        for user in users:
            old_risk_score = user.risk_score
            
            phishing_clicks = Event.objects.filter(user=user, event_type='phishing_click').count()
            bulk_exports = Event.objects.filter(user=user, event_type='bulk_export').count()
            usb_connects = Event.objects.filter(user=user, event_type='usb_connect').count()
            critical_incidents = Incident.objects.filter(user=user, severity='CRITICAL').count()
            medium_incidents = Incident.objects.filter(user=user, severity='MEDIUM').count()
            
            new_risk_score = (
                phishing_clicks * 10 +
                bulk_exports * 15 +
                usb_connects * 8 +
                critical_incidents * 25 +
                medium_incidents * 12
            )
            
            if new_risk_score >= 50:
                risk_level = 'CRITICAL'
            elif new_risk_score >= 20:
                risk_level = 'MEDIUM'
            else:
                risk_level = 'LOW'
            
            if old_risk_score != new_risk_score:
                user.risk_score = new_risk_score
                user.risk_level = risk_level
                user.save()
                
                RiskHistory.objects.create(
                    user=user,
                    risk_score=new_risk_score,
                    reason=f'Recalculated: {phishing_clicks} phishing clicks, {bulk_exports} bulk exports, {usb_connects} USB connects, {critical_incidents} critical incidents, {medium_incidents} medium incidents'
                )
                recalculated_count += 1
        
        return Response({'message': f'Recalculated risk scores for {recalculated_count} users'})