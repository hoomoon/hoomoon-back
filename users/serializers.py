"""
Serializers para o app de usuários
"""
from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from core.utils import BusinessRulesValidator, FeatureToggle
from .models import User, UserProfile, UserActivity


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer para registro de novos usuários
    """
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    sponsor_code = serializers.CharField(max_length=20, required=False, write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'name', 'email', 'phone', 'country', 'cpf',
            'password', 'password_confirm', 'sponsor_code'
        ]
        extra_kwargs = {
            'username': {'required': True},
            'name': {'required': True},
            'email': {'required': True},
        }
    
    def validate(self, attrs):
        """Validação customizada"""
        # Verificar se as senhas coincidem
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("As senhas não coincidem")
        
        # Verificar código do patrocinador se fornecido
        sponsor_code = attrs.get('sponsor_code')
        if sponsor_code:
            try:
                sponsor = User.objects.get(referral_code=sponsor_code)
                attrs['sponsor'] = sponsor
            except User.DoesNotExist:
                raise serializers.ValidationError("Código de indicação inválido")
        
        # Remover campos que não são do modelo
        attrs.pop('password_confirm', None)
        attrs.pop('sponsor_code', None)
        
        return attrs
    
    def create(self, validated_data):
        """Criar usuário com senha criptografada"""
        password = validated_data.pop('password')
        user = User.objects.create_user(password=password, **validated_data)
        
        # Criar perfil automaticamente
        UserProfile.objects.create(user=user)
        
        return user


class UserLoginSerializer(serializers.Serializer):
    """
    Serializer para login de usuários
    """
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """Validar credenciais"""
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if not user:
                raise serializers.ValidationError("Credenciais inválidas")
            if not user.is_active:
                raise serializers.ValidationError("Conta desativada")
                
            attrs['user'] = user
            return attrs
        
        raise serializers.ValidationError("Username e password são obrigatórios")


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para perfil estendido do usuário
    """
    class Meta:
        model = UserProfile
        exclude = ['user', 'created_at', 'updated_at']


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer principal do usuário
    """
    profile = UserProfileSerializer(read_only=True)
    referral_stats = serializers.SerializerMethodField()
    investment_summary = serializers.SerializerMethodField()
    is_kyc_approved = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'name', 'email', 'phone', 'country', 'cpf',
            'referral_code', 'balance', 'kyc_status', 'is_kyc_approved',
            'is_active', 'date_joined',
            'profile', 'referral_stats', 'investment_summary'  
        ]
        read_only_fields = [
            'id', 'username', 'referral_code', 'balance', 'date_joined'
        ]
    
    def get_referral_stats(self, obj):
        """Retorna estatísticas de indicação se a feature estiver habilitada"""
        if FeatureToggle.is_enabled('REFERRAL_SYSTEM'):
            return obj.get_referral_stats()
        return None
    
    def get_investment_summary(self, obj):
        """Retorna resumo de investimentos"""
        try:
            return obj.get_investment_summary()
        except Exception:
            # Se o app investments não estiver disponível ainda
            return None


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer para atualização de dados do usuário
    """
    profile = UserProfileSerializer(required=False)
    
    class Meta:
        model = User
        fields = [
            'name', 'email', 'phone', 'country', 'cpf', 'profile'
        ]
    
    def update(self, instance, validated_data):
        """Atualizar usuário e perfil"""
        profile_data = validated_data.pop('profile', None)
        
        # Atualizar usuário
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Atualizar perfil se fornecido
        if profile_data:
            profile, created = UserProfile.objects.get_or_create(user=instance)
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()
        
        return instance


class UserActivitySerializer(serializers.ModelSerializer):
    """
    Serializer para atividades do usuário
    """
    class Meta:
        model = UserActivity
        fields = '__all__'
        read_only_fields = ['user', 'created_at']


# O serializer UserNotificationSerializer foi migrado para o app notifications
# como NotificationSerializer, que é mais completo e modular


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer para mudança de senha
    """
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        """Validar mudança de senha"""
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("As novas senhas não coincidem")
        return attrs
    
    def validate_old_password(self, value):
        """Validar senha atual"""
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Senha atual incorreta")
        return value


class KYCDocumentSerializer(serializers.Serializer):
    """
    Serializer para upload de documentos KYC
    """
    document_type = serializers.ChoiceField(
        choices=[
            ('ID', 'Documento de Identidade'),
            ('PASSPORT', 'Passaporte'),
            ('DRIVER_LICENSE', 'Carteira de Motorista'),
            ('PROOF_ADDRESS', 'Comprovante de Endereço'),
            ('SELFIE', 'Selfie com Documento')
        ]
    )
    document_url = serializers.URLField()
    document_number = serializers.CharField(max_length=50, required=False)
    
    def validate(self, attrs):
        """Validar documento KYC"""
        if not FeatureToggle.is_enabled('KYC_VERIFICATION'):
            raise serializers.ValidationError("Verificação KYC não está habilitada")
        return attrs


class ReferralInfoSerializer(serializers.Serializer):
    """
    Serializer para informações de indicação
    """
    referral_code = serializers.CharField(read_only=True)
    referral_link = serializers.SerializerMethodField()
    referral_stats = serializers.SerializerMethodField()
    
    def get_referral_link(self, obj):
        """Gerar link de indicação"""
        request = self.context.get('request')
        if request:
            return f"{request.build_absolute_uri('/')}{obj.referral_code}"
        return f"https://example.com/{obj.referral_code}"
    
    def get_referral_stats(self, obj):
        """Estatísticas de indicação"""
        return obj.get_referral_stats() 