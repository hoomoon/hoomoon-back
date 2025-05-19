# api/views.py
from datetime import timedelta
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from rest_framework.generics import CreateAPIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny

from .serializers import (
    RegisterSerializer, UserSerializer,
    PlanSerializer, DepositSerializer
)
from .models import Plan, Deposit

User = get_user_model()

def _secs(delta: timedelta) -> int:
    return int(delta.total_seconds())

class RegisterView(CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return serializer.to_response(user)

@method_decorator(csrf_exempt, name='dispatch')
class CookieTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        res = super().post(request, *args, **kwargs)
        if res.status_code == status.HTTP_200_OK:
            access = res.data['access']
            refresh = res.data['refresh']
            res.set_cookie('access_token', access, max_age=_secs(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']), httponly=True, secure=True, samesite='Lax', path='/')
            res.set_cookie('refresh_token', refresh, max_age=_secs(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']), httponly=True, secure=True, samesite='Lax', path='/')
            res.data = {'detail': 'Login successful'}
        return res

@method_decorator(csrf_exempt, name='dispatch')
class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        token = request.COOKIES.get('refresh_token')
        if not token:
            return Response({'detail': 'Refresh token missing.'}, status=status.HTTP_401_UNAUTHORIZED)
        request.data['refresh'] = token
        res = super().post(request, *args, **kwargs)
        if res.status_code == status.HTTP_200_OK:
            access = res.data['access']
            res.set_cookie('access_token', access, max_age=_secs(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']), httponly=True, secure=True, samesite='Lax', path='/')
            res.data = {'detail': 'Token refreshed'}
        return res

@method_decorator(csrf_exempt, name='dispatch')
class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        resp = Response({'detail': 'Logged out'}, status=status.HTTP_200_OK)
        resp.delete_cookie('access_token', path='/', samesite='Lax')
        resp.delete_cookie('refresh_token', path='/', samesite='Lax')
        return resp

class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]

class DepositViewSet(viewsets.ModelViewSet):
    queryset = Deposit.objects.all()
    serializer_class = DepositSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)