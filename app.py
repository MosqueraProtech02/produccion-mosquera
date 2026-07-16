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

# Estilos CSS de entorno corporativo (Diseño elegante del Logo/Encabezado)
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
        border-left: 5px solid #1A365D;
    }
    .kpi-title { font-size: 14px; color: #6c757d; font-weight: bold; text-transform: uppercase; }
    .kpi-value { font-size: 28px; font-weight: bold; color: #212529; margin-top: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- CARGA DE DATOS DESDE GOOGLE SHEETS ---
@st.cache_data(ttl=10)
def cargar_datos_reales():
    try:
        url = "https://docs.google.com/spreadsheets/d/1ld0sxAyU9mYhQ69yv6w2d4sWhK8QW4E0XZlz4hYMhfA/export?format=csv&gid=990786706"
        df = pd.read_csv(url)
        
        # Limpieza uniforme de nombres de columnas
        df.columns = [col.strip().lower().replace('á','a').replace('é','e').replace('í','i').replace('ó','o').replace('ú','u') for col in df.columns]
        
        # Mapeo inteligente con prioridades corregidas
        col_fecha = None
        for c in df.columns:
            if c in ['fecha', 'dia']:
                col_fecha = c
                break
        if not col_fecha:
            for c in df.columns:
                if 'fecha' in c or 'dia' in c:
                    col_fecha = c
                    break
        if not col_fecha: 
            col_fecha = df.columns[0]
        
        col_persona = None
        for c in df.columns:
            if c in ['persona', 'operario']:
                col_persona = c
                break
        if not col_persona:
            for c in df.columns:
                if any(x in c for x in ['persona', 'operario', 'nombre', 'usuario', 'empleado']):
                    col_persona = c
                    break
        if not col_persona: 
            col_persona = df.columns[1]
        
        col_cajas = None
        for c in df.columns:
            if any(x in c for x in ['cajas_identidad', 'caja_identidad', 'identidad']):
                col_cajas = c
                break
        if not col_cajas:
            for c in df.columns:
                if any(x in c for x in ['caja', 'produc', 'rendi', 'total', 'cant']):
                    col_cajas = c
                    break
        if not col_cajas: 
            col_cajas = df.columns[2]
        
        # Renombrar columnas de forma segura
        df = df.rename(columns={col_fecha: "Fecha", col_persona: "Persona", col_cajas: "Cajas_Identidad"})
        
        # 1. Interpretación de fecha estricta (Prioriza formato DD/MM/AAAA)
        df["Fecha"] = pd.to_datetime(df["Fecha"], dayfirst=True, errors='coerce')
        
        # Estandarizar nombres: Quita espacios extra y homogeniza el formato tipo Título (Capitalizado)
        # Esto soluciona que "Luz Dary" y "luz Dary" se muestren por separado.
        df["Persona"] = df["Persona"].astype(str).str.strip().str.title().fillna("No Asignado")
        
        # Extraer números de manera segura previniendo errores de conversión
        df["Cajas_Identidad_Num"] = df["Cajas_Identidad"].astype(str).str.extract(r'(\d+)').astype(float).fillna(0).astype(int)
        
        # Eliminar filas donde la Fecha sea inválida o nula
        df = df.dropna(subset=["Fecha"])
        
        # 2. Filtro de seguridad dinámico contra fechas futuras accidentales
        hoy = pd.Timestamp.now().normalize()
        df = df[df["Fecha"] <= hoy]
        
        return df.sort_values(by="Fecha")
    except Exception as e:
        st.sidebar.error(f"❌ Error al mapear Hoja Principal: {str(e)}")
        # Datos simulados de respaldo estructurados idénticamente
        np.random.seed(42)
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
        
        # 1. Interpretación de fecha estricta (Prioriza formato DD/MM/AAAA)
        df_est["Fecha"] = pd.to_datetime(df_est["Fecha"], dayfirst=True, errors='coerce')
        
        # 2. Filtro de seguridad dinámico contra fechas futuras accidentales
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
        # Estructura vacía resiliente para evitar romper el flujo visual
        return pd.DataFrame(columns=["Fecha", "TRD", "TP", "VIG", "FA"])

# --- CARGA INICIAL ---
df_raw = cargar_datos_reales()
df_estados_raw = cargar_datos_estados()

# --- CONSTANTES DE METAS ---
META_DIARIA_INDIVIDUAL = 3
META_MENSUAL_EQUIPO = 2400
META_GLOBAL_PROYECTO = 36099

# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/771/771239.png", width=80)
st.sidebar.title("Panel de Control")
st.sidebar.markdown("Datos del archivo de Google Sheets.")

st.sidebar.info("Columnas detectadas en tu hoja:\n- Fecha: `Fecha` \n- Operario: `Persona` \n- Identidad Caja: `Cajas_Identidad`")

if st.sidebar.button("🔄 Sincronizar Google Sheets", key="sync_btn"):
    st.cache_data.clear()
    st.rerun()

# --- LIMPIEZA AVANZADA DE OPERARIOS (Filtro Anti-Ruidos) ---
# Excluye vacíos, 'No Asignado', y textos informales que se ingresen por error
palabras_ruido = ["humedad", "observacion", "comentario", "error", "vacio", "no asignado", "nan", "prueba"]
df_limpio = df_raw[
    (df_raw["Persona"].notna()) & 
    (df_raw["Persona"] != "") &
    (df_raw["Persona"] != "No Asignado") &
    (~df_raw["Persona"].str.lower().str.contains('|'.join(palabras_ruido))) &
    (df_raw["Persona"].str.len() < 45) # Excluye textos descriptivos accidentalmente largos
].copy()

# Selectores dinámicos basados en la lista limpia
lista_personas = ["Todos"] + sorted(list(df_limpio["Persona"].unique()))
persona_seleccionada = st.sidebar.selectbox("Seleccionar Operario:", lista_personas)

fechas_disponibles_dt = sorted(list(df_limpio["Fecha"].unique()))
fechas_disponibles_str = [pd.to_datetime(f).strftime('%Y-%m-%d') for f in fechas_disponibles_dt]

if fechas_disponibles_str:
    # Posicionar el selector por defecto en el día real con datos más recientes
    ultima_fecha_str = pd.to_datetime(df_limpio["Fecha"].max()).strftime('%Y-%m-%d')
    try:
        index_defecto = fechas_disponibles_str.index(ultima_fecha_str)
    except ValueError:
        index_defecto = len(fechas_disponibles_str) - 1

    fecha_seleccionada_str = st.sidebar.selectbox(
        "Seleccionar Día Específico:", 
        fechas_disponibles_str,
        index=index_defecto  
    )
    fecha_seleccionada = pd.to_datetime(fecha_seleccionada_str)
else:
    fecha_seleccionada = None

# --- FILTRADO DE DATOS ---
df_filtrado_persona = df_limpio if persona_seleccionada == "Todos" else df_limpio[df_limpio["Persona"] == persona_seleccionada]

# 1. Cajas del día seleccionado (Para KPIs del día)
if fecha_seleccionada is not None:
    df_filtrado_dia = df_filtrado_persona[df_filtrado_persona["Fecha"] == fecha_seleccionada]
    total_cajas_dia = len(df_filtrado_dia)
else:
    df_filtrado_dia = pd.DataFrame()
    total_cajas_dia = 0

# 2. Cálculo del mes con datos más recientes para la meta mensual (Traducido y dinámico)
if not df_limpio.empty:
    fecha_base_mes = fecha_seleccionada if fecha_seleccionada is not None else df_limpio["Fecha"].max()
    mes_actual = fecha_base_mes.month
    anio_actual = fecha_base_mes.year
    
    df_mes_actual = df_limpio[
        (df_limpio["Fecha"].dt.month == mes_actual) & 
        (df_limpio["Fecha"].dt.year == anio_actual)
    ]
    total_acumulado_mes_actual = len(df_mes_actual)
    
    # Diccionario de traducción para asegurar que el mes esté siempre en español
    meses_espanol = {
        1: "ENERO", 2: "FEBRERO", 3: "MARZO", 4: "ABRIL", 
        5: "MAYO", 6: "JUNIO", 7: "JULIO", 8: "AGOSTO", 
        9: "SEPTIEMBRE", 10: "OCTUBRE", 11: "NOVIEMBRE", 12: "DICIEMBRE"
    }
    nombre_mes_kpi = meses_espanol.get(mes_actual, "MES ACTUAL")
else:
    total_acumulado_mes_actual = 0
    nombre_mes_kpi = "MES"

# 3. Avance Global dinámico basado en ID consecutivo más alto
total_acumulado_proyecto = int(df_limpio["Cajas_Identidad_Num"].max()) if not df_limpio.empty else 0

# --- DISEÑO DE INTERFAZ PRINCIPAL ---
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
    st.markdown(f'<div class="kpi-card"><div class="kpi-title">Producción del Día ({fecha_str})</div><div class="kpi-value">{total_cajas_dia} Cajas</div></div>', unsafe_allow_html=True)

with col2:
    avance_mensual = (total_acumulado_mes_actual / META_MENSUAL_EQUIPO) * 100 if META_MENSUAL_EQUIPO > 0 else 0
    st.markdown(f'<div class="kpi-card" style="border-left-color: #2E7D32;"><div class="kpi-title">Avance Meta Mensual ({nombre_mes_kpi})</div><div class="kpi-value">{avance_mensual:.1f}%</div></div>', unsafe_allow_html=True)

with col3:
    avance_global = (total_acumulado_proyecto / META_GLOBAL_PROYECTO) * 100 if META_GLOBAL_PROYECTO > 0 else 0
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">Avance Global Real</div>
        <div class="kpi-value">{avance_global:.2f}%</div>
        <div style="font-size: 11px; color: #6C757D; margin-top: 5px;">(Caja {total_acumulado_proyecto:,} de {META_GLOBAL_PROYECTO:,})</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    if not df_filtrado_dia.empty:
        conteo_diario_personas = df_filtrado_dia.groupby("Persona").size().reset_index(name="Cajas")
        num_criticos = len(conteo_diario_personas[conteo_diario_personas["Cajas"] < META_DIARIA_INDIVIDUAL])
    else:
        num_criticos = 0
    st.markdown(f'<div class="kpi-card" style="border-left-color: #EF553B;"><div class="kpi-title">Alertas Bajo Rendimiento</div><div class="kpi-value" style="color: #EF553B;">{num_criticos} Pers.</div></div>', unsafe_allow_html=True)

# --- SECCIÓN DE GRÁFICOS DE RENDIMIENTO ---
st.markdown("<br>", unsafe_allow_html=True)
col_graf1, col_graf2 = st.columns([3, 2])

with col_graf1:
    st.markdown("### 🏆 Ranking de Producción Acumulada por Persona")
    if not df_filtrado_persona.empty:
        # IMPORTANTE: Agrupa usando 'df_filtrado_persona' entero para mostrar el histórico acumulado sin importar el día lateral seleccionado
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
        # Margen amplio izquierdo (l=200) para garantizar apellidos completos e índice estricto por operario
        fig_ranking.update_layout(
            margin=dict(l=200, r=25, t=10, b=20), 
            height=altura_dinamica,
            yaxis=dict(
                autorange="ascending",
                dtick=1  # Obliga a mostrar cada etiqueta/operario consecutivamente en el eje vertical
            )
        )
        st.plotly_chart(fig_ranking, use_container_width=True)
    else:
        st.info("No hay datos disponibles para generar el ranking.")

with col_graf2:
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
            margin=dict(l=20, r=20, t=10, b=20),
            height=400
        )
        st.plotly_chart(fig_lineas, use_container_width=True)
    else:
        st.info("No hay datos históricos disponibles.")

# --- SECCIÓN CONSOLIDADO ESTADOS ---
st.markdown("---")
st.header("📊 Consolidado Estados")
st.subheader("Avance Diario e Histórico Consecutivo")

if not df_estados_raw.empty:
    df_estados_sorted = df_estados_raw.sort_values(by="Fecha")
    ultimo_registro = df_estados_sorted.iloc[-1]
    fecha_reciente = pd.to_datetime(ultimo_registro['Fecha']).strftime('%Y-%m-%d')
    
    st.markdown(f"##### 📅 Último Estado Reportado en Sheets: **{fecha_reciente}**")
    
    me1, me2, me3, me4 = st.columns(4)
    with me1: st.metric(label="TRD", value=f"{int(ultimo_registro['TRD'])}")
    with me2: st.metric(label="TP", value=f"{int(ultimo_registro['TP'])}")
    with me3: st.metric(label="VIG", value=f"{int(ultimo_registro['VIG'])}")
    with me4: st.metric(label="FA", value=f"{int(ultimo_registro['FA'])}")
        
    st.markdown("#### 📈 Comportamiento y Evolución Diaria de los Estados")
    
    fig_estados = px.line(
        df_estados_sorted, 
        x="Fecha", 
        y=["TRD", "TP", "VIG", "FA"],
        labels={"value": "Cantidad", "Fecha": "Fecha", "variable": "Estado"},
        markers=True,
        color_discrete_sequence=["#1A365D", "#2E7D32", "#FF9800", "#E91E63"]
    )
    
    fig_estados.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=20, r=20, t=10, b=20),
        xaxis=dict(type='date', tickformat='%Y-%m-%d')
    )
    st.plotly_chart(fig_estados, use_container_width=True)
    
    with st.expander("🔍 Ver historial de registros diarios (Tabla)"):
        df_tabla_ver = df_estados_sorted.copy()
        df_tabla_ver["Fecha"] = df_tabla_ver["Fecha"].dt.strftime('%Y-%m-%d')
        st.dataframe(df_tabla_ver, use_container_width=True, hide_index=True)
else:
    st.warning("⚠️ No se pudieron recuperar datos en la pestaña 'Estados' de tu Google Sheets.")
