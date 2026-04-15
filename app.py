import streamlit as st
import pandas as pd
from datetime import date

# =============================================================================
# --- 1. CONFIGURAÇÕES GERAIS E VISUAIS (TEMA CLARO E EDUCACIONAL) ---
# =============================================================================
st.set_page_config(page_title="Projeto Saber - Gestão Escolar", page_icon="🏫", layout="wide")

st.markdown("""
<style>
    /* Reset de cores para tema claro escolar */
    .stApp { background-color: #f4f7f6; color: #1e3d59; }
    h1, h2, h3, h4, h5 { color: #004d99 !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    /* Estilo dos Cards de Métrica (Dashboard) */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* Estilo do Diário de Seleção */
    .painel-selecao {
        background-color: #ffffff;
        border-radius: 15px;
        padding: 25px;
        border-top: 5px solid #004d99;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    
    /* Botões personalizados */
    .stButton>button {
        border-radius: 8px;
        font-weight: bold;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #ddd;
    }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# --- 2. BANCO DE DADOS SIMULADO (MOCKUP) ---
# =============================================================================
MOCK_USERS = {
    "prof456": {"senha": "456", "perfil": "professor", "nome": "LUCIANA AUGUSTO SOARES"},
    "admin": {"senha": "admin", "perfil": "diretoria", "nome": "Diretoria"},
    "pai123": {"senha": "123", "perfil": "responsavel", "nome": "Responsável Teste"}
}

ALUNOS_MOCK = [
    "ANA JULIA SILVA SOARES COSTA",
    "ANA LETICIA FERREIRA DA SILVA",
    "ANDRIELLY DA SILVA OLIVEIRA",
    "ANNA FLAVIA DOS SANTOS ARAQUAM",
    "ANNA SOFIA DOS SANTOS",
    "ARTHUR GUILHERME DA SILVA SEVERINO",
    "DANIEL AUGUSTO DOS SANTOS NASCIMENTO"
]

if "usuario_logado" not in st.session_state: st.session_state.usuario_logado = None
if "perfil_logado" not in st.session_state: st.session_state.perfil_logado = None
if "diario_aberto" not in st.session_state: st.session_state.diario_aberto = False

def fazer_login(usuario, senha):
    if usuario in MOCK_USERS and MOCK_USERS[usuario]["senha"] == senha:
        st.session_state.usuario_logado = MOCK_USERS[usuario]["nome"]
        st.session_state.perfil_logado = MOCK_USERS[usuario]["perfil"]
        st.success("Acesso Concedido!")
        st.rerun()
    else: st.error("Credenciais inválidas!")

def fazer_logout():
    st.session_state.usuario_logado = None
    st.session_state.perfil_logado = None
    st.session_state.diario_aberto = False
    st.rerun()

# =============================================================================
# --- 3. MENU LATERAL (SIDEBAR) ---
# =============================================================================
with st.sidebar:
    st.markdown("<h2 style='text-align:center;'>🌎 PROJETO SABER</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-size:0.8em; color:#888;'>Colégio e Curso Potencial</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    if st.session_state.usuario_logado is None:
        st.markdown("### 🔐 Acesso ao Sistema")
        user_input = st.text_input("Usuário")
        pass_input = st.text_input("Senha", type="password")
        if st.button("Entrar", use_container_width=True, type="primary"):
            fazer_login(user_input, pass_input)
        st.info("💡 **Dica de Teste:**\n\nLogin: `prof456`\nSenha: `456`")
    else:
        st.success(f"👤 {st.session_state.usuario_logado}")
        
        # Menu de Navegação (Simulando a imagem)
        st.markdown("**PEDAGÓGICO**")
        st.button("📖 Notas", use_container_width=True)
        st.button("📅 Frequência", use_container_width=True)
        st.button("📄 Ocorrências", use_container_width=True)
        st.button("🗓️ Calendário", use_container_width=True)
        
        st.markdown("---")
        if st.button("🚪 Sair", use_container_width=True): fazer_logout()

# =============================================================================
# --- 4. ÁREA PRINCIPAL (FRONT-END) ---
# =============================================================================

if st.session_state.usuario_logado is None:
    # --- VITRINE PARA PAIS / PÚBLICO ---
    st.markdown("<h1 style='text-align: center;'>Bem-vindo ao Portal do Aluno</h1>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.info("📝 **Matrículas 2026**\n\nGaranta a vaga do seu filho.")
    with col2: st.success("💰 **Financeiro**\n\nAcesse boletos e pagamentos.")
    with col3: st.warning("📍 **Localização**\n\nVeja como chegar à escola.")
    with col4: st.error("📞 **Contatos**\n\nFale com a secretaria.")

elif st.session_state.perfil_logado == "professor":
    # --- PAINEL DO PROFESSOR (O CORAÇÃO DO SISTEMA) ---
    
    # Abas Superiores
    aba_dash, aba_freq, aba_notas = st.tabs(["📊 Dashboard", "📅 Frequência", "📝 Notas"])
    
    # ---------------------------------------------------------
    # ABA 1: DASHBOARD (VISÃO GERAL)
    # ---------------------------------------------------------
    with aba_dash:
        st.markdown("<h2>Visão Geral</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color:#666;'>Bem-vindo de volta! Aqui está o resumo da sua escola hoje.</p>", unsafe_allow_html=True)
        
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Alunos Ativos", "620", "Total")
        c2.metric("Presentes", "584", "Hoje")
        c3.metric("Ausentes", "36", "Faltas")
        c4.metric("Notas Diário", "28/28", "Progresso")
        c5.metric("Frequência Média", "94%", "Mensal")
        
        st.markdown("---")
        col_esq, col_dir = st.columns([2, 1])
        with col_esq:
            st.markdown("#### 📈 Atividade Recente (Turmas)")
            st.info("🚀 **1º Ano A:** Turma atingiu 94% da capacidade!")
            st.info("🚀 **5º Ano B:** Lançamento de notas concluído.")
            st.info("🚀 **6º Ano A:** Turma atingiu 99% da capacidade!")
        with col_dir:
            st.markdown("#### 🗓️ Calendário Escolar")
            st.markdown("**20/04** - Tiradentes (Feriado)")
            st.markdown("**23/04** - Fim do 1º Bimestre")
            st.markdown("**26/04** - Início do 2º Bimestre")
            st.markdown("**01/05** - Dia do Trabalho")
            
    # ---------------------------------------------------------
    # ABA 2: FREQUÊNCIA
    # ---------------------------------------------------------
    with aba_freq:
        st.markdown("<h2>Registro de Frequência</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color:#666;'>Selecione o status de presença para cada aluno.</p>", unsafe_allow_html=True)
        
        col_turma, col_data = st.columns(2)
        with col_turma: st.selectbox("Turma:", ["6º Ano A", "7º Ano B", "8º Ano A"], key="freq_turma")
        with col_data: st.date_input("Data da Aula:", date.today())
        
        st.markdown("---")
        st.markdown("<div style='display:flex; justify-content:space-between; padding:0 20px;'><b>ALUNO</b><b>STATUS DE PRESENÇA</b></div>", unsafe_allow_html=True)
        st.markdown("<hr style='margin:5px 0;'>", unsafe_allow_html=True)
        
        for aluno in ALUNOS_MOCK:
            ca, cb = st.columns([3, 2])
            with ca:
                st.markdown(f"**{aluno}**<br><span style='font-size:0.8em; color:#888;'>ID: {hash(aluno)}</span>", unsafe_allow_html=True)
            with cb:
                # Botões de rádio horizontais simulando os blocos (P, F, FJ)
                st.radio("Status", ["P (Presente)", "F (Falta)", "FJ (Justificada)"], horizontal=True, label_visibility="collapsed", key=f"rad_{aluno}")
            st.markdown("<hr style='margin:5px 0; opacity:0.3;'>", unsafe_allow_html=True)
        
        st.button("💾 Salvar Frequência", type="primary", use_container_width=True)

    # ---------------------------------------------------------
    # ABA 3: NOTAS (DIÁRIO DE CLASSE)
    # ---------------------------------------------------------
    with aba_notas:
        if not st.session_state.diario_aberto:
            st.markdown(f"<h1 style='text-align:center;'>Bom dia, Prof. {st.session_state.usuario_logado.split()[0]}!</h1>", unsafe_allow_html=True)
            st.markdown("<p style='text-align:center; color:#666;'>Pronto para lançar os resultados? Selecione a turma abaixo.</p>", unsafe_allow_html=True)
            
            st.markdown('<div class="painel-selecao">', unsafe_allow_html=True)
            st.text_input("👤 Professor", st.session_state.usuario_logado, disabled=True)
            sel_turma = st.selectbox("👥 Turma", ["Selecione...", "6º Ano A", "7º Ano B", "8º Ano C"])
            sel_disc = st.selectbox("📄 Disciplina", ["Selecione...", "Língua Portuguesa", "Matemática", "História"])
            sel_bim = st.selectbox("📅 Bimestre", ["Selecione...", "1º Bimestre", "2º Bimestre", "3º Bimestre", "4º Bimestre"])
            st.markdown('</div>', unsafe_allow_html=True)
            
            if sel_turma != "Selecione..." and sel_disc != "Selecione..." and sel_bim != "Selecione...":
                if st.button("Abrir Diário de Notas ➔", type="primary", use_container_width=True):
                    st.session_state.diario_aberto = True
                    st.session_state.ctx_turma = sel_turma
                    st.session_state.ctx_disc = sel_disc
                    st.session_state.ctx_bim = sel_bim
                    st.rerun()
            else:
                st.button("Abrir Diário de Notas ➔", disabled=True, use_container_width=True)

        else:
            # DIÁRIO ABERTO (Quadro de Notas)
            st.markdown(f"""
            <div style='background-color:#e6f2ff; padding:15px; border-radius:8px; display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;'>
                <div>
                    <span style='color:#004d99; font-weight:bold; font-size:0.9em;'>CONTEXTO ATUAL: <span style='background:#004d99; color:#fff; padding:2px 8px; border-radius:10px;'>{st.session_state.ctx_bim}</span></span><br>
                    <span style='font-size:1.2em;'>👤 <b>{st.session_state.usuario_logado}</b> &nbsp;|&nbsp; 👥 {st.session_state.ctx_turma} &nbsp;|&nbsp; 📄 {st.session_state.ctx_disc}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("⬅️ Trocar Período/Turma"):
                st.session_state.diario_aberto = False
                st.rerun()
                
            st.markdown("### Quadro de Médias")
            st.caption("Fórmula de Média: (AV1 + AV2 + AV3 + PE) / 4")
            
            # Criando DataFrame Editável para simular a planilha de notas da imagem
            df_notas = pd.DataFrame({
                "ALUNO": ALUNOS_MOCK,
                "AV1 (Prova)": [10.0, 6.5, 7.5, 9.0, 8.5, 8.5, 7.0],
                "AV2 (Prova)": [7.0, 5.0, 7.0, 8.0, 6.0, 4.0, 7.0],
                "AV3 (Prova)": [6.0, 4.0, 6.0, 4.0, 3.0, 4.0, 7.0],
                "PE (Trabalho)": [3.0, 3.0, 3.0, 2.0, 3.0, 3.0, 3.0]
            })
            
            # Editor de dados do Streamlit (Permite digitar igual Excel)
            df_editado = st.data_editor(
                df_notas,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "ALUNO": st.column_config.TextColumn(disabled=True),
                    "AV1 (Prova)": st.column_config.NumberColumn(min_value=0.0, max_value=10.0, format="%.1f"),
                    "AV2 (Prova)": st.column_config.NumberColumn(min_value=0.0, max_value=10.0, format="%.1f"),
                    "AV3 (Prova)": st.column_config.NumberColumn(min_value=0.0, max_value=10.0, format="%.1f"),
                    "PE (Trabalho)": st.column_config.NumberColumn(min_value=0.0, max_value=10.0, format="%.1f"),
                }
            )
            
            # Cálculo em tempo real da Média Final e Situação
            st.markdown("### Resultado Consolidado")
            df_resultado = df_editado.copy()
            df_resultado["MÉDIA FINAL"] = df_resultado[["AV1 (Prova)", "AV2 (Prova)", "AV3 (Prova)", "PE (Trabalho)"]].mean(axis=1).round(1)
            
            def calc_situacao(media):
                if media >= 7.0: return "🟢 APROVADO"
                elif media >= 5.0: return "🟡 RECUPERAÇÃO"
                else: return "🔴 REPROVADO"
                
            df_resultado["SITUAÇÃO"] = df_resultado["MÉDIA FINAL"].apply(calc_situacao)
            
            st.dataframe(
                df_resultado[["ALUNO", "MÉDIA FINAL", "SITUAÇÃO"]],
                hide_index=True,
                use_container_width=True
            )
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1: st.button("+ Nova Atividade", use_container_width=True)
            with col_btn2: st.button("💾 Salvar Diário de Notas", type="primary", use_container_width=True)
