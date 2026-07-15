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

# Estilos CSS de entorno corporativo
st.markdown("""
    <style>
    .main { background-color: #F8F9FA; }
    .kpi-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        text-align: center;
        border-left: 5px solid #636EFA;
    }
    .kpi-title { font-size: 14px; color: #6c757d; font-weight: bold; text-transform: uppercase; }
    .kpi-value { font-size: 28px; font-weight: bold; color: #212529; margin-top: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- CARGA DE DATOS DESDE GOOGLE SHEETS ---
@st.cache_data(ttl=10) # Forzar refresco rápido cada 10 segundos
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
        
        # Conversión y limpieza estricta de tipos
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors='coerce').dt.date
        df["Cajas_Identidad"] = df["Cajas_Identidad"].astype(str).str.strip()
        df["Persona"] = df["Persona"].astype(str).str.strip()
        
        # Filtrar filas vacías o nulas
        df = df.dropna(subset=["Fecha", "Persona"])
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
                records.append({"Fecha": fecha.date(), "Persona": persona, "Cajas_Identidad": f"Caja-{i}"})
        return pd.DataFrame(records)

# --- CARGA DE LA NUEVA PESTAÑA 'Estados' ---
@st.cache_data(ttl=10)
def cargar_datos_estados():
    try:
        # URL de exportación para la pestaña 'Estados' en formato CSV
        # (Ajusta el 'gid' si Google Sheets le asigna uno diferente al crear la pestaña)
        url_estados = "https://docs.google.com/spreadsheets/d/1ld0sxAyU9mYhQ69yv6w2d4sWhK8QW4E0XZlz4hYMhfA/export?format=csv&sheet=Estados"
        df_est = pd.read_csv(url_estados)
        
        # Limpiar nombres de columnas
        df_est.columns = [col.strip() for col in df_est.columns]
        
        # Asegurar tipos y limpiar vacíos
        df_est = df_est.dropna(subset=["Fecha"]).copy()
        df_est["Fecha"] = pd.to_datetime(df_est["Fecha"], errors='coerce').dt.date
        df_est["TRD"] = pd.to_numeric(df_est["TRD"], errors='coerce').fillna(0).astype(int)
        df_est["TP"] = pd.to_numeric(df_est["TP"], errors='coerce').fillna(0).astype(int)
        df_est["VIG"] = pd.to_numeric(df_est["VIG"], errors='coerce').fillna(0).astype(int)
        df_est["FA"] = pd.to_numeric(df_est["FA"], errors='coerce').fillna(0).astype(int)
        
        return df_est.dropna(subset=["Fecha"])
    except Exception as e:
        # Retorna DataFrame vacío si hay algún inconveniente inicial de conexión
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

fechas_disponibles = sorted(list(df_raw["Fecha"].unique()))
if len(fechas_disponibles) > 0:
    fecha_seleccionada = st.sidebar.selectbox("Seleccionar Día Específico:", fechas_disponibles)
else:
    fecha_seleccionada = None

# Filtrado por Operario
df_filtrado_persona = df_raw if persona_seleccionada == "Todos" else df_raw[df_raw["Persona"] == persona_seleccionada]

# --- NUEVOS CÁLCULOS CORREGIDOS (CONTEO DE FILAS) ---

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

# Convertimos la columna Fecha a formato de fecha temporal para filtrar por mes
df_raw_datetime = df_raw.copy()
df_raw_datetime["Fecha_dt"] = pd.to_datetime(df_raw_datetime["Fecha"])

# Contamos los registros del mes actual
df_mes_actual = df_raw_datetime[
    (df_raw_datetime["Fecha_dt"].dt.month == mes_actual) & 
    (df_raw_datetime["Fecha_dt"].dt.year == anio_actual)
]
total_acumulado_mes_actual = len(df_mes_actual)

# Si el mes actual aún no tiene registros, tomamos el último mes con datos para no mostrar 0%
if total_acumulado_mes_actual == 0 and len(df_raw_datetime) > 0:
    ultimo_registro_fecha = df_raw_datetime["Fecha_dt"].max()
    df_mes_actual = df_raw_datetime[
        (df_raw_datetime["Fecha_dt"].dt.month == ultimo_registro_fecha.month) & 
        (df_raw_datetime["Fecha_dt"].dt.year == ultimo_registro_fecha.year)
    ]
    total_acumulado_mes_actual = len(df_mes_actual)

# 3. Avance Global
total_acumulado_proyecto = len(df_raw)

# --- DISEÑO DE INTERFAZ ---
st.title("📈 Dashboard Ejecutivo de Producción")
st.subheader("Proceso: Clasificación de Documentos | Contrato 2026")
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)
with col1:
    fecha_str = str(fecha_seleccionada) if fecha_seleccionada else ""
    html_kpi1 = '<div class="kpi-card"><div class="kpi-title">Producción del Día ({fecha})</div><div class="kpi-value">{valor} Cajas</div></div>'.format(fecha=fecha_str, valor=total_cajas_dia)
    st.markdown(html_kpi1, unsafe_allow_html=True)
with col2:
    avance_mensual = (total_acumulado_mes_actual / META_MENSUAL_EQUIPO) * 100 if META_MENSUAL_EQUIPO > 0 else 0
    html_kpi2 = '<div class="kpi-card"><div class="kpi-title">Avance Meta Mensual</div><div class="kpi-value">{porcentaje:.1f}%</div></div>'.format(porcentaje=avance_mensual)
    st.markdown(html_kpi2, unsafe_allow_html=True)
with col3:
    avance_global = (total_acumulado_proyecto / META_GLOBAL_PROYECTO) * 100 if META_GLOBAL_PROYECTO > 0 else 0
    html_kpi3 = '<div class="kpi-card"><div class="kpi-title">Avance Global</div><div class="kpi-value">{porcentaje:.1f}%</div></div>'.format(porcentaje=avance_global)
    st.markdown(html_kpi3, unsafe_allow_html=True)
with col4:
    if fecha_seleccionada:
        conteo_diario_personas = df_filtrado_dia.groupby("Persona").size().reset_index(name="Cajas")
        bajos_rendimientos = conteo_diario_personas[conteo_diario_personas["Cajas"] < META_DIARIA_INDIVIDUAL]
        num_criticos = len(bajos_rendimientos)
    else:
        num_criticos = 0
    html_kpi4 = '<div class="kpi-card"><div class="kpi-title">Alertas Bajo Rendimiento</div><div class="kpi-value" style="color: #EF553B;">{criticos} Pers.</div></div>'.format(criticos=num_criticos)
    st.markdown(html_kpi4, unsafe_allow_html=True)

# --- GRÁFICOS ---
st.markdown("<br>", unsafe_allow_html=True)
col_graf1, col_graf2 = st.columns([3, 2])

with col_graf1:
    st.markdown("### 🏆 Ranking de Producción Acumulada por Persona")
    ranking_df = df_filtrado_persona.groupby("Persona").size().reset_index(name="Cajas_Producidas").sort_values(by="Cajas_Producidas", ascending=True)
    fig_ranking = px.bar(ranking_df, x="Cajas_Producidas", y="Persona", orientation="h", color="Cajas_Producidas", color_continuous_scale="Viridis")
    st.plotly_chart(fig_ranking, use_container_width=True)

with col_graf2:
    st.markdown("### 🎯 Progreso de Metas e Historial")
    evolucion_diaria = df_filtrado_persona.groupby("Fecha").size().reset_index(name="Cajas_Producidas")
    fig_lineas = px.line(evolucion_diaria, x="Fecha", y="Cajas_Producidas", markers=True)
    st.plotly_chart(fig_lineas, use_container_width=True)

# ==============================================================================
# INTEGRACIÓN NUEVA: 📊 CONSOLIDADO ESTADOS (Histórico Diario Directo sin Sumar)
# ==============================================================================
st.markdown("---")
st.header("📊 Consolidado Estados")
st.subheader("Avance Diario e Histórico Consecutivo")

try:
    if not df_estados_raw.empty:
        # Ordenar datos cronológicamente por la columna Fecha
        df_estados_sorted = df_estados_raw.sort_values(by="Fecha").copy()
        
        # --- VALORES DEL ÚLTIMO REGISTRO ENCONTRADO ---
        ultimo_registro = df_estados_sorted.iloc[-1]
        fecha_reciente = ultimo_registro['Fecha'].strftime('%Y-%m-%d')
        
        st.markdown(f"##### 📅 Estado del día reportado en Sheets: **{fecha_reciente}**")
        
        # Renderizado de Tarjetas de Métricas Puras (sin acumular)
        me1, me2, me3, me4 = st.columns(4)
        with me1:
            st.metric(label="TRD", value=f"{int(ultimo_registro['TRD'])}")
        with me2:
            st.metric(label="TP", value=f"{int(ultimo_registro['TP'])}")
        with me3:
            st.metric(label="VIG", value=f"{int(ultimo_registro['VIG'])}")
        with me4:
            st.metric(label="FA", value=f"{int(ultimo_registro['FA'])}")
            
        # --- GRÁFICO HISTÓRICO DE COMPORTAMIENTO ---
        st.markdown("#### 📈 Comportamiento y Evolución Diaria de los Estados")
        
        # Establecer la fecha como índice para graficar la línea de tiempo real sin agregaciones
        df_grafico_est = df_estados_sorted.set_index('Fecha')[['TRD', 'TP', 'VIG', 'FA']]
        st.line_chart(df_grafico_est)
        
        # --- TABLA DE HISTORIAL DETALLADA ---
        with st.expander("🔍 Ver historial de registros diarios"):
            st.dataframe(
                df_estados_sorted.style.format({'Fecha': lambda t: t.strftime('%Y-%m-%d')}),
                use_container_width=True
            )
    else:
        st.warning("⚠️ No se encontraron datos en la pestaña 'Estados' de tu Google Sheets.")
        st.info(
            "Por favor, ve a tu Google Sheets y asegúrate de haber creado una nueva pestaña "
            "llamada exactamente **'Estados'** con los encabezados: **'Fecha'**, **'TRD'**, **'TP'**, **'VIG'** y **'FA'**."
        )

except Exception as e:
    st.error(f"⚠️ Ocurrió un error al procesar el Consolidado de Estados: {e}")
