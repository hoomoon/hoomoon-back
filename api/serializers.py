# api/serializers.py
from datetime import timedelta
from decimal import Decimal
from django.conf import settings
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.validators import UniqueValidator

from .models import User, Plan, Deposit, Investment, Earning, OnchainTransaction



class RegisterSerializer(serializers.ModelSerializer):
    username = serializers.CharField(write_only=True, required=True,
                                   validators=[UniqueValidator(queryset=User.objects.all(), message="Este nome de usuário já está em uso.")])
    name = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    sponsor_code = serializers.CharField(write_only=True, required=False)
    email = serializers.EmailField(
        required=False, allow_null=True, allow_blank=True,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="Este email já está em uso.",
                lookup='iexact'
            )
        ]
    )
    cpf = serializers.CharField(
        allow_blank=True,
        required=False,
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="Este CPF já está em uso."
            )
        ]
    )

    class Meta:
        model = User
        fields = ('username', 'name', 'email', 'password', 'phone', 'country', 'cpf', 'sponsor_code')

    def create(self, validated_data):
        username = validated_data.pop('username')
        name = validated_data.pop('name')
        email = validated_data.pop('email', None)
        sponsor_code = validated_data.pop('sponsor_code', None)
        password = validated_data.pop('password')
        user = User.objects.create_user(
            username=username,
            name=name,
            email=email,
            password=password,
            **validated_data
        )
        if sponsor_code:
            try:
                user.sponsor = User.objects.get(referral_code=sponsor_code)
                user.save(update_fields=['sponsor'])
            except User.DoesNotExist:
                raise serializers.ValidationError({'sponsor_code': 'Código inválido.'})
        return user

    def to_response(self, user):
        from rest_framework.response import Response
        from rest_framework import status
        from rest_framework_simplejwt.tokens import RefreshToken
        from django.conf import settings
        from datetime import timedelta

        def _secs(delta: timedelta) -> int:
            return int(delta.total_seconds())

        refresh = RefreshToken.for_user(user)
        access = str(refresh.access_token)
        resp = Response({'detail': 'Cadastro e login bem-sucedidos'}, status=status.HTTP_201_CREATED)
        common = {
            'httponly': True,
            'secure': True,
            'samesite': 'None',
            'domain': settings.SESSION_COOKIE_DOMAIN,
            'path': '/',
        }
        resp.set_cookie(
            'access_token', access,
            max_age=_secs(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']),
            **common
        )
        resp.set_cookie(
            'refresh_token', str(refresh),
            max_age=_secs(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']),
            **common
        )
        return resp


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'name', 'email', 'phone', 'country', 'referral_code', 'balance')


class PlanSerializer(serializers.ModelSerializer):
    title = serializers.CharField(source='name', read_only=True)
    imageSrc = serializers.CharField(source='image_src', read_only=True)
    minValue = serializers.DecimalField(source='min_value', max_digits=10, decimal_places=2, read_only=True)
    
    features = serializers.SerializerMethodField()

    class Meta:
        model = Plan
        fields = ('id', 'title', 'imageSrc', 'color', 'minValue', 'features', 'tag')

    def get_features(self, obj):
        feature_list = []

        if obj.id == Plan.HOO_FREE:
            feature_list.extend([
                "Plano gratuito para novos usuários",
                "Acesso ao sistema e recompensas de indicação",
                "Não exige investimento inicial"
            ])
        else:
            if obj.min_value > 0:
                min_value_display = f"${int(obj.min_value)}" if obj.min_value % 1 == 0 else f"${obj.min_value:.2f}"
                feature_list.append(f"Locação mínima: {min_value_display}")
            
            feature_list.append(f"Duração: {obj.duration_days} dias")
            
            total_return_display = f"{int(obj.cap_percent)}%" if obj.cap_percent % 1 == 0 else f"{obj.cap_percent:.2f}%"
            feature_list.append(f"Retorno total: {total_return_display}")
            
            daily_reward_display = f"{int(obj.daily_percent)}%" if obj.daily_percent % 1 == 0 else f"{obj.daily_percent:.2f}%"
            feature_list.append(f"Recompensa diária: até {daily_reward_display}")
            
            feature_list.append("Saques diários")
        if obj.description:
            feature_list.append(obj.description)
            
        return feature_list

class DepositSerializer(serializers.ModelSerializer):
    plan_id = serializers.PrimaryKeyRelatedField(
        queryset=Plan.objects.all(), source='plan', write_only=True, 
        allow_null=True, required=False
    )
    plan_name = serializers.CharField(source='plan.name', read_only=True, allow_null=True)


    class Meta:
        model = Deposit
        fields = (
            'id', 'user', 'plan_id', 'plan_name', 'method', 'amount', 'status', 
            'transaction_hash', 'created_at', 
            'coinpayments_txn_id', 'payment_address', 'qrcode_url', 'status_url',
            'pix_qr_code_payload', 'pix_qr_code_image_url', 'pix_key', 'pix_key_type', 'pix_beneficiary_name'
        )
        read_only_fields = (
            'user', 'status', 'created_at', 'plan_name',
            'coinpayments_txn_id', 'payment_address', 'qrcode_url', 'status_url',
            'pix_qr_code_payload', 'pix_qr_code_image_url', 'pix_key', 'pix_key_type', 'pix_beneficiary_name'
        )


class InvestmentSerializer(serializers.ModelSerializer):
    plan_id = serializers.PrimaryKeyRelatedField(queryset=Plan.objects.all(), source='plan', write_only=True)
    plan = PlanSerializer(read_only=True) 
    deposit_code = serializers.CharField(source='deposit_source.id', read_only=True, allow_null=True)

    class Meta:
        model = Investment
        fields = (
            'id', 'user', 'plan', 'plan_id', 'deposit_code', 'code', 'amount', 'start_date',
            'next_yield_date', 'expiration_date', 'progress_percent', 'total_yielded', 'status'
        )
        read_only_fields = (
            'user', 'plan', 'deposit_code', 'code', 'start_date', 'next_yield_date',
            'expiration_date', 'progress_percent', 'total_yielded', 'status'
        )


class EarningSerializer(serializers.ModelSerializer):
    investment_code = serializers.CharField(source='investment_source.code', read_only=True, allow_null=True)

    class Meta:
        model = Earning
        fields = ('id', 'user', 'investment_code', 'type', 'origin', 'description', 'amount', 'status', 'created_at', 'effective_date')
        read_only_fields = ('user', 'created_at', 'effective_date', 'investment_code')



class OnchainTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnchainTransaction
        fields = ('id', 'user', 'tx_type', 'status', 'tx_hash', 'value', 'fee', 'timestamp', 'notes')
        read_only_fields = ('user', 'timestamp')

class InitiateDepositPayloadSerializer(serializers.Serializer):
    planId = serializers.PrimaryKeyRelatedField(
        queryset=Plan.objects.all(),
        source='plan',
        help_text=("ID do plano selecionado (e.g., PANDORA, TITAN).")
    )
    amount = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2,
        help_text=("Valor do depósito/investimento.")
    )
    paymentMethod = serializers.ChoiceField(
        choices=Deposit.METHOD_CHOICES,
        help_text=("Método de pagamento selecionado ('USDT_BEP20' ou 'PIX').")
    )

    def validate_planId(self, plan):
        if plan.id == Plan.HOO_FREE:
            raise serializers.ValidationError("O plano gratuito não requer depósito. Selecione um plano pago.")
        return plan

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("O valor do depósito deve ser positivo.")
        return value

    def validate(self, data):
        plan = data.get('plan')
        amount = data.get('amount')

        if plan and amount is not None:
            if amount < plan.min_value:
                raise serializers.ValidationError({
                    "amount": f"O valor do depósito (R${amount}) é inferior ao mínimo exigido para o plano {plan.name} (R${plan.min_value})."
                })
        return data
