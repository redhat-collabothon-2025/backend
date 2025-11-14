from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from ..models import User
from ..serializers import UserSerializer


class UserListView(APIView):
    @extend_schema(
        responses={200: UserSerializer(many=True)}
    )
    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
