from datetime import date, datetime
import time
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
WEBHOOK_ROTINAS_CRIAR = st.secrets.get(
    "POWER_AUTOMATE_ROTINAS_CRIAR_URL",
    "https://defaultcd14821755e24b4e86f837f80bf5ae.f3.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/27/workflows/b5825bef53af44be9972fed8172241ee/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=3IQZAY4rMptiHzx_F1QYUjqIsWV4HhSoeQWsGloCAMU",
)
WEBHOOK_ROTINAS_LER = st.secrets.get(
    "POWER_AUTOMATE_ROTINAS_LER_URL",
    "https://defaultcd14821755e24b4e86f837f80bf5ae.f3.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/09/workflows/4c0c6254cf6a451f8b3180c48f3a8343/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=2E_zEeQwzxqgnFviwSiv3Q8xdbbpqKJM0odK2N9pKvE",
)
WEBHOOK_ROTINAS_EXCLUIR = st.secrets.get(
    "POWER_AUTOMATE_ROTINAS_EXCLUIR_URL",
    "https://defaultcd14821755e24b4e86f837f80bf5ae.f3.environment.api.powerplatform.com:443/powerautomate/automations/direct/cu/17/workflows/fc5c58c8f88f41a4aef0bed4e3a90d6e/triggers/manual/paths/invoke?api-version=1&sp=%2Ftriggers%2Fmanual%2Frun&sv=1.0&sig=naGDxbqgt9BRHgMszDYJTPpNDqO7gbXxUCxjIn2bzmQ",
)

# --- 3. LISTAS FIXAS ---
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

AUDITORES_GESTORES = sorted(
    list(
        set([
            "Jaqueline Guerra",
            "Geovane Valdevino",
            "Gissele Nogueira",
            "Yuri Fernandes",
            "Felipe Possato",
            "Henrique Borges",
            "Jessica Brandão",
            "Helen Esteves",
            "Giovane Carvalho",
            "Nelcir Junior",
            "Hebert Murtha",
            "Maicon Alves",
            "Victor Cavadas",
            "William Sousa",
            "Felipe Muniz",
            "Eduardo Francisco",
            "Tamires Ferreira",
        ])
    )
)

DIAS_SEMANA = [
    "Segunda-feira",
    "Terça-feira",
    "Quarta-feira",
    "Quinta-feira",
    "Sexta-feira",
    "Sábado",
    "Domingo",
]

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


# --- 5. FUNÇÕES PARA CARREGAR DADOS ---
@st.cache_data(ttl=5, show_spinner=False)
def buscar_dados_servidor(url_webhook):
    if not url_webhook:
        return pd.DataFrame()
    try:
        res = requests.get(url_webhook, timeout=15)
        if res.status_code != 200:
            res = requests.post(url_webhook, json={}, timeout=15)

        if res.status_code in [200, 202]:
            dados_json = res.json()
            df = pd.DataFrame()

            if isinstance(dados_json, list):
                df = pd.DataFrame(dados_json)
            elif isinstance(dados_json, dict):
                for chave in ["value", "dados", "items", "body"]:
                    if chave in dados_json and isinstance(dados_json[chave], list):
                        df = pd.DataFrame(dados_json[chave])
                        break
                if df.empty:
                    df = pd.DataFrame([dados_json])

            if not df.empty:
                df.columns = [str(c).strip() for c in df.columns]
            return df
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


# BARRA LATERAL (SIDEBAR)
with st.sidebar:
    if st.button("🔄 Atualizar Dados", use_container_width=True):
        st.cache_data.clear()
        st.session_state.pop("df_override", None)
        st.rerun()

    st.divider()
    st.markdown("### 🧪 Diagnóstico de Webhook")

    if st.button("🚀 Testar Fluxo de E-mail", use_container_width=True):
        if not WEBHOOK_ROTINAS_LER:
            st.error("URL do webhook não configurada.")
        else:
            payload_teste = {
                "origem": "Teste via Streamlit App",
                "data_hora_teste": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
            try:
                with st.spinner("Disparando requisição ao Power Automate..."):
                    res_teste = requests.post(
                        WEBHOOK_ROTINAS_LER, json=payload_teste, timeout=10
                    )
                    if res_teste.status_code in [200, 202]:
                        st.success(f"✅ Executado! Status: {res_teste.status_code}")
                    else:
                        st.error(
                            f"⚠️ Erro {res_teste.status_code}: {res_teste.text}"
                        )
            except Exception as e:
                st.error(f"❌ Falha de conexão: {e}")

# Inicialização de dados das inspeções
if "df_override" in st.session_state:
    df_dados = st.session_state["df_override"]
else:
    df_dados = buscar_dados_servidor(WEBHOOK_LER)

# Leitura das rotinas
df_rotinas_remoto = buscar_dados_servidor(WEBHOOK_ROTINAS_LER)

# Gerenciamento de exclusões na sessão local
if "rotinas_excluidas" not in st.session_state:
    st.session_state["rotinas_excluidas"] = set()

# Combina remoto + local
if "rotinas_local" in st.session_state and not st.session_state["rotinas_local"].empty:
    df_rotinas = pd.concat(
        [df_rotinas_remoto, st.session_state["rotinas_local"]], ignore_index=True
    )
else:
    df_rotinas = df_rotinas_remoto.copy()

# DEDUPLICAÇÃO DE ROTINAS (Evita a duplicação visual de rotinas recém-criadas)
if not df_rotinas.empty:
    col_id_dedup = next((c for c in df_rotinas.columns if c.lower() in ["id0_", "id0", "id", "_x0069_d0"]), None)
    if col_id_dedup:
        df_rotinas = df_rotinas.drop_duplicates(subset=[col_id_dedup], keep="last")

# Filtra rotinas excluídas localmente antes de renderizar
if not df_rotinas.empty:
    col_id_ref = next((c for c in df_rotinas.columns if c.lower() in ["id0_", "id0", "id", "_x0069_d0", "id_1"]), None)
    if col_id_ref:
        df_rotinas = df_rotinas[
            ~df_rotinas[col_id_ref]
            .astype(str)
            .isin(st.session_state["rotinas_excluidas"])
        ]

# Identificar a coluna de status principal e de inspeção
col_status = next((c for c in df_dados.columns if c.lower() == "status" or "status" in c.lower()), None) if not df_dados.empty else None

if not df_dados.empty and col_status:
    df_dados["status_clean"] = df_dados[col_status].fillna("").astype(str).str.strip().str.lower()

# Identificar colunas de ID
col_id0 = next((c for c in df_dados.columns if c.lower() in ["id0_", "id0"]), None) if not df_dados.empty else None
col_sp_id = next((c for c in df_dados.columns if c.lower() in ["id", "id_unico", "title"]), None) if not df_dados.empty else None

# --- 6. INTERFACE PRINCIPAL ---
st.title("🔍 Gemba Walk Digital")
aba1, aba2, aba3, aba4, aba5 = st.tabs([
    "📋 Novo Registro", 
    "📌 Quadro de Post-its", 
    "📅 Rotinas", 
    "🚨 Rotinas Pendentes", 
    "📊 Dashboard"
])

# --- ABA 1: NOVO REGISTRO ---
with aba1:
    status_op = st.radio(
        "Status da Inspeção*",
        ["Conforme", "Não Conforme"],
        horizontal=True,
        key="status_op_input",
    )

    st.divider()

    with st.form("form_novo_registro", clear_on_submit=True):
        st.subheader("Informações Gerais")
        col1, col2 = st.columns(2)
        with col1:
            auditor = st.selectbox(
                "Nome do Auditor/Gestor*",
                options=AUDITORES_GESTORES,
                index=None,
                placeholder="Selecione ou digite o nome...",
                key="auditor_input",
            )
        with col2:
            estacao = st.text_input("Área / Estação*", key="estacao_input")

        categoria_sel = st.selectbox("Selecione a Categoria*", list(CATEGORIAS.keys()), key="cat_input")
        st.info(f"💡 **O que observar:** {CATEGORIAS[categoria_sel]}")

        if status_op == "Não Conforme":
            st.divider()
            st.markdown("**Detalhes da Inspeção**")
            problema = st.text_area("Qual foi o problema?*")
            local = st.text_input("Onde ocorreu?*")
            impacto = st.text_area("Qual o impacto?")
            causa = st.text_area("Causa aparente?")
            acao_imediata = st.text_area("Ação imediata?")

            col_resp, col_prazo = st.columns(2)

            with col_resp:
                responsavel_email = st.selectbox(
                    "E-mail do Responsável*",
                    options=EMAILS_CORPORATIVOS,
                    index=None,
                    placeholder="Selecione ou digite o e-mail...",
                )

            with col_prazo:
                st.markdown("🚨 **Atenção**")
                prazo = st.date_input(
                    "📅 **Prazo para Solução**",
                    value=date.today(),
                )
        else:
            problema, local, impacto, causa, acao_imediata = "", "", "", "", ""
            responsavel_email = None
            prazo = date.today()

        submitted = st.form_submit_button("Salvar Registro", type="primary")

    if submitted:
        if not WEBHOOK_CRIAR:
            st.error("URL do Webhook de criação (POWER_AUTOMATE_CRIAR_URL) não configurada nos secrets.")
        elif not auditor or not estacao:
            st.error("Preencha as Informações Gerais obrigatórias (Auditor e Área/Estação).")
        elif status_op == "Não Conforme" and (not problema or not responsavel_email):
            st.error("Preencha todos os campos obrigatórios (*) do detalhamento da Não Conformidade.")
        else:
            id_unico = str(uuid.uuid4())[:8]

            payload = {
                "id0_": str(id_unico),
                "id0": str(id_unico),
                "id": str(id_unico),
                "auditor": str(auditor),
                "data_criacao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "estacao": str(estacao),
                "categoria": str(categoria_sel),
                "status_inspecao": str(status_op),
                "problema": str(problema) if status_op == "Não Conforme" else "N/A - Conforme",
                "local": str(local) if status_op == "Não Conforme" else str(estacao),
                "impacto": str(impacto) if status_op == "Não Conforme" else "",
                "causa": str(causa) if status_op == "Não Conforme" else "",
                "acao_imediata": str(acao_imediata) if status_op == "Não Conforme" else "",
                "responsavel": str(responsavel_email) if status_op == "Não Conforme" else str(auditor),
                "prazo": prazo.strftime("%Y-%m-%d") if status_op == "Não Conforme" else "",
                "status": "Finalizado" if status_op == "Conforme" else "Pendente",
                "data_solucao": datetime.now().strftime("%Y-%m-%d %H:%M:%S") if status_op == "Conforme" else "",
            }

            try:
                with st.spinner("Enviando registro..."):
                    res = requests.post(WEBHOOK_CRIAR, json=payload, timeout=15)
                    if res.status_code in [200, 202, 502]:
                        time.sleep(1.5)
                        st.cache_data.clear()
                        st.session_state.pop("df_override", None)
                        st.success(f"Registro '{status_op}' salvo com sucesso!")
                        st.rerun()
                    else:
                        st.error(f"Erro {res.status_code}: {res.text}")
            except requests.exceptions.Timeout:
                st.cache_data.clear()
                st.session_state.pop("df_override", None)
                st.success(f"Registro '{status_op}' processado com sucesso!")
                st.rerun()
            except Exception as e:
                st.error(f"Falha de conexão com o Power Automate: {e}")

# --- ABA 2: QUADRO DE POST-ITS ---
with aba2:
    st.subheader("📌 Pendências Ativas (Post-its)")

    if df_dados.empty or "status_clean" not in df_dados.columns:
        st.info("Nenhuma pendência encontrada no momento.")
    else:
        # Exclui tudo que for Conforme, Finalizado ou Resolvido
        mask_excluir = df_dados["status_clean"].str.contains("finalizado|resolvido|conforme", case=False, na=False)
        # Mantém apenas os itens pendentes ou não resolvidos
        pendentes = df_dados[~mask_excluir]

        if pendentes.empty:
            st.success("🎉 Nenhuma pendência aberta no momento!")
        else:
            cols = st.columns(2)
            for idx, (original_idx, row) in enumerate(pendentes.iterrows()):
                val_id0 = str(row.get(col_id0)) if col_id0 and pd.notna(row.get(col_id0)) else None
                val_sp_id = str(row.get(col_sp_id)) if col_sp_id and pd.notna(row.get(col_sp_id)) else str(idx)
                display_id = val_id0 if val_id0 else val_sp_id

                with cols[idx % 2]:
                    with st.container(border=True):
                        st.markdown(f"### 🟨 {row.get('categoria', 'Não Conformidade')}")
                        st.caption(f"**ID:** `{display_id}` | **Criado por:** {row.get('auditor', 'N/A')}")
                        st.write(f"**Local:** {row.get('estacao', '')} - {row.get('local', '')}")
                        st.write(f"**Problema:** {row.get('problema', '')}")
                        st.write(f"**Impacto:** {row.get('impacto', '')}")
                        st.write(f"**Causa Aparente:** {row.get('causa', '')}")
                        st.write(f"**Ação Imediata:** {row.get('acao_imediata', '')}")
                        st.write(f"**Responsável:** {row.get('responsavel', '')}")
                        st.markdown(f"🗓️ **Prazo:** `{row.get('prazo', 'N/A')}`")

                        if st.button("✅ Resolvido", key=f"btn_res_{display_id}_{original_idx}"):
                            if not WEBHOOK_RESOLVER:
                                st.error("URL de resolução não configurada.")
                            else:
                                payload_sol = {
                                    "id0_": val_id0 if val_id0 else val_sp_id,
                                    "id0": val_id0 if val_id0 else val_sp_id,
                                    "id": val_sp_id,
                                    "ID": val_sp_id,
                                    "status": "Resolvido",
                                    "data_solucao": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                }
                                try:
                                    with st.spinner("Enviando atualização..."):
                                        res_sol = requests.post(WEBHOOK_RESOLVER, json=payload_sol, timeout=15)
                                        if res_sol.status_code in [200, 202, 502]:
                                            if col_status:
                                                df_dados.loc[original_idx, col_status] = "Resolvido"
                                            df_dados.loc[original_idx, "status_clean"] = "resolvido"
                                            st.session_state["df_override"] = df_dados
                                            st.cache_data.clear()
                                            st.toast("Item marcado como Resolvido!", icon="✅")
                                            st.rerun()
                                        else:
                                            st.error(f"Erro Power Automate ({res_sol.status_code}): {res_sol.text}")
                                except requests.exceptions.Timeout:
                                    st.toast("Item atualizado!", icon="✅")
                                    st.cache_data.clear()
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Falha de conexão com a API: {e}")

# --- ABA 3: ROTINAS PROGRAMADAS ---
with aba3:
    st.subheader("📅 Programação de Rotinas Gemba")
    st.write("Agende inspeções recorrentes e receba lembretes automáticos por e-mail.")

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
                        "id0_": id_rotina,
                        "id0": id_rotina,
                        "id": id_rotina,
                        "ID": id_rotina,
                        "responsavel_nome": rotina_pessoa,
                        "responsavel_email": rotina_email,
                        "dia_semana": rotina_dia,
                        "categoria": rotina_categoria,
                        "estacao": rotina_estacao,
                        "instrucoes": rotina_obs,
                        "data_cadastro": datetime.now().strftime("%Y-%m-%d"),
                    }

                    if WEBHOOK_ROTINAS_CRIAR:
                        try:
                            with st.spinner("Cadastrando rotina..."):
                                res_rot = requests.post(WEBHOOK_ROTINAS_CRIAR, json=payload_rotina, timeout=10)
                                if res_rot.status_code in [200, 202, 502]:
                                    time.sleep(1)
                                    st.session_state.pop("rotinas_local", None)
                                    st.cache_data.clear()
                                    st.success("Rotina agendada com sucesso no sistema!")
                                    st.rerun()
                                else:
                                    # Caso o webhook dê erro, salva na sessão temporária
                                    if "rotinas_local" not in st.session_state:
                                        st.session_state["rotinas_local"] = pd.DataFrame()
                                    st.session_state["rotinas_local"] = pd.concat(
                                        [st.session_state["rotinas_local"], pd.DataFrame([payload_rotina])],
                                        ignore_index=True,
                                    )
                                    st.warning("Salvo localmente. O webhook retornou um status inesperado.")
                        except Exception:
                            if "rotinas_local" not in st.session_state:
                                st.session_state["rotinas_local"] = pd.DataFrame()
                            st.session_state["rotinas_local"] = pd.concat(
                                [st.session_state["rotinas_local"], pd.DataFrame([payload_rotina])],
                                ignore_index=True,
                            )
                            st.warning("Salvo localmente. Falha ao conectar ao webhook de rotinas.")
                    else:
                        if "rotinas_local" not in st.session_state:
                            st.session_state["rotinas_local"] = pd.DataFrame()
                        st.session_state["rotinas_local"] = pd.concat(
                            [st.session_state["rotinas_local"], pd.DataFrame([payload_rotina])],
                            ignore_index=True,
                        )
                        st.success("Rotina agendada com sucesso!")

                    st.cache_data.clear()
                    st.rerun()

    st.divider()
    st.markdown("### 🟦 Quadro de Rotinas Ativas")

    df_rot_exibir = df_rotinas.copy()

    if df_rot_exibir.empty:
        st.info("Nenhuma rotina cadastrada ainda ou o webhook não retornou dados.")
    else:
        cols_r = st.columns(2)
        for idx_r, (r_idx, row_r) in enumerate(df_rot_exibir.iterrows()):
            # Procura pelo ID nativo do SharePoint/Lists
            id_sp_val = None
            for col_k in ["ID", "id", "Id"]:
                if col_k in row_r and pd.notna(row_r[col_k]):
                    id_sp_val = str(row_r[col_k])
                    break

            if not id_sp_val:
                id_sp_val = str(r_idx)

            # Procura pelo ID customizado id0_ / id0
            id0_rot = None
            for col_k in ["id0_", "id0", "ID0_", "ID0"]:
                if col_k in row_r and pd.notna(row_r[col_k]):
                    id0_rot = str(row_r[col_k])
                    break

            if not id0_rot:
                id0_rot = id_sp_val

            nome_resp = str(row_r.get("responsavel_nome", row_r.get("responsavel", "N/A")))
            email_resp = str(row_r.get("responsavel_email", "Não informado"))
            dia_semana_rot = str(row_r.get("dia_semana", "N/A"))
            cat_rot = str(row_r.get("categoria", "N/A"))
            estacao_rot = str(row_r.get("estacao", "N/A"))
            instrucoes_rot = str(row_r.get("instrucoes", ""))

            with cols_r[idx_r % 2]:
                with st.container(border=True):
                    col_tit, col_del = st.columns([0.85, 0.15])
                    with col_tit:
                        st.markdown(f"### 📅 {dia_semana_rot} - {cat_rot}")
                    with col_del:
                        if st.button("🗑️", key=f"btn_del_rot_{id_sp_val}_{idx_r}", help="Excluir esta rotina"):
                            st.session_state[f"confirm_delete_{id_sp_val}"] = True
                            st.rerun()

                    if st.session_state.get(f"confirm_delete_{id_sp_val}", False):
                        st.warning("⚠️ Deseja excluir esta rotina permanentemente do Microsoft Lists?")
                        col_c1, col_c2 = st.columns(2)

                        with col_c1:
                            if st.button("Sim, Excluir", key=f"sim_del_{id_sp_val}_{idx_r}", type="primary"):
                                try:
                                    parsed_id = int(id_sp_val)
                                except (ValueError, TypeError):
                                    parsed_id = id_sp_val

                                payload_excluir = {
                                    "ID": parsed_id,
                                    "id0_": str(id0_rot),
                                    "id0": str(id0_rot),
                                }

                                if WEBHOOK_ROTINAS_EXCLUIR:
                                    try:
                                        with st.spinner("Excluindo no Microsoft Lists..."):
                                            res_del = requests.post(WEBHOOK_ROTINAS_EXCLUIR, json=payload_excluir, timeout=15)
                                            
                                            if res_del.status_code in [200, 202, 204, 502]:
                                                st.session_state["rotinas_excluidas"].add(str(id_sp_val))
                                                st.session_state["rotinas_excluidas"].add(str(id0_rot))
                                                st.cache_data.clear()
                                                st.toast("Rotina excluída com sucesso!", icon="🗑️")
                                                st.rerun()
                                            else:
                                                st.error(f"Erro no Power Automate ({res_del.status_code}): {res_del.text}")
                                    except requests.exceptions.Timeout:
                                        st.session_state["rotinas_excluidas"].add(str(id_sp_val))
                                        st.session_state["rotinas_excluidas"].add(str(id0_rot))
                                        st.cache_data.clear()
                                        st.toast("Solicitação enviada!", icon="🗑️")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Erro de conexão ao excluir: {e}")
                                else:
                                    st.error("URL 'POWER_AUTOMATE_ROTINAS_EXCLUIR_URL' não encontrada nos secrets.")

                        with col_c2:
                            if st.button("Cancelar", key=f"cancel_del_{id_sp_val}_{idx_r}"):
                                st.session_state.pop(f"confirm_delete_{id_sp_val}", None)
                                st.rerun()

                    st.write(f"👤 **Responsável pela Rotina:** {nome_resp}")
                    st.write(f"📧 **E-mail para Notificação:** {email_resp}")
                    st.write(f"🏢 **Setor / Área a ser Inspecionada:** {estacao_rot}")
                    st.write(f"📆 **Dia da Semana Fixo:** {dia_semana_rot}")
                    st.write(f"🏷️ **Categoria da Inspeção:** {cat_rot}")

                    if instrucoes_rot and instrucoes_rot.strip() != "" and instrucoes_rot.upper() != "NONE":
                        st.caption(f"📝 **Instruções:** {instrucoes_rot}")

# --- ABA 4: ROTINAS PENDENTES ---
with aba4:
    st.subheader("🚨 Rotinas Pendentes (Hoje)")

    # Descobrir o dia da semana atual
    dias_pt = [
        "Segunda-feira",
        "Terça-feira",
        "Quarta-feira",
        "Quinta-feira",
        "Sexta-feira",
        "Sábado",
        "Domingo",
    ]
    hoje_idx = datetime.now().weekday()
    hoje_str = dias_pt[hoje_idx]
    hoje_date = datetime.now().date()

    st.write(f"**Dia de hoje:** {hoje_str} ({hoje_date.strftime('%d/%m/%Y')})")
    st.info(
        "💡 Este painel cruza os dados ao vivo: verifica quem está agendado para hoje e se já preencheu o registro. Os pendentes aparecem abaixo."
    )

    if df_rotinas.empty:
        st.info("Nenhuma rotina cadastrada no sistema.")
    else:
        # Filtra rotinas que caem no dia da semana de hoje
        rotinas_hoje = df_rotinas[df_rotinas["dia_semana"] == hoje_str]

        if rotinas_hoje.empty:
            st.success("Nenhuma rotina agendada para hoje!")
        else:
            # Prepara os dados de inspeção (Gemba_Walk_Dados) filtrando apenas as de hoje
            if not df_dados.empty:
                col_data = next(
                    (
                        c
                        for c in df_dados.columns
                        if "data" in c.lower() or "created" in c.lower()
                    ),
                    None,
                )
                if col_data:
                    # Converte a data do Lists para o formato de data puro (sem hora) para comparar
                    df_dados["data_date"] = pd.to_datetime(
                        df_dados[col_data], errors="coerce"
                    ).dt.date
                    inspecoes_hoje = df_dados[df_dados["data_date"] == hoje_date]
                else:
                    inspecoes_hoje = pd.DataFrame()
            else:
                inspecoes_hoje = pd.DataFrame()

            # Verifica quem fez e quem não fez
            pendentes_hoje = []
            for _, rotina in rotinas_hoje.iterrows():
                resp_rotina = (
                    str(
                        rotina.get(
                            "responsavel_nome", rotina.get("responsavel", "")
                        )
                    )
                    .strip()
                    .lower()
                )

                realizado = False
                if not inspecoes_hoje.empty:
                    # Busca a coluna com o nome do auditor/responsável no registro
                    col_aud = next(
                        (
                            c
                            for c in inspecoes_hoje.columns
                            if "auditor" in c.lower() or "responsavel" in c.lower()
                        ),
                        None,
                    )
                    if col_aud:
                        # Compara se o responsável da rotina existe nos registros de hoje
                        filtro = (
                            inspecoes_hoje[col_aud]
                            .astype(str)
                            .str.strip()
                            .str.lower()
                            == resp_rotina
                        )
                        if filtro.any():
                            realizado = True

                # Se não realizou, adiciona à lista de pendentes
                if not realizado:
                    pendentes_hoje.append(rotina)

            # Exibe o resultado
            if not pendentes_hoje:
                st.balloons()
                st.success("🎉 Todas as rotinas de hoje já foram realizadas!")
            else:
                st.warning(
                    f"⚠️ Há {len(pendentes_hoje)} rotina(s) pendente(s) para hoje."
                )
                cols_p = st.columns(2)
                for idx_p, p in enumerate(pendentes_hoje):
                    nome_p = p.get("responsavel_nome", p.get("responsavel", "N/A"))
                    email_p = p.get("responsavel_email", "N/A")
                    dia_p = p.get("dia_semana", "N/A")
                    cat_p = p.get("categoria", "N/A")
                    est_p = p.get("estacao", "N/A")

                    with cols_p[idx_p % 2]:
                        with st.container(border=True):
                            st.markdown("#### ⏳ Pendente")
                            st.write(f"👤 **Responsável pela Rotina:** {nome_p}")
                            st.write(f"📧 **E-mail para Notificação:** {email_p}")
                            st.write(f"📆 **Dia da Semana Fixo:** {dia_p}")
                            st.write(f"🏷️ **Categoria da Inspeção:** {cat_p}")
                            st.write(f"🏢 **Estação / Área:** {est_p}")

# --- ABA 5: DASHBOARD ---
with aba5:
    st.subheader("📊 Métricas e Desempenho do Gemba Walk")
    if df_dados.empty:
        st.info("Sem dados suficientes para exibir métricas no momento.")
    else:
        m1, m2, m3 = st.columns(3)
        total_regs = len(df_dados)

        if "status_clean" in df_dados.columns:
            mask_encerrados = df_dados["status_clean"].str.contains("finalizado|resolvido|conforme", case=False, na=False)
            pendentes_cnt = len(df_dados[~mask_encerrados])
            resolvidos_cnt = len(df_dados[mask_encerrados])
        else:
            pendentes_cnt = 0
            resolvidos_cnt = 0

        m1.metric("Total de Inspeções", total_regs)
        m2.metric("Pendências Abertas", pendentes_cnt)
        m3.metric("Concluídas / Resolvidas", resolvidos_cnt)

        st.divider()

        col_chart1, col_chart2 = st.columns(2)
        with col_chart1:
            st.markdown("#### Inspeções por Categoria")
            col_cat = next((c for c in df_dados.columns if "categoria" in c.lower()), None)
            if col_cat:
                cat_counts = df_dados[col_cat].value_counts()
                st.bar_chart(cat_counts)
            else:
                st.caption("Coluna de categoria não identificada.")

        with col_chart2:
            st.markdown("#### Inspeções por Auditor")
            col_aud = next((c for c in df_dados.columns if "auditor" in c.lower() or "responsavel" in c.lower()), None)
            if col_aud:
                aud_counts = df_dados[col_aud].value_counts()
                st.bar_chart(aud_counts)
            else:
                st.caption("Coluna de auditor não identificada.")
