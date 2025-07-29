"""
API Principal - Sistema Logística JIT
FastAPI com endpoints para as 3 curvas principais
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import json
import sqlite3 
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import uvicorn
import sys
from pathlib import Path

# Adicionar o diretório database ao path
sys.path.append(str(Path(__file__).parent.parent / "database"))
from prediction_model import PredictionModel

# Imports locais
from database import DatabaseManager
from models import (
    TresCurvasBase, EstadoFrota, CaminhaoDetalhado, 
    ResumoOperacional, HistoricoResponse, StatusSistema,
    AlertaOperacional, ErrorResponse
)

# Configuração da API
app = FastAPI(
    title="Sistema Logística JIT",
    description="API para dashboard de monitoramento das 3 curvas principais",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS para permitir conexão do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Instância do gerenciador de banco
db_manager = DatabaseManager()

# Lista de conexões WebSocket ativas
websocket_connections: List[WebSocket] = []

@app.on_event("startup")
async def startup_event():
    """Evento de inicialização da API"""
    print("🚀 Iniciando API Sistema Logística JIT")
    
    # Verificar conexão com banco
    health = db_manager.health_check()
    if health["banco_conectado"]:
        print("✅ Banco conectado com sucesso")
        if health["dados_recentes"]:
            print(f"✅ Dados recentes (último há {health['minutos_desde_ultimo']} min)")
        else:
            print("⚠️ Dados não estão sendo atualizados recentemente")
    else:
        print(f"❌ Erro na conexão com banco: {health.get('erro')}")

@app.get("/")
async def root():
    """Endpoint raiz com informações da API"""
    return {
        "message": "Sistema Logística JIT - API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "health": "/health",
            "tres_curvas": "/api/tres-curvas",
            "historico": "/api/historico/{horas}",
            "frota": "/api/estado-frota",
            "caminhoes": "/api/caminhoes",
            "resumo": "/api/resumo-operacional",
            "docs": "/docs"
        }
    }

@app.get("/health")
async def health_check():
    """Health check da API e banco"""
    health = db_manager.health_check()
    status_code = 200 if health["banco_conectado"] else 503
    
    return JSONResponse(
        status_code=status_code,
        content={
            **health,
            "api_timestamp": datetime.now().isoformat(),
            "api_status": "online"
        }
    )

@app.get("/api/tres-curvas")
async def get_tres_curvas():
    """
    Endpoint principal: dados atuais das 3 curvas
    (Colheitabilidade, Moagem, Estoque sobre rodas)
    """
    try:
        dados = db_manager.get_dados_tempo_real_atual()
        
        if not dados:
            raise HTTPException(
                status_code=404, 
                detail="Nenhum dado encontrado. Verifique se o data generator está rodando."
            )
        
        return dados
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar dados: {str(e)}")

@app.get("/api/historico/{horas}")
async def get_historico(horas: int = 24):
    """
    Histórico das 3 curvas das últimas X horas
    """
    try:
        if horas < 1 or horas > 168:  # Max 1 semana
            raise HTTPException(status_code=400, detail="Horas deve estar entre 1 e 168")
        
        dados = db_manager.get_historico_tres_curvas(horas)
        
        return {
            "periodo": f"Últimas {horas} horas",
            "dados": dados,
            "total_registros": len(dados),
            "timestamp_consulta": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar histórico: {str(e)}")

@app.get("/api/estado-frota")
async def get_estado_frota():
    """
    Estado atual da frota (46 caminhões)
    Distribuição entre T1, T2, T3, T4
    """
    try:
        estado = db_manager.get_estado_frota_atual()
        
        if not estado:
            raise HTTPException(status_code=404, detail="Estado da frota não encontrado")
        
        return estado
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar estado da frota: {str(e)}")

@app.get("/api/caminhoes")
async def get_caminhoes(limit: int = 20):
    """
    Lista dos caminhões ativos com detalhes
    """
    try:
        if limit < 1 or limit > 100:
            raise HTTPException(status_code=400, detail="Limit deve estar entre 1 e 100")
        
        caminhoes = db_manager.get_caminhoes_ativos(limit)
        
        return {
            "caminhoes": caminhoes,
            "total": len(caminhoes),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar caminhões: {str(e)}")

@app.get("/api/colheitabilidade-fazendas")
async def get_colheitabilidade_fazendas():
    """
    Colheitabilidade por fazenda/setor
    """
    try:
        dados = db_manager.get_colheitabilidade_por_fazenda()
        
        return {
            "fazendas": dados,
            "total_fazendas": len(dados),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar colheitabilidade: {str(e)}")

@app.get("/api/resumo-operacional")
async def get_resumo_operacional():
    """
    Resumo operacional completo para o dashboard
    """
    try:
        # Dados principais
        dados_atuais = db_manager.get_dados_tempo_real_atual()
        estado_frota = db_manager.get_estado_frota_atual()
        
        if not dados_atuais or not estado_frota:
            raise HTTPException(status_code=404, detail="Dados insuficientes para resumo")
        
        # Cálculos
        colheita = dados_atuais.get('colheitabilidade_ton_h', 0)
        moagem = dados_atuais.get('moagem_ton_h', 0)
        estoque = dados_atuais.get('estoque_total_ton', 0)
        diferenca = colheita - moagem
        
        # Tendência e alertas
        tendencia = db_manager.get_tendencia_estoque()
        alertas = db_manager.get_alertas_automaticos()
        recomendacoes = db_manager.get_recomendacoes_automaticas()
        
        resumo = {
            "timestamp": datetime.now().isoformat(),
            "colheitabilidade_atual": colheita,
            "moagem_atual": moagem,
            "estoque_atual": estoque,
            "diferenca_colheita_moagem": diferenca,
            "tendencia_estoque": tendencia,
            "frota_total": estado_frota.get('caminhoes_total', 46),
            "frota_distribuicao": {
                "T1_voltando": estado_frota.get('caminhoes_t1_voltando', 0),
                "T2_carregando": estado_frota.get('caminhoes_t2_carregando', 0),
                "T3_indo": estado_frota.get('caminhoes_t3_indo', 0),
                "T4_patio": estado_frota.get('caminhoes_t4_patio', 0)
            },
            "alertas": [alerta["titulo"] for alerta in alertas],
            "recomendacoes": recomendacoes,
            "balanceamento_status": "EQUILIBRADO" if abs(diferenca) < 20 else "DESBALANCEADO"
        }
        
        return resumo
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar resumo: {str(e)}")

@app.get("/api/alertas")
async def get_alertas():
    """
    Alertas operacionais automáticos
    """
    try:
        alertas = db_manager.get_alertas_automaticos()
        
        return {
            "alertas": alertas,
            "total": len(alertas),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar alertas: {str(e)}")

@app.get("/api/recomendacoes")
async def get_recomendacoes():
    """
    Recomendações operacionais automáticas
    """
    try:
        recomendacoes = db_manager.get_recomendacoes_automaticas()
        
        return {
            "recomendacoes": recomendacoes,
            "total": len(recomendacoes),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar recomendações: {str(e)}")

@app.get("/api/estatisticas")
async def get_estatisticas():
    """
    Estatísticas gerais do sistema
    """
    try:
        stats = db_manager.get_estatisticas_gerais()
        
        return {
            "estatisticas": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar estatísticas: {str(e)}")

# ============================================================================
# WEBSOCKET PARA TEMPO REAL
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket para dados em tempo real
    Envia dados das 3 curvas a cada 5 segundos
    """
    await websocket.accept()
    websocket_connections.append(websocket)
    
    print(f"✅ Nova conexão WebSocket. Total: {len(websocket_connections)}")
    
    try:
        while True:
            # Enviar dados atuais
            try:
                dados_atuais = db_manager.get_dados_tempo_real_atual()
                estado_frota = db_manager.get_estado_frota_atual()
                
                if dados_atuais and estado_frota:
                    mensagem = {
                        "tipo": "dados_tempo_real",
                        "timestamp": datetime.now().isoformat(),
                        "tres_curvas": dados_atuais,
                        "estado_frota": estado_frota,
                        "alertas": db_manager.get_alertas_automaticos()
                    }
                    
                    await websocket.send_text(json.dumps(mensagem, default=str))
                
            except Exception as e:
                print(f"Erro no WebSocket: {e}")
                break
            
            # Aguardar 5 segundos
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        print("🔌 Cliente desconectado do WebSocket")
    except Exception as e:
        print(f"❌ Erro no WebSocket: {e}")
    finally:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)
        print(f"📊 Conexões WebSocket restantes: {len(websocket_connections)}")

async def broadcast_to_websockets(data: dict):
    """Envia dados para todas as conexões WebSocket ativas"""
    if not websocket_connections:
        return
    
    message = json.dumps(data, default=str)
    disconnected = []
    
    for websocket in websocket_connections:
        try:
            await websocket.send_text(message)
        except:
            disconnected.append(websocket)
    
    # Remover conexões mortas
    for ws in disconnected:
        websocket_connections.remove(ws)

# ============================================================================
# TRATAMENTO DE ERROS
# ============================================================================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handler para 404"""
    return JSONResponse(
        status_code=404,
        content={
            "error": True,
            "message": "Endpoint não encontrado",
            "code": "NOT_FOUND",
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url)
        }
    )

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handler para erros 500"""
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "Erro interno do servidor",
            "code": "INTERNAL_ERROR",
            "timestamp": datetime.now().isoformat()
        }
    )

@app.get("/api/estoque-patio-consolidado")
async def get_estoque_patio_consolidado():
    """
    Endpoint principal para o novo gráfico consolidado
    Retorna dados históricos + predições futuras
    """
    try:
        # Usar a conexão diretamente
        conn = sqlite3.connect(db_manager.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Histórico das últimas 12 horas
        limite_historico = datetime.now() - timedelta(hours=12)
        cursor.execute("""
            SELECT 
                timestamp,
                estoque_patio_ton,
                COALESCE(estoque_patio_fisico_ton, estoque_patio_ton * 0.7) as estoque_fisico,
                COALESCE(taxa_entrada_patio_ton_h, 0) as taxa_entrada,
                COALESCE(taxa_saida_patio_ton_h, moagem_ton_h) as taxa_saida,
                moagem_ton_h,
                colheitabilidade_ton_h
            FROM dados_tempo_real 
            WHERE timestamp >= ?
            ORDER BY timestamp ASC
        """, (limite_historico,))
        
        historico = []
        rows = cursor.fetchall()
        for row in rows:
            historico.append({
                'timestamp': row['timestamp'],
                'estoque_patio': row['estoque_patio_ton'],
                'estoque_fisico': row['estoque_fisico'],
                'taxa_entrada': row['taxa_entrada'],
                'taxa_saida': row['taxa_saida'],
                'moagem': row['moagem_ton_h'],
                'colheitabilidade': row['colheitabilidade_ton_h']
            })
        
        # Buscar última predição
        cursor.execute("""
            SELECT 
                timestamp_predicao,
                hora_futura,
                timestamp_previsto,
                estoque_patio_previsto_ton,
                estoque_limite_superior_ton,
                estoque_limite_inferior_ton,
                confiabilidade_percent,
                ofensor_principal,
                ofensor_valor
            FROM predicoes_estoque_patio
            WHERE timestamp_predicao = (
                SELECT MAX(timestamp_predicao) FROM predicoes_estoque_patio
            )
            ORDER BY hora_futura ASC
        """)
        
        predicoes = []
        timestamp_predicao = None
        pred_rows = cursor.fetchall()
        for row in pred_rows:
            if not timestamp_predicao:
                timestamp_predicao = row[0]
            predicoes.append({
                'hora_futura': row[1],
                'timestamp_previsto': row[2],
                'estoque_previsto': row[3],
                'limite_superior': row[4],
                'limite_inferior': row[5],
                'confiabilidade': row[6] / 100.0,
                'ofensor': row[7],
                'ofensor_valor': row[8]
            })
        
        # Buscar limites operacionais
        cursor.execute("""
            SELECT limite_inferior, limite_superior,
                   limite_critico_inferior, limite_critico_superior
            FROM limites_operacionais
            WHERE variavel = 'estoque_patio_ton'
        """)
        limites_row = cursor.fetchone()
        
        conn.close()
        
        # Estado atual
        estado_atual = None
        if historico:
            ultimo = historico[-1]
            estado_atual = {
                'timestamp': ultimo['timestamp'],
                'estoque_patio': ultimo['estoque_patio'],
                'taxa_entrada': ultimo['taxa_entrada'],
                'taxa_saida': ultimo['taxa_saida'],
                'balanco': ultimo['taxa_entrada'] - ultimo['taxa_saida']
            }
        
        return {
            "timestamp_consulta": datetime.now().isoformat(),
            "limites": {
                "inferior": limites_row[0] if limites_row else 800,
                "superior": limites_row[1] if limites_row else 1500,
                "critico_inferior": limites_row[2] if limites_row else 600,
                "critico_superior": limites_row[3] if limites_row else 1800
            },
            "historico": {
                "dados": historico,
                "total_pontos": len(historico),
                "horas": 12
            },
            "estado_atual": estado_atual,
            "predicao": {
                "timestamp_predicao": timestamp_predicao,
                "dados": predicoes,
                "horizonte_horas": len(predicoes)
            } if predicoes else None
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar dados consolidados: {str(e)}")

@app.post("/api/gerar-predicao",
    summary="Gera nova predição",
    description="Força geração de nova predição de estoque para próximas 9 horas")
async def gerar_nova_predicao():
    """
    Força geração de nova predição
    """
    try:
        model = PredictionModel()
        resultado = model.executar_predicao(salvar=True)
        
        return {
            "status": "success",
            "timestamp_predicao": resultado['timestamp_predicao'].isoformat(),
            "horizonte_horas": resultado['horizonte_horas'],
            "predicoes_geradas": len(resultado['predicoes']),
            "modelo": resultado['modelo_usado']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar predição: {str(e)}")


@app.get("/api/eventos-alertas/{horas}",
    summary="Eventos e alertas recentes",
    description="Retorna eventos do sistema nas últimas X horas")
async def get_eventos_alertas(horas: int = 2):
    """
    Retorna eventos e alertas do sistema
    """
    try:
        if horas < 1 or horas > 24:
            raise HTTPException(status_code=400, detail="Horas deve estar entre 1 e 24")
        
        limite = datetime.now() - timedelta(hours=horas)
        conn = sqlite3.connect(db_manager.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT * FROM eventos_sistema
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
            LIMIT 100
        """, (limite,))
        
        eventos = []
        resumo = {"INFO": 0, "AVISO": 0, "CRITICO": 0}
        
        for row in cursor.fetchall():
            evento = dict(row)
            eventos.append(evento)
            resumo[evento['severidade']] += 1
        
        conn.close()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "periodo_horas": horas,
            "resumo_severidade": resumo,
            "total_eventos": len(eventos),
            "eventos": eventos[:50]  # Limitar resposta
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao buscar eventos: {str(e)}")


@app.get("/api/analise-ofensores",
    summary="Análise de ofensores",
    description="Identifica principais causas de violações de limites")
async def get_analise_ofensores():
    """
    Analisa principais ofensores nas últimas horas
    """
    try:
        conn = sqlite3.connect(db_manager.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Buscar ofensores das predições recentes
        cursor.execute("""
            SELECT 
                ofensor_principal,
                COUNT(*) as ocorrencias,
                AVG(ofensor_valor) as valor_medio
            FROM predicoes_estoque_patio
            WHERE timestamp_predicao > datetime('now', '-6 hours')
                AND ofensor_principal IS NOT NULL
            GROUP BY ofensor_principal
            ORDER BY ocorrencias DESC
        """)
        
        ofensores = []
        for row in cursor.fetchall():
            ofensores.append({
                'tipo': row[0],
                'ocorrencias': row[1],
                'valor_medio': round(row[2], 1) if row[2] else None
            })
        
        # Buscar o ofensor mais frequente
        ofensor_principal = ofensores[0]['tipo'] if ofensores else None
        
        # Gerar recomendações
        recomendacoes_map = {
            "COLHEITA_ALTA": [
                "🌾 Reduzir temporariamente frentes de colheita",
                "🚚 Priorizar fazendas mais distantes", 
                "📊 Verificar capacidade máxima de moagem"
            ],
            "MOAGEM_BAIXA": [
                "🏭 Verificar status dos equipamentos",
                "⚡ Otimizar eficiência da moenda",
                "🔧 Avaliar necessidade de manutenção"
            ],
            "CHEGADAS_EXCESSIVAS": [
                "🚛 Espaçar melhor as chegadas",
                "📍 Direcionar para fazendas distantes",
                "⏱️ Implementar agendamento"
            ],
            "POUCAS_CHEGADAS": [
                "🚚 Aumentar frota ativa",
                "📍 Focar em fazendas próximas",
                "🔄 Reduzir tempo de ciclo"
            ]
        }
        
        recomendacoes = recomendacoes_map.get(ofensor_principal, ["📊 Continuar monitorando"])
        
        conn.close()
        
        return {
            "periodo_analise": "Últimas 6 horas",
            "timestamp": datetime.now().isoformat(),
            "total_violacoes": sum(o['ocorrencias'] for o in ofensores),
            "ofensores_frequentes": ofensores,
            "ofensor_principal": ofensor_principal,
            "recomendacoes": recomendacoes
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na análise: {str(e)}")


@app.websocket("/ws/estoque-patio")
async def websocket_estoque_patio(websocket: WebSocket):
    """
    WebSocket específico para dados do estoque no pátio
    Envia atualizações a cada 10 segundos
    """
    await websocket.accept()
    
    try:
        while True:
            # Buscar dados atuais
            conn = sqlite3.connect(db_manager.db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Estado atual
            cursor.execute("""
                SELECT 
                    timestamp,
                    estoque_patio_ton,
                    COALESCE(taxa_entrada_patio_ton_h, 0) as taxa_entrada,
                    COALESCE(taxa_saida_patio_ton_h, moagem_ton_h) as taxa_saida
                FROM dados_tempo_real
                ORDER BY timestamp DESC
                LIMIT 1
            """)
            
            atual = cursor.fetchone()
            
            # Verificar alertas
            cursor.execute("""
                SELECT COUNT(*) FROM eventos_sistema
                WHERE timestamp > datetime('now', '-5 minutes')
                AND severidade IN ('AVISO', 'CRITICO')
            """)
            
            alertas_recentes = cursor.fetchone()[0]
            
            conn.close()
            
            if atual:
                mensagem = {
                    "tipo": "estoque_patio_update",
                    "timestamp": datetime.now().isoformat(),
                    "dados": {
                        "estoque_atual": atual[1],
                        "taxa_entrada": atual[2],
                        "taxa_saida": atual[3],
                        "balanco": atual[2] - atual[3],
                        "timestamp_dado": atual[0]
                    },
                    "tem_alertas": alertas_recentes > 0,
                    "num_alertas": alertas_recentes
                }
                
                await websocket.send_json(mensagem)
            
            # Aguardar 10 segundos
            await asyncio.sleep(10)
            
    except WebSocketDisconnect:
        print("🔌 Cliente desconectado do WebSocket estoque-patio")
    except Exception as e:
        print(f"❌ Erro no WebSocket estoque-patio: {e}")
        await websocket.close()


# ============================================================================
# 3. ADICIONAR ESTE ENDPOINT DE STATUS PARA VERIFICAR SE TUDO ESTÁ FUNCIONANDO
# ============================================================================

@app.get("/api/status-v2",
    summary="Status do sistema V2",
    description="Verifica se todos os componentes V2 estão funcionando")
async def get_status_v2():
    """
    Verifica status de todos os componentes V2
    """
    try:
        status = {
            "timestamp": datetime.now().isoformat(),
            "componentes": {}
        }
        
        conn = sqlite3.connect(db_manager.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # 1. Verificar novas tabelas
        tabelas_v2 = [
            'padroes_horarios',
            'predicoes_estoque_patio',
            'limites_operacionais',
            'eventos_sistema'
        ]
        
        for tabela in tabelas_v2:
            cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
            count = cursor.fetchone()[0]
            status["componentes"][f"tabela_{tabela}"] = {
                "existe": True,
                "registros": count
            }
        
        # 2. Verificar novas colunas
        cursor.execute("PRAGMA table_info(dados_tempo_real)")
        colunas = [col[1] for col in cursor.fetchall()]
        
        novas_colunas = [
            'estoque_patio_fisico_ton',
            'taxa_entrada_patio_ton_h',
            'taxa_saida_patio_ton_h'
        ]
        
        for coluna in novas_colunas:
            status["componentes"][f"coluna_{coluna}"] = coluna in colunas
        
        # 3. Verificar última predição
        cursor.execute("""
            SELECT MAX(timestamp_predicao) FROM predicoes_estoque_patio
        """)
        ultima_predicao = cursor.fetchone()[0]
        
        if ultima_predicao:
            minutos_desde_predicao = (datetime.now() - datetime.fromisoformat(ultima_predicao.replace('Z', '+00:00'))).total_seconds() / 60
            status["componentes"]["predicao"] = {
                "ultima": ultima_predicao,
                "minutos_atras": round(minutos_desde_predicao, 1),
                "status": "OK" if minutos_desde_predicao < 10 else "ATRASADA"
            }
        else:
            status["componentes"]["predicao"] = {
                "status": "SEM_PREDICOES"
            }
        
        # 4. Verificar dados recentes
        cursor.execute("""
            SELECT 
                MAX(timestamp) as ultimo,
                COUNT(*) as total
            FROM dados_tempo_real
            WHERE timestamp > datetime('now', '-1 hour')
        """)
        dados_recentes = cursor.fetchone()
        
        status["componentes"]["dados_tempo_real"] = {
            "ultimo_registro": dados_recentes[0],
            "registros_ultima_hora": dados_recentes[1],
            "gerando_dados": dados_recentes[1] > 3
        }
        
        conn.close()
        
        # Status geral
        tudo_ok = all(
            comp.get("existe", comp.get("status", True)) 
            for comp in status["componentes"].values()
        )
        
        status["status_geral"] = "OK" if tudo_ok else "PROBLEMAS"
        status["versao"] = "2.0"
        
        return status
        
    except Exception as e:
        return {
            "status_geral": "ERRO",
            "erro": str(e),
            "timestamp": datetime.now().isoformat()
        }

# ============================================================================
# INICIALIZAÇÃO
# ============================================================================

if __name__ == "__main__":
    print("🚀 Iniciando servidor FastAPI")
    print("📊 Dashboard API - Sistema Logística JIT")
    print("=" * 50)
    print("🌐 Acesse:")
    print("   API: http://localhost:8000")
    print("   Docs: http://localhost:8000/docs")
    print("   Health: http://localhost:8000/health")
    print("   3 Curvas: http://localhost:8000/api/tres-curvas")
    print("=" * 50)
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000,
        reload=False,  # Desabilitar em produção
        log_level="info"
    )
    
