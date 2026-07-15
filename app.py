import streamlit as st
import pandas as pd
import numpy as np
import datetime
import plotly.express as px
import plotly.graph_objects as go

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Dashboard de Producción - Proceso Clasificación",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilos CSS de entorno corporativo (Incluye el nuevo diseño elegante del Logo/Encabezado)
st.markdown("""
    <style>
    .main { background-color: #F8F9FA; }
    
    /* Contenedor del encabezado elegante */
    .header-container {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding-bottom: 15px;
        border-bottom: 2px solid #E9ECEF;
        margin-bottom: 25px;
    }
    .logo-text {
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 28px;
        font-weight: 800;
        letter-spacing: 0.5px;
    }
    .logo-consorcio {
        color: #1A365D; /* Azul Marino Formal */
    }
    .logo-prosyc {
        color: #2E7D32; /* Verde Esmeralda Elegante */
    }
    .header-subtitle {
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 13px;
        color: #6C757D;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        font-weight: 600;
        text-align: right;
    }
    
    /* Tarjetas KPI */
    .kpi-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
        border-left: 5px solid #1A365D; /* Azul como color principal de la marca */
    }
    .kpi-title { font-size: 14px; color: #6c757d; font-weight: bold; text-transform: uppercase; }
    .kpi-value { font-size: 28px; font-weight: bold; color: #212529; margin-top: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- CARGA DE DATOS DESDE GOOGLE SHEETS ---
@st.cache_data(ttl=10) # ⚡ Reducido a 10 segundos para actualización en tiempo real sin bloqueos
def cargar_datos_reales():
    try:
        url = "https://docs.google.com/spreadsheets/d/1ld0sxAyU9mYhQ69yv6w2d4sWhK8QW4E0XZlz4hYMhfA/export?format=csv&gid=990786706"
        df = pd.read_csv(url)
        
        # Limpieza básica de nombres de columnas
        df.columns = [col.strip().lower().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u') for col in df.columns]
        
        # Mapeo inteligente con prioridades
        col_fecha = None
        for c in df.columns:
            if 'fecha' in c or 'dia' in c:
                col_fecha = c
                break
        if not col_fecha: col_fecha = df.columns[0]
        
        col_persona = None
        for c in df.columns:
            if 'persona' in c or 'operario' in c or 'nombre' in c or 'usuario' in c or 'empleado' in c:
                col_persona = c
                break
        if not col_persona: col_persona = df.columns[1]
        
        col_cajas = None
        for c in df.columns:
            if 'caja' in c or 'produc' in c or 'rendi' in c or 'total' in c or 'cant' in c:
                col_cajas = c
                break
        if not col_cajas: col_cajas = df.columns[2]
        
        # Renombrar columnas para estandarizarlas
        df = df.rename(columns={col_fecha: "Fecha", col_persona: "Persona", col_cajas: "Cajas_Identidad"})
        
        # Conversión y limpieza estricta de tipos a DateTime real
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors='coerce')
        df["Cajas_Identidad"] = df["Cajas_Identidad"].astype(str).str.strip()
        df["Persona"] = df["Persona"].astype(str).str.strip()
        
        # 💡 Evitamos descartar la fila si falta el nombre del Operario para no alterar el conteo de cajas
        df["Persona"] = df["Persona"].fillna("No Asignado")
        
        # Filtrar únicamente filas donde la Fecha sea totalmente nula
        df = df.dropna(subset=["Fecha"])
        return df[["Fecha", "Persona", "Cajas_Identidad"]]
    except Exception as e:
        st.sidebar.error(f"❌ Error de Conexión. Detalle: {str(e)}")
        # Base de datos simulada de respaldo
        np.random.seed(42)
        personas = ["Yamith Marín", "Operario de Prueba A", "Operario de Prueba B"]
        fechas = pd.date_range(start="2026-05-01", end="2026-05-05", freq="D")
        records = []
        for i, fecha in enumerate(fechas):
            for persona in personas:
                records.append({"Fecha": fecha, "Persona": persona, "Cajas_Identidad": f"Caja-{i}"})
        return pd.DataFrame(records)

# --- CARGA DE LA NUEVA PESTAÑA 'Estados' ---
@st.cache_data(ttl=10) # ⚡ Sincronizado a 10 segundos
def cargar_datos_estados():
    try:
        # Usamos gviz/tq para apuntar directamente a la pestaña "Estados" de manera robusta
        url_estados = "https://docs.google.com/spreadsheets/d/1ld0sxAyU9mYhQ69yv6w2d4sWhK8QW4E0XZlz4hYMhfA/gviz/tq?tqx=out:csv&sheet=Estados"
        df_est = pd.read_csv(url_estados)
        
        # Limpiar nombres de columnas y quitar vacíos
        df_est.columns = [col.strip() for col in df_est.columns]
        df_est = df_est.dropna(subset=["Fecha"]).copy()
        
        df_est["Fecha"] = pd.to_datetime(df_est["Fecha"], errors='coerce')
        df_est["TRD"] = pd.to_numeric(df_est["TRD"], errors='coerce').fillna(0).astype(int)
        df_est["TP"] = pd.to_numeric(df_est["TP"], errors='coerce').fillna(0).astype(int)
        df_est["VIG"] = pd.to_numeric(df_est["VIG"], errors='coerce').fillna(0).astype(int)
        df_est["FA"] = pd.to_numeric(df_est["FA"], errors='coerce').fillna(0).astype(int)
        
        # Filtrar registros sin fecha válida y ordenar cronológicamente
        df_est = df_est.dropna(subset=["Fecha"]).sort_values(by="Fecha")
        return df_est
    except Exception as e:
        return pd.DataFrame(columns=["Fecha", "TRD", "TP", "VIG", "FA"])

df_raw = cargar_datos_reales()
df_estados_raw = cargar_datos_estados()

# --- CONSTANTES ---
META_DIARIA_INDIVIDUAL = 3
META_MENSUAL_EQUIPO = 2400
META_GLOBAL_PROYECTO = 36099

# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/771/771239.png", width=80)
st.sidebar.title("Panel de Control")
st.sidebar.markdown("Datos del archivo de Google Sheets.")

st.sidebar.info(f"Columnas detectadas en tu hoja:\n- Fecha: `{df_raw.columns[0]}`\n- Operario: `{df_raw.columns[1]}`\n- Identidad Caja: `{df_raw.columns[2]}`")

if st.sidebar.button("🔄 Sincronizar Google Sheets"):
    st.cache_data.clear()
    st.rerun()

lista_personas = ["Todos"] + sorted(list(df_raw["Persona"].unique()))
persona_seleccionada = st.sidebar.selectbox("Seleccionar Operario:", lista_personas)

# Mostrar fechas ordenadas cronológicamente en formato legible 'YYYY-MM-DD'
fechas_disponibles_dt = sorted(list(df_raw["Fecha"].unique()))
fechas_disponibles_str = [f.strftime('%Y-%m-%d') for f in fechas_disponibles_dt]

if len(fechas_disponibles_str) > 0:
    fecha_seleccionada_str = st.sidebar.selectbox("Seleccionar Día Específico:", fechas_disponibles_str)
    fecha_seleccionada = pd.to_datetime(fecha_seleccionada_str)
else:
    fecha_seleccionada = None

# Filtrado por Operario
df_filtrado_persona = df_raw if persona_seleccionada == "Todos" else df_raw[df_raw["Persona"] == persona_seleccionada]

# --- NUEVOS CÁLCULOS (CONTEO DE FILAS) ---

# 1. Producción del Día Seleccionado
if fecha_seleccionada:
    df_filtrado_dia = df_filtrado_persona[df_filtrado_persona["Fecha"] == fecha_seleccionada]
    total_cajas_dia = len(df_filtrado_dia)
else:
    total_cajas_dia = 0

# 2. Obtener año y mes actual para la Meta Mensual
hoy = datetime.date.today()
mes_actual = hoy.month
anio_actual = hoy.year

# Contamos los registros del mes actual
df_mes_actual = df_raw[
    (df_raw["Fecha"].dt.month == mes_actual) & 
    (df_raw["Fecha"].dt.year == anio_actual)
]
total_acumulado_mes_actual = len(df_mes_actual)

# Si el mes actual aún no tiene registros, tomamos el último mes con datos
if total_acumulado_mes_actual == 0 and len(df_raw) > 0:
    ultimo_registro_fecha = df_raw["Fecha"].max()
    df_mes_actual = df_raw[
        (df_raw["Fecha"].dt.month == ultimo_registro_fecha.month) & 
        (df_raw["Fecha"].dt.year == ultimo_registro_fecha.year)
    ]
    total_acumulado_mes_actual = len(df_mes_actual)

# 3. Avance Global (Se tasa estrictamente sobre el total de filas físicas de manera directa)
total_acumulado_proyecto = len(df_raw)

# --- DISEÑO DE INTERFAZ CON EL NUEVO LOGO CORPORATIVO ---
st.markdown("""
    <div class="header-container">
        <div class="logo-text">
            <span class="logo-consorcio">Consorcio</span> <span class="logo-prosyc">Prosyc</span>
        </div>
        <div class="header-subtitle">
            Dashboard Ejecutivo de Producción<br>
            <span style="font-size: 11px; color: #ADB5BD;">Proceso: Clasificación de Documentos | Contrato 2026</span>
        </div>
    </div>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1:
    fecha_str = fecha_seleccionada.strftime('%Y-%m-%d') if fecha_seleccionada else ""
    html_kpi1 = '<div class="kpi-card" style="border-left-color: #1A365D;"><div class="kpi-title">Producción del Día ({fecha})</div><div class="kpi-value">{valor} Cajas</div></div>'.format(fecha=fecha_str, valor=total_cajas_dia)
    st.markdown(html_kpi1, unsafe_allow_html=True)
with col2:
    avance_mensual = (total_acumulado_mes_actual / META_MENSUAL_EQUIPO) * 100 if META_MENSUAL_EQUIPO > 0 else 0
    html_kpi2 = '<div class="kpi-card" style="border-left-color: #2E7D32;"><div class="kpi-title">Avance Meta Mensual</div><div class="kpi-value">{porcentaje:.1f}%</div></div>'.format(porcentaje=avance_mensual)
    st.markdown(html_kpi2, unsafe_allow_html=True)
with col3:
    # 🎯 Ajustado con porcentaje a dos decimales y el contador de cajas acumulado/meta para transparencia
    avance_global = (total_acumulado_proyecto / META_GLOBAL_PROYECTO) * 100 if META_GLOBAL_PROYECTO > 0 else 0
    html_kpi3 = """
    <div class="kpi-card" style="border-left-color: #1A365D;">
        <div class="kpi-title">Avance Global</div>
        <div class="kpi-value">{porcentaje:.2f}%</div>
        <div style="font-size: 11px; color: #6C757D; margin-top: 5px;">
            ({acumulado:,} de {meta:,} Cajas)
        </div>
    </div>
    """.format(porcentaje=avance_global, acumulado=total_acumulado_proyecto, meta=META_GLOBAL_PROYECTO)
    st.markdown(html_kpi3, unsafe_allow_html=True)
with col4:
    if fecha_seleccionada:
        conteo_diario_personas = df_filtrado_dia.groupby("Persona").size().reset_index(name="Cajas")
        bajos_rendimientos = conteo_diario_personas[conteo_diario_personas["Cajas"] < META_DIARIA_INDIVIDUAL]
        num_criticos = len(bajos_rendimientos)
    else:
        num_criticos = 0
    html_kpi4 = '<div class="kpi-card" style="border-left-color: #EF553B;"><div class="kpi-title">Alertas Bajo Rendimiento</div><div class="kpi-value" style="color: #EF553B;">{criticos} Pers.</div></div>'.format(criticos=num_criticos)
    st.markdown(html_kpi4, unsafe_allow_html=True)

# --- GRÁFICOS ---
st.markdown("<br>", unsafe_allow_html=True)
col_graf1, col_graf2 = st.columns([3, 2])

with col_graf1:
    st.markdown("### 🏆 Ranking de Producción Acumulada por Persona")
    ranking_df = df_filtrado_persona.groupby("Persona").size().reset_index(name="Cajas_Producidas").sort_values(by="Cajas_Producidas", ascending=True)
    fig_ranking = px.bar(
        ranking_df, 
        x="Cajas_Producidas", 
        y="Persona", 
        orientation="h", 
        color="Cajas_Producidas", 
        color_continuous_scale=["#1A365D", "#2E7D32"] # Colores Corporativos: Azul a Verde
    )
    st.plotly_chart(fig_ranking, use_container_width=True)

with col_graf2:
    st.markdown("### 🎯 Progreso de Metas e Historial")
    # 1. Aseguramos orden cronológico estricto
    df_progreso_sorted = df_filtrado_persona.sort_values(by="Fecha")
    
    # 2. Agrupamos y contamos la producción por día
    evolucion_diaria = df_progreso_sorted.groupby(df_progreso_sorted["Fecha"].dt.date).size().reset_index(name="Cajas_Por_Dia")
    evolucion_diaria["Fecha"] = pd.to_datetime(evolucion_diaria["Fecha"])
    evolucion_diaria = evolucion_diaria.sort_values(by="Fecha")
    
    # 3. CALCULAMOS EL ACUMULADO PROGRESIVO (Suma consecutiva para ascenso continuo)
    evolucion_diaria["Cajas_Acumuladas"] = evolucion_diaria["Cajas_Por_Dia"].cumsum()
    
    # 4. Trazamos la línea acumulada en ascenso
    fig_lineas = px.line(
        evolucion_diaria, 
        x="Fecha", 
        y="Cajas_Acumuladas", 
        markers=True,
        labels={"Cajas_Acumuladas": "Cajas Acumuladas"},
        color_discrete_sequence=["#1A365D"] # Línea principal en color Azul Corporativo
    )
    
    # 5. Configuración limpia del eje X (Evita que se empalmen las etiquetas grises del calendario)
    fig_lineas.update_layout(
        xaxis=dict(
            type='date',
            tickformat='%Y-%m-%d'
        ),
        margin=dict(l=20, r=20, t=10, b=20)
    )
    st.plotly_chart(fig_lineas, use_container_width=True)

# ==============================================================================
# INTEGRACIÓN: 📊 CONSOLIDADO ESTADOS
# ==============================================================================
st.markdown("---")
st.header("📊 Consolidado Estados")
st.subheader("Avance Diario e Histórico Consecutivo")

try:
    if not df_estados_raw.empty:
        df_estados_sorted = df_estados_raw.copy()
        df_estados_sorted["Fecha"] = pd.to_datetime(df_estados_sorted["Fecha"])
        df_estados_sorted = df_estados_sorted.sort_values(by="Fecha")
        
        # Valores del último registro encontrado
        ultimo_registro = df_estados_sorted.iloc[-1]
        fecha_reciente = ultimo_registro['Fecha'].strftime('%Y-%m-%d')
        
        st.markdown(f"##### 📅 Estado del día reportado en Sheets: **{fecha_reciente}**")
        
        # Tarjetas de Métricas Puras
        me1, me2, me3, me4 = st.columns(4)
        with me1:
            st.metric(label="TRD", value=f"{int(ultimo_registro['TRD'])}")
        with me2:
            st.metric(label="TP", value=f"{int(ultimo_registro['TP'])}")
        with me3:
            st.metric(label="VIG", value=f"{int(ultimo_registro['VIG'])}")
        with me4:
            st.metric(label="FA", value=f"{int(ultimo_registro['FA'])}")
            
        # Gráfico Histórico de Comportamiento
        st.markdown("#### 📈 Comportamiento y Evolución Diaria de los Estados")
        
        fig_estados = px.line(
            df_estados_sorted, 
            x="Fecha", 
            y=["TRD", "TP", "VIG", "FA"],
            labels={"value": "Cantidad", "Fecha": "Fecha", "variable": "Estado"},
            markers=True,
            color_discrete_sequence=["#1A365D", "#2E7D32", "#FF9800", "#E91E63"] # Colores balanceados y corporativos
        )
        
        # Configuración del eje X para que no se encimen las fechas
        fig_estados.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=10, b=20),
            xaxis=dict(
                type='date',
                tickformat='%Y-%m-%d'
            )
        )
        
        st.plotly_chart(fig_estados, use_container_width=True)
        
        # Tabla de Historial Detallada
        with st.expander("🔍 Ver historial de registros diarios"):
            df_tabla_ver = df_estados_sorted.copy()
            df_tabla_ver["Fecha"] = df_tabla_ver["Fecha"].dt.strftime('%Y-%m-%d')
            st.dataframe(df_tabla_ver, use_container_width=True, hide_index=True)
            
    else:
        st.warning("⚠️ No se encontraron datos en la pestaña 'Estados' de tu Google Sheets.")

except Exception as e:
    st.error(f"⚠️ Ocurrió un error al procesar el Consolidado de Estados: {e}")
