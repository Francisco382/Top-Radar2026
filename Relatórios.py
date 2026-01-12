elif pagina == "Relatórios":    
    # 1. Busca os dados brutos
    conn = sqlite3.connect('top_radar.db')
    df_bruto = pd.read_sql("SELECT * FROM tabulacoes", conn)
    conn.close()

    if not df_bruto.empty:
        # Preparação das datas para o filtro (converte texto para data real)
        df_bruto['dt_objeto'] = pd.to_datetime(df_bruto['data_registro'], format="%d/%m/%Y %H:%M:%S").dt.date
        
        # --- SEÇÃO DE FILTROS ---
        st.sidebar.subheader("🎯 Filtros do Relatório")
        
        # Filtro por Vendedor
        lista_vendedores = df_bruto['vendedor'].unique().tolist()
        vendedores_sel = st.sidebar.multiselect("Selecionar Vendedores", lista_vendedores, default=lista_vendedores)
        
        # Filtro por Período
        col_d1, col_d2 = st.sidebar.columns(2)
        data_ini = col_d1.date_input("Início", datetime.now() - timedelta(days=7))
        data_fim = col_d2.date_input("Fim", datetime.now())

        # 2. APLICAÇÃO DOS FILTROS NO DATAFRAME
        df = df_bruto[
            (df_bruto['vendedor'].isin(vendedores_sel)) & 
            (df_bruto['dt_objeto'] >= data_ini) & 
            (df_bruto['dt_objeto'] <= data_fim)
        ]

        if not df.empty:
            # --- MÉTRICAS ---
            col1, col2, col3, col4 = st.columns(4)
            vendas = len(df[df['tipo'] == 'Venda'])
            nao_vendas = len(df[df['tipo'] == 'Não Venda'])
            agendamentos = len(df[df['tipo'] == 'Agendamento'])
            taxa = (vendas / len(df)) * 100
            
            col1.metric("Vendas no Período", vendas)
            col2.metric("Não Vendas", nao_vendas)
            col3.metric("Agendamentos", agendamentos)
            col4.metric("Conversão", f"{taxa:.1f}%")

            st.divider()

            # --- ANÁLISE VISUAL ---
            col_esq, col_dir = st.columns(2)
            with col_esq:
                st.subheader("Mix de Produtos")
                st.bar_chart(df[df['tipo'] == 'Venda']['produto'].value_counts())
            with col_dir:
                st.subheader("Motivos de Perda")
                st.bar_chart(df[df['tipo'] == 'Não Venda']['motivo'].value_counts())

            # --- EXPORTAÇÃO ---
            st.divider()
            # Botão de Excel usando apenas os dados FILTRADOS
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Relatorio_Filtrado')
            
            st.download_button(
                label="📥 Baixar Dados Filtrados (Excel)",
                data=output.getvalue(),
                file_name=f"relatorio_topradar_filtrado.xlsx",
                mime="application/vnd.ms-excel"
            )
            
            st.write("### Detalhes dos Registros Filtrados")
            st.dataframe(df.drop(columns=['dt_objeto']), use_container_width=True)
        else:
            st.warning("Nenhum dado encontrado para os filtros selecionados.")
    else:
        st.info("O banco de dados de tabulações está vazio.")