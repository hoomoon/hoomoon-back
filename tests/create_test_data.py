#!/usr/bin/env python
"""
Script para criar dados de teste completos para o sistema HooMoon
"""
import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from investments.models import Plan, Investment
from payments.models import Deposit
from financial.models import Earning
from notifications.models import NotificationTemplate, NotificationPreference

User = get_user_model()

def create_test_users():
    """Criar usuários de teste"""
    print("👤 Criando usuários de teste...")
    
    users_data = [
        {
            'username': 'admin_test',
            'email': 'admin@admin.com',
            'name': 'Admin Test',
            'is_staff': True,
            'is_superuser': True
        },
        {
            'username': 'user_test1', 
            'email': 'user1@hoomoon.com',
            'name': 'User Test 1',
            'balance': Decimal('1000.00')
        },
        {
            'username': 'user_test2',
            'email': 'user2@hoomoon.com', 
            'name': 'User Test 2',
            'balance': Decimal('500.00')
        }
    ]
    
    created_users = []
    for user_data in users_data:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={
                'email': user_data['email'],
                'name': user_data['name'],
                'balance': user_data.get('balance', Decimal('0.00')),
                'is_staff': user_data.get('is_staff', False),
                'is_superuser': user_data.get('is_superuser', False),
                'kyc_status': 'APPROVED'
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
            print(f"✅ Usuário criado: {user.username}")
        else:
            print(f"ℹ️ Usuário já existe: {user.username}")
            
        created_users.append(user)
    
    return created_users

def create_investment_plans():
    """Criar planos de investimento"""
    print("\n💰 Criando planos de investimento...")
    
    plans_data = [
        {
            'id': 'STARTER',
            'name': 'Hoo Starter', 
            'min_value': Decimal('10.00'),
            'daily_percent': Decimal('0.5'),
            'duration_days': 30,
            'cap_percent': Decimal('15.0'),
            'tag': 'Iniciante',
            'color': '#10b981'
        },
        {
            'id': 'PREMIUM',
            'name': 'Hoo Premium',
            'min_value': Decimal('100.00'), 
            'daily_percent': Decimal('1.0'),
            'duration_days': 60,
            'cap_percent': Decimal('60.0'),
            'tag': 'Popular',
            'color': '#3b82f6'
        },
        {
            'id': 'VIP',
            'name': 'Hoo VIP',
            'min_value': Decimal('1000.00'),
            'daily_percent': Decimal('1.5'), 
            'duration_days': 90,
            'cap_percent': Decimal('135.0'),
            'tag': 'Elite',
            'color': '#8b5cf6'
        }
    ]
    
    created_plans = []
    for plan_data in plans_data:
        plan, created = Plan.objects.get_or_create(
            id=plan_data['id'],
            defaults=plan_data
        )
        
        if created:
            print(f"✅ Plano criado: {plan.name}")
        else:
            print(f"ℹ️ Plano já existe: {plan.name}")
            
        created_plans.append(plan)
    
    return created_plans

def create_sample_investments(users, plans):
    """Criar investimentos de exemplo"""
    print("\n📈 Criando investimentos de exemplo...")
    
    if len(users) < 2 or len(plans) < 2:
        print("⚠️ Usuários ou planos insuficientes para criar investimentos")
        return []
    
    investments_data = [
        {
            'user': users[1],  # user_test1
            'plan': plans[0],  # STARTER
            'amount': Decimal('50.00')
        },
        {
            'user': users[1],  # user_test1
            'plan': plans[1],  # PREMIUM
            'amount': Decimal('200.00')
        },
        {
            'user': users[2],  # user_test2
            'plan': plans[0],  # STARTER
            'amount': Decimal('25.00')
        }
    ]
    
    created_investments = []
    for inv_data in investments_data:
        # Verificar se o investimento já existe
        existing = Investment.objects.filter(
            user=inv_data['user'],
            plan=inv_data['plan'],
            amount=inv_data['amount']
        ).first()
        
        if not existing:
            investment = Investment.objects.create(**inv_data)
            print(f"✅ Investimento criado: {investment.user.username} -> {investment.plan.name}")
            created_investments.append(investment)
        else:
            print(f"ℹ️ Investimento já existe: {existing.user.username} -> {existing.plan.name}")
            created_investments.append(existing)
    
    return created_investments

def create_sample_deposits(users):
    """Criar depósitos de exemplo"""
    print("\n💳 Criando depósitos de exemplo...")
    
    if len(users) < 2:
        print("⚠️ Usuários insuficientes para criar depósitos")
        return []
    
    deposits_data = [
        {
            'user': users[1],
            'amount': Decimal('100.00'),
            'method': 'PIX',
            'status': 'CONFIRMED'
        },
        {
            'user': users[2],
            'amount': Decimal('50.00'), 
            'method': 'USDT_BEP20',
            'status': 'PENDING'
        }
    ]
    
    created_deposits = []
    for dep_data in deposits_data:
        deposit = Deposit.objects.create(**dep_data)
        print(f"✅ Depósito criado: {deposit.user.username} - {deposit.amount}")
        created_deposits.append(deposit)
    
    return created_deposits

def create_sample_earnings(users):
    """Criar ganhos de exemplo"""
    print("\n💎 Criando ganhos de exemplo...")
    
    if len(users) < 2:
        print("⚠️ Usuários insuficientes para criar ganhos")
        return []
    
    earnings_data = [
        {
            'user': users[1],
            'amount': Decimal('5.00'),
            'type': 'DAILY_YIELD',
            'description': 'Rendimento diário - Plano Starter'
        },
        {
            'user': users[1],
            'amount': Decimal('10.00'),
            'type': 'REFERRAL',
            'description': 'Bônus de indicação'
        },
        {
            'user': users[2],
            'amount': Decimal('2.50'),
            'type': 'DAILY_YIELD', 
            'description': 'Rendimento diário - Plano Starter'
        }
    ]
    
    created_earnings = []
    for earn_data in earnings_data:
        earning = Earning.objects.create(**earn_data)
        print(f"✅ Ganho criado: {earning.user.username} - {earning.amount}")
        created_earnings.append(earning)
    
    return created_earnings

def create_notification_templates():
    """Criar templates de notificação"""
    print("\n🔔 Criando templates de notificação...")
    
    templates_data = [
        {
            'name': 'Bem-vindo',
            'notification_type': 'WELCOME',
            'channel': 'EMAIL',
            'subject': 'Bem-vindo ao HooMoon!',
            'content': 'Olá {name}, bem-vindo ao HooMoon! Sua conta foi criada com sucesso.',
            'is_default': True
        },
        {
            'name': 'Depósito Confirmado',
            'notification_type': 'DEPOSIT',
            'channel': 'IN_APP',
            'subject': 'Depósito Confirmado',
            'content': 'Seu depósito de {amount} foi confirmado com sucesso!',
            'is_default': True
        },
        {
            'name': 'Rendimento Diário',
            'notification_type': 'EARNING',
            'channel': 'IN_APP',
            'subject': 'Novo Rendimento',
            'content': 'Você recebeu {amount} de rendimento em seus investimentos.',
            'is_default': True
        }
    ]
    
    created_templates = []
    for template_data in templates_data:
        template, created = NotificationTemplate.objects.get_or_create(
            name=template_data['name'],
            notification_type=template_data['notification_type'],
            channel=template_data['channel'],
            defaults=template_data
        )
        
        if created:
            print(f"✅ Template criado: {template.name}")
        else:
            print(f"ℹ️ Template já existe: {template.name}")
            
        created_templates.append(template)
    
    return created_templates

def create_notification_preferences(users):
    """Criar preferências de notificação para usuários"""
    print("\n⚙️ Criando preferências de notificação...")
    
    created_prefs = []
    for user in users:
        pref, created = NotificationPreference.objects.get_or_create(
            user=user,
            defaults={
                'email_enabled': True,
                'sms_enabled': False,
                'push_enabled': True,
                'in_app_enabled': True
            }
        )
        
        if created:
            print(f"✅ Preferências criadas para: {user.username}")
        else:
            print(f"ℹ️ Preferências já existem para: {user.username}")
            
        created_prefs.append(pref)
    
    return created_prefs

def main():
    """Função principal"""
    print("🚀 Iniciando criação de dados de teste para HooMoon...")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Criar dados na ordem correta
        users = create_test_users()
        plans = create_investment_plans()
        investments = create_sample_investments(users, plans)
        deposits = create_sample_deposits(users)
        earnings = create_sample_earnings(users)
        templates = create_notification_templates()
        preferences = create_notification_preferences(users)
        
        print("\n" + "="*50)
        print("📊 RESUMO DOS DADOS CRIADOS")
        print("="*50)
        print(f"👤 Usuários: {len(users)}")
        print(f"💰 Planos: {len(plans)}")
        print(f"📈 Investimentos: {len(investments)}")
        print(f"💳 Depósitos: {len(deposits)}")
        print(f"💎 Ganhos: {len(earnings)}")
        print(f"🔔 Templates: {len(templates)}")
        print(f"⚙️ Preferências: {len(preferences)}")
        print("="*50)
        print("✅ Dados de teste criados com sucesso!")
        
        # Informações úteis
        print("\n💡 INFORMAÇÕES ÚTEIS:")
        print("🔑 Credenciais de teste:")
        print("   Admin: admin_test / testpass123")
        print("   User1: user_test1 / testpass123")
        print("   User2: user_test2 / testpass123")
        print("\n🌐 Endpoints para testar:")
        print("   Admin: http://localhost:8000/admin/")
        print("   API: http://localhost:8000/api/docs/")
        
    except Exception as e:
        print(f"❌ Erro ao criar dados de teste: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Erro durante a execução: {str(e)}")
        sys.exit(1)
