"""
Padrões REALISTAS descobertos dos dados reais para o mock
Valores dentro das zonas de segurança na maioria do tempo
"""

import random
from datetime import datetime

class PadroesNaturais:
    """
    Versão REALISTA - baseada nas zonas de segurança dos gráficos.
    Os valores ficam DENTRO dos limites seguros 80% do tempo.
    """
    
    def __init__(self):
        # FAIXAS REALISTAS baseadas nas linhas de segurança dos gráficos
        
        # COLHEITABILIDADE: zona segura entre 40-80 ton/h (gráfico simple_chart)
        self.COLHEITABILIDADE_ZONA_SEGURA_MIN = 45.0    # Acima da linha mínima
        self.COLHEITABILIDADE_ZONA_SEGURA_MAX = 75.0    # Abaixo da linha máxima
        self.COLHEITABILIDADE_MIN_ABSOLUTO = 35.0       # Raramente
        self.COLHEITABILIDADE_MAX_ABSOLUTO = 85.0       # Raramente
        
        # MOAGEM: zona segura entre 70-110 ton/h (gráfico simple_chart)
        self.MOAGEM_ZONA_SEGURA_MIN = 75.0              # Acima da linha mínima
        self.MOAGEM_ZONA_SEGURA_MAX = 105.0             # Abaixo da linha máxima
        self.MOAGEM_MIN_ABSOLUTO = 65.0                 # Raramente
        self.MOAGEM_MAX_ABSOLUTO = 120.0                # Raramente
        self.MOAGEM_CAPACIDADE = 1150.0                 # ton/h (máxima)
        
        # ESTOQUE SOBRE RODAS: zona segura entre 2100-2700 ton (gráfico simple_chart)
        self.ESTOQUE_ZONA_SEGURA_MIN = 2150.0           # Acima da linha baixa
        self.ESTOQUE_ZONA_SEGURA_MAX = 2650.0           # Abaixo da linha alta
        self.ESTOQUE_MIN_ABSOLUTO = 1900.0              # Raramente
        self.ESTOQUE_MAX_ABSOLUTO = 2900.0              # Raramente
        
        # ESTOQUE PÁTIO: zona segura entre 800-1500 ton (gráfico predição)
        self.ESTOQUE_PATIO_ZONA_SEGURA_MIN = 850.0      # Acima do limite inferior
        self.ESTOQUE_PATIO_ZONA_SEGURA_MAX = 1450.0     # Abaixo do limite superior
        self.ESTOQUE_PATIO_MIN_ABSOLUTO = 600.0         # Crítico
        self.ESTOQUE_PATIO_MAX_ABSOLUTO = 1800.0        # Crítico
        
        # CONFIGURAÇÕES DE REALISMO
        self.PROBABILIDADE_ZONA_SEGURA = 0.85           # 85% do tempo na zona segura
        self.VARIACAO_MAXIMA_POR_CICLO = 0.05           # Máximo 5% de variação por ciclo
        
        # Outras configurações mantidas
        self.FROTA_TOTAL = 46
        self.CARGA_MEDIA_MIN = 65000        # kg por caminhão
        self.CARGA_MEDIA_MAX = 75000        # kg por caminhão
        
        # Faixas de tempos mais estáveis
        self.T1_MIN = 1.0    # horas
        self.T1_MAX = 3.0    # horas
        self.T2_FIXO = 2.0   # horas (carregamento)
        self.T3_MIN = 1.5    # horas  
        self.T3_MAX = 6.0    # horas
        self.T4_MIN = 0.5    # horas
        self.T4_MAX = 4.0    # horas
        
        # Distâncias mais realistas
        self.DISTANCIA_MIN = 25.0    # km
        self.DISTANCIA_MAX = 75.0    # km
        
        # Tipos de caminhão encontrados
        self.TIPOS_CAMINHAO = [
            "(T) Caminhao Cav Mec",
            "Rodotrem", 
            "Treminhão",
            "Bi-trem"
        ]
        
        # Fazendas exemplo
        self.FAZENDAS = [
            "Fazenda Santa Rita", "Fazenda Boa Vista", "Fazenda São João",
            "Fazenda Esperança", "Fazenda Progresso", "Fazenda União",
            "Fazenda Aurora", "Fazenda Vitória", "Fazenda Harmonia"
        ]
        
        self.SETORES = ["A", "B", "C", "D", "E", "F", "G", "H"]
        
        # Estado anterior para suavizar transições
        self.estado_anterior = None
    
    def _gerar_valor_realista(self, zona_min, zona_max, absoluto_min, absoluto_max, valor_anterior=None):
        """
        Gera valor realista que fica na zona segura 85% do tempo
        """
        # Se temos valor anterior, aplicar variação suave
        if valor_anterior is not None:
            # Variação máxima por ciclo: 5%
            variacao_max = valor_anterior * self.VARIACAO_MAXIMA_POR_CICLO
            
            # 90% do tempo: variação pequena
            if random.random() < 0.9:
                variacao = random.uniform(-variacao_max, variacao_max)
                novo_valor = valor_anterior + variacao
                
                # Garantir que está dentro dos limites absolutos
                novo_valor = max(absoluto_min, min(absoluto_max, novo_valor))
                return round(novo_valor, 2)
        
        # Decidir se fica na zona segura (85% do tempo)
        if random.random() < self.PROBABILIDADE_ZONA_SEGURA:
            # Zona segura
            return round(random.uniform(zona_min, zona_max), 2)
        else:
            # Fora da zona segura (15% do tempo)
            if random.random() < 0.5:
                # Abaixo da zona segura
                return round(random.uniform(absoluto_min, zona_min), 2)
            else:
                # Acima da zona segura
                return round(random.uniform(zona_max, absoluto_max), 2)
    
    def gerar_colheitabilidade(self):
        """Gera colheitabilidade REALISTA - na zona segura 85% do tempo"""
        valor_anterior = None
        if self.estado_anterior:
            valor_anterior = self.estado_anterior.get('colheitabilidade_ton_h')
        
        return self._gerar_valor_realista(
            self.COLHEITABILIDADE_ZONA_SEGURA_MIN,
            self.COLHEITABILIDADE_ZONA_SEGURA_MAX,
            self.COLHEITABILIDADE_MIN_ABSOLUTO,
            self.COLHEITABILIDADE_MAX_ABSOLUTO,
            valor_anterior
        )
    
    def gerar_moagem(self):
        """Gera moagem REALISTA - na zona segura 85% do tempo"""
        valor_anterior = None
        if self.estado_anterior:
            valor_anterior = self.estado_anterior.get('moagem_ton_h')
        
        return self._gerar_valor_realista(
            self.MOAGEM_ZONA_SEGURA_MIN,
            self.MOAGEM_ZONA_SEGURA_MAX,
            self.MOAGEM_MIN_ABSOLUTO,
            self.MOAGEM_MAX_ABSOLUTO,
            valor_anterior
        )
    
    def gerar_estoque_total_base(self):
        """Gera estoque total REALISTA - na zona segura 85% do tempo"""
        valor_anterior = None
        if self.estado_anterior:
            valor_anterior = self.estado_anterior.get('estoque_total_ton')
        
        return self._gerar_valor_realista(
            self.ESTOQUE_ZONA_SEGURA_MIN,
            self.ESTOQUE_ZONA_SEGURA_MAX,
            self.ESTOQUE_MIN_ABSOLUTO,
            self.ESTOQUE_MAX_ABSOLUTO,
            valor_anterior
        )
    
    def gerar_estoque_patio_base(self):
        """Gera estoque pátio REALISTA - na zona segura 85% do tempo"""
        valor_anterior = None
        if self.estado_anterior:
            valor_anterior = self.estado_anterior.get('estoque_patio_ton')
        
        return self._gerar_valor_realista(
            self.ESTOQUE_PATIO_ZONA_SEGURA_MIN,
            self.ESTOQUE_PATIO_ZONA_SEGURA_MAX,
            self.ESTOQUE_PATIO_MIN_ABSOLUTO,
            self.ESTOQUE_PATIO_MAX_ABSOLUTO,
            valor_anterior
        )
    
    def gerar_distribuicao_frota_estavel(self):
        """
        Distribui a frota de forma mais ESTÁVEL
        Mudanças graduais, não bruscas
        """
        if not self.estado_anterior:
            # Primeira vez - distribuição equilibrada
            t2_fixo = 8
            t1 = 12
            t4 = 7
            t3 = self.FROTA_TOTAL - t2_fixo - t1 - t4  # 19
        else:
            # Usar distribuição anterior com pequenos ajustes
            frota_anterior = self.estado_anterior.get('distribuicao_frota', {})
            
            t1_anterior = frota_anterior.get('t1_voltando', 12)
            t2_anterior = frota_anterior.get('t2_carregando', 8)
            t3_anterior = frota_anterior.get('t3_indo', 19)
            t4_anterior = frota_anterior.get('t4_patio', 7)
            
            # Variações pequenas (máximo ±2 caminhões por vez)
            t1 = max(8, min(16, t1_anterior + random.randint(-2, 2)))
            t2_fixo = max(6, min(10, t2_anterior + random.randint(-1, 1)))
            t4 = max(5, min(10, t4_anterior + random.randint(-2, 2)))
            t3 = self.FROTA_TOTAL - t2_fixo - t1 - t4
            
            # Garantir que T3 fique razoável
            if t3 < 10:
                t3 = 10
                t1 = self.FROTA_TOTAL - t2_fixo - t3 - t4
        
        return {
            "t1_voltando": max(1, t1),
            "t2_carregando": max(1, t2_fixo),
            "t3_indo": max(1, t3),
            "t4_patio": max(1, t4)
        }
    
    def calcular_estoque_detalhado_realista(self, distribuicao_frota, estoque_total_desejado):
        """
        Calcula estoque baseado na distribuição da frota
        Mas respeitando o estoque total desejado
        """
        carga_media = random.randint(self.CARGA_MEDIA_MIN, self.CARGA_MEDIA_MAX)
        
        # Calcular proporções realistas
        total_caminhoes = sum(distribuicao_frota.values())
        
        # Estoque pátio com valor realista específico
        estoque_patio = self.gerar_estoque_patio_base()
        
        # Distribuir o restante entre T1 e T3
        estoque_restante = estoque_total_desejado - estoque_patio
        
        # Proporção baseada nos caminhões
        prop_t1 = distribuicao_frota["t1_voltando"] / (distribuicao_frota["t1_voltando"] + distribuicao_frota["t3_indo"])
        
        estoque_voltando = estoque_restante * prop_t1
        estoque_indo = estoque_restante * (1 - prop_t1)
        
        return {
            "estoque_voltando": max(100, estoque_voltando),    # Mínimo 100 ton
            "estoque_indo": max(100, estoque_indo),            # Mínimo 100 ton  
            "estoque_patio": estoque_patio,
            "carga_media": carga_media
        }
    
    def gerar_placa(self):
        """Gera placa realística"""
        letras = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))
        numeros = random.randint(1000, 9999)
        return f"{letras}{numeros}"
    
    def gerar_tempos_transporte_estaveis(self):
        """Gera tempos mais estáveis"""
        return {
            "T_1": round(random.uniform(self.T1_MIN, self.T1_MAX), 2),
            "T_3": round(random.uniform(self.T3_MIN, self.T3_MAX), 2), 
            "T_4": round(random.uniform(self.T4_MIN, self.T4_MAX), 2)
        }
    
    def gerar_caminhao_detalhado(self):
        """Gera dados completos de um caminhão (versão estável)"""
        tempos = self.gerar_tempos_transporte_estaveis()
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
        """Gera dados detalhados de colheita (versão estável)"""
        # Colheitabilidade individual um pouco menor que a geral
        ton_hora = self.gerar_colheitabilidade() * random.uniform(0.3, 0.8)
        
        return {
            "HORA_ELEVADOR_TIME": datetime.now(),
            "FAZENDA": random.choice(self.FAZENDAS),
            "SETOR": random.choice(self.SETORES),
            "TON_HORA": round(ton_hora, 2),
            "data_origem": datetime.now().date()
        }
    
    def gerar_dados_completos(self):
        """
        Gera um conjunto completo de dados REALISTAS
        Valores ficam na zona segura 85% do tempo
        """
        # Dados principais das 3 curvas
        colheitabilidade = self.gerar_colheitabilidade()
        moagem = self.gerar_moagem()
        estoque_total_desejado = self.gerar_estoque_total_base()
        
        # Distribuição da frota (estável)
        frota = self.gerar_distribuicao_frota_estavel()
        
        # Calcular estoque detalhado
        estoque_detalhado = self.calcular_estoque_detalhado_realista(frota, estoque_total_desejado)
        
        # Montar dados finais
        dados = {
            "timestamp": datetime.now(),
            "colheitabilidade_ton_h": colheitabilidade,
            "fazendas_ativas": random.randint(10, 14),  # Mais estável
            "moagem_ton_h": moagem,
            "capacidade_moagem": self.MOAGEM_CAPACIDADE,
            "estoque_total_ton": estoque_detalhado["estoque_voltando"] + estoque_detalhado["estoque_indo"] + estoque_detalhado["estoque_patio"],
            "estoque_voltando_ton": estoque_detalhado["estoque_voltando"],
            "estoque_indo_ton": estoque_detalhado["estoque_indo"], 
            "estoque_patio_ton": estoque_detalhado["estoque_patio"],
            "distribuicao_frota": frota,
            "carga_media_kg": estoque_detalhado["carga_media"]
        }
        
        # Guardar estado para próximo ciclo
        self.estado_anterior = dados.copy()
        
        return dados
    
    def aplicar_influencia_horario(self, dados):
        """
        Aplica influências sutis baseadas no horário
        """
        hora_atual = datetime.now().hour
        
        # Período noturno (22h-6h): colheita reduzida
        if 22 <= hora_atual or hora_atual <= 6:
            dados["colheitabilidade_ton_h"] *= random.uniform(0.7, 0.9)
        
        # Período de pico (8h-16h): moagem mais intensa
        elif 8 <= hora_atual <= 16:
            dados["moagem_ton_h"] *= random.uniform(1.0, 1.1)
        
        # Arredondar valores
        dados["colheitabilidade_ton_h"] = round(dados["colheitabilidade_ton_h"], 2)
        dados["moagem_ton_h"] = round(dados["moagem_ton_h"], 2)
        
        return dados