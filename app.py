import streamlit as st
import pandas as pd
import numpy as np
import datetime
import io
import plotly.express as px
import plotly.graph_objects as go

# Librerías para generación de PDF
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

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
    .stApp {
        background-color: #E2E8F0 !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #0F172A !important;
    }
    section[data-testid="stSidebar"] * {
        color: #E2E8F0 !important;
    }
    .header-banner {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        color: white;
        padding: 24px 32px;
        border-radius: 16px;
        margin-bottom: 25px;
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.2);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .logo-consorcio { color: #FFFFFF; font-weight: 800; font-size: 28px; }
    .logo-prosyc { color: #22C55E; font-weight: 800; font-size: 28px; }
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
        border-radius: 14px;
        padding: 20px;
        border-left: 6px solid #1E3A8A;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
        height: 100%;
    }
    .kpi-title {
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #64748B;
        font-weight: 700;
    }
    .kpi-value {
        font-size: 28px;
        font-weight: 800;
        color: #0F172A;
        margin: 6px 0;
    }
    .kpi-subtext {
        font-size: 12px;
        color: #64748B;
    }
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        background-color: #FFFFFF !important;
        border-radius: 16px !important;
        border: 1px solid #CBD5E1 !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08) !important;
        padding: 22px !important;
    }
    div.stButton > button, div.stDownloadButton > button {
        border-radius: 8px;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

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
        df["Persona"] = df["Persona"].astype(str).str.strip().str.title().fillna("No Asignado")
        df["Cajas_Identidad_Num"] = df["Cajas_Identidad"].astype(str).str.extract(r'(\d+)').astype(float).fillna(0).astype(int)
        
        df = df.dropna(subset=["Fecha"])
        hoy = pd.Timestamp.now().normalize()
        df = df[df["Fecha"] <= hoy]
        
        return df.sort_values(by="Fecha")
    except Exception as e:
        st.sidebar.error(f"❌ Error al mapear Hoja Principal: {str(e)}")
        personas = ["Yamith Marín", "Andres Felipe Riveros", "Adriana Patricia Riano Medina"]
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
        
        hoy = pd.Timestamp.now().normalize()
        df_est = df_est[df_est["Fecha"] <= hoy]
        
        for col in ["TRD", "TP", "VIG", "FA"]:
            if col in df_est.columns:
                df_est[col] = pd.to_numeric(df_est[col], errors='coerce').fillna(0).astype(int)
            else:
                df_est[col] = 0
                
        return df_est.dropna(subset=["Fecha"]).sort_values(by="Fecha")
    except Exception as e:
        st.sidebar.error(f"❌ Error al mapear Hoja Estados: {str(e)}")
        return pd.DataFrame(columns=["Fecha", "TRD", "TP", "VIG", "FA"])

# --- FUNCION AUXILIAR: GENERAR PDF ---
def generar_pdf_reporte(df_data, nombre_operario):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    story = []
    styles = getSampleStyleSheet()
    
    # Estilos personalizados
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'DocSubTitle',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#64748B'),
        spaceAfter=15
    )
    
    # Encabezado del PDF
    story.append(Paragraph("Consorcio Prosyc - Reporte de Producción", title_style))
    story.append(Paragraph(f"<b>Filtro:</b> {nombre_operario} | <b>Fecha de emisión:</b> {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", subtitle_style))
    story.append(Spacer(1, 10))
    
    # Construcción de la Tabla de Datos
    tabla_datos = [["Fecha", "Operario / Persona", "Identificación Caja"]]
    for _, row in df_data.iterrows():
        fecha_str = row['Fecha'].strftime('%Y-%m-%d') if isinstance(row['Fecha'], pd.Timestamp) else str(row['Fecha'])
        tabla_datos.append([fecha_str, str(row['Persona']), str(row['Cajas_Identidad'])])
    
    # Estilo visual de la Tabla
    t = Table(tabla_datos, colWidths=[120, 240, 180])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E293B')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8FAFC')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#CBD5E1')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
    ]))
    
    story.append(t)
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# --- CARGA INICIAL DE DATOS ---
df_raw = cargar_datos_reales()
df_estados_raw = cargar_datos_estados()

# --- CONSTANTES DE METAS ---
META_DIARIA_INDIVIDUAL = 3
META_MENSUAL_EQUIPO = 2400
META_GLOBAL_PROYECTO = 36099

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/771/771239.png", width=70)
    st.title("Panel de Control")
    st.caption("Datos sincronizados en tiempo real")
    
    st.info("Columnas detectadas:\n- Fecha: `Fecha` \n- Operario: `Persona` \n- Identidad Caja: `Cajas_Identidad`")

    if st.button("🔄 Sincronizar Google Sheets", key="sync_btn", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    
    # Limpieza de operarios
    palabras_ruido = ["humedad", "observacion", "comentario", "error", "vacio", "no asignado", "nan", "prueba"]
    df_limpio = df_raw[
        (df_raw["Persona"].notna()) & 
        (df_raw["Persona"] != "") &
        (df_raw["Persona"] != "No Asignado") &
        (~df_raw["Persona"].str.lower().str.contains('|'.join(palabras_ruido))) &
        (df_raw["Persona"].str.len() < 45)
    ].copy()

    lista_personas = ["Todos"] + sorted(list(df_limpio["Persona"].unique()))
    persona_seleccionada = st.selectbox("Seleccionar Operario:", lista_personas)

    fechas_disponibles_dt = sorted(list(df_limpio["Fecha"].unique()))
    fechas_disponibles_str = [pd.to_datetime(f).strftime('%Y-%m-%d') for f in fechas_disponibles_dt]

    if fechas_disponibles_str:
        ultima_fecha_str = pd.to_datetime(df_limpio["Fecha"].max()).strftime('%Y-%m-%d')
        index_defecto = fechas_disponibles_str.index(ultima_fecha_str) if ultima_fecha_str in fechas_disponibles_str else len(fechas_disponibles_str) - 1
        fecha_seleccionada_str = st.selectbox("Seleccionar Día Específico:", fechas_disponibles_str, index=index_defecto)
        fecha_seleccionada = pd.to_datetime(fecha_seleccionada_str)
    else:
        fecha_seleccionada = None

    # --- MÓDULO DE DESCARGA (EXCEL Y PDF) ---
    st.markdown("---")
    st.subheader("📥 Descargar Reporte")
    
    df_exportar = df_limpio if persona_seleccionada == "Todos" else df_limpio[df_limpio["Persona"] == persona_seleccionada]
    
    formato_descarga = st.radio("Formato de exportación:", ["Excel (.xlsx)", "PDF Documento (.pdf)"], key="format_download")
    
    if formato_descarga == "Excel (.xlsx)":
        output = io.BytesIO()
        df_excel = df_exportar[["Fecha", "Persona", "Cajas_Identidad"]].copy()
        df_excel["Fecha"] = df_excel["Fecha"].dt.strftime('%Y-%m-%d')
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_excel.to_excel(writer, index=False, sheet_name='Reporte_Produccion')
        excel_bytes = output.getvalue()
        
        st.download_button(
            label="📊 Descargar Excel",
            data=excel_bytes,
            file_name=f"reporte_produccion_{persona_seleccionada.lower().replace(' ', '_')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    else:
        pdf_bytes = generar_pdf_reporte(df_exportar, persona_seleccionada)
        
        st.download_button(
            label="📄 Descargar Reporte PDF",
            data=pdf_bytes,
            file_name=f"reporte_produccion_{persona_seleccionada.lower().replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

# --- FILTRADO DE DATOS ---
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
    
    meses_espanol = {
        1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL", 
        5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO", 
        9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"
    }
    nombre_mes_kpi = meses_espanol.get(mes_actual, "MES ACTUAL")
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
        <div class="kpi-card" style="border-left-color: #1E3A8A;">
            <div class="kpi-title">Producción del Día ({fecha_str})</div>
            <div class="kpi-value">{total_cajas_dia} Cajas</div>
            <div class="kpi-subtext">Registradas en el sistema</div>
        </div>
    """, unsafe_allow_html=True)

with col2:
    avance_mensual = (total_acumulado_mes_actual / META_MENSUAL_EQUIPO) * 100 if META_MENSUAL_EQUIPO > 0 else 0
    st.markdown(f"""
        <div class="kpi-card" style="border-left-color: #16A34A;">
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
        <div class="kpi-card" style="border-left-color: #DC2626;">
            <div class="kpi-title">Alertas Bajo Rendimiento</div>
            <div class="kpi-value" style="color: #DC2626;">{num_criticos} Pers.</div>
            <div class="kpi-subtext">Menos de {META_DIARIA_INDIVIDUAL} cajas/día</div>
        </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- SECCIÓN DE GRÁFICOS ---
with st.container(border=True):
    st.markdown("### 🏆 Ranking de Producción Acumulada por Persona")
    if not df_filtrado_persona.empty:
        ranking_df = df_filtrado_persona.groupby("Persona").size().reset_index(name="Cajas_Producidas").sort_values(by="Cajas_Producidas", ascending=True)
        cant_operarios = len(ranking_df)
        altura_dinamica = int(max(400, 150 + (cant_operarios * 30)))
        
        fig_ranking = px.bar(
            ranking_df, x="Cajas_Producidas", y="Persona", orientation="h", color="Cajas_Producidas", text="Cajas_Producidas",
            color_continuous_scale=["#1E3A8A", "#16A34A"]
        )
        fig_ranking.update_traces(texttemplate='%{text}', textposition='outside')
        fig_ranking.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=180, r=60, t=10, b=20), height=altura_dinamica,
            xaxis=dict(showgrid=True, gridcolor="#CBD5E1"), yaxis=dict(type='category', showgrid=False)
        )
        st.plotly_chart(fig_ranking, use_container_width=True)
    else:
        st.info("No hay datos disponibles para generar el ranking.")

st.markdown("<br>", unsafe_allow_html=True)

with st.container(border=True):
    st.markdown("### 🎯 Progreso de Metas e Historial")
    if not df_filtrado_persona.empty:
        evolucion_diaria = df_filtrado_persona.groupby(df_filtrado_persona["Fecha"].dt.date).size().reset_index(name="Cajas_Por_Dia")
        evolucion_diaria["Fecha"] = pd.to_datetime(evolucion_diaria["Fecha"])
        evolucion_diaria = evolucion_diaria.sort_values(by="Fecha")
        evolucion_diaria["Cajas_Acumuladas"] = evolucion_diaria["Cajas_Por_Dia"].cumsum()
        
        fig_lineas = px.area(evolucion_diaria, x="Fecha", y="Cajas_Acumuladas", markers=True, color_discrete_sequence=["#1E3A8A"])
        fig_lineas.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            xaxis=dict(type='date', tickformat='%Y-%m-%d', showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="#CBD5E1"), margin=dict(l=40, r=40, t=10, b=20), height=380
        )
        st.plotly_chart(fig_lineas, use_container_width=True)
    else:
        st.info("No hay datos históricos disponibles.")

st.markdown("<br>", unsafe_allow_html=True)

# --- CONSOLIDADO ESTADOS ---
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
            
        fig_estados = px.line(
            df_estados_sorted, x="Fecha", y=["TRD", "TP", "VIG", "FA"],
            labels={"value": "Cantidad", "Fecha": "Fecha", "variable": "Estado"},
            markers=True, color_discrete_sequence=["#1E3A8A", "#16A34A", "#F59E0B", "#DC2626"]
        )
        fig_estados.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=10, b=20), xaxis=dict(type='date', tickformat='%Y-%m-%d', showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="#CBD5E1")
        )
        st.plotly_chart(fig_estados, use_container_width=True)
        
        with st.expander("🔍 Ver historial de registros diarios (Tabla)"):
            df_tabla_ver = df_estados_sorted.copy()
            df_tabla_ver["Fecha"] = df_tabla_ver["Fecha"].dt.strftime('%Y-%m-%d')
            st.dataframe(df_tabla_ver, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ No se pudieron recuperar datos en la pestaña 'Estados' de tu Google Sheets.")
