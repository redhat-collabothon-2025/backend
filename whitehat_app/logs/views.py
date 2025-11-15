from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from whitehat_app.models import Log, Incident, User
from whitehat_app.serializers import LogSerializer
from whitehat_app.ai_service import ai_service


class LogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Log.objects.all()
    serializer_class = LogSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post']

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

    @action(detail=False, methods=['post'], url_path='analyze')
    def analyze_logs(self, request):
        """Analyze logs for security risks and create incidents"""
        limit = request.data.get('limit', 100)

        logs = Log.objects.all().order_by('-timestamp')[:limit]

        analyzed_count = 0
        incidents_created = 0
        results = {
            'analyzed': 0,
            'medium_risk': 0,
            'critical_risk': 0,
            'incidents_created': 0,
            'errors': []
        }

        for log in logs:
            try:
                log_data = {
                    'action_type': log.action_type,
                    'resource_type': log.resource_type,
                    'resource_accessed': log.resource_accessed,
                    'request_status': log.request_status,
                    'employee_id': log.employee_id,
                    'ip_address': log.ip_address,
                }

                analysis = ai_service.analyze_log_risk(log_data)
                results['analyzed'] += 1

                if analysis['risk_level'] == 'MEDIUM':
                    results['medium_risk'] += 1
                elif analysis['risk_level'] == 'CRITICAL':
                    results['critical_risk'] += 1

                if analysis['create_incident'] and analysis['risk_level'] in ['MEDIUM', 'CRITICAL']:
                    user = None
                    try:
                        user = User.objects.filter(email__icontains=log.employee_id).first()
                        if not user:
                            user = User.objects.filter(name__icontains=log.employee_id).first()
                    except Exception:
                        pass

                    if not user:
                        user, _ = User.objects.get_or_create(
                            email=f'{log.employee_id}@company.com',
                            defaults={
                                'name': log.employee_id,
                                'risk_level': analysis['risk_level']
                            }
                        )

                    incident_type = f"Log Analysis: {log.action_type}"
                    existing_incident = Incident.objects.filter(
                        user=user,
                        incident_type=incident_type,
                        created_at__date=log.timestamp.date()
                    ).first()

                    if not existing_incident:
                        Incident.objects.create(
                            user=user,
                            incident_type=incident_type,
                            severity=analysis['risk_level'],
                        )
                        results['incidents_created'] += 1

            except Exception as e:
                results['errors'].append(str(e))

        return Response({
            'message': 'Log analysis completed',
            'results': results
        }, status=status.HTTP_200_OK)
