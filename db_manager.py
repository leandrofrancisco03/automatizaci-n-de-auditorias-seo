import psycopg2
import pandas as pd
import streamlit as st

# --- LEYENDO CREDENCIALES DE STREAMLIT SECRETS ---
DB_HOST = st.secrets["DB_HOST"]
DB_PORT = st.secrets["DB_PORT"]
DB_NAME = st.secrets["DB_NAME"]
DB_USER = st.secrets["DB_USER"]
DB_PASS = st.secrets["DB_PASS"]

# Agregamos el decorador de caché. ttl=7200 significa que dura 2 horas.
@st.cache_data(ttl=7200, show_spinner=False)
def fetch_data(query):
    """Ejecuta una consulta SQL abriendo y cerrando la conexión de forma segura."""
    conn = None
    try:
        # 1. Abrimos una conexión fresca cada vez
        conn = psycopg2.connect(
            host=DB_HOST, port=DB_PORT, dbname=DB_NAME, user=DB_USER, password=DB_PASS
        )
        
        # 2. Pandas lee los datos usando esta conexión
        df = pd.read_sql(query, conn)
        
        return df
        
    except Exception as e:
        st.error(f"Error ejecutando consulta: {e}")
        return pd.DataFrame()
        
    finally:
        # 3. Este bloque se ejecuta SIEMPRE, garantizando que colgamos el teléfono
        if conn is not None:
            conn.close()