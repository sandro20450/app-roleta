import streamlit as st
import requests
from datetime import datetime, timezone, timedelta

# 1. A SUA CHAVE DE ACESSO (Já configurada)
API_KEY = "06a0a753d3cb6191c16c3a0ec17dbf50" 

# --- FILTRO DE CASAS BRASILEIRAS ---
# Lista atualizada com as suas casas. Mantidas em minúsculas para o filtro não falhar.
casas_brasileiras = [
    "bet365", "betano", "betfair", "pinnacle", "1xbet", 
    "betway", "888sport", "sportingbet", "bwin", "marathonbet", "william hill",
    "kto", "f12 bet", "superbet", "mostbet", "pixbet"
]

st.title("⚽ Radar de Arbitragem Esportiva")
st.info("Varrendo o mercado em busca de lucro matemático (Surebets). Apenas jogos futuros e casas BR.")

st.write("---")
liga_escolhida = st.selectbox(
    "Selecione o Campeonato para rastrear:",
    [
        ("Futebol Brasileiro (Série A)", "soccer_brazil_campeonato"),
        ("Liga dos Campeões (UEFA)", "soccer_uefa_champs_league"),
        ("Campeonato Inglês (Premier League)", "soccer_epl"),
        ("Campeonato Espanhol (La Liga)", "soccer_spain_la_liga")
    ],
    format_func=lambda x: x[0]
)

esporte_id = liga_escolhida[1]

# O BOTÃO DE VARREDURA
if st.button("🚀 Iniciar Varredura de Odds (Filtro BR + Idade da Odd)"):
    with st.spinner('Conectando aos servidores das casas de apostas...'):
        url = f"https://api.the-odds-api.com/v4/sports/{esporte_id}/odds/?apiKey={API_KEY}&regions=eu,uk,us&markets=h2h"
        
        resposta = requests.get(url)
        
        if resposta.status_code != 200:
            st.error(f"Erro ao conectar com a API. Código: {resposta.status_code}. Verifique sua chave.")
        else:
            jogos = resposta.json()
            
            if not jogos:
                st.warning("Nenhum jogo encontrado para esta liga com odds abertas no momento.")
            else:
                st.success(f"Radar ativo! Analisando jogos...")
                
                oportunidades_encontradas = 0
                agora_utc = datetime.now(timezone.utc)
                
                for jogo in jogos:
                    # --- FILTRO DE TEMPO (Apenas jogos futuros) ---
                    horario_jogo_str = jogo['commence_time']
                    horario_jogo_utc = datetime.strptime(horario_jogo_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                    
                    if horario_jogo_utc < agora_utc:
                        continue # Pula jogos que já começaram
                    
                    horario_brasilia = horario_jogo_utc - timedelta(hours=3)
                    data_hora_formatada = horario_brasilia.strftime("%d/%m/%Y às %H:%M")
                    
                    time_casa = jogo['home_team']
                    time_fora = jogo['away_team']
                    
                    melhor_odd_casa, melhor_odd_empate, melhor_odd_fora = 0.0, 0.0, 0.0
                    casa_da_odd_casa, casa_da_odd_empate, casa_da_odd_fora = "", "", ""
                    
                    # Variáveis para rastrear a idade da odd
                    idade_casa, idade_empate, idade_fora = 999, 999, 999
                    
                    for bookmaker in jogo['bookmakers']:
                        nome_casa = bookmaker['title']
                        nome_casa_minusculo = nome_casa.lower()
                        
                        # Filtro Vip: Apenas casas da lista
                        if not any(casa_br in nome_casa_minusculo for casa_br in casas_brasileiras):
                            continue 
                        
                        # Calcula a idade da odd (atraso da leitura)
                        ultima_att_str = bookmaker['last_update']
                        ultima_att_utc = datetime.strptime(ultima_att_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                        minutos_atras = int((agora_utc - ultima_att_utc).total_seconds() / 60)
                        
                        mercados = bookmaker['markets']
                        
                        for mercado in mercados:
                            if mercado['key'] == 'h2h':
                                for opcao in mercado['outcomes']:
                                    odd = opcao['price']
                                    nome_opcao = opcao['name']
                                    
                                    if nome_opcao == time_casa and odd > melhor_odd_casa:
                                        melhor_odd_casa = odd
                                        casa_da_odd_casa = nome_casa
                                        idade_casa = minutos_atras
                                    elif nome_opcao == 'Draw' and odd > melhor_odd_empate:
                                        melhor_odd_empate = odd
                                        casa_da_odd_empate = nome_casa
                                        idade_empate = minutos_atras
                                    elif nome_opcao == time_fora and odd > melhor_odd_fora:
                                        melhor_odd_fora = odd
                                        casa_da_odd_fora = nome_casa
                                        idade_fora = minutos_atras

                    # O CÁLCULO MATEMÁTICO (SUREBET)
                    if melhor_odd_casa > 0 and melhor_odd_empate > 0 and melhor_odd_fora > 0:
                        margem = (1 / melhor_odd_casa) + (1 / melhor_odd_empate) + (1 / melhor_odd_fora)
                        
                        # Exige pelo menos 0.5% de lucro para evitar "poeira" de mercado
                        if margem < 0.995: 
                            oportunidades_encontradas += 1
                            lucro_pct = (1.0 - margem) * 100
                            
                            st.write("---")
                            st.success(f"🎯 **SUREBET ENCONTRADA:** Lucro de **{lucro_pct:.2f}%**")
                            st.write(f"**⚽ {time_casa} x {time_fora}**")
                            st.write(f"🕒 **Início do Jogo:** {data_hora_formatada} (Brasília)")
                            
                            st.caption(f"⏱️ **Atraso da leitura:** Casa ({idade_casa} min) | Empate ({idade_empate} min) | Fora ({idade_fora} min)")
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric(label=f"Vit. Casa ({casa_da_odd_casa})", value=f"{melhor_odd_casa}")
                            with col2:
                                st.metric(label=f"Empate ({casa_da_odd_empate})", value=f"{melhor_odd_empate}")
                            with col3:
                                st.metric(label=f"Vit. Fora ({casa_da_odd_fora})", value=f"{melhor_odd_fora}")
                                
                            st.code(f"""
Para R$ 1.000 investidos:
- R$ {(1000/melhor_odd_casa)/margem:.2f} na casa '{casa_da_odd_casa}'
- R$ {(1000/melhor_odd_empate)/margem:.2f} na casa '{casa_da_odd_empate}'
- R$ {(1000/melhor_odd_fora)/margem:.2f} na casa '{casa_da_odd_fora}'
-------------------------
Retorno Limpo em qualquer cenário: R$ {(1000/margem):.2f}
                            """)

                if oportunidades_encontradas == 0:
                    st.info("Varredura concluída. As odds estão alinhadas ou o lucro é menor que 0.5%. Tente novamente nos horários de pico (pré-jogos).")

st.write("---")

# --- PAINEL DE LEMBRETE TÁTICO DOS HORÁRIOS ---
st.markdown("""
### ⏰ Lembrete Tático: Horários Nobres de Varredura
O mercado de apostas corrige erros rápido. Concentre suas varreduras nestes momentos de "estresse" nas linhas, onde as distorções acontecem:

1. **Sexta-feira (Noite) e Sábado (Manhã cedo):** Abertura das linhas de fim de semana das casas europeias. As casas brasileiras demoram a copiar e geram erros grandes.
2. **1 a 2 horas antes do jogo:** Anúncio das escalações oficiais. Lesões ou craques poupados fazem as odds oscilarem violentamente.
3. **Terças e Quartas (13h às 15h - Horário de Brasília):** Foco nas rodadas da Liga dos Campeões (UEFA) e torneios europeus.
""")
