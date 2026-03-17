import streamlit as st

st.title("🎯 Roleta Tracker - 12 Segundos")

# 1. MEMÓRIA RÁPIDA E CHAVE DE LIMPEZA
if 'historico' not in st.session_state:
    st.session_state.historico = []
# Esta variável vai mudar para recriar a caixa de texto sempre limpa
if 'chave_input' not in st.session_state:
    st.session_state.chave_input = 0

# A função do Enter agora recria a caixa instantaneamente
def registrar_numero():
    nome_da_chave = f"num_{st.session_state.chave_input}"
    num = st.session_state[nome_da_chave]
    if num is not None:
        st.session_state.historico.append(int(num))
        # Muda a chave, o que limpa a caixa sem dar erro
        st.session_state.chave_input += 1 

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

    duzias_atrasadas = [(i, atrasos[f"d{i}"]) for i in range(1, 4) if atrasos[f"d{i}"] >= 5]
    linhas_atrasadas = [(i, atrasos[f"l{i}"]) for i in range(1, 4) if atrasos[f"l{i}"] >= 5]

    # IDENTIFICANDO A REGRA DE OURO (Ambos atrasados)
    regra_de_ouro = len(duzias_atrasadas) > 0 and len(linhas_atrasadas) > 0
    emoji_moeda = " 💰 (REGRA DE OURO!)" if regra_de_ouro else ""

    # REGRAS DAS DÚZIAS
    if len(duzias_atrasadas) >= 2:
        d1_n, d1_v = duzias_atrasadas[0]
        d2_n, d2_v = duzias_atrasadas[1]
        alertas_verdes.append(f"💤 **APOSTE:** {d1_n}ª Dúzia + {d2_n}ª Dúzia (Atrasos: {d1_v} e {d2_v}).{emoji_moeda}")
    elif len(duzias_atrasadas) == 1:
        d_n, d_v = duzias_atrasadas[0]
        if duzia_atual != 0:
            alertas_verdes.append(f"💤 **APOSTE:** {d_n}ª Dúzia + {duzia_atual}ª Dúzia (Última que saiu). *Atraso: {d_v}*{emoji_moeda}")

    # REGRAS DAS LINHAS
    if len(linhas_atrasadas) >= 2:
        l1_n, l1_v = linhas_atrasadas[0]
        l2_n, l2_v = linhas_atrasadas[1]
        alertas_verdes.append(f"🧵 **APOSTE:** {l1_n}ª Linha + {l2_n}ª Linha (Atrasos: {l1_v} e {l2_v}).{emoji_moeda}")
    elif len(linhas_atrasadas) == 1:
        l_n, l_v = linhas_atrasadas[0]
        if linha_atual != 0:
            alertas_verdes.append(f"🧵 **APOSTE:** {l_n}ª Linha + {linha_atual}ª Linha (Última que saiu). *Atraso: {l_v}*{emoji_moeda}")

# 4. EXIBINDO OS ALERTAS NO TOPO
if alertas_verdes:
    for alerta in alertas_verdes:
        st.success(alerta)
elif len(st.session_state.historico) > 0:
    st.info("Monitorando padrões... Digite o próximo número e aperte ENTER.")

# 5. ÁREA DE ENTRADA (Com Enter Perfeito)
st.write("**Digite o número e aperte ENTER (0 a 36):**")
col_input, col_limpar = st.columns([3, 1])

with col_input:
    # A chave muda dinamicamente, evitando qualquer erro de estado
    st.number_input(
        "Digite", 
        min_value=0, max_value=36, step=1, value=None, 
        key=f"num_{st.session_state.chave_input}", 
        on_change=registrar_numero, 
        label_visibility="collapsed"
    )

with col_limpar:
    # O botão limpar agora reseta o histórico e também força a troca da chave
    if st.button("🗑️ Limpar"):
        st.session_state.historico = []
        st.session_state.chave_input += 1
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
        
    st.caption(f"Últimos números registrados: {st.session_state.historico}")
else:
    st.info("Nenhum número registrado no momento.")
