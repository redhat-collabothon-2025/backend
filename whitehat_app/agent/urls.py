"""
Agent API URL Configuration

This module defines all API endpoints for agent communication and monitoring.

Endpoints:
- /heartbeat: Agent status check and registration (POST)
- /upload/request: Request presigned URL for file upload (POST)
- /upload/complete: Confirm file upload completion (POST)
- /offline-queue: Submit offline events queue (POST)
- /commands: Retrieve pending commands for agent (GET)
- /whitelist: Get USB device whitelist (GET)
- /agent-config: Get agent configuration settings (GET)
- /usb-event: Report USB insertion event and get file policies (POST)
- /tamper: Report tamper detection alert (POST)
- /insider-alert: Report insider threat alert (POST)
"""

from django.urls import path
import logging

from . import views

# Initialize logger for URL routing
logger = logging.getLogger(__name__)

urlpatterns = [
    # Agent lifecycle management
    path('heartbeat', views.heartbeat, name='agent_heartbeat'),  # Agent check-in and status update

    # File upload management
    path('upload/request', views.request_upload, name='agent_upload_request'),  # Request upload URL
    path('upload/complete', views.complete_upload, name='agent_upload_complete'),  # Confirm upload

    # Event and command management
    path('offline-queue', views.offline_queue, name='agent_offline_queue'),  # Submit offline events
    path('commands', views.get_commands, name='agent_commands'),  # Get pending commands

    # Configuration and policies
    path('whitelist', views.get_whitelist, name='agent_whitelist'),  # USB whitelist
    path('agent-config', views.get_agent_config, name='agent_config'),  # Agent config

    # Security events
    path('usb-event', views.usb_event, name='agent_usb_event'),  # USB insertion event
    path('tamper', views.tamper_alert, name='agent_tamper'),  # Tamper detection
    path('insider-alert', views.insider_alert, name='agent_insider_alert'),  # Insider threat

    # ============================================================================
    # API Endpoints for Agent Management (GET requests for monitoring/dashboard)
    # ============================================================================

    # Agent management endpoints
    path('list', views.list_agents, name='agent_list'),  # Get all agents
    path('<str:agent_id>/detail', views.get_agent_detail, name='agent_detail'),  # Get agent details
    path('statistics', views.agent_statistics, name='agent_statistics'),  # Get agent statistics

    # File upload monitoring endpoints
    path('uploads/list', views.list_file_uploads, name='agent_uploads_list'),  # Get all uploads
    path('uploads/<str:upload_id>/detail', views.get_file_upload_detail, name='agent_upload_detail'),  # Get upload details

    # Offline events monitoring endpoints
    path('offline-events/list', views.list_offline_events, name='agent_offline_events_list'),  # Get all offline events
]
