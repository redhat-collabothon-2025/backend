from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from drf_spectacular.utils import extend_schema
from whitehat_app.models import User, Incident, RiskHistory


@extend_schema(
    responses={200: {
        'type': 'object',
        'properties': {
            'total_employees': {'type': 'integer'},
            'average_risk_score': {'type': 'number'},
            'critical_count': {'type': 'integer'},
            'medium_count': {'type': 'integer'},
            'low_count': {'type': 'integer'},
            'recent_incidents': {'type': 'integer'}
        }
    }}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def overview(request):
    # Filter by active users only
    active_users = User.objects.filter(is_active=True)
    total_employees = active_users.count()
    average_risk_score = active_users.aggregate(avg=Avg('risk_score'))['avg'] or 0
    
    critical_count = active_users.filter(risk_level='CRITICAL').count()
    medium_count = active_users.filter(risk_level='MEDIUM').count()
    low_count = active_users.filter(risk_level='LOW').count()

    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_incidents = Incident.objects.filter(created_at__gte=thirty_days_ago).count()
    
    return Response({
        'total_employees': total_employees,
        'average_risk_score': round(average_risk_score, 2),
        'critical_count': critical_count,
        'medium_count': medium_count,
        'low_count': low_count,
        'recent_incidents': recent_incidents
    })


@extend_schema(
    responses={200: {
        'type': 'array',
        'items': {
            'type': 'object',
            'properties': {
                'risk_level': {'type': 'string'},
                'count': {'type': 'integer'},
                'percentage': {'type': 'number'}
            }
        }
    }}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def distribution(request):
    # Filter by active users only
    active_users = User.objects.filter(is_active=True)
    total_users = active_users.count()
    
    if total_users == 0:
        return Response([])
    
    # Get distribution for each risk level
    risk_distribution = active_users.values('risk_level').annotate(
        count=Count('id')
    )
    
    # Create a dictionary for easy lookup
    distribution_dict = {item['risk_level']: item['count'] for item in risk_distribution}
    
    # Return in consistent order: CRITICAL, MEDIUM, LOW
    # Ensure all three levels are always present (with 0 if no users)
    result = []
    for risk_level in ['CRITICAL', 'MEDIUM', 'LOW']:
        count = distribution_dict.get(risk_level, 0)
        result.append({
            'risk_level': risk_level,
            'count': count,
            'percentage': round((count / total_users) * 100, 2) if total_users > 0 else 0
        })
    
    return Response(result)


@extend_schema(
    responses={200: {
        'type': 'array',
        'items': {
            'type': 'object',
            'properties': {
                'date': {'type': 'string', 'format': 'date'},
                'average_risk_score': {'type': 'number'},
                'critical_count': {'type': 'integer'},
                'medium_count': {'type': 'integer'},
                'low_count': {'type': 'integer'}
            }
        }
    }}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def trending(request):
    from django.db.models import Case, When, IntegerField, Sum

    thirty_days_ago = timezone.now() - timedelta(days=30)

    risk_history = RiskHistory.objects.filter(
        created_at__gte=thirty_days_ago
    ).values('created_at__date').annotate(
        avg_risk=Avg('risk_score'),
        critical_count=Sum(
            Case(
                When(risk_score__gte=50, then=1),
                default=0,
                output_field=IntegerField()
            )
        ),
        medium_count=Sum(
            Case(
                When(risk_score__gte=20, risk_score__lt=50, then=1),
                default=0,
                output_field=IntegerField()
            )
        ),
        low_count=Sum(
            Case(
                When(risk_score__lt=20, then=1),
                default=0,
                output_field=IntegerField()
            )
        )
    ).order_by('created_at__date')

    result = []
    for item in risk_history:
        result.append({
            'date': item['created_at__date'].isoformat(),
            'average_risk_score': round(item['avg_risk'], 2),
            'critical_count': item['critical_count'],
            'medium_count': item['medium_count'],
            'low_count': item['low_count']
        })

    return Response(result)


@extend_schema(
    responses={200: {
        'type': 'array',
        'items': {
            'type': 'object',
            'properties': {
                'risk_level': {'type': 'string'},
                'week': {'type': 'string'},
                'risk_score': {'type': 'number'},
                'incident_count': {'type': 'integer'}
            }
        }
    }}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def heatmap(request):
    from django.db.models import Case, When, IntegerField, Sum

    result = []

    thirty_days_ago = timezone.now() - timedelta(days=30)

    risk_levels = ['LOW', 'MEDIUM', 'CRITICAL']

    for week_num in range(4):
        week_start = thirty_days_ago + timedelta(weeks=week_num)
        week_end = week_start + timedelta(days=7)
        week_label = f"Week {week_num + 1}"

        for risk_level in risk_levels:
            # Get users with this risk level
            users_with_risk = User.objects.filter(risk_level=risk_level)

            # Count incidents for users with this risk level in this week
            incidents_count = Incident.objects.filter(
                user__risk_level=risk_level,
                created_at__gte=week_start,
                created_at__lt=week_end
            ).count()

            # Average risk score for users with this risk level
            avg_risk = users_with_risk.aggregate(avg=Avg('risk_score'))['avg'] or 0

            result.append({
                'risk_level': risk_level,
                'week': week_label,
                'risk_score': round(avg_risk, 2),
                'incident_count': incidents_count
            })

    return Response(result)