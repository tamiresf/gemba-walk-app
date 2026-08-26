import uuid
import datetime
from datetime import datetime
import time
import requests
import pandas as pd
import streamlit as st
import plotly.express as px

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Gestão Gemba & Rotinas",
    page_icon="📋",
    layout="wide"
)

# -----------------------------------------------------------------------------
# CONSTANTES E CONFIGURAÇÕES DE WEBHOOKS
# -----------------------------------------------------------------------------
# Substitua pelas suas URLs reais de Webhook (Make/n8n/Power Automate/SharePoint)
WEBHOOK_CARREGAR_DADOS = ""  # URL para ler inspeções
WEBHOOK_CARREGAR_ROTINAS = ""  # URL para ler rotinas
WEBHOOK_SALVAR_INSPECAO = ""  # URL para criar inspeção
WEBHOOK_ROTINAS_CRIAR = ""  # URL para criar rotina
WEBHOOK_ROTINAS_EXCLUIR = ""  # URL para excluir rotina

AUDITORES_GESTORES = [
    "Carlos Silva",
    "Ana Souza",
    "Roberto Lima",
    "Mariana Costa"
]

EMAILS_CORPORATIVOS = [
    "carlos.silva@empresa.com",
    "ana.souza@empresa.com",
    "roberto.lima@empresa.com",
    "mariana.costa@empresa.com"
]

DIAS_SEMANA = [
    "Segunda-feira",
    "Terça-feira",
    "Quarta-feira",
    "Quinta-feira",
    "Sexta-feira",
    "Sábado",
    "Domingo"
]

CATEGORIAS = {
    "5S / Organização": ["Bancadas limpas e organizadas?", "Ferramentas no local correto?", "Descarte adequado de resíduos?"],
    "Segurança (EPI/EPC)": ["Uso obrigatório de EPIs?", "Extintores desobstruídos?", "Saídas de emergência sinalizadas?"],
    "Qualidade & Processo": ["Instruções de trabalho visíveis?", "Identificação de peças/lotes?", "Calibração dos instrumentos em dia?"],
    "Manutenção Preventiva": ["Vazamentos de óleo/ar visíveis?", "Ruídos anormais nos equipamentos?", "Proteções físicas presentes?"]
}

# -----------------------------------------------------------------------------
# FUNÇÕES DE CARREGAMENTO DE DADOS (COM CACHE)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=60)
def carregar_dados_inspecoes():
    """Busca o histórico de inspeções cadastradas."""
    if not WEBHOOK_CARREGAR_DADOS:
        return pd.DataFrame()
    try:
        response = requests.get(WEBHOOK_CARREGAR_DADOS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Erro ao carregar inspeções: {e}")
    return pd.DataFrame()

@st.cache_data(ttl=60)
def carregar_dados_rotinas():
    """Busca a lista de rotinas agendadas."""
    if not WEBHOOK_CARREGAR_ROTINAS:
        return pd.DataFrame()
    try:
        response = requests.get(WEBHOOK_CARREGAR_ROTINAS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Erro ao carregar rotinas: {e}")
    return pd.DataFrame()

df_dados = carregar_dados_inspecoes()
df_rotinas = carregar_dados_rotinas()

# -----------------------------------------------------------------------------
# INTERFACE PRINCIPAL
# -----------------------------------------------------------------------------
st.title("📋 Sistema de Inspeções Gemba & Rotinas")
st.markdown("Acompanhamento contínuo de auditorias, segurança e manutenção na fábrica.")

aba1, aba2, aba3 = st.tabs([
    "📝 Nova Inspeção", 
    "📊 Dashboard & Histórico", 
    "📅 Rotinas Programadas"
])

# =============================================================================
# ABA 1: NOVA INSPEÇÃO GEMBA
# =============================================================================
with aba1:
    st.subheader("Registrar Inspeção no Gemba")
    
    with st.form("form_nova_inspecao", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            auditor = st.selectbox("Auditor / Responsável*", options=AUDITORES_GESTORES, index=None)
            setor = st.text_input("Setor / Estação de Trabalho*", placeholder="Ex: Linha de Montagem 01")
        with col2:
            categoria_sel = st.selectbox("Categoria de Auditoria*", options=list(CATEGORIAS.keys()))
            data_inspecao = st.date_input("Data da Inspeção*", value=datetime.now())

        st.markdown("### Checklists de Verificação")
        perguntas = CATEGORIAS.get(categoria_sel, [])
        respostas = {}
        
        for idx, pergunta in enumerate(perguntas):
            respostas[f"pergunta_{idx}"] = {
                "pergunta": pergunta,
                "status": st.radio(f"{pergunta}", ["Conforme", "Não Conforme", "N/A"], key=f"p_{idx}", horizontal=True)
            }
        
        observacoes = st.text_area("Observações / Ações Imediatas", placeholder="Descreva os achados importantes...")
        
        btn_salvar_inspecao = st.form_submit_button("Salvar Inspeção", type="primary")

        if btn_salvar_inspecao:
            if not auditor or not setor:
                st.error("Preencha todos os campos obrigatórios (*).")
            else:
                payload_inspecao = {
                    "id": str(uuid.uuid4())[:8],
                    "auditor": auditor,
                    "setor": setor,
                    "categoria": categoria_sel,
                    "data": str(data_inspecao),
                    "observacoes": observacoes,
                    "detalhes": respostas
                }

                sucesso = False
                if WEBHOOK_SALVAR_INSPECAO:
                    try:
                        with st.spinner("Enviando dados da inspeção..."):
                            res = requests.post(WEBHOOK_SALVAR_INSPECAO, json=payload_inspecao, timeout=12)
                            if res.status_code in [200, 201, 202, 204]:
                                sucesso = True
                            else:
                                st.error(f"Erro no servidor: {res.status_code}")
                    except Exception as e:
                        st.error(f"Falha de conexão: {e}")
                else:
                    # Modo Simulação/Sem Webhook
                    sucesso = True

                if sucesso:
                    st.cache_data.clear()
                    st.toast("Inspeção gravada com sucesso!", icon="✅")
                    time.sleep(1)
                    st.rerun()

# =============================================================================
# ABA 2: DASHBOARD & HISTÓRICO
# =============================================================================
with aba2:
    st.subheader("Histórico e Indicadores Gemba")
    
    if df_dados.empty:
        st.info("Nenhum dado de inspeção encontrado.")
    else:
        # Filtros Globais no Dashboard
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            filtro_auditor = st.multiselect("Filtrar por Auditor", options=df_dados["auditor"].unique() if "auditor" in df_dados.columns else [])
        with col_f2:
            filtro_cat = st.multiselect("Filtrar por Categoria", options=df_dados["categoria"].unique() if "categoria" in df_dados.columns else [])

        df_filtrado = df_dados.copy()
        if filtro_auditor and "auditor" in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["auditor"].isin(filtro_auditor)]
        if filtro_cat and "categoria" in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado["categoria"].isin(filtro_cat)]

        # KPIs
        st.markdown("---")
        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Total de Inspeções", len(df_filtrado))
        kpi2.metric("Auditores Ativos", df_filtrado["auditor"].nunique() if "auditor" in df_filtrado.columns else 0)
        kpi3.metric("Setores Auditados", df_filtrado["setor"].nunique() if "setor" in df_filtrado.columns else 0)

        # Gráfico
        if "categoria" in df_filtrado.columns:
            fig = px.bar(
                df_filtrado["categoria"].value_counts().reset_index(),
                x="categoria",
                y="count",
                labels={"categoria": "Categoria", "count": "Quantidade"},
                title="Volume de Inspeções por Categoria",
                color="categoria"
            )
            st.plotly_chart(fig, use_container_width=True)

        # Tabela completa
        st.markdown("### Dados Brutos")
        st.dataframe(df_filtrado, use_container_width=True)

# =============================================================================
# ABA 3: ROTINAS PROGRAMADAS
# =============================================================================
with aba3:
    st.subheader("📅 Programação de Rotinas Gemba")
    st.write("Agende inspeções recorrentes e acompanhe a realização semanal.")

    # Form de Cadastro de Rotina
    with st.expander("➕ Cadastrar Nova Rotina Programada", expanded=False):
        with st.form("form_nova_rotina", clear_on_submit=True):
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                rotina_pessoa = st.selectbox("Responsável pela Rotina*", options=AUDITORES_GESTORES, index=None)
                rotina_email = st.selectbox("E-mail para Notificação*", options=EMAILS_CORPORATIVOS, index=None)
            with col_r2:
                rotina_dia = st.selectbox("Dia da Semana Fixo*", options=DIAS_SEMANA)
                rotina_categoria = st.selectbox("Categoria da Inspeção*", options=list(CATEGORIAS.keys()))

            rotina_estacao = st.text_input("Setor / Área a ser Inspecionada*", placeholder="Ex: Linha de Montagem 02")
            rotina_obs = st.text_area("Objetivo / Instruções adicionais", placeholder="Ex: Verificar uso correto de EPIs")

            btn_salvar_rotina = st.form_submit_button("Agendar Rotina", type="primary")

            if btn_salvar_rotina:
                if not rotina_pessoa or not rotina_email or not rotina_estacao:
                    st.error("Preencha todos os campos obrigatórios (*).")
                else:
                    id_rotina = str(uuid.uuid4())[:8]
                    payload_rotina = {
                        "id0": id_rotina,
                        "id": id_rotina,
                        "ID": id_rotina,
                        "responsavel_nome": str(rotina_pessoa),
                        "responsavel_email": str(rotina_email),
                        "dia_semana": str(rotina_dia),
                        "categoria": str(rotina_categoria),
                        "estacao": str(rotina_estacao),
                        "instrucoes": str(rotina_obs),
                        "data_cadastro": datetime.now().strftime("%Y-%m-%d"),
                    }

                    sucesso = False
                    if WEBHOOK_ROTINAS_CRIAR:
                        try:
                            with st.spinner("Agendando rotina no servidor..."):
                                res_rot = requests.post(WEBHOOK_ROTINAS_CRIAR, json=payload_rotina, timeout=12)
                                if res_rot.status_code in [200, 201, 202, 204]:
                                    sucesso = True
                                else:
                                    st.error(f"Erro no servidor ({res_rot.status_code}): {res_rot.text}")
                        except Exception as e:
                            st.error(f"Falha ao conectar com o webhook: {e}")
                    else:
                        st.error("URL do webhook de criação de rotinas não configurada.")

                    if sucesso:
                        st.cache_data.clear()
                        st.toast("Rotina agendada com sucesso!", icon="✅")
                        time.sleep(1)
                        st.rerun()

    st.divider()
    st.markdown("### 🟦 Quadro de Rotinas Ativas")

    df_rot_exibir = df_rotinas.copy()

    if df_rot_exibir.empty:
        st.info("Nenhuma rotina cadastrada ainda ou o servidor não retornou dados.")
    else:
        semana_atual = datetime.now().isocalendar()[1]
        ano_atual = datetime.now().year

        cols_r = st.columns(2)
        for idx_r, (r_idx, row_r) in enumerate(df_rot_exibir.iterrows()):
            # Chaves flexíveis para tratar variações do backend
            id_sp_val = str(row_r.get("ID", row_r.get("id", row_r.get("id0", r_idx))))
            id0_rot = str(row_r.get("id0", id_sp_val))

            nome_resp = str(row_r.get("responsavel_nome", row_r.get("responsavel", "N/A")))
            email_resp = str(row_r.get("responsavel_email", "Não informado"))
            dia_semana_rot = str(row_r.get("dia_semana", "N/A"))
            cat_rot = str(row_r.get("categoria", "N/A"))
            estacao_rot = str(row_r.get("estacao", "N/A"))
            instrucoes_rot = str(row_r.get("instrucoes", ""))

            # Validação se a rotina foi realizada nesta semana corrente
            executou_semana = False
            if not df_dados.empty:
                col_auditor = next((c for c in df_dados.columns if "auditor" in c.lower() or "responsavel" in c.lower()), None)
                col_data = next((c for c in df_dados.columns if "data" in c.lower() or "created" in c.lower()), None)

                if col_auditor and col_data:
                    datas_convertidas = pd.to_datetime(df_dados[col_data], errors="coerce")
                    filtro = (
                        (df_dados[col_auditor].astype(str).str.strip().str.lower() == nome_resp.strip().lower())
                        & (datas_convertidas.dt.isocalendar().week == semana_atual)
                        & (datas_convertidas.dt.year == ano_atual)
                    )
                    executou_semana = filtro.any()

            with cols_r[idx_r % 2]:
                with st.container(border=True):
                    col_tit, col_del = st.columns([0.85, 0.15])
                    with col_tit:
                        st.markdown(f"### 📅 {dia_semana_rot} - {cat_rot}")
                    with col_del:
                        if st.button("🗑️", key=f"btn_del_rot_{id_sp_val}_{idx_r}", help="Excluir esta rotina"):
                            st.session_state[f"confirm_delete_{id_sp_val}"] = True
                            st.rerun()

                    # Lógica de confirmação de exclusão
                    if st.session_state.get(f"confirm_delete_{id_sp_val}", False):
                        st.warning("⚠️ Deseja excluir esta rotina permanentemente?")
                        col_c1, col_c2 = st.columns(2)

                        with col_c1:
                            if st.button("Sim, Excluir", key=f"sim_del_{id_sp_val}_{idx_r}", type="primary"):
                                try:
                                    parsed_id = int(id_sp_val) if id_sp_val.isdigit() else id_sp_val
                                except ValueError:
                                    parsed_id = id_sp_val

                                payload_excluir = {
                                    "ID": parsed_id,
                                    "id": id_sp_val,
                                    "id0": id0_rot,
                                }

                                if WEBHOOK_ROTINAS_EXCLUIR:
                                    try:
                                        with st.spinner("Excluindo no servidor..."):
                                            res_del = requests.post(WEBHOOK_ROTINAS_EXCLUIR, json=payload_excluir, timeout=12)
                                            if res_del.status_code in [200, 202, 204]:
                                                st.session_state.pop(f"confirm_delete_{id_sp_val}", None)
                                                st.cache_data.clear()
                                                st.toast("Rotina excluída com sucesso!", icon="🗑️")
                                                time.sleep(1)
                                                st.rerun()
                                            else:
                                                st.error(f"Erro ao excluir no servidor: {res_del.status_code}")
                                    except Exception as e:
                                        st.error(f"Erro de conexão ao excluir: {e}")
                                else:
                                    st.error("Webhook de exclusão não configurado.")

                        with col_c2:
                            if st.button("Cancelar", key=f"cancel_del_{id_sp_val}_{idx_r}"):
                                st.session_state.pop(f"confirm_delete_{id_sp_val}", None)
                                st.rerun()

                    st.write(f"👤 **Responsável pela Rotina:** {nome_resp}")
                    st.write(f"📧 **E-mail para Notificação:** {email_resp}")
                    st.write(f"🏢 **Setor / Área:** {estacao_rot}")
                    st.write(f"📆 **Dia Fixo:** {dia_semana_rot}")
                    st.write(f"🏷️ **Categoria:** {cat_rot}")

                    if instrucoes_rot and instrucoes_rot.strip() not in ["", "None", "NONE"]:
                        st.caption(f"📝 **Instruções:** {instrucoes_rot}")

                    if executou_semana:
                        st.success("✅ Rotina Realizada esta Semana!")
                    else:
                        st.warning("⚠️ Pendente de Realização esta Semana")
