#!/usr/bin/env python
"""
Script principal de testes do HooMoon
Ponto de entrada único para todos os tipos de teste
"""
import sys
import os
import subprocess
import time

def print_header():
    """Imprime cabeçalho"""
    print("🧪 HooMoon - Executando Testes")
    print("="*40)

def show_help():
    """Mostra a ajuda de comandos"""
    print_header()
    print("📚 Comandos disponíveis:\n")
    print("  python test.py          - Teste rápido (endpoints básicos)")
    print("  python test.py data     - Criar dados de teste")
    print("  python test.py django   - Verificações Django")
    print("  python test.py all      - Executar todos os testes")
    print("  python test.py help     - Mostrar esta ajuda")
    print("\n💡 Exemplos:")
    print("  python test.py          # Teste rápido")
    print("  python test.py all      # Suite completa")

def run_command(cmd, description):
    """Executa comando sem capturar saída"""
    print(f"\n▶️ {description}")
    print("-" * 30)
    try:
        result = subprocess.run(cmd, shell=True, cwd=os.getcwd())
        if result.returncode == 0:
            print(f"✅ {description} - Sucesso")
            return True
        else:
            print(f"❌ {description} - Falhou (código: {result.returncode})")
            return False
    except Exception as e:
        print(f"❌ {description} - Erro de execução: {str(e)}")
        return False

def run_quick_test():
    """Executa teste rápido"""
    print_header()
    print("⚡ Executando teste rápido...")
    return run_command(f"{sys.executable} tests/quick_test.py", "Teste rápido de endpoints")

def create_test_data():
    """Cria dados de teste"""
    print_header()
    print("📦 Criando dados de teste...")
    return run_command(f"{sys.executable} tests/create_test_data.py", "Criação de dados de teste")

def run_django_checks():
    """Executa verificações Django"""
    print_header()
    print("🔧 Executando verificações Django...")
    
    checks = [
        (f"{sys.executable} manage.py check", "Verificação geral do sistema"),
        (f"{sys.executable} tests/django_tests.py", "Testes básicos Django"),
    ]
    
    results = []
    for cmd, desc in checks:
        result = run_command(cmd, desc)
        results.append(result)
    
    return all(results)

def run_all_tests():
    """Executa todos os testes disponíveis"""
    print_header()
    print("🏆 Executando todos os testes...")
    
    start_time = time.time()
    
    tests = [
        ("Verificações Django", run_django_checks),
        ("Dados de Teste", create_test_data),
        ("Teste Rápido", run_quick_test),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Erro em {test_name}: {str(e)}")
            results.append((test_name, False))
    
    # Resumo final
    end_time = time.time()
    duration = end_time - start_time
    
    print("\n" + "="*50)
    print("📊 RESUMO FINAL DOS TESTES")
    print("="*50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{status} | {test_name}")
    
    print("-"*50)
    print(f"📈 Total: {passed}/{total} testes passaram")
    print(f"⏱️ Tempo total: {duration:.2f} segundos")
    print(f"📊 Taxa de sucesso: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        print("🚀 Sistema HooMoon está funcionando perfeitamente!")
    else:
        print(f"\n⚠️ {total-passed} teste(s) falharam.")
        print("🔧 Verifique os detalhes acima.")
    
    print("="*50)
    
    return passed == total

def main():
    """Função principal"""
    if len(sys.argv) == 1:
        # Sem argumentos = teste rápido
        success = run_quick_test()
    elif len(sys.argv) == 2:
        command = sys.argv[1].lower()
        
        if command == "help":
            show_help()
            return
        elif command == "data":
            success = create_test_data() 
        elif command == "django":
            success = run_django_checks()
        elif command == "all":
            success = run_all_tests()
        else:
            print(f"❌ Comando desconhecido: {command}")
            show_help()
            return
    else:
        print("❌ Muitos argumentos")
        show_help()
        return
    
    # Resultado final
    if success:
        print("\n✅ Testes concluídos com sucesso!")
    else:
        print("\n❌ Alguns testes falharam.")
        print("💡 Dica: Execute 'python test.py' para teste rápido")
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main() 