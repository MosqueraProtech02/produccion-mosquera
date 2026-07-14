import streamlit as st
import pandas as pd
import numpy as np
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
        df = df.rename(columns={col_fecha: "Fecha", col_persona: "Persona", col_cajas: "Cajas_Producidas"})
        
        # Conversión y limpieza estricta de tipos
        df["Fecha"] = pd.to_datetime(df["Fecha"], errors='coerce').dt.date
        df["Cajas_Producidas"] = pd.to_numeric(df["Cajas_Producidas"], errors='coerce').fillna(0).astype(int)
        df["Persona"] = df["Persona"].astype(str).str.strip()
        
        # Filtrar filas vacías o nulas
        df = df.dropna(subset=["Fecha", "Persona"])
        return df[["Fecha", "Persona", "Cajas_Producidas"]]
    except Exception as e:
        st.sidebar.error(f"❌ Error de Conexión. Detalle: {str(e)}")
        # Base de datos simulada de respaldo
        np.random.seed(42)
        personas = ["Yamith Marín", "Operario de Prueba A", "Operario de Prueba B"]
        fechas = pd.date_range(start="2026-05-01", end="2026-05-05", freq="D")
        records = []
        for fecha in fechas:
            for persona in personas:
                records.append({"Fecha": fecha.date(), "Persona": persona, "Cajas_Producidas": int(np.random.randint(1, 5))})
        return pd.DataFrame(records)

df_raw = cargar_datos_reales()

# --- CONSTANTES ---
META_DIARIA_INDIVIDUAL = 3
META_MENSUAL_EQUIPO = 2400
META_GLOBAL_PROYECTO = 36099

# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/771/771239.png", width=80)
st.sidebar.title("Panel de Control")
st.sidebar.markdown("Datos del archivo de Google Sheets.")

st.sidebar.info(f"Columnas detectadas en tu hoja:\n- Fecha: `{df_raw.columns[0]}`\n- Operario: `{df_raw.columns[1]}`\n- Cajas: `{df_raw.columns[2]}`")

if st.sidebar.button("🔄 Sincronizar Google Sheets"):
    st.cache_data.clear()
    st.rerun()

lista_personas = ["Todos"] + sorted(list(df_raw["Persona"].unique()))
persona_seleccionada = st.sidebar.selectbox("Seleccionar Operario:", lista_personas)

fechas_disponibles = sorted(list(df_raw["Fecha"].unique()))
if len(fechas_disponibles) > 0:
    fecha_seleccionada = st.sidebar.selectbox("Seleccionar Día Específico:", fechas_disponibles)
else:
    fecha_seleccionada = "Sin Registros"

df_filtrado_persona = df_raw if persona_seleccionada == "Todos" else df_raw[df_raw["Persona"] == persona_seleccionada]
df_filtrado_dia = df_raw[df_raw["Fecha"] == fecha_seleccionada] if fecha_seleccionada != "Sin Registros" else df_raw

# --- CÁLCULOS PRINCIPALES ---
total_acumulado_proyecto = df_raw["Cajas_Producidas"].sum()
total_acumulado_mes_actual = df_raw["Cajas_Producidas"].sum()
total_cajas_dia = df_filtrado_dia["Cajas_Producidas"].sum()

# --- DISEÑO DE INTERFAZ ---
st.title("📈 Dashboard Ejecutivo de Producción")
st.subheader("Proceso: Clasificación de Documentos | Contrato 2026")
st.markdown("---")

col1, col2, col3, col4 = st.columns(4)
with col1:
    html_kpi1 = '<div class="kpi-card"><div class="kpi-title">Producción del Día ({fecha})</div><div class="kpi-value">{valor} Cajas</div></div>'.format(fecha=fecha_seleccionada, valor=total_cajas_dia)
    st.markdown(html_kpi1, unsafe_allow_html=True)
with col2:
    avance_mensual = (total_acumulado_mes_actual / META_MENSUAL_EQUIPO) * 100
    html_kpi2 = '<div class="kpi-card"><div class="kpi-title">Avance Meta Mensual</div><div class="kpi-value">{porcentaje:.1f}%</div></div>'.format(porcentaje=avance_mensual)
    st.markdown(html_kpi2, unsafe_allow_html=True)
with col3:
    avance_global = (total_acumulado_proyecto / META_GLOBAL_PROYECTO) * 100
    html_kpi3 = '<div class="kpi-card"><div class="kpi-title">Avance Global</div><div class="kpi-value">{porcentaje:.1f}%</div></div>'.format(porcentaje=avance_global)
    st.markdown(html_kpi3, unsafe_allow_html=True)
with col4:
    bajos_rendimientos = df_filtrado_dia[df_filtrado_dia["Cajas_Producidas"] < META_DIARIA_INDIVIDUAL]
    html_kpi4 = '<div class="kpi-card"><div class="kpi-title">Alertas Bajo Rendimiento</div><div class="kpi-value" style="color: #EF553B;">{criticos} Pers.</div></div>'.format(criticos=len(bajos_rendimientos))
    st.markdown(html_kpi4, unsafe_allow_html=True)

# --- GRÁFICOS ---
st.markdown("<br>", unsafe_allow_html=True)
col_graf1, col_graf2 = st.columns([3, 2])

with col_graf1:
    st.markdown("### 🏆 Ranking de Producción Acumulada por Persona")
    ranking_df = df_raw.groupby("Persona")["Cajas_Producidas"].sum().reset_index()
    fig_ranking = px.bar(ranking_df, x="Cajas_Producidas", y="Persona", orientation="h")
    st.plotly_chart(fig_ranking, use_container_width=True)

with col_graf2:
    st.markdown("### 🎯 Progreso de Metas e Historial")
    evolucion_diaria = df_raw.groupby("Fecha")["Cajas_Producidas"].sum().reset_index()
    fig_lineas = px.line(evolucion_diaria, x="Fecha", y="Cajas_Producidas")
    st.plotly_chart(fig_lineas, use_container_width=True)
