import streamlit as st
import requests
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import time
import random
from datetime import datetime, timedelta

# Configuração da página
st.set_page_config(
    page_title="Sistema Logística",
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
    """Cria gráfico das 3 curvas - versão limpa e espaçada"""
    if not dados_atuais:
        return None
    
    # Criar figura
    fig = make_subplots(specs=[[{"secondary_y": True}]])
    
    # Valores atuais
    colheita_atual = dados_atuais.get('colheitabilidade_ton_h', 60)
    moagem_atual = dados_atuais.get('moagem_ton_h', 85)
    estoque_atual = dados_atuais.get('estoque_total_ton', 2300)
    
    # Timestamp atual
    agora = datetime.now()
    
    # CONFIGURAÇÃO DE TEMPO: 1/3 passado, 2/3 futuro
    # Total: 9 horas (3 passado + 6 futuro)
    
    # 1. DADOS HISTÓRICOS - Apenas 3 pontos no passado (bem espaçados)
    timestamps_hist = [
        agora - timedelta(hours=3),  # -3h
        agora - timedelta(hours=2),  # -2h
        agora - timedelta(hours=1),  # -1h
    ]
    
    # Simular variação suave dos dados históricos
    colheitas_hist = [
        colheita_atual + random.uniform(-10, 10),
        colheita_atual + random.uniform(-8, 8),
        colheita_atual + random.uniform(-5, 5),
    ]
    
    moagens_hist = [
        moagem_atual + random.uniform(-15, 15),
        moagem_atual + random.uniform(-10, 10),
        moagem_atual + random.uniform(-5, 5),
    ]
    
    # Calcular estoque histórico baseado no balanço
    estoque_3h = estoque_atual - 3 * (colheita_atual - moagem_atual)
    estoque_2h = estoque_atual - 2 * (colheita_atual - moagem_atual)
    estoque_1h = estoque_atual - 1 * (colheita_atual - moagem_atual)
    estoques_hist = [estoque_3h, estoque_2h, estoque_1h]
    
    # Adicionar ponto atual
    timestamps_hist.append(agora)
    colheitas_hist.append(colheita_atual)
    moagens_hist.append(moagem_atual)
    estoques_hist.append(estoque_atual)
    
    # 2. DADOS FUTUROS - 6 pontos (1 por hora)
    timestamps_fut = []
    colheitas_fut = [colheita_atual]
    moagens_fut = [moagem_atual]
    estoques_fut = [estoque_atual]
    
    for h in range(1, 7):  # 1 a 6 horas
        timestamps_fut.append(agora + timedelta(hours=h))
        
        # Predição com variação suave
        hora_futura = (agora.hour + h) % 24
        
        # Colheita reduz à noite
        if 22 <= hora_futura or hora_futura <= 6:
            fator_colheita = 0.7
        else:
            fator_colheita = 1.0
            
        colheita_pred = colheita_atual * fator_colheita + random.uniform(-5, 5)
        moagem_pred = moagem_atual + random.uniform(-5, 5)
        
        colheitas_fut.append(max(30, min(80, colheita_pred)))
        moagens_fut.append(max(70, min(110, moagem_pred)))
        
        # Estoque baseado no balanço
        ultimo_estoque = estoques_fut[-1]
        balanco = colheitas_fut[-1] - moagens_fut[-1]
        novo_estoque = ultimo_estoque + balanco
        estoques_fut.append(max(1800, min(2800, novo_estoque)))
    
    # PLOTAR DADOS HISTÓRICOS (linhas sólidas)
    # Colheitabilidade histórica
    fig.add_trace(
        go.Scatter(
            x=timestamps_hist,
            y=colheitas_hist,
            mode='lines+markers',
            name='🌾 Colheitabilidade',
            line=dict(color='#2E8B57', width=3),
            marker=dict(size=10),
            hovertemplate='<b>Colheita</b><br>%{y:.1f} ton/h<extra></extra>'
        ),
        secondary_y=False
    )
    
    # Moagem histórica
    fig.add_trace(
        go.Scatter(
            x=timestamps_hist,
            y=moagens_hist,
            mode='lines+markers',
            name='🏭 Moagem',
            line=dict(color='#4169E1', width=3),
            marker=dict(size=10),
            hovertemplate='<b>Moagem</b><br>%{y:.1f} ton/h<extra></extra>'
        ),
        secondary_y=False
    )
    
    # Estoque histórico
    fig.add_trace(
        go.Scatter(
            x=timestamps_hist,
            y=estoques_hist,
            mode='lines+markers',
            name='🚚 Estoque sobre Rodas',
            line=dict(color='#DC143C', width=3),
            marker=dict(size=10),
            hovertemplate='<b>Estoque</b><br>%{y:.0f} ton<extra></extra>'
        ),
        secondary_y=True
    )
    
    # MARCADOR "AGORA" - Estrelas grandes
    fig.add_trace(
        go.Scatter(
            x=[agora],
            y=[colheita_atual],
            mode='markers+text',
            marker=dict(color='#2E8B57', size=20, symbol='star'),
            text=['AGORA'],
            textposition='top center',
            textfont=dict(size=14, color='#FFD700'),
            showlegend=False,
            hovertemplate='<b>AGORA</b><br>Colheita: %{y:.1f} ton/h<extra></extra>'
        ),
        secondary_y=False
    )
    
    # PLOTAR PREDIÇÕES (linhas tracejadas)
    # Colheita futura
    fig.add_trace(
        go.Scatter(
            x=[agora] + timestamps_fut,
            y=colheitas_fut,
            mode='lines+markers',
            name='🌾 Colheita (Predição)',
            line=dict(color='#2E8B57', width=2, dash='dash'),
            marker=dict(size=8),
            opacity=0.7,
            hovertemplate='<b>+%{customdata}h</b><br>Colheita: %{y:.1f} ton/h<extra></extra>',
            customdata=[0, 1, 2, 3, 4, 5, 6]
        ),
        secondary_y=False
    )
    
    # Moagem futura
    fig.add_trace(
        go.Scatter(
            x=[agora] + timestamps_fut,
            y=moagens_fut,
            mode='lines+markers',
            name='🏭 Moagem (Predição)',
            line=dict(color='#4169E1', width=2, dash='dash'),
            marker=dict(size=8),
            opacity=0.7,
            hovertemplate='<b>+%{customdata}h</b><br>Moagem: %{y:.1f} ton/h<extra></extra>',
            customdata=[0, 1, 2, 3, 4, 5, 6]
        ),
        secondary_y=False
    )
    
    # Estoque futuro
    fig.add_trace(
        go.Scatter(
            x=[agora] + timestamps_fut,
            y=estoques_fut,
            mode='lines+markers',
            name='🚚 Estoque (Predição)',
            line=dict(color='#DC143C', width=2, dash='dash'),
            marker=dict(size=8),
            opacity=0.7,
            hovertemplate='<b>+%{customdata}h</b><br>Estoque: %{y:.0f} ton<extra></extra>',
            customdata=[0, 1, 2, 3, 4, 5, 6]
        ),
        secondary_y=True
    )
    
    # Linhas de referência para COLHEITABILIDADE (verde)
    fig.add_hline(
        y=80, 
        line=dict(color='#2E8B57', width=1, dash='dot'),
        annotation_text="Colheita Máx",
        annotation_position="left",
        annotation=dict(font=dict(size=10)),
        secondary_y=False
    )
    
    fig.add_hline(
        y=40, 
        line=dict(color='#2E8B57', width=1, dash='dot'),
        annotation_text="Colheita Mín",
        annotation_position="left",
        annotation=dict(font=dict(size=10)),
        secondary_y=False
    )
    
    # Linhas de referência para MOAGEM (azul)
    fig.add_hline(
        y=110, 
        line=dict(color='#4169E1', width=1, dash='dot'),
        annotation_text="Moagem Máx",
        annotation_position="right",
        annotation=dict(font=dict(size=10)),
        secondary_y=False
    )
    
    fig.add_hline(
        y=70, 
        line=dict(color='#4169E1', width=1, dash='dot'),
        annotation_text="Moagem Mín",
        annotation_position="right",
        annotation=dict(font=dict(size=10)),
        secondary_y=False
    )
    
    # Linhas de referência para ESTOQUE (vermelho)
    fig.add_hline(
        y=2700, 
        line=dict(color='#DC143C', width=1, dash='dot'),
        annotation_text="Estoque Alto",
        annotation_position="left",
        annotation=dict(font=dict(size=10)),
        secondary_y=True
    )
    
    fig.add_hline(
        y=2100, 
        line=dict(color='#DC143C', width=1, dash='dot'),
        annotation_text="Estoque Baixo",
        annotation_position="left",
        annotation=dict(font=dict(size=10)),
        secondary_y=True
    )
    
    # Configurar eixos
    fig.update_xaxes(
        title_text="⏰ Tempo",
        tickformat='%H:%M',  # Apenas hora:minuto
        dtick=3600000,  # 1 hora
        tickangle=0,
        gridcolor='rgba(128,128,128,0.2)',
        showgrid=True
    )
    
    fig.update_yaxes(
        title_text="📈 Colheita e Moagem (ton/h)", 
        secondary_y=False,
        range=[0, 200],
        gridcolor='rgba(128,128,128,0.2)',
        showgrid=True
    )
    
    fig.update_yaxes(
        title_text="🚚 Estoque sobre Rodas (ton)", 
        secondary_y=True,
        range=[1000, 3500]
    )
    
    # Layout
    fig.update_layout(
        title={
            'text': "📊 TRÊS CURVAS PRINCIPAIS - ANÁLISE TEMPORAL",
            'font': {'size': 20},
            'x': 0.5,
            'xanchor': 'center'
        },
        height=650,
        hovermode='x unified',
        showlegend=True,
        legend=dict(
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="left",
            x=1.02,
            bgcolor="rgba(0,0,0,0.8)",
            bordercolor="rgba(255,255,255,0.3)",
            borderwidth=1,
            font=dict(size=12)
        ),
        xaxis=dict(
            range=[timestamps_hist[0], timestamps_fut[-1]],  # Range fixo
            fixedrange=False
        ),
        margin=dict(
            l=100,
            r=250,  # Espaço para legenda
            t=100,
            b=100
        ),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)'
    )
    
    # Adicionar área sombreada para separar passado/futuro
    fig.add_vrect(
        x0=agora - timedelta(minutes=30),
        x1=agora + timedelta(minutes=30),
        fillcolor="yellow",
        opacity=0.1,
        line_width=0
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

def mostrar_dados_brutos(tipo):
    """Mostra dados brutos das tabelas do banco"""
    st.subheader(f"📋 Dados Brutos - {tipo.upper()}")
    
    if tipo == "colheitabilidade":
        # Dados das 3 curvas principais
        dados = fetch_api_data("/api/tres-curvas")
        if dados:
            st.markdown("**🌾 TABELA: dados_tempo_real (último registro)**")
            df = pd.DataFrame([dados])
            st.dataframe(df, use_container_width=True)
        
        # Dados por fazenda
        dados_fazendas = fetch_api_data("/api/colheitabilidade-fazendas")
        if dados_fazendas and dados_fazendas.get('fazendas'):
            st.markdown("**🏡 TABELA: colheitabilidade_detalhada (registros recentes)**")
            df = pd.DataFrame(dados_fazendas['fazendas'])
            st.dataframe(df, use_container_width=True)
    
    elif tipo == "moagem":
        # Dados das 3 curvas
        dados = fetch_api_data("/api/tres-curvas")
        if dados:
            st.markdown("**🏭 TABELA: dados_tempo_real (campos relacionados à moagem)**")
            campos_moagem = {
                'timestamp': dados.get('timestamp'),
                'moagem_ton_h': dados.get('moagem_ton_h'),
                'capacidade_moagem': dados.get('capacidade_moagem'),
                'fazendas_ativas': dados.get('fazendas_ativas')
            }
            df = pd.DataFrame([campos_moagem])
            st.dataframe(df, use_container_width=True)
    
    elif tipo == "estoque":
        # Estado da frota
        estado_frota = fetch_api_data("/api/estado-frota")
        if estado_frota:
            st.markdown("**🚚 TABELA: estado_frota (último registro)**")
            df = pd.DataFrame([estado_frota])
            st.dataframe(df, use_container_width=True)
        
        # Caminhões detalhados
        dados_caminhoes = fetch_api_data("/api/caminhoes")
        if dados_caminhoes and dados_caminhoes.get('caminhoes'):
            st.markdown("**🚛 TABELA: transporte_detalhado (últimos registros)**")
            df = pd.DataFrame(dados_caminhoes['caminhoes'])
            st.dataframe(df, use_container_width=True)
        
        # Dados de estoque das 3 curvas
        dados = fetch_api_data("/api/tres-curvas")
        if dados:
            st.markdown("**📊 TABELA: dados_tempo_real (campos de estoque)**")
            campos_estoque = {
                'timestamp': dados.get('timestamp'),
                'estoque_total_ton': dados.get('estoque_total_ton'),
                'estoque_voltando_ton': dados.get('estoque_voltando_ton'),
                'estoque_indo_ton': dados.get('estoque_indo_ton'),
                'estoque_patio_ton': dados.get('estoque_patio_ton')
            }
            df = pd.DataFrame([campos_estoque])
            st.dataframe(df, use_container_width=True)

def criar_grafico_estoque_patio_v2():
    """
    Cria o novo gráfico principal: histórico + predição
    """
    try:
        # Buscar dados consolidados da API
        response = requests.get(f"{API_BASE}/api/estoque-patio-consolidado", timeout=5)
        if response.status_code != 200:
            return None
        
        dados = response.json()
        
        # Extrair componentes
        historico = dados.get('historico', {}).get('dados', [])
        estado_atual = dados.get('estado_atual', {})
        predicao = dados.get('predicao', {})
        limites = dados.get('limites', {})
        
        # Criar figura
        fig = go.Figure()
        
        # 1. HISTÓRICO (linha azul)
        if historico:
            timestamps_hist = [d['timestamp'] for d in historico]
            estoques_hist = [float(d['estoque_patio']) for d in historico]
            
            fig.add_trace(go.Scatter(
                x=timestamps_hist,
                y=estoques_hist,
                mode='lines',
                name='📈 Histórico Real',
                line=dict(color='#1f77b4', width=3),
                hovertemplate='<b>Real</b><br>%{y:.0f} ton<extra></extra>'
            ))
        
        # 2. LINHA "AGORA" 
        if estado_atual and estado_atual.get('timestamp'):
            fig.add_trace(go.Scatter(
                x=[estado_atual['timestamp']],
                y=[float(estado_atual.get('estoque_patio', 0))],
                mode='markers+text',
                name='AGORA',
                marker=dict(color='#FFD700', size=15, symbol='star'),
                text=['AGORA'],
                textposition='top center',
                showlegend=False
            ))
        
        # 3. PREDIÇÃO
        if predicao and predicao.get('dados'):
            pred_dados = predicao['dados']
            
            # Conectar com linha pontilhada
            if estado_atual and pred_dados:
                estoque_atual = float(estado_atual.get('estoque_patio', 0))
                primeiro_pred = float(pred_dados[0].get('estoque_previsto', 0))
                
                fig.add_trace(go.Scatter(
                    x=[estado_atual.get('timestamp'), pred_dados[0].get('timestamp_previsto')],
                    y=[estoque_atual, primeiro_pred],
                    mode='lines',
                    line=dict(color='gray', width=1, dash='dot'),
                    showlegend=False
                ))
            
            # Separar predições por nível de confiança
            for i, pred in enumerate(pred_dados):
                hora = pred.get('hora_futura', i+1)
                timestamp = pred.get('timestamp_previsto', '')
                estoque = float(pred.get('estoque_previsto', 0))
                confianca = float(pred.get('confiabilidade', 0))
                
                # Determinar cor e grupo
                if confianca >= 0.85:
                    cor = '#2ca02c'
                    grupo = 'alta'
                elif confianca >= 0.65:
                    cor = '#ff7f0e'
                    grupo = 'media'
                else:
                    cor = '#d62728'
                    grupo = 'baixa'
                
                # Adicionar ponto
                fig.add_trace(go.Scatter(
                    x=[timestamp],
                    y=[estoque],
                    mode='markers',
                    marker=dict(color=cor, size=10),
                    name=f'🟢 Alta Conf.' if grupo == 'alta' and i < 3 else
                         f'🟡 Média Conf.' if grupo == 'media' and i == 3 else
                         f'🔴 Baixa Conf.' if grupo == 'baixa' and i == 6 else None,
                    showlegend=(i == 0 or i == 3 or i == 6),
                    hovertemplate=f'<b>+{hora}h</b><br>Estoque: {estoque:.0f} ton<br>Confiança: {confianca*100:.0f}%<extra></extra>'
                ))
                
                # Conectar pontos com linha
                if i > 0:
                    prev_timestamp = pred_dados[i-1].get('timestamp_previsto')
                    prev_estoque = float(pred_dados[i-1].get('estoque_previsto', 0))
                    
                    fig.add_trace(go.Scatter(
                        x=[prev_timestamp, timestamp],
                        y=[prev_estoque, estoque],
                        mode='lines',
                        line=dict(color=cor, width=2, dash='dash' if grupo != 'alta' else 'solid'),
                        showlegend=False
                    ))
        
        # 4. LIMITES
        limite_inf = float(limites.get('inferior', 800))
        limite_sup = float(limites.get('superior', 1500))
        
        fig.add_hline(
            y=limite_sup,
            line=dict(color='red', width=2, dash='dash'),
            annotation_text=f"Limite Superior ({limite_sup:.0f} ton)",
            annotation_position="right"
        )
        
        fig.add_hline(
            y=limite_inf,
            line=dict(color='red', width=2, dash='dash'),
            annotation_text=f"Limite Inferior ({limite_inf:.0f} ton)",
            annotation_position="right"
        )
        
        # Layout
        fig.update_layout(
            title='📊 ESTOQUE NO PÁTIO - ANÁLISE PREDITIVA',
            xaxis_title="Tempo",
            yaxis_title="Estoque no Pátio (ton)",
            height=500,
            hovermode='x unified',
            showlegend=True
        )
        
        # Zona segura
        fig.add_hrect(
            y0=limite_inf,
            y1=limite_sup,
            fillcolor="green",
            opacity=0.05,
            line_width=0
        )
        
        return fig
        
    except Exception as e:
        st.error(f"Erro ao criar gráfico V2: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Função principal"""
    
    # Título
    st.title("🌾 Sistema Logística JIT")
    
    # Variável para auto_refresh (precisa estar definida antes de ser usada)
    auto_refresh = True
    
    # Criar abas
    tab1, tab2 = st.tabs(["📊 Três Curvas Clássicas", "🚚 Estoque Pátio (Novo)"])
    
    with tab1:
        # ===== CÓDIGO EXISTENTE DO DASHBOARD =====
        st.markdown("**Dashboard de Três Curvas**")
        
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
        
        # Seção de dados brutos
        st.markdown("---")
        st.markdown("### 📋 Dados Brutos das Tabelas do Banco")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🌾 Colheitabilidade", use_container_width=True):
                st.session_state.dados_tipo = "colheitabilidade"
        
        with col2:
            if st.button("🏭 Moagem", use_container_width=True):
                st.session_state.dados_tipo = "moagem"
        
        with col3:
            if st.button("🚚 Estoque", use_container_width=True):
                st.session_state.dados_tipo = "estoque"
        
        if hasattr(st.session_state, 'dados_tipo'):
            mostrar_dados_brutos(st.session_state.dados_tipo)
            
            if st.button("❌ Esconder Dados"):
                del st.session_state.dados_tipo
                st.rerun()
    
    with tab2:
        # ===== NOVO DASHBOARD V2 =====
        st.markdown("**Análise Preditiva com Inteligência Artificial**")
        
        # Buscar dados consolidados
        dados_v2 = fetch_api_data("/api/estoque-patio-consolidado")
        
        if not dados_v2:
            st.warning("⚠️ Não foi possível carregar dados V2")
            st.info("Certifique-se que o serviço de predição está rodando:")
            st.code("python database/prediction_service.py")
            
            # Botão para gerar primeira predição
            if st.button("🔮 Gerar Primeira Predição"):
                response = requests.post(f"{API_BASE}/api/gerar-predicao")
                if response.status_code == 200:
                    st.success("Predição gerada! Recarregando...")
                    time.sleep(2)
                    st.rerun()
            return
        
        # Métricas V2
        col1, col2, col3, col4 = st.columns(4)
        
        estado_atual = dados_v2.get('estado_atual', {})
        predicao = dados_v2.get('predicao', {})
        limites = dados_v2.get('limites', {})
        
        with col1:
            estoque_atual = estado_atual.get('estoque_patio', 0)
            st.metric(
                "🚚 Estoque Pátio",
                f"{estoque_atual:.0f} ton"
            )
        
        with col2:
            entrada = estado_atual.get('taxa_entrada', 0)
            saida = estado_atual.get('taxa_saida', 0)
            balanco = entrada - saida
            
            st.metric(
                "⚖️ Balanço",
                f"{balanco:+.1f} ton/h",
                "Acumulando" if balanco > 0 else "Consumindo"
            )
        
        with col3:
            dentro_limites = limites['inferior'] <= estoque_atual <= limites['superior']
            status = "✅ Normal" if dentro_limites else "⚠️ Atenção"
            
            st.metric(
                "📊 Status",
                status,
                f"Limites: {limites['inferior']}-{limites['superior']}"
            )
        
        with col4:
            if st.button("🔮 Nova Predição", use_container_width=True):
                response = requests.post(f"{API_BASE}/api/gerar-predicao")
                if response.status_code == 200:
                    st.success("Nova predição gerada!")
                    st.rerun()
        
        # Gráfico V2
        st.markdown("### 📈 Estoque no Pátio - Visão Preditiva")
        grafico_v2 = criar_grafico_estoque_patio_v2()
        if grafico_v2:
            st.plotly_chart(grafico_v2, use_container_width=True)
        
        # Análise de ofensores
        with st.expander("🔍 Análise de Causas e Recomendações"):
            analise = fetch_api_data("/api/analise-ofensores")
            if analise:
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Principais Ofensores:**")
                    for ofensor in analise.get('ofensores_frequentes', [])[:3]:
                        st.write(f"• {ofensor['tipo']}: {ofensor['ocorrencias']}x")
                
                with col2:
                    st.markdown("**Recomendações:**")
                    for rec in analise.get('recomendacoes', []):
                        st.write(rec)
        
        # Informações do modelo
        if predicao:
            st.caption(f"Última predição: {predicao.get('timestamp_predicao', 'N/A')}")
    
    # Rodapé (em ambas as abas)
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.caption("🕐 Sistema em tempo real")
    
    with col2:
        st.caption(f"📡 API: {API_BASE}")
    
    with col3:
        st.caption("🔄 Atualização automática: 30s")
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(30)
        st.rerun()

if __name__ == "__main__":
    main()