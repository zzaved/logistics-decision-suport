-- ============================================================================
-- SISTEMA LOGÍSTICA JIT - UPDATE V2
-- Adiciona estruturas para cálculo de estoque no pátio e predições
-- ============================================================================

-- 1. ADICIONAR COLUNAS FALTANTES NA TABELA EXISTENTE
-- ----------------------------------------------------------------------------

-- Adicionar velocidade média e tempo de descarga aos caminhões
ALTER TABLE transporte_detalhado ADD COLUMN velocidade_media_kmh REAL DEFAULT 0;
ALTER TABLE transporte_detalhado ADD COLUMN tempo_descarga_min REAL DEFAULT 0;
ALTER TABLE transporte_detalhado ADD COLUMN hora_chegada_patio DATETIME;
ALTER TABLE transporte_detalhado ADD COLUMN hora_saida_patio DATETIME;

-- Adicionar taxa de chegada ao estado da frota
ALTER TABLE estado_frota ADD COLUMN taxa_chegada_caminhoes_hora REAL DEFAULT 0;
ALTER TABLE estado_frota ADD COLUMN previsao_chegadas_prox_hora INTEGER DEFAULT 0;

-- Adicionar estoque específico do pátio (mais detalhado)
ALTER TABLE dados_tempo_real ADD COLUMN estoque_patio_fisico_ton REAL DEFAULT 0;
ALTER TABLE dados_tempo_real ADD COLUMN taxa_entrada_patio_ton_h REAL DEFAULT 0;
ALTER TABLE dados_tempo_real ADD COLUMN taxa_saida_patio_ton_h REAL DEFAULT 0;

-- 2. CRIAR TABELA DE PADRÕES HISTÓRICOS POR HORA
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS padroes_horarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hora_dia INTEGER NOT NULL CHECK (hora_dia >= 0 AND hora_dia <= 23),
    dia_semana INTEGER NOT NULL CHECK (dia_semana >= 0 AND dia_semana <= 6),
    
    -- Médias históricas por hora
    colheita_media_ton_h REAL NOT NULL DEFAULT 0,
    moagem_media_ton_h REAL NOT NULL DEFAULT 0,
    chegadas_media_caminhoes REAL NOT NULL DEFAULT 0,
    velocidade_media_kmh REAL NOT NULL DEFAULT 0,
    
    -- Desvios padrão para cálculo de confiabilidade
    colheita_desvio_padrao REAL NOT NULL DEFAULT 0,
    moagem_desvio_padrao REAL NOT NULL DEFAULT 0,
    chegadas_desvio_padrao REAL NOT NULL DEFAULT 0,
    
    -- Metadados
    total_amostras INTEGER NOT NULL DEFAULT 0,
    ultima_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(hora_dia, dia_semana)
);

-- 3. CRIAR TABELA DE PREDIÇÕES
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS predicoes_estoque_patio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp_predicao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Horizonte da predição
    hora_futura INTEGER NOT NULL, -- 1 a 9 horas à frente
    timestamp_previsto DATETIME NOT NULL,
    
    -- Valores previstos
    estoque_patio_previsto_ton REAL NOT NULL,
    chegadas_previstas_ton REAL NOT NULL,
    moagem_prevista_ton REAL NOT NULL,
    
    -- Limites de confiança
    estoque_limite_superior_ton REAL NOT NULL,
    estoque_limite_inferior_ton REAL NOT NULL,
    confiabilidade_percent REAL NOT NULL CHECK (confiabilidade_percent >= 0 AND confiabilidade_percent <= 100),
    
    -- Ofensores identificados
    ofensor_principal TEXT, -- 'COLHEITA_ALTA', 'MOAGEM_BAIXA', 'CHEGADAS_ALTAS', etc
    ofensor_valor REAL,
    
    -- Metadados
    modelo_usado TEXT DEFAULT 'V1_BASELINE',
    criado_em DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_predicoes_timestamp (timestamp_predicao),
    INDEX idx_predicoes_hora (hora_futura)
);

-- 4. CRIAR TABELA DE LIMITES OPERACIONAIS
-- ----------------------------------------------------------------------------
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
);

-- Inserir limites padrão
INSERT OR REPLACE INTO limites_operacionais (variavel, limite_inferior, limite_superior, limite_critico_inferior, limite_critico_superior, unidade, descricao) VALUES
('estoque_patio_ton', 800, 1500, 600, 1800, 'ton', 'Estoque físico no pátio da usina'),
('taxa_chegada_hora', 15, 35, 10, 40, 'caminhões/h', 'Taxa de chegada de caminhões no pátio'),
('moagem_ton_h', 800, 1100, 700, 1150, 'ton/h', 'Taxa de moagem da usina');

-- 5. CRIAR TABELA DE EVENTOS E ALERTAS
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS eventos_sistema (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    tipo_evento TEXT NOT NULL, -- 'LIMITE_EXCEDIDO', 'OFENSOR_DETECTADO', 'PREDICAO_ALERTA'
    severidade TEXT NOT NULL CHECK (severidade IN ('INFO', 'AVISO', 'CRITICO')),
    variavel_afetada TEXT NOT NULL,
    valor_atual REAL,
    limite_violado REAL,
    descricao TEXT NOT NULL,
    acao_tomada TEXT,
    resolvido BOOLEAN DEFAULT 0,
    resolvido_em DATETIME,
    
    INDEX idx_eventos_timestamp (timestamp),
    INDEX idx_eventos_tipo (tipo_evento)
);

-- 6. CRIAR VIEW CONSOLIDADA PARA O NOVO GRÁFICO
-- ----------------------------------------------------------------------------
CREATE VIEW IF NOT EXISTS view_estoque_patio_consolidado AS
SELECT 
    d.timestamp,
    d.estoque_patio_ton as estoque_sobre_rodas_patio,
    COALESCE(d.estoque_patio_fisico_ton, d.estoque_patio_ton * 0.7) as estoque_fisico_patio,
    d.moagem_ton_h,
    COALESCE(d.taxa_entrada_patio_ton_h, 
        (SELECT COUNT(*) * 70 / 1000.0 
         FROM transporte_detalhado t 
         WHERE t.status_caminhao = 'T3' 
         AND t.timestamp >= datetime(d.timestamp, '-1 hour')
        )) as taxa_entrada_patio,
    d.taxa_saida_patio_ton_h as taxa_saida_patio,
    
    -- Cálculo do balanço
    COALESCE(d.taxa_entrada_patio_ton_h, 0) - d.moagem_ton_h as balanco_ton_h,
    
    -- Identificação de ofensores
    CASE 
        WHEN d.estoque_patio_ton > 1500 THEN 
            CASE 
                WHEN d.colheitabilidade_ton_h > 700 THEN 'COLHEITA_ALTA'
                WHEN d.moagem_ton_h < 900 THEN 'MOAGEM_BAIXA'
                ELSE 'CHEGADAS_EXCESSIVAS'
            END
        WHEN d.estoque_patio_ton < 800 THEN
            CASE
                WHEN d.colheitabilidade_ton_h < 500 THEN 'COLHEITA_BAIXA'
                WHEN d.moagem_ton_h > 1050 THEN 'MOAGEM_ALTA'
                ELSE 'POUCAS_CHEGADAS'
            END
        ELSE NULL
    END as ofensor_principal
    
FROM dados_tempo_real d
ORDER BY d.timestamp DESC;

-- 7. CRIAR TRIGGERS PARA CÁLCULOS AUTOMÁTICOS
-- ----------------------------------------------------------------------------

-- Trigger para calcular velocidade média ao inserir caminhão
CREATE TRIGGER IF NOT EXISTS calcular_velocidade_media
AFTER INSERT ON transporte_detalhado
BEGIN
    UPDATE transporte_detalhado
    SET velocidade_media_kmh = CASE
        WHEN T_3 > 0 THEN DISTANCIA_PIMS_MEDIA / T_3
        ELSE 0
    END
    WHERE id = NEW.id;
END;

-- Trigger para atualizar padrões históricos
CREATE TRIGGER IF NOT EXISTS atualizar_padroes_horarios
AFTER INSERT ON dados_tempo_real
BEGIN
    INSERT OR REPLACE INTO padroes_horarios (
        hora_dia, 
        dia_semana,
        colheita_media_ton_h,
        moagem_media_ton_h,
        total_amostras
    )
    SELECT 
        CAST(strftime('%H', NEW.timestamp) AS INTEGER),
        CAST(strftime('%w', NEW.timestamp) AS INTEGER),
        AVG(colheitabilidade_ton_h),
        AVG(moagem_ton_h),
        COUNT(*)
    FROM dados_tempo_real
    WHERE 
        CAST(strftime('%H', timestamp) AS INTEGER) = CAST(strftime('%H', NEW.timestamp) AS INTEGER)
        AND CAST(strftime('%w', timestamp) AS INTEGER) = CAST(strftime('%w', NEW.timestamp) AS INTEGER)
        AND timestamp >= datetime('now', '-30 days');
END;

-- 8. ÍNDICES PARA PERFORMANCE
-- ----------------------------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_transporte_status_timestamp ON transporte_detalhado(status_caminhao, timestamp);
CREATE INDEX IF NOT EXISTS idx_transporte_velocidade ON transporte_detalhado(velocidade_media_kmh);
CREATE INDEX IF NOT EXISTS idx_dados_estoque_patio ON dados_tempo_real(estoque_patio_ton, timestamp);

-- 9. POPULAR DADOS INICIAIS DE PADRÕES (baseado em observações típicas)
-- ----------------------------------------------------------------------------

-- Inserir padrões típicos por hora (segunda a sexta)
INSERT OR IGNORE INTO padroes_horarios (hora_dia, dia_semana, colheita_media_ton_h, moagem_media_ton_h, chegadas_media_caminhoes, velocidade_media_kmh, colheita_desvio_padrao, moagem_desvio_padrao, chegadas_desvio_padrao)
VALUES
-- Madrugada (0-5h) - Operação reduzida
(0, 1, 450, 850, 18, 65, 50, 40, 3), (1, 1, 430, 840, 17, 65, 45, 35, 3),
(2, 1, 420, 830, 16, 68, 40, 30, 2), (3, 1, 410, 820, 16, 70, 40, 30, 2),
(4, 1, 420, 830, 17, 68, 45, 35, 3), (5, 1, 450, 850, 18, 65, 50, 40, 3),

-- Manhã (6-11h) - Ramp up
(6, 1, 500, 900, 22, 60, 60, 45, 4), (7, 1, 550, 950, 25, 58, 70, 50, 5),
(8, 1, 600, 1000, 28, 55, 80, 55, 5), (9, 1, 650, 1050, 30, 52, 85, 60, 6),
(10, 1, 680, 1080, 32, 50, 90, 65, 6), (11, 1, 700, 1100, 33, 48, 95, 70, 7),

-- Tarde (12-17h) - Pico com queda
(12, 1, 690, 1090, 32, 48, 90, 65, 6), (13, 1, 650, 1050, 30, 50, 85, 60, 6),
(14, 1, 600, 1000, 28, 52, 80, 55, 5), (15, 1, 550, 950, 25, 55, 70, 50, 5),
(16, 1, 520, 920, 23, 58, 65, 45, 4), (17, 1, 500, 900, 22, 60, 60, 45, 4),

-- Noite (18-23h) - Operação noturna
(18, 1, 480, 880, 20, 62, 55, 40, 4), (19, 1, 470, 870, 19, 63, 50, 38, 3),
(20, 1, 460, 860, 19, 64, 48, 36, 3), (21, 1, 450, 850, 18, 65, 45, 35, 3),
(22, 1, 450, 850, 18, 65, 45, 35, 3), (23, 1, 450, 850, 18, 65, 45, 35, 3);

-- Mensagem de conclusão
SELECT 'Banco de dados atualizado com sucesso para V2!' as mensagem;