"""
Dashboard Simplificado - Sistema Logística JIT
Versão que funciona sem erros
"""

import streamlit as st
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime
import time

# Configuração da página
st.set_page_config(
    page_title="Sistema Logística JIT",
    page_icon="🌾",
    layout="wide"
)

# URLs da API
API_BASE = "http://localhost:8000"

@st.cache_data(ttl=30)
def fetch_api_data(endpoint):
    """Busca dados da API"""
    try:
        response = requests.get(f"{API_BASE}{endpoint}", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except:
        return None

def check_api_status():
    """Verifica se a API está online"""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=3)
        return response.status_code == 200
    except:
        return False

def create_simple_chart(dados_atuais):
    """Cria gráfico simples das 3 curvas"""
    if not dados_atuais:
        return None
    
    # Dados simulados para demonstração
    horas = list(range(24))
    
    # Valores base
    colheita_base = dados_atuais.get('colheitabilidade_ton_h', 60)
    moagem_base = dados_atuais.get('moagem_ton_h', 85)
    estoque_base = dados_atuais.get('estoque_total_ton', 2300)
    
    # Criar variações ao longo do dia
    colheita_valores = [colheita_base + (h % 5 - 2) * 3 for h in horas]
    moagem_valores = [moagem_base + (h % 7 - 3) * 2 for h in horas]
    estoque_valores = [estoque_base + (h % 12 - 6) * 30 for h in horas]
    
    # Criar subplots
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Colheitabilidade
    fig.add_trace(
        go.Scatter(
            x=horas,
            y=colheita_valores,
            mode='lines+markers',
            name='🌾 Colheitabilidade',
            line=dict(color='#2E8B57', width=3),
            hovertemplate='<b>Colheitabilidade</b><br>%{y:.1f} ton/h<extra></extra>'
        ),
        secondary_y=False
    )
    
    # Moagem
    fig.add_trace(
        go.Scatter(
            x=horas,
            y=moagem_valores,
            mode='lines+markers',
            name='🏭 Moagem',
            line=dict(color='#4169E1', width=3),
            hovertemplate='<b>Moagem</b><br>%{y:.1f} ton/h<extra></extra>'
        ),
        secondary_y=False
    )
    
    # Estoque
    fig.add_trace(
        go.Scatter(
            x=horas,
            y=estoque_valores,
            mode='lines+markers',
            name='🚚 Estoque sobre Rodas',
            line=dict(color='#DC143C', width=3),
            hovertemplate='<b>Estoque</b><br>%{y:.0f} ton<extra></extra>'
        ),
        secondary_y=True
    )
    
    # Configurar eixos
    fig.update_xaxes(title_text="⏰ Hora do Dia")
    fig.update_yaxes(title_text="📈 Colheita e Moagem (ton/h)", secondary_y=False)
    fig.update_yaxes(title_text="🚚 Estoque sobre Rodas (ton)", secondary_y=True)
    
    # Layout
    fig.update_layout(
        title="📊 SISTEMA LOGÍSTICA JIT - TRÊS CURVAS PRINCIPAIS",
        height=500,
        hovermode='x unified'
    )
    
    return fig

def display_frota_pie(estado_frota):
    """Gráfico pizza simples da frota"""
    if not estado_frota:
        return None
    
    labels = ['T1 - Voltando', 'T2 - Carregando', 'T3 - Indo', 'T4 - Pátio']
    values = [
        estado_frota.get('caminhoes_t1_voltando', 14),
        estado_frota.get('caminhoes_t2_carregando', 8),
        estado_frota.get('caminhoes_t3_indo', 16),
        estado_frota.get('caminhoes_t4_patio', 8)
    ]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=.3,
        textinfo='label+value'
    )])
    
    fig.update_layout(
        title=f"🚚 FROTA TOTAL: {sum(values)} CAMINHÕES",
        height=400
    )
    
    return fig

def main():
    """Função principal"""
    
    # Título
    st.title("🌾 Sistema Logística JIT - Usina Sucroenergética")
    st.markdown("**Dashboard Simplificado - Três Curvas Principais**")
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Status")
        
        api_online = check_api_status()
        status = "🟢 Online" if api_online else "🔴 Offline"
        st.markdown(f"**API:** {status}")
        
        auto_refresh = st.checkbox("🔄 Auto-refresh", value=True)
        
        if st.button("🔄 Atualizar"):
            st.cache_data.clear()
            st.rerun()
    
    if not api_online:
        st.error("❌ API não está respondendo")
        st.code("python3 run_backend.py")
        return
    
    # Buscar dados
    dados_atuais = fetch_api_data("/api/tres-curvas")
    estado_frota = fetch_api_data("/api/estado-frota")
    
    if not dados_atuais:
        st.warning("⚠️ Não foi possível carregar dados")
        return
    
    # Métricas principais
    st.markdown("### 📊 Situação Atual")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "🌾 Colheitabilidade",
            f"{dados_atuais.get('colheitabilidade_ton_h', 0):.1f} ton/h"
        )
    
    with col2:
        moagem = dados_atuais.get('moagem_ton_h', 0)
        capacidade = dados_atuais.get('capacidade_moagem', 1150)
        utilizacao = (moagem / capacidade * 100) if capacidade > 0 else 0
        
        st.metric(
            "🏭 Moagem",
            f"{moagem:.1f} ton/h",
            f"{utilizacao:.1f}% da capacidade"
        )
    
    with col3:
        st.metric(
            "🚚 Estoque sobre Rodas",
            f"{dados_atuais.get('estoque_total_ton', 0):.0f} ton"
        )
    
    with col4:
        colheita = dados_atuais.get('colheitabilidade_ton_h', 0)
        moagem = dados_atuais.get('moagem_ton_h', 0)
        diferenca = colheita - moagem
        status = "⚖️ EQUILIBRADO" if abs(diferenca) < 20 else "⚠️ DESBALANCEADO"
        
        st.metric(
            "📊 Balanceamento",
            status,
            f"{diferenca:+.1f} ton/h"
        )
    
    # Gráfico principal
    st.markdown("### 📈 Gráfico das Três Curvas")
    chart = create_simple_chart(dados_atuais)
    if chart:
        st.plotly_chart(chart, use_container_width=True)
    
    # Segunda linha
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🚚 Estado da Frota")
        frota_chart = display_frota_pie(estado_frota)
        if frota_chart:
            st.plotly_chart(frota_chart, use_container_width=True)
    
    with col2:
        st.markdown("### 🎯 Informações")
        
        # Alertas baseados nos dados
        if dados_atuais:
            estoque = dados_atuais.get('estoque_total_ton', 0)
            if estoque > 2600:
                st.warning("⚠️ Estoque alto - considere fazendas distantes")
            elif estoque < 2000:
                st.error("🚨 Estoque baixo - priorize fazendas próximas")
            else:
                st.success("✅ Estoque em nível adequado")
            
            # Balanceamento
            colheita = dados_atuais.get('colheitabilidade_ton_h', 0)
            moagem = dados_atuais.get('moagem_ton_h', 0)
            
            if moagem > colheita + 20:
                st.info("📈 Moagem maior que colheita - estoque tende a diminuir")
            elif colheita > moagem + 20:
                st.info("📉 Colheita maior que moagem - estoque tende a crescer")
    
    # Rodapé
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.caption(f"🕐 Último update: {dados_atuais.get('timestamp', 'N/A')}")
    
    with col2:
        st.caption(f"📡 API: {API_BASE}")
    
    with col3:
        st.caption("🔄 Sistema em tempo real")
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(30)
        st.rerun()

if __name__ == "__main__":
    main()