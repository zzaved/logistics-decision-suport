"""
Gerador de Dados Mock V2 REALISTA para Sistema Logística JIT
Dados ficam na zona de segurança 85% do tempo, com variações suaves
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
    Versão 2 REALISTA: Dados mais estáveis e dentro das zonas de segurança
    """
    
    def __init__(self, db_path="database/logistics.db"):
        self.db_path = Path(db_path)
        self.padroes = PadroesNaturais()
        
        # Estado interno para suavização
        self.estado_anterior = None
        self.historico_chegadas = []
        self.taxa_entrada_anterior = None
        self.taxa_saida_anterior = None
        
        # Verificar se banco existe
        if not self.db_path.exists():
            raise FileNotFoundError(f"Banco não encontrado: {self.db_path}")
            
        print(f"📊 Mock Generator V2 REALISTA conectado ao banco: {self.db_path}")
        print(f"🎯 Configurado para zona segura 85% do tempo")
    
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
            # Valores padrão REALISTAS
            return {
                'colheita_esperada': 60,
                'moagem_esperada': 85,
                'chegadas_esperadas': 3,  # Mais realista
                'velocidade_esperada': 55
            }
    
    def calcular_velocidade_realista(self, distancia_km, carregado=True):
        """Calcula velocidade baseada em distância e estado do caminhão"""
        padroes = self.obter_padroes_hora_atual()
        velocidade_base = padroes['velocidade_esperada']
        
        # Ajustes por condição (mais suaves)
        if carregado:
            velocidade_base *= random.uniform(0.85, 0.90)  # 10-15% mais lento
        
        # Ajuste por distância (mais suave)
        if distancia_km > 60:
            velocidade_base *= random.uniform(0.90, 0.95)
        elif distancia_km < 30:
            velocidade_base *= random.uniform(1.05, 1.10)
        
        # Variação menor (±5%)
        variacao = random.uniform(0.95, 1.05)
        
        return round(velocidade_base * variacao, 1)
    
    def calcular_estoque_patio_detalhado(self, dados_principais):
        """
        Calcula variáveis detalhadas do estoque no pátio
        VERSÃO REALISTA - valores mais estáveis e coerentes
        """
        frota = dados_principais['distribuicao_frota']
        
        # Usar o estoque pátio já calculado de forma realista
        estoque_patio_atual = dados_principais['estoque_patio_ton']
        
        # Taxa de entrada REALISTA E SUAVE
        # Basear na colheitabilidade com fator de conversão
        colheita_atual = dados_principais['colheitabilidade_ton_h']
        
        # Taxa de entrada = 15-25% da colheitabilidade (realista)
        fator_conversao = random.uniform(0.15, 0.25)
        taxa_entrada = colheita_atual * fator_conversao
        
        # Suavizar se temos valor anterior
        if hasattr(self, 'taxa_entrada_anterior') and self.taxa_entrada_anterior:
            # Variação máxima de 10% por ciclo
            variacao_max = self.taxa_entrada_anterior * 0.1
            taxa_entrada = self.taxa_entrada_anterior + random.uniform(-variacao_max, variacao_max)
        
        # Taxa de saída = moagem com pequena variação
        taxa_saida = dados_principais['moagem_ton_h'] * random.uniform(0.98, 1.02)
        
        # Suavizar taxa de saída também
        if hasattr(self, 'taxa_saida_anterior') and self.taxa_saida_anterior:
            variacao_max = self.taxa_saida_anterior * 0.05
            taxa_saida = self.taxa_saida_anterior + random.uniform(-variacao_max, variacao_max)
        
        # Garantir limites realistas
        taxa_entrada = max(10, min(200, taxa_entrada))   # Entre 10-200 ton/h
        taxa_saida = max(40, min(150, taxa_saida))       # Entre 40-150 ton/h
        
        # Calcular chegadas de caminhões baseado na taxa de entrada
        carga_media_ton = dados_principais['carga_media_kg'] / 1000
        caminhoes_chegando_hora = taxa_entrada / carga_media_ton if carga_media_ton > 0 else 3
        caminhoes_chegando_hora = max(1, min(6, caminhoes_chegando_hora))  # Entre 1-6 caminhões/h
        
        # Guardar valores para suavização
        self.taxa_entrada_anterior = taxa_entrada
        self.taxa_saida_anterior = taxa_saida
        
        return {
            'estoque_patio_fisico_ton': estoque_patio_atual * random.uniform(0.85, 0.95),
            'taxa_entrada_patio_ton_h': round(taxa_entrada, 1),
            'taxa_saida_patio_ton_h': round(taxa_saida, 1),
            'caçambas_fila': int(frota['t4_patio'] * random.uniform(0.3, 0.5)),
            'caçambas_descarga': int(frota['t4_patio'] * random.uniform(0.2, 0.4)),
            'taxa_chegada_caminhoes_hora': round(caminhoes_chegando_hora, 1),
            'previsao_chegadas_prox_hora': int(round(caminhoes_chegando_hora))
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
            
            # Simular tempos de pátio mais realistas
            if caminhao["status_caminhao"] == "T4":
                hora_chegada = datetime.now() - timedelta(minutes=random.randint(15, 90))
                tempo_descarga = random.uniform(20, 60)  # minutos mais realistas
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
                # Identificar ofensor com mais precisão
                taxa_entrada = dados.get('taxa_entrada_patio_ton_h', 0)
                taxa_saida = dados.get('taxa_saida_patio_ton_h', 0)
                balanco = taxa_entrada - taxa_saida
                
                if estoque_atual > lim_sup:
                    if balanco > 10:  # Entrada muito maior que saída
                        if dados['colheitabilidade_ton_h'] > 65:
                            ofensor = 'COLHEITA_ALTA'
                        else:
                            ofensor = 'CHEGADAS_EXCESSIVAS'
                    elif dados['moagem_ton_h'] < 80:
                        ofensor = 'MOAGEM_BAIXA'
                    else:
                        ofensor = 'ACUMULO_PATIO'
                else:
                    if balanco < -10:  # Saída muito maior que entrada
                        if dados['moagem_ton_h'] > 100:
                            ofensor = 'MOAGEM_ALTA'
                        else:
                            ofensor = 'POUCAS_CHEGADAS'
                    elif dados['colheitabilidade_ton_h'] < 50:
                        ofensor = 'COLHEITA_BAIXA'
                    else:
                        ofensor = 'BAIXA_DISPONIBILIDADE'
                
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
                    f"Estoque pátio {severidade.lower()}: {estoque_atual:.0f} ton - Balanço: {balanco:+.1f} ton/h - Ofensor: {ofensor}"
                ))
        
        conn.commit()
        conn.close()
    
    def gerar_ciclo_completo_v2(self):
        """Gera ciclo completo com dados REALISTAS"""
        print(f"🔄 Gerando dados REALISTAS às {datetime.now().strftime('%H:%M:%S')}")
        
        # Gerar dados base REALISTAS
        dados_principais = self.padroes.gerar_dados_completos()
        
        # Aplicar influências do horário
        dados_principais = self.padroes.aplicar_influencia_horario(dados_principais)
        
        # Calcular detalhes do pátio REALISTAS
        detalhes_patio = self.calcular_estoque_patio_detalhado(dados_principais)
        
        # Adicionar novas variáveis aos dados
        dados_principais.update(detalhes_patio)
        
        # Inserir no banco
        self.inserir_dados_tempo_real_v2(dados_principais)
        self.inserir_estado_frota_v2(dados_principais)
        self.inserir_caminhao_detalhado_v2(random.randint(2, 4))  # Menos variação
        self.inserir_colheitabilidade_detalhada(random.randint(4, 6))  # Menos variação
        
        # Verificar alertas
        self.verificar_e_gerar_alertas(dados_principais)
        
        # Log mais detalhado sobre zona de segurança
        colheita = dados_principais['colheitabilidade_ton_h']
        moagem = dados_principais['moagem_ton_h']
        estoque = dados_principais['estoque_total_ton']
        estoque_patio = dados_principais['estoque_patio_ton']
        
        # Verificar se estão nas zonas seguras
        colheita_segura = 45 <= colheita <= 75
        moagem_segura = 75 <= moagem <= 105
        estoque_seguro = 2150 <= estoque <= 2650
        patio_seguro = 850 <= estoque_patio <= 1450
        
        status_seguranca = "🟢" if all([colheita_segura, moagem_segura, estoque_seguro, patio_seguro]) else "🟡"
        
        print(f"   {status_seguranca} Zona Segurança: C={colheita_segura} M={moagem_segura} E={estoque_seguro} P={patio_seguro}")
        print(f"   🌾 Colheitabilidade: {colheita:.1f} ton/h {'✅' if colheita_segura else '⚠️'}")
        print(f"   🏭 Moagem: {moagem:.1f} ton/h {'✅' if moagem_segura else '⚠️'}")
        print(f"   🚚 Estoque Total: {estoque:.0f} ton {'✅' if estoque_seguro else '⚠️'}")
        print(f"   🚛 Estoque Pátio: {estoque_patio:.0f} ton {'✅' if patio_seguro else '⚠️'}")
        print(f"   📥 Taxa Entrada: {dados_principais['taxa_entrada_patio_ton_h']:.1f} ton/h")
        print(f"   📤 Taxa Saída: {dados_principais['taxa_saida_patio_ton_h']:.1f} ton/h")
        print(f"   ⚖️ Balanço: {dados_principais['taxa_entrada_patio_ton_h'] - dados_principais['taxa_saida_patio_ton_h']:+.1f} ton/h")
        
        # Guardar estado para próximo ciclo
        self.estado_anterior = dados_principais
        
        return dados_principais
    
    def inserir_colheitabilidade_detalhada(self, num_registros=5):
        """Insere dados de colheitabilidade por fazenda"""
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
    
    def limpar_dados_antigos(self, horas=4):
        """Remove dados antigos do banco (mantém últimas X horas)"""
        limite = datetime.now() - timedelta(hours=horas)
        
        conn = self.conectar_banco()
        cursor = conn.cursor()
        
        tabelas = [
            'dados_tempo_real',
            'estado_frota', 
            'transporte_detalhado',
            'colheitabilidade_detalhada'
        ]
        
        total_removidos = 0
        for tabela in tabelas:
            cursor.execute(f"""
                DELETE FROM {tabela} 
                WHERE timestamp < ?
            """, (limite,))
            total_removidos += cursor.rowcount
        
        conn.commit()
        conn.close()
        
        if total_removidos > 0:
            print(f"🧹 Limpeza: {total_removidos} registros antigos removidos")

def testar_gerador_v2_realista():
    """Testa o gerador V2 REALISTA"""
    print("🧪 Testando Mock Data Generator V2 REALISTA")
    print("🎯 Dados ficam na zona segura 85% do tempo")
    print("=" * 60)
    
    try:
        generator = MockDataGeneratorV2()
        
        # Estatísticas de teste
        total_ciclos = 10
        dentro_zona = 0
        
        # Gerar vários ciclos para testar
        for i in range(total_ciclos):
            print(f"\n--- Ciclo {i+1}/{total_ciclos} ---")
            dados = generator.gerar_ciclo_completo_v2()
            
            # Verificar se está na zona segura
            colheita = dados['colheitabilidade_ton_h']
            moagem = dados['moagem_ton_h']
            estoque = dados['estoque_total_ton']
            estoque_patio = dados['estoque_patio_ton']
            
            na_zona = (45 <= colheita <= 75 and 
                      75 <= moagem <= 105 and 
                      2150 <= estoque <= 2650 and 
                      850 <= estoque_patio <= 1450)
            
            if na_zona:
                dentro_zona += 1
        
        # Estatísticas finais
        percentual_zona = (dentro_zona / total_ciclos) * 100
        print(f"\n📊 RESULTADO DO TESTE:")
        print(f"   Ciclos na zona segura: {dentro_zona}/{total_ciclos} ({percentual_zona:.0f}%)")
        print(f"   Meta: 85% na zona segura")
        print(f"   Status: {'✅ APROVADO' if percentual_zona >= 70 else '⚠️ AJUSTAR'}")
        
        print("\n✅ Teste V2 REALISTA concluído!")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    testar_gerador_v2_realista()