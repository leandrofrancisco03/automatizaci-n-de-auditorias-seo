import streamlit as st
from db_manager import fetch_data

# --- CONFIGURACIÓN GLOBAL Y COLORES An16 ---
st.set_page_config(page_title="An16 | Auditorías SEO", page_icon="🚀", layout="wide")

st.markdown("""
    <style>
    [data-testid="stSidebar"] { background-color: #0f3082; }
    [data-testid="stSidebar"] * { color: white !important; }
    .stButton>button { background-color: #f06c00; color: white; border: none; }
    .stButton>button:hover { background-color: #d15d00; }
    </style>
""", unsafe_allow_html=True)

st.sidebar.image("https://media.licdn.com/dms/image/v2/D4D0BAQHt0cetmTHiLw/company-logo_200_200/company-logo_200_200/0/1719255445615/agencia_n16_logo?e=2147483647&v=beta&t=FZ6X50bTtC3kMo-QrZG4G5wXV_evlnT5z8wz6Cf9RNU", use_container_width=True)

params = st.query_params

# 🟢 1. MODO CLIENTE (URL Directa con ?id=...)
if "id" in params:
    id_url = params["id"]
    
    df_cliente = fetch_data(f"SELECT cliente_nombre FROM auditorias_historico WHERE auditoria_id = '{id_url}'")
    
    if not df_cliente.empty:
        cliente = df_cliente.iloc[0]['cliente_nombre']
        
        # Guardamos la sesión
        st.session_state['auditoria_id_actual'] = id_url
        st.session_state['cliente_actual'] = cliente
        
        # 🔥 MAGIA 1: Redirigimos al cliente INMEDIATAMENTE a la pestaña de Resumen
        st.switch_page("pages/1_📊_Resumen.py")
            
    else:
        st.error("❌ Enlace no válido o auditoría no encontrada. Por favor, contacta a N16.")

# 🔵 2. MODO AGENCIA (URL Limpia - Muro de Administrador)
else:
    # 🔥 MAGIA 2: El Escudo Protector
    # Si un cliente que ya está adentro hace clic en "app" por error en el menú lateral,
    # lo rebotamos automáticamente de vuelta al Resumen para que NUNCA vea tu panel de contraseñas.
    if 'auditoria_id_actual' in st.session_state and 'admin_auth' not in st.session_state:
        st.switch_page("pages/1_📊_Resumen.py")

    st.title("🛡️ Centro de Mando Interno - N16")
    
    password = st.text_input("Ingresa la contraseña maestra", type="password")
    
    if password == st.secrets["MASTER_PASSWORD"]: 
        # Registramos que fuiste tú (la agencia) quien inició sesión
        st.session_state['admin_auth'] = True 
        
        st.success("Acceso concedido.")
        st.write("---")
        
        df_historico = fetch_data("SELECT auditoria_id, cliente_nombre, dominio, fecha_auditoria FROM auditorias_historico ORDER BY fecha_auditoria DESC")
        
        if not df_historico.empty:
            st.subheader("🔍 Selector Global de Auditorías")
            opciones = df_historico.apply(lambda row: f"{row['cliente_nombre']} ({row['dominio']}) - {row['fecha_auditoria'].strftime('%Y-%m-%d')}", axis=1)
            seleccion = st.selectbox("Elige un reporte para visualizar:", opciones.tolist())
            
            indice = opciones.tolist().index(seleccion)
            id_seleccionado = df_historico.iloc[indice]['auditoria_id']
            
            # Guardamos en sesión
            st.session_state['auditoria_id_actual'] = id_seleccionado
            st.session_state['cliente_actual'] = df_historico.iloc[indice]['cliente_nombre']
            
            st.info("📲 **Enlace directo para enviar al cliente:**")
            
            url_base = st.context.headers.get("Host") if "Host" in st.context.headers else "localhost:8501"
            enlace_magico = f"https://{url_base}/?id={id_seleccionado}" if "localhost" not in url_base else f"http://{url_base}/?id={id_seleccionado}"
            
            st.code(enlace_magico, language="text")
            
            # Botón de atajo para que tú como admin también saltes directo al resumen si quieres
            if st.button("Ver Dashboard de este Cliente", type="primary"):
                st.switch_page("pages/1_📊_Resumen.py")
            
        else:
            st.warning("No hay auditorías en la base de datos.")
    elif password:
        st.error("Contraseña incorrecta.")