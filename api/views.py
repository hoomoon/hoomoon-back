# api/views.py
import logging
import re
from django.core.mail import mail_admins
from django.urls import reverse
from datetime import timedelta
from django.conf import settings
from django.db.models import Sum
from django.db import transaction
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.generics import CreateAPIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated, AllowAny
from urllib.parse import urlencode
from .serializers import RegisterSerializer, UserSerializer, PlanSerializer, DepositSerializer
from .models import Plan, Deposit, Earning, Investment, User
from .coinpayments_service import CoinPaymentsService

logger = logging.getLogger(__name__)

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
        resp.delete_cookie('access_token', path='/', samesite='None' if not settings.DEBUG else 'Lax')
        resp.delete_cookie('refresh_token', path='/', samesite='None' if not settings.DEBUG else 'Lax')
        return resp
    
class UserProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Plan.objects.all().order_by('min_value')
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]

class DepositViewSet(viewsets.ModelViewSet):
    queryset = Deposit.objects.all()
    serializer_class = DepositSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if serializer.validated_data.get('method') != 'USDT':
            self.perform_create(serializer)
            headers = self.get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        logger.info(f"Iniciando processo de depósito USDT para usuário {request.user.email} com valor {serializer.validated_data.get('amount')}")
        deposit = serializer.save(user=self.request.user, status='FAILED')
        
        try:
            ipn_url = request.build_absolute_uri(reverse('coinpayments-ipn'))
            
            service = CoinPaymentsService()
            transaction = service.create_transaction(
                amount=float(deposit.amount),
                user_email=request.user.email,
                ipn_url=ipn_url,
                deposit_id=deposit.id
            )

            if not transaction or transaction.get('error') != 'ok':
                error_message = transaction.get('error') if transaction else "Erro desconhecido na chamada do serviço CoinPayments"
                logger.warning(f"Falha na API CoinPayments ao criar depósito para {request.user.email} (ID: {deposit.id}): {error_message}. Dados da transação: {transaction}")
                return Response(
                    {"detail": f"Falha na comunicação com o gateway: {error_message}"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            result = transaction['result']
            deposit.coinpayments_txn_id = result['txn_id']
            deposit.payment_address = result['address']
            deposit.qrcode_url = result['qrcode_url']
            deposit.status_url = result['status_url']
            deposit.status = 'PENDING'
            deposit.save()

            logger.info(f"Depósito {deposit.id} (CP ID: {result['txn_id']}) com CoinPayments criado com sucesso para {request.user.email}.")
            updated_serializer = self.get_serializer(deposit)
            headers = self.get_success_headers(updated_serializer.data)
            return Response(updated_serializer.data, status=status.HTTP_201_CREATED, headers=headers)

        except Exception as e:
            logger.error(f"ERRO INESPERADO ao criar depósito para {request.user.email} (ID provisório: {deposit.id}): {e}", exc_info=True)
            return Response(
                {"detail": "Ocorreu um erro interno ao processar o depósito. Nossa equipe foi notificada."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@method_decorator(csrf_exempt, name='dispatch')
class CoinPaymentsIPNView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        logger.info(f"Recebida notificação IPN da CoinPayments. Headers: {request.headers}. Body (primeiros 500 chars): {str(request.data)[:500]}")
        
        raw_post_data = urlencode(request.data)
        
        try:
            ipn_secret = settings.COINPAYMENTS_IPN_SECRET
            merchant_id = settings.COINPAYMENTS_MERCHANT_ID
            
            hmac_from_request = request.headers.get('Hmac') 
            if not hmac_from_request:
                logger.warning("IPN recebido sem header HMAC. Rejeitando.")
                return HttpResponse("HMAC header missing", status=400)
                
            import hmac
            import hashlib
            
            hmac_signature = hmac.new(ipn_secret.encode('utf-8'), raw_post_data.encode('utf-8'), hashlib.sha512).hexdigest()

            if not hmac.compare_digest(hmac_signature, hmac_from_request):
                logger.warning(f"HMAC inválido para IPN. Recebido: {hmac_from_request}, Calculado: {hmac_signature}. Body: {raw_post_data}")
                return HttpResponse("Invalid HMAC", status=403)
                
            if request.data.get('merchant') != merchant_id:
                logger.warning(f"Merchant ID inválido para IPN. Esperado: {merchant_id}, Recebido: {request.data.get('merchant')}")
                return HttpResponse("Invalid Merchant ID", status=400)

            deposit_id_str = request.data.get('custom')
            if not deposit_id_str or not deposit_id_str.isdigit():
                logger.error(f"IPN recebido com 'custom' (deposit_id) inválido ou ausente: {deposit_id_str}")
                return HttpResponse("Invalid or missing custom field (deposit_id)", status=400)
            
            deposit_id = int(deposit_id_str)
            txn_id_coinpayments = request.data.get('txn_id')
            
            logger.info(f"Processando IPN para deposit_id: {deposit_id}, txn_id CoinPayments: {txn_id_coinpayments}")
            
            deposit = Deposit.objects.get(id=deposit_id)
            
            payment_status_str = request.data.get('status')
            if not payment_status_str or not payment_status_str.lstrip('-').isdigit():
                logger.error(f"IPN para deposit_id {deposit_id} recebido com 'status' inválido ou ausente: {payment_status_str}")
                return HttpResponse("Invalid or missing status field", status=400)

            payment_status = int(payment_status_str)
            status_text = request.data.get('status_text', '')
            logger.info(f"Status do pagamento IPN para deposit_id {deposit_id}: {payment_status} ({status_text})")

            if deposit.status in ['CONFIRMED', 'FAILED']:
                logger.info(f"Depósito {deposit_id} já está no estado final '{deposit.status}'. Ignorando IPN.")
                return HttpResponse("IPN already processed for this deposit or deposit is failed", status=200)

            previous_status = deposit.status
            new_status = previous_status

            if payment_status >= 100 or payment_status == 2:
                new_status = 'CONFIRMED'
                deposit.transaction_hash = txn_id_coinpayments
            elif payment_status == 1:
                new_status = 'PAID'
            elif payment_status < 0:
                new_status = 'FAILED'

            if previous_status != new_status:
                if new_status == 'CONFIRMED':
                    with transaction.atomic():
                        d_to_update = Deposit.objects.select_for_update().get(pk=deposit.id)
                        
                        if d_to_update.status == 'CONFIRMED':
                            logger.warning(f"Depósito {deposit_id} já estava confirmado dentro da transação. Abortando.")
                            return HttpResponse("IPN already processed.", status=200)

                        user_to_update = User.objects.select_for_update().get(pk=d_to_update.user.id)
                        
                        user_to_update.balance += d_to_update.amount
                        user_to_update.save()
                        
                        d_to_update.status = 'CONFIRMED'
                        d_to_update.transaction_hash = txn_id_coinpayments 
                        d_to_update.save()
                        
                        logger.info(f"SALDO CREDITADO! Usuário: {user_to_update.email}, Valor: {d_to_update.amount}, Novo Saldo: {user_to_update.balance}")
                else:
                    deposit.status = new_status
                    deposit.save()
                    logger.info(f"Depósito {deposit_id} atualizado de '{previous_status}' para '{new_status}'.")

        except Deposit.DoesNotExist:
            logger.error(f"IPN recebido para deposit_id {request.data.get('custom')} não encontrado no banco de dados.", exc_info=True)
            return HttpResponse("Deposit not found", status=404)
        except ValueError as ve:
            logger.error(f"Erro de valor ao processar IPN (custom ou status inválido). Custom: {request.data.get('custom')}, Status: {request.data.get('status')}. Erro: {ve}", exc_info=True)
            return HttpResponse("Invalid data in IPN (custom or status field).", status=400)
        except Exception as e:
            logger.error(f"Erro CRÍTICO ao processar IPN para deposit_id {request.data.get('custom')}: {e}", exc_info=True)
            
            try:
                subject = f"ALERTA CRÍTICO: Erro no Processamento de IPN - Depósito {request.data.get('custom')}"
                message_body = (
                    f"Ocorreu um erro crítico e inesperado ao processar uma notificação IPN da CoinPayments.\n\n"
                    f"É crucial investigar este problema para garantir a consistência dos dados.\n\n"
                    f"Deposit ID (custom): {request.data.get('custom')}\n"
                    f"CoinPayments TXN ID: {request.data.get('txn_id', 'N/A')}\n"
                    f"Status Recebido: {request.data.get('status', 'N/A')} ({request.data.get('status_text', 'N/A')})\n"
                    f"Erro: {str(e)}\n\n"
                    f"Traceback e mais detalhes podem ser encontrados nos logs do servidor (logger: api.views).\n\n"
                    f"Dados completos do IPN (raw POST data):\n{raw_post_data}"
                )
                mail_admins(subject, message_body, fail_silently=False)
                logger.info(f"Email de alerta de erro crítico para IPN (depósito {request.data.get('custom')}) enviado aos administradores.")
            except Exception as mail_exc:
                logger.error(f"FALHA AO ENVIAR EMAIL de alerta de erro crítico para admins (IPN depósito {request.data.get('custom')}): {mail_exc}", exc_info=True)

            return HttpResponse("Internal Server Error while processing IPN. Admins notified.", status=500)
            
        logger.info(f"IPN para deposit_id {request.data.get('custom')} processado com sucesso.")
        return HttpResponse("IPN Processed", status=200)

@extend_schema(summary="Retorna a rede de referência do usuário")
class MyNetworkView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        niveis = []
        nivel_atual = [user]
        for i in range(10):
            prox = list(User.objects.filter(sponsor__in=nivel_atual))
            total_investido = Investment.objects.filter(user__in=prox, status='ACTIVE').aggregate(soma=Sum('amount'))['soma'] or 0
            indicados = []
            for u in prox:
                investido = Investment.objects.filter(user=u, status='ACTIVE').aggregate(soma=Sum('amount'))['soma'] or 0
                comissoes = Earning.objects.filter(user=u, type='REFERRAL', status='CONFIRMED').aggregate(soma=Sum('amount'))['soma'] or 0
                indicados.append({
                    'id': u.referral_code,
                    'nome': u.name,
                    'valorInvestido': float(investido),
                    'status': 'Ativo' if u.is_active else 'Inativo',
                    'dataEntrada': u.date_joined.isoformat(),
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
                'desbloqueado': True if i == 0 else False,
            })
            nivel_atual = prox

        ultima = user.investments.order_by('-start_date').first()
        if ultima and ultima.plan and ultima.plan.name:
            slug = ultima.plan.name.split()[-1].lower()
        else:
            slug = "silver"

        return Response({
            'plano': slug,
            'referral_code': user.referral_code,
            'totalN1': niveis[0]['totalInvestido'] if niveis else 0,
            'niveis': niveis,
        })
    
@extend_schema(
    summary="Verificar Existência de Nome de Usuário",
    request={'application/json': {'type': 'object', 'properties': {'username': {'type': 'string'}}}},
    responses={
        200: {'description': 'Indica se o nome de usuário existe.', 'examples': {'application/json': {'exists': False}}},
        400: {'description': 'Nome de usuário não fornecido ou inválido (ex: muito curto, caracteres não permitidos).'}
    },
    tags=['Verificações de Usuário']
)
@api_view(['POST'])
@permission_classes([AllowAny])
def check_username_exists(request):
    username_to_check = request.data.get('username', '').strip()

    if not username_to_check:
        return Response({'error': 'Nome de usuário é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)

    if len(username_to_check) < 3:
        return Response({'error': 'Nome de usuário deve ter pelo menos 3 caracteres.'}, status=status.HTTP_400_BAD_REQUEST)
    
    if not re.match(r"^[a-z0-9_.]+$", username_to_check):
        return Response({'error': "Nome de usuário pode conter apenas letras minúsculas, números, '_' e '.'."}, status=status.HTTP_400_BAD_REQUEST)

    exists = User.objects.filter(username__iexact=username_to_check).exists()
    
    return Response({'exists': exists})
    
@api_view(['POST'])
@permission_classes([AllowAny])
def check_email_exists(request):
    email = request.data.get('email', '').lower().strip()
    if not email:
        return Response({'error': 'E-mail é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
    exists = User.objects.filter(email=email).exists()
    return Response({'exists': exists})

@api_view(['POST'])
@permission_classes([AllowAny])
def check_cpf_exists(request):
    cpf = request.data.get('cpf', '').strip()
    if not cpf:
        return Response({'error': 'CPF é obrigatório'}, status=status.HTTP_400_BAD_REQUEST)
    cpf = ''.join(filter(str.isdigit, cpf))
    if len(cpf) != 11:
        return Response({'error': 'CPF deve ter 11 dígitos'}, status=status.HTTP_400_BAD_REQUEST)
    exists = User.objects.filter(cpf=cpf).exists()
    return Response({'exists': exists})