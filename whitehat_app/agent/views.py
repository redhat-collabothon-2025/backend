import time
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from whitehat_app.models import Agent, FileUpload, OfflineEvent, User, Incident, Event
from whitehat_app.minio_service import minio_service
from whitehat_app.serializers import AgentSerializer, FileUploadSerializer, OfflineEventSerializer

# Initialize logger
logger = logging.getLogger(__name__)


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
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def heartbeat(request):
    try:
        data = request.data
        agent_id = data.get('agent_id')
        hostname = data.get('hostname')
        os_type = data.get('os')
        user_email = data.get('user_email')

        logger.info(f"Heartbeat received from agent_id={agent_id}, hostname={hostname}, user_email={user_email}")

        if not all([agent_id, hostname, os_type, user_email]):
            logger.warning(f"Heartbeat missing fields: agent_id={agent_id}, hostname={hostname}, os={os_type}, user_email={user_email}")
            return Response(
                {'error': 'missing_fields'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(email=user_email)
        except User.DoesNotExist:
            logger.error(f"User not found for email={user_email} in heartbeat from agent_id={agent_id}")
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

        if created:
            logger.info(f"New agent created: agent_id={agent_id}, hostname={hostname}, user={user.email}")
        else:
            logger.debug(f"Agent updated: agent_id={agent_id}, status=online, ip={request.META.get('REMOTE_ADDR')}")

        file_actions = []

        return Response({
            'status': 'ok',
            'file_actions': file_actions
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Heartbeat error for agent_id={agent_id}: {str(e)}", exc_info=True)
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
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def request_upload(request):
    try:
        data = request.data
        agent_id = data.get('agent_id')
        filename = data.get('filename')
        file_size = data.get('file_size')
        category = data.get('category', 'unknown')
        metadata = data.get('metadata', {})

        # Support both old and new parameter names
        file_path = data.get('file_path') or metadata.get('original_path') or filename
        file_hash = data.get('file_hash') or metadata.get('hash', '')

        logger.info(f"Upload request from agent_id={agent_id}, filename={filename}, size={file_size}, category={category}")

        if not all([agent_id, filename, file_size]):
            logger.warning(f"Upload request missing fields: agent_id={agent_id}, filename={filename}, file_size={file_size}")
            return Response(
                {'error': 'missing_fields'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            agent = Agent.objects.get(agent_id=agent_id)
        except Agent.DoesNotExist:
            logger.error(f"Agent not found for upload request: agent_id={agent_id}")
            return Response(
                {'error': 'agent_not_found'},
                status=status.HTTP_404_NOT_FOUND
            )

        upload_id = f"upload_{agent_id}_{int(time.time())}"
        object_name = f"agents/{agent_id}/{category}/{filename}"

        logger.debug(f"Generating presigned URL for upload_id={upload_id}, object_name={object_name}")
        presigned_url = minio_service.get_upload_url(object_name)

        if not presigned_url:
            logger.error(f"Failed to generate presigned URL for upload_id={upload_id}, agent_id={agent_id}")
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
            minio_url=presigned_url,
            bucket=minio_service.bucket,
            object_name=object_name,
            status='pending'
        )

        logger.info(f"Upload request created: upload_id={upload_id}, agent_id={agent_id}, hash={file_hash[:16]}...")

        return Response({
            'upload_id': upload_id,
            'presigned_url': presigned_url
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Upload request error: {str(e)}", exc_info=True)
        return Response(
            {
                'upload_id': f"upload_{int(time.time())}",
                'success': False,
                'error': str(e)
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
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def complete_upload(request):
    try:
        data = request.data
        agent_id = data.get('agent_id')
        upload_id = data.get('upload_id')
        success = data.get('success', False)
        error = data.get('error')

        logger.info(f"Upload completion from agent_id={agent_id}, upload_id={upload_id}, success={success}")

        if not upload_id:
            logger.warning(f"Upload completion missing upload_id from agent_id={agent_id}")
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
            logger.error(f"Upload not found: upload_id={upload_id}, agent_id={agent_id}")
            return Response(
                {
                    'upload_id': upload_id,
                    'success': False,
                    'error': 'upload_not_found'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        if success:
            # Agent reports successful upload
            file_upload.status = 'completed'
            file_upload.completed_at = timezone.now()
            file_upload.save()

            logger.info(f"Upload completed successfully: upload_id={upload_id}, agent_id={agent_id}, file_path={file_upload.file_path}")

            return Response({
                'upload_id': upload_id,
                'success': True
            }, status=status.HTTP_200_OK)
        else:
            # Agent reports failed upload
            file_upload.status = 'failed'
            file_upload.error_message = error or 'Unknown error'
            file_upload.save()

            logger.error(f"Upload failed: upload_id={upload_id}, agent_id={agent_id}, error={error}")

            return Response({
                'upload_id': upload_id,
                'success': False,
                'error': error or 'upload_failed'
            }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Upload completion error: upload_id={upload_id if 'upload_id' in locals() else 'unknown'}, error={str(e)}", exc_info=True)
        return Response(
            {
                'upload_id': upload_id if 'upload_id' in locals() else 'unknown',
                'success': False,
                'error': str(e)
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
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def offline_queue(request):
    try:
        data = request.data
        events = data.get('events', [])
        agent_id = data.get('agent_id')

        logger.info(f"Offline queue submission from agent_id={agent_id}, event_count={len(events)}")

        if not agent_id:
            logger.warning(f"Offline queue missing agent_id")
            return Response(
                {'error': 'missing_agent_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            agent = Agent.objects.get(agent_id=agent_id)
        except Agent.DoesNotExist:
            logger.error(f"Agent not found for offline queue: agent_id={agent_id}")
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
            logger.debug(f"Offline event queued: agent_id={agent_id}, type={event.get('type')}")

        logger.info(f"Offline events queued successfully: agent_id={agent_id}, count={len(events)}")

        return Response({
            'status': 'ok',
            'queued': len(events)
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Offline queue error: agent_id={agent_id if 'agent_id' in locals() else 'unknown'}, error={str(e)}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='agent_id',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Agent ID to retrieve commands for'
        )
    ],
    responses={200: {'description': 'Agent commands retrieved'}}
)
@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def get_commands(request):
    """Get pending commands for an agent"""
    try:
        agent_id = request.query_params.get('agent_id')

        logger.debug(f"Command request from agent_id={agent_id}")

        if not agent_id:
            logger.warning(f"Command request missing agent_id")
            return Response(
                {'error': 'missing_agent_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # For now, return empty commands list
        # Future: implement AgentCommand model and retrieve pending commands
        logger.debug(f"Returning empty commands list for agent_id={agent_id}")
        return Response({
            'commands': []
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Get commands error: agent_id={agent_id if 'agent_id' in locals() else 'unknown'}, error={str(e)}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='agent_id',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Agent ID to retrieve whitelist for'
        )
    ],
    responses={200: {'description': 'Whitelist retrieved'}}
)
@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def get_whitelist(request):
    """Get USB device whitelist for an agent"""
    try:
        agent_id = request.query_params.get('agent_id')

        logger.debug(f"Whitelist request from agent_id={agent_id}")

        if not agent_id:
            logger.warning(f"Whitelist request missing agent_id")
            return Response(
                {'error': 'missing_agent_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # For now, return empty whitelist
        # Future: implement UsbWhitelist model
        logger.debug(f"Returning empty whitelist for agent_id={agent_id}")
        return Response({
            'devices': []
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Get whitelist error: agent_id={agent_id if 'agent_id' in locals() else 'unknown'}, error={str(e)}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='agent_id',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=True,
            description='Agent ID to retrieve configuration for'
        )
    ],
    responses={200: {'description': 'Agent configuration retrieved'}}
)
@csrf_exempt
@api_view(['GET'])
@permission_classes([AllowAny])
def get_agent_config(request):
    """Get agent configuration"""
    try:
        agent_id = request.query_params.get('agent_id')

        logger.info(f"Config request from agent_id={agent_id}")

        if not agent_id:
            logger.warning(f"Config request missing agent_id")
            return Response(
                {'error': 'missing_agent_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Return default configuration
        # Future: make this configurable per agent or globally
        config = {
            'enforce_acl': True,
            'dangerous_ext': ['.exe', '.ps1', '.bat', '.vbs', '.scr', '.com', '.pif'],
            'max_upload_size': 52428800  # 50MB
        }
        logger.debug(f"Returning config for agent_id={agent_id}: {config}")
        return Response(config, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Get config error: agent_id={agent_id if 'agent_id' in locals() else 'unknown'}, error={str(e)}", exc_info=True)
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
                'drive': {'type': 'string'},
                'volume': {
                    'type': 'object',
                    'properties': {
                        'label': {'type': 'string'},
                        'fs': {'type': 'string'},
                        'serial': {'type': 'string'}
                    }
                },
                'files': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'relpath': {'type': 'string'},
                            'size': {'type': 'integer'},
                            'ext': {'type': 'string'},
                            'sha256': {'type': 'string'},
                            'vt_result': {'type': 'object'}
                        }
                    }
                },
                'timestamp': {'type': 'integer'}
            }
        }
    },
    responses={200: {'description': 'USB event processed, file actions returned'}}
)
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def usb_event(request):
    """Process USB insertion event and return file action policies"""
    try:
        data = request.data
        agent_id = data.get('agent_id')
        drive = data.get('drive')
        volume = data.get('volume', {})
        files = data.get('files', [])
        timestamp = data.get('timestamp')

        logger.info(f"USB event from agent_id={agent_id}, drive={drive}, file_count={len(files)}, volume_label={volume.get('label', 'N/A')}")

        if not agent_id:
            logger.warning(f"USB event missing agent_id")
            return Response(
                {'error': 'missing_agent_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify agent exists
        try:
            agent = Agent.objects.get(agent_id=agent_id)
        except Agent.DoesNotExist:
            logger.error(f"Agent not found for USB event: agent_id={agent_id}")
            return Response(
                {'error': 'agent_not_found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Analyze files and determine actions
        file_actions = {}
        dangerous_extensions = ['.exe', '.ps1', '.bat', '.vbs', '.scr', '.com', '.pif']

        for file_info in files:
            relpath = file_info.get('relpath')
            ext = file_info.get('ext', '').lower()
            vt_result = file_info.get('vt_result')

            # Determine action based on file characteristics
            if vt_result and vt_result.get('malicious', 0) > 0:
                # VirusTotal detected malware
                file_actions[relpath] = 'quarantine'
                logger.warning(f"Malware detected: agent_id={agent_id}, file={relpath}, malicious_count={vt_result.get('malicious')}")
            elif ext in dangerous_extensions:
                # Dangerous extension - upload for deep scan
                file_actions[relpath] = 'upload_for_deep_scan'
                logger.info(f"Dangerous file detected: agent_id={agent_id}, file={relpath}, ext={ext}")
            # else: allow by default (not added to file_actions)

        logger.info(f"USB event processed: agent_id={agent_id}, total_files={len(files)}, actions={len(file_actions)}")

        return Response({
            'default_action': 'allow',
            'file_actions': file_actions
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"USB event error: agent_id={agent_id if 'agent_id' in locals() else 'unknown'}, error={str(e)}", exc_info=True)
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
                'timestamp': {'type': 'integer'},
                'detail': {'type': 'string'}
            }
        }
    },
    responses={200: {'description': 'Tamper alert received'}}
)
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def tamper_alert(request):
    """Process tamper detection alert from agent"""
    try:
        data = request.data
        agent_id = data.get('agent_id')
        detail = data.get('detail')
        timestamp = data.get('timestamp')

        logger.critical(f"TAMPER ALERT from agent_id={agent_id}, detail={detail}")

        if not agent_id:
            logger.warning(f"Tamper alert missing agent_id")
            return Response(
                {'error': 'missing_agent_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify agent exists
        try:
            agent = Agent.objects.get(agent_id=agent_id)
        except Agent.DoesNotExist:
            logger.error(f"Agent not found for tamper alert: agent_id={agent_id}")
            return Response(
                {'error': 'agent_not_found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Update agent status to suspicious
        agent.status = 'suspicious'
        agent.save()
        logger.warning(f"Agent status updated to suspicious: agent_id={agent_id}, user={agent.user.email}")

        # Create an incident for tamper detection
        incident = Incident.objects.create(
            user=agent.user,
            incident_type=f'Tamper Detection: {detail}',
            severity='CRITICAL'
        )
        logger.critical(f"Tamper incident created: incident_id={incident.id}, agent_id={agent_id}, user={agent.user.email}, detail={detail}")

        return Response({
            'status': 'ok',
            'message': 'Tamper alert recorded'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Tamper alert error: agent_id={agent_id if 'agent_id' in locals() else 'unknown'}, error={str(e)}", exc_info=True)
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
                'event_type': {'type': 'string'},
                'details': {'type': 'object'},
                'timestamp': {'type': 'integer'}
            }
        }
    },
    responses={200: {'description': 'Insider alert received'}}
)
@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def insider_alert(request):
    """Process insider threat alert from agent"""
    try:
        data = request.data
        agent_id = data.get('agent_id')
        event_type = data.get('event_type')
        details = data.get('details', {})
        timestamp = data.get('timestamp')

        logger.warning(f"INSIDER THREAT ALERT from agent_id={agent_id}, event_type={event_type}")

        if not agent_id:
            logger.warning(f"Insider alert missing agent_id")
            return Response(
                {'error': 'missing_agent_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify agent exists
        try:
            agent = Agent.objects.get(agent_id=agent_id)
        except Agent.DoesNotExist:
            logger.error(f"Agent not found for insider alert: agent_id={agent_id}")
            return Response(
                {'error': 'agent_not_found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Create event
        event = Event.objects.create(
            user=agent.user,
            event_type=event_type,
            event_data=details
        )
        logger.info(f"Insider event created: event_id={event.id}, agent_id={agent_id}, type={event_type}")

        # Create incident based on severity
        severity = 'MEDIUM'
        if 'bulk_export' in event_type.lower():
            severity = 'CRITICAL'
            logger.critical(f"Bulk export detected: agent_id={agent_id}, user={agent.user.email}")

        incident = Incident.objects.create(
            user=agent.user,
            incident_type=f'Insider Threat: {event_type}',
            severity=severity
        )
        logger.warning(f"Insider incident created: incident_id={incident.id}, agent_id={agent_id}, user={agent.user.email}, severity={severity}, type={event_type}")

        return Response({
            'status': 'ok',
            'message': 'Insider alert recorded'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Insider alert error: agent_id={agent_id if 'agent_id' in locals() else 'unknown'}, error={str(e)}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


# ============================================================================
# API Endpoints for Agent Management and Monitoring
# ============================================================================

@extend_schema(
    parameters=[
        OpenApiParameter(
            name='status',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Filter agents by status (online, offline, suspicious)'
        ),
        OpenApiParameter(
            name='user_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Filter agents by user ID'
        ),
    ],
    responses={200: AgentSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def list_agents(request):
    """Get list of all agents with optional filtering"""
    try:
        logger.info(f"Agent list request from IP: {request.META.get('REMOTE_ADDR')}")

        agents = Agent.objects.select_related('user').all()

        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            agents = agents.filter(status=status_filter)
            logger.debug(f"Filtering agents by status: {status_filter}")

        # Filter by user_id if provided
        user_id = request.query_params.get('user_id')
        if user_id:
            agents = agents.filter(user_id=user_id)
            logger.debug(f"Filtering agents by user_id: {user_id}")

        serializer = AgentSerializer(agents, many=True)
        logger.info(f"Returning {agents.count()} agents")

        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"List agents error: {str(e)}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    responses={200: AgentSerializer()}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_agent_detail(request, agent_id):
    """Get detailed information about a specific agent"""
    try:
        logger.info(f"Agent detail request for agent_id={agent_id}")

        agent = Agent.objects.select_related('user').get(agent_id=agent_id)
        serializer = AgentSerializer(agent)

        logger.info(f"Returning agent details for {agent_id}")
        return Response(serializer.data, status=status.HTTP_200_OK)

    except Agent.DoesNotExist:
        logger.warning(f"Agent not found: agent_id={agent_id}")
        return Response(
            {'error': 'agent_not_found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Get agent detail error: {str(e)}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='agent_id',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Filter file uploads by agent ID'
        ),
        OpenApiParameter(
            name='status',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Filter by upload status (pending, completed, failed)'
        ),
    ],
    responses={200: FileUploadSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def list_file_uploads(request):
    """Get list of all file uploads with optional filtering"""
    try:
        logger.info(f"File uploads list request from IP: {request.META.get('REMOTE_ADDR')}")

        uploads = FileUpload.objects.select_related('agent', 'agent__user').all()

        # Filter by agent_id if provided
        agent_id = request.query_params.get('agent_id')
        if agent_id:
            uploads = uploads.filter(agent_id=agent_id)
            logger.debug(f"Filtering uploads by agent_id: {agent_id}")

        # Filter by status if provided
        status_filter = request.query_params.get('status')
        if status_filter:
            uploads = uploads.filter(status=status_filter)
            logger.debug(f"Filtering uploads by status: {status_filter}")

        serializer = FileUploadSerializer(uploads, many=True)
        logger.info(f"Returning {uploads.count()} file uploads")

        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"List file uploads error: {str(e)}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    responses={200: FileUploadSerializer()}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_file_upload_detail(request, upload_id):
    """Get detailed information about a specific file upload"""
    try:
        logger.info(f"File upload detail request for upload_id={upload_id}")

        upload = FileUpload.objects.select_related('agent', 'agent__user').get(upload_id=upload_id)
        serializer = FileUploadSerializer(upload)

        logger.info(f"Returning file upload details for {upload_id}")
        return Response(serializer.data, status=status.HTTP_200_OK)

    except FileUpload.DoesNotExist:
        logger.warning(f"File upload not found: upload_id={upload_id}")
        return Response(
            {'error': 'upload_not_found'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Get file upload detail error: {str(e)}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    parameters=[
        OpenApiParameter(
            name='agent_id',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Filter offline events by agent ID'
        ),
        OpenApiParameter(
            name='event_type',
            type=OpenApiTypes.STR,
            location=OpenApiParameter.QUERY,
            required=False,
            description='Filter by event type'
        ),
    ],
    responses={200: OfflineEventSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def list_offline_events(request):
    """Get list of all offline events with optional filtering"""
    try:
        logger.info(f"Offline events list request from IP: {request.META.get('REMOTE_ADDR')}")

        events = OfflineEvent.objects.select_related('agent', 'agent__user').all()

        # Filter by agent_id if provided
        agent_id = request.query_params.get('agent_id')
        if agent_id:
            events = events.filter(agent_id=agent_id)
            logger.debug(f"Filtering offline events by agent_id: {agent_id}")

        # Filter by event_type if provided
        event_type = request.query_params.get('event_type')
        if event_type:
            events = events.filter(event_type=event_type)
            logger.debug(f"Filtering offline events by event_type: {event_type}")

        serializer = OfflineEventSerializer(events, many=True)
        logger.info(f"Returning {events.count()} offline events")

        return Response(serializer.data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"List offline events error: {str(e)}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    responses={200: {
        'description': 'Agent statistics',
        'type': 'object',
        'properties': {
            'total_agents': {'type': 'integer'},
            'online_agents': {'type': 'integer'},
            'offline_agents': {'type': 'integer'},
            'suspicious_agents': {'type': 'integer'},
            'total_uploads': {'type': 'integer'},
            'pending_uploads': {'type': 'integer'},
            'completed_uploads': {'type': 'integer'},
            'failed_uploads': {'type': 'integer'},
        }
    }}
)
@api_view(['GET'])
@permission_classes([AllowAny])
def agent_statistics(request):
    """Get overall agent statistics"""
    try:
        logger.info(f"Agent statistics request from IP: {request.META.get('REMOTE_ADDR')}")

        stats = {
            'total_agents': Agent.objects.count(),
            'online_agents': Agent.objects.filter(status='online').count(),
            'offline_agents': Agent.objects.filter(status='offline').count(),
            'suspicious_agents': Agent.objects.filter(status='suspicious').count(),
            'total_uploads': FileUpload.objects.count(),
            'pending_uploads': FileUpload.objects.filter(status='pending').count(),
            'completed_uploads': FileUpload.objects.filter(status='completed').count(),
            'failed_uploads': FileUpload.objects.filter(status='failed').count(),
        }

        logger.info(f"Returning agent statistics: {stats}")
        return Response(stats, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Agent statistics error: {str(e)}", exc_info=True)
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )