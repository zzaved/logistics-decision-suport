#!/usr/bin/env python3
"""
Script para executar o Frontend Dashboard
Sistema Logística JIT
"""

import subprocess
import sys
import requests
from pathlib import Path

def verificar_dependencias():
    """Verifica se as dependências do frontend estão instaladas"""
    dependencias = [
        'streamlit',
        'plotly', 
        'pandas',
        'requests'
    ]
    
    print("📦 Verificando dependências do frontend...")
    
    faltando = []
    for dep in dependencias:
        try:
            __import__(dep)
            print(f"   ✅ {dep}")
        except ImportError:
            print(f"   ❌ {dep}")
            faltando.append(dep)
    
    return faltando

def instalar_dependencias():
    """Instala dependências do frontend"""
    print("🔧 Instalando dependências do frontend...")
    
    requirements = [
        "streamlit==1.28.1",
        "plotly==5.17.0", 
        "pandas==2.1.3",
        "requests==2.31.0"
    ]
    
    for req in requirements:
        print(f"   📦 Instalando {req}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", req])
            print(f"   ✅ {req} instalado")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Erro ao instalar {req}: {e}")
            return False
    
    return True

def verificar_backend():
    """Verifica se o backend está rodando"""
    print("🔗 Verificando conexão com backend...")
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Backend online")
            print(f"   📊 Status: {data.get('status', 'unknown')}")
            print(f"   🗄️ Banco: {'conectado' if data.get('banco_conectado') else 'desconectado'}")
            return True
        else:
            print(f"   ❌ Backend respondeu com status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Backend não está respondendo: {e}")
        return False

def verificar_arquivos():
    """Verifica se os arquivos do frontend existem"""
    arquivos_necessarios = [
        "frontend/dashboard.py"
    ]
    
    print("📁 Verificando arquivos do frontend...")
    
    faltando = []
    for arquivo in arquivos_necessarios:
        if Path(arquivo).exists():
            print(f"   ✅ {arquivo}")
        else:
            print(f"   ❌ {arquivo}")
            faltando.append(arquivo)
    
    return faltando

def executar_streamlit():
    """Executa o dashboard Streamlit"""
    print("\n🚀 Iniciando Dashboard Streamlit...")
    print("=" * 50)
    
    try:
        # Executar streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "frontend/dashboard.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
            "--server.headless", "false"
        ])
    except KeyboardInterrupt:
        print("\n⏹️ Dashboard parado pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao executar dashboard: {e}")

def main():
    """Função principal"""
    print("🚀 SISTEMA LOGÍSTICA JIT - FRONTEND")
    print("=" * 50)
    
    # 1. Verificar dependências
    faltando_deps = verificar_dependencias()
    
    if faltando_deps:
        resposta = input(f"\n❓ Instalar dependências faltando? (s/n): ").strip().lower()
        if resposta in ['s', 'sim', 'y', 'yes']:
            if not instalar_dependencias():
                print("❌ Falha na instalação, abortando...")
                return
        else:
            print("❌ Dependências necessárias não instaladas, abortando...")
            return
    
    # 2. Verificar arquivos
    print()
    faltando_arquivos = verificar_arquivos()
    
    if faltando_arquivos:
        print(f"\n❌ Arquivos necessários não encontrados:")
        for arquivo in faltando_arquivos:
            print(f"   - {arquivo}")
        print("\n💡 Certifique-se de copiar o código do dashboard.py para frontend/")
        return
    
    # 3. Verificar backend
    print()
    if not verificar_backend():
        print("\n❌ Backend não está rodando!")
        print("💡 Execute em outro terminal:")
        print("   python3 run_backend.py")
        print("\n❓ Quer continuar mesmo assim? (dashboard ficará com erro)")
        resposta = input("(s/n): ").strip().lower()
        if resposta not in ['s', 'sim', 'y', 'yes']:
            return
    
    # 4. Executar dashboard
    print("\n🎯 Tudo pronto! Executando dashboard...")
    print("\n🌐 O dashboard estará disponível em:")
    print("   • http://localhost:8501")
    print("\n📊 Funcionalidades:")
    print("   • Gráfico das 3 curvas em tempo real")
    print("   • Estado da frota (46 caminhões)")
    print("   • Alertas e recomendações automáticas")
    print("   • Auto-refresh a cada 30 segundos")
    print("\n💡 Pressione Ctrl+C para parar\n")
    
    input("Pressione ENTER para continuar...")
    
    executar_streamlit()

if __name__ == "__main__":
    main()