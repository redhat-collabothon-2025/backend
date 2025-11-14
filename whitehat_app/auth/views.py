from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from whitehat_app.models import User
from whitehat_app.serializers import UserSerializer, LoginSerializer, RefreshTokenSerializer


@extend_schema(
    request=LoginSerializer,
    responses={
        200: {
            'type': 'object',
            'properties': {
                'access': {'type': 'string'},
                'refresh': {'type': 'string'},
                'user': {'type': 'object'}
            }
        },
        400: {'description': 'Invalid credentials'}
    },
    examples=[
        OpenApiExample(
            'Login Example',
            value={
                'email': 'user@example.com',
                'password': 'securepassword123'
            },
            request_only=True
        )
    ]
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    email = serializer.validated_data['email']
    password = serializer.validated_data['password']

    user = User.objects.filter(email=email).first()

    if user is None or not user.check_password(password):
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_400_BAD_REQUEST
        )

    refresh = RefreshToken.for_user(user)

    return Response({
        'access': str(refresh.access_token),
        'refresh': str(refresh),
        'user': UserSerializer(user).data
    })


@extend_schema(
    request=RefreshTokenSerializer,
    responses={
        205: {'description': 'Token blacklisted successfully'},
        400: {'description': 'Invalid token'}
    },
    examples=[
        OpenApiExample(
            'Logout Example',
            value={'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGc...'},
            request_only=True
        )
    ]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    serializer = RefreshTokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        refresh_token = serializer.validated_data['refresh']
        token = RefreshToken(refresh_token)
        token.blacklist()
        return Response(status=status.HTTP_205_RESET_CONTENT)
    except TokenError:
        return Response(
            {'error': 'Invalid token'},
            status=status.HTTP_400_BAD_REQUEST
        )


@extend_schema(
    request=RefreshTokenSerializer,
    responses={
        200: {
            'type': 'object',
            'properties': {
                'access': {'type': 'string'}
            }
        },
        400: {'description': 'Invalid token'}
    },
    examples=[
        OpenApiExample(
            'Refresh Token Example',
            value={'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGc...'},
            request_only=True
        )
    ]
)
@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token(request):
    serializer = RefreshTokenSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    try:
        refresh = RefreshToken(serializer.validated_data['refresh'])
        return Response({
            'access': str(refresh.access_token)
        })
    except TokenError:
        return Response(
            {'error': 'Invalid token'},
            status=status.HTTP_400_BAD_REQUEST
        )


@extend_schema(
    responses={
        200: UserSerializer
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)
