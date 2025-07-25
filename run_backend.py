#!/usr/bin/env python3
"""
Script para executar o Backend API
Sistema Logística JIT
"""

import subprocess
import sys
import os
from pathlib import Path

def verificar_dependencias():
    """Verifica se as dependências estão instaladas"""
    dependencias = [
        'fastapi',
        'uvicorn',
        'pydantic'
    ]
    
    print("📦 Verificando dependências...")
    
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
    """Instala dependências via pip"""
    print("🔧 Instalando dependências...")
    
    requirements = [
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0", 
        "pydantic==2.4.2",
        "websockets==12.0",
        "python-multipart==0.0.6"
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

def verificar_arquivos():
    """Verifica se os arquivos necessários existem"""
    arquivos_necessarios = [
        "backend/main.py",
        "backend/database.py", 
        "backend/models.py",
        "database/logistics.db"
    ]
    
    print("📁 Verificando arquivos...")
    
    faltando = []
    for arquivo in arquivos_necessarios:
        if Path(arquivo).exists():
            print(f"   ✅ {arquivo}")
        else:
            print(f"   ❌ {arquivo}")
            faltando.append(arquivo)
    
    return faltando

def executar_api():
    """Executa a API FastAPI"""
    print("\n🚀 Iniciando API FastAPI...")
    print("=" * 50)
    
    # Mudar para diretório backend
    os.chdir("backend")
    
    try:
        # Executar com uvicorn
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "main:app",
            "--host", "0.0.0.0",
            "--port", "8000", 
            "--reload"
        ])
    except KeyboardInterrupt:
        print("\n⏹️ API parada pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao executar API: {e}")

def main():
    """Função principal"""
    print("🚀 SISTEMA LOGÍSTICA JIT - BACKEND")
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
        print("\n💡 Certifique-se de copiar todos os códigos para os arquivos corretos")
        return
    
    # 3. Verificar banco com dados
    print("\n🗄️ Verificando banco de dados...")
    try:
        import sqlite3
        conn = sqlite3.connect("database/logistics.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM dados_tempo_real")
        count = cursor.fetchone()[0]
        conn.close()
        
        if count == 0:
            print("⚠️ Banco vazio! Execute primeiro:")
            print("   python3 data_generator/scheduler.py --teste")
        else:
            print(f"✅ Banco tem {count} registros")
    except Exception as e:
        print(f"❌ Erro ao verificar banco: {e}")
        return
    
    # 4. Executar API
    print("\n🎯 Tudo pronto! Executando API...")
    print("\n🌐 A API estará disponível em:")
    print("   • http://localhost:8000")
    print("   • http://localhost:8000/docs (documentação)")
    print("   • http://localhost:8000/api/tres-curvas (dados principais)")
    print("\n💡 Pressione Ctrl+C para parar\n")
    
    input("Pressione ENTER para continuar...")
    
    executar_api()

if __name__ == "__main__":
    main()