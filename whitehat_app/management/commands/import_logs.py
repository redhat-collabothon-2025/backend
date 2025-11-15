import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db.models.signals import post_save
from whitehat_app.models import Log


class Command(BaseCommand):
    help = 'Import employee logs from CSV file'

    def add_arguments(self, parser):
        parser.add_argument('csv_file', type=str, help='Path to the CSV file')

    def handle(self, *args, **options):
        csv_file_path = options['csv_file']

        self.stdout.write(f'Importing logs from {csv_file_path}...')

        imported_count = 0
        skipped_count = 0

        # Disable signals during bulk import for performance
        from whitehat_app import signals
        post_save.disconnect(signals.analyze_log_on_create, sender=Log)

        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)

                logs_to_create = []

                for row in reader:
                    try:
                        # Parse timestamp
                        timestamp = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')

                        # Create log object
                        log = Log(
                            timestamp=timestamp,
                            employee_id=row['employee_id'],
                            session_id=row['session_id'],
                            ip_address=row['ip_address'],
                            user_agent=row['user_agent'],
                            action_type=row['action_type'],
                            resource_accessed=row['resource_accessed'],
                            resource_type=row['resource_type'],
                            request_status=row['request_status']
                        )

                        logs_to_create.append(log)
                        imported_count += 1

                        # Bulk create every 1000 records for efficiency
                        if len(logs_to_create) >= 1000:
                            Log.objects.bulk_create(logs_to_create, ignore_conflicts=True)
                            self.stdout.write(f'Imported {imported_count} logs so far...')
                            logs_to_create = []

                    except Exception as e:
                        skipped_count += 1
                        self.stdout.write(
                            self.style.WARNING(f'Skipped row due to error: {e}')
                        )

                # Create remaining logs
                if logs_to_create:
                    Log.objects.bulk_create(logs_to_create, ignore_conflicts=True)

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully imported {imported_count} logs. Skipped {skipped_count} rows.'
                )
            )

        finally:
            # Re-enable signals
            post_save.connect(signals.analyze_log_on_create, sender=Log)
            self.stdout.write('Auto-analysis enabled for future logs.')
