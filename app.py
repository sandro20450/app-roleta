import streamlit as st

st.title("🎯 Roleta Tracker - 12 Segundos")

# 1. MEMÓRIA RÁPIDA
if 'historico' not in st.session_state:
    st.session_state.historico = []

# 2. FUNÇÕES DE MAPEAMENTO
def qual_duzia(n):
    if n == 0: return 0
    if 1 <= n <= 12: return 1
    if 13 <= n <= 24: return 2
    if 25 <= n <= 36: return 3

def qual_linha(n):
    if n == 0: return 0
    if n % 3 == 1: return 1
    if n % 3 == 2: return 2
    if n % 3 == 0: return 3

# 3. O CÉREBRO E OS ALERTAS INTELIGENTES
alertas_verdes = []

if len(st.session_state.historico) > 0:
    def contar_atraso(funcao_mapeamento, valor_alvo):
        atraso = 0
        for num in reversed(st.session_state.historico):
            if funcao_mapeamento(num) == valor_alvo:
                break
            atraso += 1
        return atraso

    # Calculando os atrasos exatos
    atrasos = {
        "d1": contar_atraso(qual_duzia, 1),
        "d2": contar_atraso(qual_duzia, 2),
        "d3": contar_atraso(qual_duzia, 3),
        "l1": contar_atraso(qual_linha, 1),
        "l2": contar_atraso(qual_linha, 2),
        "l3": contar_atraso(qual_linha, 3)
    }

    ultimo_num = st.session_state.historico[-1]
    duzia_atual = qual_duzia(ultimo_num)
    linha_atual = qual_linha(ultimo_num)

    # Identificando quem passou de 5 atrasos
    duzias_atrasadas = [(i, atrasos[f"d{i}"]) for i in range(1, 4) if atrasos[f"d{i}"] >= 5]
    linhas_atrasadas = [(i, atrasos[f"l{i}"]) for i in range(1, 4) if atrasos[f"l{i}"] >= 5]

    # NOVA REGRA DAS DÚZIAS
    if len(duzias_atrasadas) >= 2:
        d1_nome, d1_val = duzias_atrasadas[0]
        d2_nome, d2_val = duzias_atrasadas[1]
        alertas_verdes.append(f"💤 **APOSTE:** {d1_nome}ª Dúzia + {d2_nome}ª Dúzia (Ambas muito atrasadas: {d1_val} e {d2_val}).")
    elif len(duzias_atrasadas) == 1:
        d_nome, d_val = duzias_atrasadas[0]
        if duzia_atual != 0:
            alertas_verdes.append(f"💤 **APOSTE:** {d_nome}ª Dúzia + {duzia_atual}ª Dúzia (Última que saiu). *Atraso: {d_val}*")

    # NOVA REGRA DAS LINHAS
    if len(linhas_atrasadas) >= 2:
        l1_nome, l1_val = linhas_atrasadas[0]
        l2_nome, l2_val = linhas_atrasadas[1]
        alertas_verdes.append(f"🧵 **APOSTE:** {l1_nome}ª Linha + {l2_nome}ª Linha (Ambas muito atrasadas: {l1_val} e {l2_val}).")
    elif len(linhas_atrasadas) == 1:
        l_nome, l_val = linhas_atrasadas[0]
        if linha_atual != 0:
            alertas_verdes.append(f"🧵 **APOSTE:** {l_nome}ª Linha + {linha_atual}ª Linha (Última que saiu). *Atraso: {l_val}*")

# 4. EXIBINDO OS ALERTAS NO TOPO
if alertas_verdes:
    for alerta in alertas_verdes:
        st.success(alerta)
elif len(st.session_state.historico) > 0:
    st.info("Monitorando padrões... Registe o próximo número.")

# 5. ÁREA DE ENTRADA (Com Enter e Limpeza Automática)
st.write("**Digite o número (0 a 36):**")
col_form, col_espaco, col_limpar = st.columns([3, 0.5, 1])

with col_form:
    # O clear_on_submit=True esvazia a caixa após o Enter
    with st.form("registro_form", clear_on_submit=True):
        col_input, col_btn = st.columns([2, 1])
        with col_input:
            # value=None deixa a caixa sem números iniciais
            numero_sorteado = st.number_input("Digite", min_value=0, max_value=36, step=1, value=None, label_visibility="collapsed")
        with col_btn:
            submit = st.form_submit_button("Registrar")
            if submit and numero_sorteado is not None:
                st.session_state.historico.append(int(numero_sorteado))
                st.rerun()

with col_limpar:
    if st.button("🗑️ Limpar"):
        st.session_state.historico = []
        st.rerun()

st.write("---")

# 6. PAINEL DE ATRASOS COMPACTO
if len(st.session_state.historico) > 0:
    st.write("**Atrasos Atuais:**")
    
    def formata_linha(nome, valor):
        icone = " 💚" if valor >= 5 else ""
        return f"- {nome}: **{valor}**{icone}"

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
        {formata_linha('1ª Dúzia', atrasos['d1'])}
        {formata_linha('2ª Dúzia', atrasos['d2'])}
        {formata_linha('3ª Dúzia', atrasos['d3'])}
        """)
    with col2:
        st.markdown(f"""
        {formata_linha('1ª Linha', atrasos['l1'])}
        {formata_linha('2ª Linha', atrasos['l2'])}
        {formata_linha('3ª Linha', atrasos['l3'])}
        """)
        
    st.caption(f"Últimos números registados: {st.session_state.historico}")
else:
    st.info("Nenhum número registado no momento.")
