"""
Modelo de Predição de Estoque no Pátio
Sistema Logística JIT - V2
"""

import sqlite3
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import math
import statistics
from pathlib import Path

class PredictionModel:
    """
    Modelo para prever estoque no pátio nas próximas 9 horas
    com níveis de confiabilidade decrescentes
    """
class PredictionModel:
    def __init__(self, db_path=None):
        if db_path is None:
            # Use caminho absoluto baseado na localização do arquivo
            self.db_path = Path(__file__).parent / "logistics.db"
        else:
            self.db_path = Path(db_path)

        # Configurações de confiabilidade por horizonte
        self.confiabilidade_por_hora = {
            1: 0.95,   # 95% para 1 hora
            2: 0.92,   # 92% para 2 horas
            3: 0.88,   # 88% para 3 horas
            4: 0.82,   # 82% para 4 horas
            5: 0.75,   # 75% para 5 horas
            6: 0.68,   # 68% para 6 horas
            7: 0.60,   # 60% para 7 horas
            8: 0.52,   # 52% para 8 horas
            9: 0.45    # 45% para 9 horas
        }
        
        # Cache de padrões históricos
        self.padroes_cache = {}
    
    def conectar_banco(self):
        """Conecta ao banco SQLite"""
        return sqlite3.connect(self.db_path)
    
    def obter_dados_atuais(self) -> Dict:
        """Obtém o estado atual do sistema"""
        conn = self.conectar_banco()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                timestamp,
                estoque_patio_ton,
                estoque_patio_fisico_ton,
                taxa_entrada_patio_ton_h,
                taxa_saida_patio_ton_h,
                colheitabilidade_ton_h,
                moagem_ton_h,
                estoque_indo_ton
            FROM dados_tempo_real
            ORDER BY timestamp DESC
            LIMIT 1
        """)
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
        
        return {
            'timestamp': row[0],
            'estoque_patio_atual': row[1],
            'estoque_fisico_atual': row[2] or row[1] * 0.7,
            'taxa_entrada_atual': row[3] or 0,
            'taxa_saida_atual': row[4] or row[6],  # Se não tiver, usa moagem
            'colheitabilidade': row[5],
            'moagem': row[6],
            'estoque_indo': row[7]
        }
    
    def obter_padroes_historicos(self, hora: int, dia_semana: int) -> Dict:
        """Obtém padrões históricos para uma hora específica"""
        cache_key = f"{hora}_{dia_semana}"
        
        if cache_key in self.padroes_cache:
            return self.padroes_cache[cache_key]
        
        conn = self.conectar_banco()
        cursor = conn.cursor()
        
        # Buscar padrões da tabela
        cursor.execute("""
            SELECT 
                colheita_media_ton_h,
                moagem_media_ton_h,
                chegadas_media_caminhoes,
                colheita_desvio_padrao,
                moagem_desvio_padrao,
                chegadas_desvio_padrao
            FROM padroes_horarios
            WHERE hora_dia = ? AND dia_semana = ?
        """, (hora, dia_semana))
        
        row = cursor.fetchone()
        
        if not row:
            # Se não houver padrão, calcular dos dados históricos
            cursor.execute("""
                SELECT 
                    AVG(taxa_entrada_patio_ton_h) as entrada_media,
                    AVG(taxa_saida_patio_ton_h) as saida_media,
                    AVG(colheitabilidade_ton_h) as colheita_media,
                    AVG(moagem_ton_h) as moagem_media,
                    COUNT(*) as amostras
                FROM dados_tempo_real
                WHERE CAST(strftime('%H', timestamp) AS INTEGER) = ?
                AND timestamp > datetime('now', '-7 days')
            """, (hora,))
            
            historico = cursor.fetchone()
            
            padroes = {
                'entrada_media': historico[0] or 50,
                'saida_media': historico[1] or 85,
                'colheita_media': historico[2] or 60,
                'moagem_media': historico[3] or 85,
                'entrada_desvio': 10,  # Valores padrão
                'saida_desvio': 8,
                'amostras': historico[4] or 0
            }
        else:
            # Calcular entrada baseada em chegadas
            carga_media = 70  # toneladas por caminhão
            entrada_estimada = row[2] * carga_media
            
            padroes = {
                'entrada_media': entrada_estimada,
                'saida_media': row[1],
                'colheita_media': row[0],
                'moagem_media': row[1],
                'entrada_desvio': row[5] * carga_media if row[5] else 10,
                'saida_desvio': row[4] or 8,
                'amostras': 100  # Assumir boa quantidade de dados
            }
        
        conn.close()
        
        self.padroes_cache[cache_key] = padroes
        return padroes
    
    def calcular_tendencia_recente(self) -> Dict:
        """Calcula tendências das últimas 2 horas"""
        conn = self.conectar_banco()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                timestamp,
                estoque_patio_ton,
                taxa_entrada_patio_ton_h,
                taxa_saida_patio_ton_h
            FROM dados_tempo_real
            WHERE timestamp > datetime('now', '-2 hours')
            ORDER BY timestamp ASC
        """)
        
        dados = cursor.fetchall()
        conn.close()
        
        if len(dados) < 3:
            return {'tendencia_estoque': 0, 'tendencia_entrada': 0, 'tendencia_saida': 0}
        
        # Calcular tendências usando regressão linear simples
        estoques = [d[1] for d in dados]
        entradas = [d[2] or 0 for d in dados]
        saidas = [d[3] or 0 for d in dados]
        
        # Diferença média por hora
        horas = len(dados) / 6  # Assumindo dados a cada 10 minutos
        
        tendencia_estoque = (estoques[-1] - estoques[0]) / horas if horas > 0 else 0
        tendencia_entrada = (sum(entradas[-3:]) - sum(entradas[:3])) / (len(entradas) * 0.3) if len(entradas) > 6 else 0
        tendencia_saida = (sum(saidas[-3:]) - sum(saidas[:3])) / (len(saidas) * 0.3) if len(saidas) > 6 else 0
        
        return {
            'tendencia_estoque': tendencia_estoque,
            'tendencia_entrada': tendencia_entrada,
            'tendencia_saida': tendencia_saida
        }
    
    def prever_hora(self, hora_futura: int, estado_anterior: Dict, 
                    hora_do_dia: int, dia_semana: int) -> Dict:
        """Prevê o estado para uma hora específica no futuro"""
        
        # Obter padrões históricos para a hora
        padroes = self.obter_padroes_historicos(hora_do_dia, dia_semana)
        
        # Obter tendências recentes
        tendencias = self.calcular_tendencia_recente()
        
        # Calcular confiabilidade
        confiabilidade = self.confiabilidade_por_hora.get(hora_futura, 0.4)
        
        # Peso para combinar histórico com tendência recente
        peso_historico = 0.7 * confiabilidade
        peso_tendencia = 0.3
        
        # Prever entrada (chegadas no pátio)
        entrada_historica = padroes['entrada_media']
        entrada_tendencia = estado_anterior['taxa_entrada'] + tendencias['tendencia_entrada']
        entrada_prevista = (entrada_historica * peso_historico + 
                           entrada_tendencia * peso_tendencia)
        
        # Prever saída (moagem)
        saida_historica = padroes['saida_media']
        saida_tendencia = estado_anterior['taxa_saida'] + tendencias['tendencia_saida']
        saida_prevista = (saida_historica * peso_historico + 
                         saida_tendencia * peso_tendencia)
        
        # Calcular balanço
        balanco = entrada_prevista - saida_prevista
        
        # Prever estoque
        estoque_previsto = estado_anterior['estoque'] + balanco
        
        # Adicionar incerteza baseada na confiabilidade
        desvio_entrada = padroes.get('entrada_desvio', 10)
        desvio_saida = padroes.get('saida_desvio', 8)
        
        # Intervalo de confiança cresce com o horizonte
        fator_incerteza = 1 + (1 - confiabilidade)
        
        limite_superior = estoque_previsto + (desvio_entrada + desvio_saida) * fator_incerteza
        limite_inferior = estoque_previsto - (desvio_entrada + desvio_saida) * fator_incerteza
        
        # Garantir limites não negativos
        limite_inferior = max(0, limite_inferior)
        
        return {
            'hora_futura': hora_futura,
            'timestamp_previsto': datetime.now() + timedelta(hours=hora_futura),
            'estoque_previsto': round(estoque_previsto, 1),
            'entrada_prevista': round(entrada_prevista, 1),
            'saida_prevista': round(saida_prevista, 1),
            'balanco_previsto': round(balanco, 1),
            'limite_superior': round(limite_superior, 1),
            'limite_inferior': round(limite_inferior, 1),
            'confiabilidade': confiabilidade,
            'hora_do_dia': hora_do_dia,
            'taxa_entrada': entrada_prevista,
            'taxa_saida': saida_prevista,
            'estoque': estoque_previsto
        }
    
    def identificar_ofensor(self, estoque: float, entrada: float, 
                           saida: float, limites: Dict) -> Tuple[str, float]:
        """Identifica o principal ofensor quando estoque sai dos limites"""
        
        if estoque > limites['superior']:
            # Estoque muito alto
            if entrada > 60:  # Alta entrada
                return "CHEGADAS_EXCESSIVAS", entrada
            elif saida < 80:  # Baixa saída
                return "MOAGEM_BAIXA", saida
            else:
                return "ACUMULO_GRADUAL", estoque
                
        elif estoque < limites['inferior']:
            # Estoque muito baixo
            if entrada < 40:  # Baixa entrada
                return "POUCAS_CHEGADAS", entrada
            elif saida > 100:  # Alta saída
                return "MOAGEM_ALTA", saida
            else:
                return "CONSUMO_GRADUAL", estoque
        
        return None, None
    
    def gerar_predicao_completa(self, horizonte_horas: int = 9) -> Dict:
        """Gera predição completa para as próximas N horas"""
        
        # Estado atual
        dados_atuais = self.obter_dados_atuais()
        if not dados_atuais:
            raise ValueError("Não há dados atuais disponíveis")
        
        # Obter limites operacionais
        conn = self.conectar_banco()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT limite_inferior, limite_superior 
            FROM limites_operacionais 
            WHERE variavel = 'estoque_patio_ton'
        """)
        limites_row = cursor.fetchone()
        conn.close()
        
        limites = {
            'inferior': limites_row[0] if limites_row else 800,
            'superior': limites_row[1] if limites_row else 1500
        }
        
        # Preparar predições
        predicoes = []
        hora_atual = datetime.now().hour
        dia_semana = datetime.now().weekday()
        
        # Estado para propagação
        estado = {
            'estoque': dados_atuais['estoque_patio_atual'],
            'taxa_entrada': dados_atuais['taxa_entrada_atual'],
            'taxa_saida': dados_atuais['taxa_saida_atual']
        }
        
        # Gerar predição para cada hora
        for h in range(1, horizonte_horas + 1):
            hora_futura = (hora_atual + h) % 24
            dia_futuro = dia_semana if (hora_atual + h) < 24 else (dia_semana + 1) % 7
            
            predicao = self.prever_hora(h, estado, hora_futura, dia_futuro)
            
            # Identificar ofensor se necessário
            ofensor, valor_ofensor = self.identificar_ofensor(
                predicao['estoque_previsto'],
                predicao['entrada_prevista'],
                predicao['saida_prevista'],
                limites
            )
            
            predicao['ofensor_principal'] = ofensor
            predicao['ofensor_valor'] = valor_ofensor
            predicao['dentro_limites'] = (limites['inferior'] <= 
                                         predicao['estoque_previsto'] <= 
                                         limites['superior'])
            
            predicoes.append(predicao)
            
            # Atualizar estado para próxima hora
            estado = {
                'estoque': predicao['estoque_previsto'],
                'taxa_entrada': predicao['entrada_prevista'],
                'taxa_saida': predicao['saida_prevista']
            }
        
        return {
            'timestamp_predicao': datetime.now(),
            'dados_atuais': dados_atuais,
            'limites_operacionais': limites,
            'predicoes': predicoes,
            'horizonte_horas': horizonte_horas,
            'modelo_usado': 'V2_TENDENCIA_HISTORICO'
        }
    
    def salvar_predicao(self, predicao_completa: Dict):
        """Salva predição no banco de dados"""
        conn = self.conectar_banco()
        cursor = conn.cursor()
        
        timestamp_pred = predicao_completa['timestamp_predicao']
        
        for pred in predicao_completa['predicoes']:
            cursor.execute("""
                INSERT INTO predicoes_estoque_patio
                (timestamp_predicao, hora_futura, timestamp_previsto,
                 estoque_patio_previsto_ton, chegadas_previstas_ton,
                 moagem_prevista_ton, estoque_limite_superior_ton,
                 estoque_limite_inferior_ton, confiabilidade_percent,
                 ofensor_principal, ofensor_valor, modelo_usado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp_pred,
                pred['hora_futura'],
                pred['timestamp_previsto'],
                pred['estoque_previsto'],
                pred['entrada_prevista'],
                pred['saida_prevista'],
                pred['limite_superior'],
                pred['limite_inferior'],
                pred['confiabilidade'] * 100,
                pred['ofensor_principal'],
                pred['ofensor_valor'],
                predicao_completa['modelo_usado']
            ))
        
        conn.commit()
        conn.close()
    
    def executar_predicao(self, salvar=True) -> Dict:
        """Executa predição completa e opcionalmente salva"""
        try:
            predicao = self.gerar_predicao_completa()
            
            if salvar:
                self.salvar_predicao(predicao)
                
            # Log resumido
            print(f"\n📊 Predição gerada às {datetime.now().strftime('%H:%M:%S')}")
            print(f"   Estoque atual: {predicao['dados_atuais']['estoque_patio_atual']:.0f} ton")
            
            # Mostrar previsões chave
            for h in [1, 3, 6, 9]:
                if h <= len(predicao['predicoes']):
                    pred = predicao['predicoes'][h-1]
                    status = "✅" if pred['dentro_limites'] else "⚠️"
                    print(f"   +{h}h: {pred['estoque_previsto']:.0f} ton "
                          f"({pred['confiabilidade']*100:.0f}%) {status}")
            
            return predicao
            
        except Exception as e:
            print(f"❌ Erro na predição: {e}")
            raise


def testar_modelo():
    """Testa o modelo de predição"""
    print("🧪 Testando Modelo de Predição")
    print("=" * 50)
    
    model = PredictionModel()
    
    try:
        # Executar predição
        resultado = model.executar_predicao(salvar=False)
        
        print("\n📈 Detalhes da Predição:")
        print(f"Modelo: {resultado['modelo_usado']}")
        print(f"Limites: {resultado['limites_operacionais']['inferior']:.0f} - "
              f"{resultado['limites_operacionais']['superior']:.0f} ton")
        
        print("\n📊 Predições por hora:")
        print("Hora | Estoque | Entrada | Saída | Balanço | Confiab. | Status")
        print("-" * 70)
        
        for pred in resultado['predicoes']:
            status = "OK" if pred['dentro_limites'] else f"FORA ({pred['ofensor_principal']})"
            print(f" +{pred['hora_futura']:2d}h | "
                  f"{pred['estoque_previsto']:7.1f} | "
                  f"{pred['entrada_prevista']:7.1f} | "
                  f"{pred['saida_prevista']:6.1f} | "
                  f"{pred['balanco_previsto']:+7.1f} | "
                  f"{pred['confiabilidade']*100:6.0f}% | "
                  f"{status}")
        
        print("\n✅ Teste concluído com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    testar_modelo()