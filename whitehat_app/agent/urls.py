from django.urls import path
from . import views

urlpatterns = [
    path('heartbeat', views.heartbeat, name='agent_heartbeat'),
    path('upload/request', views.request_upload, name='agent_upload_request'),
    path('upload/complete', views.complete_upload, name='agent_upload_complete'),
    path('offline-queue', views.offline_queue, name='agent_offline_queue'),
    path('commands', views.get_commands, name='agent_commands'),
    path('whitelist', views.get_whitelist, name='agent_whitelist'),
    path('agent-config', views.get_agent_config, name='agent_config'),
    path('usb-event', views.usb_event, name='agent_usb_event'),
]
