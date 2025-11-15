from io import BytesIO
from django.http import StreamingHttpResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from whitehat_app.minio_service import minio_service


@csrf_exempt
@require_http_methods(["GET", "PUT", "POST", "HEAD"])
def minio_proxy(request, bucket, object_name):
    minio_service._ensure_client()

    if not minio_service.client:
        return HttpResponse('Minio unavailable', status=503)

    if request.method == 'PUT' or request.method == 'POST':
        try:
            file_data = request.body
            file_obj = BytesIO(file_data)

            minio_service.client.put_object(
                bucket,
                object_name,
                file_obj,
                length=len(file_data),
                content_type=request.content_type or 'application/octet-stream'
            )

            return HttpResponse(status=200)

        except Exception as e:
            return HttpResponse(str(e), status=500)

    elif request.method == 'GET':
        try:
            response = minio_service.client.get_object(bucket, object_name)

            def file_iterator():
                for chunk in response.stream(chunk_size=8192):
                    yield chunk

            http_response = StreamingHttpResponse(
                file_iterator(),
                content_type='application/octet-stream'
            )

            filename = object_name.split('/')[-1]
            http_response['Content-Disposition'] = f'attachment; filename="{filename}"'

            return http_response

        except Exception as e:
            return HttpResponse(str(e), status=404)

    elif request.method == 'HEAD':
        try:
            minio_service.client.stat_object(bucket, object_name)
            return HttpResponse(status=200)
        except:
            return HttpResponse(status=404)

    return HttpResponse('Method not allowed', status=405)
