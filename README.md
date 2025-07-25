# Sistema Logística JIT - Usina Sucroenergética

Dashboard de monitoramento visual em tempo real das 3 curvas principais:
- 🌾 **Colheitabilidade** hora-a-hora  
- 🏭 **Moagem** hora-a-hora
- 🚚 **Estoque sobre rodas** (T1 + T3 + T4)

## 🚀 Como Executar

### 1. Configurar Ambiente
```bash
cd logistics-decision-support
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### 2. Instalar Dependências
```bash
pip install -r data_generator/requirements.txt
pip install -r backend/requirements.txt  
pip install -r frontend/requirements.txt
```

### 3. Inicializar Banco
```bash
python database/init_db.py
```

### 4. Executar Sistema
```bash
# Terminal 1: Data Generator (mock em tempo real)
python data_generator/scheduler.py

# Terminal 2: Backend API
python backend/main.py

# Terminal 3: Frontend Dashboard  
streamlit run frontend/dashboard.py
```

### 5. Acessar Dashboard
- **Frontend:** http://localhost:8501
- **API:** http://localhost:8000/docs

## 📊 Arquitetura

```
Data Generator → SQLite → FastAPI → Streamlit
    (10s)       (banco)   (API)    (dashboard)
```

## 🎯 Funcionalidades

- ✅ Gráfico principal com 3 curvas sobrepostas
- ✅ Estado da frota (46 caminhões) 
- ✅ Alertas automáticos baseados em balanceamento
- ✅ Dados mock baseados em padrões reais
- ✅ Atualização tempo real (WebSocket)
- ✅ Drill-down interativo (clique nas linhas)

## 📂 Estrutura

```
logistics-decision-support/
├── database/           # SQLite + schema
├── data_generator/     # Mock baseado em dados reais
├── backend/           # FastAPI + endpoints
├── frontend/          # Streamlit dashboard
└── scripts/           # Scripts de execução
```

## 🔧 Dados Simulados

Baseados em análise real de 609k registros:
- Colheitabilidade: 30-80 ton/h (variação natural)
- Moagem: 50-200 ton/h (capacidade 1.150 ton/h)
- Estoque: 1.800-2.800 ton (46 caminhões)
- Frota: T1+T2+T3+T4 distribuição realística

**Sem regras fixas** - padrões emergem naturalmente para decisão visual!
