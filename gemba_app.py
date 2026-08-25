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

# NOVO WEBHOOK PARA SALVAR E LER ROTINAS
WEBHOOK_ROTINAS_CRIAR = st.secrets.get("POWER_AUTOMATE_ROTINAS_CRIAR_URL", "")
WEBHOOK_ROTINAS_LER = st.secrets.get("POWER_AUTOMATE_ROTINAS_LER_URL", "")

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
@st.cache_data(ttl=2, show_spinner=False)
def buscar_dados_servidor():
    try:
        res = requests.get(WEBHOOK_LER, timeout=15)
        if res.status_code != 200:
            res = requests.post(WEBHOOK_LER, json={}, timeout=15)

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


@st.cache_data(ttl=5, show_spinner=False)
def buscar_rotinas_servidor():
    if not WEBHOOK_ROTINAS_LER:
        # Retorna lista guardada na sessão para testes se não houver webhook configurado
        return st.session_state.get("rotinas_local", pd.DataFrame())
    try:
        res = requests.get(WEBHOOK_ROTINAS_LER, timeout=15)
        if res.status_code != 200:
            res = requests.post(WEBHOOK_ROTINAS_LER, json={}, timeout=15)

        if res.status_code in [200, 202]:
            dados_json = res.json()
            df_rotinas = pd.DataFrame()

            if isinstance(dados_json, list):
                df_rotinas = pd.DataFrame(dados_json)
            elif isinstance(dados_json, dict):
                for chave in ["value", "dados", "items", "body"]:
                    if chave in dados_json and isinstance(
                        dados_json[chave], list
                    ):
                        df_rotinas = pd.DataFrame(dados_json[chave])
                        break
                if df_rotinas.empty:
                    df_rotinas = pd.DataFrame([dados_json])

            if not df_rotinas.empty:
                df_rotinas.columns = (
                    df_rotinas.columns.astype(str).str.strip().str.lower()
                )

            return df_rotinas
        else:
            return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


# Botão lateral para atualizar manualmente
with st.sidebar:
    if st.button("🔄 Atualizar Dados", use_container_width=True):
        st.cache_data.clear()
        st.session_state.pop("df_override", None)
        st.rerun()

# Inicialização de dados
if "df_override" in st.session_state:
    df_dados = st.session_state["df_override"]
else:
    df_dados = buscar_dados_servidor()

df_rotinas = buscar_rotinas_servidor()

# Identificar a coluna de status
col_status = (
    next((c for c in df_dados.columns if "status" in c), None)
    if not df_dados.empty
    else None
)

if not df_dados.empty and col_status:
    df_dados["status_clean"] = (
        df_dados[col_status].fillna("").astype(str).str.strip().str.lower()
    )

# Identificar colunas de ID
col_id0 = (
    next((c for c in df_dados.columns if c == "id0"), None)
    if not df_dados.empty
    else None
)

col_sp_id = (
    next((c for c in df_dados.columns if c in ["id", "id_unico", "title"]), None)
    if not df_dados.empty
    else None
)

# --- 6. INTERFACE PRINCIPAL ---
st.title("🔍 Gemba Walk Digital")
aba1, aba2, aba3, aba4 = st.tabs(
    ["📋 Novo Registro", "📌 Quadro de Post-its", "📅 Rotinas", "📊 Dashboard"]
)

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
                help="Digite as primeiras letras do nome para filtrar a lista.",
                key="auditor_input",
            )
        with col2:
            estacao = st.text_input("Área / Estação*", key="estacao_input")

        categoria_sel = st.selectbox(
            "Selecione a Categoria*", list(CATEGORIAS.keys()), key="cat_input"
        )
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
                    help="Digite as primeiras letras do e-mail para filtrar a lista.",
                )

            with col_prazo:
                st.markdown("🚨 **Atenção ao Prazo Acordado**")
                prazo = st.date_input(
                    "📅 Prazo para Solução*",
                    value=date.today(),
                    help="⚠️ DEFINA UM PRAZO ACORDADO COM O RESPONSÁVEL!",
                )
        else:
            problema = ""
            local = ""
            impacto = ""
            causa = ""
            acao_imediata = ""
            responsavel_email = None
            prazo = date.today()

        submitted = st.form_submit_button("Salvar Registro", type="primary")

    if submitted:
        if not auditor or not estacao:
            st.error(
                "Preencha as Informações Gerais obrigatórias (Auditor e Área/Estação)."
            )
        elif status_op == "Não Conforme" and (
            not problema or not responsavel_email
        ):
            st.error(
                "Preencha todos os campos obrigatórios (*) do detalhamento da Não Conformidade."
            )
        else:
            id_unico = str(uuid.uuid4())[:8]

            payload = {
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
                with st.spinner("Enviando registro ao Microsoft Lists..."):
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
        pendentes = df_dados[df_dados["status_clean"] == "pendente"]

        if pendentes.empty:
            st.success("🎉 Nenhuma pendência aberta no momento!")
        else:
            cols = st.columns(2)
            for idx, (original_idx, row) in enumerate(pendentes.iterrows()):
                val_id0 = (
                    str(row.get(col_id0))
                    if col_id0 and pd.notna(row.get(col_id0))
                    else None
                )
                val_sp_id = (
                    str(row.get(col_sp_id))
                    if col_sp_id and pd.notna(row.get(col_sp_id))
                    else str(idx)
                )

                display_id = val_id0 if val_id0 else val_sp_id

                with cols[idx % 2]:
                    with st.container(border=True):
                        st.markdown(
                            f"### 🟨 {row.get('categoria', 'Não Conformidade')}"
                        )
                        st.caption(
                            f"**ID:** `{display_id}` | **Criado por:** {row.get('auditor', 'N/A')}"
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
                        st.markdown(f"🗓️ **Prazo:** `{row.get('prazo', 'N/A')}`")

                        if st.button(
                            "✅ Resolvido",
                            key=f"btn_res_{display_id}_{original_idx}",
                        ):
                            payload_sol = {
                                "id0": val_id0 if val_id0 else val_sp_id,
                                "id": val_sp_id,
                                "ID": val_sp_id,
                                "status": "Resolvido",
                                "Status": "Resolvido",
                                "data_solucao": datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                            }

                            try:
                                with st.spinner(
                                    "Enviando atualização para o Power Automate..."
                                ):
                                    res_sol = requests.post(
                                        WEBHOOK_RESOLVER,
                                        json=payload_sol,
                                        timeout=15,
                                    )

                                    if res_sol.status_code in [200, 202, 502]:
                                        if col_status:
                                            df_dados.loc[
                                                original_idx, col_status
                                            ] = "Resolvido"
                                        df_dados.loc[
                                            original_idx, "status_clean"
                                        ] = "resolvido"
                                        st.session_state["df_override"] = (
                                            df_dados
                                        )

                                        st.cache_data.clear()
                                        st.toast(
                                            "Item marcado como Resolvido!",
                                            icon="✅",
                                        )
                                        st.rerun()
                                    else:
                                        st.error(
                                            f"Erro Power Automate ({res_sol.status_code}): {res_sol.text}"
                                        )
                            except requests.exceptions.Timeout:
                                st.toast(
                                    "Item atualizado!",
                                    icon="✅",
                                )
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Falha de conexão com a API: {e}")

# --- ABA 3: ROTINAS PROGRAMADAS ---
with aba4 if False else aba3:
    st.subheader("📅 Programação de Rotinas Gemba")
    st.write("Agende inspeções recorrentes e receba lembretes automáticos por e-mail.")

    with st.expander("➕ Cadastrar Nova Rotina Programada", expanded=False):
        with st.form("form_nova_rotina", clear_on_submit=True):
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                rotina_pessoa = st.selectbox(
                    "Responsável pela Rotina*",
                    options=AUDITORES_GESTORES,
                    index=None,
                    placeholder="Selecione o auditor...",
                )
                rotina_email = st.selectbox(
                    "E-mail para Notificação*",
                    options=EMAILS_CORPORATIVOS,
                    index=None,
                    placeholder="Selecione o e-mail...",
                )
            with col_r2:
                rotina_dia = st.selectbox(
                    "Dia da Semana Fixo*",
                    options=DIAS_SEMANA,
                )
                rotina_categoria = st.selectbox(
                    "Categoria da Inspeção*",
                    options=list(CATEGORIAS.keys()),
                )

            rotina_estacao = st.text_input("Setor / Área a ser Inspecionada*", placeholder="Ex: Linha de Montagem 02")
            rotina_obs = st.text_area("Objetivo / Instruções adicionais", placeholder="Ex: Verificar uso correto de EPIs e organização da bancada.")

            btn_salvar_rotina = st.form_submit_button("Agendar Rotina", type="primary")

            if btn_salvar_rotina:
                if not rotina_pessoa or not rotina_email or not rotina_estacao:
                    st.error("Preencha todos os campos obrigatórios (*).")
                else:
                    id_rotina = str(uuid.uuid4())[:8]
                    payload_rotina = {
                        "id0": id_rotina,
                        "responsavel_nome": rotina_pessoa,
                        "responsavel_email": rotina_email,
                        "dia_semana": rotina_dia,
                        "categoria": rotina_categoria,
                        "estacao": rotina_estacao,
                        "instrucoes": rotina_obs,
                        "data_cadastro": datetime.now().strftime("%Y-%m-%d"),
                    }

                    # Armazenar localmente (fallback para sessão)
                    if "rotinas_local" not in st.session_state:
                        st.session_state["rotinas_local"] = pd.DataFrame()
                    st.session_state["rotinas_local"] = pd.concat([
                        st.session_state["rotinas_local"],
                        pd.DataFrame([payload_rotina])
                    ], ignore_index=True)

                    if WEBHOOK_ROTINAS_CRIAR:
                        try:
                            res_r = requests.post(WEBHOOK_ROTINAS_CRIAR, json=payload_rotina, timeout=10)
                            st.success("Rotina agendada com sucesso no sistema!")
                        except Exception as e:
                            st.warning("Salvo localmente. Falha ao conectar ao webhook de rotinas.")
                    else:
                        st.success("Rotina agendada com sucesso!")

                    st.cache_data.clear()
                    st.rerun()

    st.divider()
    st.markdown("### 🟦 Quadro de Rotinas Ativas")

    # Obter DataFrame de Rotinas (servidor ou sessão local)
    df_rot_exibir = df_rotinas if not df_rotinas.empty else st.session_state.get("rotinas_local", pd.DataFrame())

    if df_rot_exibir.empty:
        st.info("Nenhuma rotina cadastrada ainda. Clique no campo acima para agendar.")
    else:
        # Mapeamento para verificar se a pessoa realizou a inspeção esta semana
        # Obtém o número da semana atual
        semana_atual = datetime.now().isocalendar()[1]
        ano_atual = datetime.now().year

        cols_r = st.columns(2)
        for idx_r, row_r in df_rot_exibir.iterrows():
            nome_resp = row_r.get("responsavel_nome", row_r.get("responsavel", "N/A"))
            email_resp = row_r.get("responsavel_email", "")
            dia_semana_rot = row_r.get("dia_semana", "N/A")
            cat_rot = row_r.get("categoria", "N/A")
            estacao_rot = row_r.get("estacao", "N/A")
            instrucoes_rot = row_r.get("instrucoes", "")

            # Checar se existe registro no banco de dados para essa pessoa nesta semana
            executou_semana = False
            if not df_dados.empty:
                col_auditor = next((c for c in df_dados.columns if "auditor" in c), None)
                col_data = next((c for c in df_dados.columns if "data" in c or "created" in c), None)

                if col_auditor and col_data:
                    for _, row_d in df_dados.iterrows():
                        if str(row_d.get(col_auditor, "")).strip().lower() == str(nome_resp).strip().lower():
                            raw_dt = str(row_d.get(col_data, ""))
                            try:
                                dt_obj = pd.to_datetime(raw_dt)
                                if dt_obj.isocalendar()[1] == semana_atual and dt_obj.year == ano_atual:
                                    executou_semana = True
                                    break
                            except Exception:
                                pass

            with cols_r[idx_r % 2]:
                with st.container(border=True):
                    st.markdown(f"### 🟦 Rotina: {cat_rot}")
                    st.caption(f"**Dia Programado:** 📅 `{dia_semana_rot}`")
                    st.write(f"👤 **Responsável:** {nome_resp}")
                    st.write(f"📧 **E-mail:** `{email_resp}`")
                    st.write(f"📍 **Setor / Área:** {estacao_rot}")
                    if instrucoes_rot:
                        st.write(f"📝 **Instruções:** {instrucoes_rot}")

                    st.divider()

                    if executou_semana:
                        st.success("✅ **Status desta semana:** Tarefa Executada")
                    else:
                        st.error("❌ **Status desta semana:** Pendente / Não Executada")

# --- ABA 4: DASHBOARD ---
with aba4:
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
