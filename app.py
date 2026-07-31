import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.express as px
import plotly.graph_objects as go

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Dashboard de Producción - Proceso Clasificación",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
    <style>
    .stApp { background-color: #F1F5F9; }
    section[data-testid="stSidebar"] { background-color: #2D3748 !important; }
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p { color: #F8FAFC !important; }

    section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
        background-color: #1A202C !important;
        color: #FFFFFF !important;
        border-color: #4A5568 !important;
    }

    .header-banner {
        background: linear-gradient(135deg, #1A365D 0%, #0F172A 100%);
        color: white;
        padding: 22px 28px;
        border-radius: 14px;
        margin-bottom: 25px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .logo-consorcio { color: #FFFFFF; font-weight: 800; font-size: 26px; }
    .logo-prosyc { color: #4ADE80; font-weight: 800; font-size: 26px; }
    .header-subtitle {
        font-size: 12px;
        color: #94A3B8;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        text-align: right;
        font-weight: 600;
    }

    .kpi-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-left: 5px solid #1A365D;
        border-radius: 12px;
        padding: 16px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        height: 100%;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
    }
    .kpi-title { font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: #64748B; font-weight: 700; }
    .kpi-value { font-size: 26px; font-weight: 800; color: #0F172A; margin: 4px 0; }
    .kpi-subtext { font-size: 11px; color: #64748B; }

    div.stButton > button, div.stDownloadButton > button { border-radius: 8px; font-weight: 600; }
    </style>
""", unsafe_allow_html=True)

MESES_ESPANOL = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

# --- 3. CARGA DE DATOS DESDE GOOGLE SHEETS ---
@st.cache_data(ttl=10)
def cargar_datos_reales():
    try:
        url = "https://docs.google.com/spreadsheets/d/1ld0sxAyU9mYhQ69yv6w2d4sWhK8QW4E0XZlz4hYMhfA/export?format=csv&gid=990786706"
        df = pd.read_csv(url)
        
        df.columns = [col.strip().lower().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u') for col in df.columns]
        
        col_fecha = next((c for c in df.columns if c in ['fecha', 'dia']), None)
        if not col_fecha:
            col_fecha = next((c for c in df.columns if 'fecha' in c or 'dia' in c), df.columns[0])
        
        col_persona = next((c for c in df.columns if c in ['persona', 'operario']), None)
        if not col_persona:
            col_persona = next((c for c in df.columns if any(x in c for x in ['persona', 'operario', 'nombre', 'usuario', 'empleado'])), df.columns[1])
        
        col_cajas = next((c for c in df.columns if any(x in c for x in ['cajas_identidad', 'caja_identidad', 'identidad'])), None)
        if not col_cajas:
            col_cajas = next((c for c in df.columns if any(x in c for x in ['caja', 'produc', 'rendi', 'total', 'cant'])), df.columns[2])
        
        df = df.rename(columns={col_fecha: "Fecha", col_persona: "Persona", col_cajas: "Cajas_Identidad"})
        df["Fecha"] = pd.to_datetime(df["Fecha"], dayfirst=True, errors='coerce')
        
        # Limpieza suave de espacios antes de dar formato
        df["Persona"] = df["Persona"].astype(str).str.strip().str.title().fillna("No Asignado")
        df["Cajas_Identidad_Num"] = df["Cajas_Identidad"].astype(str).str.extract(r'(\d+)').astype(float).fillna(0).astype(int)
        
        df = df.dropna(subset=["Fecha"])
        
        # Permitir hasta el final del día de hoy para no descartar registros de la jornada actual
        hoy_fin = pd.Timestamp.now().floor('D') + pd.Timedelta(days=1)
        df = df[df["Fecha"] < hoy_fin]
        
        return df.sort_values(by="Fecha")
    except Exception as e:
        st.sidebar.error(f"❌ Error al mapear Hoja Principal: {str(e)}")
        np.random.seed(42)
        personas = ["Yamith Marín", "Andres Felipe Riveros", "Monica Hernandez Morales"]
        fechas = pd.date_range(start="2026-05-01", end="2026-05-10", freq="D")
        records = []
        for i, fecha in enumerate(fechas):
            for persona in personas:
                records.append({"Fecha": fecha, "Persona": persona, "Cajas_Identidad": f"Caja {3300 + (i * 10)}"})
        df_backup = pd.DataFrame(records)
        df_backup["Cajas_Identidad_Num"] = df_backup["Cajas_Identidad"].astype(str).str.extract(r'(\d+)').astype(float).fillna(0).astype(int)
        return df_backup

@st.cache_data(ttl=10)
def cargar_datos_estados():
    try:
        url_estados = "https://docs.google.com/spreadsheets/d/1ld0sxAyU9mYhQ69yv6w2d4sWhK8QW4E0XZlz4hYMhfA/gviz/tq?tqx=out:csv&sheet=Estados"
        df_est = pd.read_csv(url_estados)
        df_est.columns = [col.strip() for col in df_est.columns]
        df_est = df_est.dropna(subset=["Fecha"]).copy()
        df_est["Fecha"] = pd.to_datetime(df_est["Fecha"], dayfirst=True, errors='coerce')
        
        hoy_fin = pd.Timestamp.now().floor('D') + pd.Timedelta(days=1)
        df_est = df_est[df_est["Fecha"] < hoy_fin]
        
        for col in ["TRD", "TP", "VIG", "FA"]:
            df_est[col] = pd.to_numeric(df_est[col], errors='coerce').fillna(0).astype(int) if col in df_est.columns else 0
        
        return df_est.dropna(subset=["Fecha"]).sort_values(by="Fecha")
    except Exception as e:
        st.sidebar.error(f"❌ Error al mapear Hoja Estados: {str(e)}")
        return pd.DataFrame(columns=["Fecha", "TRD", "TP", "VIG", "FA"])

# --- CARGA INICIAL DE DATOS ---
df_raw = cargar_datos_reales()
df_estados_raw = cargar_datos_estados()

# --- CONSTANTES DE METAS ---
META_DIARIA_INDIVIDUAL = 3
META_MENSUAL_EQUIPO = 2400
META_GLOBAL_PROYECTO = 36099

# --- BARRA LATERAL (SIDEBAR / PANEL DE CONTROL) ---
with st.sidebar:
    # --- LOGO INTEGRADO EN EL SIDEBAR ---
    st.image("LOGO-PROTECH.jpg", use_container_width=True)
    st.title("Panel de Control")
    st.caption("Datos sincronizados en tiempo real")

    if st.button("🔄 Sincronizar Google Sheets", key="sync_btn", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    
    # Limpieza de personas evitando coincidencias parciales con nombres/apellidos
    palabras_ruido = ["humedad", "observacion", "comentario", "error", "vacio", "no asignado", "nan", "prueba"]
    patron_ruido = r'\b(' + '|'.join(palabras_ruido) + r')\b'
    
    df_limpio = df_raw[
        (df_raw["Persona"].notna()) & 
        (df_raw["Persona"].str.strip() != "") & 
        (df_raw["Persona"] != "No Asignado") & 
        (~df_raw["Persona"].str.lower().str.contains(patron_ruido, regex=True)) & 
        (df_raw["Persona"].str.len() < 80)
    ].copy()

    df_limpio["Anio_Mes"] = df_limpio["Fecha"].dt.to_period("M")

    lista_personas = ["Todos"] + sorted(list(df_limpio["Persona"].unique()))
    persona_seleccionada = st.selectbox("Seleccionar Operario:", lista_personas)

    if persona_seleccionada != "Todos":
        df_op_info = df_limpio[df_limpio["Persona"] == persona_seleccionada]
        if not df_op_info.empty:
            p_registro = df_op_info["Fecha"].min().strftime('%Y-%m-%d')
            u_registro = df_op_info["Fecha"].max().strftime('%Y-%m-%d')
            st.info(f"📌 **Periodo ({persona_seleccionada}):**\n- **Inicio:** `{p_registro}`\n- **Último:** `{u_registro}`")

    fechas_disponibles_dt = sorted(list(df_limpio["Fecha"].unique()))
    fechas_disponibles_str = [pd.to_datetime(f).strftime('%Y-%m-%d') for f in fechas_disponibles_dt]

    if fechas_disponibles_str:
        ultima_fecha_str = pd.to_datetime(df_limpio["Fecha"].max()).strftime('%Y-%m-%d')
        index_defecto = fechas_disponibles_str.index(ultima_fecha_str) if ultima_fecha_str in fechas_disponibles_str else len(fechas_disponibles_str) - 1
        fecha_seleccionada_str = st.selectbox("Seleccionar Día Específico:", fechas_disponibles_str, index=index_defecto)
        fecha_seleccionada = pd.to_datetime(fecha_seleccionada_str)
    else:
        fecha_seleccionada = None

    # REPORTE DE DESCARGA
    st.markdown("---")
    st.subheader("📥 Exportar Reporte")
    
    tipo_filtro_reporte = st.selectbox(
        "🔍 Búsqueda Avanzada / Filtro:",
        ["Primer al Último Registro (Histórico)", "Por Mes", "Por Día Específico"],
        key="tipo_filtro_reporte"
    )

    df_base_descarga = df_limpio if persona_seleccionada == "Todos" else df_limpio[df_limpio["Persona"] == persona_seleccionada]

    if tipo_filtro_reporte == "Por Mes":
        periodos_disponibles = sorted(list(df_base_descarga["Anio_Mes"].unique()), reverse=True)
        opciones_meses = [f"{MESES_ESPANOL[p.month]} {p.year}" for p in periodos_disponibles]
        
        if opciones_meses:
            mes_seleccionado_txt = st.selectbox("Seleccionar Mes a Exportar:", opciones_meses)
            idx_mes = opciones_meses.index(mes_seleccionado_txt)
            periodo_elegido = periodos_disponibles[idx_mes]
            
            df_exportar = df_base_descarga[df_base_descarga["Anio_Mes"] == periodo_elegido]
            nombre_sufijo = f"mes_{periodo_elegido.strftime('%Y_%m')}"
        else:
            df_exportar = pd.DataFrame()
            nombre_sufijo = "mes"

    elif tipo_filtro_reporte == "Por Día Específico":
        if fechas_disponibles_str:
            dia_reporte_str = st.selectbox("Seleccionar Día a Exportar:", fechas_disponibles_str, key="dia_rep")
            df_exportar = df_base_descarga[df_base_descarga["Fecha"] == pd.to_datetime(dia_reporte_str)]
            nombre_sufijo = f"dia_{dia_reporte_str}"
        else:
            df_exportar = pd.DataFrame()
            nombre_sufijo = "dia"
    else:
        df_exportar = df_base_descarga
        nombre_sufijo = "completo"

    if not df_exportar.empty:
        df_csv = df_exportar[["Fecha", "Persona", "Cajas_Identidad"]].copy()
        df_csv["Fecha"] = df_csv["Fecha"].dt.strftime('%Y-%m-%d')
        csv_bytes = df_csv.to_csv(index=False).encode('utf-8-sig')
        
        nombre_persona_slug = persona_seleccionada.lower().replace(' ', '_')
        
        st.download_button(
            label=f"📊 Descargar Reporte ({len(df_exportar)} reg.)",
            data=csv_bytes,
            file_name=f"reporte_{nombre_persona_slug}_{nombre_sufijo}.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        st.warning("Sin datos para los filtros seleccionados.")

# --- FILTRADO Y VISTA DASHBOARD ---
df_filtrado_persona = df_limpio if persona_seleccionada == "Todos" else df_limpio[df_limpio["Persona"] == persona_seleccionada]

if fecha_seleccionada is not None:
    df_filtrado_dia = df_filtrado_persona[df_filtrado_persona["Fecha"] == fecha_seleccionada]
    total_cajas_dia = len(df_filtrado_dia)
else:
    df_filtrado_dia = pd.DataFrame()
    total_cajas_dia = 0

if not df_limpio.empty:
    fecha_base_mes = fecha_seleccionada if fecha_seleccionada is not None else df_limpio["Fecha"].max()
    mes_actual = fecha_base_mes.month
    anio_actual = fecha_base_mes.year
    
    df_mes_actual = df_limpio[
        (df_limpio["Fecha"].dt.month == mes_actual) & 
        (df_limpio["Fecha"].dt.year == anio_actual)
    ]
    total_acumulado_mes_actual = len(df_mes_actual)
    nombre_mes_kpi = MESES_ESPANOL.get(mes_actual, "MES ACTUAL").upper()
else:
    total_acumulado_mes_actual = 0
    nombre_mes_kpi = "MES"

total_acumulado_proyecto = int(df_limpio["Cajas_Identidad_Num"].max()) if not df_limpio.empty else 0

# --- BANNER PRINCIPAL ---
st.markdown("""
    <div class="header-banner">
        <div>
            <span class="logo-consorcio">Consorcio</span> <span class="logo-prosyc">Prosyc</span>
        </div>
        <div class="header-subtitle">
            Dashboard Ejecutivo de Producción<br>
            <span style="font-size: 11px; color: #CBD5E1;">Proceso: Clasificación de Documentos | Contrato 2026</span>
        </div>
    </div>
""", unsafe_allow_html=True)

# --- TARJETAS DE KPIS PRINCIPALES ---
col1, col2, col3, col4 = st.columns(4)
fecha_str = fecha_seleccionada.strftime('%Y-%m-%d') if fecha_seleccionada else ""

with col1:
    st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #1A365D;">
            <div class="kpi-title">Producción del Día ({fecha_str})</div>
            <div class="kpi-value">{total_cajas_dia} Cajas</div>
            <div class="kpi-subtext">Registradas en el sistema</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    avance_mensual = (total_acumulado_mes_actual / META_MENSUAL_EQUIPO) * 100 if META_MENSUAL_EQUIPO > 0 else 0
    st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #2E7D32;">
            <div class="kpi-title">Avance Meta Mensual ({nombre_mes_kpi})</div>
            <div class="kpi-value">{avance_mensual:.1f}%</div>
            <div class="kpi-subtext">{total_acumulado_mes_actual:,} de {META_MENSUAL_EQUIPO:,} Cajas</div>
        </div>
    """, unsafe_allow_html=True)

with col3:
    avance_global = (total_acumulado_proyecto / META_GLOBAL_PROYECTO) * 100 if META_GLOBAL_PROYECTO > 0 else 0
    st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #0284C7;">
            <div class="kpi-title">Avance Global Real</div>
            <div class="kpi-value">{avance_global:.2f}%</div>
            <div class="kpi-subtext">Caja {total_acumulado_proyecto:,} de {META_GLOBAL_PROYECTO:,}</div>
        </div>
    """, unsafe_allow_html=True)

with col4:
    if not df_filtrado_dia.empty:
        conteo_diario_personas = df_filtrado_dia.groupby("Persona").size().reset_index(name="Cajas")
        num_criticos = len(conteo_diario_personas[conteo_diario_personas["Cajas"] < META_DIARIA_INDIVIDUAL])
    else:
        num_criticos = 0
        
    st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #EF4444;">
            <div class="kpi-title">Alertas Bajo Rendimiento</div>
            <div class="kpi-value" style="color: #EF4444;">{num_criticos} Pers.</div>
            <div class="kpi-subtext">Menos de {META_DIARIA_INDIVIDUAL} cajas/día</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- RANKING DE PRODUCCIÓN POR OPERARIO Y MES ---
with st.container(border=True):
    col_rank_head, col_rank_filter = st.columns([0.65, 0.35])
    with col_rank_head:
        st.markdown("### 🏆 Ranking de Producción por Operario")
    with col_rank_filter:
        periodos_rank = sorted(list(df_limpio["Anio_Mes"].unique()), reverse=True)
        opciones_meses_rank = ["Todos los Meses"] + [f"{MESES_ESPANOL[p.month]} {p.year}" for p in periodos_rank]
        mes_rank_sel = st.selectbox("📅 Seleccionar Mes para Ranking:", opciones_meses_rank, key="rank_mes_sel")

    if mes_rank_sel != "Todos los Meses":
        idx_mes_rank = opciones_meses_rank.index(mes_rank_sel) - 1
        periodo_rank_elegido = periodos_rank[idx_mes_rank]
        df_ranking_base = df_filtrado_persona[df_filtrado_persona["Anio_Mes"] == periodo_rank_elegido]
    else:
        df_ranking_base = df_filtrado_persona

    if not df_ranking_base.empty:
        ranking_df = df_ranking_base.groupby("Persona").size().reset_index(name="Cajas_Producidas").sort_values(by="Cajas_Producidas", ascending=True)
        altura_dinamica = int(max(450, 150 + (len(ranking_df) * 35)))
        
        fig_ranking = px.bar(
            ranking_df, x="Cajas_Producidas", y="Persona", orientation="h",
            color="Cajas_Producidas", text="Cajas_Producidas",
            color_continuous_scale=["#1A365D", "#2E7D32"]
        )
        fig_ranking.update_traces(texttemplate='%{text}', textposition='outside')
        fig_ranking.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=220, r=60, t=10, b=20), height=altura_dinamica,
            xaxis=dict(showgrid=True, gridcolor="#E2E8F0"), 
            yaxis=dict(type='category', showgrid=False, dtick=1)
        )
        st.plotly_chart(fig_ranking, use_container_width=True)
    else:
        st.info("No hay datos disponibles para el mes o filtro seleccionado.")

st.markdown("<br>", unsafe_allow_html=True)

# --- GRÁFICO HISTÓRICO ---
with st.container(border=True):
    st.markdown("### 🎯 Progreso de Metas e Historial")
    if not df_filtrado_persona.empty:
        evolucion_diaria = df_filtrado_persona.groupby(df_filtrado_persona["Fecha"].dt.date).size().reset_index(name="Cajas_Por_Dia")
        evolucion_diaria["Fecha"] = pd.to_datetime(evolucion_diaria["Fecha"])
        evolucion_diaria = evolucion_diaria.sort_values(by="Fecha")
        evolucion_diaria["Cajas_Acumuladas"] = evolucion_diaria["Cajas_Por_Dia"].cumsum()
        
        fig_lineas = px.area(evolucion_diaria, x="Fecha", y="Cajas_Acumuladas", markers=True, color_discrete_sequence=["#1A365D"])
        fig_lineas.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(type='date', tickformat='%Y-%m-%d', showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="#E2E8F0"),
            margin=dict(l=40, r=40, t=10, b=20), height=380
        )
        st.plotly_chart(fig_lineas, use_container_width=True)
    else:
        st.info("No hay datos históricos disponibles.")

st.markdown("<br>", unsafe_allow_html=True)

# --- CONSOLIDADO DE ESTADOS ---
with st.container(border=True):
    st.markdown("## 📊 Consolidado Estados")
    st.caption("Avance Diario e Histórico Consecutivo")

    if not df_estados_raw.empty:
        df_estados_sorted = df_estados_raw.sort_values(by="Fecha")
        ultimo_registro = df_estados_sorted.iloc[-1]
        fecha_reciente = pd.to_datetime(ultimo_registro['Fecha']).strftime('%Y-%m-%d')
        
        st.markdown(f"**📅 Último Estado Reportado en Sheets:** `{fecha_reciente}`")
        
        me1, me2, me3, me4 = st.columns(4)
        me1.metric(label="TRD", value=f"{int(ultimo_registro['TRD'])}")
        me2.metric(label="TP", value=f"{int(ultimo_registro['TP'])}")
        me3.metric(label="VIG", value=f"{int(ultimo_registro['VIG'])}")
        me4.metric(label="FA", value=f"{int(ultimo_registro['FA'])}")
            
        st.markdown("#### 📈 Comportamiento y Evolución Diaria de los Estados")
        
        fig_estados = px.line(
            df_estados_sorted, x="Fecha", y=["TRD", "TP", "VIG", "FA"],
            labels={"value": "Cantidad", "Fecha": "Fecha", "variable": "Estado"},
            markers=True, color_discrete_sequence=["#1A365D", "#2E7D32", "#F59E0B", "#EF4444"]
        )
        fig_estados.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=10, b=20),
            xaxis=dict(type='date', tickformat='%Y-%m-%d', showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="#E2E8F0")
        )
        st.plotly_chart(fig_estados, use_container_width=True)
        
        with st.expander("🔍 Ver historial de registros diarios (Tabla)"):
            df_tabla_ver = df_estados_sorted.copy()
            df_tabla_ver["Fecha"] = df_tabla_ver["Fecha"].dt.strftime('%Y-%m-%d')
            st.dataframe(df_tabla_ver, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ No se pudieron recuperar datos en la pestaña 'Estados' de tu Google Sheets.")

# --- DETALLE Y REVISIÓN DE REGISTROS ---
st.markdown("<br>", unsafe_allow_html=True)
with st.expander("📄 Ver detalle de datos procesados (Tabla de Operarios)"):
    if not df_filtrado_persona.empty:
        df_detalle = df_filtrado_persona[["Fecha", "Persona", "Cajas_Identidad"]].copy()
        df_detalle["Fecha"] = df_detalle["Fecha"].dt.strftime('%Y-%m-%d')
        st.dataframe(df_detalle, use_container_width=True, hide_index=True)
    else:
        st.info("No hay datos de operarios registrados para los filtros seleccionados.")
