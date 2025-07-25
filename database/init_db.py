#!/usr/bin/env python3
"""
Script de Inicialização do Banco de Dados
Sistema Logística JIT - Usina Sucroenergética

Cria o banco SQLite com todas as tabelas necessárias
baseadas EXATAMENTE na estrutura dos dados reais descobertos.
"""

import sqlite3
import os
from pathlib import Path

def create_database():
    """Cria o banco SQLite e todas as tabelas"""
    
    # Garantir que a pasta database existe
    db_dir = Path("database")
    db_dir.mkdir(exist_ok=True)
    
    db_path = db_dir / "logistics.db"
    
    # Se já existe, fazer backup
    if db_path.exists():
        backup_path = db_dir / "logistics_backup.db"
        os.rename(db_path, backup_path)
        print(f"✅ Backup criado: {backup_path}")
    
    # Conectar ao banco
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"🗄️ Criando banco: {db_path}")
    
    # Schema SQL
    schema_sql = """
    -- Tabela principal: dados agregados das 3 curvas em tempo real
    CREATE TABLE dados_tempo_real (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        -- Colheitabilidade (bronze_cubo.colheitabilidade)
        colheitabilidade_ton_h REAL,           -- TON_HORA (30-80 range natural)
        fazendas_ativas INTEGER,               -- COUNT(DISTINCT FAZENDA)
        -- Moagem (bronze_pims.pimspro_rel_003) 
        moagem_ton_h REAL,                     -- VAR_RESULT_DIA convertido (50-200 range)
        capacidade_moagem REAL,                -- Capacidade máxima da usina
        -- Estoque sobre rodas (calculado de bronze_pims.McKinsey_data_request_transporte_v3)
        estoque_total_ton REAL,                -- Total estoque sobre rodas (1800-2800 range)
        estoque_voltando_ton REAL,             -- T1 - caminhões voltando
        estoque_indo_ton REAL,                 -- T3 - caminhões indo
        estoque_patio_ton REAL,                -- T4 - caminhões no pátio
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- Detalhes do transporte (como chegam do PIMS)
    CREATE TABLE transporte_detalhado (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        -- Colunas EXATAS do bronze_pims.McKinsey_data_request_transporte_v3
        HR_ENTRADA_PIMS DATETIME,              -- TIMESTAMP como chega
        NO_PLACA TEXT,                         -- STRING - placa do caminhão
        T_1 REAL,                             -- FLOAT64 - tempo vazio até colhedora
        T_3 REAL,                             -- FLOAT64 - tempo carregado até usina  
        T_4 REAL,                             -- FLOAT64 - tempo na usina
        QT_LIQUIDO_PESAGEM INTEGER,           -- INT - peso líquido em kg
        DISTANCIA_PIMS_MEDIA REAL,            -- FLOAT64 - distância em km
        de_categ_oper TEXT,                   -- STRING - tipo de caminhão
        -- Campos calculados
        ciclo_total REAL,                     -- T_1 + 2.0 + T_3 + T_4
        status_caminhao TEXT,                 -- 'T1', 'T2', 'T3', 'T4'
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- Detalhes da colheitabilidade (como chegam do cubo)
    CREATE TABLE colheitabilidade_detalhada (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        -- Colunas EXATAS do bronze_cubo.colheitabilidade
        HORA_ELEVADOR_TIME DATETIME,          -- TIMESTAMP da colheita
        FAZENDA TEXT,                         -- STRING - nome da fazenda
        SETOR TEXT,                          -- STRING - setor da fazenda
        TON_HORA REAL,                       -- FLOAT64 - toneladas por hora
        data_origem DATE,                    -- DATE - data da origem
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- Estado atual da frota (46 caminhões)
    CREATE TABLE estado_frota (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        -- Distribuição dos 46 caminhões
        caminhoes_t1_voltando INTEGER,        -- Quantos em T1
        caminhoes_t2_carregando INTEGER,      -- Quantos em T2 (fixo ~8)
        caminhoes_t3_indo INTEGER,           -- Quantos em T3
        caminhoes_t4_patio INTEGER,          -- Quantos em T4
        -- Totais
        caminhoes_total INTEGER DEFAULT 46,   -- Total da frota
        carga_media_kg INTEGER,               -- Carga média por caminhão
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- Moagem detalhada (como chega do PIMS)
    CREATE TABLE moagem_detalhada (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        -- Colunas EXATAS do bronze_pims.pimspro_rel_003
        DATA DATETIME,                        -- TIMESTAMP
        ORR_DESCRI TEXT,                     -- STRING - descrição da variável
        VAR_RESULT_DIA REAL,                 -- FLOAT64 - resultado do dia
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    );

    -- Índices para performance
    CREATE INDEX idx_dados_tempo_real_timestamp ON dados_tempo_real(timestamp);
    CREATE INDEX idx_transporte_hr_entrada ON transporte_detalhado(HR_ENTRADA_PIMS);
    CREATE INDEX idx_transporte_placa ON transporte_detalhado(NO_PLACA);
    CREATE INDEX idx_colheitabilidade_hora ON colheitabilidade_detalhada(HORA_ELEVADOR_TIME);
    CREATE INDEX idx_estado_frota_timestamp ON estado_frota(timestamp);
    CREATE INDEX idx_moagem_data ON moagem_detalhada(DATA);
    """
    
    # Executar schema
    cursor.executescript(schema_sql)
    
    # Inserir dados iniciais de teste
    cursor.execute("""
        INSERT INTO dados_tempo_real 
        (colheitabilidade_ton_h, fazendas_ativas, moagem_ton_h, capacidade_moagem, 
         estoque_total_ton, estoque_voltando_ton, estoque_indo_ton, estoque_patio_ton)
        VALUES (60.5, 12, 85.2, 1150, 2324, 980, 910, 434)
    """)
    
    cursor.execute("""
        INSERT INTO estado_frota 
        (caminhoes_t1_voltando, caminhoes_t2_carregando, caminhoes_t3_indo, caminhoes_t4_patio, carga_media_kg)
        VALUES (14, 8, 13, 6, 70000)
    """)
    
    # Commit e fechar
    conn.commit()
    conn.close()
    
    print("✅ Banco criado com sucesso!")
    print("✅ Tabelas criadas:")
    print("   - dados_tempo_real")
    print("   - transporte_detalhado") 
    print("   - colheitabilidade_detalhada")
    print("   - estado_frota")
    print("   - moagem_detalhada")
    print("✅ Índices criados para performance")
    print("✅ Dados iniciais inseridos")
    print(f"📁 Localização: {db_path.absolute()}")

def verify_database():
    """Verifica se o banco foi criado corretamente"""
    db_path = Path("database/logistics.db")
    
    if not db_path.exists():
        print("❌ Banco não encontrado!")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Verificar tabelas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    expected_tables = [
        'dados_tempo_real', 'transporte_detalhado', 
        'colheitabilidade_detalhada', 'estado_frota', 'moagem_detalhada'
    ]
    
    print("🔍 Verificação do banco:")
    for table in expected_tables:
        if table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"✅ {table}: {count} registros")
        else:
            print(f"❌ {table}: não encontrada")
    
    conn.close()
    return True

if __name__ == "__main__":
    print("🚀 Inicializando Sistema Logística JIT")
    print("=" * 50)
    
    create_database()
    print()
    verify_database()
    
    print()
    print("🎯 Próximos passos:")
    print("1. Executar data generator: python data_generator/scheduler.py")
    print("2. Executar backend: python backend/main.py") 
    print("3. Executar frontend: streamlit run frontend/dashboard.py")