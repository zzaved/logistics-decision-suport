"""
Gerador de Dados Mock V2 para Sistema Logística JIT
Inclui variáveis para predição de estoque no pátio
"""

import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path
import sys
import math

# Adicionar o diretório pai ao path para importar patterns
sys.path.append(str(Path(__file__).parent))
from patterns import PadroesNaturais

class MockDataGeneratorV2:
    """
    Versão 2: Inclui cálculos detalhados para estoque no pátio
    """
    
    def __init__(self, db_path="database/logistics.db"):
        self.db_path = Path(db_path)
        self.padroes = PadroesNaturais()
        
        # Estado interno para simular continuidade
        self.estado_anterior = None
        self.historico_chegadas = []  # Para calcular taxas
        
        # Verificar se banco existe
        if not self.db_path.exists():
            raise FileNotFoundError(f"Banco não encontrado: {self.db_path}")
            
        print(f"📊 Mock Generator V2 conectado ao banco: {self.db_path}")
    
    def conectar_banco(self):
        """Conecta ao banco SQLite"""
        return sqlite3.connect(self.db_path)
    
    def obter_padroes_hora_atual(self):
        """Obtém padrões históricos para a hora atual"""
        hora_atual = datetime.now().hour
        dia_semana = datetime.now().weekday()
        
        conn = self.conectar_banco()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT colheita_media_ton_h, moagem_media_ton_h, 
                   chegadas_media_caminhoes, velocidade_media_kmh
            FROM padroes_horarios 
            WHERE hora_dia = ? AND dia_semana = ?
        """, (hora_atual, dia_semana))
        
        resultado = cursor.fetchone()
        conn.close()
        
        if resultado:
            return {
                'colheita_esperada': resultado[0],
                'moagem_esperada': resultado[1],
                'chegadas_esperadas': resultado[2],
                'velocidade_esperada': resultado[3]
            }
        else:
            # Valores padrão se não houver histórico
            return {
                'colheita_esperada': 60,
                'moagem_esperada': 85,
                'chegadas_esperadas': 25,
                'velocidade_esperada': 55
            }
    
    def calcular_velocidade_realista(self, distancia_km, carregado=True):
        """Calcula velocidade baseada em distância e estado do caminhão"""
        padroes = self.obter_padroes_hora_atual()
        velocidade_base = padroes['velocidade_esperada']
        
        # Ajustes por condição
        if carregado:
            velocidade_base *= 0.85  # 15% mais lento carregado
        
        # Ajuste por distância
        if distancia_km > 60:
            velocidade_base *= 0.9  # Mais lento em trajetos longos
        elif distancia_km < 30:
            velocidade_base *= 1.1  # Mais rápido em trajetos curtos
        
        # Adicionar variação aleatória (±10%)
        variacao = random.uniform(0.9, 1.1)
        
        return round(velocidade_base * variacao, 1)
    
    def calcular_taxa_chegada_patio(self, frota_t3):
        """Calcula quantos caminhões chegarão ao pátio na próxima hora"""
        if not hasattr(self, 'tempos_chegada_t3'):
            self.tempos_chegada_t3 = {}
        
        chegadas_estimadas = 0
        hora_atual = datetime.now()
        
        # Para cada caminhão em T3, estimar quando chegará
        for i in range(frota_t3):
            caminhao_id = f"T3_{i}"
            
            if caminhao_id not in self.tempos_chegada_t3:
                # Novo caminhão em T3, calcular tempo restante
                tempo_restante = random.uniform(0.2, 2.0)  # horas
                self.tempos_chegada_t3[caminhao_id] = tempo_restante
            
            # Verificar se chegará na próxima hora
            if self.tempos_chegada_t3[caminhao_id] <= 1.0:
                chegadas_estimadas += 1
        
        return chegadas_estimadas
    
    def calcular_estoque_patio_detalhado(self, dados_principais):
        """Calcula variáveis detalhadas do estoque no pátio"""
        frota = dados_principais['distribuicao_frota']
        
        # Caçambas no pátio (T4)
        caçambas_patio = frota['t4_patio']
        carga_media = dados_principais['carga_media_kg'] / 1000  # em toneladas
        
        # Estoque total no pátio (todas as caçambas)
        estoque_patio_total = caçambas_patio * carga_media
        
        # Taxa de entrada REALISTA (baseada em caminhões chegando)
        # Assumir que 2-4 caminhões chegam por hora (não todos de T3!)
        caminhoes_chegando_hora = random.uniform(2, 4)
        taxa_entrada = caminhoes_chegando_hora * carga_media
        
        # Taxa de saída (moagem com variação)
        taxa_saida = dados_principais['moagem_ton_h'] * random.uniform(0.95, 1.05)
        
        # Garantir que as taxas sejam realistas
        taxa_entrada = min(taxa_entrada, 300)  # Máximo 300 ton/h
        taxa_saida = max(taxa_saida, 50)       # Mínimo 50 ton/h
        
        return {
            'estoque_patio_fisico_ton': estoque_patio_total * 0.8,
            'taxa_entrada_patio_ton_h': taxa_entrada,
            'taxa_saida_patio_ton_h': taxa_saida,
            'caçambas_fila': int(caçambas_patio * 0.4),
            'caçambas_descarga': int(caçambas_patio * 0.3),
            'taxa_chegada_caminhoes_hora': caminhoes_chegando_hora,
            'previsao_chegadas_prox_hora': int(caminhoes_chegando_hora)
        }
    
    def inserir_dados_tempo_real_v2(self, dados):
        """Insere dados na tabela principal com novas colunas"""
        conn = self.conectar_banco()
        cursor = conn.cursor()
        
        query = """
        INSERT INTO dados_tempo_real 
        (timestamp, colheitabilidade_ton_h, fazendas_ativas, moagem_ton_h, 
         capacidade_moagem, estoque_total_ton, estoque_voltando_ton, 
         estoque_indo_ton, estoque_patio_ton, estoque_patio_fisico_ton,
         taxa_entrada_patio_ton_h, taxa_saida_patio_ton_h)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        valores = (
            dados["timestamp"],
            dados["colheitabilidade_ton_h"],
            dados["fazendas_ativas"], 
            dados["moagem_ton_h"],
            dados["capacidade_moagem"],
            dados["estoque_total_ton"],
            dados["estoque_voltando_ton"],
            dados["estoque_indo_ton"],
            dados["estoque_patio_ton"],
            dados["estoque_patio_fisico_ton"],
            dados["taxa_entrada_patio_ton_h"],
            dados["taxa_saida_patio_ton_h"]
        )
        
        cursor.execute(query, valores)
        conn.commit()
        conn.close()
    
    def inserir_estado_frota_v2(self, dados):
        """Insere estado da frota com novas métricas"""
        conn = self.conectar_banco()
        cursor = conn.cursor()
        
        frota = dados["distribuicao_frota"]
        
        query = """
        INSERT INTO estado_frota 
        (timestamp, caminhoes_t1_voltando, caminhoes_t2_carregando,
         caminhoes_t3_indo, caminhoes_t4_patio, carga_media_kg,
         taxa_chegada_caminhoes_hora, previsao_chegadas_prox_hora)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        valores = (
            dados["timestamp"],
            frota["t1_voltando"],
            frota["t2_carregando"], 
            frota["t3_indo"],
            frota["t4_patio"],
            dados["carga_media_kg"],
            dados["taxa_chegada_caminhoes_hora"],
            dados["previsao_chegadas_prox_hora"]
        )
        
        cursor.execute(query, valores)
        conn.commit()
        conn.close()
    
    def inserir_caminhao_detalhado_v2(self, num_caminhoes=3):
        """Insere caminhões com velocidade e tempos realistas"""
        conn = self.conectar_banco()
        cursor = conn.cursor()
        
        for _ in range(num_caminhoes):
            caminhao = self.padroes.gerar_caminhao_detalhado()
            
            # Calcular velocidade média realista
            velocidade = self.calcular_velocidade_realista(
                caminhao["DISTANCIA_PIMS_MEDIA"], 
                carregado=(caminhao["status_caminhao"] == "T3")
            )
            
            # Simular tempos de pátio
            if caminhao["status_caminhao"] == "T4":
                hora_chegada = datetime.now() - timedelta(minutes=random.randint(10, 60))
                tempo_descarga = random.uniform(15, 45)  # minutos
            else:
                hora_chegada = None
                tempo_descarga = 0
            
            query = """
            INSERT INTO transporte_detalhado
            (timestamp, HR_ENTRADA_PIMS, NO_PLACA, T_1, T_3, T_4,
             QT_LIQUIDO_PESAGEM, DISTANCIA_PIMS_MEDIA, de_categ_oper,
             ciclo_total, status_caminhao, velocidade_media_kmh,
             tempo_descarga_min, hora_chegada_patio)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            valores = (
                datetime.now(),
                caminhao["HR_ENTRADA_PIMS"],
                caminhao["NO_PLACA"],
                caminhao["T_1"],
                caminhao["T_3"],
                caminhao["T_4"],
                caminhao["QT_LIQUIDO_PESAGEM"],
                caminhao["DISTANCIA_PIMS_MEDIA"],
                caminhao["de_categ_oper"],
                caminhao["ciclo_total"],
                caminhao["status_caminhao"],
                velocidade,
                tempo_descarga,
                hora_chegada
            )
            
            cursor.execute(query, valores)
        
        conn.commit()
        conn.close()
    
    def verificar_e_gerar_alertas(self, dados):
        """Verifica limites e gera alertas se necessário"""
        conn = self.conectar_banco()
        cursor = conn.cursor()
        
        # Buscar limites
        cursor.execute("""
            SELECT variavel, limite_inferior, limite_superior,
                   limite_critico_inferior, limite_critico_superior
            FROM limites_operacionais
        """)
        
        limites = {row[0]: row[1:] for row in cursor.fetchall()}
        
        # Verificar estoque no pátio
        if 'estoque_patio_ton' in limites:
            lim_inf, lim_sup, crit_inf, crit_sup = limites['estoque_patio_ton']
            estoque_atual = dados['estoque_patio_ton']
            
            if estoque_atual < crit_inf or estoque_atual > crit_sup:
                severidade = 'CRITICO'
            elif estoque_atual < lim_inf or estoque_atual > lim_sup:
                severidade = 'AVISO'
            else:
                severidade = None
            
            if severidade:
                # Identificar ofensor
                if estoque_atual > lim_sup:
                    if dados['colheitabilidade_ton_h'] > 70:
                        ofensor = 'COLHEITA_ALTA'
                    elif dados['moagem_ton_h'] < 85:
                        ofensor = 'MOAGEM_BAIXA'
                    else:
                        ofensor = 'ACUMULO_PATIO'
                else:
                    if dados['colheitabilidade_ton_h'] < 50:
                        ofensor = 'COLHEITA_BAIXA'
                    elif dados['moagem_ton_h'] > 100:
                        ofensor = 'MOAGEM_ALTA'
                    else:
                        ofensor = 'POUCAS_CHEGADAS'
                
                # Inserir evento
                cursor.execute("""
                    INSERT INTO eventos_sistema
                    (timestamp, tipo_evento, severidade, variavel_afetada,
                     valor_atual, limite_violado, descricao)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    dados['timestamp'],
                    'LIMITE_EXCEDIDO',
                    severidade,
                    'estoque_patio_ton',
                    estoque_atual,
                    lim_sup if estoque_atual > lim_sup else lim_inf,
                    f"Estoque no pátio {severidade.lower()}: {estoque_atual:.0f} ton - Ofensor: {ofensor}"
                ))
        
        conn.commit()
        conn.close()
    
    def gerar_ciclo_completo_v2(self):
        """Gera ciclo completo com novas variáveis para predição"""
        print(f"🔄 Gerando dados V2 às {datetime.now().strftime('%H:%M:%S')}")
        
        # Gerar dados base
        dados_principais = self.padroes.gerar_dados_completos()
        
        # Calcular detalhes do pátio
        detalhes_patio = self.calcular_estoque_patio_detalhado(dados_principais)
        
        # Adicionar novas variáveis aos dados
        dados_principais.update(detalhes_patio)
        
        # Inserir no banco
        self.inserir_dados_tempo_real_v2(dados_principais)
        self.inserir_estado_frota_v2(dados_principais)
        self.inserir_caminhao_detalhado_v2(random.randint(2, 5))
        self.inserir_colheitabilidade_detalhada(random.randint(3, 8))
        
        # Verificar alertas
        self.verificar_e_gerar_alertas(dados_principais)
        
        # Log detalhado
        print(f"   🌾 Colheitabilidade: {dados_principais['colheitabilidade_ton_h']:.1f} ton/h")
        print(f"   🏭 Moagem: {dados_principais['moagem_ton_h']:.1f} ton/h")
        print(f"   🚚 Estoque Pátio: {dados_principais['estoque_patio_ton']:.0f} ton")
        print(f"   📥 Taxa Entrada: {dados_principais['taxa_entrada_patio_ton_h']:.1f} ton/h")
        print(f"   📤 Taxa Saída: {dados_principais['taxa_saida_patio_ton_h']:.1f} ton/h")
        print(f"   🚛 Chegadas/hora: {dados_principais['taxa_chegada_caminhoes_hora']}")
        
        # Guardar estado para próximo ciclo
        self.estado_anterior = dados_principais
        
        return dados_principais
    
    def inserir_colheitabilidade_detalhada(self, num_registros=5):
        """Mantém compatibilidade com versão anterior"""
        conn = self.conectar_banco()
        cursor = conn.cursor()
        
        for _ in range(num_registros):
            colheita = self.padroes.gerar_colheitabilidade_detalhada()
            
            query = """
            INSERT INTO colheitabilidade_detalhada
            (timestamp, HORA_ELEVADOR_TIME, FAZENDA, SETOR, TON_HORA, data_origem)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            
            valores = (
                datetime.now(),
                colheita["HORA_ELEVADOR_TIME"],
                colheita["FAZENDA"],
                colheita["SETOR"],
                colheita["TON_HORA"],
                colheita["data_origem"]
            )
            
            cursor.execute(query, valores)
        
        conn.commit()
        conn.close()

def testar_gerador_v2():
    """Testa o gerador V2"""
    print("🧪 Testando Mock Data Generator V2")
    print("=" * 50)
    
    try:
        generator = MockDataGeneratorV2()
        
        # Gerar alguns ciclos
        for i in range(3):
            print(f"\n--- Ciclo {i+1} ---")
            dados = generator.gerar_ciclo_completo_v2()
            
        print("\n✅ Teste V2 concluído com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    testar_gerador_v2()