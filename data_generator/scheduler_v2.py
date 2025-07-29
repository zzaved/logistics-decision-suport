"""
Scheduler V2 - Sistema Logística JIT
Usa o novo gerador com variáveis de predição
"""

import time
import signal
import sys
from datetime import datetime
from pathlib import Path

# Adicionar path para importar mock_generator_v2
sys.path.append(str(Path(__file__).parent))
from mock_generator_v2 import MockDataGeneratorV2

class LogisticaSchedulerV2:
    """
    Scheduler V2 com suporte às novas variáveis
    """
    
    def __init__(self, intervalo_segundos=10):
        self.intervalo = intervalo_segundos
        self.executando = False
        self.generator = None
        self.contador_ciclos = 0
        
        # Configurar handler para parada graceful (Ctrl+C)
        signal.signal(signal.SIGINT, self.parar_graceful)
        signal.signal(signal.SIGTERM, self.parar_graceful)
    
    def inicializar(self):
        """Inicializa o gerador V2"""
        try:
            self.generator = MockDataGeneratorV2()
            print("✅ Mock Data Generator V2 inicializado")
            print("📊 Novas variáveis incluídas:")
            print("   - Taxa de entrada/saída do pátio")
            print("   - Velocidade dos caminhões")
            print("   - Previsão de chegadas")
            print("   - Alertas automáticos")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao inicializar: {e}")
            return False
    
    def executar_ciclo(self):
        """Executa um ciclo de geração de dados V2"""
        try:
            dados = self.generator.gerar_ciclo_completo_v2()
            self.contador_ciclos += 1
            
            # A cada 50 ciclos, limpar dados antigos
            if self.contador_ciclos % 50 == 0:
                self.generator.limpar_dados_antigos(horas=2)
                print(f"\n📊 Estatísticas após {self.contador_ciclos} ciclos:")
                self.mostrar_estatisticas()
            
            return True
            
        except Exception as e:
            print(f"❌ Erro no ciclo {self.contador_ciclos}: {e}")
            return False
    
    def mostrar_estatisticas(self):
        """Mostra estatísticas do sistema"""
        conn = self.generator.conectar_banco()
        cursor = conn.cursor()
        
        # Média das últimas 10 leituras
        cursor.execute("""
            SELECT 
                AVG(estoque_patio_ton) as estoque_medio,
                AVG(taxa_entrada_patio_ton_h) as entrada_media,
                AVG(taxa_saida_patio_ton_h) as saida_media,
                MIN(estoque_patio_ton) as estoque_min,
                MAX(estoque_patio_ton) as estoque_max
            FROM (
                SELECT * FROM dados_tempo_real 
                ORDER BY timestamp DESC LIMIT 10
            )
        """)
        
        stats = cursor.fetchone()
        if stats:
            print(f"   📈 Estoque médio: {stats[0]:.0f} ton (min: {stats[3]:.0f}, max: {stats[4]:.0f})")
            print(f"   📥 Entrada média: {stats[1]:.1f} ton/h")
            print(f"   📤 Saída média: {stats[2]:.1f} ton/h")
            print(f"   ⚖️ Balanço: {stats[1] - stats[2]:+.1f} ton/h")
        
        # Contar alertas
        cursor.execute("""
            SELECT severidade, COUNT(*) 
            FROM eventos_sistema 
            WHERE timestamp > datetime('now', '-1 hour')
            GROUP BY severidade
        """)
        
        alertas = cursor.fetchall()
        if alertas:
            print("   🚨 Alertas última hora:")
            for severidade, count in alertas:
                print(f"      - {severidade}: {count}")
        
        conn.close()
    
    def executar(self):
        """Loop principal do scheduler V2"""
        if not self.inicializar():
            return
        
        self.executando = True
        
        print(f"\n🚀 Scheduler V2 iniciado - dados a cada {self.intervalo}s")
        print("💡 Pressione Ctrl+C para parar")
        print("=" * 60)
        
        try:
            while self.executando:
                inicio = time.time()
                
                # Executar ciclo
                sucesso = self.executar_ciclo()
                
                if not sucesso:
                    print("⚠️ Erro no ciclo, continuando...")
                
                # Aguardar intervalo
                tempo_execucao = time.time() - inicio
                tempo_espera = max(0, self.intervalo - tempo_execucao)
                
                if tempo_espera > 0:
                    time.sleep(tempo_espera)
                
        except KeyboardInterrupt:
            self.parar_graceful(None, None)
        
        except Exception as e:
            print(f"❌ Erro crítico no scheduler: {e}")
            self.parar()
    
    def parar_graceful(self, signum, frame):
        """Para o scheduler de forma graciosa"""
        print("\n\n⏹️ Parando scheduler V2...")
        self.executando = False
        
        if self.generator:
            print("\n📊 Resumo final:")
            self.mostrar_estatisticas()
            
            # Mostrar últimos eventos
            conn = self.generator.conectar_banco()
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT timestamp, descricao 
                FROM eventos_sistema 
                ORDER BY timestamp DESC 
                LIMIT 5
            """)
            
            eventos = cursor.fetchall()
            if eventos:
                print("\n📋 Últimos eventos:")
                for timestamp, descricao in eventos:
                    print(f"   {timestamp}: {descricao}")
            
            conn.close()
        
        print(f"\n✅ Scheduler V2 parado após {self.contador_ciclos} ciclos")

def main():
    """Função principal"""
    
    # Processar argumentos
    args = sys.argv[1:]
    
    if "--help" in args or "-h" in args:
        print("""
🚀 Sistema Logística JIT - Scheduler V2

NOVIDADES V2:
  - Cálculo de taxa de entrada/saída do pátio
  - Velocidade realista dos caminhões  
  - Previsão de chegadas por hora
  - Alertas automáticos por limites
  - Identificação de ofensores

USO:
  python scheduler_v2.py              # Intervalo padrão (10s)
  python scheduler_v2.py --intervalo 5   # A cada 5 segundos
  python scheduler_v2.py --teste      # Modo teste (5 ciclos)
""")
        return
    
    # Intervalo personalizado
    intervalo = 10
    if "--intervalo" in args:
        try:
            idx = args.index("--intervalo")
            intervalo = int(args[idx + 1])
        except (IndexError, ValueError):
            print("❌ Erro: --intervalo precisa de um número")
            return
    
    # Modo teste
    if "--teste" in args:
        print("🧪 Modo teste V2")
        from mock_generator_v2 import testar_gerador_v2
        testar_gerador_v2()
    else:
        scheduler = LogisticaSchedulerV2(intervalo_segundos=intervalo)
        scheduler.executar()

if __name__ == "__main__":
    main()