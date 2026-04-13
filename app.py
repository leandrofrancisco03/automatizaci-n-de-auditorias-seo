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

# 🟢 1. MODO CLIENTE (Si la URL trae un ?id=...)
if "id" in params:
    id_url = params["id"]
    
    # Buscamos el cliente y su PIN en la base de datos
    df_cliente = fetch_data(f"SELECT cliente_nombre, pin_acceso FROM auditorias_historico WHERE auditoria_id = '{id_url}'")
    
    if not df_cliente.empty:
        cliente = df_cliente.iloc[0]['cliente_nombre']
        pin_real = str(df_cliente.iloc[0]['pin_acceso'])
        
        # Verificamos si ya inició sesión en esta ventana
        if st.session_state.get('cliente_autenticado') != id_url:
            st.title(f"🔒 Acceso Seguro: {cliente}")
            st.write("Por favor, ingresa el PIN de 4 dígitos proporcionado por tu asesor de N16.")
            
            # Formulario de Login
            with st.form("login_form"):
                pin_ingresado = st.text_input("PIN de Acceso", type="password", max_chars=4)
                submit = st.form_submit_button("Desbloquear Reporte")
                
                if submit:
                    if pin_ingresado == pin_real:
                        st.session_state['cliente_autenticado'] = id_url
                        st.session_state['auditoria_id_actual'] = id_url
                        st.session_state['cliente_actual'] = cliente
                        st.rerun() # Recarga la página para mostrar el dashboard
                    else:
                        st.error("❌ PIN incorrecto. Inténtalo de nuevo.")
        
        # Si ya puso el PIN correcto, le mostramos el menú y la bienvenida
        else:
            st.title(f"📊 Reporte de Auditoría SEO: {cliente}")
            st.success("¡Acceso verificado! Navega por el menú de la izquierda para explorar las métricas de tu sitio web.")
            
    else:
        st.error("❌ Enlace no válido. Por favor, contacta a N16.")

# 🔵 2. MODO AGENCIA (URL Limpia - Muro de Administrador)
else:
    st.title("🛡️ Centro de Mando Interno - N16")
    
    password = st.text_input("Ingresa la contraseña maestra", type="password")
    
    if password == st.secrets["MASTER_PASSWORD"]: 
        st.success("Acceso concedido.")
        st.write("---")
        
        df_historico = fetch_data("SELECT auditoria_id, cliente_nombre, dominio, fecha_auditoria, pin_acceso FROM auditorias_historico ORDER BY fecha_auditoria DESC")
        
        if not df_historico.empty:
            st.subheader("🔍 Selector Global de Auditorías")
            opciones = df_historico.apply(lambda row: f"{row['cliente_nombre']} ({row['dominio']}) - {row['fecha_auditoria'].strftime('%Y-%m-%d')}", axis=1)
            seleccion = st.selectbox("Elige un reporte para visualizar:", opciones.tolist())
            
            indice = opciones.tolist().index(seleccion)
            id_seleccionado = df_historico.iloc[indice]['auditoria_id']
            pin_cliente = df_historico.iloc[indice]['pin_acceso']
            
            # Guardamos en sesión como admin (bypass de PIN)
            st.session_state['auditoria_id_actual'] = id_seleccionado
            st.session_state['cliente_actual'] = df_historico.iloc[indice]['cliente_nombre']
            
            # Tarjeta de información para enviar al cliente
            st.info("📲 **Datos para compartir con el cliente:**")
            url_base = st.context.headers.get("Host") if "Host" in st.context.headers else "localhost:8501"
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Enlace de acceso:**")
                st.code(f"http://{url_base}/?id={id_seleccionado}", language="text")
            with col2:
                st.write("**PIN de Seguridad:**")
                st.code(f"{pin_cliente}", language="text")
            
        else:
            st.warning("No hay auditorías en la base de datos.")
    elif password:
        st.error("Contraseña incorrecta.")