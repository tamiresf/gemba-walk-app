from datetime import date, datetime
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

# --- 3. LISTA DE E-MAILS CORPORATIVOS ---
EMAILS_BRUTOS = [
    "jaqueline.silva@mustad.com",
    "geovane.valdevino@mustad.com",
    "gissele.nogueira@mustad.com",
    "yuri.fernandes@mustad.com",
    "felipe.possato@mustad.com",
    "henrique.borges@mustad.com",
    "jessica.brandao@mustad.com",
    "helen.esteves@mustad.com",
    "giovane.carvalho@mustad.com",
    "nelcir.junior@mustad.com",
    "hebert.murtha@mustad.com",
    "maicon.alves@mustad.com",
    "victor.cavadas@mustad.com",
    "william.sousa@mustad.com",
    "felipe.muniz@mustad.com",
    "tamires.santos@mustad.com",
]

LISTA_EMAILS_CORPORATIVOS = sorted(
    list(set(e.strip().lower() for e in EMAILS_BRUTOS))
)
OPCOES_EMAILS = [""] + LISTA_EMAILS_CORPORATIVOS

# --- 4. CATEGORIAS DA INSPEÇÃO ---
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


# --- 5. BUSCAR DADOS REAIS DO MICROSOFT LISTS ---
@st.cache_data(ttl=2, show_spinner=False)
def buscar_dados_lists():
    try:
        # Tenta requisição POST/GET dependendo do seu fluxo do Power Automate
        res = requests.get(WEBHOOK_LER, timeout=10)
        if res.status_code != 200:
            res = requests.post(WEBHOOK_LER, json={}, timeout=10)

        if res.status_code in [200, 202]:
            data = res.json()
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                df = pd.DataFrame(
                    data.get("value", data.get("dados", [data]))
                )
            else:
                df = pd.DataFrame()

            if not df.empty:
                df.columns = df.columns.astype(str).str.strip().str.lower()
            return df
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


# Executa a busca real no Lists ao carregar o código
df_dados = buscar_dados_lists()

# --- 6. INTERFACE PRINCIPAL ---
st.title("🔍 Gemba Walk Digital")

aba1, aba2, aba3 = st.tabs(
    ["📋 Novo Registro", "📌 Quadro de Post-its", "📊 Dashboard"]
)

# --- ABA 1: NOVO REGISTRO ---
with aba1:
    with st.form("form_novo_registro", clear_on_submit=True):
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

        st.divider()

        st.warning("Preencha os detalhes (Obrigatório se Não Conforme):")
        problema = st.text_area("Qual foi o problema?")
        local = st.text_input("Onde ocorreu?")
        impacto = st.text_area("Qual o impacto?")
        causa = st.text_area("Causa aparente?")
        acao_imediata = st.text_area("Ação imediata?")

        responsavel_email = st.selectbox(
            "E-mail do Responsável",
            options=OPCOES_EMAILS,
            help="Digite para buscar e filtrar o e-mail corporativo.",
        )

        prazo = st.date_input("Prazo para Solução", value=date.today())

        submitted = st.form_submit_button("Salvar Registro")

        if submitted:
            if status_op == "Não Conforme":
                if (
                    not auditor
                    or not estacao
                    or not problema
                    or not responsavel_email
                ):
                    st.error(
                        "Preencha todos os campos obrigatórios (*) para Não Conformidades."
                    )
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
                            st.rerun()
                        else:
                            st.error(
                                f"Erro no Power Automate (Código {res.status_code}): {res.text}"
                            )
                    except Exception as e:
                        st.error(f"Falha de conexão com o Power Automate: {e}")
            else:
                st.success("Conformidade registrada com sucesso!")
                st.rerun()

# --- ABA 2: QUADRO DE POST-ITS ---
with aba2:
    st.subheader("📌 Pendências Ativas (Post-its)")

    if df_dados.empty:
        st.info("Nenhuma pendência encontrada no Microsoft Lists.")
    else:
        # Busca flexível por colunas equivalentes do Lists
        col_status = next(
            (c for c in df_dados.columns if "status" in c), None
        )

        if not col_status:
            st.warning(
                "A coluna 'Status' não foi retornada pelo Power Automate."
            )
        else:
            df_dados["status_clean"] = (
                df_dados[col_status]
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
                    item_id = str(
                        row.get("id", row.get("title", row.get("id_unico", idx)))
                    )
                    with cols[idx % 2]:
                        with st.container(border=True):
                            st.markdown(
                                f"### 🟨 {row.get('categoria', 'Não Conformidade')}"
                            )
                            st.caption(
                                f"**Criado por:** {row.get('auditor', 'N/A')} em {row.get('data_criacao', row.get('created', 'N/A'))}"
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
                                        st.toast("Item resolvido!", icon="✅")
                                        st.cache_data.clear()
                                        st.rerun()
                                    else:
                                        st.error(
                                            f"Erro ao atualizar status: {res_sol.status_code}"
                                        )
                                except Exception as e:
                                    st.error(f"Falha de conexão: {e}")

# --- ABA 3: DASHBOARD ---
with aba3:
    st.subheader("📊 Indicadores do Gemba Walk")

    if not df_dados.empty:
        col_status = next(
            (c for c in df_dados.columns if "status" in c), None
        )

        if col_status:
            status_serie = (
                df_dados[col_status]
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
            col_cat = next(
                (c for c in df_dados.columns if "categoria" in c), None
            )
            if col_cat:
                st.bar_chart(df_dados[col_cat].value_counts())
    else:
        st.info("Aguardando registros para exibir indicadores.")
