import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date
import uuid

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Gemba Walk Digital",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CARREGAR URLs DOS SECRETS (URLs Corrigidas) ---
WEBHOOK_CRIAR = st.secrets.get(
    "POWER_AUTOMATE_CRIAR_URL", 
    "https://defaultcd14821755e24b4e86f837f80bf5ae.f3.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/06/workflows/a1df9787e2b94d19ab5643e165491bc8/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=yLF9HKRO6XtG75qHGA_U7X1g-NMCcnT4QHGXPdUkiFA"
)

# ATENÇÃO: Garanta que esta URL tenha a assinatura (&sig=...) igual à de criação
WEBHOOK_RESOLVER = st.secrets.get(
    "POWER_AUTOMATE_RESOLVER_URL", 
    "https://defaultcd14821755e24b4e86f837f80bf5ae.f3.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/08/workflows/24e560b839864d9b91720231dbb6584e/triggers/manual/paths/invoke?api-version=1"
)

# CORREÇÃO: Substituído o segundo '?' por '&download=1'
EXCEL_READ_URL = st.secrets.get(
    "EXCEL_READ_URL", 
    "https://mustad365-my.sharepoint.com/:x:/g/personal/tamires_santos_mustad_com/IQA3ok4bdtHdTZJmv3peAXnDAWwLIWJPfODXehQOxxdKAYY?e=T3wWP9&download=1"
)

CATEGORIAS = {
    "Segurança": "EPIs, máquinas, proteções, riscos, circulação",
    "Qualidade": "Dimensões, formato, acabamento, defeitos",
    "Processo": "Sequência correta, parâmetros, padrão operacional",
    "Máquinas": "Condições, anomalias, vazamentos, ruídos",
    "Materiais": "Aço correto, identificação, armazenamento",
    "5S": "Organização, limpeza, identificação",
    "Produtividade": "Paradas, gargalos, retrabalho, espera",
    "Pessoas": "Dificuldades encontradas pelos operadores",
    "Meio ambiente": "Resíduos, sucata, descarte, organização"
}

# --- FUNÇÃO PARA CARREGAR DADOS DO SHAREPOINT ---
@st.cache_data(ttl=5)
def carregar_dados():
    if EXCEL_READ_URL:
        try:
            df = pd.read_excel(EXCEL_READ_URL)
            # Remove espaços em branco dos nomes das colunas
            df.columns = df.columns.str.strip().str.lower()
            return df
        except Exception as e:
            st.error(f"Erro ao ler a planilha Excel: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

# --- INTERFACE PRINCIPAL ---
st.title("🔍 Gemba Walk Digital")
aba1, aba2, aba3 = st.tabs(["📋 Novo Registro", "📌 Quadro de Post-its", "📊 Dashboard"])

# --- ABA 1: NOVO REGISTRO ---
with aba1:
    st.subheader("Informações Gerais")
    col1, col2 = st.columns(2)
    with col1:
        auditor = st.text_input("Nome do Auditor/Gestor*")
    with col2:
        estacao = st.text_input("Área / Estação*")
    
    categoria_sel = st.selectbox("Selecione a Categoria", list(CATEGORIAS.keys()))
    st.info(f"💡 **O que observar:** {CATEGORIAS[categoria_sel]}")
    
    status_op = st.radio("Status da Inspeção", ["Conforme", "Não Conforme"], horizontal=True)
    
    if status_op == "Não Conforme":
        with st.form("form_nc", clear_on_submit=True):
            st.warning("Preencha os detalhes da Não Conformidade:")
            
            problema = st.text_area("Qual foi o problema?*")
            local = st.text_input("Onde ocorreu?*")
            impacto = st.text_area("Qual o impacto?")
            causa = st.text_area("Causa aparente?")
            acao_imediata = st.text_area("Ação imediata?")
            responsavel_email = st.text_input("E-mail do Responsável*")
            prazo = st.date_input("Prazo para Solução", value=date.today())
            
            submitted = st.form_submit_button("Salvar Não Conformidade")
            
            if submitted:
                if not auditor or not estacao or not problema or not responsavel_email:
                    st.error("Preencha todos os campos obrigatórios (*).")
                else:
                    id_unico = str(uuid.uuid4())[:8]
                    
                    payload = {
                        "id": str(id_unico),
                        "auditor": str(auditor),
                        "data_criacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "estacao": str(estacao),
                        "categoria": str(categoria_sel),
                        "problema": str(problema),
                        "local": str(local),
                        "impacto": str(impacto),
                        "causa": str(causa),
                        "acao_imediata": str(acao_imediata),
                        "responsavel": str(responsavel_email),
                        "prazo": prazo.strftime("%Y-%m-%d"),
                        "status": "Pendente",
                        "data_solucao": ""
                    }
                    
                    try:
                        res = requests.post(WEBHOOK_CRIAR, json=payload)
                        if res.status_code in [200, 202]:
                            st.success("Não conformidade salva com sucesso no Excel do SharePoint!")
                            st.cache_data.clear()
                        else:
                            st.error(f"Erro no Power Automate (Código {res.status_code}): {res.text}")
                    except Exception as e:
                        st.error(f"Falha de conexão com o Power Automate: {e}")
    else:
        if st.button("Salvar Conformidade"):
            st.success("Conformidade registrada com sucesso!")

# --- ABA 2: QUADRO DE POST-ITS ---
with aba2:
    st.subheader("📌 Pendências Ativas (Post-its)")
    df_dados = carregar_dados()
    
    if df_dados.empty or "status" not in df_dados.columns:
        st.info("Nenhuma pendência encontrada ou aguardando sincronização com a planilha.")
    else:
        pendentes = df_dados[df_dados["status"].astype(str).str.strip().str.capitalize() == "Pendente"]
        
        if pendentes.empty:
            st.success("🎉 Nenhuma pendência aberta no momento!")
        else:
            cols = st.columns(2)
            for idx, row in pendentes.reset_index().iterrows():
                with cols[idx % 2]:
                    with st.container(border=True):
                        st.markdown(f"### 🟨 {row.get('categoria', 'N/A')}")
                        st.caption(f"**Criado por:** {row.get('auditor', 'N/A')} em {row.get('data_criacao', 'N/A')}")
                        st.write(f"**Local:** {row.get('estacao', '')} - {row.get('local', '')}")
                        st.write(f"**Problema:** {row.get('problema', '')}")
                        st.write(f"**Impacto:** {row.get('impacto', '')}")
                        st.write(f"**Causa Aparente:** {row.get('causa', '')}")
                        st.write(f"**Ação Imediata:** {row.get('acao_imediata', '')}")
                        st.write(f"**Responsável:** {row.get('responsavel', '')}")
                        st.write(f"**Prazo:** {row.get('prazo', '')}")
                        
                        if st.button("✅ Resolvido", key=f"btn_res_{row.get('id')}"):
                            payload_sol = {
                                "id": str(row.get('id')),
                                "data_solucao": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                            try:
                                res_sol = requests.post(WEBHOOK_RESOLVER, json=payload_sol)
                                if res_sol.status_code in [200, 202]:
                                    st.success("Item resolvido e atualizado no Excel!")
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error(f"Erro ao atualizar status: {res_sol.status_code}")
                            except Exception as e:
                                st.error(f"Falha de conexão: {e}")

# --- ABA 3: DASHBOARD ---
with aba3:
    st.subheader("📊 Indicadores do Gemba Walk")
    df_dados = carregar_dados()
    
    if not df_dados.empty and "status" in df_dados.columns:
        c1, c2, c3 = st.columns(3)
        c1.metric("Total de Registros", len(df_dados))
        c2.metric("Pendentes", len(df_dados[df_dados['status'].astype(str).str.strip().str.capitalize() == 'Pendente']))
        c3.metric("Resolvidos", len(df_dados[df_dados['status'].astype(str).str.strip().str.capitalize() == 'Resolvido']))
        
        st.divider()
        st.markdown("**Problemas Encontrados por Categoria**")
        if 'categoria' in df_dados.columns:
            st.bar_chart(df_dados['categoria'].value_counts())
        
        st.subheader("📋 Tabela Geral de Dados")
        st.dataframe(df_dados)
    else:
        st.info("Aguardando registros para exibir indicadores.")
