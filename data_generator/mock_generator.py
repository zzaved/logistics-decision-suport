"""
Gerador de Dados Mock para Sistema Logística JIT
Simula dados chegando em tempo real como se fossem da usina
"""

import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Adicionar o diretório pai ao path para importar patterns
sys.path.append(str(Path(__file__).parent))
from patterns import PadroesNaturais

class MockDataGenerator:
    """
    Gera dados mock baseados nos padrões reais descobertos
    SEM regras fixas - apenas simulação natural
    """
    
    def __init__(self, db_path="database/logistics.db"):
        self.db_path = Path(db_path)
        self.padroes = PadroesNaturais()
        
        # Verificar se banco existe
        if not self.db_path.exists():
            raise FileNotFoundError(f"Banco não encontrado: {self.db_path}")
            
        print(f"📊 Mock Generator conectado ao banco: {self.db_path}")
    
    def conectar_banco(self):
        """Conecta ao banco SQLite"""
        return sqlite3.connect(self.db_path)
    
    def inserir_dados_tempo_real(self, dados):
        """Insere dados na tabela principal das 3 curvas"""
        conn = self.conectar_banco()
        cursor = conn.cursor()
        
        query = """
        INSERT INTO dados_tempo_real 
        (timestamp, colheitabilidade_ton_h, fazendas_ativas, moagem_ton_h, 
         capacidade_moagem, estoque_total_ton, estoque_voltando_ton, 
         estoque_indo_ton, estoque_patio_ton)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            dados["estoque_patio_ton"]
        )
        
        cursor.execute(query, valores)
        conn.commit()
        conn.close()
    
    def inserir_estado_frota(self, dados):
        """Insere estado atual da frota"""
        conn = self.conectar_banco()
        cursor = conn.cursor()
        
        frota = dados["distribuicao_frota"]
        
        query = """
        INSERT INTO estado_frota 
        (timestamp, caminhoes_t1_voltando, caminhoes_t2_carregando,
         caminhoes_t3_indo, caminhoes_t4_patio, carga_media_kg)
        VALUES (?, ?, ?, ?, ?, ?)
        """
        
        valores = (
            dados["timestamp"],
            frota["t1_voltando"],
            frota["t2_carregando"], 
            frota["t3_indo"],
            frota["t4_patio"],
            dados["carga_media_kg"]
        )
        
        cursor.execute(query, valores)
        conn.commit()
        conn.close()
    
    def inserir_caminhao_detalhado(self, num_caminhoes=3):
        """Insere alguns caminhões detalhados (simula chegadas)"""
        conn = self.conectar_banco()
        cursor = conn.cursor()
        
        for _ in range(num_caminhoes):
            caminhao = self.padroes.gerar_caminhao_detalhado()
            
            query = """
            INSERT INTO transporte_detalhado
            (timestamp, HR_ENTRADA_PIMS, NO_PLACA, T_1, T_3, T_4,
             QT_LIQUIDO_PESAGEM, DISTANCIA_PIMS_MEDIA, de_categ_oper,
             ciclo_total, status_caminhao)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                caminhao["status_caminhao"]
            )
            
            cursor.execute(query, valores)
        
        conn.commit()
        conn.close()
    
    def inserir_colheitabilidade_detalhada(self, num_registros=5):
        """Insere dados detalhados de colheita"""
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
    
    def gerar_ciclo_completo(self):
        """
        Gera um ciclo completo de dados como chegaria da usina
        Simula dados chegando em tempo real a cada 10 segundos
        """
        print(f"🔄 Gerando dados às {datetime.now().strftime('%H:%M:%S')}")
        
        # Gerar dados principais das 3 curvas
        dados_principais = self.padroes.gerar_dados_completos()
        
        # Inserir no banco
        self.inserir_dados_tempo_real(dados_principais)
        self.inserir_estado_frota(dados_principais) 
        self.inserir_caminhao_detalhado(random.randint(2, 5))
        self.inserir_colheitabilidade_detalhada(random.randint(3, 8))
        
        # Log do que foi gerado
        print(f"   🌾 Colheitabilidade: {dados_principais['colheitabilidade_ton_h']:.1f} ton/h")
        print(f"   🏭 Moagem: {dados_principais['moagem_ton_h']:.1f} ton/h")
        print(f"   🚚 Estoque: {dados_principais['estoque_total_ton']:.0f} ton")
        print(f"   👥 Frota: T1={dados_principais['distribuicao_frota']['t1_voltando']} | T2={dados_principais['distribuicao_frota']['t2_carregando']} | T3={dados_principais['distribuicao_frota']['t3_indo']} | T4={dados_principais['distribuicao_frota']['t4_patio']}")
        
        return dados_principais
    
    def limpar_dados_antigos(self, horas=24):
        """Remove dados mais antigos que X horas (manter banco pequeno)"""
        conn = self.conectar_banco()
        cursor = conn.cursor()
        
        limite = datetime.now() - timedelta(hours=horas)
        
        tabelas = [
            'dados_tempo_real',
            'estado_frota', 
            'transporte_detalhado',
            'colheitabilidade_detalhada'
        ]
        
        for tabela in tabelas:
            cursor.execute(f"DELETE FROM {tabela} WHERE timestamp < ?", (limite,))
        
        conn.commit()
        conn.close()
        
        print(f"🧹 Dados antigos removidos (mais de {horas}h)")
    
    def status_banco(self):
        """Mostra status atual do banco"""
        conn = self.conectar_banco()
        cursor = conn.cursor()
        
        tabelas = [
            'dados_tempo_real',
            'estado_frota',
            'transporte_detalhado', 
            'colheitabilidade_detalhada'
        ]
        
        print("📊 Status do Banco:")
        for tabela in tabelas:
            cursor.execute(f"SELECT COUNT(*) FROM {tabela}")
            count = cursor.fetchone()[0]
            
            # Último registro
            cursor.execute(f"SELECT timestamp FROM {tabela} ORDER BY timestamp DESC LIMIT 1")
            ultimo = cursor.fetchone()
            ultimo_str = ultimo[0] if ultimo else "Nenhum"
            
            print(f"   {tabela}: {count} registros (último: {ultimo_str})")
        
        conn.close()

def testar_gerador():
    """Testa o gerador criando alguns dados"""
    print("🧪 Testando Mock Data Generator")
    print("=" * 50)
    
    try:
        generator = MockDataGenerator()
        
        # Status inicial
        generator.status_banco()
        print()
        
        # Gerar alguns ciclos de teste
        for i in range(3):
            dados = generator.gerar_ciclo_completo()
            print()
        
        # Status final
        generator.status_banco()
        
        print("\n✅ Teste concluído com sucesso!")
        print("🎯 Próximo passo: python data_generator/scheduler.py")
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")

if __name__ == "__main__":
    testar_gerador()