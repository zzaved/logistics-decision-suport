"""
Modelos Pydantic para API - Sistema Logística JIT
Baseados EXATAMENTE na estrutura do banco SQLite
"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class TresCurvasBase(BaseModel):
    """Modelo principal das 3 curvas (colheita, moagem, estoque)"""
    timestamp: datetime
    colheitabilidade_ton_h: float = Field(..., description="Colheitabilidade em ton/h")
    fazendas_ativas: int = Field(..., description="Número de fazendas ativas")
    moagem_ton_h: float = Field(..., description="Moagem atual em ton/h")
    capacidade_moagem: float = Field(..., description="Capacidade máxima de moagem")
    estoque_total_ton: float = Field(..., description="Estoque total sobre rodas")
    estoque_voltando_ton: float = Field(..., description="Estoque T1 - voltando")
    estoque_indo_ton: float = Field(..., description="Estoque T3 - indo")
    estoque_patio_ton: float = Field(..., description="Estoque T4 - pátio")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class EstadoFrota(BaseModel):
    """Estado atual da frota (46 caminhões)"""
    timestamp: datetime
    caminhoes_t1_voltando: int = Field(..., description="Caminhões em T1")
    caminhoes_t2_carregando: int = Field(..., description="Caminhões em T2")
    caminhoes_t3_indo: int = Field(..., description="Caminhões em T3")
    caminhoes_t4_patio: int = Field(..., description="Caminhões em T4")
    caminhoes_total: int = Field(default=46, description="Total da frota")
    carga_media_kg: int = Field(..., description="Carga média por caminhão")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class CaminhaoDetalhado(BaseModel):
    """Detalhes de um caminhão individual"""
    timestamp: datetime
    HR_ENTRADA_PIMS: datetime
    NO_PLACA: str = Field(..., description="Placa do caminhão")
    T_1: float = Field(..., description="Tempo T1 - vazio até colhedora")
    T_3: float = Field(..., description="Tempo T3 - carregado até usina")
    T_4: float = Field(..., description="Tempo T4 - na usina")
    QT_LIQUIDO_PESAGEM: int = Field(..., description="Peso líquido em kg")
    DISTANCIA_PIMS_MEDIA: float = Field(..., description="Distância em km")
    de_categ_oper: str = Field(..., description="Tipo de caminhão")
    ciclo_total: float = Field(..., description="Tempo total do ciclo")
    status_caminhao: str = Field(..., description="Status atual: T1, T2, T3 ou T4")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ColheitabilidadeDetalhada(BaseModel):
    """Detalhes de colheitabilidade por fazenda"""
    timestamp: datetime
    HORA_ELEVADOR_TIME: datetime
    FAZENDA: str = Field(..., description="Nome da fazenda")
    SETOR: str = Field(..., description="Setor da fazenda")
    TON_HORA: float = Field(..., description="Toneladas por hora")
    data_origem: str = Field(..., description="Data de origem")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ResumoOperacional(BaseModel):
    """Resumo operacional para o dashboard"""
    timestamp: datetime
    # 3 Curvas principais
    colheitabilidade_atual: float
    moagem_atual: float
    estoque_atual: float
    # Balanceamento
    diferenca_colheita_moagem: float = Field(..., description="Colheita - Moagem")
    tendencia_estoque: str = Field(..., description="SUBINDO, DESCENDO ou ESTAVEL")
    # Frota
    frota_total: int
    frota_distribuicao: dict
    # Alertas
    alertas: List[str] = Field(default_factory=list)
    recomendacoes: List[str] = Field(default_factory=list)

class HistoricoResponse(BaseModel):
    """Resposta com histórico das 3 curvas"""
    periodo: str = Field(..., description="Período do histórico")
    dados: List[TresCurvasBase]
    total_registros: int

class StatusSistema(BaseModel):
    """Status geral do sistema"""
    timestamp: datetime
    banco_online: bool
    ultimo_dado: Optional[datetime]
    total_registros: int
    dados_por_tabela: dict
    versao_api: str = "1.0.0"

# Modelos para WebSocket
class MensagemWebSocket(BaseModel):
    """Mensagem padrão do WebSocket"""
    tipo: str = Field(..., description="Tipo da mensagem")
    timestamp: datetime
    dados: dict

class DadosTempoReal(BaseModel):
    """Dados em tempo real para WebSocket"""
    tres_curvas: TresCurvasBase
    estado_frota: EstadoFrota
    resumo: ResumoOperacional

# Modelos para análise e relatórios
class EficienciaPorHora(BaseModel):
    """Eficiência operacional por hora"""
    hora: int
    colheitabilidade_media: float
    moagem_media: float
    estoque_medio: float
    ciclos_completados: int
    eficiencia_geral: float

class AlertaOperacional(BaseModel):
    """Alerta operacional"""
    timestamp: datetime
    tipo: str = Field(..., description="CRITICO, ATENCAO, INFO")
    titulo: str
    descricao: str
    variavel_afetada: str = Field(..., description="colheita, moagem, estoque, frota")
    valor_atual: float
    valor_limite: Optional[float]
    acao_recomendada: str

# Modelos para predição
class PredicaoTendencia(BaseModel):
    """Predição baseada em tendência"""
    timestamp_predicao: datetime
    horizonte_horas: int = Field(..., description="Quantas horas à frente")
    colheitabilidade_prevista: List[float]
    moagem_prevista: List[float]
    estoque_previsto: List[float]
    confianca_predicao: float = Field(..., description="0-1, confiança da predição")

# Responses de erro
class ErrorResponse(BaseModel):
    """Resposta de erro padrão"""
    error: bool = True
    message: str
    code: str
    timestamp: datetime
    details: Optional[dict] = None