import streamlit as st
import requests

# 1. A SUA CHAVE DE ACESSO
API_KEY = "06a0a753d3cb6191c16c3a0ec17dbf50" 

# --- NOVA TÁTICA: FILTRO DE CASAS BRASILEIRAS ---
# O aplicativo só vai aceitar odds se o nome da casa estiver nesta lista.
# Você pode adicionar ou remover nomes depois, se quiser.
casas_brasileiras = [
    "bet365", "betano", "betfair", "pinnacle", "1xbet", 
    "betway", "888sport", "sportingbet", "bwin", "marathonbet", "william hill"
]

st.title("⚽ Radar de Arbitragem Esportiva")
st.info("Varrendo o mercado de apostas em busca de lucro matemático (Surebets) focando apenas em casas que operam no Brasil.")

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

if st.button("🚀 Iniciar Varredura de Odds (Filtro BR)"):
    if API_KEY == "COLE_SUA_CHAVE_AQUI" or API_KEY == "":
        st.error("⚠️ Alerta tático: Você esqueceu de colocar a sua API Key na linha 5 do código!")
    else:
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
                    st.success(f"Radar ativo! Analisando {len(jogos)} jogos usando apenas as Casas Brasileiras...")
                    
                    oportunidades_encontradas = 0
                    
                    for jogo in jogos:
                        time_casa = jogo['home_team']
                        time_fora = jogo['away_team']
                        
                        melhor_odd_casa = 0.0
                        casa_da_odd_casa = ""
                        melhor_odd_empate = 0.0
                        casa_da_odd_empate = ""
                        melhor_odd_fora = 0.0
                        casa_da_odd_fora = ""
                        
                        for bookmaker in jogo['bookmakers']:
                            nome_casa = bookmaker['title']
                            
                            # A MÁGICA DO FILTRO ACONTECE AQUI
                            # Ele transforma o nome da casa em letras minúsculas e checa se está na nossa lista VIP
                            nome_casa_minusculo = nome_casa.lower()
                            if not any(casa_br in nome_casa_minusculo for casa_br in casas_brasileiras):
                                continue # Se não for uma casa brasileira, ele pula e ignora as odds dela
                            
                            mercados = bookmaker['markets']
                            
                            for mercado in mercados:
                                if mercado['key'] == 'h2h':
                                    for opcao in mercado['outcomes']:
                                        odd = opcao['price']
                                        nome_opcao = opcao['name']
                                        
                                        if nome_opcao == time_casa and odd > melhor_odd_casa:
                                            melhor_odd_casa = odd
                                            casa_da_odd_casa = nome_casa
                                        elif nome_opcao == 'Draw' and odd > melhor_odd_empate:
                                            melhor_odd_empate = odd
                                            casa_da_odd_empate = nome_casa
                                        elif nome_opcao == time_fora and odd > melhor_odd_fora:
                                            melhor_odd_fora = odd
                                            casa_da_odd_fora = nome_casa

                        # O CÁLCULO DE ARBITRAGEM
                        if melhor_odd_casa > 0 and melhor_odd_empate > 0 and melhor_odd_fora > 0:
                            margem = (1 / melhor_odd_casa) + (1 / melhor_odd_empate) + (1 / melhor_odd_fora)
                            
                            if margem < 1.0:
                                oportunidades_encontradas += 1
                                lucro_pct = (1.0 - margem) * 100
                                
                                st.write("---")
                                st.success(f"🎯 **SUREBET ENCONTRADA:** Lucro de **{lucro_pct:.2f}%**")
                                st.write(f"**⚽ {time_casa} x {time_fora}**")
                                
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
                        st.info("Varredura concluída. As odds entre as casas brasileiras estão alinhadas neste momento. Tente novamente mais tarde para buscar novas brechas.")
