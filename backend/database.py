"""
Conexão e queries do banco SQLite - Sistema Logística JIT
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager

class DatabaseManager:
    """Gerenciador de conexão e queries do banco SQLite"""
    
    def __init__(self, db_path: str = "../database/logistics.db"):
        self.db_path = Path(db_path)
        
        if not self.db_path.exists():
            raise FileNotFoundError(f"Banco não encontrado: {self.db_path}")
    
    @contextmanager
    def get_connection(self):
        """Context manager para conexão com o banco"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Para acessar colunas por nome
        try:
            yield conn
        finally:
            conn.close()
    
    def get_dados_tempo_real_atual(self) -> Optional[Dict]:
        """Obtém os dados mais recentes das 3 curvas"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM dados_tempo_real 
                ORDER BY timestamp DESC 
                LIMIT 1
            """)
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_historico_tres_curvas(self, horas: int = 24) -> List[Dict]:
        """Obtém histórico das 3 curvas das últimas X horas"""
        limite = datetime.now() - timedelta(hours=horas)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM dados_tempo_real 
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
            """, (limite,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_estado_frota_atual(self) -> Optional[Dict]:
        """Obtém estado atual da frota"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM estado_frota 
                ORDER BY timestamp DESC 
                LIMIT 1
            """)
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def get_caminhoes_ativos(self, limit: int = 20) -> List[Dict]:
        """Obtém lista de caminhões com detalhes"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM transporte_detalhado 
                ORDER BY timestamp DESC 
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_colheitabilidade_por_fazenda(self, limit: int = 50) -> List[Dict]:
        """Obtém dados de colheitabilidade por fazenda"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT FAZENDA, SETOR, AVG(TON_HORA) as media_ton_hora,
                       COUNT(*) as registros, MAX(timestamp) as ultimo_update
                FROM colheitabilidade_detalhada 
                WHERE timestamp >= datetime('now', '-2 hours')
                GROUP BY FAZENDA, SETOR
                ORDER BY media_ton_hora DESC
                LIMIT ?
            """, (limit,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    def get_estatisticas_gerais(self) -> Dict:
        """Obtém estatísticas gerais do sistema"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Contadores por tabela
            stats = {}
            tabelas = ['dados_tempo_real', 'estado_frota', 'transporte_detalhado', 'colheitabilidade_detalhada']
            
            for tabela in tabelas:
                cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
                stats[f"{tabela}_count"] = cursor.fetchone()[0]
                
                cursor.execute(f"SELECT MAX(timestamp) FROM {tabela}")
                ultimo = cursor.fetchone()[0]
                stats[f"{tabela}_ultimo"] = ultimo
            
            # Dados da última hora
            cursor.execute("""
                SELECT 
                    AVG(colheitabilidade_ton_h) as colheita_media,
                    AVG(moagem_ton_h) as moagem_media,
                    AVG(estoque_total_ton) as estoque_medio,
                    COUNT(*) as registros_ultima_hora
                FROM dados_tempo_real 
                WHERE timestamp >= datetime('now', '-1 hour')
            """)
            
            row = cursor.fetchone()
            if row:
                stats.update(dict(row))
            
            return stats
    
    def get_tendencia_estoque(self, minutos: int = 30) -> str:
        """Calcula tendência do estoque (SUBINDO, DESCENDO, ESTAVEL)"""
        limite = datetime.now() - timedelta(minutes=minutos)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT estoque_total_ton, timestamp 
                FROM dados_tempo_real 
                WHERE timestamp >= ?
                ORDER BY timestamp ASC
            """, (limite,))
            
            dados = cursor.fetchall()
            
            if len(dados) < 2:
                return "ESTAVEL"
            
            # Comparar primeiro e último
            primeiro = dados[0][0]
            ultimo = dados[-1][0]
            diferenca = ultimo - primeiro
            
            if diferenca > 100:  # +100 ton
                return "SUBINDO"
            elif diferenca < -100:  # -100 ton
                return "DESCENDO"
            else:
                return "ESTAVEL"
    
    def get_alertas_automaticos(self) -> List[Dict]:
        """Gera alertas baseados nos dados atuais"""
        alertas = []
        
        # Dados atuais
        dados_atuais = self.get_dados_tempo_real_atual()
        if not dados_atuais:
            return alertas
        
        colheita = dados_atuais.get('colheitabilidade_ton_h', 0)
        moagem = dados_atuais.get('moagem_ton_h', 0)
        estoque = dados_atuais.get('estoque_total_ton', 0)
        
        # Alerta: Estoque muito alto
        if estoque > 2700:
            alertas.append({
                "tipo": "ATENCAO",
                "titulo": "Estoque Alto",
                "descricao": f"Estoque atual: {estoque:.0f} ton (acima de 2.700)",
                "variavel": "estoque",
                "valor": estoque
            })
        
        # Alerta: Estoque muito baixo
        if estoque < 2000:
            alertas.append({
                "tipo": "CRITICO",
                "titulo": "Estoque Baixo",
                "descricao": f"Estoque atual: {estoque:.0f} ton (abaixo de 2.000)",
                "variavel": "estoque",
                "valor": estoque
            })
        
        # Alerta: Desbalanceamento
        diferenca = colheita - moagem
        if abs(diferenca) > 50:
            tipo_alerta = "CRITICO" if abs(diferenca) > 100 else "ATENCAO"
            if diferenca > 0:
                msg = f"Colheita muito maior que moagem ({diferenca:+.1f} ton/h)"
            else:
                msg = f"Moagem muito maior que colheita ({diferenca:+.1f} ton/h)"
                
            alertas.append({
                "tipo": tipo_alerta,
                "titulo": "Desbalanceamento",
                "descricao": msg,
                "variavel": "balanceamento",
                "valor": diferenca
            })
        
        # Alerta: Colheita muito baixa
        if colheita < 35:
            alertas.append({
                "tipo": "ATENCAO",
                "titulo": "Colheita Baixa",
                "descricao": f"Colheitabilidade: {colheita:.1f} ton/h (abaixo de 35)",
                "variavel": "colheita",
                "valor": colheita
            })
        
        return alertas
    
    def get_recomendacoes_automaticas(self) -> List[str]:
        """Gera recomendações baseadas nos dados atuais"""
        recomendacoes = []
        
        dados_atuais = self.get_dados_tempo_real_atual()
        if not dados_atuais:
            return recomendacoes
        
        colheita = dados_atuais.get('colheitabilidade_ton_h', 0)
        moagem = dados_atuais.get('moagem_ton_h', 0)
        estoque = dados_atuais.get('estoque_total_ton', 0)
        tendencia = self.get_tendencia_estoque()
        
        # Recomendações baseadas no estoque
        if estoque > 2600 and tendencia == "SUBINDO":
            recomendacoes.append("✅ Momento ideal para despachar fazendas distantes")
            recomendacoes.append("📊 Estoque alto permite ciclos mais longos")
        
        elif estoque < 2100 and tendencia == "DESCENDO":
            recomendacoes.append("⚠️ Priorizar fazendas próximas apenas")
            recomendacoes.append("🚀 Focar em ciclos rápidos")
        
        # Recomendações baseadas no balanceamento
        if colheita > moagem + 30:
            recomendacoes.append("🏭 Considerar aumentar ritmo da moagem")
            recomendacoes.append("📈 Estoque tende a crescer")
        
        elif moagem > colheita + 30:
            recomendacoes.append("🌾 Verificar disponibilidade de mais frentes")
            recomendacoes.append("📉 Estoque tende a diminuir")
        
        # Recomendações baseadas na hora atual
        hora_atual = datetime.now().hour
        if 13 <= hora_atual <= 16:
            recomendacoes.append("🕐 Horário crítico da tarde - evitar fazendas distantes")
        elif 6 <= hora_atual <= 9:
            recomendacoes.append("🌅 Horário ideal da manhã - aproveitar para otimizar")
        
        return recomendacoes
    
    def health_check(self) -> Dict:
        """Verifica saúde do banco de dados"""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                
                # Verificar última atualização
                cursor.execute("SELECT MAX(timestamp) FROM dados_tempo_real")
                ultimo_dado = cursor.fetchone()[0]
                
                if ultimo_dado:
                    ultimo_dt = datetime.fromisoformat(ultimo_dado.replace('Z', '+00:00'))
                    minutos_desde_ultimo = (datetime.now() - ultimo_dt).total_seconds() / 60
                else:
                    minutos_desde_ultimo = 999
                
                return {
                    "status": "healthy",
                    "banco_conectado": True,
                    "ultimo_dado": ultimo_dado,
                    "minutos_desde_ultimo": round(minutos_desde_ultimo, 1),
                    "dados_recentes": minutos_desde_ultimo < 5  # Menos de 5 min
                }
                
        except Exception as e:
            return {
                "status": "error",
                "banco_conectado": False,
                "erro": str(e)
            }