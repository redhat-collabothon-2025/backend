from rest_framework import serializers

from whitehat_app.models import (
    User, Campaign, Event, Incident, RiskHistory, Log,
    Agent, FileUpload, OfflineEvent
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'name', 'risk_score', 'risk_level', 'created_at']
        read_only_fields = ['id', 'created_at']


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField()


class CampaignSerializer(serializers.ModelSerializer):
    class Meta:
        model = Campaign
        fields = '__all__'


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = Event
        fields = '__all__'


class IncidentSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)

    class Meta:
        model = Incident
        fields = ['id', 'user', 'user_email', 'user_name', 'incident_type', 'severity', 'created_at']


class RiskHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RiskHistory
        fields = '__all__'


class SendPhishingEmailSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    campaign_id = serializers.UUIDField(required=False, allow_null=True)
    template_type = serializers.ChoiceField(
        choices=['linkedin', 'general'],
        default='linkedin'
    )
    tracking_enabled = serializers.BooleanField(default=True)


class BulkPhishingSerializer(serializers.Serializer):
    user_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False
    )
    campaign_id = serializers.UUIDField(required=False, allow_null=True)
    template_type = serializers.ChoiceField(
        choices=['linkedin', 'general'],
        default='linkedin'
    )


class PhishingResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    tracking_id = serializers.UUIDField()


class BulkPhishingResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
    sent_count = serializers.IntegerField()
    failed_count = serializers.IntegerField()
    skipped_count = serializers.IntegerField()


class AddTargetsSerializer(serializers.Serializer):
    user_ids = serializers.ListField(
        child=serializers.UUIDField(),
        allow_empty=False
    )


class EventCreateSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    event_type = serializers.ChoiceField(
        choices=['phishing_click', 'bulk_export', 'usb_connect']
    )
    event_data = serializers.JSONField()


class IncidentCreateSerializer(serializers.Serializer):
    user_id = serializers.UUIDField()
    incident_type = serializers.CharField()
    severity = serializers.ChoiceField(
        choices=Incident.SEVERITY_CHOICES
    )


class IncidentUpdateSerializer(serializers.Serializer):
    incident_type = serializers.CharField(required=False)
    severity = serializers.ChoiceField(
        choices=Incident.SEVERITY_CHOICES,
        required=False
    )


class LogSerializer(serializers.ModelSerializer):
    class Meta:
        model = Log
        fields = '__all__'


class AgentSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)
    user_risk_level = serializers.CharField(source='user.risk_level', read_only=True)

    class Meta:
        model = Agent
        fields = [
            'agent_id', 'user', 'user_email', 'user_name', 'user_risk_level',
            'hostname', 'os_type', 'ip_address', 'status',
            'last_heartbeat', 'created_at'
        ]
        read_only_fields = ['agent_id', 'last_heartbeat', 'created_at']


class FileUploadSerializer(serializers.ModelSerializer):
    agent_hostname = serializers.CharField(source='agent.hostname', read_only=True)
    agent_user_email = serializers.CharField(source='agent.user.email', read_only=True)

    class Meta:
        model = FileUpload
        fields = [
            'upload_id', 'agent', 'agent_hostname', 'agent_user_email',
            'file_path', 'file_size', 'file_hash', 'bucket', 'object_name',
            'status', 'error_message', 'created_at', 'completed_at'
        ]
        read_only_fields = ['upload_id', 'created_at', 'completed_at']


class OfflineEventSerializer(serializers.ModelSerializer):
    agent_hostname = serializers.CharField(source='agent.hostname', read_only=True)
    agent_id = serializers.CharField(source='agent.agent_id', read_only=True)

    class Meta:
        model = OfflineEvent
        fields = [
            'id', 'agent', 'agent_id', 'agent_hostname',
            'event_type', 'payload', 'timestamp', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
