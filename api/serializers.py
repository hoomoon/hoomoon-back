# api/serializers.py
from datetime import timedelta
from django.conf import settings
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.validators import UniqueValidator

from .models import User, Plan, Deposit, Investment, Earning, OnchainTransaction


def _secs(delta: timedelta) -> int:
    return int(delta.total_seconds())


class RegisterSerializer(serializers.ModelSerializer):
    name = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    sponsor_code = serializers.CharField(write_only=True, required=False)
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
        fields = ('name', 'email', 'password', 'phone', 'country', 'cpf', 'sponsor_code')

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('Email já cadastrado.')
        return value

    def create(self, validated_data):
        name = validated_data.pop('name')
        sponsor = validated_data.pop('sponsor_code', None)
        password = validated_data.pop('password')
        user = User(name=name, **validated_data)
        if sponsor:
            try:
                user.sponsor = User.objects.get(referral_code=sponsor)
            except User.DoesNotExist:
                raise serializers.ValidationError({'sponsor_code': 'Código inválido.'})
        user.set_password(password)
        user.save()
        return user

    def to_response(self, user):
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
        fields = ('id', 'name', 'email', 'phone', 'country', 'referral_code', 'balance')


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ('id', 'name', 'tag', 'description', 'daily_percent', 'duration_days', 'cap_percent')


class DepositSerializer(serializers.ModelSerializer):
    class Meta:
        model = Deposit
        fields = (
            'id', 'user', 'method', 'amount', 'status', 
            'transaction_hash', 'created_at', 
            'coinpayments_txn_id', 'payment_address', 'qrcode_url', 'status_url'
        )
        read_only_fields = (
            'user', 'status', 'created_at',
            'coinpayments_txn_id', 'payment_address', 'qrcode_url', 'status_url'
        )


class InvestmentSerializer(serializers.ModelSerializer):
    plan_id = serializers.PrimaryKeyRelatedField(queryset=Plan.objects.all(), source='plan', write_only=True)

    class Meta:
        model = Investment
        fields = ('id', 'user', 'plan', 'plan_id', 'code', 'amount', 'start_date',
                  'next_release', 'expiration_date', 'progress_percent', 'status')
        read_only_fields = ('user', 'plan', 'code', 'start_date', 'next_release',
                            'expiration_date', 'progress_percent', 'status')


class EarningSerializer(serializers.ModelSerializer):
    class Meta:
        model = Earning
        fields = ('id', 'user', 'type', 'origin', 'description', 'amount', 'status', 'created_at')
        read_only_fields = ('user', 'created_at')


class OnchainTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnchainTransaction
        fields = ('id', 'user', 'tx_type', 'status', 'tx_hash', 'value', 'fee', 'timestamp')
        read_only_fields = ('user', 'timestamp')
