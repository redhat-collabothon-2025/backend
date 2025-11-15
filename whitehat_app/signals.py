from django.db.models.signals import post_save
from django.dispatch import receiver
from whitehat_app.models import Log, Incident, User
from whitehat_app.ai_service import ai_service
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Log)
def analyze_log_on_create(sender, instance, created, **kwargs):
    """Automatically analyze logs when they are created"""
    if not created:
        return  # Only analyze new logs

    try:
        # Prepare log data for analysis
        log_data = {
            'action_type': instance.action_type,
            'resource_type': instance.resource_type,
            'resource_accessed': instance.resource_accessed,
            'request_status': instance.request_status,
            'employee_id': instance.employee_id,
            'ip_address': instance.ip_address,
        }

        # Analyze the log
        analysis = ai_service.analyze_log_risk(log_data)

        # Create incident if needed
        if analysis['create_incident'] and analysis['risk_level'] in ['MEDIUM', 'CRITICAL']:
            # Try to find user by email or name
            user = None
            try:
                user = User.objects.filter(email__icontains=instance.employee_id).first()
                if not user:
                    user = User.objects.filter(name__icontains=instance.employee_id).first()
            except Exception:
                pass

            if not user:
                # Create a user for unmatched employee IDs
                user, _ = User.objects.get_or_create(
                    email=f'{instance.employee_id}@company.com',
                    defaults={
                        'name': instance.employee_id,
                        'risk_level': analysis['risk_level']
                    }
                )

            # Check if incident already exists for this log
            incident_type = f"Log Analysis: {instance.action_type}"
            existing_incident = Incident.objects.filter(
                user=user,
                incident_type=incident_type,
                created_at__date=instance.timestamp.date()
            ).first()

            if not existing_incident:
                incident = Incident.objects.create(
                    user=user,
                    incident_type=incident_type,
                    severity=analysis['risk_level'],
                )
                logger.info(
                    f"Created {analysis['risk_level']} incident for {instance.employee_id}: "
                    f"{analysis['description']}"
                )

    except Exception as e:
        logger.error(f"Error analyzing log {instance.id}: {str(e)}")
