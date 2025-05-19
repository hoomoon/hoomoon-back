# api/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta
from django.conf import settings
from .models import Plan, Deposit, Investment, Earning, OnchainTransaction

User = get_user_model()

def _secs(delta: timedelta) -> int:
    return int(delta.total_seconds())

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    sponsor_code = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = (
            'username', 'email', 'password',
            'phone', 'country', 'cpf', 'sponsor_code'
        )

    def validate(self, attrs):
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError('Username já existe.')
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError('Email já cadastrado.')
        return attrs

    def create(self, validated_data):
        sponsor_code = validated_data.pop('sponsor_code', None)
        password = validated_data.pop('password')
        user = User(**validated_data)
        if sponsor_code:
            try:
                user.sponsor = User.objects.get(referral_code=sponsor_code)
            except User.DoesNotExist:
                raise serializers.ValidationError({'sponsor_code': 'Código inválido.'})
        user.set_password(password)
        user.save()
        return user

    def to_response(self, user):
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        resp = serializers.Response({'detail': 'Cadastro e login bem-sucedidos'}, status=201)
        resp.set_cookie('access_token', str(access), max_age=_secs(settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME']), httponly=True, secure=True, samesite='Lax', path='/')
        resp.set_cookie('refresh_token', str(refresh), max_age=_secs(settings.SIMPLE_JWT['REFRESH_TOKEN_LIFETIME']), httponly=True, secure=True, samesite='Lax', path='/')
        return resp

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'phone', 'country', 'referral_code']

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ['id', 'name', 'tag', 'description', 'daily_percent', 'duration_days', 'cap_percent']

class DepositSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Deposit
        fields = ['id', 'user', 'method', 'amount', 'status', 'transaction_hash', 'created_at']
        read_only_fields = ['status', 'created_at']

class InvestmentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    plan = PlanSerializer(read_only=True)
    plan_id = serializers.PrimaryKeyRelatedField(queryset=Plan.objects.all(), source='plan', write_only=True)

    class Meta:
        model = Investment
        fields = ['id', 'user', 'plan', 'plan_id', 'code', 'amount', 'start_date', 'next_release', 'expiration_date', 'progress_percent', 'status']
        read_only_fields = ['code', 'start_date', 'next_release', 'expiration_date', 'progress_percent', 'status']

class EarningSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Earning
        fields = ['id', 'user', 'type', 'origin', 'description', 'amount', 'status', 'created_at']
        read_only_fields = ['created_at']

class OnchainTransactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = OnchainTransaction
        fields = ['id', 'user', 'tx_type', 'status', 'tx_hash', 'value', 'fee', 'timestamp']
        read_only_fields = ['timestamp']