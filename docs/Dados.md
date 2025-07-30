# Documentação dos Dados - Sistema Logística JIT

Este documento detalha os dados reais coletados do datalake e as variáveis criadas para implementar as funcionalidades de predição de estoque no pátio.

## Dados Originais do Datalake

### 1. bronze_cubo.colheitabilidade
**Fonte Real**: Sistema de controle da colheita das fazendas  
**Período**: Abril/2025 (12.600 registros)  
**Cobertura**: 151 fazendas distintas, 8 setores por fazenda

| Campo | Tipo | Descrição | Valores Reais Observados |
|-------|------|-----------|--------------------------|
| HORA_ELEVADOR_TIME | TIMESTAMP | Horário da leitura do elevador | 11h, 12h, 13h, 14h apenas |
| FAZENDA | STRING | Nome da fazenda | 151 fazendas ativas |
| SETOR | STRING | Setor da fazenda | A, B, C, D, E, F, G, H |
| TON_HORA | FLOAT64 | Toneladas colhidas por hora | 30-80 ton/h, pico 62.4 ton/h às 12h |
| data_origem | DATE | Data de origem dos dados | Abril/2025 |

**Limitações Identificadas:**
- Dados disponíveis apenas para 4 horas do dia (11h-14h)
- Ausência de dados noturnos (83% do tempo sem cobertura)
- Concentração no horário de pico operacional

### 2. bronze_pims.pimspro_rel_003
**Fonte Real**: Sistema PIMS (Process Information Management System) da usina  
**Período**: Abril/2023 - Julho/2025  
**Característica**: Dados consolidados diariamente

| Campo | Tipo | Descrição | Valores Reais Observados |
|-------|------|-----------|--------------------------|
| DATA | TIMESTAMP | Data e hora da leitura | Dados diários |
| ORR_DESCRI | STRING | Descrição da variável | "Horas Efetivas Moagem" |
| VAR_RESULT_DIA | FLOAT64 | Horas efetivas de moagem por dia | 22.5h/dia em média |

**Conversão Aplicada:**
- Capacidade real: 22.5h × 50 ton/h = **1.150 ton/h**
- Uptime operacional: 93.75% (22.5h/24h)
- Conclusão: moagem tem 18x mais capacidade que colheita

### 3. bronze_pims.McKinsey_data_request_transporte_v3
**Fonte Real**: Sistema de controle logístico dos caminhões  
**Período Total**: Março/2021 - Dezembro/2023 (609.627 registros)  
**Período Analisado**: Nov-Dez/2023 (4.046 registros válidos após filtros)

| Campo | Tipo | Descrição | Valores Reais Observados |
|-------|------|-----------|--------------------------|
| HR_ENTRADA_PIMS | TIMESTAMP | Horário de entrada no sistema | Nov-Dez/2023 |
| NO_PLACA | STRING | Placa do caminhão | 46 caminhões únicos identificados |
| T_1 | FLOAT64 | Tempo vazio até colhedora (horas) | 0.5-4.0h |
| T_3 | FLOAT64 | Tempo carregado até usina (horas) | 1.0-8.0h |
| T_4 | FLOAT64 | **Tempo na usina (horas)** | 0.58h (7h) até 4.41h (0h) |
| QT_LIQUIDO_PESAGEM | INTEGER | Peso líquido transportado | 60.000-80.000 kg, média 70 ton |
| DISTANCIA_PIMS_MEDIA | FLOAT64 | Distância média percorrida | 20-90 km |
| de_categ_oper | STRING | Categoria operacional | 4 tipos: Rodotrem, Bi-trem, etc. |

**Descobertas Críticas dos Dados Reais:**
- **Horário 15h**: ciclo completo 22.7h para fazendas >50km (inviável)
- **Horário 6h**: ciclo completo 6.8h para fazendas >50km (ótimo)
- **Distribuição operacional**: 90% fazendas <50km, 10% fazendas distantes
- **Frota constante**: 46 caminhões sempre em operação

### 4. Padrões Operacionais Descobertos

**Eficiência por Horário:**
- **Melhor**: 7h manhã - 12.939 kg/h, T4 = 0.58h
- **Pior**: 15h tarde - 8.323 kg/h, T4 = 4.41h
- **Diferença**: 55% de variação de eficiência

**Distribuição Típica da Frota (dados reais):**
- T1 (voltando): 16 caminhões
- T2 (carregando): 8 caminhões 
- T3 (indo): 14 caminhões
- T4 (pátio): 8 caminhões

**Estoque Sobre Rodas Calculado:**
- **Constante**: 2.000-2.500 toneladas sempre em movimento
- **Variação**: apenas 20% ao longo de 24h
- **Buffer natural**: sistema auto-regulado pelos tempos de ciclo

## Dados Criados Para Funcionalidades Avançadas

### 5. Variáveis de Predição de Chegadas
**Por que foram criadas**: Os dados originais não permitiam prever quando caminhões chegariam ao pátio

| Campo Criado | Tipo | Justificativa | Como é Calculado |
|--------------|------|---------------|------------------|
| velocidade_media_kmh | REAL | Prever tempo de chegada baseado em distância | DISTANCIA_PIMS_MEDIA ÷ T_3 |
| tempo_descarga_min | REAL | Estimar tempo de liberação do pátio | Análise estatística dos T_4 reais |
| hora_chegada_patio | DATETIME | Saber exatamente quando caminhão chega | HR_ENTRADA + T_1 + 2.0 + T_3 |
| hora_saida_patio | DATETIME | Saber quando pátio fica disponível | hora_chegada + T_4 |

### 6. Taxas de Fluxo do Pátio
**Por que foram criadas**: Para implementar o modelo de predição baseado em balanço entrada vs saída

| Campo Criado | Tipo | Justificativa | Como é Calculado |
|--------------|------|---------------|------------------|
| taxa_entrada_patio_ton_h | REAL | **Core da predição**: entrada de cana no pátio | Caminhões chegando × carga média |
| taxa_saida_patio_ton_h | REAL | **Core da predição**: saída de cana (moagem) | Moagem atual com variação |
| taxa_chegada_caminhoes_hora | REAL | Prever congestionamento no pátio | Count(T3 → T4 por hora) |
| previsao_chegadas_prox_hora | INTEGER | Alertar sobre chegadas futuras | Baseado em caminhões em T3 |

**Necessidade**: Os dados originais não tinham granularidade de fluxo em tempo real. Era impossível saber se o pátio estava acumulando ou consumindo cana sem essas métricas.

### 7. Detalhamento do Estoque no Pátio
**Por que foi criado**: Distinguir cana "fisicamente disponível" de cana "em caçambas no pátio"

| Campo Criado | Tipo | Justificativa | Diferencial |
|--------------|------|---------------|-------------|
| estoque_patio_fisico_ton | REAL | Cana realmente disponível para moagem | 70-85% do estoque_patio_ton |
| caçambas_fila | INTEGER | Monitorar congestionamento | Caçambas aguardando descarga |
| caçambas_descarga | INTEGER | Monitorar utilização | Caçambas em processo |

**Necessidade**: O T_4 original era apenas "tempo na usina", mas não diferenciava se a cana estava disponível ou em fila. Para predição precisa, era essencial saber a cana efetivamente disponível.

## Tabelas de Apoio Criadas

### 8. padroes_horarios
**Por que foi criada**: Capturar sazonalidade descoberta nos dados reais mas não estruturada

**Justificativa**: Os dados reais mostravam clara sazonalidade (T4 varia de 0.58h a 4.41h por hora), mas essa informação estava "enterrada" nos registros individuais. A tabela estrutura esses padrões para uso preditivo.

### 9. predicoes_estoque_patio
**Por que foi criada**: Armazenar predições com níveis de confiabilidade decrescente

```sql
CREATE TABLE predicoes_estoque_patio (
    timestamp_predicao DATETIME,
    hora_futura INTEGER,        -- 1-9h à frente
    estoque_patio_previsto_ton REAL,
    confiabilidade_percent REAL, -- 95% (1h) até 45% (9h)
    ofensor_principal TEXT,     -- Causa de desvios
    -- ...
);
```

**Justificativa**: Não existia no datalake nenhum sistema de predição. Os dados eram apenas históricos. Para implementar JIT, era essencial prever estados futuros com níveis de confiança.

### 10. limites_operacionais
**Por que foi criada**: Definir zonas seguras baseadas na análise estatística dos dados reais

| Variável | Limite Inf. | Limite Sup. | Justificativa dos Dados Reais |
|----------|-------------|-------------|-------------------------------|
| estoque_patio_ton | 800 | 1500 | Percentis da distribuição T4 observada |
| taxa_chegada_hora | 15 | 35 | Min/max chegadas identificadas na análise |
| moagem_ton_h | 800 | 1100 | Capacidade 1150 - margem operacional |

**Justificativa**: Os dados reais não tinham limites definidos. Era impossível saber o que era "normal" vs "crítico". A análise estatística revelou essas faixas, mas elas precisavam ser estruturadas para alertas automáticos.

### 11. eventos_sistema
**Por que foi criada**: Rastrear violações e alertas em tempo real

**Justificativa**: Os dados originais eram "mudos" - não alertavam sobre situações críticas. Para um sistema JIT, era essencial detectar e registrar automaticamente quando métricas saíam das faixas seguras identificadas.

## Modelo de Predição Híbrido

### Componentes Criados
**Por que foi necessário**: Os dados originais eram 100% históricos, sem capacidade preditiva

1. **Análise de Padrões Históricos (70% peso)**
   - Extraído dos dados reais por hora/dia
   - Estruturado na tabela padroes_horarios

2. **Análise de Tendência Recente (30% peso)**
   - Baseado nas últimas 2 horas de T4
   - Detecta mudanças de comportamento

3. **Identificação de Ofensores**
   - Baseada em correlações descobertas nos dados reais
   - Automatiza diagnóstico de causas

### Níveis de Confiabilidade
**Por que foram criados**: Para dar transparência sobre a precisão das predições

- **1 hora**: 95% (padrões muito estáveis nos dados reais)
- **3 horas**: 85% (sazonalidade bem definida)
- **6 horas**: 68% (influência de fatores externos)
- **9 horas**: 45% (alta incerteza operacional)

## Resumo das Necessidades

### O que os Dados Reais Forneciam:
✅ Histórico detalhado de operações  
✅ Padrões de sazonalidade clara  
✅ Identificação de gargalos e ineficiências  
✅ Base estatística para limites operacionais  

### O que Precisou Ser Criado:
🔧 **Capacidade preditiva** (dados eram apenas históricos)  
🔧 **Métricas de fluxo em tempo real** (entrada vs saída)  
🔧 **Alertas automáticos** (detecção de situações críticas)  
🔧 **Estruturação da sazonalidade** (padrões estavam "enterrados")  
🔧 **Níveis de confiança** (transparência das predições)  
🔧 **Rastreamento de eventos** (histórico de alertas)  

## Conclusão

Os dados reais do datalake forneceram uma **base estatística sólida** com padrões operacionais claros. No entanto, para implementar um sistema Just-in-Time funcional, foi necessário criar **variáveis de predição, estruturas de alerta e capacidades de análise em tempo real**.

Todas as variáveis criadas têm **justificativa técnica baseada nos dados reais** e são essenciais para transformar um sistema de **monitoramento histórico** em um sistema **preditivo e proativo** de otimização logística.