import streamlit as st
import pandas as pd
from datetime import date
import time

# =============================================================================
# --- 1. CONFIGURAÇÕES GERAIS E VISUAIS (TEMA CLARO E EDUCACIONAL) ---
# =============================================================================
st.set_page_config(page_title="Projeto Saber - Gestão Escolar", page_icon="🏫", layout="wide")

st.markdown("""
<style>
    /* FUNDO GERAL CLARO */
    .stApp { background-color: #f4f7f6; }
    
    /* FORÇA TEXTOS A SEREM ESCUROS (Corrigindo o conflito com o Dark Mode) */
    .stApp p, .stApp span, .stApp label, .stApp div[data-testid="stMarkdownContainer"] {
        color: #1e3d59 !important;
    }

    /* TÍTULOS */
    h1, h2, h3, h4, h5 { color: #004d99 !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    /* EXCEÇÃO: TEXTO DOS BOTÕES DEVE SER BRANCO */
    .stButton > button p, .stButton > button span {
        color: #ffffff !important;
    }
    
    /* SIDEBAR BRANCA */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #ddd;
    }
    
    /* CARDS DO DASHBOARD */
    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    
    /* PAINEL DE SELEÇÃO DO DIÁRIO */
    .painel-selecao {
        background-color: #ffffff;
        border-radius: 15px;
        padding: 25px;
        border-top: 5px solid #004d99;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    
    /* CORREÇÃO MÁXIMA PARA CAIXAS DE TEXTO E INPUTS FICAREM VISÍVEIS (TINTA INVISÍVEL RESOLVIDA) */
    div[data-baseweb="select"] > div, 
    input, 
    textarea, 
    div[data-baseweb="base-input"] {
        background-color: #ffffff !important;
        color: #000000 !important; /* Força o texto digitado a ser PRETO */
        -webkit-text-fill-color: #000000 !important; /* Proteção extra para navegadores webkit */
    }
    
    /* Ajuste da cor do texto de dica (placeholder) */
    input::placeholder, textarea::placeholder {
        color: #888888 !important;
        -webkit-text-fill-color: #888888 !important;
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
        user_input = st.text_input("Usuário", placeholder="Digite sua matrícula")
        pass_input = st.text_input("Senha", type="password", placeholder="Digite sua senha")
        if st.button("Entrar", use_container_width=True, type="primary"):
            fazer_login(user_input, pass_input)
        st.info("💡 **Dica de Teste:**\n\nLogin: `prof456`\nSenha: `456`")
    else:
        # Banner de Identificação (Estilo verde igual à foto)
        st.markdown(f"""
        <div style='background-color: #d4edda; padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center; border: 1px solid #c3e6cb;'>
            <span style='color: #155724 !important; font-weight: bold; font-size: 1.1em;'>🧑‍🏫 {st.session_state.usuario_logado}</span>
        </div>
        """, unsafe_allow_html=True)
        
        # Menu de Navegação Pedagógica
        st.markdown("<span style='color:#888; font-size:0.8em; font-weight:bold;'>PEDAGÓGICO</span>", unsafe_allow_html=True)
        st.button("📖 Diário de Classe", use_container_width=True)
        st.button("🤖 Gerador de Provas", use_container_width=True)
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
    
    aba_dash, aba_freq, aba_notas, aba_ia = st.tabs(["📊 Dashboard", "📅 Frequência", "📝 Notas", "🤖 Gerador IA"])
    
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
    # ABA 2: FREQUÊNCIA E DIÁRIO DE AULA 
    # ---------------------------------------------------------
    with aba_freq:
        st.markdown("<h2>Registro de Frequência e Conteúdo</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color:#666;'>Preencha os dados da aula e selecione o status de presença para cada aluno.</p>", unsafe_allow_html=True)
        
        st.markdown("<div style='background-color:#ffffff; padding:20px; border-radius:10px; border: 1px solid #e0e0e0; margin-bottom: 20px;'>", unsafe_allow_html=True)
        col_turma, col_data = st.columns(2)
        with col_turma: st.selectbox("Turma:", ["6º Ano A", "7º Ano B", "8º Ano A"], key="freq_turma")
        with col_data: st.date_input("Data da Aula:", date.today())
        
        assunto_aula = st.text_area("📚 Assunto do Dia / Conteúdo Lecionado:", placeholder="Descreva os conteúdos abordados nesta aula...", height=100)
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("<div style='display:flex; justify-content:space-between; padding:0 20px; color:#004d99; font-weight:bold;'><span>ALUNO</span><span>STATUS DE PRESENÇA</span></div>", unsafe_allow_html=True)
        st.markdown("<hr style='margin:5px 0; border-top: 2px solid #ccc;'>", unsafe_allow_html=True)
        
        for aluno in ALUNOS_MOCK:
            ca, cb = st.columns([3, 2])
            with ca:
                st.markdown(f"<span style='font-weight:bold; color:#1e3d59;'>{aluno}</span><br><span style='font-size:0.8em; color:#888;'>ID: {abs(hash(aluno))}</span>", unsafe_allow_html=True)
            with cb:
                st.radio("Status", ["P (Presente)", "F (Falta)", "FJ (Justificada)"], horizontal=True, label_visibility="collapsed", key=f"rad_{aluno}")
            st.markdown("<hr style='margin:5px 0; opacity:0.3;'>", unsafe_allow_html=True)
        
        if st.button("💾 Salvar Frequência e Assunto do Dia", type="primary", use_container_width=True):
            if assunto_aula.strip() == "": st.warning("⚠️ Atenção: Você não preencheu o Assunto da Aula, mas a frequência foi salva.")
            else: st.success("✅ Frequência e Diário de Conteúdo salvos com sucesso!")

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
            st.markdown(f"""
            <div style='background-color:#e6f2ff; padding:15px; border-radius:8px; display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; border: 1px solid #b3d9ff;'>
                <div>
                    <span style='color:#004d99 !important; font-weight:bold; font-size:0.9em;'>CONTEXTO ATUAL: <span style='background:#004d99; color:#fff !important; padding:2px 8px; border-radius:10px;'>{st.session_state.ctx_bim}</span></span><br>
                    <span style='font-size:1.2em; color:#1e3d59 !important;'>👤 <b>{st.session_state.usuario_logado}</b> &nbsp;|&nbsp; 👥 {st.session_state.ctx_turma} &nbsp;|&nbsp; 📄 {st.session_state.ctx_disc}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("⬅️ Trocar Período/Turma"):
                st.session_state.diario_aberto = False
                st.rerun()
                
            st.markdown("### Quadro de Médias")
            st.caption("Fórmula de Média: (AV1 + AV2 + AV3 + PE) / 4")
            
            df_notas = pd.DataFrame({
                "ALUNO": ALUNOS_MOCK,
                "AV1 (Prova)": [10.0, 6.5, 7.5, 9.0, 8.5, 8.5, 7.0],
                "AV2 (Prova)": [7.0, 5.0, 7.0, 8.0, 6.0, 4.0, 7.0],
                "AV3 (Prova)": [6.0, 4.0, 6.0, 4.0, 3.0, 4.0, 7.0],
                "PE (Trabalho)": [3.0, 3.0, 3.0, 2.0, 3.0, 3.0, 3.0]
            })
            
            df_editado = st.data_editor(
                df_notas, hide_index=True, use_container_width=True,
                column_config={
                    "ALUNO": st.column_config.TextColumn(disabled=True),
                    "AV1 (Prova)": st.column_config.NumberColumn(min_value=0.0, max_value=10.0, format="%.1f"),
                    "AV2 (Prova)": st.column_config.NumberColumn(min_value=0.0, max_value=10.0, format="%.1f"),
                    "AV3 (Prova)": st.column_config.NumberColumn(min_value=0.0, max_value=10.0, format="%.1f"),
                    "PE (Trabalho)": st.column_config.NumberColumn(min_value=0.0, max_value=10.0, format="%.1f"),
                }
            )
            
            st.markdown("### Resultado Consolidado")
            df_resultado = df_editado.copy()
            df_resultado["MÉDIA FINAL"] = df_resultado[["AV1 (Prova)", "AV2 (Prova)", "AV3 (Prova)", "PE (Trabalho)"]].mean(axis=1).round(1)
            
            def calc_situacao(media):
                if media >= 7.0: return "🟢 APROVADO"
                elif media >= 5.0: return "🟡 RECUPERAÇÃO"
                else: return "🔴 REPROVADO"
                
            df_resultado["SITUAÇÃO"] = df_resultado["MÉDIA FINAL"].apply(calc_situacao)
            st.dataframe(df_resultado[["ALUNO", "MÉDIA FINAL", "SITUAÇÃO"]], hide_index=True, use_container_width=True)
            
            col_btn1, col_btn2 = st.columns(2)
            with col_btn1: st.button("+ Nova Atividade", use_container_width=True)
            with col_btn2: st.button("💾 Salvar Diário de Notas", type="primary", use_container_width=True)

    # ---------------------------------------------------------
    # ABA 4: GERADOR DE PROVAS COM IA
    # ---------------------------------------------------------
    with aba_ia:
        st.markdown("<h2>🤖 Fábrica de Avaliações com IA</h2>", unsafe_allow_html=True)
        st.markdown("<p style='color:#666;'>Gere provas, testes e exercícios inéditos e randomizados em segundos.</p>", unsafe_allow_html=True)
        
        with st.form("form_ia_gerador"):
            st.markdown("#### Configurações da Avaliação")
            assunto = st.text_area("📚 Assunto(s) da Avaliação", placeholder="Ex: Equações de 2º Grau, Revolução Francesa, Biologia Celular...")
            
            c_ia1, c_ia2, c_ia3, c_ia4 = st.columns(4)
            with c_ia1: tipo_quest = st.selectbox("📝 Tipo de Questão", ["Múltipla Escolha (A-E)", "Abertas (Dissertativas)", "Mista (50/50)"])
            with c_ia2: nivel_dif = st.selectbox("⚙️ Dificuldade", ["Fácil", "Médio", "Difícil"])
            with c_ia3: qtd_quest = st.number_input("🔢 Quantidade de Questões", min_value=1, max_value=50, value=10)
            with c_ia4: peso_quest = st.number_input("⚖️ Peso (Pts) por Questão", min_value=0.1, max_value=10.0, value=1.0, step=0.1)
                
            gerar_prova_btn = st.form_submit_button("🚀 Elaborar Avaliação Inédita com IA", type="primary", use_container_width=True)

        if gerar_prova_btn and assunto:
            with st.spinner("Conectando ao núcleo de IA... Cruzando dados e elaborando questões inéditas..."):
                time.sleep(3) 
                
                texto_prova = f"==========================================================\n"
                texto_prova += f"ESCOLA PROJETO SABER\n"
                texto_prova += f"Data: ___/___/2026\n"
                texto_prova += f"Professor(a): {st.session_state.usuario_logado}\n"
                texto_prova += f"Aluno(a): ________________________________________________\n"
                texto_prova += f"Assunto: {assunto.upper()}\n"
                texto_prova += f"Nível: {nivel_dif} | Total de Questões: {qtd_quest}\n"
                texto_prova += f"==========================================================\n\n"
                
                for i in range(1, int(qtd_quest) + 1):
                    texto_prova += f"QUESTÃO {i} (Valor: {peso_quest} pts)\n"
                    texto_prova += f"[A Inteligência Artificial inseriria aqui um enunciado original e contextualizado sobre {assunto}].\n\n"
                    
                    if tipo_quest == "Múltipla Escolha (A-E)" or (tipo_quest == "Mista (50/50)" and i % 2 != 0):
                        texto_prova += "A) [Alternativa Incorreta Gerada pela IA]\n"
                        texto_prova += "B) [Alternativa Incorreta Gerada pela IA]\n"
                        texto_prova += "C) [Alternativa Correta Gerada pela IA]\n"
                        texto_prova += "D) [Alternativa Incorreta Gerada pela IA]\n"
                        texto_prova += "E) [Alternativa Incorreta Gerada pela IA]\n\n"
                    else:
                        texto_prova += "R: ___________________________________________________________________\n"
                        texto_prova += "______________________________________________________________________\n"
                        texto_prova += "______________________________________________________________________\n\n"
                
                texto_prova += f"--- FIM DA AVALIAÇÃO ---\n\nGABARITO DO PROFESSOR (OCULTO PARA IMPRESSÃO):\n[Gabarito automático gerado pela IA]"

                st.success("✅ Avaliação elaborada com sucesso! Uma prova única foi forjada.")
                st.text_area("📄 Pré-Visualização do Documento:", texto_prova, height=400)
                
                col_exp1, col_exp2 = st.columns(2)
                with col_exp1: st.download_button(label="📥 Baixar Documento (.TXT)", data=texto_prova, file_name=f"Prova_{assunto.replace(' ', '_')}.txt", mime="text/plain", use_container_width=True)
                with col_exp2: st.button("🖨️ Imprimir / Salvar PDF (Use Ctrl+P)", use_container_width=True)
