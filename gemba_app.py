# --- ABA 3: ROTINAS PROGRAMADAS (TRECHO DE EXCLUSÃO CORRIGIDO) ---
with aba3:
    st.subheader("📅 Programação de Rotinas Gemba")
    st.write("Agende inspeções recorrentes e receba lembretes automáticos por e-mail.")

    # ... [MANTENHA O BLOCO DE CADASTRAR NOVA ROTINA AQUI] ...

    st.divider()
    st.markdown("### 🟦 Quadro de Rotinas Ativas")

    df_rot_exibir = df_rotinas.copy()

    if df_rot_exibir.empty:
        st.info("Nenhuma rotina cadastrada ainda ou o webhook não retornou dados.")
    else:
        semana_atual = datetime.now().isocalendar()[1]
        ano_atual = datetime.now().year

        cols_r = st.columns(2)
        for idx_r, (r_idx, row_r) in enumerate(df_rot_exibir.iterrows()):
            # Captura de IDs para garantir compatibilidade com o SharePoint
            id0_rot = str(row_r.get("id0", ""))
            sp_id_rot = str(row_r.get("id", row_r.get("ID", id0_rot)))
            
            nome_resp = str(row_r.get("responsavel_nome", row_r.get("responsavel", "N/A")))
            email_resp = str(row_r.get("responsavel_email", "Não informado"))
            dia_semana_rot = str(row_r.get("dia_semana", "N/A"))
            cat_rot = str(row_r.get("categoria", "N/A"))
            estacao_rot = str(row_r.get("estacao", "N/A"))
            instrucoes_rot = str(row_r.get("instrucoes", ""))

            executou_semana = False
            if not df_dados.empty:
                col_auditor = next((c for c in df_dados.columns if "auditor" in c or "responsavel" in c), None)
                col_data = next((c for c in df_dados.columns if "data" in c or "created" in c), None)

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
                        btn_delete = st.button("🗑️", key=f"btn_del_rot_{id0_rot}_{r_idx}", help="Excluir esta rotina")

                    if btn_delete:
                        st.session_state[f"confirm_delete_{id0_rot}_{r_idx}"] = True

                    # Confirmação de exclusão dentro do card
                    if st.session_state.get(f"confirm_delete_{id0_rot}_{r_idx}", False):
                        st.warning("Tem certeza que deseja excluir esta rotina do sistema?")
                        col_c1, col_c2 = st.columns(2)
                        with col_c1:
                            if st.button("Sim, Excluir", key=f"sim_del_{id0_rot}_{r_idx}", type="primary"):
                                payload_excluir = {
                                    "id0": id0_rot,
                                    "id": sp_id_rot,
                                    "ID": sp_id_rot
                                }
                                
                                # 1. Disparo ao Power Automate para deletar no Microsoft Lists
                                se_excluiu_remoto = False
                                if WEBHOOK_ROTINAS_EXCLUIR:
                                    try:
                                        with st.spinner("Removendo do Microsoft Lists..."):
                                            res_del = requests.post(WEBHOOK_ROTINAS_EXCLUIR, json=payload_excluir, timeout=12)
                                            if res_del.status_code in [200, 202, 204]:
                                                se_excluiu_remoto = True
                                            else:
                                                st.error(f"Erro no Power Automate ({res_del.status_code}): {res_del.text}")
                                    except Exception as e:
                                        st.error(f"Falha na conexão com o Webhook de exclusão: {e}")
                                else:
                                    st.warning("URL 'POWER_AUTOMATE_ROTINAS_EXCLUIR_URL' não encontrada nos secrets.")

                                # 2. Remoção imediata da memória/sessão para atualização visual instantânea
                                if "rotinas_local" in st.session_state and not st.session_state["rotinas_local"].empty:
                                    st.session_state["rotinas_local"] = st.session_state["rotinas_local"][
                                        (st.session_state["rotinas_local"].get("id0", pd.Series()) != id0_rot) &
                                        (st.session_state["rotinas_local"].get("id", pd.Series()) != sp_id_rot)
                                    ]

                                # Limpa o cache para recarregar da nuvem na próxima atualização
                                st.cache_data.clear()
                                st.session_state.pop(f"confirm_delete_{id0_rot}_{r_idx}", None)
                                st.toast("Rotina excluída com sucesso!", icon="🗑️")
                                st.rerun()

                        with col_c2:
                            if st.button("Cancelar", key=f"cancel_del_{id0_rot}_{r_idx}"):
                                st.session_state[f"confirm_delete_{id0_rot}_{r_idx}"] = False
                                st.rerun()

                    st.write(f"👤 **Responsável pela Rotina:** {nome_resp}")
                    st.write(f"📧 **E-mail para Notificação:** {email_resp}")
                    st.write(f"🏢 **Setor / Área a ser Inspecionada:** {estacao_rot}")
                    st.write(f"📆 **Dia da Semana Fixo:** {dia_semana_rot}")
                    st.write(f"🏷️ **Categoria da Inspeção:** {cat_rot}")
                    
                    if instrucoes_rot and instrucoes_rot.strip() != "" and instrucoes_rot.upper() != "NONE":
                        st.caption(f"📝 **Instruções:** {instrucoes_rot}")

                    if executou_semana:
                        st.success("✅ Rotina Realizada esta Semana!")
                    else:
                        st.warning("⚠️ Pendente de Realização esta Semana")
