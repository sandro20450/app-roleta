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

# DOCUMENTAÇÃO: LIMPEZA DE CSS
# Mantemos apenas a estrutura (sem forçar cores de fundo) para os painéis
st.markdown("""
<style>
    /* Esconde a marca d'água do Streamlit no rodapé */
    footer { display: none !important; visibility: hidden !important; }
    
    .painel-selecao { border-radius: 15px; padding: 25px; border-top: 5px solid #004d99; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 20px; }
    .painel-login { border-radius: 15px; padding: 30px; border-top: 5px solid #004d99; box-shadow: 0 4px 10px rgba(0,0,0,0.15); margin-bottom: 20px; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# --- 2. CONEXÃO COM BANCO DE DADOS, MEMÓRIA E PDF ---
# =============================================================================
@st.cache_resource(ttl=3600, show_spinner=False)
def get_gspread_client():
    if "gcp_service_account" in st.secrets:
        creds = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds)
    return None

@st.cache_data(ttl=300, show_spinner=False)
def fetch_sheet_data_cached(nome_aba):
    gc = get_gspread_client()
    if gc:
        ws = gc.open("Base_SEEA").worksheet(nome_aba)
        return ws.get_all_values()
    return []

def carregar_tabela_completa(nome_aba):
    try:
        dados = fetch_sheet_data_cached(nome_aba)
        if not dados:
            if nome_aba == "Avisos": return pd.DataFrame(columns=["tipo", "aluno", "mensagem", "data"])
            return pd.DataFrame()
        if len(dados) == 1:
            df = pd.DataFrame(columns=dados[0])
        else:
            df = pd.DataFrame(dados[1:], columns=dados[0])
        df.columns = df.columns.astype(str).str.strip().str.lower()
        return df
    except Exception as e:
        return pd.DataFrame()

def carregar_usuarios():
    try:
        df = carregar_tabela_completa("Usuarios")
        if not df.empty and 'usuario' in df.columns and 'senha' in df.columns:
            usuarios = {}
            for _, row in df.iterrows():
                if str(row.get('usuario', '')).strip() != "":
                    usuarios[str(row['usuario']).strip()] = { "senha": str(row.get('senha', '')).strip(), "perfil": str(row.get('perfil', '')).lower().strip(), "nome": str(row.get('nome', '')).strip() }
            return usuarios
        return {}
    except Exception: return {}

def carregar_turmas():
    try:
        df = carregar_tabela_completa("Alunos")
        if not df.empty and 'turma' in df.columns:
            turmas = df['turma'].astype(str).str.strip().unique().tolist()
            turmas = [t for t in turmas if t != ""]
            return sorted(turmas) if turmas else []
        return []
    except: return []

def carregar_alunos(turma):
    try:
        df = carregar_tabela_completa("Alunos")
        if not df.empty and 'turma' in df.columns:
            col_nome = 'nome_aluno' if 'nome_aluno' in df.columns else ('aluno' if 'aluno' in df.columns else None)
            if col_nome:
                turma_limpa = str(turma).strip()
                df_filtrado = df[df['turma'].astype(str).str.strip() == turma_limpa]
                alunos = df_filtrado[col_nome].astype(str).str.strip().tolist()
                alunos = [a for a in alunos if a != ""]
                return alunos if alunos else []
        return []
    except Exception as e: return []

def buscar_dados_aluno(nome_aluno):
    try:
        df = carregar_tabela_completa("Alunos")
        col_nome = 'nome_aluno' if 'nome_aluno' in df.columns else ('aluno' if 'aluno' in df.columns else None)
        if not df.empty and col_nome:
            aluno_row = df[df[col_nome].astype(str).str.strip() == str(nome_aluno).strip()]
            if not aluno_row.empty: return aluno_row.iloc[0].to_dict()
    except Exception: return None
    return None

def carregar_notas_aluno(nome_aluno):
    try:
        df = carregar_tabela_completa("Notas")
        if not df.empty and 'aluno' in df.columns:
            return df[df['aluno'].astype(str).str.strip() == str(nome_aluno).strip()]
        return pd.DataFrame()
    except: return pd.DataFrame() 

def salvar_notas_bd(turma, disciplina, df_resultados):
    try:
        gc = get_gspread_client()
        if gc:
            ws = gc.open("Base_SEEA").worksheet("Notas")
            df_banco = carregar_tabela_completa("Notas")
            
            colunas_padrao = ['turma', 'aluno', 'disciplina', 'unidade_1', 'unidade_2', 'unidade_3', 'unidade_4', 'media_final', 'situacao']
            if df_banco.empty: df_banco = pd.DataFrame(columns=colunas_padrao)
            
            for index, row in df_resultados.iterrows():
                aluno_atual = str(row["ALUNO"]).strip()
                mask = ((df_banco['aluno'].astype(str).str.strip() == aluno_atual) & (df_banco['disciplina'].astype(str).str.strip() == disciplina.strip()))
                nova_linha = {
                    'turma': turma, 'aluno': aluno_atual, 'disciplina': disciplina,
                    'unidade_1': str(row.get("I Unidade", "-")), 'unidade_2': str(row.get("II Unidade", "-")),
                    'unidade_3': str(row.get("III Unidade", "-")), 'unidade_4': str(row.get("IV Unidade", "-")),
                    'media_final': str(row.get("MÉDIA FINAL", "-")), 'situacao': str(row.get("SITUAÇÃO", "-"))
                }
                if df_banco[mask].empty: df_banco = pd.concat([df_banco, pd.DataFrame([nova_linha])], ignore_index=True)
                else:
                    idx = df_banco[mask].index[0]
                    for col, val in nova_linha.items(): df_banco.at[idx, col] = val
                        
            dados_lista = [df_banco.columns.values.tolist()] + df_banco.values.tolist()
            ws.clear()
            ws.update(values=dados_lista, range_name="A1")
            st.cache_data.clear() 
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
            st.cache_data.clear()
            return True
    except Exception as e:
        st.error(f"Erro ao salvar frequência no banco: {e}")
        return False

def sincronizar_aba_completa(nome_aba, df_editado):
    try:
        gc = get_gspread_client()
        if gc:
            ws = gc.open("Base_SEEA").worksheet(nome_aba)
            df_editado = df_editado.fillna("")
            dados_lista = [df_editado.columns.values.tolist()] + df_editado.values.tolist()
            ws.clear()
            ws.update(values=dados_lista, range_name="A1")
            st.cache_data.clear()
            return True
    except Exception as e:
        st.error(f"Erro ao sincronizar a aba {nome_aba}: {e}")
        return False

# DOCUMENTAÇÃO: MOTOR GERADOR DE PDF
def gerar_pdf_boletim(nome_aluno, dados_aluno, df_boletim):
    try:
        from fpdf import FPDF
    except ImportError:
        return None 
        
    class PDF(FPDF):
        def header(self):
            self.set_font('Arial', 'B', 14)
            self.cell(0, 10, 'SEEA - BOLETIM ESCOLAR OFICIAL', 0, 1, 'C')
            self.ln(5)

    pdf = PDF()
    pdf.add_page()
    
    def limpa_txt(texto):
        for emoji in ["🟢", "🟡", "⚪", "🔴"]:
            texto = texto.replace(emoji, "")
        return texto.strip().encode('latin-1', 'replace').decode('latin-1')

    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 8, limpa_txt(f"Aluno(a): {nome_aluno}"), 0, 1)
    
    turma = dados_aluno.get('turma', 'N/A')
    turno = dados_aluno.get('turno', 'N/A')
    pdf.set_font('Arial', '', 10)
    pdf.cell(0, 8, limpa_txt(f"Turma: {turma}  |  Turno: {turno}"), 0, 1)
    pdf.ln(5)
    
    colunas = df_boletim.columns.tolist()
    largura_col = 190 / len(colunas) 
    
    pdf.set_font('Arial', 'B', 9)
    for col in colunas:
        pdf.cell(largura_col, 8, limpa_txt(str(col)), 1, 0, 'C')
    pdf.ln()
    
    pdf.set_font('Arial', '', 8)
    for _, row in df_boletim.iterrows():
        for col in colunas:
            val = str(row[col])
            pdf.cell(largura_col, 8, limpa_txt(val), 1, 0, 'C')
        pdf.ln()
        
    return pdf.output(dest='S').encode('latin-1')

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
    st.cache_data.clear() 
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
        
        if st.button("🔄 Atualizar Sistema (Limpar Memória)", use_container_width=True):
            st.cache_data.clear()
            st.success("Memória renovada!")
            time.sleep(1)
            st.rerun()
            
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
            st.info("Para recuperar o seu acesso, fale com a Secretaria.\n\n📞 (81) 98328-8495")
            
    with col_info:
        st.markdown("### 📌 Informações Úteis")
        
        with st.expander("💰 **Financeiro (Pagamentos e Taxas)**", expanded=False):
            st.markdown("Realize o pagamento da sua mensalidade de forma rápida e segura escolhendo uma das opções abaixo:")
            st.markdown("---")
            
            st.markdown("##### 1. PIX (Cópia e Cola)")
            st.write("Copie a chave PIX (CPF: ELIUDE BERNARDO DE SOUZA SILVA) abaixo usando o botão de copiar à direita:")
            st.code("04994867460", language="text") 
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            st.markdown("##### 2. PAGAMENTO NA PLATAFORMA ASAAS")
            st.write("Acesse o link para o portal de pagamentos seguros.")
            st.link_button("💳 Abrir Plataforma ASAAS", "https://api.whatsapp.com/send?phone=5547933007606", use_container_width=True)
                
        with st.expander("📍 **Nossa localização**", expanded=False):
            st.markdown("**Endereço:** Endereço: Rua Antônio José de Paiva, S/N Loteamento Real Vitória - Vitória de Santo Antão - PE")
            st.markdown("**Ponto de Referência:** 2ª rua à direita após a antiga Escola do Rotary (entrar ao lado da Igreja Assembleia de Deus).")
            st.markdown("---")
            st.link_button("🗺️ Ver Rota no Google Maps", "https://www.google.com/maps/place/R.+Nossa+Sra.+da+Aparecida,+396+-+L%C3%ADdia+Queiroz,+Vit%C3%B3ria+de+Santo+Ant%C3%A3o+-+PE,+55614-700/@-8.1252024,-35.2906503,17z/data=!4m16!1m9!3m8!1s0x7aa54bd26c5d1c9:0x8f8f9c6e05c506a1!2sR.+Nossa+Sra.+da+Aparecida,+396+-+L%C3%ADdia+Queiroz,+Vit%C3%B3ria+de+Santo+Ant%C3%A3o+-+PE,+55614-700!3b1!8m2!3d-8.1253253!4d-35.2907675!10e5!16s%2Fg%2F11hpy78k5b!3m5!1s0x7aa54bd26c5d1c9:0x8f8f9c6e05c506a1!8m2!3d-8.1253253!4d-35.2907675!16s%2Fg%2F11hpy78k5b?entry=ttu&g_ep=EgoyMDI1MDYxMS4wIKXMDSoASAFQAw%3D%3D", use_container_width=True)
            
        with st.expander("📞 **Contatos e Suporte**", expanded=False):
            st.markdown("Precisando de ajuda? Nossa equipe está pronta para atender:")
            st.markdown("<br>", unsafe_allow_html=True) 
            st.markdown("- **Secretaria (WhatsApp):** [(81) 98328-8495](https://wa.me/5581983288495)")
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("- **Coord. Infantil:** [(81) 99394-3245](https://wa.me/5581993943245)")
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("- **Coord. Fundamental 1:** [(81) 98508-0876](https://wa.me/5581985080876)")

elif st.session_state.perfil_logado == "aluno":
    st.markdown(f"<h1 style='text-align: center;'>🎓 Portal do Aluno</h1>", unsafe_allow_html=True)
    
    dados_do_aluno = buscar_dados_aluno(st.session_state.usuario_logado)
    if dados_do_aluno:
        st.markdown(f"""
        <div style='background-color:#e6f2ff; padding:15px; border-radius:8px; display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; border: 1px solid #b3d9ff;'>
            <div>
                <span style='font-size:1.2em; color:#1e3d59 !important;'>👤 <b>{st.session_state.usuario_logado}</b></span><br>
                <span style='color:#004d99 !important; font-weight:bold;'>👥 Turma: {dados_do_aluno.get('turma', 'N/A')}  |  🏫 Ensino: {dados_do_aluno.get('ensino', 'N/A')}  |  ⏰ Turno: {dados_do_aluno.get('turno', 'N/A')}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    aba_boletim, aba_avisos = st.tabs(["📊 Boletim de Notas", "📢 Mural de Avisos"])
    
    with aba_boletim:
        st.markdown("### 📝 Desempenho Acadêmico")
        df_notas_aluno = carregar_notas_aluno(st.session_state.usuario_logado)
        
        if not df_notas_aluno.empty:
            colunas_esperadas = ['disciplina', 'unidade_1', 'unidade_2', 'unidade_3', 'unidade_4', 'media_final', 'situacao']
            colunas_presentes = [col for col in colunas_esperadas if col in df_notas_aluno.columns]
            
            if len(colunas_presentes) > 0:
                df_boletim_visual = df_notas_aluno[colunas_presentes]
                
                renomear_para_tela = {
                    'disciplina': 'Disciplina', 'unidade_1': 'I Unid.', 'unidade_2': 'II Unid.',
                    'unidade_3': 'III Unid.', 'unidade_4': 'IV Unid.', 'media_final': 'Média Final', 'situacao': 'Situação'
                }
                df_boletim_visual = df_boletim_visual.rename(columns=renomear_para_tela)
                
                st.dataframe(df_boletim_visual, hide_index=True, use_container_width=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                
                pdf_bytes = gerar_pdf_boletim(st.session_state.usuario_logado, dados_do_aluno, df_boletim_visual)
                if pdf_bytes:
                    col_vazia, col_btn = st.columns([3, 1]) 
                    with col_btn:
                        st.download_button(
                            label="📄 Baixar Boletim em PDF",
                            data=pdf_bytes,
                            file_name=f"Boletim_{st.session_state.usuario_logado}.pdf",
                            mime="application/pdf",
                            type="primary",
                            use_container_width=True
                        )
                else:
                    st.warning("⚠️ Ferramenta PDF não instalada. Administrador: adicione 'fpdf' no arquivo requirements.txt do GitHub.")

            else:
                st.info("⚠️ A planilha de notas não está com as colunas formatadas corretamente (unidade_1, unidade_2...).")
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
        if not df_notas_calc.empty and 'media_final' in df_notas_calc.columns:
            notas_validas = pd.to_numeric(df_notas_calc['media_final'], errors='coerce').dropna()
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
                
            # CORREÇÃO APLICADA AQUI: df_freq_calc em vez de df_hoje no filtro
            if 'data' in df_freq_calc.columns:
                df_hoje = df_freq_calc[df_freq_calc['data'].astype(str) == hoje_str]
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
        with col_turma: selecao_turma = st.selectbox("Turma:", ["Selecione..."] + lista_turmas, key="freq_turma")
        with col_data: data_aula = st.date_input("Data da Aula:", date.today())
        
        assunto_aula = st.text_area("📚 Assunto do Dia / Conteúdo Lecionado:", placeholder="Descreva os conteúdos abordados nesta aula...", height=100)
        st.markdown("</div>", unsafe_allow_html=True)
        
        if selecao_turma and selecao_turma != "Selecione...":
            st.markdown("<div style='display:flex; justify-content:space-between; padding:0 20px; color:#004d99; font-weight:bold;'><span>ALUNO</span><span>STATUS DE PRESENÇA</span></div><hr style='margin:5px 0; border-top: 2px solid #ccc;'>", unsafe_allow_html=True)
            
            lista_alunos = carregar_alunos(selecao_turma)
            if not lista_alunos:
                st.warning("Nenhum aluno encontrado para esta turma. Clique em 'Atualizar Sistema' na barra lateral.")
            else:
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
            
            sel_aval = st.selectbox("⚖️ Sistema de Avaliação", ["Selecione...", "Numérico (Notas 0 a 10)", "Conceitual (Ótimo, Bom, Regular)"])
            st.markdown('</div>', unsafe_allow_html=True)
            
            if sel_turma != "Selecione..." and sel_disc != "Selecione..." and sel_aval != "Selecione...":
                if st.button("Abrir Diário de Lançamento ➔", type="primary", use_container_width=True):
                    st.session_state.diario_aberto = True
                    st.session_state.ctx_turma = sel_turma
                    st.session_state.ctx_disc = sel_disc
                    st.session_state.ctx_aval = sel_aval
                    st.rerun()
            else: st.button("Abrir Diário de Lançamento ➔", disabled=True, use_container_width=True)

        else:
            st.markdown(f"""
            <div style='background-color:#e6f2ff; padding:15px; border-radius:8px; display:flex; justify-content:space-between; align-items:center; margin-bottom:20px; border: 1px solid #b3d9ff;'>
                <div>
                    <span style='color:#004d99 !important; font-weight:bold; font-size:0.9em;'>VISÃO ANUAL COMPLETA</span><br>
                    <span style='font-size:1.2em; color:#1e3d59 !important;'>👤 <b>{st.session_state.usuario_logado}</b>  |  👥 {st.session_state.ctx_turma}  |  📄 {st.session_state.ctx_disc}  |  ⚖️ {st.session_state.ctx_aval}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if st.button("⬅️ Voltar ao Menu de Seleção"):
                st.session_state.diario_aberto = False
                st.rerun()
                
            st.markdown("### Quadro de Lançamentos")
            
            lista_alunos_notas = carregar_alunos(st.session_state.ctx_turma)
            df_notas_banco = carregar_tabela_completa("Notas")
            
            df_contexto = pd.DataFrame()
            if not df_notas_banco.empty:
                df_contexto = df_notas_banco[
                    (df_notas_banco['turma'].astype(str).str.strip() == st.session_state.ctx_turma.strip()) &
                    (df_notas_banco['disciplina'].astype(str).str.strip() == st.session_state.ctx_disc.strip())
                ]
            
            if not lista_alunos_notas:
                st.warning("⚠️ Nenhum aluno foi encontrado para esta turma.")
            else:
                if st.session_state.ctx_aval == "Numérico (Notas 0 a 10)":
                    u1_l, u2_l, u3_l, u4_l = [], [], [], []
                    for aluno in lista_alunos_notas:
                        aluno_row = df_contexto[df_contexto['aluno'].astype(str).str.strip() == aluno] if not df_contexto.empty else pd.DataFrame()
                        if not aluno_row.empty:
                            def safe_float(v):
                                try: return float(v)
                                except: return 0.0
                            u1_l.append(safe_float(aluno_row.iloc[0].get('unidade_1', 0.0)))
                            u2_l.append(safe_float(aluno_row.iloc[0].get('unidade_2', 0.0)))
                            u3_l.append(safe_float(aluno_row.iloc[0].get('unidade_3', 0.0)))
                            u4_l.append(safe_float(aluno_row.iloc[0].get('unidade_4', 0.0)))
                        else:
                            u1_l.append(0.0); u2_l.append(0.0); u3_l.append(0.0); u4_l.append(0.0)

                    df_notas = pd.DataFrame({"ALUNO": lista_alunos_notas, "I Unidade": u1_l, "II Unidade": u2_l, "III Unidade": u3_l, "IV Unidade": u4_l})
                    df_editado = st.data_editor(df_notas, hide_index=True, use_container_width=True, column_config={"ALUNO": st.column_config.TextColumn(disabled=True), "I Unidade": st.column_config.NumberColumn(min_value=0.0, max_value=10.0, format="%.1f"), "II Unidade": st.column_config.NumberColumn(min_value=0.0, max_value=10.0, format="%.1f"), "III Unidade": st.column_config.NumberColumn(min_value=0.0, max_value=10.0, format="%.1f"), "IV Unidade": st.column_config.NumberColumn(min_value=0.0, max_value=10.0, format="%.1f")})
                    
                    df_resultado = df_editado.copy()
                    df_resultado["MÉDIA FINAL"] = df_resultado[["I Unidade", "II Unidade", "III Unidade", "IV Unidade"]].sum(axis=1) / 4
                    df_resultado["MÉDIA FINAL"] = df_resultado["MÉDIA FINAL"].round(1)
                    df_resultado["SITUAÇÃO"] = df_resultado["MÉDIA FINAL"].apply(lambda m: "🟢 APROVADO" if m >= 7.0 else ("🟡 EM ANDAMENTO/RECUPERAÇÃO" if m > 0.0 else "⚪ PENDENTE"))
                    
                    st.dataframe(df_resultado[["ALUNO", "MÉDIA FINAL", "SITUAÇÃO"]], hide_index=True, use_container_width=True)
                
                else:
                    u1_c, u2_c, u3_c, u4_c = [], [], [], []
                    opcoes_conceito = ["-", "Ótimo", "Bom", "Regular"]
                    for aluno in lista_alunos_notas:
                        aluno_row = df_contexto[df_contexto['aluno'].astype(str).str.strip() == aluno] if not df_contexto.empty else pd.DataFrame()
                        if not aluno_row.empty:
                            def safe_conc(v): return v if v in opcoes_conceito else "-"
                            u1_c.append(safe_conc(aluno_row.iloc[0].get('unidade_1', '-')))
                            u2_c.append(safe_conc(aluno_row.iloc[0].get('unidade_2', '-')))
                            u3_c.append(safe_conc(aluno_row.iloc[0].get('unidade_3', '-')))
                            u4_c.append(safe_conc(aluno_row.iloc[0].get('unidade_4', '-')))
                        else:
                            u1_c.append("-"); u2_c.append("-"); u3_c.append("-"); u4_c.append("-")

                    df_notas = pd.DataFrame({"ALUNO": lista_alunos_notas, "I Unidade": u1_c, "II Unidade": u2_c, "III Unidade": u3_c, "IV Unidade": u4_c})
                    df_editado = st.data_editor(df_notas, hide_index=True, use_container_width=True, column_config={"ALUNO": st.column_config.TextColumn(disabled=True), "I Unidade": st.column_config.SelectboxColumn("I Unidade", options=opcoes_conceito, required=True), "II Unidade": st.column_config.SelectboxColumn("II Unidade", options=opcoes_conceito, required=True), "III Unidade": st.column_config.SelectboxColumn("III Unidade", options=opcoes_conceito, required=True), "IV Unidade": st.column_config.SelectboxColumn("IV Unidade", options=opcoes_conceito, required=True)})
                    
                    df_resultado = df_editado.copy()
                    df_resultado["MÉDIA FINAL"] = "-" 
                    def calc_situacao(row):
                        ultimo_conc = row["IV Unidade"] if row["IV Unidade"] != "-" else (row["III Unidade"] if row["III Unidade"] != "-" else (row["II Unidade"] if row["II Unidade"] != "-" else row["I Unidade"]))
                        return "🟢 APROVADO" if ultimo_conc in ["Ótimo", "Bom"] else ("🟡 ATENÇÃO" if ultimo_conc == "Regular" else "⚪ PENDENTE")
                    
                    df_resultado["SITUAÇÃO"] = df_resultado.apply(calc_situacao, axis=1)
                    st.markdown("#### Resumo da Situação Atual")
                    st.dataframe(df_resultado[["ALUNO", "SITUAÇÃO"]], hide_index=True, use_container_width=True)

                if st.button("💾 Salvar Diário de Notas no Banco de Dados", type="primary", use_container_width=True):
                    with st.spinner("Sincronizando registros..."):
                        if salvar_notas_bd(st.session_state.ctx_turma, st.session_state.ctx_disc, df_resultado): st.success("✅ Diário atualizado com sucesso!")

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


