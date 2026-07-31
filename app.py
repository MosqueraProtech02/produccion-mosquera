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

# --- 2. ESTILOS CSS PERSONALIZADOS (Campos de Búsqueda y Selectbox Corregidos) ---
st.markdown("""
    <style>
    /* Fondo principal gris suave */
    .stApp { 
        background-color: #F1F5F9 !important; 
    }

    /* Texto base */
    html, body, p, span, label, .stMarkdown {
        color: #0F172A !important;
    }

    /* Barra Lateral */
    section[data-testid="stSidebar"] { 
        background-color: #0F172A !important; 
    }

    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3, 
    section[data-testid="stSidebar"] span, 
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p { 
        color: #FFFFFF !important; 
        font-weight: 500;
    }

    section[data-testid="stSidebar"] .stCaption {
        color: #94A3B8 !important;
    }

    /* ========================================================= */
    /*   CORRECCIÓN COMPLETA DE CAMPOS DE BÚSQUEDA Y SELECTBOX   */
    /* ========================================================= */

    /* Contenedor Base de los Selectbox (Tanto en Sidebar como Principal) */
    div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border: 1.5px solid #94A3B8 !important;
        border-radius: 8px !important;
        color: #0F172A !important;
    }

    /* Texto seleccionado visible dentro de la caja de selección */
    div[data-baseweb="select"] div[aria-selected="true"],
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] input {
        color: #0F172A !important;
        font-weight: 600 !important;
        -webkit-text-fill-color: #0F172A !important;
    }

    /* Icono de la flecha del desplegable */
    div[data-baseweb="select"] svg {
        fill: #0F172A !important;
    }

    /* Menú flotante / Opciones desplegables (Popover) */
    ul[role="listbox"],
    div[data-baseweb="popover"] {
        background-color: #FFFFFF !important;
        border: 1px solid #CBD5E1 !important;
        border-radius: 8px !important;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1) !important;
    }

    /* Cada elemento de la lista desplegable */
    li[role="option"] {
        color: #0F172A !important;
        background-color: #FFFFFF !important;
        font-weight: 500 !important;
    }

    /* Al pasar el mouse por encima de una opción */
    li[role="option"]:hover,
    li[role="option"][aria-selected="true"] {
        background-color: #E2E8F0 !important;
        color: #0F172A !important;
    }

    /* ========================================================= */

    /* Contenedores de Tarjetas / Bloques */
    div[data-testid="stVerticalBlockBorderWrapper"] > div {
        background-color: #FFFFFF !important;
        border-radius: 14px !important;
        border: 1px solid #CBD5E1 !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05) !important;
        padding: 18px !important;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] h1,
    div[data-testid="stVerticalBlockBorderWrapper"] h2,
    div[data-testid="stVerticalBlockBorderWrapper"] h3,
    div[data-testid="stVerticalBlockBorderWrapper"] h4 {
        color: #0F172A !important;
        font-weight: 800 !important;
    }

    /* Banner Principal */
    .header-banner {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        color: white;
        padding: 22px 28px;
        border-radius: 14px;
        margin-bottom: 25px;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
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

    /* Tarjetas KPI */
    .kpi-card {
        background-color: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-left: 5px solid #0F172A;
        border-radius: 12px;
        padding: 18px 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.06);
        height: 100%;
    }
    .kpi-title { font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; color: #334155; font-weight: 800; }
    .kpi-value { font-size: 28px; font-weight: 800; color: #0F172A; margin: 4px 0; }
    .kpi-subtext { font-size: 11px; color: #475569; font-weight: 600; }

    /* Botones */
    div.stButton > button, div.stDownloadButton > button { 
        border-radius: 8px; 
        font-weight: 700;
        background-color: #2563EB !important;
        color: #FFFFFF !important;
        border: none !important;
    }
    div.stButton > button:hover, div.stDownloadButton > button:hover {
        background-color: #1D4ED8 !important;
    }
    </style>
""", unsafe_allow_html=True)
