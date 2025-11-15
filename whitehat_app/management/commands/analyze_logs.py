from django.core.management.base import BaseCommand
from whitehat_app.models import Log, Incident, User
from whitehat_app.ai_service import ai_service


class Command(BaseCommand):
    help = 'Analyze logs for security risks and create incidents for medium/high risk activities'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit the number of logs to analyze (default: all unprocessed logs)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Re-analyze all logs, even those already processed'
        )

    def handle(self, *args, **options):
        limit = options.get('limit')
        force = options.get('force', False)

        self.stdout.write('Starting log analysis...')

        # Get logs to analyze
        logs_query = Log.objects.all().order_by('-timestamp')

        if limit:
            logs_query = logs_query[:limit]

        analyzed_count = 0
        incidents_created = 0
        medium_risk_count = 0
        critical_risk_count = 0

        for log in logs_query:
            try:
                # Prepare log data for analysis
                log_data = {
                    'action_type': log.action_type,
                    'resource_type': log.resource_type,
                    'resource_accessed': log.resource_accessed,
                    'request_status': log.request_status,
                    'employee_id': log.employee_id,
                    'ip_address': log.ip_address,
                }

                # Analyze the log
                analysis = ai_service.analyze_log_risk(log_data)

                analyzed_count += 1

                # Track risk levels
                if analysis['risk_level'] == 'MEDIUM':
                    medium_risk_count += 1
                elif analysis['risk_level'] == 'CRITICAL':
                    critical_risk_count += 1

                # Create incident if needed
                if analysis['create_incident'] and analysis['risk_level'] in ['MEDIUM', 'CRITICAL']:
                    # Try to find user by email (employee_id might be email)
                    user = None
                    try:
                        user = User.objects.filter(email__icontains=log.employee_id).first()
                        if not user:
                            # Try to find by name
                            user = User.objects.filter(name__icontains=log.employee_id).first()
                    except Exception:
                        pass

                    if not user:
                        # Get or create a default user for unmatched employee IDs
                        user, _ = User.objects.get_or_create(
                            email=f'{log.employee_id}@company.com',
                            defaults={
                                'name': log.employee_id,
                                'risk_level': analysis['risk_level']
                            }
                        )

                    # Check if incident already exists for this log
                    incident_type = f"Log Analysis: {log.action_type}"
                    existing_incident = Incident.objects.filter(
                        user=user,
                        incident_type=incident_type,
                        created_at__date=log.timestamp.date()
                    ).first()

                    if not existing_incident or force:
                        if existing_incident and force:
                            existing_incident.delete()

                        Incident.objects.create(
                            user=user,
                            incident_type=incident_type,
                            severity=analysis['risk_level'],
                        )
                        incidents_created += 1

                        self.stdout.write(
                            self.style.WARNING(
                                f"Created {analysis['risk_level']} incident for {log.employee_id}: {analysis['description']}"
                            )
                        )

                if analyzed_count % 50 == 0:
                    self.stdout.write(f'Analyzed {analyzed_count} logs so far...')

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error analyzing log {log.id}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nAnalysis complete!\n'
                f'Total logs analyzed: {analyzed_count}\n'
                f'Medium risk activities: {medium_risk_count}\n'
                f'Critical risk activities: {critical_risk_count}\n'
                f'Incidents created: {incidents_created}'
            )
        )
