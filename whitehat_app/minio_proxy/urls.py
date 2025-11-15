from django.urls import path, re_path
from . import views

urlpatterns = [
    re_path(r'^(?P<bucket>[^/]+)/(?P<object_name>.+)$', views.upload_file, name='minio_upload'),
    re_path(r'^(?P<bucket>[^/]+)/(?P<object_name>.+)$', views.download_file, name='minio_download'),
    re_path(r'^(?P<bucket>[^/]+)/(?P<object_name>.+)$', views.check_file, name='minio_check'),
]
