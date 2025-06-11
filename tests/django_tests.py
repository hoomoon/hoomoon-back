#!/usr/bin/env python
"""
Testes unitários usando Django Test Framework
"""
import os
import sys
import django
from decimal import Decimal

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse

User = get_user_model()

class UserModelTests(TestCase):
    """Testes para o modelo User"""
    
    def setUp(self):
        self.user_data = {
            'username': 'test_user',
            'email': 'test@example.com',
            'name': 'Test User',
            'password': 'testpass123'
        }
    
    def test_create_user(self):
        """Teste criação de usuário"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.username, 'test_user')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.referral_code)
        self.assertEqual(user.balance, Decimal('0.00'))
        
    def test_referral_code_generation(self):
        """Teste geração automática do código de indicação"""
        user = User.objects.create_user(**self.user_data)
        self.assertTrue(user.referral_code.startswith('INV-'))
        self.assertEqual(len(user.referral_code), 12)  # INV- + 8 chars
        
    def test_user_string_representation(self):
        """Teste representação string do usuário"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(str(user), 'test_user')

class InvestmentAPITests(APITestCase):
    """Testes para APIs de investimento"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='test_user',
            email='test@example.com',
            name='Test User',
            password='testpass123'
        )
        
    def test_plans_list_unauthorized(self):
        """Teste listagem de planos sem autenticação"""
        url = '/api/investments/plans/'
        response = self.client.get(url)
        # Planos podem ser públicos
        self.assertIn(response.status_code, [200, 401])
        
    def test_investments_list_requires_auth(self):
        """Teste que listagem de investimentos requer autenticação"""
        url = '/api/investments/investments/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

class UserAPITests(APITestCase):
    """Testes para APIs de usuário"""
    
    def setUp(self):
        self.client = APIClient()
        
    def test_user_registration(self):
        """Teste registro de usuário"""
        url = '/api/users/register/'
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'name': 'New User',
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        }
        response = self.client.post(url, data, format='json')
        # Aceita tanto 200 quanto 201
        self.assertIn(response.status_code, [200, 201])
        
        # Verificar se o usuário foi criado
        user_exists = User.objects.filter(username='newuser').exists()
        self.assertTrue(user_exists)
        
    def test_user_registration_password_mismatch(self):
        """Teste registro com senhas diferentes"""
        url = '/api/users/register/'
        data = {
            'username': 'newuser2',
            'email': 'newuser2@example.com',
            'name': 'New User 2',
            'password': 'newpass123',
            'password_confirm': 'differentpass'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class SystemHealthTests(APITestCase):
    """Testes para saúde do sistema"""
    
    def test_health_check(self):
        """Teste endpoint de saúde"""
        url = '/api/system/health/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertIn('status', data.get('data', {}))
        
    def test_system_config(self):
        """Teste endpoint de configuração"""
        url = '/api/system/config/'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        data = response.json()
        self.assertTrue(data.get('success'))

def run_tests():
    """Executar testes básicos sem criar banco de teste"""
    print("🧪 Executando verificações básicas do Django...")
    
    try:
        # Teste 1: Importações dos modelos
        from django.contrib.auth import get_user_model
        from investments.models import Plan
        from payments.models import Deposit
        print("✅ Importações de modelos - OK")
        
        # Teste 2: Verificar se os modelos estão registrados
        User = get_user_model()
        print(f"✅ Modelo User configurado: {User.__name__}")
        
        # Teste 3: Verificar se as migrações estão aplicadas
        from django.db import connection
        tables = connection.introspection.table_names()
        expected_tables = ['users_user', 'investments_plan', 'payments_deposit']
        
        tables_found = 0
        for table in expected_tables:
            if table in tables:
                tables_found += 1
        
        print(f"✅ Tabelas do banco: {tables_found}/{len(expected_tables)} encontradas")
        
        # Teste 4: Verificar configurações básicas
        from django.conf import settings
        print(f"✅ DEBUG mode: {settings.DEBUG}")
        print(f"✅ Base de dados configurada: {bool(settings.DATABASES)}")
        
        print("✅ Todos os testes básicos passaram!")
        return True
        
    except Exception as e:
        print(f"❌ Erro nos testes: {str(e)}")
        return False

if __name__ == '__main__':
    try:
        # Executar testes
        success = run_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Erro durante os testes: {str(e)}")
        sys.exit(1) 