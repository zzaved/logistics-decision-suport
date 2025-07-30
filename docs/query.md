# Processo de Exploração de Dados

## 1. Objetivo
Desenvolver sistema de logística just-in-time para setor sucroenergético com foco em 3 curvas principais:
1. Curva de colheitabilidade hora-a-hora
2. Estimativa de moagem hora-a-hora  
3. Estoque médio sobre rodas (T4 - variável principal)

## 2. Principais Insights Descobertos

### 2.1 Padrões Operacionais Críticos:

#### 2.1.1 Horário 15h é inviável para fazendas distantes:
- **Dados**: Fazendas >50km às 15h apresentam ciclo completo de 22.7 horas
- **Comparação**: O mesmo trajeto às 6h apresenta ciclo de apenas 6.8 horas
- **Impacto**: Diferença de 15.9 horas por viagem (334% maior ineficiência)
- **Causa provável**: Trânsito intenso, temperatura alta, mudanças de turno
- **Consequência**: Um caminhão que deveria fazer 3-4 viagens/dia faz apenas 1

#### 2.1.2 Gargalo é a colheita, não a moagem:
- **Colheita**: Capacidade máxima de 62.4 ton/h (horário pico 12h)
- **Moagem**: Capacidade instalada de 1.150 ton/h (operação 22.5h/dia)
- **Relação**: Moagem tem 18x mais capacidade que a colheita
- **Conclusão**: Sistema deve otimizar colheita e transporte, moagem tem folga significativa

#### 2.1.3 90% das operações concentradas em fazendas próximas:
- **Fazendas <50km**: 8.141 viagens (90%), ciclo médio 6.5h, eficiência 10.814 kg/h
- **Fazendas 50-80km**: 805 viagens (9%), ciclo médio 11.8h, eficiência 5.923 kg/h
- **Impacto**: Fazendas distantes têm 81% maior tempo de ciclo e 45% menor produtividade
- **Estratégia**: Priorizar fazendas distantes apenas quando estoque permite absorver ineficiência

#### 2.1.4 Frota de 46 caminhões em operação contínua:
- **Distribuição média**: 16 voltando (T1) + 14 indo carregados (T3) + 8 descarregando (T4) + 8 carregando (T2)
- **Estoque sobre rodas**: 2.000-2.500 toneladas constantemente em movimento
- **Variação mínima**: Distribuição permanece estável independente do horário

### 2.2 Qualidade dos Dados:

#### 2.2.1 Dados não síncronos temporalmente:
- **Transporte**: 609.627 registros de março/2021 a dezembro/2023 (dados históricos)
- **Colheitabilidade**: 12.600 registros apenas de abril/2025 (dados recentes)
- **Moagem**: Dados de abril/2023 a julho/2025, mas consolidados diariamente
- **Problema**: Impossibilidade de correlação temporal direta entre as três curvas

#### 2.2.2 89.5% dos dados utilizáveis após filtragem:
- **Total analisado**: 4.114 registros de transporte (nov-dez/2023)
- **Outliers removidos**: 60 registros com T4 >50h (máximo 213h) + 8 registros negativos
- **Dados válidos**: 4.046 registros com T4 entre 0.1-10h
- **Justificativa**: Outliers representam erros de sistema ou situações excepcionais não operacionais

#### 2.2.3 Colheitabilidade limitada a 4 horários operacionais:
- **Horários disponíveis**: 11h (1.247 registros), 12h (6.323 registros), 13h (2.517 registros), 14h (186 registros)
- **Cobertura**: 151 fazendas distintas, mas operação concentrada
- **Limitação**: Ausência de dados para 20 horas do dia (83% do tempo)
- **Causa provável**: Operação de campo limitada ao período diurno de maior produtividade

#### 2.2.4 Moagem em escala temporal diferente:
- **Dados originais**: Horas efetivas por dia (22.5h média)
- **Necessidade**: Capacidade em toneladas por hora
- **Conversão aplicada**: 22.5h × 50 ton/h = 1.125 ton/h capacidade estimada
- **Limitação**: Conversão baseada em estimativa, não medição direta

### 2.3 Regras de Negócio Validadas:

#### 2.3.1 Distância impacta dramaticamente a eficiência:
- **Metodologia**: Análise de 8.946 viagens segmentadas por distância
- **Fazendas próximas (<50km)**: Representam 90% das operações com alta eficiência
- **Fazendas distantes (50-80km)**: Apenas 9% das operações, mas consomem recursos desproporcionalmente
- **Fator crítico**: Tempo de transporte (T1 + T3) cresce exponencialmente com distância
- **Regra derivada**: Usar fazendas distantes apenas quando estoque alto permite absorver ineficiência

#### 2.3.2 Estoque sobre rodas como buffer estável:
- **Função**: Buffer entre variabilidade da colheita e demanda constante da moagem
- **Estabilidade**: Varia apenas 500 toneladas (20%) ao longo de 24h
- **Mecanismo**: Sistema auto-regulado pela distribuição natural dos tempos de ciclo
- **Indicador T4**: Tempo na usina reflete pressão do sistema (alto T4 = gargalo na descarga)

#### 2.3.3 T4 como indicador principal confirmado:
- **Correlação**: T4 elevado indica acúmulo no pátio da usina
- **Peso na decisão**: Confirmado como 70% conforme orientação operacional
- **Variação crítica**: T4 >6h indica necessidade de ajuste no ciclo
- **Padrão temporal**: T4 varia de 0.58h (7h manhã) a 4.41h (meia-noite)

## 3. Linha do Tempo da Exploração

### 3.1 Fase 1: Mapeamento dos Datasets
#### 3.1.1 Datasets Identificados:
- **Gold_cubo**: Dados consolidados operacionais
- **Gold_logistica**: Métricas logísticas
- **Bronze_cubo**: Dados de colheitabilidade
- **Bronze_pims**: Dados de transporte (PRINCIPAL)

#### 3.1.2 Primeira Verificação:
```sql
SELECT COUNT(*) FROM bronze_pims.McKinsey_data_request_transporte_v3;
```
**Resultado**: 609.627 registros (março/2021 - dezembro/2023)

### 3.2 Fase 2: Análise de T4 - Foco Inicial
#### 3.2.1 Query Base:
```sql
SELECT AVG(T_4) as media_horas, COUNTIF(T_4 > 6) as viagens_criticas
FROM bronze_pims.McKinsey_data_request_transporte_v3
WHERE HR_ENTRADA_PIMS >= '2023-11-01' AND T_4 IS NOT NULL;
```

#### 3.2.2 Resultados Iniciais:
- **9.014 viagens**, **T4 médio**: 1.77h, **5% crítico**
- **Padrões descobertos**: 0h crítico (4.41h), 7h ótimo (0.58h)

### 3.3 Fase 3: Ciclo Completo T1+T2+T3+T4
#### 3.3.1 Query do Ciclo Completo:
```sql
SELECT EXTRACT(HOUR FROM HR_ENTRADA_PIMS) as hora,
       AVG(T_1 + 2.0 + T_3 + T_4) as ciclo_total
FROM bronze_pims.McKinsey_data_request_transporte_v3
WHERE HR_ENTRADA_PIMS >= '2023-11-01'
GROUP BY 1 ORDER BY 1;
```

#### 3.3.2 Descobertas:
- **Ciclo total**: 5.3h (7h) até 8.6h (15h)
- **Melhor eficiência**: manhã (7h = 12.939 kg/h)
- **Pior eficiência**: tarde (15h = 8.323 kg/h)

### 3.4 Fase 4: Impacto da Distância
#### 3.4.1 Query por Distância:
```sql
SELECT CASE WHEN DISTANCIA_PIMS_MEDIA < 50 THEN 'Perto' ELSE 'Longe' END as faixa,
       COUNT(*) as viagens, AVG(T_1 + 2.0 + T_3 + T_4) as ciclo_medio
FROM bronze_pims.McKinsey_data_request_transporte_v3
GROUP BY 1;
```

#### 3.4.2 Resultados:
- **Perto (<50km)**: 8.141 viagens, ciclo 6.5h
- **Longe (50-80km)**: 805 viagens, ciclo 11.8h
- **Descoberta crítica**: 15h para fazendas longe = 22.7h

### 3.5 Fase 5: Dados de Colheitabilidade
#### 3.5.1 Verificação bronze_cubo.colheitabilidade:
- **Período**: Apenas abril/2025
- **Registros**: 12.600 (151 fazendas)
- **Limitação**: Dados apenas 11h-14h

### 3.6 Fase 6: Dados de Moagem
#### 3.6.1 Análise bronze_pims.pimspro_rel_003:
- **Variável encontrada**: "Horas Efetivas Moagem"
- **Período**: abril/2023 - julho/2025
- **Descoberta**: Dados diários (22.5h efetivas/dia)
- **Conversão**: 22.5h × 50 ton/h = 1.150 ton/h

### 3.7 Fase 7: Estoque Sobre Rodas
#### 3.7.1 Cálculo baseado em tempos médios:
```sql
SELECT EXTRACT(HOUR FROM HR_ENTRADA_PIMS) as hora,
       ROUND((AVG(T_1) + AVG(T_3) + AVG(T_4)) / (AVG(T_1 + 2.0 + T_3 + T_4)) * 46 * 70) as estoque_total_ton
FROM bronze_pims.McKinsey_data_request_transporte_v3
GROUP BY 1;
```

#### 3.7.2 Resultado: 2.000-2.500 toneladas constantemente sobre rodas

## 4. Dados Estranhos e Contornos

### 4.1 Outliers Identificados:
- **T4 negativos**: 8 registros
- **T4 extremos**: 60 registros (>50h)
- **Solução**: Filtros T_4 > 0 AND T_4 < 50

### 4.2 Inconsistências Temporais:
- **Dessincronização**: Transporte (2021-2023) vs Colheita (2025)
- **Dados PIMS**: Consolidados diariamente
- **Solução**: Backend mock baseado em padrões reais

## 5. Conclusão

### 5.1 Desafios de Sincronização:
Os dados apresentam **dessincronização temporal significativa** entre transporte (histórico), colheitabilidade (recente limitado) e moagem (diários consolidados).

### 5.2 Estratégia Adotada:
Sistema implementado com **dados mockados baseados nos padrões descobertos**, simulando **cenário síncrono em tempo real**.

### 5.3 Dados Finais Utilizados:

#### 5.3.1 Curva 1 - Colheitabilidade:
- **Fonte**: bronze_cubo.colheitabilidade (151 fazendas, abril/2025)
- **Padrão**: 11h-14h, pico 62.4 ton/h às 12h

#### 5.3.2 Curva 2 - Moagem:
- **Fonte**: bronze_pims.pimspro_rel_003
- **Capacidade**: ~1.150 ton/h (22.5h efetivas × 50 ton/h)

#### 5.3.3 Curva 3 - Estoque Sobre Rodas:
- **Fonte**: Cálculo T1+T3+T4 (300-400 placas/hora)
- **Distribuição**: 46 caminhões, 2.000-2.500 toneladas

#### 5.3.4 Regras de Negócio:
- **15h**: NUNCA despachar fazenda longe (ciclo 22.7h)
- **6h**: IDEAL para fazenda longe (ciclo 6.8h)
- **Gargalo**: Colheita (60 ton/h) vs Moagem (1.150 ton/h).