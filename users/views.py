"""
Views para o app de usuários
"""
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from core.authentication import CookieTokenManager
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from core.utils import APIResponseHandler, FeatureToggle, log_api_activity
from core.permissions import IsOwnerOrReadOnly, IsKYCVerified
from .models import UserProfile, UserActivity
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, UserSerializer,
    UserUpdateSerializer, UserProfileSerializer, UserActivitySerializer,
    ChangePasswordSerializer, KYCDocumentSerializer,
    ReferralInfoSerializer
)

User = get_user_model()


class UserRegistrationView(APIView):
    """
    Endpoint para registro de novos usuários
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Registrar novo usuário"""
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Log da atividade
            log_api_activity(user, "user_registered", {
                "ip_address": request.META.get('REMOTE_ADDR'),
                "user_agent": request.META.get('HTTP_USER_AGENT', '')
            })
            
            # Criar resposta de sucesso
            response = APIResponseHandler.success(
                data={
                    'user': UserSerializer(user).data,
                    'message': 'Usuário registrado com sucesso'
                },
                message="Usuário registrado com sucesso",
                status_code=status.HTTP_201_CREATED
            )
            
            # Configurar cookies seguros de autenticação
            response = CookieTokenManager.set_auth_cookies(response, user, request)
            
            return response
        
        return APIResponseHandler.error(
            message="Erro no registro",
            details=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )


class UserLoginView(APIView):
    """
    Endpoint para login de usuários
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Fazer login do usuário"""
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Log da atividade
            log_api_activity(user, "user_login", {
                "ip_address": request.META.get('REMOTE_ADDR'),
                "user_agent": request.META.get('HTTP_USER_AGENT', '')
            })
            
            # Criar resposta de sucesso
            response = APIResponseHandler.success(
                data={
                    'user': UserSerializer(user).data,
                    'message': 'Login realizado com sucesso'
                },
                message="Login realizado com sucesso"
            )
            
            # Configurar cookies seguros de autenticação
            response = CookieTokenManager.set_auth_cookies(response, user, request)
            
            return response
        
        return APIResponseHandler.error(
            message="Credenciais inválidas",
            details=serializer.errors,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class UserLogoutView(APIView):
    """
    Endpoint para logout seguro de usuários
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Fazer logout do usuário"""
        user = request.user
        
        # Log da atividade
        log_api_activity(user, "user_logout", {
            "ip_address": request.META.get('REMOTE_ADDR'),
            "user_agent": request.META.get('HTTP_USER_AGENT', '')
        })
        
        # Criar resposta de sucesso
        response = APIResponseHandler.success(
            data={'message': 'Logout realizado com sucesso'},
            message="Logout realizado com sucesso"
        )
        
        # Limpar cookies de autenticação
        response = CookieTokenManager.clear_auth_cookies(response, request)
        
        return response


class RefreshTokenView(APIView):
    """
    Endpoint para renovar access token usando refresh token do cookie
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        """Renovar access token"""
        success, data = CookieTokenManager.refresh_access_token(request)
        
        if success:
            # Criar resposta com novo token
            response = APIResponseHandler.success(
                data={'message': 'Token renovado com sucesso'},
                message="Token renovado com sucesso"
            )
            
            # Configurar novo cookie de access token
            response.set_cookie(
                'access_token',
                data['access_token'],
                max_age=data['token_lifetime'],
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Strict' if not settings.DEBUG else 'Lax',
                path='/'
            )
            
            return response
        else:
            return APIResponseHandler.error(
                message="Falha ao renovar token",
                details=data,
                status_code=status.HTTP_401_UNAUTHORIZED
            )


class UserLogoutView(APIView):
    """
    Endpoint para logout de usuários
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Fazer logout do usuário"""
        try:
            refresh_token = request.data.get("refresh_token")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            # Log da atividade
            log_api_activity(request.user, "user_logout")
            
            return APIResponseHandler.success(
                message="Logout realizado com sucesso"
            )
        except Exception as e:
            return APIResponseHandler.error(
                message="Erro no logout",
                details=str(e)
            )


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gerenciamento completo de usuários
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    
    def get_queryset(self):
        """Filtrar usuários baseado no usuário logado"""
        if self.request.user.is_staff:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)
    
    def get_serializer_class(self):
        """Escolher serializer baseado na ação"""
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Retorna informações do usuário logado"""
        serializer = self.get_serializer(request.user)
        return APIResponseHandler.success(
            data=serializer.data,
            message="Perfil do usuário obtido com sucesso"
        )
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """Alterar senha do usuário"""
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            # Log da atividade
            log_api_activity(user, "password_changed")
            
            return APIResponseHandler.success(
                message="Senha alterada com sucesso"
            )
        
        return APIResponseHandler.error(
            message="Erro na alteração da senha",
            details=serializer.errors
        )
    
    @action(detail=False, methods=['get', 'post'])
    def referral_info(self, request):
        """Obter/atualizar informações de indicação"""
        # Verificar se a feature está habilitada
        if not FeatureToggle.is_enabled('REFERRAL_SYSTEM'):
            return APIResponseHandler.error(
                message="Sistema de indicação não está habilitado",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        if request.method == 'GET':
            serializer = ReferralInfoSerializer(
                request.user,
                context={'request': request}
            )
            return APIResponseHandler.success(
                data=serializer.data,
                message="Informações de indicação obtidas com sucesso"
            )
        
        # POST: Para operações futuras de indicação
        return APIResponseHandler.success(
            message="Funcionalidade em desenvolvimento"
        )
    
    @action(detail=False, methods=['get'])
    def referrals(self, request):
        """Listar usuários indicados"""
        if not FeatureToggle.is_enabled('REFERRAL_SYSTEM'):
            return APIResponseHandler.error(
                message="Sistema de indicação não está habilitado",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        referrals = request.user.referrals.all().order_by('-date_joined')
        serializer = UserSerializer(referrals, many=True)
        
        return APIResponseHandler.success(
            data=serializer.data,
            message="Lista de indicados obtida com sucesso"
        )
    
    @action(detail=False, methods=['post'])
    def upload_kyc_document(self, request):
        """Upload de documento para verificação KYC"""
        # Verificar se a feature está habilitada
        if not FeatureToggle.is_enabled('KYC_VERIFICATION'):
            return APIResponseHandler.error(
                message="Verificação KYC não está habilitada",
                status_code=status.HTTP_404_NOT_FOUND
            )
        
        serializer = KYCDocumentSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            document_data = serializer.validated_data
            
            # Adicionar documento aos dados KYC do usuário
            if not user.kyc_documents:
                user.kyc_documents = {}
            
            user.kyc_documents[document_data['document_type']] = {
                'url': document_data['document_url'],
                'number': document_data.get('document_number', ''),
                'uploaded_at': timezone.now().isoformat()
            }
            
            # Atualizar status para análise se todos os documentos necessários foram enviados
            required_docs = ['ID', 'PROOF_ADDRESS', 'SELFIE']
            if all(doc in user.kyc_documents for doc in required_docs):
                user.kyc_status = 'REVIEW'
            
            user.save()
            
            # Log da atividade
            log_api_activity(user, "kyc_document_uploaded", {
                "document_type": document_data['document_type']
            })
            
            return APIResponseHandler.success(
                message="Documento enviado com sucesso"
            )
        
        return APIResponseHandler.error(
            message="Erro no envio do documento",
            details=serializer.errors
        )


class UserActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para visualização de atividades do usuário
    """
    serializer_class = UserActivitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Filtrar atividades do usuário logado"""
        return UserActivity.objects.filter(user=self.request.user)


# O ViewSet UserNotificationViewSet foi migrado para o app notifications
# como NotificationViewSet, que é mais completo e modular


class CheckUsernameView(APIView):
    """
    Verificar se username está disponível
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, username):
        """Verificar disponibilidade do username"""
        exists = User.objects.filter(username=username).exists()
        
        return APIResponseHandler.success(
            data={
                'username': username,
                'available': not exists
            },
            message="Verificação de username realizada"
        )


class CheckEmailView(APIView):
    """
    Verificar se email está disponível
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, email):
        """Verificar disponibilidade do email"""
        exists = User.objects.filter(email=email).exists()
        
        return APIResponseHandler.success(
            data={
                'email': email,
                'available': not exists
            },
            message="Verificação de email realizada"
        )


class SponsorByCodeView(APIView):
    """
    Buscar patrocinador pelo código de indicação
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, code):
        """Buscar informações do patrocinador"""
        try:
            sponsor = User.objects.get(referral_code=code)
            return APIResponseHandler.success(
                data={
                    'name': sponsor.name,
                    'username': sponsor.username
                },
                message="Patrocinador encontrado"
            )
        except User.DoesNotExist:
            return APIResponseHandler.error(
                message="Código de indicação não encontrado",
                status_code=status.HTTP_404_NOT_FOUND
            )
