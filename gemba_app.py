from datetime import datetime, date
import uuid
import pandas as pd
import requests
import streamlit as st

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Gemba Walk Digital",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- 2. CARREGAR URLs DOS SECRETS ---
WEBHOOK_CRIAR = st.secrets.get(
    "POWER_AUTOMATE_CRIAR_URL",
    "https://defaultcd14821755e24b4e86f837f80bf5ae.f3.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/08/workflows/24e560b839864d9b91720231dbb6584e/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=cZEo_aNlKwbk9kP84Yu_OITxnl6wZqrM-RCGjOZXzss",
)

WEBHOOK_RESOLVER = st.secrets.get(
    "POWER_AUTOMATE_RESOLVER_URL",
    "https://defaultcd14821755e24b4e86f837f80bf5ae.f3.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/06/workflows/a1df9787e2b94d19ab5643e165491bc8/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=yLF9HKRO6XtG75qHGA_U7X1g-NMCcnT4QHGXPdUkiFA",
)

WEBHOOK_LER = st.secrets.get(
    "POWER_AUTOMATE_LER_URL",
    "https://defaultcd14821755e24b4e86f837f80bf5ae.f3.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/27/workflows/62a264c57b214336aa6205ae2fb47c59/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=JJ2EZPMarOKgpxHQNzHh0ZR7N5LKtQ53eEO1wB-eePM",
)

# --- 3. CATEGORIAS DA INSPEÇÃO ---
CATEGORIAS = {
    "Segurança": "EPIs, máquinas, proteções, riscos, circulação",
    "Qualidade": "Dimensões, formato, acabamento, defeitos",
    "Processo": "Sequência correta, parâmetros, padrão operacional",
    "Máquinas": "Condições, anomalias, vazamentos, ruídos",
    "Materiais": "Aço correto, identificação, armazenamento",
    "5S": "Organização, limpeza, identificação",
    "Produtividade": "Paradas, gargalos, retrabalho, espera",
    "Pessoas": "Dificuldades encontradas pelos operadores",
    "Meio ambiente": "Resíduos, sucata, descarte, organização",
}


# --- 4. FUNÇÃO PARA CARREGAR DADOS E E-MAILS DO POWER AUTOMATE ---
@st.cache_data(ttl=10, show_spinner=False)
def carregar_dados_e_usuarios():
    try:
        res = requests.get(WEBHOOK_LER, timeout=10)
        if res.status_code == 200:
            dados_json = res.json()

            df_dados = pd.DataFrame()
            usuarios = []

            if isinstance(dados_json, dict):
                if "dados" in dados_json:
                    df_dados = pd.DataFrame(dados_json.get("dados", []))
                elif "value" in dados_json:
                    df_dados = pd.DataFrame(dados_json.get("value", []))

                for chave_usr in ["usuarios", "users", "emails", "value"]:
                    if chave_usr in dados_json and isinstance(
                        dados_json[chave_usr], list
                    ):
                        usuarios = dados_json[chave_usr]
                        break
            elif isinstance(dados_json, list):
                df_dados = pd.DataFrame(dados_json)
                usuarios = dados_json

            if not df_dados.empty:
                df_dados.columns = df_dados.columns.str.strip().str.lower()

            emails = []
            if isinstance(usuarios, list):
                for u in usuarios:
                    if isinstance(u, dict):
                        for k, v in u.items():
                            if v and isinstance(v, str) and "@" in v:
                                emails.append(v.lower().strip())
                    elif isinstance(u, str) and "@" in u:
                        emails.append(u.lower().strip())

            emails_unicos = sorted(list(set(emails)))

            return df_dados, emails_unicos
        else:
            st.error(
                f"Erro ao buscar dados do Power Automate (Código {res.status_code})"
            )
            return pd.DataFrame(), []
    except Exception as e:
        st.error(f"Falha de conexão com o Power Automate: {e}")
        return pd.DataFrame(), []


# Obter registros e e-mails do backend
df_dados_raw, lista_emails_corporativos = carregar_dados_e_usuarios()
opcoes_emails = [""] + lista_emails_corporativos

# Inicializa ou sincroniza a base local do session_state
if (
    "df_dados" not in st.session_state
    or st.session_state.get("forcar_recarga", False)
):
    st.session_state["df_dados"] = df_dados_raw.copy()
    st.session_state["forcar_recarga"] = False

df_dados = st.session_state["df_dados"]

# --- DIAGNÓSTICO (Visível apenas na barra lateral recolhida) ---
with st.sidebar.expander("🛠️ Diagnóstico do Sistema"):
    st.write(f"**E-mails carregados:** {len(lista_emails_corporativos)}")
    if lista_emails_corporativos:
        st.caption(
            ", ".join(lista_emails_corporativos[:5])
            + ("..." if len(lista_emails_corporativos) > 5 else "")
        )

# --- 5. INTERFACE PRINCIPAL ---
st.title("🔍 Gemba Walk Digital")
aba1, aba2, aba3 = st.tabs(
    ["📋 Novo Registro", "📌 Quadro de Post-its", "📊 Dashboard"]
)

# --- ABA 1: NOVO REGISTRO ---
with aba1:
    st.subheader("Informações Gerais")
    col1, col2 = st.columns(2)
    with col1:
        auditor = st.text_input("Nome do Auditor/Gestor*")
    with col2:
        estacao = st.text_input("Área / Estação*")

    categoria_sel = st.selectbox(
        "Selecione a Categoria", list(CATEGORIAS.keys())
    )
    st.info(f"💡 **O que observar:** {CATEGORIAS[categoria_sel]}")

    status_op = st.radio(
        "Status da Inspeção", ["Conforme", "Não Conforme"], horizontal=True
    )

    if status_op == "Não Conforme":
        with st.form("form_nc", clear_on_submit=True):
            st.warning("Preencha os detalhes da Não Conformidade:")

            problema = st.text_area("Qual foi o problema?*")
            local = st.text_input("Onde ocorreu?*")
            impacto = st.text_area("Qual o impacto?")
            causa = st.text_area("Causa aparente?")
            acao_imediata = st.text_area("Ação imediata?")

            if lista_emails_corporativos:
                responsavel_email = st.selectbox(
                    "E-mail do Responsável*",
                    options=opcoes_emails,
                    help="Digite para filtrar o e-mail corporativo do colaborador.",
                )
            else:
                responsavel_email = st.text_input("E-mail do Responsável*")

            prazo = st.date_input("Prazo para Solução", value=date.today())

            submitted = st.form_submit_button("Salvar Não Conformidade")

            if submitted:
                if (
                    not auditor
                    or not estacao
                    or not problema
                    or not responsavel_email
                ):
                    st.error("Preencha todos os campos obrigatórios (*).")
                else:
                    id_unico = str(uuid.uuid4())[:8]

                    payload = {
                        "id": str(id_unico),
                        "auditor": str(auditor),
                        "data_criacao": datetime.now().strftime(
                            "%Y-%m-%d %H:%M:%S"
                        ),
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
                        "data_solucao": "",
                    }

                    try:
                        res = requests.post(WEBHOOK_CRIAR, json=payload)
                        if res.status_code in [200, 202]:
                            st.success(
                                "Não conformidade salva com sucesso no Microsoft Lists!"
                            )
                            st.cache_data.clear()
                            st.session_state["forcar_recarga"] = True
                            st.rerun()
                        else:
                            st.error(
                                f"Erro no Power Automate (Código {res.status_code}): {res.text}"
                            )
                    except Exception as e:
                        st.error(
                            f"Falha de conexão com o Power Automate: {e}"
                        )
    else:
        if st.button("Salvar Conformidade"):
            st.success("Conformidade registrada com sucesso!")

# --- ABA 2: QUADRO DE POST-ITS ---
with aba2:
    st.subheader("📌 Pendências Ativas (Post-its)")

    if df_dados.empty or "status" not in df_dados.columns:
        st.info(
            "Nenhuma pendência encontrada ou aguardando sincronização com a lista."
        )
    else:
        # Tratamento rigoroso da coluna de status
        df_dados["status_clean"] = (
            df_dados["status"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.capitalize()
        )

        pendentes = df_dados[df_dados["status_clean"] == "Pendente"]

        if pendentes.empty:
            st.success("🎉 Nenhuma pendência aberta no momento!")
        else:
            cols = st.columns(2)
            for idx, row in pendentes.reset_index().iterrows():
                item_id = str(row.get("id", ""))
                with cols[idx % 2]:
                    with st.container(border=True):
                        st.markdown(f"### 🟨 {row.get('categoria', 'N/A')}")
                        st.caption(
                            f"**Criado por:** {row.get('auditor', 'N/A')} em {row.get('data_criacao', 'N/A')}"
                        )
                        st.write(
                            f"**Local:** {row.get('estacao', '')} - {row.get('local', '')}"
                        )
                        st.write(f"**Problema:** {row.get('problema', '')}")
                        st.write(f"**Impacto:** {row.get('impacto', '')}")
                        st.write(f"**Causa Aparente:** {row.get('causa', '')}")
                        st.write(
                            f"**Ação Imediata:** {row.get('acao_imediata', '')}"
                        )
                        st.write(
                            f"**Responsável:** {row.get('responsavel', '')}"
                        )
                        st.write(f"**Prazo:** {row.get('prazo', '')}")

                        if st.button(
                            "✅ Resolvido", key=f"btn_res_{item_id}_{idx}"
                        ):
                            data_solucao_str = datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            )
                            payload_sol = {
                                "id": item_id,
                                "data_solucao": data_solucao_str,
                            }
                            try:
                                res_sol = requests.post(
                                    WEBHOOK_RESOLVER,
                                    json=payload_sol,
                                    timeout=10,
                                )
                                if res_sol.status_code in [200, 202]:
                                    # Atualização otimista imediata na memória da aplicação
                                    mask = (
                                        st.session_state["df_dados"][
                                            "id"
                                        ].astype(str)
                                        == item_id
                                    )
                                    st.session_state["df_dados"].loc[
                                        mask, "status"
                                    ] = "Resolvido"
                                    st.session_state["df_dados"].loc[
                                        mask, "data_solucao"
                                    ] = data_solucao_str

                                    st.toast("Item resolvido!", icon="✅")
                                    st.cache_data.clear()
                                    st.rerun()
                                else:
                                    st.error(
                                        f"Erro ao atualizar status no Power Automate: {res_sol.status_code}"
                                    )
                            except Exception as e:
                                st.error(f"Falha de conexão: {e}")

# --- ABA 3: DASHBOARD ---
with aba3:
    st.subheader("📊 Indicadores do Gemba Walk")

    if not df_dados.empty and "status" in df_dados.columns:
        status_serie = (
            df_dados["status"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.capitalize()
        )

        total_registros = len(df_dados)
        qtd_pendentes = (status_serie == "Pendente").sum()
        qtd_resolvidos = (status_serie == "Resolvido").sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("Total de Registros", total_registros)
        c2.metric("Pendentes", qtd_pendentes)
        c3.metric("Resolvidos", qtd_resolvidos)

        st.divider()
        st.markdown("**Problemas Encontrados por Categoria**")
        if "categoria" in df_dados.columns:
            st.bar_chart(df_dados["categoria"].value_counts())
    else:
        st.info("Aguardando registros para exibir indicadores.")
