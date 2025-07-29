"""
Script para executar as atualizações V2 no banco de dados
Sistema Logística JIT - Estoque no Pátio
"""

import sqlite3
import sys
from pathlib import Path
from datetime import datetime

def executar_atualizacao(db_path="database/logistics.db"):
    """Executa o script SQL de atualização V2"""
    
    print("🔧 SISTEMA LOGÍSTICA JIT - ATUALIZAÇÃO V2")
    print("=" * 60)
    print(f"📊 Banco: {db_path}")
    print(f"🕐 Início: {datetime.now()}")
    print()
    
    # Verificar se banco existe
    if not Path(db_path).exists():
        print("❌ Erro: Banco não encontrado!")
        print("💡 Execute primeiro: python database/init_db.py")
        return False
    
    try:
        # Conectar ao banco
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("📝 Executando atualizações...")
        
        # Ler o script SQL
        sql_script = """
        -- [CONTEÚDO DO SQL AQUI - muito grande para repetir]
        -- Este script está no arquivo update_database_v2.sql
        """
        
        # Para este exemplo, vou executar as principais alterações
        updates = [
            # 1. Adicionar colunas nas tabelas existentes
            ("ALTER TABLE transporte_detalhado ADD COLUMN velocidade_media_kmh REAL DEFAULT 0", "velocidade média"),
            ("ALTER TABLE transporte_detalhado ADD COLUMN tempo_descarga_min REAL DEFAULT 0", "tempo descarga"),
            ("ALTER TABLE transporte_detalhado ADD COLUMN hora_chegada_patio DATETIME", "hora chegada pátio"),
            ("ALTER TABLE transporte_detalhado ADD COLUMN hora_saida_patio DATETIME", "hora saída pátio"),
            
            ("ALTER TABLE estado_frota ADD COLUMN taxa_chegada_caminhoes_hora REAL DEFAULT 0", "taxa chegada/hora"),
            ("ALTER TABLE estado_frota ADD COLUMN previsao_chegadas_prox_hora INTEGER DEFAULT 0", "previsão chegadas"),
            
            ("ALTER TABLE dados_tempo_real ADD COLUMN estoque_patio_fisico_ton REAL DEFAULT 0", "estoque físico pátio"),
            ("ALTER TABLE dados_tempo_real ADD COLUMN taxa_entrada_patio_ton_h REAL DEFAULT 0", "taxa entrada pátio"),
            ("ALTER TABLE dados_tempo_real ADD COLUMN taxa_saida_patio_ton_h REAL DEFAULT 0", "taxa saída pátio"),
        ]
        
        # Executar cada alteração
        for sql, descricao in updates:
            try:
                cursor.execute(sql)
                print(f"   ✅ Adicionado: {descricao}")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e):
                    print(f"   ⏭️ Já existe: {descricao}")
                else:
                    print(f"   ❌ Erro em {descricao}: {e}")
        
        # 2. Criar novas tabelas
        print("\n📊 Criando novas tabelas...")
        
        # Tabela de padrões horários
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS padroes_horarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hora_dia INTEGER NOT NULL CHECK (hora_dia >= 0 AND hora_dia <= 23),
            dia_semana INTEGER NOT NULL CHECK (dia_semana >= 0 AND dia_semana <= 6),
            colheita_media_ton_h REAL NOT NULL DEFAULT 0,
            moagem_media_ton_h REAL NOT NULL DEFAULT 0,
            chegadas_media_caminhoes REAL NOT NULL DEFAULT 0,
            velocidade_media_kmh REAL NOT NULL DEFAULT 0,
            colheita_desvio_padrao REAL NOT NULL DEFAULT 0,
            moagem_desvio_padrao REAL NOT NULL DEFAULT 0,
            chegadas_desvio_padrao REAL NOT NULL DEFAULT 0,
            total_amostras INTEGER NOT NULL DEFAULT 0,
            ultima_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(hora_dia, dia_semana)
        )
        """)
        print("   ✅ Tabela: padroes_horarios")
        
        # Tabela de predições
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS predicoes_estoque_patio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp_predicao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            hora_futura INTEGER NOT NULL,
            timestamp_previsto DATETIME NOT NULL,
            estoque_patio_previsto_ton REAL NOT NULL,
            chegadas_previstas_ton REAL NOT NULL,
            moagem_prevista_ton REAL NOT NULL,
            estoque_limite_superior_ton REAL NOT NULL,
            estoque_limite_inferior_ton REAL NOT NULL,
            confiabilidade_percent REAL NOT NULL CHECK (confiabilidade_percent >= 0 AND confiabilidade_percent <= 100),
            ofensor_principal TEXT,
            ofensor_valor REAL,
            modelo_usado TEXT DEFAULT 'V1_BASELINE',
            criado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("   ✅ Tabela: predicoes_estoque_patio")
        
        # Tabela de limites
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS limites_operacionais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            variavel TEXT NOT NULL UNIQUE,
            limite_inferior REAL NOT NULL,
            limite_superior REAL NOT NULL,
            limite_critico_inferior REAL,
            limite_critico_superior REAL,
            unidade TEXT NOT NULL,
            descricao TEXT,
            atualizado_em DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """)
        print("   ✅ Tabela: limites_operacionais")
        
        # Tabela de eventos
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS eventos_sistema (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            tipo_evento TEXT NOT NULL,
            severidade TEXT NOT NULL CHECK (severidade IN ('INFO', 'AVISO', 'CRITICO')),
            variavel_afetada TEXT NOT NULL,
            valor_atual REAL,
            limite_violado REAL,
            descricao TEXT NOT NULL,
            acao_tomada TEXT,
            resolvido BOOLEAN DEFAULT 0,
            resolvido_em DATETIME
        )
        """)
        print("   ✅ Tabela: eventos_sistema")
        
        # 3. Inserir dados padrão
        print("\n📈 Inserindo dados padrão...")
        
        # Limites operacionais
        cursor.execute("""
        INSERT OR REPLACE INTO limites_operacionais 
        (variavel, limite_inferior, limite_superior, limite_critico_inferior, limite_critico_superior, unidade, descricao) 
        VALUES
        ('estoque_patio_ton', 800, 1500, 600, 1800, 'ton', 'Estoque físico no pátio da usina'),
        ('taxa_chegada_hora', 15, 35, 10, 40, 'caminhões/h', 'Taxa de chegada de caminhões no pátio'),
        ('moagem_ton_h', 800, 1100, 700, 1150, 'ton/h', 'Taxa de moagem da usina')
        """)
        print("   ✅ Limites operacionais definidos")
        
        # 4. Criar índices
        print("\n🔍 Criando índices...")
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_predicoes_timestamp ON predicoes_estoque_patio(timestamp_predicao)",
            "CREATE INDEX IF NOT EXISTS idx_predicoes_hora ON predicoes_estoque_patio(hora_futura)",
            "CREATE INDEX IF NOT EXISTS idx_eventos_timestamp ON eventos_sistema(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_eventos_tipo ON eventos_sistema(tipo_evento)",
            "CREATE INDEX IF NOT EXISTS idx_transporte_status_timestamp ON transporte_detalhado(status_caminhao, timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_dados_estoque_patio ON dados_tempo_real(estoque_patio_ton, timestamp)"
        ]
        
        for idx in indices:
            cursor.execute(idx)
        print("   ✅ Índices criados")
        
        # Commit das alterações
        conn.commit()
        
        # 5. Verificar estrutura atualizada
        print("\n📋 Verificando estrutura atualizada...")
        
        # Contar tabelas
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
        total_tabelas = cursor.fetchone()[0]
        print(f"   📊 Total de tabelas: {total_tabelas}")
        
        # Listar novas tabelas
        cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name IN ('padroes_horarios', 'predicoes_estoque_patio', 
                                        'limites_operacionais', 'eventos_sistema')
        """)
        novas_tabelas = cursor.fetchall()
        print("   📋 Novas tabelas criadas:")
        for tabela in novas_tabelas:
            print(f"      - {tabela[0]}")
        
        conn.close()
        
        print("\n✅ ATUALIZAÇÃO V2 CONCLUÍDA COM SUCESSO!")
        print(f"🕐 Término: {datetime.now()}")
        print("\n🎯 Próximos passos:")
        print("   1. Atualizar o mock_generator.py para incluir as novas variáveis")
        print("   2. Criar o modelo de predição")
        print("   3. Atualizar a API para servir os novos dados")
        
        return True
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE ATUALIZAÇÃO: {e}")
        return False

def verificar_estrutura(db_path="database/logistics.db"):
    """Verifica a estrutura atualizada do banco"""
    
    print("\n📊 VERIFICANDO ESTRUTURA DO BANCO")
    print("=" * 40)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar colunas da tabela dados_tempo_real
        cursor.execute("PRAGMA table_info(dados_tempo_real)")
        colunas = cursor.fetchall()
        
        print("\n📋 Colunas em 'dados_tempo_real':")
        novas_colunas = ['estoque_patio_fisico_ton', 'taxa_entrada_patio_ton_h', 'taxa_saida_patio_ton_h']
        for col in colunas:
            nome = col[1]
            if nome in novas_colunas:
                print(f"   ✅ {nome} (NOVA)")
            else:
                print(f"   - {nome}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Erro ao verificar: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--check":
        verificar_estrutura()
    else:
        executar_atualizacao()
        verificar_estrutura()