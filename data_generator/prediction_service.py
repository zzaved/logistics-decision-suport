"""
Serviço de Predição Automática
Executa predições periodicamente e salva no banco
"""

import time
import signal
import sys
from datetime import datetime
from pathlib import Path
import threading

import sys
from pathlib import Path

# Adicionar path para database
sys.path.append(str(Path(__file__).parent.parent / "database"))
from prediction_model import PredictionModel

class PredictionService:
    """
    Serviço que executa predições automaticamente
    """
    
    def __init__(self, intervalo_minutos=5):
        self.intervalo = intervalo_minutos * 60  # Converter para segundos
        self.executando = False
        self.model = PredictionModel()
        self.contador_predicoes = 0
        
        # Handler para parada
        signal.signal(signal.SIGINT, self.parar_graceful)
        signal.signal(signal.SIGTERM, self.parar_graceful)
    
    def executar_predicao_thread(self):
        """Executa predição em thread separada"""
        try:
            resultado = self.model.executar_predicao(salvar=True)
            self.contador_predicoes += 1
            
            # Verificar alertas críticos
            alertas_criticos = []
            for pred in resultado['predicoes'][:3]:  # Próximas 3 horas
                if not pred['dentro_limites']:
                    alertas_criticos.append({
                        'hora': pred['hora_futura'],
                        'estoque': pred['estoque_previsto'],
                        'ofensor': pred['ofensor_principal']
                    })
            
            if alertas_criticos:
                print("\n🚨 ALERTAS CRÍTICOS:")
                for alerta in alertas_criticos:
                    print(f"   +{alerta['hora']}h: Estoque {alerta['estoque']:.0f} ton - "
                          f"Causa: {alerta['ofensor']}")
            
        except Exception as e:
            print(f"❌ Erro na predição #{self.contador_predicoes}: {e}")
    
    def executar(self):
        """Loop principal do serviço"""
        print(f"🔮 Serviço de Predição iniciado")
        print(f"📊 Predições a cada {self.intervalo//60} minutos")
        print(f"💡 Pressione Ctrl+C para parar")
        print("=" * 60)
        
        self.executando = True
        
        # Executar primeira predição imediatamente
        print(f"\n🎯 Executando predição inicial...")
        self.executar_predicao_thread()
        
        try:
            while self.executando:
                # Aguardar intervalo
                for _ in range(self.intervalo):
                    if not self.executando:
                        break
                    time.sleep(1)
                
                if self.executando:
                    print(f"\n🔄 Executando predição #{self.contador_predicoes + 1}...")
                    
                    # Executar em thread para não bloquear
                    thread = threading.Thread(target=self.executar_predicao_thread)
                    thread.start()
                    thread.join(timeout=30)  # Timeout de 30 segundos
                    
                    if thread.is_alive():
                        print("⚠️ Predição demorou muito, continuando...")
                        
        except KeyboardInterrupt:
            self.parar_graceful(None, None)
        except Exception as e:
            print(f"❌ Erro crítico: {e}")
            self.executando = False
    
    def parar_graceful(self, signum, frame):
        """Para o serviço graciosamente"""
        print("\n\n⏹️ Parando serviço de predição...")
        self.executando = False
        
        # Estatísticas finais
        conn = self.model.conectar_banco()
        cursor = conn.cursor()
        
        # Contar predições salvas
        cursor.execute("""
            SELECT COUNT(DISTINCT timestamp_predicao) 
            FROM predicoes_estoque_patio
            WHERE timestamp_predicao > datetime('now', '-1 day')
        """)
        predicoes_24h = cursor.fetchone()[0]
        
        # Última predição
        cursor.execute("""
            SELECT timestamp_predicao, COUNT(*) 
            FROM predicoes_estoque_patio
            GROUP BY timestamp_predicao
            ORDER BY timestamp_predicao DESC
            LIMIT 1
        """)
        ultima = cursor.fetchone()
        
        conn.close()
        
        print(f"\n📊 Estatísticas finais:")
        print(f"   Predições executadas: {self.contador_predicoes}")
        print(f"   Predições últimas 24h: {predicoes_24h}")
        if ultima:
            print(f"   Última predição: {ultima[0]} ({ultima[1]} horas)")
        
        print("\n✅ Serviço finalizado")
    
    def limpar_predicoes_antigas(self, dias=7):
        """Remove predições antigas do banco"""
        conn = self.model.conectar_banco()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM predicoes_estoque_patio
            WHERE timestamp_predicao < datetime('now', '-{} days')
        """.format(dias))
        
        deletados = cursor.rowcount
        conn.commit()
        conn.close()
        
        if deletados > 0:
            print(f"🧹 Removidas {deletados} predições antigas (>{dias} dias)")


def testar_servico():
    """Teste rápido do serviço"""
    print("🧪 Teste do Serviço de Predição")
    print("=" * 40)
    
    service = PredictionService(intervalo_minutos=0.1)  # 6 segundos para teste
    
    # Executar por 20 segundos
    print("Executando por 20 segundos...")
    
    thread = threading.Thread(target=service.executar)
    thread.start()
    
    time.sleep(20)
    
    service.executando = False
    thread.join()
    
    print("\n✅ Teste concluído")


def main():
    """Função principal"""
    args = sys.argv[1:]
    
    if "--help" in args or "-h" in args:
        print("""
🔮 Serviço de Predição - Sistema Logística JIT

USO:
  python prediction_service.py              # Intervalo padrão (5 min)
  python prediction_service.py --intervalo 10  # A cada 10 minutos
  python prediction_service.py --teste      # Modo teste rápido
  python prediction_service.py --limpar     # Limpar predições antigas

FUNCIONALIDADES:
  - Executa predição das próximas 9 horas
  - Identifica ofensores quando sai dos limites
  - Salva histórico de predições
  - Alertas automáticos para situações críticas
  - Níveis de confiabilidade decrescentes

MODELO:
  - Combina padrões históricos com tendências recentes
  - Confiabilidade: 95% (1h) até 45% (9h)
  - Identifica causas de desvios
""")
        return
    
    # Modo teste
    if "--teste" in args:
        testar_servico()
        return
    
    # Limpar predições antigas
    if "--limpar" in args:
        service = PredictionService()
        service.limpar_predicoes_antigas()
        return
    
    # Intervalo personalizado
    intervalo = 5  # padrão 5 minutos
    if "--intervalo" in args:
        try:
            idx = args.index("--intervalo")
            intervalo = int(args[idx + 1])
        except (IndexError, ValueError):
            print("❌ Erro: --intervalo precisa de um número")
            return
    
    # Executar serviço
    service = PredictionService(intervalo_minutos=intervalo)
    service.executar()


if __name__ == "__main__":
    main()