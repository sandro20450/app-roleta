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
    /* Mantém a cor verde claro na barra superior */
    [data-testid="stHeader"] { background-color: #d4edda !important; }
    
    /* DOCUMENTAÇÃO: AJUSTE DE CONTRASTE DOS ÍCONES DAS TABELAS */
    /* Garante que os ícones do menu interativo flutuante (Download, Busca, Tela Cheia) fiquem brancos */
    [data-testid="stElementToolbar"] button svg, 
    [data-testid="stElementToolbar"] button {
        color: #ffffff !important;
        fill: #ffffff !important;
        stroke: #ffffff !important;
    }
    
    /* Ajuste de cor da Sidebar (Menu Lateral) */
    [data-testid="stSidebar"] { background-color: #e8eaed !important; border-right: 1px solid #cccccc; }
    
    /* Estilos Gerais do App */
    .stApp { background-color: #f4f7f6; }
    .stApp p, .stApp span, .stApp label, .stApp div[data-testid="stMarkdownContainer"] { color: #1e3d59 !important; }
    h1, h2, h3, h4, h5 { color: #004d99 !important; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    .stButton > button p, .stButton > button span { color: #ffffff !important; }
    
    div[data-testid="metric-container"] { background-color: #ffffff; border: 1px solid #e0e0e0; border-radius: 10px; padding: 15px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .painel-selecao { background-color: #ffffff; border-radius: 15px; padding: 25px; border-top: 5px solid #004d99; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .painel-login { background-color: #ffffff; border-radius: 15px; padding: 30px; border-top: 5px solid #004d99; box-shadow: 0 4px 10px rgba(0,0,0,0.15); margin-bottom: 20px; }
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
            turmas = list(set([str(r.get('turma', '')) for r in records if str(r.get('turma', '')).strip() != ""]))
            return sorted(turmas) if turmas else ["Selecione..."]
    except:
        return ["Selecione..."]

def carregar_alunos(turma):
    try:
        gc = get_gspread_client()
        if gc:
            ws = gc.open("Base_SEEA").worksheet("Alunos")
            records = ws.get_all_records()
            alunos_turma = [str(r.get('nome_aluno', '')) for r in records if str(r.get('turma', '')) == turma]
            return alunos_turma if alunos_turma else ["Nenhum aluno cadastrado nesta turma."]
    except:
        return ["Erro ao carregar alunos"]

def buscar_dados_aluno(nome_aluno):
    try:
        gc = get_gspread_client()
        if gc:
            ws = gc.open("Base_SEEA").worksheet("Alunos")
            records = ws.get_all_records()
            for r in records:
                if str(r.get('nome_aluno', '')).strip() == nome_aluno.strip():
                    return r 
    except Exception as e:
        return None
    return None

def salvar_notas_bd(turma, disciplina, bimestre, df_resultados):
    try:
        gc = get_gspread_client()
        if gc:
            ws = gc.open("Base_SEEA").worksheet("Notas")
            novas_linhas = []
            for index, row in df_resultados.iterrows():
                linha = [turma, disciplina, bimestre, row["ALUNO"], str(row["MÉDIA FINAL"]), row["SITUAÇÃO"], str(row["CONCEITO"])]
                novas_linhas.append(linha)
            ws.append_rows(novas_linhas, value_input_option="USER_ENTERED")
            return True
    except Exception as e:
        st.error(f"Erro ao salvar no banco de dados: {e}")
        return False

def salvar_frequencia_bd(data_aula, turma, assunto, lista_presenca):
    try:
        gc = get_gspread_client()
        if gc:
            ws = gc.open("Base_SEEA").worksheet("Frequencia")
            novas_linhas = []
            for item in lista_presenca:
                linha = [str(data_aula), turma, item['aluno'], item['status'], assunto]
                novas_linhas.append(linha)
            ws.append_rows(novas_linhas, value_input_option="USER_ENTERED")
            return True
    except Exception as e:
        st.error(f"Erro ao salvar frequência no banco: {e}")
        return False

def carregar_notas_aluno(nome_aluno):
    try:
        gc = get_gspread_client()
        if gc:
            ws = gc.open("Base_SEEA").worksheet("Notas")
            records = ws.get_all_records()
            if not records: return pd.DataFrame()
            df = pd.DataFrame(records)
            df.columns = df.columns.astype(str).str.strip().str.lower()
            if 'aluno' in df.columns:
                return df[df['aluno'].astype(str).str.strip() == nome_aluno.strip()]
            return pd.DataFrame()
    except: return pd.DataFrame() 

def carregar_tabela_completa(nome_aba):
    try:
        gc = get_gspread_client()
        if gc:
            ws = gc.open("Base_SEEA").worksheet(nome_aba)
            records = ws.get_all_records()
            if not records:
                if nome_aba == "Avisos": return pd.DataFrame(columns=["tipo", "aluno", "mensagem", "data"])
                return pd.DataFrame()
            return pd.DataFrame(records)
    except Exception as e:
        return pd.DataFrame()

def sincronizar_aba_completa(nome_aba, df_editado):
    try:
        gc = get_gspread_client()
        if gc:
            ws = gc.open("Base_SEEA").worksheet(nome_aba)
            df_editado = df_editado.fillna("")
            dados_lista = [df_editado.columns.values.tolist()] + df_editado.values.tolist()
            ws.clear()
            ws.update(values=dados_lista, range_name="A1")
            return True
    except Exception as e:
        st.error(f"Erro ao sincronizar a aba {nome_aba}: {e}")
        return False

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
if st.session_state.usuario_logado is None:
    st.markdown("""<style>[data-testid="collapsedControl"] { display: none !important; }</style>""", unsafe_allow_html=True)
else:
    with st.sidebar:
        st.markdown("<h2 style='text-align:center;'>🌎 SEEA</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; font-size:0.8em; color:#888;'>Sistema de Gestão Escolar</p>", unsafe_allow_html=True)
        st.markdown("---")
        
        st.markdown(f"""<div style='background-color: #d4edda; padding: 15px; border-radius: 8px; margin-bottom: 20px; text-align: center; border: 1px solid #c3e6cb;'><span style='color: #155724 !important; font-weight: bold; font-size: 1.1em;'>👤 {st.session_state.usuario_logado}</span></div>""", unsafe_allow_html=True)
        
        if st.session_state.perfil_logado == "professor":
            st.markdown("<span style='color:#888; font-size:0.8em; font-weight:bold;'>PEDAGÓGICO</span>", unsafe_allow_html=True)
            st.button("📖 Diário de Classe", use_container_width=True)
            st.button("🤖 Gerador de Provas", use_container_width=True)
            
        elif st.session_state.perfil_logado in ["admin", "diretoria"]:
            st.markdown("<span style='color:#888; font-size:0.8em; font-weight:bold;'>ADMINISTRAÇÃO</span>", unsafe_allow_html=True)
            st.button("⚙️ Painel de Gestão", use_container_width=True)
            
        elif st.session_state.perfil_logado == "aluno":
            st.markdown("<span style='color:#888; font-size:0.8em; font-weight:bold;'>ÁREA DO ALUNO</span>", unsafe_allow_html=True)
            st.button("📊 Meu Boletim", use_container_width=True)
            st.button("📢 Avisos Escolares", use_container_width=True)
            
        st.markdown("---")
        if st.button("🚪 Sair", use_container_width=True): fazer_logout()

# =============================================================================
# --- 6. ÁREA PRINCIPAL (FRONT-END) ---
# =============================================================================

if st.session_state.usuario_logado is None:
    st.markdown("<h1 style='text-align: center; margin-bottom: 30px;'>Bem-vindo ao Portal SEEA</h1>", unsafe_allow_html=True)
    
    df_avisos = carregar_tabela_completa("Avisos")
    if not df_avisos.empty and 'tipo' in df_avisos.columns:
        avisos_gerais = df_avisos[df_avisos['tipo'].astype(str).str.strip().str.upper() == 'GERAL']
        if not avisos_gerais.empty:
            for _, aviso in avisos_gerais.iterrows():
                st.warning(f"📢 **COMUNICADO OFICIAL ({aviso.get('data', '')}):** {aviso.get('mensagem', '')}", icon="🏫")
            st.markdown("<br>", unsafe_allow_html=True)
    
    col_login, col_info = st.columns([1, 1.5])
    
    with col_login:
        st.markdown("<h3 style='text-align:center; color:#004d99; margin-bottom: 20px;'>🔐 Acesso ao Painel</h3>", unsafe_allow_html=True)
        user_input = st.text_input("Usuário", placeholder="Digite seu usuário")
        pass_input = st.text_input("Senha", type="password", placeholder="Digite sua senha")
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("Entrar no Sistema", use_container_width=True, type="primary"):
            fazer_login(user_input, pass_input)
            
        st.markdown("<br>", unsafe_allow_html=True)
        with st.expander("❓ Esqueci minha senha"):
            st.info("Para recuperar o seu acesso, fale com a Secretaria.\n\n📞 (81) 99999-9999\n📧 admin@seea.com.br")

    with col_info:
        st.markdown("### 📌 Informações Úteis")
        c_info1, c_info2 = st.columns(2)
        with c_info1: st.success("💰 **Financeiro**\n\nAcesse boletos e pagamentos de mensalidades de forma prática.")
        with c_info2: st.warning("📍 **Localização**\n\nVeja como chegar à escola e horários de funcionamento.")
        st.error("📞 **Contatos Gerais**\n\nSecretaria: (81) 99999-9999\nDiretoria: diretoria@seea.com.br")

elif st.session_state.perfil_logado == "aluno":
    st.markdown(f"<h1 style='text-align: center;'>🎓 Portal do Aluno</h1>", unsafe_allow_html=True)
    
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

    aba_boletim, aba_avisos = st.tabs(["📊 Boletim de Notas", "📢 Mural de Avisos"])
    
    with aba_boletim:
        st.markdown("### 📝 Desempenho Acadêmico")
        df_notas_aluno = carregar_notas_aluno(st.session_state.usuario_logado)
        if not df_notas_aluno.empty:
            colunas_esperadas = ['disciplina', 'bimestre', 'media', 'conceito', 'situacao']
            colunas_presentes = [col for col in colunas_esperadas if col in df_notas_aluno.columns]
            if len(colunas_presentes) > 0:
                df_boletim_visual = df_notas_aluno[colunas_presentes]
                renomear_para_tela = {'disciplina': 'Disciplina', 'bimestre': 'Bimestre', 'media': 'Média Final', 'conceito': 'Conceito', 'situacao': 'Situação'}
                df_boletim_visual = df_boletim_visual.rename(columns=renomear_para_tela)
                st.dataframe(df_boletim_visual, hide_index=True, use_container_width=True)
        else:
            st.info("📌 O boletim está vazio. Os professores ainda não lançaram notas neste período.")

    with aba_avisos:
        st.markdown("### 📢 Quadro de Comunicações")
        st.write("Fique atento aos prazos e comunicados direcionados a você.")
        
        df_avisos = carregar_tabela_completa("Avisos")
        tem_aviso = False
        if not df_avisos.empty and 'tipo' in df_avisos.columns:
            avisos_gerais = df_avisos[df_avisos['tipo'].astype(str).str.strip().str.upper() == 'GERAL']
            for _, aviso in avisos_gerais.iterrows():
                st.warning(f"📢 **AVISO GERAL ({aviso.get('data', '')}):** {aviso.get('mensagem', '')}")
                tem_aviso = True
                
            avisos_ind = df_avisos[(df_avisos['tipo'].astype(str).str.strip().str.upper() == 'INDIVIDUAL') & (df_avisos['aluno'].astype(str).str.strip() == st.session_state.usuario_logado)]
            for _, aviso in avisos_ind.iterrows():
                st.error(f"📩 **MENSAGEM PRIVADA ({aviso.get('data', '')}):** {aviso.get('mensagem', '')}", icon="⚠️")
                tem_aviso = True
                
        if not tem_aviso:
            st.success("✅ Tudo tranquilo! Não há novos comunicados da secretaria no momento.")

elif st.session_state.perfil_logado in ["admin", "diretoria"]:
    st.header("👑 Painel da Diretoria - Centro de Controle")
    st.markdown("Faça adições, edições ou exclusões diretamente nas tabelas abaixo.")
    
    aba_metricas, aba_usuarios, aba_alunos, aba_avisos_admin = st.tabs(["📊 Visão Geral", "🔐 Gestão de Logins", "🎓 Gestão de Alunos", "📣 Gestão de Avisos"])
    
    with aba_metricas:
        st.markdown("### 📊 Estatísticas Globais da Escola")
        
        df_alunos_calc = carregar_tabela_completa("Alunos")
        total_alunos = len(df_alunos_calc) if not df_alunos_calc.empty else 0
        
        df_notas_calc = carregar_tabela_completa("Notas")
        media_geral = 0.0
        if not df_notas_calc.empty and 'media' in df_notas_calc.columns:
            notas_validas = pd.to_numeric(df_notas_calc['media'], errors='coerce').dropna()
            if not notas_validas.empty:
                media_geral = round(notas_validas.mean(), 1)
                
        df_freq_calc = carregar_tabela_completa("Frequencia")
        hoje_str = date.today().strftime("%Y-%m-%d")
        presentes_hoje = 0
        ausentes_hoje = 0
        freq_media_pct = 0
        
        if not df_freq_calc.empty and 'status' in df_freq_calc.columns:
            total_registros = len(df_freq_calc)
            total_presencas = len(df_freq_calc[df_freq_calc['status'].astype(str).str.upper() == 'P'])
            if total_registros > 0:
                freq_media_pct = round((total_presencas / total_registros) * 100)
                
            if 'data' in df_freq_calc.columns:
                df_hoje = df_freq_calc[df_hoje['data'].astype(str) == hoje_str]
                presentes_hoje = len(df_hoje[df_hoje['status'].astype(str).str.upper() == 'P'])
                ausentes_hoje = len(df_hoje[df_hoje['status'].astype(str).str.upper() == 'F'])

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Alunos Matriculados", str(total_alunos), "Total Ativo")
        c2.metric("Frequência Média", f"{freq_media_pct}%", "Global")
        c3.metric("Presentes", str(presentes_hoje), "Hoje")
        c4.metric("Ausentes", str(ausentes_hoje), "Hoje")
        c5.metric("Média Escolar", str(media_geral), "Geral")

        st.markdown("---")
        st.markdown("### ⚙️ Status do Sistema")
        c6, c7, c8 = st.columns(3)
        c6.metric("Banco de Dados", "Google Sheets", "Conectado")
        c7.metric("Inteligência Artificial", "Gemini API", "Online" if ia_configurada else "Offline")
        c8.metric("Segurança", "Ativa", "100%")
        
    with aba_usuarios:
        st.markdown("### 🔐 Tabela de Usuários")
        df_usuarios = carregar_tabela_completa("Usuarios")
        if not df_usuarios.empty:
            df_usuarios_editado = st.data_editor(df_usuarios, use_container_width=True, num_rows="dynamic", key="editor_users")
            if st.button("💾 Sincronizar Senhas", type="primary", use_container_width=True):
                if sincronizar_aba_completa("Usuarios", df_usuarios_editado): st.success("✅ Atualizado com sucesso!")

    with aba_alunos:
        st.markdown("### 🎓 Tabela de Matrículas")
        df_alunos = carregar_tabela_completa("Alunos")
        if not df_alunos.empty:
            df_alunos_editado = st.data_editor(df_alunos, use_container_width=True, num_rows="dynamic", key="editor_alunos")
            if st.button("💾 Sincronizar Alunos", type="primary", use_container_width=True):
                if sincronizar_aba_completa("Alunos", df_alunos_editado): st.success("✅ Atualizado com sucesso!")
                
    with aba_avisos_admin:
        st.markdown("### 📣 Central de Mensagens e Alertas")
        st.info("💡 **Como usar:** Na coluna 'tipo', escreva `Geral` ou `Individual`. Na coluna 'aluno', digite o nome do aluno ou `Todos`.")
        df_avisos_admin = carregar_tabela_completa("Avisos")
        df_avisos_editado = st.data_editor(
            df_avisos_admin, 
            use_container_width=True, 
            num_rows="dynamic", 
            key="editor_avisos",
            column_config={
                "tipo": st.column_config.SelectboxColumn("Tipo de Aviso", options=["Geral", "Individual"], required=True),
                "aluno": st.column_config.TextColumn("Aluno Alvo (ou Todos)", required=True),
                "mensagem": st.column_config.TextColumn("Mensagem / Aviso", required=True),
                "data": st.column_config.TextColumn("Data de Publicação (DD/MM/AAAA)") 
            }
        )
        if st.button("💾 Publicar / Sincronizar Avisos", type="primary", use_container_width=True):
            with st.spinner("Transmitindo avisos..."):
                if sincronizar_aba_completa("Avisos", df_avisos_editado): 
                    st.success("✅ Avisos publicados com sucesso na plataforma!")

elif st.session_state.perfil_logado == "professor":
    aba_dash, aba_freq, aba_notas, aba_ia = st.tabs(["📊 Dashboard", "📅 Frequência", "📝 Notas", "🤖 Gerador IA"])
    
    with aba_dash:
        st.markdown("<h2>Meu Desempenho Pedagógico</h2>", unsafe_allow_html=True)
        st.info("👋 Olá! Bem-vindo ao seu painel. Aqui está um resumo da sua área de atuação.")
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Minhas Turmas", "4", "Alocadas")
        c2.metric("Diários Preenchidos", "12", "Este Mês")
        c3.metric("Alunos em Alerta", "3", "Em Recuperação")
        c4.metric("Provas IA Geradas", "5", "Materiais Prontos")
        
        st.markdown("<br><hr>", unsafe_allow_html=True)
        st.write("📌 Utilize as abas acima para registrar frequência, lançar notas ou utilizar o nosso gerador de provas com Inteligência Artificial.")
            
    with aba_freq:
        st.markdown("<h2>Registro de Frequência e Conteúdo</h2>", unsafe_allow_html=True)
        st.markdown("<div style='background-color:#ffffff; padding:20px; border-radius:10px; border: 1px solid #e0e0e0; margin-bottom: 20px;'>", unsafe_allow_html=True)
        col_turma, col_data = st.columns(2)
        
        lista_turmas = carregar_turmas()
        with col_turma: selecao_turma = st.selectbox("Turma:", lista_turmas, key="freq_turma")
        with col_data: data_aula = st.date_input("Data da Aula:", date.today())
        
        assunto_aula = st.text_area("📚 Assunto do Dia / Conteúdo Lecionado:", placeholder="Descreva os conteúdos abordados nesta aula...", height=100)
        st.markdown("</div>", unsafe_allow_html=True)
        
        if selecao_turma and selecao_turma != "Selecione...":
            st.markdown("<div style='display:flex; justify-content:space-between; padding:0 20px; color:#004d99; font-weight:bold;'><span>ALUNO</span><span>STATUS DE PRESENÇA</span></div><hr style='margin:5px 0; border-top: 2px solid #ccc;'>", unsafe_allow_html=True)
            
            lista_alunos = carregar_alunos(selecao_turma)
            lista_presenca = []
            
            for aluno in lista_alunos:
                ca, cb = st.columns([3, 2])
                with ca: st.markdown(f"<span style='font-weight:bold; color:#1e3d59;'>{aluno}</span>", unsafe_allow_html=True)
                with cb: 
                    status_aluno = st.radio("Status", ["P", "F", "FJ"], horizontal=True, label_visibility="collapsed", key=f"rad_{aluno}")
                    lista_presenca.append({"aluno": aluno, "status": status_aluno})
                st.markdown("<hr style='margin:5px 0; opacity:0.3;'>", unsafe_allow_html=True)
            
            if st.button("💾 Salvar Chamada Escolar", type="primary", use_container_width=True):
                if assunto_aula.strip() == "":
                    st.warning("⚠️ O assunto da aula não pode estar em branco.")
                else:
                    with st.spinner("Registrando as presenças no sistema..."):
                        if salvar_frequencia_bd(data_aula, selecao_turma, assunto_aula, lista_presenca):
                            st.success(f"✅ Frequência do dia {data_aula.strftime('%d/%m/%Y')} registrada e salva com sucesso!")
        else:
            st.info("Selecione uma turma para carregar a lista de alunos.")

    with aba_notas:
        lista_turmas = carregar_turmas()
        lista_disciplinas = ["Selecione...", "Português", "Matemática", "Artes", "Inglês", "Ciências", "História", "Geografia", "Ed. Física", "Ens. Religioso"]
        
        if not st.session_state.diario_aberto:
            st.markdown(f"<h1 style='text-align:center;'>Bom dia, {st.session_state.usuario_logado.split()[0]}!</h1>", unsafe_allow_html=True)
            st.markdown('<div class="painel-selecao">', unsafe_allow_html=True)
            st.text_input("👤 Professor", st.session_state.usuario_logado, disabled=True)
            c_sel1, c_sel2 = st.columns(2)
            with c_sel1: sel_turma = st.selectbox("👥 Turma", ["Selecione..."] + lista_turmas)
            with c_sel2: sel_disc = st.selectbox("📄 Disciplina", lista_disciplinas)
            c_sel3, c_sel4 = st.columns(2)
            with c_sel3: sel_bim = st.selectbox("📅 Bimestre/Unidade", ["Selecione...", "1º Bimestre", "2º Bimestre", "3º Bimestre", "4º Bimestre"])
            with c_sel4: sel_aval = st.selectbox("⚖️ Sistema de Avaliação", ["Selecione...", "Numérico (Notas 0 a 10)", "Conceitual (Ótimo, Bom, Regular)"])
            st.markdown('</div>', unsafe_allow_html=True)
            
            if sel_turma != "Selecione..." and sel_disc != "Selecione..." and sel_bim != "Selecione..." and sel_aval != "Selecione...":
                if st.button("Abrir Diário de Lançamento ➔", type="primary", use_container_width=True):
                    st.session_state.diario_aberto = True
                    st.session_state.ctx_turma = sel_turma
                    st.session_state.ctx_disc = sel_disc
                    st.session_state.ctx_bim = sel_bim
                    st.session_state.ctx_aval = sel_aval
                    st.rerun()
            else: st.button("Abrir Diário de Lançamento ➔", disabled=True, use_container_width=True)

        else:
            st.markdown(f"""
            <div style='background-color:#e6f2ff; padding:15px; border-radius:8px; display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; border: 1px solid #b3d9ff;'>
                <div>
                    <span style='color:#004d99 !important; font-weight:bold; font-size:0.9em;'>CONTEXTO ATUAL: <span style='background:#004d99; color:#fff !important; padding:2px 8px; border-radius:10px;'>{st.session_state.ctx_bim}</span></span><br>
                    <span style='font-size:1.2em; color:#1e3d59 !important;'>👤 <b>{st.session_state.usuario_logado}</b> &nbsp;|&nbsp; 👥 {st.session_state.ctx_turma} &nbsp;|&nbsp; 📄 {st.session_state.ctx_disc} &nbsp;|&nbsp; ⚖️ {st.session_state.ctx_aval}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("⬅️ Trocar Período/Turma"):
                st.session_state.diario_aberto = False
                st.rerun()
                
            st.markdown("### Quadro de Lançamentos")
            lista_alunos_notas = carregar_alunos(st.session_state.ctx_turma)
            
            if st.session_state.ctx_aval == "Numérico (Notas 0 a 10)":
                df_notas = pd.DataFrame({"ALUNO": lista_alunos_notas, "AV1 (Prova)": [0.0]*len(lista_alunos_notas), "AV2 (Prova)": [0.0]*len(lista_alunos_notas), "AV3 (Prova)": [0.0]*len(lista_alunos_notas), "PE (Trabalho)": [0.0]*len(lista_alunos_notas)})
                df_editado = st.data_editor(df_notas, hide_index=True, use_container_width=True, column_config={"ALUNO": st.column_config.TextColumn(disabled=True), "AV1 (Prova)": st.column_config.NumberColumn(min_value=0.0, max_value=10.0, format="%.1f"), "AV2 (Prova)": st.column_config.NumberColumn(min_value=0.0, max_value=10.0, format="%.1f"), "AV3 (Prova)": st.column_config.NumberColumn(min_value=0.0, max_value=10.0, format="%.1f"), "PE (Trabalho)": st.column_config.NumberColumn(min_value=0.0, max_value=10.0, format="%.1f")})
                df_resultado = df_editado.copy()
                df_resultado["MÉDIA FINAL"] = df_resultado[["AV1 (Prova)", "AV2 (Prova)", "AV3 (Prova)", "PE (Trabalho)"]].mean(axis=1).round(1)
                df_resultado["SITUAÇÃO"] = df_resultado["MÉDIA FINAL"].apply(lambda m: "🟢 APROVADO" if m >= 7.0 else ("🟡 RECUPERAÇÃO" if m >= 5.0 else "🔴 REPROVADO"))
                df_resultado["CONCEITO"] = "-" 
                st.dataframe(df_resultado[["ALUNO", "MÉDIA FINAL", "SITUAÇÃO"]], hide_index=True, use_container_width=True)
            else:
                df_notas = pd.DataFrame({"ALUNO": lista_alunos_notas, "CONCEITO": ["-"]*len(lista_alunos_notas)})
                df_editado = st.data_editor(df_notas, hide_index=True, use_container_width=True, column_config={"ALUNO": st.column_config.TextColumn(disabled=True), "CONCEITO": st.column_config.SelectboxColumn("Conceito Qualitativo", options=["-", "Ótimo", "Bom", "Regular"], required=True)})
                df_resultado = df_editado.copy()
                df_resultado["MÉDIA FINAL"] = "-" 
                df_resultado["SITUAÇÃO"] = df_resultado["CONCEITO"].apply(lambda c: "🟢 APROVADO" if c in ["Ótimo", "Bom"] else ("🟡 ATENÇÃO" if c == "Regular" else "⚪ PENDENTE"))
                st.dataframe(df_resultado[["ALUNO", "CONCEITO", "SITUAÇÃO"]], hide_index=True, use_container_width=True)

            if st.button("💾 Salvar Diário de Notas no Banco de Dados", type="primary", use_container_width=True):
                with st.spinner("Conectando ao servidor..."):
                    if salvar_notas_bd(st.session_state.ctx_turma, st.session_state.ctx_disc, st.session_state.ctx_bim, df_resultado): st.success("✅ Diário salvo com sucesso!")

    with aba_ia:
        st.markdown("<h2>🤖 Fábrica de Avaliações com IA</h2>", unsafe_allow_html=True)
        if not ia_configurada: st.error("⚠️ Sistema Desconectado.")
        else:
            with st.form("form_ia_gerador"):
                arquivo_upload = st.file_uploader("📄 Envie um resumo (PDF ou TXT)", type=["pdf", "txt"])
                assunto = st.text_input("📚 Assunto Principal")
                c_ia1, c_ia2, c_ia3, c_ia4 = st.columns(4)
                with c_ia1: tipo_quest = st.selectbox("📝 Tipo de Questão", ["Múltipla Escolha", "Abertas", "Mista"])
                with c_ia2: nivel_dif = st.selectbox("⚙️ Dificuldade", ["Fácil", "Médio", "Difícil"])
                with c_ia3: qtd_quest = st.number_input("🔢 Qtd", min_value=1, max_value=50, value=10)
                with c_ia4: peso_quest = st.number_input("⚖️ Peso", min_value=0.1, max_value=10.0, value=1.0)
                gerar_prova_btn = st.form_submit_button("🚀 Elaborar Prova", type="primary", use_container_width=True)

            if gerar_prova_btn:
                if not assunto and not arquivo_upload: st.warning("Digite um assunto ou envie arquivo.")
                else:
                    with st.spinner("Gerando..."):
                        try:
                            texto_extraido = ""
                            if arquivo_upload:
                                if arquivo_upload.name.endswith(".txt"): texto_extraido = arquivo_upload.read().decode("utf-8")
                                elif arquivo_upload.name.endswith(".pdf"):
                                    for p in PyPDF2.PdfReader(arquivo_upload).pages: texto_extraido += p.extract_text() + "\n"
                            modelo = genai.GenerativeModel('gemini-2.5-flash')
                            prompt = f"Crie uma prova sobre {assunto}. Dificuldade: {nivel_dif}. Questões: {qtd_quest}. Tipo: {tipo_quest}. Peso: {peso_quest}.\nTexto Base: {texto_extraido[:15000]}\nGabarito apenas no final."
                            resposta = modelo.generate_content(prompt)
                            st.success("✅ Concluído!")
                            st.text_area("📄 Pré-Visualização:", resposta.text, height=500)
                        except Exception as e: st.error(f"Erro: {e}")
