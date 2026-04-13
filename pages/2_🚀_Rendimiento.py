import streamlit as st
from db_manager import fetch_data
import pandas as pd

# Configuración de la página
st.set_page_config(page_title="Rendimiento Web | An16", page_icon="🚀", layout="wide")

# Validar seguridad/sesión
if 'auditoria_id_actual' not in st.session_state:
    st.warning("👈 Por favor, selecciona un cliente en la página principal primero.")
    st.stop()

id_actual = st.session_state['auditoria_id_actual']
cliente = st.session_state['cliente_actual']

st.title(f"🚀 Velocidad y Experiencia de Usuario")
st.markdown(f"**Cliente:** {cliente} | Evaluamos qué tan rápido carga tu sitio web simulando conexiones de usuarios reales (3G/4G).")
st.write("---")

# 1. Extraer los datos de esta auditoría
query = f"SELECT * FROM seo_rendimiento_lighthouse WHERE auditoria_id = '{id_actual}'"
df = fetch_data(query)

if df.empty:
    st.info("No hay datos de rendimiento cargados para esta auditoría aún.")
    st.stop()

# 2. Selector de URL
urls_analizadas = df['url_analizada'].unique()
url_seleccionada = st.selectbox("🌐 Selecciona la página específica a visualizar:", urls_analizadas)

# Filtramos el dataframe
df_filtrado = df[df['url_analizada'] == url_seleccionada]

# Separamos la data
df_mobile = df_filtrado[df_filtrado['dispositivo'].str.lower() == 'mobile']
df_desktop = df_filtrado[df_filtrado['dispositivo'].str.lower() == 'desktop']

# 3. Función para dibujar las métricas
def dibujar_metricas(df_dispositivo):
    if df_dispositivo.empty:
        st.warning("No se realizó análisis para este dispositivo en esta página.")
        return

    row = df_dispositivo.iloc[0]

    # --- SECCIÓN A: PUNTUACIONES GENERALES ---
    st.subheader("🏆 Puntuación Global de Salud Web")
    
    # Extraemos y redondeamos todas las métricas a números enteros limpios
    perf = int(round(float(row['score_performance'] or 0)))
    acc = int(round(float(row['score_accesibilidad'] or 0)))
    bp = int(round(float(row['score_buenas_practicas'] or 0)))
    seo = int(round(float(row['score_seo'] or 0)))

    # Diagnóstico dinámico basado en el performance
    if perf < 50:
        st.error("🚨 **Alerta Crítica:** Tu página carga muy lento. Estás perdiendo clientes porque se desesperan y abandonan el sitio antes de que termine de cargar. Google también está penalizando tu posición por esto.")
        color_barra = "#ff4b4b" # Rojo Streamlit
    elif perf < 90:
        st.warning("⚠️ **Precaución:** Tu página carga a una velocidad aceptable, pero hay 'cuellos de botella' (imágenes pesadas, código innecesario) que están frenando tu potencial de ventas.")
        color_barra = "#ffa421" # Naranja Streamlit
    else:
        st.success("✅ **Excelente:** Tu sitio está altamente optimizado. La velocidad de carga es un punto a favor para retener clientes y gustarle al algoritmo de Google.")
        color_barra = "#00c04b" # Verde Streamlit

    c1, c2, c3, c4 = st.columns(4)
    
    c1.metric("⚡ Velocidad General", f"{perf}/100", help="Nota global dada por Google. Menos de 50 es crítico para el negocio.")
    c2.metric("♿ Accesibilidad", f"{acc}/100", help="Qué tan fácil es navegar para personas con discapacidades o en pantallas con poca luz.")
    c3.metric("✨ Buenas Prácticas", f"{bp}/100", help="Seguridad básica del sitio (como tener HTTPS activo).")
    c4.metric("🔍 Estructura Técnica", f"{seo}/100", help="Nivel de preparación del código para ser leído por motores de búsqueda.")

    # Barra de progreso visual
    st.markdown(f"""
        <div style="width: 100%; background-color: #2b2b36; border-radius: 5px; margin-top: 10px; margin-bottom: 30px;">
          <div style="width: {perf}%; background-color: {color_barra}; height: 12px; border-radius: 5px;"></div>
        </div>
    """, unsafe_allow_html=True)


    # --- SECCIÓN B: TIEMPOS REALES DE CARGA ---
    st.subheader("⏱️ La Experiencia Real de tu Cliente")
    st.markdown("Estos son los segundos exactos que un cliente debe esperar mientras mira la pantalla de su dispositivo.")
    
    cw1, cw2, cw3, cw4 = st.columns(4)

    # LCP -> Tiempo de Carga Principal
    lcp = float(row['largest_contentful_paint'])
    lcp_sec = lcp / 1000 
    estado_lcp = "Óptimo" if lcp <= 2500 else "- Requiere Mejora" if lcp <= 4000 else "- Crítico (Muy Lento)"
    ayuda_lcp = "Es el tiempo que tarda en aparecer la imagen o el texto más grande de tu página. Si tarda más de 2.5 segundos, el cliente siente que la web 'está rota'."
    cw1.metric("Carga del Contenido Principal", f"{lcp_sec:.1f} seg.", delta=estado_lcp, delta_color="normal", help=ayuda_lcp)

    # FCP -> Primera Señal de Vida
    fcp = float(row['first_contentful_paint'])
    fcp_sec = fcp / 1000
    estado_fcp = "Óptimo" if fcp <= 1800 else "- Requiere Mejora" if fcp <= 3000 else "- Crítico (Pobre)"
    ayuda_fcp = "El momento exacto en el que el cliente ve 'algo' (un logo, un color de fondo) en lugar de una pantalla en blanco."
    cw2.metric("Primera Señal de Vida", f"{fcp_sec:.1f} seg.", delta=estado_fcp, delta_color="normal", help=ayuda_fcp)

    # Speed Index -> Sensación de Velocidad
    si = float(row['speed_index_ms'])
    si_sec = si / 1000
    estado_si = "Óptimo" if si <= 3400 else "- Requiere Mejora" if si <= 5800 else "- Crítico (Lento)"
    ayuda_si = "Qué tan rápido se llena la pantalla con todo el contenido visual. Si es lento, el cliente se frustra esperando ver tus servicios."
    cw3.metric("Sensación Visual de Velocidad", f"{si_sec:.1f} seg.", delta=estado_si, delta_color="normal", help=ayuda_si)

    # CLS -> Estabilidad Visual
    cls = float(row['cumulative_layout_shift'])
    estado_cls = "Estable" if cls <= 0.1 else "- Requiere Mejora" if cls <= 0.25 else "- Inestable (Saltos)"
    ayuda_cls = "¿Alguna vez fuiste a hacer clic en un botón y la página se movió de golpe, haciéndote presionar otra cosa? Esto mide esos saltos molestos. Debe ser lo más cercano a 0."
    cw4.metric("Estabilidad Visual (Saltos)", f"{cls:.3f}", delta=estado_cls, delta_color="normal", help=ayuda_cls)

# 4. Crear las pestañas en la interfaz
tab_mobile, tab_desktop = st.tabs(["📱 Dispositivos Móviles (Prioridad del Algoritmo)", "💻 Computadoras de Escritorio"])

with tab_mobile:
    dibujar_metricas(df_mobile)

with tab_desktop:
    dibujar_metricas(df_desktop)