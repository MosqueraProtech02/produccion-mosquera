# --- 1. CONFIGURACIÓN DE LA PÁGINA (Barra lateral desplegable) ---
st.set_page_config(
    page_title="Dashboard de Producción - Proceso Clasificación",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"  # <-- Inicia contraída para que el usuario la despliegue a conveniencia
)

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/771/771239.png", width=60)
    st.title("Panel de Control")
    st.caption("Datos sincronizados en tiempo real")
    
    # Campo de columnas detectadas ultracompacto
    st.markdown("""
        <div style="background-color: rgba(255, 255, 255, 0.05); padding: 8px 12px; border-radius: 8px; border: 1px solid rgba(255, 255, 255, 0.1); margin-bottom: 12px;">
            <span style="font-size: 11px; color: #94A3B8; font-weight: 600; text-transform: uppercase;">Columnas:</span>
            <div style="font-size: 11px; color: #E2E8F0; margin-top: 2px;">
                <code>Fecha</code> • <code>Persona</code> • <code>Cajas_Identidad</code>
            </div>
        </div>
    """, unsafe_allow_html=True)

    if st.button("🔄 Sincronizar Google Sheets", key="sync_btn", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")
    
    # ... resto del contenido del sidebar (selectores de persona, fecha, etc.)
