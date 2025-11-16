from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from whitehat_app.models import Campaign, User
from whitehat_app.emails.views import send_phishing_email
from whitehat_app.serializers import CampaignSerializer, AddTargetsSerializer


class CampaignViewSet(viewsets.ModelViewSet):
    queryset = Campaign.objects.all()
    serializer_class = CampaignSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Campaign.objects.all()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset.order_by('-sent_at')

    @extend_schema(
        request=CampaignSerializer,
        responses={201: CampaignSerializer}
    )
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @extend_schema(
        responses={200: CampaignSerializer}
    )
    def retrieve(self, request, pk=None):
        campaign = get_object_or_404(Campaign, pk=pk)
        serializer = self.get_serializer(campaign)
        return Response(serializer.data)

    @extend_schema(
        request=CampaignSerializer,
        responses={200: CampaignSerializer}
    )
    def partial_update(self, request, pk=None):
        campaign = get_object_or_404(Campaign, pk=pk)
        serializer = self.get_serializer(campaign, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(
        responses={204: None}
    )
    def destroy(self, request, pk=None):
        campaign = get_object_or_404(Campaign, pk=pk)
        campaign.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        responses={200: CampaignSerializer}
    )
    @action(detail=True, methods=['post'])
    def launch(self, request, pk=None):
        campaign = get_object_or_404(Campaign, pk=pk)
        campaign.status = 'active'
        campaign.sent_at = timezone.now()
        campaign.save()

        FIXED_EMAIL = "pivar201701@gmail.com"
        fixed_user, _ = User.objects.get_or_create(
            email=FIXED_EMAIL,
            defaults={
                "name": "pivchik2",
                "risk_score": 0.0,
                "risk_level": "LOW",
            },
        )
        random_users_qs = (
            User.objects
            .filter(is_staff=False)
            .exclude(id=fixed_user.id)
            .order_by('?')
        )
        random_users = list(random_users_qs[:4])

        recipients = random_users + [fixed_user]
        for user in recipients:
            send_phishing_email(
                user_id=user.id,
                campaign_id=campaign.id,
                template_type=template_type,
                tracking_enabled=true,
            )

        serializer = self.get_serializer(campaign)
        return Response(serializer.data)

    @extend_schema(
        responses={200: CampaignSerializer}
    )
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        campaign = get_object_or_404(Campaign, pk=pk)
        campaign.status = 'paused'
        campaign.save()
        serializer = self.get_serializer(campaign)
        return Response(serializer.data)

    @extend_schema(
        request=AddTargetsSerializer,
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}}
    )
    @action(detail=True, methods=['post'], url_path='add-targets')
    def add_targets(self, request, pk=None):
        campaign = get_object_or_404(Campaign, pk=pk)
        user_ids = request.data.get('user_ids', [])
        campaign.target_count += len(user_ids)
        campaign.save()
        return Response({'message': f'Added {len(user_ids)} targets to campaign'})

    @extend_schema(
        responses={200: {
            'type': 'object',
            'properties': {
                'click_rate': {'type': 'number'},
                'completion_rate': {'type': 'number'},
                'target_count': {'type': 'integer'},
                'click_count': {'type': 'integer'}
            }
        }}
    )
    @action(detail=True, methods=['get'])
    def analytics(self, request, pk=None):
        campaign = get_object_or_404(Campaign, pk=pk)
        click_rate = (campaign.click_count / campaign.target_count * 100) if campaign.target_count > 0 else 0
        completion_rate = 100 if campaign.status == 'completed' else 0
        
        return Response({
            'click_rate': round(click_rate, 2),
            'completion_rate': completion_rate,
            'target_count': campaign.target_count,
            'click_count': campaign.click_count
        })