# --- REEMPLAZA EL BLOQUE DE "col_graf1" POR ESTE CÓDIGO CORREGIDO ---

with col_graf1:
    st.markdown("### 🏆 Ranking de Producción Acumulada por Persona")
    if not df_filtrado_persona.empty:
        # Agrupa usando 'df_filtrado_persona' entero para mostrar el histórico acumulado sin importar el día lateral seleccionado
        ranking_df = df_filtrado_persona.groupby("Persona").size().reset_index(name="Cajas_Producidas").sort_values(by="Cajas_Producidas", ascending=True)
        
        # Altura dinámica del gráfico para que la lista crezca con los operarios sin colapsar las barras
        cant_operarios = len(ranking_df)
        altura_dinamica = int(max(400, 150 + (cant_operarios * 30)))
        
        fig_ranking = px.bar(
            ranking_df, 
            x="Cajas_Producidas", 
            y="Persona", 
            orientation="h", 
            color="Cajas_Producidas", 
            color_continuous_scale=["#1A365D", "#2E7D32"]
        )
        
        # 1. Configuración de márgenes, dimensiones y comportamiento general
        fig_ranking.update_layout(
            margin=dict(l=200, r=25, t=10, b=20), 
            height=altura_dinamica
        )
        
        # 2. Configuración segura del eje Y (Aquí estaba el error de validación)
        fig_ranking.update_yaxes(
            autorange="ascending",
            dtick=1  # Obliga a mostrar cada etiqueta/operario consecutivamente sin saltarse filas
        )
        
        st.plotly_chart(fig_ranking, use_container_width=True)
    else:
        st.info("No hay datos disponibles para generar el ranking.")
