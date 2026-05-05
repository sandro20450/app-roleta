import streamlit as st
import pandas as pd
from datetime import date
import time
import gspread
from google.oauth2.service_account import Credentials
import google.generativeai as genai
import PyPDF2
import io

# =============================================================================
# --- 1. CONFIGURAÇÕES GERAIS E VISUAIS ---
# =============================================================================
st.set_page_config(page_title="SEEA - Gestão Escolar", page_icon="🏫", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #f4f7f6; }
    .stApp p, .stApp span, .stApp label, .stApp div[data-testid="stMarkdownContainer"] { color: #1e3d59 !important; }
    h1, h2, h3, h4, h5 { color: #004d99 !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .stButton > button p, .stButton > button span { color: #ffffff !important; }
    [data-testid="stSidebar"] { background-color: #ffffff; border-right: 1px solid #ddd; }
    div[data-testid="metric-container"] { background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 10px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .painel-selecao { background-color: #ffffff; border-radius: 15px; padding: 25px; border-top: 5px solid #004d99; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }
    div[data-baseweb="select"] > div, input, textarea, div[data-baseweb="base-input"] { background-color: #ffffff !important; color: #000000 !important; -webkit-text-fill-color: #000000 !important; }
    input::placeholder, textarea::placeholder { color: #888888 !important; -webkit-text-fill-color: #888888 !important; }
    .aviso-card { background-color: #fff3cd; border-left: 5px solid #ffecb5; padding: 15px; border-radius: 5px; margin-bottom: 10px; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# --- 2. CONEXÃO COM BANCO DE DADOS (GOOGLE SHEETS) ---
# =============================================================================
@st.cache_resource(ttl=3600, show_spinner=False)
def get_gspread_client():
    if "gcp_service_account" in st.secrets:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds)
    return None

def carregar_usuarios():
    try:
        gc = get_gspread_client()
        if gc:
            ws = gc.open("Base_SEEA").worksheet("Usuarios")
            records = ws.get_all_records()
            usuarios = {}
            for r in records:
                usuarios[str(r['usuario'])] = { "senha": str(r['senha']), "perfil": str(r['perfil']).lower().strip(), "nome": str(r['nome']) }
            return usuarios
    except Exception as e:
        return {}

def carregar_turmas():
    try:
        gc = get_gspread_client()
        if gc:
            ws = gc.open("Base_SEEA").worksheet("Alunos")
            records = ws.get_all_records()
            turmas = list(set([str(r['turma']) for r in records if str(r['turma']).strip() != ""]))
            return sorted(turmas) if turmas else ["Selecione..."]
    except:
        return ["Selecione..."]

def carregar_alunos(turma):
    try:
        gc = get_gspread_client()
        if gc:
            ws = gc.open("Base_SEEA").worksheet("Alunos")
            records = ws.get_all_records()
            alunos_turma = [str(r['nome_aluno']) for r in records if str(r['turma']) == turma]
            return alunos_turma if alunos_turma else ["Nenhum aluno cadastrado nesta turma."]
    except:
        return ["Erro ao carregar alunos"]

# NOVA FUNÇÃO: Busca os dados específicos do aluno logado na aba "Alunos"
def buscar_dados_aluno(nome_aluno):
    try:
        gc = get_gspread_client()
        if gc:
            ws = gc.open("Base_SEEA").worksheet("Alunos")
            records = ws.get_all_records()
            for r in records:
                if str(r['nome_aluno']).strip() == nome_aluno.strip():
                    return r # Retorna os dados (turma, turno, etc.) se encontrar o aluno
    except Exception as e:
        return None
    return None

# =============================================================================
# --- 3. CONFIGURAÇÃO DA INTELIGÊNCIA ARTIFICIAL (GEMINI) ---
# =============================================================================
if "GEMINI_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    ia_configurada = True
else:
    ia_configurada = False

# =============================================================================
# --- 4. SISTEMA DE LOGIN E CONTROLE DE ESTADO ---
# =============================================================================
if "usuario_logado" not in st.session_state: st.session_state.usuario_logado = None
if "perfil_logado" not in st.session_state: st.session_state.perfil_logado = None
if "diario_aberto" not in st.session_state: st.session_state.diario_aberto = False

def fazer_login(usuario, senha):
    usuarios_db = carregar_usuarios()
    if usuario in usuarios_db and usuarios_db[usuario]["senha"] == senha:
        st.session_state.usuario_logado = usuarios_db[usuario]["nome"]
        st.session_state.perfil_logado = usuarios_db[usuario]["perfil"]
        st.success("Acesso Concedido!")
        st.rerun()
    else: st.error("Credenciais inválidas ou usuário não encontrado na planilha!")

def fazer_logout():
    st.session_state.usuario_logado = None
    st.session_state.perfil_logado = None
    st.session_state.diario_aberto = False
    st.rerun()

# =============================================================================
# --- 5. MENU LATERAL (SIDEBAR) ---
# =============================================================================
with st.sidebar:
    st.markdown("<h2 style='text-align:center;'>🌎 SEEA</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-size:0.8em; color:#888;'>Sistema de Gestão Escolar</p>", unsafe_allow_html=True)
    st.markdown("---")
    
    if st.session_state.usuario_logado is None:
        st.markdown("### 🔐 Acesso ao Sistema")
        user_input = st.text_input("Usuário", placeholder="Digite seu usuário")
        pass_input = st.text_input("Senha", type="password", placeholder="Digite sua senha")
        if st.button("Entrar", use_container_width=True, type="primary"):
            fazer_login(user_input, pass_input)
    else:
        st.markdown(f"""<div style='background-color: #d4edda; padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center; border: 1px solid #c3e6cb;'><span style='color: #155724 !important; font-weight: bold; font-size: 1.1em;'>👤 {st.session_state.usuario_logado}</span></div>""", unsafe_allow_html=True)
        
        # Menu adaptado para Professor
        if st.session_state.perfil_logado == "professor":
            st.markdown("<span style='color:#888; font-size:0.8em; font-weight:bold;'>PEDAGÓGICO</span>", unsafe_allow_html=True)
            st.button("📖 Diário de Classe", use_container_width=True)
            st.button("🤖 Gerador de Provas", use_container_width=True)
            
        # Menu adaptado para Administração
        elif st.session_state.perfil_logado in ["admin", "diretoria"]:
            st.markdown("<span style='color:#888; font-size:0.8em; font-weight:bold;'>ADMINISTRAÇÃO</span>", unsafe_allow_html=True)
            st.button("⚙️ Painel Geral", use_container_width=True)
            
        # NOVO: Menu adaptado para o Aluno / Responsável
        elif st.session_state.perfil_logado == "aluno":
            st.markdown("<span style='color:#888; font-size:0.8em; font-weight:bold;'>ÁREA DO ALUNO</span>", unsafe_allow_html=True)
            st.button("📊 Meu Boletim", use_container_width=True)
            st.button("📢 Avisos Escolares", use_container_width=True)
            
        st.markdown("---")
        if st.button("🚪 Sair", use_container_width=True): fazer_logout()

# =============================================================================
# --- 6. ÁREA PRINCIPAL (FRONT-END) ---
# =============================================================================

# Tela Inicial (Deslogado)
if st.session_state.usuario_logado is None:
    st.markdown("<h1 style='text-align: center;'>Bem-vindo ao Portal SEEA</h1>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.info("📝 **Matrículas 2026**\n\nGaranta a vaga do seu filho.")
    with col2: st.success("💰 **Financeiro**\n\nAcesse boletos e pagamentos.")
    with col3: st.warning("📍 **Localização**\n\nVeja como chegar à escola.")
    with col4: st.error("📞 **Contatos**\n\nFale com a secretaria.")

# NOVO: Painel exclusivo do Aluno / Responsável
elif st.session_state.perfil_logado == "aluno":
    st.markdown(f"<h1 style='text-align: center;'>🎓 Portal do Aluno</h1>", unsafe_allow_html=True)
    
    # Busca as informações do aluno logado na planilha
    dados_do_aluno = buscar_dados_aluno(st.session_state.usuario_logado)
    
    if dados_do_aluno:
        st.markdown(f"""
        <div style='background-color:#e6f2ff; padding:15px; border-radius:8px; display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; border: 1px solid #b3d9ff;'>
            <div>
                <span style='font-size:1.2em; color:#1e3d59 !important;'>👤 <b>{st.session_state.usuario_logado}</b></span><br>
                <span style='color:#004d99 !important; font-weight:bold;'>👥 Turma: {dados_do_aluno.get('turma', 'N/A')} &nbsp;|&nbsp; 🏫 Ensino: {dados_do_aluno.get('ensino', 'N/A')} &nbsp;|&nbsp; ⏰ Turno: {dados_do_aluno.get('turno', 'N/A')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.warning("⚠️ Dados da turma não encontrados. Por favor, contacte a secretaria.")

    # Criação das Abas de navegação para o Aluno
    aba_boletim, aba_avisos = st.tabs(["📊 Boletim de Notas", "📢 Mural de Avisos"])
    
    with aba_boletim:
        st.markdown("### 📝 Desempenho Académico - 2026")
        st.write("Acompanhe as notas do aluno por disciplina em cada bimestre.")
        
        # Tabela simulada de notas (Até conectarmos com o banco de notas oficial)
        df_boletim = pd.DataFrame({
            "Disciplina": ["Língua Portuguesa", "Matemática", "História", "Ciências", "Geografia"],
            "1º Bim": [8.5, 7.0, 9.0, 8.0, 7.5],
            "2º Bim": [7.5, 6.5, 8.5, 7.5, 8.0],
            "3º Bim": ["-", "-", "-", "-", "-"],
            "4º Bim": ["-", "-", "-", "-", "-"],
            "Média Parcial": [8.0, 6.75, 8.75, 7.75, 7.75],
            "Situação Parcial": ["🟢 OK", "🟡 ATENÇÃO", "🟢 OK", "🟢 OK", "🟢 OK"]
        })
        
        st.dataframe(df_boletim, hide_index=True, use_container_width=True)
        st.caption("Legenda: 🟢 OK (Média >= 7.0) | 🟡 ATENÇÃO (Média < 7.0) | 🔴 CRÍTICO (Média < 5.0)")

    with aba_avisos:
        st.markdown("### 📢 Quadro de Comunicações")
        st.write("Fique atento aos prazos e comunicados importantes da escola.")
        
        # Avisos (Podem ser puxados de uma nova aba na planilha no futuro)
        st.markdown("""
        <div class='aviso-card'>
            <strong>📅 Reunião de Pais e Mestres</strong><br>
            A nossa próxima reunião de acompanhamento pedagógico será no dia 15 de Junho, às 18h30. Contamos com a sua presença!
        </div>
        <div class='aviso-card'>
            <strong>📝 Avaliações do 2º Bimestre</strong><br>
            As provas globais terão início na próxima segunda-feira. Por favor, verifiquem o calendário de estudos enviado por e-mail.
        </div>
        <div class='aviso-card'>
            <strong>⚽ Jogos Interescolares</strong><br>
            As inscrições para os jogos de futsal e voleibol terminam nesta sexta-feira. Procure o professor de Educação Física.
        </div>
        """, unsafe_allow_html=True)


# Painel da Diretoria (Mantido do código original)
elif st.session_state.perfil_logado in ["admin", "diretoria"]:
    st.header("👑 Painel da Diretoria")
    st.markdown("Você está conectado como Administrador. O sistema identificou o seu nível de acesso máximo.")
    c1, c2, c3 = st.columns(3)
    c1.metric("Alunos Cadastrados", "Base_SEEA", "Conectado")
    c2.metric("Inteligência Artificial", "Gemini API", "Online" if ia_configurada else "Offline")
    c3.metric("Status do Servidor", "Estável", "100%")

# Painel do Professor (Mantido do código original)
elif st.session_state.perfil_logado == "professor":
    aba_dash, aba_freq, aba_notas, aba_ia = st.tabs(["📊 Dashboard", "📅 Frequência", "📝 Notas", "🤖 Gerador IA"])
    
    with aba_dash:
        st.markdown("<h2>Visão Geral</h2>", unsafe_allow_html=True)
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Alunos Ativos", "620", "Total")
        c2.metric("Presentes", "584", "Hoje")
        c3.metric("Ausentes", "36", "Faltas")
        c4.metric("Notas Diário", "28/28", "Progresso")
        c5.metric("Frequência Média", "94%", "Mensal")
            
    with aba_freq:
        st.markdown("<h2>Registro de Frequência e Conteúdo</h2>", unsafe_allow_html=True)
        st.markdown("<div style='background-color:#ffffff; padding:20px; border-radius:10px; border: 1px solid #e0e0e0; margin-bottom: 20px;'>", unsafe_allow_html=True)
        col_turma, col_data = st.columns(2)
        
        lista_turmas = carregar_turmas()
        with col_turma: selecao_turma = st.selectbox("Turma:", lista_turmas, key="freq_turma")
        with col_data: st.date_input("Data da Aula:", date.today())
        
        assunto_aula = st.text_area("📚 Assunto do Dia / Conteúdo Lecionado:", placeholder="Descreva os conteúdos abordados nesta aula...", height=100)
        st.markdown("</div>", unsafe_allow_html=True)
        
        if selecao_turma and selecao_turma != "Selecione...":
            st.markdown("<div style='display:flex; justify-content:space-between; padding:0 20px; color:#004d99; font-weight:bold;'><span>ALUNO</span><span>STATUS DE PRESENÇA</span></div><hr style='margin:5px 0; border-top: 2px solid #ccc;'>", unsafe_allow_html=True)
            
            lista_alunos = carregar_alunos(selecao_turma)
            for aluno in lista_alunos:
                ca, cb = st.columns([3, 2])
                with ca: st.markdown(f"<span style='font-weight:bold; color:#1e3d59;'>{aluno}</span>", unsafe_allow_html=True)
                with cb: st.radio("Status", ["P", "F", "FJ"], horizontal=True, label_visibility="collapsed", key=f"rad_{aluno}")
                st.markdown("<hr style='margin:5px 0; opacity:0.3;'>", unsafe_allow_html=True)
            
            if st.button("💾 Salvar Frequência", type="primary", use_container_width=True):
                st.success("✅ Função de salvar será ligada ao banco de dados no futuro.")
        else:
            st.info("Selecione uma turma para carregar a lista de alunos.")

    with aba_notas:
        lista_turmas = carregar_turmas()
        
        if not st.session_state.diario_aberto:
            st.markdown(f"<h1 style='text-align:center;'>Bom dia, {st.session_state.usuario_logado.split()[0]}!</h1>", unsafe_allow_html=True)
            st.markdown('<div class="painel-selecao">', unsafe_allow_html=True)
            st.text_input("👤 Professor", st.session_state.usuario_logado, disabled=True)
            sel_turma = st.selectbox("👥 Turma", ["Selecione..."] + lista_turmas)
            sel_disc = st.selectbox("📄 Disciplina", ["Selecione...", "Língua Portuguesa", "Matemática", "História", "Ciências", "Geografia"])
            sel_bim = st.selectbox("📅 Bimestre", ["Selecione...", "1º Bimestre", "2º Bimestre", "3º Bimestre", "4º Bimestre"])
            st.markdown('</div>', unsafe_allow_html=True)
            
            if sel_turma != "Selecione..." and sel_disc != "Selecione..." and sel_bim != "Selecione...":
                if st.button("Abrir Diário de Notas ➔", type="primary", use_container_width=True):
                    st.session_state.diario_aberto = True
                    st.session_state.ctx_turma = sel_turma
                    st.session_state.ctx_disc = sel_disc
                    st.session_state.ctx_bim = sel_bim
                    st.rerun()
            else: st.button("Abrir Diário de Notas ➔", disabled=True, use_container_width=True)

        else:
            st.markdown(f"<div style='background-color:#e6f2ff; padding:15px; border-radius:8px; display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; border: 1px solid #b3d9ff;'><div><span style='color:#004d99 !important; font-weight:bold; font-size:0.9em;'>CONTEXTO ATUAL: <span style='background:#004d99; color:#fff !important; padding:2px 8px; border-radius:10px;'>{st.session_state.ctx_bim}</span></span><br><span style='font-size:1.2em; color:#1e3d59 !important;'>👤 <b>{st.session_state.usuario_logado}</b> &nbsp;|&nbsp; 👥 {st.session_state.ctx_turma} &nbsp;|&nbsp; 📄 {st.session_state.ctx_disc}</span></div></div>", unsafe_allow_html=True)
            if st.button("⬅️ Trocar Período/Turma"):
                st.session_state.diario_aberto = False
                st.rerun()
                
            st.markdown("### Quadro de Médias")
            lista_alunos_notas = carregar_alunos(st.session_state.ctx_turma)
            
            df_notas = pd.DataFrame({
                "ALUNO": lista_alunos_notas,
                "AV1 (Prova)": [0.0] * len(lista_alunos_notas),
                "AV2 (Prova)": [0.0] * len(lista_alunos_notas),
                "AV3 (Prova)": [0.0] * len(lista_alunos_notas),
                "PE (Trabalho)": [0.0] * len(lista_alunos_notas)
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
            
            df_resultado = df_editado.copy()
            df_resultado["MÉDIA FINAL"] = df_resultado[["AV1 (Prova)", "AV2 (Prova)", "AV3 (Prova)", "PE (Trabalho)"]].mean(axis=1).round(1)
            df_resultado["SITUAÇÃO"] = df_resultado["MÉDIA FINAL"].apply(lambda m: "🟢 APROVADO" if m >= 7.0 else ("🟡 RECUPERAÇÃO" if m >= 5.0 else "🔴 REPROVADO"))
            st.dataframe(df_resultado[["ALUNO", "MÉDIA FINAL", "SITUAÇÃO"]], hide_index=True, use_container_width=True)
            
            st.button("💾 Salvar Diário de Notas", type="primary", use_container_width=True)

    with aba_ia:
        st.markdown("<h2>🤖 Fábrica de Avaliações com IA</h2>", unsafe_allow_html=True)
        if not ia_configurada:
            st.error("⚠️ **Sistema Desconectado:** A chave da API do Gemini não foi encontrada no cofre.")
        else:
            with st.form("form_ia_gerador"):
                st.markdown("#### 1. Material de Referência (Opcional, mas recomendado)")
                arquivo_upload = st.file_uploader("📄 Envie um resumo, texto ou conteúdo base (Apenas PDF ou TXT)", type=["pdf", "txt"])
                
                st.markdown("#### 2. Configurações da Avaliação")
                assunto = st.text_input("📚 Assunto Principal", placeholder="Ex: Fotossíntese, Equações de 2º Grau...")
                
                c_ia1, c_ia2, c_ia3, c_ia4 = st.columns(4)
                with c_ia1: tipo_quest = st.selectbox("📝 Tipo de Questão", ["Múltipla Escolha (A-E)", "Abertas (Dissertativas)", "Mista (50/50)"])
                with c_ia2: nivel_dif = st.selectbox("⚙️ Dificuldade", ["Fácil", "Médio", "Difícil"])
                with c_ia3: qtd_quest = st.number_input("🔢 Quantidade de Questões", min_value=1, max_value=50, value=10)
                with c_ia4: peso_quest = st.number_input("⚖️ Peso por Questão", min_value=0.1, max_value=10.0, value=1.0, step=0.1)
                gerar_prova_btn = st.form_submit_button("🚀 Elaborar Avaliação Inédita com IA", type="primary", use_container_width=True)

            if gerar_prova_btn:
                if not assunto and not arquivo_upload:
                    st.warning("⚠️ Por favor, digite um Assunto ou envie um Arquivo Base para a IA analisar.")
                else:
                    with st.spinner("Lendo material e conectando ao núcleo de IA... Elaborando prova..."):
                        try:
                            texto_extraido = ""
                            if arquivo_upload is not None:
                                try:
                                    if arquivo_upload.name.endswith(".txt"):
                                        texto_extraido = arquivo_upload.read().decode("utf-8")
                                    elif arquivo_upload.name.endswith(".pdf"):
                                        leitor_pdf = PyPDF2.PdfReader(arquivo_upload)
                                        for pagina in leitor_pdf.pages:
                                            texto_extraido += pagina.extract_text() + "\n"
                                except Exception as e:
                                    st.error(f"Não foi possível ler o arquivo enviado. Detalhes: {e}")
                                    texto_extraido = ""

                            modelo = genai.GenerativeModel('gemini-2.5-flash')
                            prompt = f"Você é um professor elaborando uma prova. Assunto: {assunto}. Nível: {nivel_dif}. Qtd Questões: {qtd_quest}. Tipo: {tipo_quest}. Peso: {peso_quest} pts/cada.\n"
                            
                            if texto_extraido != "":
                                prompt += f"\nATENÇÃO: Utilize o texto abaixo como sua ÚNICA e EXCLUSIVA fonte de informações para formular as questões. Não invente dados que não estejam no texto:\n\n---\n{texto_extraido[:15000]}\n---\n"
                            
                            prompt += "\nFormate a prova de forma limpa. Inclua um cabeçalho escolar (Escola Projeto Saber, Nome, Data). NÃO coloque o gabarito junto com a prova. O GABARITO DEVE FICAR APENAS NO FINAL, isolado por uma linha e marcado como 'GABARITO DO PROFESSOR'."
                            
                            safety_settings = [
                                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                            ]
                            
                            resposta = modelo.generate_content(prompt, safety_settings=safety_settings)
                            texto_prova = resposta.text
                            
                            st.success("✅ Avaliação forjada com sucesso pela Inteligência Artificial!")
                            st.text_area("📄 Pré-Visualização do Documento:", texto_prova, height=500)
                            
                            col_exp1, col_exp2 = st.columns(2)
                            with col_exp1: st.download_button(label="📥 Baixar (.TXT)", data=texto_prova, file_name=f"Prova_{assunto.replace(' ', '_')}.txt", mime="text/plain", use_container_width=True)
                            with col_exp2: st.button("🖨️ Imprimir / Salvar PDF (Ctrl+P)", use_container_width=True)
                                
                        except Exception as e:
                            erro_str = str(e).lower()
                            if "429" in erro_str or "quota" in erro_str:
                                st.warning("🚦 **Servidor Ocupado:** O limite gratuito da IA foi atingido ou sua chave está bloqueada temporariamente pelo uso excessivo. Tente novamente mais tarde.")
                            elif "api_key" in erro_str or "key invalid" in erro_str:
                                st.error("🔑 **Erro na Chave:** A sua chave da API está inválida ou foi digitada incorretamente.")
                            else:
                                st.error(f"⚠️ Erro de conexão com a IA: {e}")
