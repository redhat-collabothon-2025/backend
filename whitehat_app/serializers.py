from rest_framework import serializers

from whitehat_app.models import User, Campaign, Event, Incident, RiskHistory


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
        choices=['LOW', 'MEDIUM', 'CRITICAL']
    )


class IncidentUpdateSerializer(serializers.Serializer):
    incident_type = serializers.CharField(required=False)
    severity = serializers.ChoiceField(
        choices=['LOW', 'MEDIUM', 'CRITICAL'],
        required=False
    )
