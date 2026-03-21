import streamlit as st
import streamlit.components.v1 as components

st.title("🎯 Roleta Tracker - 12 Segundos")

# 1. MEMÓRIA RÁPIDA E CHAVE DE LIMPEZA
if 'historico' not in st.session_state:
    st.session_state.historico = []
if 'chave_input' not in st.session_state:
    st.session_state.chave_input = 0

def registrar_numero():
    nome_da_chave = f"num_{st.session_state.chave_input}"
    num = st.session_state[nome_da_chave]
    if num is not None:
        st.session_state.historico.append(int(num))
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

def qual_ipt(n):
    if n == 0: return '0'
    if 1 <= n <= 24:
        return 'I' if n % 2 != 0 else 'P'
    if 25 <= n <= 36:
        return 'T'

def qual_123(n):
    if n == 0: return '0'
    if n in [1, 7, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]: return '1'
    if n in [2, 8, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29]: return '2'
    if n in [3, 4, 5, 6, 9, 30, 31, 32, 33, 34, 35, 36]: return '3'

# --- NOVA ÁREA: ABASTECIMENTO EM LOTE (Para o início do jogo) ---
with st.expander("📥 Inserir Histórico Inicial (Lote)"):
    lote_input = st.text_input("Cole os números separados por vírgula (Ex: 14, 15, 32, 0):")
    if st.button("Carregar Histórico"):
        try:
            # Limpa o histórico atual e carrega os novos
            st.session_state.historico = [int(x.strip()) for x in lote_input.split(',') if x.strip().isdigit()]
            st.session_state.chave_input += 1
            st.success(f"✅ {len(st.session_state.historico)} números carregados com sucesso!")
        except Exception as e:
            st.error("Erro ao carregar. Certifique-se de usar apenas números e vírgulas.")
st.write("---")

# 3. O CÉREBRO E OS ALERTAS INTELIGENTES
alertas_verdes = []
alertas_amarelos = []

if len(st.session_state.historico) > 0:
    def contar_atraso(funcao_mapeamento, valor_alvo):
        atraso = 0
        for num in reversed(st.session_state.historico):
            if funcao_mapeamento(num) == valor_alvo:
                break
            atraso += 1
        return atraso

    atrasos = {
        "d1": contar_atraso(qual_duzia, 1), "d2": contar_atraso(qual_duzia, 2), "d3": contar_atraso(qual_duzia, 3),
        "l1": contar_atraso(qual_linha, 1), "l2": contar_atraso(qual_linha, 2), "l3": contar_atraso(qual_linha, 3)
    }

    ultimo_num = st.session_state.historico[-1]
    duzia_atual = qual_duzia(ultimo_num)
    linha_atual = qual_linha(ultimo_num)

    duzias_atrasadas = [(i, atrasos[f"d{i}"]) for i in range(1, 4) if atrasos[f"d{i}"] >= 5]
    linhas_atrasadas = [(i, atrasos[f"l{i}"]) for i in range(1, 4) if atrasos[f"l{i}"] >= 5]

    regra_de_ouro = len(duzias_atrasadas) > 0 and len(linhas_atrasadas) > 0
    emoji_moeda = " 💰 (REGRA DE OURO!)" if regra_de_ouro else ""

    if len(duzias_atrasadas) >= 2:
        d1_n, d1_v = duzias_atrasadas[0]
        d2_n, d2_v = duzias_atrasadas[1]
        alertas_verdes.append(f"💤 **APOSTE:** {d1_n}ª Dúzia + {d2_n}ª Dúzia (Atrasos: {d1_v} e {d2_v}).")
    elif len(duzias_atrasadas) == 1:
        d_n, d_v = duzias_atrasadas[0]
        if duzia_atual != 0:
            if regra_de_ouro:
                alertas_verdes.append(f"💤 **APOSTE:** {d_n}ª Dúzia! *Atraso: {d_v}*{emoji_moeda}")
            else:
                alertas_verdes.append(f"💤 **APOSTE:** {d_n}ª Dúzia + {duzia_atual}ª Dúzia (Última que saiu). *Atraso: {d_v}*")

    if len(linhas_atrasadas) >= 2:
        l1_n, l1_v = linhas_atrasadas[0]
        l2_n, l2_v = linhas_atrasadas[1]
        alertas_verdes.append(f"🧵 **APOSTE:** {l1_n}ª Linha + {l2_n}ª Linha (Atrasos: {l1_v} e {l2_v}).")
    elif len(linhas_atrasadas) == 1:
        l_n, l_v = linhas_atrasadas[0]
        if linha_atual != 0:
            if regra_de_ouro:
                alertas_verdes.append(f"🧵 **APOSTE:** {l_n}ª Linha! *Atraso: {l_v}*{emoji_moeda}")
            else:
                alertas_verdes.append(f"🧵 **APOSTE:** {l_n}ª Linha + {linha_atual}ª Linha (Última que saiu). *Atraso: {l_v}*")

    if len(st.session_state.historico) >= 3:
        ultimos_3_ipt = st.session_state.historico[-3:]
        grupos_3_ipt = [qual_ipt(n) for n in ultimos_3_ipt]
        if grupos_3_ipt[0] == grupos_3_ipt[1] == grupos_3_ipt[2] and grupos_3_ipt[0] != '0':
            if grupos_3_ipt[0] == 'I': alertas_amarelos.append("⚡ **ESTRATÉGIA IPT:** Grupo **I** saiu 3x seguidas! APOSTE: **P** + **T**.")
            elif grupos_3_ipt[0] == 'P': alertas_amarelos.append("⚡ **ESTRATÉGIA IPT:** Grupo **P** saiu 3x seguidas! APOSTE: **I** + **T**.")
            elif grupos_3_ipt[0] == 'T': alertas_amarelos.append("⚡ **ESTRATÉGIA IPT:** Grupo **T** saiu 3x seguidas! APOSTE: **I** + **P**.")

    if len(st.session_state.historico) >= 3:
        ultimos_3_123 = st.session_state.historico[-3:]
        grupos_3_123 = [qual_123(n) for n in ultimos_3_123]
        if grupos_3_123[0] == grupos_3_123[1] == grupos_3_123[2] and grupos_3_123[0] != '0':
            if grupos_3_123[0] == '1': alertas_amarelos.append("🔥 **ESTRATÉGIA 123:** Conjunto **1** saiu 3x seguidas! APOSTE: **Conjunto 2** + **Conjunto 3**.")
            elif grupos_3_123[0] == '2': alertas_amarelos.append("🔥 **ESTRATÉGIA 123:** Conjunto **2** saiu 3x seguidas! APOSTE: **Conjunto 1** + **Conjunto 3**.")
            elif grupos_3_123[0] == '3': alertas_amarelos.append("🔥 **ESTRATÉGIA 123:** Conjunto **3** saiu 3x seguidas! APOSTE: **Conjunto 1** + **Conjunto 2**.")

# 4. EXIBINDO OS ALERTAS NO TOPO
if alertas_amarelos:
    for alerta in alertas_amarelos:
        st.warning(alerta)
if alertas_verdes:
    for alerta in alertas_verdes:
        st.success(alerta)
if not alertas_verdes and not alertas_amarelos and len(st.session_state.historico) > 0:
    st.info("Monitorando padrões... Digite o próximo número e aperte ENTER.")

# 5. ÁREA DE ENTRADA
st.write("**Digite o número e aperte ENTER (0 a 36):**")
col_input, col_limpar = st.columns([3, 1])

with col_input:
    st.number_input(
        "Digite", min_value=0, max_value=36, step=1, value=None, 
        key=f"num_{st.session_state.chave_input}", 
        on_change=registrar_numero, label_visibility="collapsed"
    )

with col_limpar:
    if st.button("🗑️ Limpar Tudo"):
        st.session_state.historico = []
        st.session_state.chave_input += 1
        st.rerun()

# --- TRUQUE DO FOCO AUTOMÁTICO (Corrigido com atraso para o Streamlit respirar) ---
components.html(
    f"""
    <script id="foco_{st.session_state.chave_input}">
    setTimeout(function() {{
        const doc = window.parent.document;
        const inputs = doc.querySelectorAll('input[type="number"]');
        if (inputs.length > 0) {{
            inputs[0].focus();
        }}
    }}, 100); // 100 milissegundos de atraso garantem que a caixa já foi criada
    </script>
    """,
    height=0, width=0
)
# ---------------------------------------------

st.write("---")

# 6. PAINEL DE ATRASOS COMPACTO E HISTÓRICO
if len(st.session_state.historico) > 0:
    st.write("**Atrasos Atuais:**")
    def formata_linha(nome, valor):
        icone = " 💚" if valor >= 5 else ""
        return f"- {nome}: **{valor}**{icone}"

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"{formata_linha('1ª Dúzia', atrasos['d1'])}\n{formata_linha('2ª Dúzia', atrasos['d2'])}\n{formata_linha('3ª Dúzia', atrasos['d3'])}")
    with col2:
        st.markdown(f"{formata_linha('1ª Linha', atrasos['l1'])}\n{formata_linha('2ª Linha', atrasos['l2'])}\n{formata_linha('3ª Linha', atrasos['l3'])}")
    
    st.write("---")
    
    historico_visual = []
    for n in reversed(st.session_state.historico):
        grp_ipt = qual_ipt(n)
        grp_123 = qual_123(n)
        if n == 0:
            historico_visual.append("**0**")
        else:
            historico_visual.append(f"{n}**({grp_ipt}-{grp_123})**")
            
    texto_historico = " - ".join(historico_visual)
    
    st.write("**Últimos giros (Mais recentes primeiro):**")
    st.markdown(texto_historico)
else:
    st.info("Nenhum número registrado no momento.")
