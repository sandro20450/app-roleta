import streamlit as st
import requests

st.title("⚽ Radar de Arbitragem - Mercado Esportivo")

# Painel de instruções usando o componente nativo de informação
st.info("Conectando ao mercado... O radar varre as casas de apostas em busca de distorções matemáticas nas odds.")

st.write("---")

# Simulando a entrada de dados de uma API para você ver o visual nativo operando
# Em breve, substituiremos isso pela leitura real em tempo real da "The-Odds-API"
jogo_exemplo = "Palmeiras vs. River Plate"

# odds fictícias para demonstrar uma Surebet (Casa A pagando muito no Palmeiras, Casa B pagando muito no River)
odd_vitoria_casa = 2.50  # Encontrada na Bet365
odd_empate = 3.40        # Encontrada na Betano
odd_vitoria_fora = 3.80  # Encontrada na Pinnacle

# Exibindo as cotações com st.metric (Visual limpo e direto)
st.write(f"**Partida Mapeada:** {jogo_exemplo}")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Vitória (Mandante)", value=f"{odd_vitoria_casa}")
with col2:
    st.metric(label="Empate", value=f"{odd_empate}")
with col3:
    st.metric(label="Vitória (Visitante)", value=f"{odd_vitoria_fora}")

st.write("---")

# O CÉREBRO DA OPERAÇÃO: O Cálculo de Arbitragem
# Fórmula: (1 / Odd A) + (1 / Odd Empate) + (1 / Odd B)
margem_mercado = (1 / odd_vitoria_casa) + (1 / odd_empate) + (1 / odd_vitoria_fora)

if margem_mercado < 1.0:
    lucro_percentual = (1.0 - margem_mercado) * 100
    st.success(f"💰 **OPORTUNIDADE DE ARBITRAGEM DETECTADA!** Lucro garantido de **{lucro_percentual:.2f}%**.")
    
    st.write("**Instruções de Entrada (Para uma banca de R$ 1.000):**")
    # Cálculo de distribuição de apostas para garantir o mesmo retorno em qualquer cenário
    aposta_casa = (1000 / odd_vitoria_casa) / margem_mercado
    aposta_empate = (1000 / odd_empate) / margem_mercado
    aposta_fora = (1000 / odd_vitoria_fora) / margem_mercado
    
    st.code(f"""
    1. Aposte R$ {aposta_casa:.2f} na Vitória (Casa A)
    2. Aposte R$ {aposta_empate:.2f} no Empate (Casa B)
    3. Aposte R$ {aposta_fora:.2f} na Vitória Visitante (Casa C)
    
    Retorno total independentemente de quem vencer: R$ {(1000 / margem_mercado):.2f}
    """)
else:
    st.warning("Nenhuma distorção matemática encontrada para este jogo no momento. A casa ainda tem a vantagem.")
