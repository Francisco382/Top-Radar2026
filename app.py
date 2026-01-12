import streamlit as st
import pandas as pd
import sqlite3
import io
from datetime import datetime, timedelta


# 1. CONFIGURAÇÃO DA PÁGINA E ESTILO CLARO
st.set_page_config(page_title="Top-Radar", layout="wide")

# CSS para deixar os botões vermelhos (Padrão Claro)
st.markdown("""
    <style>
    .stButton>button {
        background-color: #EE2D24;
        color: white;
        border-radius: 5px;
    }
    .stButton>button:hover {
        background-color: #C1241D;
        color: white;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. FUNÇÕES DE SUPORTE
def criar_banco():
    conn = sqlite3.connect('top_radar.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tabulacoes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, vendedor TEXT, tipo TEXT, 
                  documento TEXT, produto TEXT, motivo TEXT, data_registro TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS clientes 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, endereco TEXT, bairro TEXT,
                  possui_bl TEXT, possui_tv TEXT, possui_mv TEXT,
                  aprova_fixa TEXT, aprova_movel TEXT)''')
    conn.commit()
    conn.close()

def salvar_tabulacao(vendedor, tipo, documento="", produto="", motivo=""):
    conn = sqlite3.connect('top_radar.db')
    c = conn.cursor()
    data_atual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    c.execute("INSERT INTO tabulacoes (vendedor, tipo, documento, produto, motivo, data_registro) VALUES (?, ?, ?, ?, ?, ?)",
              (vendedor, tipo, documento, produto, motivo, data_atual))
    conn.commit()
    conn.close()

def importar_planilha_para_db(arquivo):
    conn = sqlite3.connect('top_radar.db')
    df_import = pd.read_csv(arquivo) if arquivo.name.endswith('.csv') else pd.read_excel(arquivo)
    df_import.to_sql('clientes', conn, if_exists='replace', index=False)
    conn.close()
    return len(df_import)

def buscar_enderecos(termo, filtro_tipo=None):
    conn = sqlite3.connect('top_radar.db')
    query = f"SELECT * FROM clientes WHERE endereco LIKE '%{termo}%' OR bairro LIKE '%{termo}%'"
    df = pd.read_sql(query, conn)
    if filtro_tipo == "Sem BL": df = df[df['possui_bl'].astype(str).str.upper() == 'NÃO']
    elif filtro_tipo == "Sem MV": df = df[df['possui_mv'].astype(str).str.upper() == 'NÃO']
    elif filtro_tipo == "Aprova Fixa": df = df[df['aprova_fixa'].astype(str).str.upper() == 'SIM']
    elif filtro_tipo == "Aprova Móvel": df = df[df['aprova_movel'].astype(str).str.upper() == 'SIM']
    conn.close()
    return df

criar_banco()

# 3. CONTROLE DE ACESSO
if 'logado' not in st.session_state: st.session_state.logado = False

if not st.session_state.logado:
    st.title("🚀 Top-Radar 2026 - Login")
    email = st.text_input("E-mail")
    senha = st.text_input("Senha", type="password")
    if st.button("Acessar"):
        if email.endswith("@claro.com.br") and senha == "123":
            st.session_state.logado, st.session_state.vendedor_email = True, email
            st.rerun()
        else: st.error("Dados inválidos.")
else:
    # SIDEBAR COM LOGO
    st.sidebar.image("https://upload.wikimedia.org/wikipedia/commons/e/e9/Claro_logo.svg", width=100)
    pagina = st.sidebar.radio("Navegar para:", ["Localização", "Consulta Endereço", "Tabulação", "Relatórios", "Administrador"])
    if st.sidebar.button("Sair"):
        st.session_state.logado = False
        st.rerun()

    # --- TELA: LOCALIZAÇÃO ---
    if pagina == "Localização":
        st.header("📍 Localização e Carteira")
        st.map(pd.DataFrame({'lat': [-23.55], 'lon': [-46.63]}))
        st.success("Mapa carregado.")

    # --- TELA: CONSULTA ENDEREÇO ---
    elif pagina == "Consulta Endereço":
        st.header("🔍 Consulta de Endereços")
        busca = st.text_input("Pesquisar endereço...")
        col_f = st.columns(4)
        filtro = "Sem BL" if col_f[0].button("Sem BL") else "Sem MV" if col_f[1].button("Sem MV") else "Aprova Fixa" if col_f[2].button("Aprova Fixa") else "Aprova Móvel" if col_f[3].button("Aprova Móvel") else None
        res = buscar_enderecos(busca, filtro)
        for _, row in res.iterrows():
            with st.expander(f"🏠 {row['endereco']}"):
                st.write(f"BL: {row['possui_bl']} | TV: {row['possui_tv']} | MV: {row['possui_mv']}")

    # --- TELA: TABULAÇÃO ---
    elif pagina == "Tabulação":
        st.header("📝 Tabulação de Visita")
        tipo = st.selectbox("Resultado", ["Venda", "Não Venda", "Agendamento"])
        if tipo == "Venda":
            prod = st.selectbox("Produto", ["Dados", "Dados + Voz", "Dados + Voz + TV"])
            doc = st.text_input("CPF/CNPJ")
            if st.button("Salvar Venda"):
                salvar_tabulacao(st.session_state.vendedor_email, "Venda", documento=doc, produto=prod)
                st.success("Venda Salva!")
        elif tipo == "Não Venda":
            mot = st.selectbox("Motivo", ["Sem interesse", "Casa Vazia", "Concorrência"])
            if st.button("Salvar"):
                salvar_tabulacao(st.session_state.vendedor_email, "Não Venda", motivo=mot)
                st.warning("Registrado.")
        elif tipo == "Agendamento":
            d, h = st.date_input("Data"), st.time_input("Hora")
            if st.button("Agendar"):
                salvar_tabulacao(st.session_state.vendedor_email, "Agendamento", motivo=f"{d} {h}")
                st.success("Agendado!")


    # --- TELA: RELATÓRIOS ---
    elif pagina == "Relatórios":
        # OPÇÃO A: Se você quer usar o código que JÁ ESTÁ aqui no app.py:
        st.header("📊 Painel de Performance")
        conn = sqlite3.connect('top_radar.db')
        df = pd.read_sql("SELECT * FROM tabulacoes", conn)
        conn.close()
        
        if not df.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Vendas", len(df[df['tipo']=='Venda']))
            c2.metric("Não Vendas", len(df[df['tipo']=='Não Venda']))
            c3.metric("Agendamentos", len(df[df['tipo']=='Agendamento']))
            
            st.subheader("Mix de Vendas")
            st.bar_chart(df[df['tipo']=='Venda']['produto'].value_counts())
            
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False)
            st.download_button("📥 Baixar Relatório Excel", output.getvalue(), "relatorio.xlsx")
        else: 
            st.info("Sem dados.")
            
  
    # --- TELA: ADMINISTRADOR ---
    elif pagina == "Administrador":
        st.header("⚙️ Painel Administrativo")
        up = st.file_uploader("Suba a planilha", type=["csv", "xlsx"])
        if st.button("Atualizar Base"):
            if up: st.success(f"{importar_planilha_para_db(up)} endereços carregados!")

# FIM DO ARQUIVO (Não coloque nada depois do último elif)