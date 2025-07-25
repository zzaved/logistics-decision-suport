#!/usr/bin/env python3
"""
Debug do Banco - Teste direto de inserção
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path

def verificar_banco():
    """Verifica estado atual do banco"""
    db_path = Path("database/logistics.db")
    
    print("🔍 VERIFICAÇÃO DO BANCO")
    print("=" * 40)
    
    if not db_path.exists():
        print("❌ Banco não existe!")
        return False
    
    # Tamanho do arquivo
    tamanho = db_path.stat().st_size
    print(f"📁 Localização: {db_path.absolute()}")
    print(f"📏 Tamanho: {tamanho} bytes")
    
    # Verificar tabelas
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Listar tabelas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tabelas = [row[0] for row in cursor.fetchall()]
    print(f"📊 Tabelas: {tabelas}")
    
    # Contar registros
    for tabela in tabelas:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
            count = cursor.fetchone()[0]
            print(f"   {tabela}: {count} registros")
            
            if count > 0:
                cursor.execute(f"SELECT * FROM {tabela} LIMIT 1")
                exemplo = cursor.fetchone()
                print(f"      Exemplo: {exemplo}")
        except Exception as e:
            print(f"   {tabela}: ERRO - {e}")
    
    conn.close()
    return True

def inserir_teste_direto():
    """Insere dados de teste diretamente no banco"""
    print("\n🧪 INSERÇÃO TESTE DIRETO")
    print("=" * 40)
    
    db_path = Path("database/logistics.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Inserir na tabela principal
        now = datetime.now()
        cursor.execute("""
            INSERT INTO dados_tempo_real 
            (timestamp, colheitabilidade_ton_h, fazendas_ativas, moagem_ton_h, 
             capacidade_moagem, estoque_total_ton, estoque_voltando_ton, 
             estoque_indo_ton, estoque_patio_ton)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (now, 55.5, 10, 120.0, 1150.0, 2300.0, 800.0, 900.0, 600.0))
        
        # Inserir estado da frota
        cursor.execute("""
            INSERT INTO estado_frota 
            (timestamp, caminhoes_t1_voltando, caminhoes_t2_carregando,
             caminhoes_t3_indo, caminhoes_t4_patio, carga_media_kg)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (now, 14, 8, 16, 8, 70000))
        
        # COMMIT EXPLÍCITO
        conn.commit()
        print("✅ Dados inseridos com sucesso!")
        
        # Verificar se foram salvos
        cursor.execute("SELECT COUNT(*) FROM dados_tempo_real")
        count = cursor.fetchone()[0]
        print(f"✅ Registros após inserção: {count}")
        
    except Exception as e:
        print(f"❌ Erro na inserção: {e}")
        conn.rollback()
    
    finally:
        conn.close()

def verificar_permissoes():
    """Verifica permissões de escrita"""
    print("\n🔐 VERIFICAÇÃO DE PERMISSÕES")
    print("=" * 40)
    
    db_dir = Path("database")
    db_path = db_dir / "logistics.db"
    
    print(f"📁 Pasta database existe: {db_dir.exists()}")
    print(f"📁 Pasta database é diretório: {db_dir.is_dir()}")
    print(f"📁 Pasta database permissões: {oct(db_dir.stat().st_mode)[-3:] if db_dir.exists() else 'N/A'}")
    
    print(f"📄 Arquivo logistics.db existe: {db_path.exists()}")
    if db_path.exists():
        print(f"📄 Arquivo permissões: {oct(db_path.stat().st_mode)[-3:]}")
        print(f"📄 Arquivo pode ler: {os.access(db_path, os.R_OK)}")
        print(f"📄 Arquivo pode escrever: {os.access(db_path, os.W_OK)}")

def main():
    """Executa todos os testes de debug"""
    print("🚀 DEBUG DO BANCO LOGISTICS.DB")
    print("=" * 50)
    
    # 1. Verificar estado atual
    if not verificar_banco():
        print("❌ Banco não encontrado, parando debug")
        return
    
    # 2. Verificar permissões
    verificar_permissoes()
    
    # 3. Inserir teste direto
    inserir_teste_direto()
    
    # 4. Verificar novamente
    print("\n🔄 VERIFICAÇÃO FINAL")
    print("=" * 40)
    verificar_banco()
    
    print("\n💡 PRÓXIMOS PASSOS:")
    print("1. Se ainda estiver vazio, problema é na inserção")
    print("2. Se funcionou agora, problema era no commit")
    print("3. Execute novamente: python3 data_generator/mock_generator.py")

if __name__ == "__main__":
    main()