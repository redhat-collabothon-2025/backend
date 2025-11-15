import time
from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from whitehat_app.models import Agent, FileUpload, OfflineEvent, User
from whitehat_app.minio_service import minio_service


@extend_schema(
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'agent_id': {'type': 'string'},
                'hostname': {'type': 'string'},
                'os': {'type': 'string'},
                'user_email': {'type': 'string'}
            }
        }
    },
    responses={200: {'description': 'Heartbeat received'}}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def heartbeat(request):
    try:
        data = request.data
        agent_id = data.get('agent_id')
        hostname = data.get('hostname')
        os_type = data.get('os')
        user_email = data.get('user_email')

        if not all([agent_id, hostname, os_type, user_email]):
            return Response(
                {'error': 'missing_fields'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            return Response(
                {'error': 'user_not_found'},
                status=status.HTTP_404_NOT_FOUND
            )

        agent, created = Agent.objects.update_or_create(
            agent_id=agent_id,
            defaults={
                'user': user,
                'hostname': hostname,
                'os_type': os_type,
                'status': 'online',
                'ip_address': request.META.get('REMOTE_ADDR'),
            }
        )

        file_actions = []

        return Response({
            'status': 'ok',
            'file_actions': file_actions
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'agent_id': {'type': 'string'},
                'file_path': {'type': 'string'},
                'file_size': {'type': 'integer'},
                'file_hash': {'type': 'string'}
            }
        }
    },
    responses={
        200: {
            'description': 'Upload URL generated',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'upload_id': {'type': 'string'},
                            'upload_url': {'type': 'string'}
                        }
                    }
                }
            }
        }
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def request_upload(request):
    try:
        data = request.data
        agent_id = data.get('agent_id')
        file_path = data.get('file_path')
        file_size = data.get('file_size')
        file_hash = data.get('file_hash')

        if not all([agent_id, file_path, file_size, file_hash]):
            return Response(
                {'error': 'missing_fields'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            agent = Agent.objects.get(agent_id=agent_id)
        except Agent.DoesNotExist:
            return Response(
                {'error': 'agent_not_found'},
                status=status.HTTP_404_NOT_FOUND
            )

        upload_id = f"upload_{int(time.time())}"
        object_name = f"agents/{agent_id}/{file_hash}.enc"

        upload_url = minio_service.get_upload_url(object_name)

        if not upload_url:
            return Response(
                {
                    'upload_id': upload_id,
                    'success': False,
                    'error': 'connection_error'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        FileUpload.objects.create(
            upload_id=upload_id,
            agent=agent,
            file_path=file_path,
            file_size=file_size,
            file_hash=file_hash,
            minio_url=upload_url,
            bucket=minio_service.bucket,
            object_name=object_name,
            status='pending'
        )

        return Response({
            'upload_id': upload_id,
            'upload_url': upload_url
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {
                'upload_id': f"upload_{int(time.time())}",
                'success': False,
                'error': 'connection_error'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'upload_id': {'type': 'string'}
            }
        }
    },
    responses={
        200: {
            'description': 'Upload confirmed',
            'content': {
                'application/json': {
                    'schema': {
                        'type': 'object',
                        'properties': {
                            'upload_id': {'type': 'string'},
                            'success': {'type': 'boolean'}
                        }
                    }
                }
            }
        }
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def complete_upload(request):
    try:
        data = request.data
        upload_id = data.get('upload_id')

        if not upload_id:
            return Response(
                {
                    'upload_id': upload_id,
                    'success': False,
                    'error': 'missing_upload_id'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            file_upload = FileUpload.objects.get(upload_id=upload_id)
        except FileUpload.DoesNotExist:
            return Response(
                {
                    'upload_id': upload_id,
                    'success': False,
                    'error': 'upload_not_found'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if minio_service.file_exists(file_upload.object_name):
            file_upload.status = 'completed'
            file_upload.completed_at = timezone.now()
            file_upload.save()

            return Response({
                'upload_id': upload_id,
                'success': True
            }, status=status.HTTP_200_OK)
        else:
            file_upload.status = 'failed'
            file_upload.save()

            return Response({
                'upload_id': upload_id,
                'success': False,
                'error': 'file_not_found'
            }, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        return Response(
            {
                'upload_id': upload_id if 'upload_id' in locals() else 'unknown',
                'success': False,
                'error': 'connection_error'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'events': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'type': {'type': 'string'},
                            'payload': {'type': 'object'},
                            'timestamp': {'type': 'integer'}
                        }
                    }
                }
            }
        }
    },
    responses={200: {'description': 'Offline events queued'}}
)
@api_view(['POST'])
@permission_classes([AllowAny])
def offline_queue(request):
    try:
        data = request.data
        events = data.get('events', [])
        agent_id = data.get('agent_id')

        if not agent_id:
            return Response(
                {'error': 'missing_agent_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            agent = Agent.objects.get(agent_id=agent_id)
        except Agent.DoesNotExist:
            return Response(
                {'error': 'agent_not_found'},
                status=status.HTTP_404_NOT_FOUND
            )

        for event in events:
            OfflineEvent.objects.create(
                agent=agent,
                event_type=event.get('type'),
                payload=event.get('payload', {}),
                timestamp=event.get('timestamp', int(time.time()))
            )

        return Response({
            'status': 'ok',
            'queued': len(events)
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
