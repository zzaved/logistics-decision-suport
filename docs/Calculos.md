# Documentação dos Cálculos - Sistema Logística

Este documento detalha como cada gráfico e métrica do sistema é calculado a partir das variáveis base.

## Gráficos Principais

### 1. Gráfico das Três Curvas Clássicas

#### Curva Verde - Colheitabilidade
**Fonte**: Direto da variável `colheitabilidade_ton_h`
```
Colheitabilidade = colheitabilidade_ton_h
```
- **Unidade**: ton/h
- **Origem**: Agregação dos dados por fazenda/setor
- **Cálculo agregado**: `SUM(TON_HORA)` por hora de todas as fazendas ativas

#### Curva Azul - Moagem
**Fonte**: Direto da variável `moagem_ton_h`
```
Moagem = moagem_ton_h
```
- **Unidade**: ton/h
- **Origem**: Capacidade efetiva da usina
- **Relação**: `horas_efetivas_dia × capacidade_ton_h / 24h`

#### Curva Vermelha - Estoque Sobre Rodas
**Fonte**: Soma de todos os estoques em movimento
```
Estoque Total = estoque_voltando_ton + estoque_indo_ton + estoque_patio_ton
```
**Onde**:
- `estoque_voltando_ton` = Caminhões T1 × carga_média
- `estoque_indo_ton` = Caminhões T3 × carga_média  
- `estoque_patio_ton` = Caminhões T4 × carga_média

#### Balanço das Três Curvas
```
Balanço = Colheitabilidade - Moagem
```
- **Positivo**: Estoque tende a crescer
- **Negativo**: Estoque tende a diminuir
- **Próximo de zero**: Sistema equilibrado

### 2. Gráfico Estado da Frota (Pizza)

#### Distribuição dos 46 Caminhões
```
T1 (Voltando) = caminhoes_t1_voltando
T2 (Carregando) = caminhoes_t2_carregando  
T3 (Indo) = caminhoes_t3_indo
T4 (Pátio) = caminhoes_t4_patio

Verificação: T1 + T2 + T3 + T4 = 46
```

### 3. Gráfico Estoque no Pátio (Predição)

#### Linha Azul Histórica
**Fonte**: Direto da variável
```
Estoque Pátio Histórico = estoque_patio_ton
```

#### Linhas Tracejadas de Predição
**Fonte**: Modelo híbrido
```
Estoque Futuro(h) = Estoque Atual + (Taxa Entrada - Taxa Saída) × h
```

**Onde**:
```
Taxa Entrada = taxa_entrada_patio_ton_h
Taxa Saída = taxa_saida_patio_ton_h
h = horas no futuro (1-9h)
```

#### Confiabilidade das Predições
```
Confiabilidade(h) = Base × Fator Decaimento^h
```
**Onde**:
- Base = 0.95 (95%)
- Fator Decaimento = 0.92
- h = horas futuras

**Resultado**:
- 1h: 95%
- 3h: 85%
- 6h: 68%
- 9h: 45%

## Métricas do Dashboard

### 1. Métricas Principais (Cards Superiores)

#### Colheitabilidade Atual
```
Valor = colheitabilidade_ton_h (último registro)
```

#### Moagem Atual + Utilização
```
Moagem = moagem_ton_h (último registro)
Utilização = (moagem_ton_h / capacidade_moagem) × 100%
```

#### Estoque Sobre Rodas
```
Estoque = estoque_total_ton (último registro)
```

#### Balanço do Sistema
```
Diferença = colheitabilidade_ton_h - moagem_ton_h
Status = "EQUILIBRADO" se |diferença| < 20, senão "DESBALANCEADO"
```

### 2. Métricas do Estoque no Pátio

#### Estoque Atual
```
Estoque Pátio = estoque_patio_ton (último registro)
```

#### Balanço Entrada/Saída
```
Balanço = taxa_entrada_patio_ton_h - taxa_saida_patio_ton_h
```
- **Positivo**: Acumulando no pátio
- **Negativo**: Consumindo do pátio

#### Status Operacional
```
if limite_inferior ≤ estoque_patio_ton ≤ limite_superior:
    Status = "Normal"
else:
    Status = "Atenção"
```

**Limites**:
- Inferior: 800 ton
- Superior: 1500 ton

### 3. Estado da Frota Detalhado

#### Caminhões por Estado
```
T1 = caminhoes_t1_voltando
T2 = caminhoes_t2_carregando
T3 = caminhoes_t3_indo  
T4 = caminhoes_t4_patio
```

#### Carga Média
```
Carga Média = carga_media_kg / 1000 (conversão para toneladas)
```

#### Taxa de Chegadas
```
Chegadas por Hora = taxa_chegada_caminhoes_hora
Previsão Próxima Hora = previsao_chegadas_prox_hora
```

## Cálculos das Taxas de Fluxo

### 1. Taxa de Entrada no Pátio

#### Método 1: Baseado em Chegadas
```
Taxa Entrada = (Caminhões Chegando por Hora) × (Carga Média)
```

#### Método 2: Baseado na Colheitabilidade
```
Taxa Entrada = Colheitabilidade × Fator Conversão
```
**Onde**: Fator Conversão = 0.15 - 0.25 (15-25% da colheita chega ao pátio)

### 2. Taxa de Saída do Pátio

#### Método Principal
```
Taxa Saída = moagem_ton_h × Fator Variação
```
**Onde**: Fator Variação = 0.98 - 1.02 (±2% de variação)

### 3. Suavização das Taxas

#### Para Evitar Variações Bruscas
```
Nova Taxa = Taxa Anterior + ((Taxa Calculada - Taxa Anterior) × 0.3)
```
- Peso 70% para valor anterior (estabilidade)
- Peso 30% para novo valor (responsividade)

## Cálculos de Predição

### 1. Modelo Híbrido

#### Componente Histórico (70%)
```
Valor Histórico = Média da mesma hora/dia em dados históricos
```

#### Componente Tendência (30%)
```
Valor Tendência = Valor Atual + (Variação Últimas 2h)
```

#### Combinação
```
Predição = (Valor Histórico × 0.7) + (Valor Tendência × 0.3)
```

### 2. Cálculo do Estoque Futuro

#### Fórmula Base
```
Estoque(t+h) = Estoque(t) + Σ(Entrada(i) - Saída(i)) para i=1 até h
```

#### Com Incerteza
```
Limite Superior = Estoque Previsto + (Desvio Padrão × Fator Incerteza)
Limite Inferior = Estoque Previsto - (Desvio Padrão × Fator Incerteza)
```
**Onde**: Fator Incerteza = 1 + (1 - Confiabilidade)

### 3. Identificação de Ofensores

#### Estoque Alto
```
if estoque > limite_superior:
    if taxa_entrada > 60: ofensor = "CHEGADAS_EXCESSIVAS"
    elif taxa_saida < 80: ofensor = "MOAGEM_BAIXA"
    else: ofensor = "ACUMULO_GRADUAL"
```

#### Estoque Baixo
```
if estoque < limite_inferior:
    if taxa_entrada < 40: ofensor = "POUCAS_CHEGADAS"
    elif taxa_saida > 100: ofensor = "MOAGEM_ALTA"
    else: ofensor = "CONSUMO_GRADUAL"
```

## Cálculos de Alertas

### 1. Alertas Automáticos

#### Estoque Alto
```
if estoque_patio_ton > 2700:
    Tipo = "ATENÇÃO" 
    Descrição = f"Estoque atual: {estoque:.0f} ton (acima de 2.700)"
```

#### Estoque Baixo
```
if estoque_patio_ton < 2000:
    Tipo = "CRÍTICO"
    Descrição = f"Estoque atual: {estoque:.0f} ton (abaixo de 2.000)"
```

#### Desbalanceamento
```
diferenca = colheita - moagem
if |diferenca| > 50:
    Tipo = "CRÍTICO" se |diferenca| > 100 else "ATENÇÃO"
    Descrição = f"Diferença: {diferenca:+.1f} ton/h"
```

### 2. Tendência do Estoque

#### Cálculo da Tendência (30 minutos)
```
if estoque_atual - estoque_30min_atrás > 100:
    Tendência = "SUBINDO"
elif estoque_atual - estoque_30min_atrás < -100:
    Tendência = "DESCENDO"  
else:
    Tendência = "ESTÁVEL"
```

## Recomendações Automáticas

### 1. Baseadas no Estoque

#### Estoque Alto + Tendência Subindo
```
Recomendações = [
    "Momento ideal para despachar fazendas distantes",
    "Estoque alto permite ciclos mais longos"
]
```

#### Estoque Baixo + Tendência Descendo
```
Recomendações = [
    "Priorizar fazendas próximas apenas", 
    "Focar em ciclos rápidos"
]
```

### 2. Baseadas no Horário

#### Período Crítico (13h-16h)
```
if 13 ≤ hora_atual ≤ 16:
    Recomendação = "Horário crítico da tarde - evitar fazendas distantes"
```

#### Período Ideal (6h-9h)
```
if 6 ≤ hora_atual ≤ 9:
    Recomendação = "Horário ideal da manhã - aproveitar para otimizar"
```

## Validações dos Cálculos

### 1. Verificações de Consistência

#### Soma da Frota
```
assert T1 + T2 + T3 + T4 == 46
```

#### Estoque Total
```
assert estoque_total_ton == estoque_voltando_ton + estoque_indo_ton + estoque_patio_ton
```

#### Taxas Positivas
```
assert taxa_entrada_patio_ton_h ≥ 0
assert taxa_saida_patio_ton_h ≥ 0
```

### 2. Limites Operacionais

#### Valores Máximos
```
assert colheitabilidade_ton_h ≤ 100
assert moagem_ton_h ≤ capacidade_moagem
assert velocidade_media_kmh ≤ 120
```

#### Valores Mínimos
```
assert estoque_patio_ton ≥ 0
assert taxa_chegada_caminhoes_hora ≥ 0
```

## Resumo dos Cálculos por Componente

### Dashboard Principal
- **3 Curvas**: Valores diretos das variáveis base
- **Balanço**: Diferença colheita - moagem
- **Estado Frota**: Contadores diretos T1, T2, T3, T4

### Dashboard Predição  
- **Histórico**: Valores diretos `estoque_patio_ton`
- **Futuro**: Modelo híbrido com balanço entrada/saída
- **Confiabilidade**: Função decrescente por horizonte temporal

### Alertas e Recomendações
- **Limites**: Comparações com faixas pré-definidas
- **Tendências**: Diferenças temporais dos estoques
- **Ofensores**: Lógica condicional baseada nas taxas

Todos os cálculos são executados em tempo real a cada ciclo de 10 segundos, garantindo que os gráficos e métricas reflitam sempre o estado atual do sistema.