# --- SECCIÓN DE GRÁFICOS DE RENDIMIENTO (DISEÑO VERTICAL) ---
st.markdown("<br>", unsafe_allow_html=True)

# 1. Gráfico de Ranking (Ancho Completo)
st.markdown("### 🏆 Ranking de Producción Acumulada por Persona")
if not df_filtrado_persona.empty:
    # Agrupa usando el acumulado histórico (ignora la fecha)
    ranking_df = df_filtrado_persona.groupby("Persona").size().reset_index(name="Cajas_Producidas").sort_values(by="Cajas_Producidas", ascending=True)
    
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
    
    # Configuración segura del gráfico
    fig_ranking.update_layout(
        margin=dict(l=200, r=25, t=10, b=20), 
        height=altura_dinamica
    )
    # Configuración limpia del eje vertical
    fig_ranking.update_yaxes(
        type='category'
    )
    st.plotly_chart(fig_ranking, use_container_width=True)
else:
    st.info("No hay datos disponibles para generar el ranking.")

st.markdown("<br>", unsafe_allow_html=True)

# 2. Gráfico de Progreso de Metas (Ancho Completo, debajo del Ranking)
st.markdown("### 🎯 Progreso de Metas e Historial")
if not df_filtrado_persona.empty:
    evolucion_diaria = df_filtrado_persona.groupby(df_filtrado_persona["Fecha"].dt.date).size().reset_index(name="Cajas_Por_Dia")
    evolucion_diaria["Fecha"] = pd.to_datetime(evolucion_diaria["Fecha"])
    evolucion_diaria = evolucion_diaria.sort_values(by="Fecha")
    evolucion_diaria["Cajas_Acumuladas"] = evolucion_diaria["Cajas_Por_Dia"].cumsum()
    
    fig_lineas = px.line(
        evolucion_diaria, 
        x="Fecha", 
        y="Cajas_Acumuladas", 
        markers=True,
        color_discrete_sequence=["#1A365D"]
    )
    fig_lineas.update_layout(
        xaxis=dict(type='date', tickformat='%Y-%m-%d'),
        margin=dict(l=40, r=40, t=10, b=20),
        height=400  # Altura fija ideal para visualización horizontal
    )
    st.plotly_chart(fig_lineas, use_container_width=True)
else:
    st.info("No hay datos históricos disponibles.")
