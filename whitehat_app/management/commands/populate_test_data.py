"""
Django management command to populate database with test data
Usage: python manage.py populate_test_data
"""

import random
import time
import logging
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from whitehat_app.models import (
    User, Campaign, Event, Incident, RiskHistory,
    Agent, FileUpload, OfflineEvent, Log
)

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Populate database with test data for development and testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before populating',
        )

    def handle(self, *args, **options):
        logger.info("Starting database population with test data...")
        self.stdout.write(self.style.SUCCESS('Starting to populate database with test data...'))

        if options['clear']:
            self.clear_data()

        # Create test data
        users = self.create_users()
        campaigns = self.create_campaigns()
        agents = self.create_agents(users)
        events = self.create_events(users)
        incidents = self.create_incidents(users)
        risk_history = self.create_risk_history(users)
        file_uploads = self.create_file_uploads(agents)
        offline_events = self.create_offline_events(agents)
        logs = self.create_logs()

        self.stdout.write(self.style.SUCCESS(f'\n{"="*60}'))
        self.stdout.write(self.style.SUCCESS('Database populated successfully!'))
        self.stdout.write(self.style.SUCCESS(f'{"="*60}'))
        self.stdout.write(f'Users created: {len(users)}')
        self.stdout.write(f'Campaigns created: {len(campaigns)}')
        self.stdout.write(f'Agents created: {len(agents)}')
        self.stdout.write(f'Events created: {len(events)}')
        self.stdout.write(f'Incidents created: {len(incidents)}')
        self.stdout.write(f'Risk History entries: {len(risk_history)}')
        self.stdout.write(f'File Uploads: {len(file_uploads)}')
        self.stdout.write(f'Offline Events: {len(offline_events)}')
        self.stdout.write(f'Logs created: {len(logs)}')

    def clear_data(self):
        """Clear existing data from all tables"""
        self.stdout.write(self.style.WARNING('Clearing existing data...'))

        Log.objects.all().delete()
        OfflineEvent.objects.all().delete()
        FileUpload.objects.all().delete()
        Agent.objects.all().delete()
        RiskHistory.objects.all().delete()
        Incident.objects.all().delete()
        Event.objects.all().delete()
        Campaign.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()

        self.stdout.write(self.style.SUCCESS('Data cleared successfully!'))

    def create_users(self):
        """Create test users"""
        self.stdout.write('Creating users...')
        users = []

        user_data = [
            {'email': 'john.doe@company.com', 'name': 'John Doe', 'risk_level': 'LOW', 'risk_score': 15.5},
            {'email': 'jane.smith@company.com', 'name': 'Jane Smith', 'risk_level': 'MEDIUM', 'risk_score': 45.2},
            {'email': 'bob.johnson@company.com', 'name': 'Bob Johnson', 'risk_level': 'CRITICAL', 'risk_score': 85.7},
            {'email': 'alice.williams@company.com', 'name': 'Alice Williams', 'risk_level': 'LOW', 'risk_score': 12.3},
            {'email': 'charlie.brown@company.com', 'name': 'Charlie Brown', 'risk_level': 'MEDIUM', 'risk_score': 52.1},
            {'email': 'diana.prince@company.com', 'name': 'Diana Prince', 'risk_level': 'LOW', 'risk_score': 8.9},
            {'email': 'edward.stark@company.com', 'name': 'Edward Stark', 'risk_level': 'CRITICAL', 'risk_score': 92.4},
            {'email': 'fiona.gallagher@company.com', 'name': 'Fiona Gallagher', 'risk_level': 'MEDIUM', 'risk_score': 38.6},
        ]

        for data in user_data:
            user, created = User.objects.get_or_create(
                email=data['email'],
                defaults={
                    'name': data['name'],
                    'risk_level': data['risk_level'],
                    'risk_score': data['risk_score'],
                    'is_active': True,
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                logger.info(f"Created user: {user.email}")
            users.append(user)

        self.stdout.write(self.style.SUCCESS(f'Created {len(users)} users'))
        return users

    def create_campaigns(self):
        """Create test phishing campaigns"""
        self.stdout.write('Creating campaigns...')
        campaigns = []

        campaign_data = [
            {
                'persona_name': 'IT Support',
                'scenario': 'Password Reset Request',
                'target_count': 50,
                'click_count': 12,
                'status': 'completed',
                'sent_at': timezone.now() - timedelta(days=7)
            },
            {
                'persona_name': 'CEO',
                'scenario': 'Urgent Wire Transfer',
                'target_count': 20,
                'click_count': 3,
                'status': 'completed',
                'sent_at': timezone.now() - timedelta(days=14)
            },
            {
                'persona_name': 'HR Department',
                'scenario': 'Benefits Update',
                'target_count': 100,
                'click_count': 25,
                'status': 'active',
                'sent_at': timezone.now() - timedelta(days=2)
            },
            {
                'persona_name': 'Security Team',
                'scenario': 'Security Alert',
                'target_count': 75,
                'click_count': 8,
                'status': 'paused',
                'sent_at': timezone.now() - timedelta(days=5)
            },
            {
                'persona_name': 'Finance',
                'scenario': 'Invoice Payment',
                'target_count': 30,
                'click_count': 0,
                'status': 'draft',
                'sent_at': timezone.now()  # Draft campaigns can have a future send date
            },
        ]

        for data in campaign_data:
            campaign = Campaign.objects.create(**data)
            campaigns.append(campaign)
            logger.info(f"Created campaign: {campaign.persona_name} - {campaign.scenario}")

        self.stdout.write(self.style.SUCCESS(f'Created {len(campaigns)} campaigns'))
        return campaigns

    def create_agents(self, users):
        """Create test agents"""
        self.stdout.write('Creating agents...')
        agents = []

        agent_data = [
            {'hostname': 'DESKTOP-JD01', 'os_type': 'Windows 11', 'status': 'online', 'ip': '192.168.1.101'},
            {'hostname': 'LAPTOP-JS02', 'os_type': 'Windows 10', 'status': 'online', 'ip': '192.168.1.102'},
            {'hostname': 'WORKSTATION-BJ03', 'os_type': 'Windows 11', 'status': 'suspicious', 'ip': '192.168.1.103'},
            {'hostname': 'PC-AW04', 'os_type': 'Windows 10', 'status': 'online', 'ip': '192.168.1.104'},
            {'hostname': 'LAPTOP-CB05', 'os_type': 'macOS 14', 'status': 'offline', 'ip': '192.168.1.105'},
            {'hostname': 'DESKTOP-DP06', 'os_type': 'Windows 11', 'status': 'online', 'ip': '192.168.1.106'},
        ]

        for i, data in enumerate(agent_data):
            if i < len(users):
                agent_id = f"agent_{random.randint(100000, 999999)}"
                agent = Agent.objects.create(
                    agent_id=agent_id,
                    user=users[i],
                    hostname=data['hostname'],
                    os_type=data['os_type'],
                    status=data['status'],
                    ip_address=data['ip']
                )
                agents.append(agent)
                logger.info(f"Created agent: {agent.agent_id} - {agent.hostname}")

        self.stdout.write(self.style.SUCCESS(f'Created {len(agents)} agents'))
        return agents

    def create_events(self, users):
        """Create test events"""
        self.stdout.write('Creating events...')
        events = []

        event_types = [
            ('phishing_click', {'campaign_id': 'camp_123', 'url': 'http://phishing.example.com'}),
            ('bulk_export', {'file_count': 1500, 'size_mb': 250, 'destination': 'USB Drive'}),
            ('usb_connect', {'device_name': 'SanDisk USB', 'serial': 'ABC123456'}),
        ]

        for user in users[:6]:
            for _ in range(random.randint(2, 5)):
                event_type, event_data = random.choice(event_types)
                event = Event.objects.create(
                    user=user,
                    event_type=event_type,
                    event_data=event_data
                )
                events.append(event)
                logger.debug(f"Created event: {event.event_type} for {user.email}")

        self.stdout.write(self.style.SUCCESS(f'Created {len(events)} events'))
        return events

    def create_incidents(self, users):
        """Create test incidents"""
        self.stdout.write('Creating incidents...')
        incidents = []

        incident_types = [
            ('Phishing Link Click', 'MEDIUM'),
            ('Suspicious USB Device', 'CRITICAL'),
            ('Bulk Data Export', 'CRITICAL'),
            ('Tamper Detection: Process Termination', 'CRITICAL'),
            ('Insider Threat: Large File Transfer', 'MEDIUM'),
            ('Failed Login Attempts', 'LOW'),
        ]

        for user in users[:5]:
            for _ in range(random.randint(1, 3)):
                incident_type, severity = random.choice(incident_types)
                incident = Incident.objects.create(
                    user=user,
                    incident_type=incident_type,
                    severity=severity
                )
                incidents.append(incident)
                logger.info(f"Created incident: {incident_type} for {user.email}")

        self.stdout.write(self.style.SUCCESS(f'Created {len(incidents)} incidents'))
        return incidents

    def create_risk_history(self, users):
        """Create risk history entries"""
        self.stdout.write('Creating risk history...')
        risk_history = []

        reasons = [
            'Clicked on phishing link',
            'Connected unauthorized USB device',
            'Exported large dataset',
            'Multiple failed login attempts',
            'Accessed sensitive files outside work hours',
        ]

        for user in users:
            for days_ago in range(30, 0, -5):
                risk_score = max(0, user.risk_score + random.uniform(-20, 20))
                history = RiskHistory.objects.create(
                    user=user,
                    risk_score=risk_score,
                    reason=random.choice(reasons)
                )
                risk_history.append(history)

        self.stdout.write(self.style.SUCCESS(f'Created {len(risk_history)} risk history entries'))
        return risk_history

    def create_file_uploads(self, agents):
        """Create test file uploads"""
        self.stdout.write('Creating file uploads...')
        file_uploads = []

        file_data = [
            {'path': 'E:\\Documents\\confidential.pdf', 'size': 2048576, 'ext': 'pdf', 'status': 'completed'},
            {'path': 'F:\\USB\\malware.exe', 'size': 512000, 'ext': 'exe', 'status': 'completed'},
            {'path': 'E:\\Reports\\Q4_2024.xlsx', 'size': 1024000, 'ext': 'xlsx', 'status': 'pending'},
            {'path': 'F:\\Downloads\\setup.bat', 'size': 256000, 'ext': 'bat', 'status': 'failed'},
        ]

        for agent in agents[:4]:
            for i, data in enumerate(file_data):
                upload_id = f"upload_{agent.agent_id}_{int(time.time())}_{i}"
                file_hash = ''.join(random.choices('abcdef0123456789', k=64))

                upload = FileUpload.objects.create(
                    upload_id=upload_id,
                    agent=agent,
                    file_path=data['path'],
                    file_size=data['size'],
                    file_hash=file_hash,
                    minio_url=f'http://minio:9000/uploads/{upload_id}',
                    bucket='whitehat-uploads',
                    object_name=f'agents/{agent.agent_id}/suspicious/{data["path"].split("\\")[-1]}',
                    status=data['status'],
                    error_message='Upload timeout' if data['status'] == 'failed' else None
                )

                if data['status'] == 'completed':
                    upload.completed_at = timezone.now() - timedelta(hours=random.randint(1, 48))
                    upload.save()

                file_uploads.append(upload)
                logger.debug(f"Created file upload: {upload_id}")

        self.stdout.write(self.style.SUCCESS(f'Created {len(file_uploads)} file uploads'))
        return file_uploads

    def create_offline_events(self, agents):
        """Create offline events"""
        self.stdout.write('Creating offline events...')
        offline_events = []

        event_types = ['usb_connect', 'file_scan', 'process_monitor', 'network_scan']

        for agent in agents:
            for _ in range(random.randint(5, 15)):
                event = OfflineEvent.objects.create(
                    agent=agent,
                    event_type=random.choice(event_types),
                    payload={
                        'action': random.choice(['scan', 'block', 'allow']),
                        'details': f'Event details for {random.choice(event_types)}'
                    },
                    timestamp=int((timezone.now() - timedelta(hours=random.randint(1, 72))).timestamp())
                )
                offline_events.append(event)

        self.stdout.write(self.style.SUCCESS(f'Created {len(offline_events)} offline events'))
        return offline_events

    def create_logs(self):
        """Create activity logs"""
        self.stdout.write('Creating logs...')
        logs = []

        employee_ids = ['E001', 'E002', 'E003', 'E004', 'E005', 'E006', 'E007', 'E008']
        action_types = ['file_access', 'login', 'logout', 'export', 'print', 'email_send']
        resource_types = ['document', 'database', 'api', 'file_share']
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/121.0'
        ]

        for _ in range(100):
            timestamp = timezone.now() - timedelta(days=random.randint(0, 30), hours=random.randint(0, 23))

            log = Log.objects.create(
                timestamp=timestamp,
                employee_id=random.choice(employee_ids),
                session_id=f'sess_{random.randint(100000, 999999)}',
                ip_address=f'192.168.1.{random.randint(100, 200)}',
                user_agent=random.choice(user_agents),
                action_type=random.choice(action_types),
                resource_accessed=f'/api/v1/{random.choice(["users", "files", "reports"])}/{random.randint(1, 100)}',
                resource_type=random.choice(resource_types),
                request_status=random.choice(['success', 'failed'])
            )
            logs.append(log)

        self.stdout.write(self.style.SUCCESS(f'Created {len(logs)} logs'))
        return logs
