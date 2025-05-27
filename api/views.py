# api/views.py
from datetime import timedelta
from django.conf import settings
from django.db.models import Sum
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import CreateAPIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from .serializers import RegisterSerializer, UserSerializer, PlanSerializer, DepositSerializer
from .models import Plan, Deposit, Earning, Investment, User

User = get_user_model()

def _secs(delta: timedelta) -> int:
    return int(delta.total_seconds())

@api_view(['GET'])
@permission_classes([AllowAny])
def sponsor_by_code(request, code):
    try:
        user = User.objects.get(referral_code=code)
        return Response({'name': user.name})
    except User.DoesNotExist:
        return Response({'detail': 'Not found'}, status=status.HTTP_404_NOT_FOUND)

class RegisterView(CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return serializer.to_response(serializer.save())

@method_decorator(csrf_exempt, name='dispatch')
class CookieTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        res = super().post(request, *args, **kwargs)
        if res.status_code == status.HTTP_200_OK:
            access, refresh = res.data['access'], res.data['refresh']
            for name, token, lifetime in (
                ('access_token', access, settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']),
                ('refresh_token', refresh, settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']),
            ):
                res.set_cookie(
                    name, token,
                    max_age=_secs(lifetime),
                    httponly=True,
                    secure=not settings.DEBUG,
                    samesite='None' if not settings.DEBUG else 'Lax',
                    path='/'
                )
            res.data = {'detail': 'Login successful'}
        return res

@method_decorator(csrf_exempt, name='dispatch')
class CookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh = request.COOKIES.get('refresh_token')
        if not refresh:
            return Response({'detail': 'Refresh token missing.'}, status=status.HTTP_401_UNAUTHORIZED)
        request.data['refresh'] = refresh
        res = super().post(request, *args, **kwargs)
        if res.status_code == status.HTTP_200_OK:
            token = res.data['access']
            res.set_cookie(
                'access_token', token,
                max_age=_secs(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']),
                httponly=True,
                secure=not settings.DEBUG,
                samesite='None' if not settings.DEBUG else 'Lax',
                path='/'
            )
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
        return Response(UserSerializer(request.user).data)

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

class MyNetworkView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Monta até 10 níveis de indicações
        niveis = []
        nivel_atual = [user]
        for i in range(10):
            # busca usuários cujo sponsor está no nível anterior
            prox = list(User.objects.filter(sponsor__in=nivel_atual))
            # soma total investido no nível
            total_investido = Investment.objects \
                .filter(user__in=prox, status='ACTIVE') \
                .aggregate(soma=Sum('amount'))['soma'] or 0
            indicados = []
            for u in prox:
                investido = Investment.objects \
                    .filter(user=u, status='ACTIVE') \
                    .aggregate(soma=Sum('amount'))['soma'] or 0
                comissoes = Earning.objects \
                    .filter(user=u, type='REFERRAL', status='CONFIRMED') \
                    .aggregate(soma=Sum('amount'))['soma'] or 0
                indicados.append({
                    'id': u.referral_code,
                    'nome': u.name,
                    'valorInvestido': float(investido),
                    'status': 'Ativo' if u.is_active else 'Inativo',
                    'dataEntrada': u.date_joined.isoformat(),
                    # assume-se que o plano ativo é o do último investimento
                    'planoAtivo': (
                        u.investments.order_by('-start_date').first().plan.name
                        if u.investments.exists() else None
                    ),
                    'comissoesGeradas': float(comissoes),
                })
            niveis.append({
                'id': i + 1,
                'nome': f'Nível {i+1}',
                'indicados': indicados,
                'totalInvestido': float(total_investido),
                # desbloqueio inicial apenas do nível 1 (cliente faz o resto via frontend com base no plano)
                'desbloqueado': True if i == 0 else False,
            })
            nivel_atual = prox

        # pega o último investimento do próprio user pra inferir o plano
        ultima = user.investments.order_by('-start_date').first()
        if ultima and ultima.plan and ultima.plan.name:
            # Plan.name é algo como "HOO SILVER", "HOO GOLD" ou "HOO BLACK"
            slug = ultima.plan.name.split()[-1].lower()   # "silver"|"gold"|"black"
        else:
            slug = "silver"  # todo mundo começa em silver

        return Response({
            'plano': slug,
            'referral_code': user.referral_code,
            'totalN1': niveis[0]['totalInvestido'],
            'niveis': niveis,
        })