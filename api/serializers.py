# api/serializers.py

from rest_framework import serializers
from .models import User, Plan, Deposit, Investment, Earning, OnchainTransaction

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model  = User
        fields = ['id', 'username', 'email', 'phone', 'country', 'referral_code']

class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model  = Plan
        fields = [
            'id', 'name', 'tag', 'description',
            'daily_percent', 'duration_days', 'cap_percent'
        ]

class DepositSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model  = Deposit
        fields = [
            'id', 'user', 'method', 'amount',
            'status', 'transaction_hash', 'created_at'
        ]
        read_only_fields = ['status', 'created_at']

class InvestmentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    plan = PlanSerializer(read_only=True)
    plan_id = serializers.PrimaryKeyRelatedField(
        queryset=Plan.objects.all(), source='plan', write_only=True
    )

    class Meta:
        model  = Investment
        fields = [
            'id', 'user', 'plan', 'plan_id',
            'code', 'amount', 'start_date',
            'next_release', 'expiration_date',
            'progress_percent', 'status'
        ]
        read_only_fields = ['code', 'start_date', 'next_release', 'expiration_date', 'progress_percent', 'status']

class EarningSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model  = Earning
        fields = [
            'id', 'user', 'type', 'origin',
            'description', 'amount', 'status', 'created_at'
        ]
        read_only_fields = ['created_at']

class OnchainTransactionSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model  = OnchainTransaction
        fields = [
            'id', 'user', 'tx_type', 'status',
            'tx_hash', 'value', 'fee', 'timestamp'
        ]
        read_only_fields = ['timestamp']
