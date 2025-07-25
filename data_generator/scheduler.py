"""
Scheduler Automático - Sistema Logística JIT
Executa o mock generator a cada 10 segundos simulando dados em tempo real
"""

import time
import signal
import sys
from datetime import datetime
from pathlib import Path

# Adicionar path para importar mock_generator
sys.path.append(str(Path(__file__).parent))
from mock_generator import MockDataGenerator

class LogisticaScheduler:
    """
    Scheduler que executa geração de dados em intervalos regulares
    Simula dados chegando da usina em tempo real
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
        """Inicializa o gerador e verifica conexões"""
        try:
            self.generator = MockDataGenerator()
            print("✅ Mock Data Generator inicializado")
            
            # Teste rápido
            self.generator.status_banco()
            return True
            
        except Exception as e:
            print(f"❌ Erro ao inicializar: {e}")
            print("💡 Certifique-se que o banco foi criado: python database/init_db.py")
            return False
    
    def executar_ciclo(self):
        """Executa um ciclo de geração de dados"""
        try:
            dados = self.generator.gerar_ciclo_completo()
            self.contador_ciclos += 1
            
            # A cada 50 ciclos (~8min), limpar dados antigos
            if self.contador_ciclos % 50 == 0:
                self.generator.limpar_dados_antigos(horas=2)
                print(f"📊 Ciclos executados: {self.contador_ciclos}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro no ciclo {self.contador_ciclos}: {e}")
            return False
    
    def executar(self):
        """Loop principal do scheduler"""
        if not self.inicializar():
            return
        
        self.executando = True
        
        print(f"🚀 Scheduler iniciado - dados a cada {self.intervalo}s")
        print("💡 Pressione Ctrl+C para parar")
        print("=" * 60)
        
        try:
            while self.executando:
                inicio = time.time()
                
                # Executar ciclo
                sucesso = self.executar_ciclo()
                
                if not sucesso:
                    print("⚠️ Erro no ciclo, continuando...")
                
                # Aguardar intervalo (compensando tempo de execução)
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
        print("\n⏹️ Parando scheduler...")
        self.executando = False
        
        if self.generator:
            print("📊 Status final do banco:")
            self.generator.status_banco()
        
        print(f"✅ Scheduler parado após {self.contador_ciclos} ciclos")
        print("💾 Dados preservados no banco")
    
    def parar(self):
        """Para o scheduler imediatamente"""
        self.executando = False

def mostrar_ajuda():
    """Mostra instruções de uso"""
    print("""
🚀 Sistema Logística JIT - Data Scheduler

COMO USAR:
  python scheduler.py              # Executa com intervalo padrão (10s)
  python scheduler.py --intervalo 5   # Executa a cada 5 segundos
  python scheduler.py --teste      # Executa apenas 5 ciclos para teste
  python scheduler.py --help       # Mostra esta ajuda

FUNCIONAMENTO:
  - Gera dados das 3 curvas principais a cada X segundos
  - Simula operação real da usina em tempo real  
  - Dados baseados em padrões reais, mas SEM regras fixas
  - Armazena no banco SQLite para consumo da API

CONTROLES:
  Ctrl+C  = Para execução e mostra estatísticas
  
PRÓXIMOS PASSOS:
  1. Deixar este scheduler rodando
  2. Em outro terminal: python backend/main.py
  3. Em outro terminal: streamlit run frontend/dashboard.py
""")

def main():
    """Função principal"""
    
    # Processar argumentos simples
    args = sys.argv[1:]
    
    if "--help" in args or "-h" in args:
        mostrar_ajuda()
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
    modo_teste = "--teste" in args
    
    # Criar e executar scheduler
    scheduler = LogisticaScheduler(intervalo_segundos=intervalo)
    
    if modo_teste:
        print("🧪 Modo teste: executando apenas 5 ciclos")
        scheduler.inicializar()
        for i in range(5):
            print(f"\n--- Ciclo {i+1}/5 ---")
            scheduler.executar_ciclo()
            if i < 4:  # Não esperar no último
                time.sleep(intervalo)
        print("\n✅ Teste concluído!")
        scheduler.generator.status_banco()
    else:
        scheduler.executar()

if __name__ == "__main__":
    main()