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
WEBHOOK_CRIAR = st.secrets.get("POWER_AUTOMATE_CRIAR_URL", "")
WEBHOOK_RESOLVER = st.secrets.get("POWER_AUTOMATE_RESOLVER_URL", "")
WEBHOOK_LER = st.secrets.get("POWER_AUTOMATE_LER_URL", "")

# --- 3. LISTA FIXA DE E-MAILS ---
EMAILS_CORPORATIVOS = sorted(
    list(
        set([
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
            "eduardo.francisco@mustad.com",
        ])
    )
)

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


# --- 5. FUNÇÃO PARA CARREGAR DADOS ---
def carregar_dados():
    try:
        res = requests.get(WEBHOOK_LER, timeout=10)
        if res.status_code != 200:
            res = requests.post(WEBHOOK_LER, json={}, timeout=10)

        if res.status_code in [200, 202]:
            dados_json = res.json()
            df_dados = pd.DataFrame()

            if isinstance(dados_json, list):
                df_dados = pd.DataFrame(dados_json)
            elif isinstance(dados_json, dict):
                for chave in ["value", "dados", "items", "body"]:
                    if chave in dados_json and isinstance(
                        dados_json[chave], list
                    ):
                        df_dados = pd.DataFrame(dados_json[chave])
                        break
                if df_dados.empty:
                    df_dados = pd.DataFrame([dados_json])

            if not df_dados.empty:
                df_dados.columns = (
                    df_dados.columns.astype(str).str.strip().str.lower()
                )

            return df_dados
        else:
            return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


# Armazenar/Carregar dados no session_state para permitir atualizações instantâneas na tela
if "df_dados" not in st.session_state or st.sidebar.button("🔄 Recarregar Dados"):
    st.session_state["df_dados"] = carregar_dados()

df_dados = st.session_state["df_dados"]

# Normalizar coluna de status para comparação consistente
col_status = next(
    (c for c in df_dados.columns if "status" in c), None
) if not df_dados.empty else None

if df_dados is not None and not df_dados.empty and col_status:
    df_dados["status_clean"] = (
        df_dados[col_status].fillna("").astype(str).str.strip().str.lower()
    )

# Coluna de identificação do ID
col_id = next(
    (c for c in df_dados.columns if c in ["id", "id_unico", "title"]), None
) if not df_dados.empty else None

# --- DIAGNÓSTICO DA CONEXÃO ---
with st.sidebar.expander("🛠️ Diagnóstico do Sistema"):
    st.write(f"**Registros carregados:** {len(df_dados)}")
    if not df_dados.empty:
        st.write("**Colunas disponíveis:**", list(df_dados.columns))

# --- 6. INTERFACE PRINCIPAL ---
st.title("🔍 Gemba Walk Digital")
aba1, aba2, aba3 = st.tabs(
    ["📋 Novo Registro", "📌 Quadro de Post-its", "📊 Dashboard"]
)

# --- ABA 1: NOVO REGISTRO ---
with aba1:
    with st.form("form_registro", clear_on_submit=True):
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

        st.markdown("**Detalhes da Inspeção**")
        problema = st.text_area("Qual foi o problema?*")
        local = st.text_input("Onde ocorreu?*")
        impacto = st.text_area("Qual o impacto?")
        causa = st.text_area("Causa aparente?")
        acao_imediata = st.text_area("Ação imediata?")

        responsavel_email = st.selectbox(
            "E-mail do Responsável*",
            options=EMAILS_CORPORATIVOS,
            index=None,
            placeholder="Selecione ou digite o e-mail...",
            help="Digite as primeiras letras do e-mail para filtrar a lista.",
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
                            st.success("Não conformidade salva com sucesso!")
                            # Força atualização dos dados
                            st.session_state["df_dados"] = carregar_dados()
                            st.rerun()
                        else:
                            st.error(f"Erro {res.status_code}: {res.text}")
                    except Exception as e:
                        st.error(f"Falha de conexão com o Power Automate: {e}")
            else:
                st.success("Conformidade registrada com sucesso!")

# --- ABA 2: QUADRO DE POST-ITS ---
with aba2:
    st.subheader("📌 Pendências Ativas (Post-its)")

    if df_dados.empty or "status_clean" not in df_dados.columns:
        st.info("Nenhuma pendência encontrada no momento.")
    else:
        # Filtra registros com status 'pendente'
        pendentes = df_dados[df_dados["status_clean"] == "pendente"]

        if pendentes.empty:
            st.success("🎉 Nenhuma pendência aberta no momento!")
        else:
            cols = st.columns(2)
            for idx, (original_idx, row) in enumerate(pendentes.iterrows()):
                item_id = str(row.get(col_id, f"{idx}")) if col_id else str(idx)

                with cols[idx % 2]:
                    with st.container(border=True):
                        st.markdown(
                            f"### 🟨 {row.get('categoria', 'Não Conformidade')}"
                        )
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
                            "✅ Resolvido", key=f"btn_res_{item_id}_{original_idx}"
                        ):
                            payload_sol = {
                                "id": item_id,
                                "status": "Resolvido",
                                "data_solucao": datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                            }
                            try:
                                # 1. Atualizar instantaneamente no estado local (para refletir na tela na hora)
                                if col_status:
                                    st.session_state["df_dados"].at[
                                        original_idx, col_status
                                    ] = "Resolvido"
                                    st.session_state["df_dados"].at[
                                        original_idx, "status_clean"
                                    ] = "resolvido"

                                # 2. Disparar atualização assíncrona no Power Automate
                                requests.post(
                                    WEBHOOK_RESOLVER,
                                    json=payload_sol,
                                    timeout=5,
                                )

                                st.toast("Item resolvido com sucesso!", icon="✅")
                                st.rerun()

                            except Exception as e:
                                st.error(f"Falha ao comunicar envio: {e}")

# --- ABA 3: DASHBOARD ---
with aba3:
    st.subheader("📊 Indicadores do Gemba Walk")

    if not df_dados.empty and "status_clean" in df_dados.columns:
        total_registros = len(df_dados)
        qtd_pendentes = (df_dados["status_clean"] == "pendente").sum()
        qtd_resolvidos = (df_dados["status_clean"] == "resolvido").sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("Total de Registros", total_registros)
        c2.metric("Pendentes", qtd_pendentes)
        c3.metric("Resolvidos", qtd_resolvidos)

        st.divider()
        st.markdown("**Problemas Encontrados por Categoria**")

        col_cat = next((c for c in df_dados.columns if "categoria" in c), None)
        if col_cat:
            st.bar_chart(df_dados[col_cat].value_counts())
    else:
        st.info("Aguardando registros para exibir indicadores.")
