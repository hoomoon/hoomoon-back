#!/usr/bin/env python
"""
Testes Simplificados para o Sistema de Autenticação do HooMoon
Foca em testes unitários e de modelo que funcionam sem dependências complexas
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import TestCase, override_settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from decimal import Decimal

User = get_user_model()


class UserModelAuthenticationTests(TestCase):
    """Testes básicos para o modelo de usuário relacionados à autenticação"""
    
    def setUp(self):
        self.valid_user_data = {
            'username': 'teste_usuario',
            'email': 'teste@hoomoon.com',
            'name': 'Usuário de Teste',
            'password': 'SenhaSegura123!'
        }
    
    def test_create_user_basic(self):
        """Teste criação básica de usuário"""
        user = User.objects.create_user(**self.valid_user_data)
        
        # Verificar campos básicos
        self.assertEqual(user.username, 'teste_usuario')
        self.assertEqual(user.email, 'teste@hoomoon.com')
        self.assertEqual(user.name, 'Usuário de Teste')
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        
        # Verificar que referral_code foi gerado
        self.assertIsNotNone(user.referral_code)
        self.assertTrue(user.referral_code.startswith('INV-'))
        
        # Verificar balance padrão
        self.assertEqual(user.balance, Decimal('0.00'))
    
    def test_user_password_authentication(self):
        """Teste autenticação por senha"""
        user = User.objects.create_user(**self.valid_user_data)
        
        # Senha deve ser hasheada
        self.assertNotEqual(user.password, 'SenhaSegura123!')
        
        # Mas deve funcionar para autenticação
        self.assertTrue(user.check_password('SenhaSegura123!'))
        self.assertFalse(user.check_password('senhaerrada'))
    
    def test_user_email_unique(self):
        """Teste que email deve ser único"""
        # Criar primeiro usuário
        User.objects.create_user(**self.valid_user_data)
        
        # Tentar criar segundo com mesmo email
        duplicate_data = self.valid_user_data.copy()
        duplicate_data['username'] = 'outro_usuario'
        
        with self.assertRaises(IntegrityError):
            User.objects.create_user(**duplicate_data)
    
    def test_user_username_unique(self):
        """Teste que username deve ser único"""
        # Criar primeiro usuário
        User.objects.create_user(**self.valid_user_data)
        
        # Tentar criar segundo com mesmo username
        duplicate_data = self.valid_user_data.copy()
        duplicate_data['email'] = 'outro@hoomoon.com'
        
        with self.assertRaises(IntegrityError):
            User.objects.create_user(**duplicate_data)
    
    def test_user_string_representation(self):
        """Teste representação string do usuário"""
        user = User.objects.create_user(**self.valid_user_data)
        self.assertEqual(str(user), 'teste_usuario')
    
    def test_user_referral_code_generation(self):
        """Teste geração automática do código de indicação"""
        user = User.objects.create_user(**self.valid_user_data)
        
        # Código deve ter formato correto
        self.assertTrue(user.referral_code.startswith('INV-'))
        self.assertEqual(len(user.referral_code), 12)  # INV- + 8 chars
        
        # Códigos devem ser únicos
        user2_data = self.valid_user_data.copy()
        user2_data['username'] = 'outro_usuario'
        user2_data['email'] = 'outro@hoomoon.com'
        user2 = User.objects.create_user(**user2_data)
        
        self.assertNotEqual(user.referral_code, user2.referral_code)
    
    def test_user_is_active_by_default(self):
        """Teste que usuário é ativo por padrão"""
        user = User.objects.create_user(**self.valid_user_data)
        self.assertTrue(user.is_active)
    
    def test_user_balance_default_zero(self):
        """Teste que saldo padrão é zero"""
        user = User.objects.create_user(**self.valid_user_data)
        self.assertEqual(user.balance, Decimal('0.00'))
    
    def test_user_can_be_deactivated(self):
        """Teste que usuário pode ser desativado"""
        user = User.objects.create_user(**self.valid_user_data)
        user.is_active = False
        user.save()
        
        # Recarregar do banco
        user.refresh_from_db()
        self.assertFalse(user.is_active)


class UserQueryTests(TestCase):
    """Testes para consultas e filtragem de usuários"""
    
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='user1',
            email='user1@hoomoon.com',
            name='User One',
            password='password123'
        )
        self.user2 = User.objects.create_user(
            username='user2',
            email='user2@hoomoon.com', 
            name='User Two',
            password='password123',
            is_active=False
        )
    
    def test_filter_active_users(self):
        """Teste filtro de usuários ativos"""
        active_users = User.objects.filter(is_active=True)
        self.assertIn(self.user1, active_users)
        self.assertNotIn(self.user2, active_users)
    
    def test_filter_by_email(self):
        """Teste busca por email"""
        user = User.objects.filter(email='user1@hoomoon.com').first()
        self.assertEqual(user, self.user1)
    
    def test_filter_by_username(self):
        """Teste busca por username"""
        user = User.objects.filter(username='user2').first()
        self.assertEqual(user, self.user2)
    
    def test_check_username_availability(self):
        """Teste verificação de disponibilidade de username"""
        # Username existente
        self.assertTrue(User.objects.filter(username='user1').exists())
        
        # Username disponível  
        self.assertFalse(User.objects.filter(username='novo_usuario').exists())
    
    def test_check_email_availability(self):
        """Teste verificação de disponibilidade de email"""
        # Email existente
        self.assertTrue(User.objects.filter(email='user1@hoomoon.com').exists())
        
        # Email disponível
        self.assertFalse(User.objects.filter(email='novo@hoomoon.com').exists())


class PasswordValidationTests(TestCase):
    """Testes para validação de senhas"""
    
    def test_password_hashing(self):
        """Teste que senhas são hasheadas corretamente"""
        user = User.objects.create_user(
            username='test_user',
            email='test@hoomoon.com',
            password='MinhaPassword123!'
        )
        
        # Senha não deve estar em texto plano
        self.assertNotEqual(user.password, 'MinhaPassword123!')
        
        # Deve começar com algum indicador de hash
        self.assertTrue(user.password.startswith('pbkdf2_sha256$') or 
                       user.password.startswith('argon2$') or
                       user.password.startswith('bcrypt$'))
    
    def test_password_verification(self):
        """Teste verificação de senhas"""
        user = User.objects.create_user(
            username='test_user',
            email='test@hoomoon.com',
            password='MinhaPassword123!'
        )
        
        # Senha correta
        self.assertTrue(user.check_password('MinhaPassword123!'))
        
        # Senhas incorretas
        self.assertFalse(user.check_password('senhaerrada'))
        self.assertFalse(user.check_password('MinhaPassword123'))  # Sem !
        self.assertFalse(user.check_password('minhapassword123!'))  # Case diferente
        self.assertFalse(user.check_password(''))
    
    def test_password_change(self):
        """Teste mudança de senha"""
        user = User.objects.create_user(
            username='test_user',
            email='test@hoomoon.com',
            password='SenhaAntiga123!'
        )
        
        # Verificar senha antiga
        self.assertTrue(user.check_password('SenhaAntiga123!'))
        
        # Alterar senha
        user.set_password('NovaSenha456!')
        user.save()
        
        # Verificar que senha antiga não funciona mais
        self.assertFalse(user.check_password('SenhaAntiga123!'))
        
        # Verificar que nova senha funciona
        self.assertTrue(user.check_password('NovaSenha456!'))


class UserFieldValidationTests(TestCase):
    """Testes para validação de campos do usuário"""
    
    def test_username_cannot_be_empty(self):
        """Teste que username não pode ser vazio"""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                username='',
                email='test@hoomoon.com',
                password='Password123!'
            )
    
    def test_email_cannot_be_empty(self):
        """Teste que email não pode ser vazio"""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                username='test_user',
                email='',
                password='Password123!'
            )
    
    def test_password_cannot_be_empty(self):
        """Teste que senha não pode ser vazia"""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                username='test_user',
                email='test@hoomoon.com',
                password=''
            )


class ReferralSystemTests(TestCase):
    """Testes para sistema de indicação"""
    
    def test_referral_code_uniqueness(self):
        """Teste que códigos de indicação são únicos"""
        users = []
        for i in range(5):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@hoomoon.com',
                password='Password123!'
            )
            users.append(user)
        
        # Todos os códigos devem ser diferentes
        codes = [user.referral_code for user in users]
        self.assertEqual(len(codes), len(set(codes)))  # Set remove duplicatas
    
    def test_find_user_by_referral_code(self):
        """Teste busca de usuário por código de indicação"""
        user = User.objects.create_user(
            username='sponsor',
            email='sponsor@hoomoon.com',
            password='Password123!'
        )
        
        # Buscar por código
        found_user = User.objects.filter(referral_code=user.referral_code).first()
        self.assertEqual(found_user, user)


def run_simple_authentication_tests():
    """Executar todos os testes simplificados de autenticação"""
    print("🔐 Iniciando Testes Simplificados do Sistema de Autenticação...")
    
    try:
        import unittest
        
        # Classes de teste
        test_classes = [
            UserModelAuthenticationTests,
            UserQueryTests,
            PasswordValidationTests,
            UserFieldValidationTests,
            ReferralSystemTests
        ]
        
        total_tests = 0
        total_passed = 0
        
        for test_class in test_classes:
            print(f"\n📋 Executando {test_class.__name__}...")
            
            suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
            runner = unittest.TextTestRunner(verbosity=1, stream=open(os.devnull, 'w'))
            result = runner.run(suite)
            
            tests_run = result.testsRun
            tests_passed = tests_run - len(result.failures) - len(result.errors)
            
            total_tests += tests_run
            total_passed += tests_passed
            
            print(f"✅ {tests_passed}/{tests_run} testes passaram")
            
            if result.failures:
                print(f"❌ {len(result.failures)} falhas")
                for test, traceback in result.failures:
                    print(f"   FALHA: {test}")
                    
            if result.errors:
                print(f"🚨 {len(result.errors)} erros")
                for test, traceback in result.errors:
                    print(f"   ERRO: {test}")
        
        print(f"\n🎯 RESUMO FINAL: {total_passed}/{total_tests} testes passaram")
        
        if total_passed == total_tests:
            print("🎉 Todos os testes simplificados de autenticação passaram!")
            print("✅ Sistema de autenticação básico está funcionando corretamente")
            return True
        else:
            print(f"⚠️ {total_tests-total_passed} teste(s) falharam")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao executar testes: {str(e)}")
        return False


if __name__ == '__main__':
    success = run_simple_authentication_tests()
    sys.exit(0 if success else 1) 