import uuid
import random
from datetime import datetime
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from whitehat_app.models import User, Campaign, Event
from ..serializers import (
    SendPhishingEmailSerializer,
    BulkPhishingSerializer,
    PhishingResponseSerializer,
    BulkPhishingResponseSerializer
)


@extend_schema(
    request=SendPhishingEmailSerializer,
    responses={
        200: PhishingResponseSerializer,
        400: {'description': 'Invalid parameters'},
        404: {'description': 'User not found'}
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_phishing_email(request):
    serializer = SendPhishingEmailSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user_id = serializer.validated_data['user_id']
    campaign_id = serializer.validated_data.get('campaign_id')
    template_type = serializer.validated_data.get('template_type', 'linkedin')
    tracking_enabled = serializer.validated_data.get('tracking_enabled', True)

    try:
        target_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    campaign = None
    if campaign_id:
        try:
            campaign = Campaign.objects.get(id=campaign_id)
        except Campaign.DoesNotExist:
            pass

    tracking_id = str(uuid.uuid4())
    base_url = request.build_absolute_uri('/')[:-1]
    phishing_link = f"{base_url}/api/phishing/click/{tracking_id}"
    tracking_pixel_url = f"{base_url}/api/phishing/track/{tracking_id}"

    if template_type == 'linkedin':
        email_context = {
            'user_name': target_user.name.split()[0] if target_user.name else 'Professional',
            'user_email': target_user.email,
            'notification_count': random.randint(5, 23),
            'viewer_initials': random.choice(['JM', 'RS', 'AK', 'TW', 'LB']),
            'viewer_name': random.choice([
                'James Mitchell',
                'Rachel Stevens',
                'Alex Kumar',
                'Thomas Wilson',
                'Lisa Brown'
            ]),
            'viewer_title': random.choice([
                'Senior Recruiter',
                'Talent Acquisition Manager',
                'HR Director',
                'Technical Recruiter',
                'Hiring Manager'
            ]),
            'viewer_company': random.choice([
                'Tech Solutions Inc',
                'Global Innovations Corp',
                'Future Systems Ltd',
                'Digital Ventures Group',
                'Cloud Technologies'
            ]),
            'user_field': random.choice([
                'software development',
                'data analysis',
                'project management',
                'security operations',
                'system administration'
            ]),
            'pending_invitations': random.randint(2, 8),
            'unread_messages': random.randint(1, 5),
            'phishing_link': phishing_link,
            'tracking_pixel_url': tracking_pixel_url if tracking_enabled else '#',
            'current_year': datetime.now().year
        }

        html_message = render_to_string('emails/linkedin_phishing.html', email_context)
        subject = f"👤 {email_context['notification_count']} people viewed your LinkedIn profile"
    else:
        email_context = {
            'company_name': 'Your Company',
            'subject': 'Urgent: Account Verification Required',
            'user_name': target_user.name or 'Employee',
            'user_email': target_user.email,
            'email_body': 'We have detected unusual activity on your account. For your security, we need you to verify your account information immediately.',
            'warning_message': 'Your account will be suspended within 24 hours if action is not taken.',
            'action_text': 'Please click the button below to verify your account and prevent any service interruption.',
            'phishing_link': phishing_link,
            'button_text': 'Verify Account Now',
            'closing_text': 'Thank you for your immediate attention to this matter.',
            'sender_name': 'IT Security Team',
            'sender_title': 'Information Security Department',
            'tracking_pixel_url': tracking_pixel_url if tracking_enabled else '#',
            'current_year': datetime.now().year
        }

        html_message = render_to_string('emails/phishing_simulation.html', email_context)
        subject = '🔴 Urgent: Account Verification Required'

    plain_message = strip_tags(html_message)

    if tracking_enabled:
        Event.objects.create(
            user=target_user,
            event_type='phishing_click',
            event_data={
                'tracking_id': tracking_id,
                'campaign_id': str(campaign.id) if campaign else None,
                'template_type': template_type,
                'sent_at': datetime.now().isoformat(),
                'status': 'sent'
            }
        )

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email='security@company.com',
            recipient_list=[target_user.email],
            html_message=html_message,
            fail_silently=False
        )

        if campaign:
            campaign.target_count += 1
            campaign.save()

        return Response({
            'message': f'Phishing email sent to {target_user.email}',
            'tracking_id': tracking_id
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Failed to send email: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    responses={
        302: {'description': 'Redirect to warning page'},
        404: {'description': 'Tracking ID not found'}
    }
)
@api_view(['GET'])
@permission_classes([])
def track_click(request, tracking_id):
    try:
        event = Event.objects.filter(
            event_data__tracking_id=tracking_id
        ).first()

        if event:
            event.event_data['clicked'] = True
            event.event_data['clicked_at'] = datetime.now().isoformat()
            event.save()

            if 'campaign_id' in event.event_data and event.event_data['campaign_id']:
                try:
                    campaign = Campaign.objects.get(id=event.event_data['campaign_id'])
                    campaign.click_count += 1
                    campaign.save()
                except Campaign.DoesNotExist:
                    pass

        return Response(
            status=status.HTTP_302_FOUND,
            headers={'Location': '/phishing-awareness-training'}
        )
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    responses={
        200: {'description': 'Tracking pixel served'},
        404: {'description': 'Tracking ID not found'}
    }
)
@api_view(['GET'])
@permission_classes([])
def track_open(request, tracking_id):
    try:
        event = Event.objects.filter(
            event_data__tracking_id=tracking_id
        ).first()

        if event:
            event.event_data['opened'] = True
            event.event_data['opened_at'] = datetime.now().isoformat()
            event.save()

        pixel = b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\x00\x00\x00\x21\xF9\x04\x01\x00\x00\x00\x00\x2C\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3B'

        return Response(
            pixel,
            content_type='image/gif',
            status=status.HTTP_200_OK
        )
    except Exception:
        return Response(status=status.HTTP_404_NOT_FOUND)


@extend_schema(
    request=BulkPhishingSerializer,
    responses={
        200: BulkPhishingResponseSerializer
    }
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_bulk_phishing(request):
    serializer = BulkPhishingSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user_ids = serializer.validated_data['user_ids']
    campaign_id = serializer.validated_data.get('campaign_id')
    template_type = serializer.validated_data.get('template_type', 'linkedin')

    sent_count = 0
    failed_count = 0

    for user_id in user_ids:
        try:
            response = send_phishing_email(request._request.__class__(
                {
                    'REQUEST_METHOD': 'POST',
                    'wsgi.url_scheme': request._request.scheme,
                    'SERVER_NAME': request._request.META['SERVER_NAME'],
                    'SERVER_PORT': request._request.META.get('SERVER_PORT', '80'),
                    'PATH_INFO': '/api/phishing/send/',
                    'QUERY_STRING': '',
                    'CONTENT_TYPE': 'application/json',
                    'HTTP_HOST': request._request.META.get('HTTP_HOST', 'localhost'),
                }
            ))
            response._request.user = request.user
            response._request.data = {
                'user_id': user_id,
                'campaign_id': campaign_id,
                'template_type': template_type,
                'tracking_enabled': True
            }

            result = send_phishing_email(response._request)
            if result.status_code == 200:
                sent_count += 1
            else:
                failed_count += 1
        except Exception:
            failed_count += 1

    return Response({
        'message': f'Bulk phishing campaign completed',
        'sent_count': sent_count,
        'failed_count': failed_count
    }, status=status.HTTP_200_OK)