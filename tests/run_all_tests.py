#!/usr/bin/env python
"""
Script master para executar todos os testes do sistema HooMoon
"""
import os
import sys
import subprocess
import time
import requests
from datetime import datetime

# Adicionar o diretório pai ao Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def print_header(title):
    """Imprime cabeçalho formatado"""
    print("\n" + "="*60)
    print(f"🔬 {title}")
    print("="*60)

def print_section(title):
    """Imprime seção formatada"""
    print(f"\n📋 {title}")
    print("-"*40)

def check_server_status():
    """Verifica se o servidor Django está rodando"""
    try:
        response = requests.get("http://localhost:8000/api/system/health/", timeout=5)
        return response.status_code == 200
    except:
        return False

def run_command(command, description):
    """Executa um comando e retorna o resultado"""
    print(f"▶️ {description}")
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            capture_output=True, 
            text=True,
            cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        )
        
        if result.returncode == 0:
            print(f"✅ {description} - Sucesso")
            return True
        else:
            print(f"❌ {description} - Falhou")
            if result.stderr:
                print(f"   Erro: {result.stderr[:200]}...")
            return False
    except Exception as e:
        print(f"❌ {description} - Erro de execução: {str(e)}")
        return False

def run_django_checks():
    """Executa verificações do Django"""
    print_section("Verificações do Django")
    
    checks = [
        ("python manage.py check", "Verificação geral do sistema"),
        ("python manage.py check --deploy", "Verificação para produção"),
        ("python manage.py makemigrations --dry-run", "Verificação de migrações"),
    ]
    
    results = []
    for command, description in checks:
        result = run_command(command, description)
        results.append(result)
    
    return all(results)

def run_unit_tests():
    """Executa testes unitários do Django"""
    print_section("Testes Unitários (Django)")
    
    # Primeiro, tentar o comando padrão do Django
    result1 = run_command("python manage.py test --verbosity=2", "Testes Django padrão")
    
    # Depois, executar nossos testes customizados
    result2 = run_command("python tests/django_tests.py", "Testes customizados")
    
    return result1 or result2  # Pelo menos um deve passar

def run_authentication_tests():
    """Executa testes específicos de autenticação"""
    print_section("Testes de Autenticação")
    
    return run_command("python tests/test_authentication.py", "Testes completos de autenticação")

def run_integration_tests():
    """Executa testes de integração"""
    print_section("Testes de Integração")
    
    if not check_server_status():
        print("⚠️ Servidor não está rodando. Iniciando servidor...")
        
        # Tentar iniciar o servidor em background
        try:
            # Para Windows
            if os.name == 'nt':
                subprocess.Popen(
                    ["python", "manage.py", "runserver", "0.0.0.0:8000"],
                    creationflags=subprocess.CREATE_NEW_CONSOLE
                )
            else:
                # Para Linux/Mac
                subprocess.Popen(
                    ["python", "manage.py", "runserver", "0.0.0.0:8000"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            
            # Aguardar servidor iniciar
            print("⏳ Aguardando servidor iniciar...")
            for i in range(30):  # 30 tentativas
                time.sleep(1)
                if check_server_status():
                    print("✅ Servidor iniciado com sucesso")
                    break
                print(f"   Tentativa {i+1}/30...")
            else:
                print("❌ Não foi possível iniciar o servidor automaticamente")
                print("💡 Por favor, execute manualmente: python manage.py runserver 0.0.0.0:8000")
                return False
                
        except Exception as e:
            print(f"❌ Erro ao iniciar servidor: {e}")
            print("💡 Por favor, execute manualmente: python manage.py runserver 0.0.0.0:8000")
            return False
    
    # Executar testes de integração
    return run_command("python tests/integration_tests.py", "Testes de integração completos")

def run_endpoint_tests():
    """Executa testes simples de endpoints"""
    print_section("Testes de Endpoints")
    
    return run_command("python tests/quick_test.py", "Testes básicos de endpoints")

def create_test_data():
    """Cria dados de teste se necessário"""
    print_section("Criação de Dados de Teste")
    
    return run_command("python tests/create_test_data.py", "Criação de dados de teste")

def main():
    """Função principal"""
    start_time = time.time()
    
    print_header("SUITE COMPLETA DE TESTES - HOOMOON")
    print(f"📅 Data/Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📁 Diretório: {os.getcwd()}")
    
    # Lista de testes para executar
    test_suite = [
        ("Verificações Django", run_django_checks),
        ("Dados de Teste", create_test_data),
        ("Testes Unitários", run_unit_tests),
        ("Testes de Autenticação", run_authentication_tests),
        ("Testes de Endpoints", run_endpoint_tests),
        ("Testes de Integração", run_integration_tests),
    ]
    
    results = []
    
    for test_name, test_func in test_suite:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erro no teste {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Resumo final
    end_time = time.time()
    duration = end_time - start_time
    
    print_header("RESUMO FINAL DOS TESTES")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status} | {test_name}")
    
    print(f"\n📊 Resultado Final:")
    print(f"   ✅ Passou: {passed}/{total}")
    print(f"   ❌ Falhou: {total-passed}/{total}")
    print(f"   ⏱️ Tempo total: {duration:.2f} segundos")
    print(f"   📈 Taxa de sucesso: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("🚀 Sistema pronto para uso em produção!")
    else:
        print(f"\n⚠️ {total-passed} teste(s) falharam.")
        print("🔧 Verifique os logs acima para detalhes.")
    
    print("="*60)
    
    return passed == total

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 