"""
API Principal - Sistema Logística JIT
FastAPI com endpoints para as 3 curvas principais
"""

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Optional
import uvicorn

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