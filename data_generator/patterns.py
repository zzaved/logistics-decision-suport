"""
Padrões descobertos dos dados reais para o mock
SEM REGRAS FIXAS - apenas faixas naturais de variação
"""

import random
from datetime import datetime

class PadroesNaturais:
    """
    Baseado na análise real dos dados, mas SEM regras fixas.
    Os valores podem variar naturalmente dentro das faixas descobertas.
    """
    
    def __init__(self):
        # Faixas naturais descobertas (não regras!)
        self.COLHEITABILIDADE_MIN = 30.0    # ton/h
        self.COLHEITABILIDADE_MAX = 80.0    # ton/h
        
        self.MOAGEM_MIN = 50.0              # ton/h  
        self.MOAGEM_MAX = 200.0             # ton/h
        self.MOAGEM_CAPACIDADE = 1150.0     # ton/h (máxima)
        
        self.ESTOQUE_MIN = 1800.0           # ton
        self.ESTOQUE_MAX = 2800.0           # ton
        
        self.FROTA_TOTAL = 46               # caminhões
        self.CARGA_MEDIA_MIN = 60000        # kg por caminhão
        self.CARGA_MEDIA_MAX = 80000        # kg por caminhão
        
        # Faixas de tempos descobertas
        self.T1_MIN = 0.5    # horas
        self.T1_MAX = 4.0    # horas
        self.T2_FIXO = 2.0   # horas (carregamento)
        self.T3_MIN = 1.0    # horas  
        self.T3_MAX = 8.0    # horas
        self.T4_MIN = 0.3    # horas
        self.T4_MAX = 8.0    # horas
        
        # Distâncias descobertas
        self.DISTANCIA_MIN = 20.0    # km
        self.DISTANCIA_MAX = 90.0    # km
        
        # Tipos de caminhão encontrados
        self.TIPOS_CAMINHAO = [
            "(T) Caminhao Cav Mec",
            "Rodotrem", 
            "Treminhão",
            "Bi-trem"
        ]
        
        # Fazendas exemplo (baseadas nos dados)
        self.FAZENDAS = [
            "Fazenda Santa Rita", "Fazenda Boa Vista", "Fazenda São João",
            "Fazenda Esperança", "Fazenda Progresso", "Fazenda União",
            "Fazenda Aurora", "Fazenda Vitória", "Fazenda Harmonia"
        ]
        
        self.SETORES = ["A", "B", "C", "D", "E", "F", "G", "H"]
    
    def gerar_colheitabilidade(self):
        """Gera colheitabilidade natural - SEM regras por hora"""
        return round(random.uniform(self.COLHEITABILIDADE_MIN, self.COLHEITABILIDADE_MAX), 2)
    
    def gerar_moagem(self):
        """Gera moagem natural - SEM regras por hora"""
        return round(random.uniform(self.MOAGEM_MIN, self.MOAGEM_MAX), 2)
    
    def gerar_estoque_total(self):
        """Gera estoque total natural"""
        return round(random.uniform(self.ESTOQUE_MIN, self.ESTOQUE_MAX), 1)
    
    def gerar_distribuicao_frota(self):
        """
        Distribui os 46 caminhões entre T1, T2, T3, T4
        Baseado nas proporções descobertas, mas com variação natural
        """
        # Proporções aproximadas descobertas (mas podem variar!)
        t2_fixo = random.randint(6, 10)      # T2 sempre uns 8 
        restante = self.FROTA_TOTAL - t2_fixo
        
        # Distribuir o restante naturalmente
        t1 = random.randint(8, 16)
        t4 = random.randint(3, 9) 
        t3 = restante - t1 - t4
        
        # Garantir que dê 46 total
        if t3 < 5:
            t3 = 5
            t1 = restante - t3 - t4
            
        return {
            "t1_voltando": max(1, t1),
            "t2_carregando": t2_fixo,
            "t3_indo": max(1, t3),
            "t4_patio": max(1, t4)
        }
    
    def calcular_estoque_detalhado(self, distribuicao_frota):
        """Calcula estoque baseado na distribuição da frota"""
        carga_media = random.randint(self.CARGA_MEDIA_MIN, self.CARGA_MEDIA_MAX)
        
        return {
            "estoque_voltando": distribuicao_frota["t1_voltando"] * carga_media // 1000,  # em ton
            "estoque_indo": distribuicao_frota["t3_indo"] * carga_media // 1000,          # em ton  
            "estoque_patio": distribuicao_frota["t4_patio"] * carga_media // 1000         # em ton
        }
    
    def gerar_placa(self):
        """Gera placa realística"""
        letras = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))
        numeros = random.randint(1000, 9999)
        return f"{letras}{numeros}"
    
    def gerar_tempos_transporte(self):
        """Gera tempos T1, T3, T4 naturais"""
        return {
            "T_1": round(random.uniform(self.T1_MIN, self.T1_MAX), 2),
            "T_3": round(random.uniform(self.T3_MIN, self.T3_MAX), 2), 
            "T_4": round(random.uniform(self.T4_MIN, self.T4_MAX), 2)
        }
    
    def gerar_caminhao_detalhado(self):
        """Gera dados completos de um caminhão (como chegam do PIMS)"""
        tempos = self.gerar_tempos_transporte()
        carga = random.randint(self.CARGA_MEDIA_MIN, self.CARGA_MEDIA_MAX)
        
        return {
            "HR_ENTRADA_PIMS": datetime.now(),
            "NO_PLACA": self.gerar_placa(),
            "T_1": tempos["T_1"],
            "T_3": tempos["T_3"], 
            "T_4": tempos["T_4"],
            "QT_LIQUIDO_PESAGEM": carga,
            "DISTANCIA_PIMS_MEDIA": round(random.uniform(self.DISTANCIA_MIN, self.DISTANCIA_MAX), 1),
            "de_categ_oper": random.choice(self.TIPOS_CAMINHAO),
            "ciclo_total": tempos["T_1"] + self.T2_FIXO + tempos["T_3"] + tempos["T_4"],
            "status_caminhao": random.choice(["T1", "T2", "T3", "T4"])
        }
    
    def gerar_colheitabilidade_detalhada(self):
        """Gera dados detalhados de colheita (como chegam do cubo)"""
        return {
            "HORA_ELEVADOR_TIME": datetime.now(),
            "FAZENDA": random.choice(self.FAZENDAS),
            "SETOR": random.choice(self.SETORES),
            "TON_HORA": self.gerar_colheitabilidade(),
            "data_origem": datetime.now().date()
        }
    
    def gerar_dados_completos(self):
        """
        Gera um conjunto completo de dados como chegaria em tempo real
        SEM REGRAS FIXAS - apenas variação natural
        """
        # Distribuição da frota
        frota = self.gerar_distribuicao_frota()
        estoque_detalhado = self.calcular_estoque_detalhado(frota)
        
        # Dados principais das 3 curvas
        colheitabilidade = self.gerar_colheitabilidade()
        moagem = self.gerar_moagem()
        estoque_total = sum(estoque_detalhado.values())
        
        return {
            "timestamp": datetime.now(),
            "colheitabilidade_ton_h": colheitabilidade,
            "fazendas_ativas": random.randint(8, 15),
            "moagem_ton_h": moagem,
            "capacidade_moagem": self.MOAGEM_CAPACIDADE,
            "estoque_total_ton": estoque_total,
            "estoque_voltando_ton": estoque_detalhado["estoque_voltando"],
            "estoque_indo_ton": estoque_detalhado["estoque_indo"], 
            "estoque_patio_ton": estoque_detalhado["estoque_patio"],
            "distribuicao_frota": frota,
            "carga_media_kg": random.randint(self.CARGA_MEDIA_MIN, self.CARGA_MEDIA_MAX)
        }