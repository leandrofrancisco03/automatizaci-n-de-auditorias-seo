import streamlit as st
from db_manager import fetch_data
import pandas as pd
import json
import urllib.parse

st.set_page_config(page_title="Resumen Ejecutivo | An16", layout="wide")

# Verificamos si hay un cliente seleccionado en la sesión
if 'auditoria_id_actual' not in st.session_state:
    st.warning("👈 Por favor, selecciona un cliente o inicia sesión en la página principal primero.")
    st.stop()

id_actual = st.session_state['auditoria_id_actual']
cliente = st.session_state['cliente_actual']

st.title(f"📊 Resumen Ejecutivo: {cliente}")
st.write(f"ID de Ejecución: `{id_actual}` | Vista general del estado de tu proyecto digital.")
st.markdown("---")

# --- 1. OBTENER DATOS DE TODAS LAS TABLAS ---

# A) On-Page
df_onpage = fetch_data(f"SELECT onpage_score, errores_4xx, errores_5xx FROM seo_tecnico_onpage WHERE auditoria_id = '{id_actual}'")

# B) Lighthouse Móvil
query_perf = f"""
    SELECT score_performance, url_analizada, speed_index_ms 
    FROM seo_rendimiento_lighthouse 
    WHERE auditoria_id = '{id_actual}' AND dispositivo ILIKE 'mobile' 
    ORDER BY LENGTH(url_analizada) ASC LIMIT 1
"""
df_perf = fetch_data(query_perf)

# C) Backlinks
df_back = fetch_data(f"SELECT total_backlinks, rank_domain FROM seo_backlinks WHERE auditoria_id = '{id_actual}'")

# D) Competidores
df_comp = fetch_data(f"SELECT dominio_competidor, keywords_oportunidad FROM seo_brecha_competidores WHERE auditoria_id = '{id_actual}'")


# --- 2. SECCIÓN DE SALUD TÉCNICA ---
st.subheader("🩺 Salud Técnica del Sitio web")
st.caption("Esta sección evalúa qué tan fácil es para Google leer tu página y qué tan rápida es para tus clientes desde sus celulares.")

c1, c2, c3, c4 = st.columns(4)

if not df_onpage.empty:
    # Redondeamos a número entero
    score_op = int(round(float(df_onpage.iloc[0]['onpage_score'])))
    errores = int(df_onpage.iloc[0]['errores_4xx']) + int(df_onpage.iloc[0]['errores_5xx'])
    
    # Textos de ayuda para el cliente
    help_onpage = "Evalúa la estructura interna de tu web. Un score alto significa que Google entiende perfectamente qué servicios ofreces."
    help_errores = "Son enlaces rotos (404) o caídas de servidor (500). Son urgentes porque espantan a los clientes y a Google."
    
    c1.metric("Estructura SEO", f"{score_op}/100", delta="Requiere mejoras" if score_op < 80 else "Óptimo", delta_color="inverse" if score_op < 80 else "normal", help=help_onpage)
    c4.metric("Errores Críticos", errores, delta="Urgente revisar" if errores > 0 else "Limpio", delta_color="inverse" if errores > 0 else "normal", help=help_errores)
else:
    c1.metric("Estructura SEO", "N/A", help="No se encontraron datos.")
    c4.metric("Errores Críticos", "N/A")

if not df_perf.empty:
    score_speed = int(df_perf.iloc[0]['score_performance'])
    speed_idx = float(df_perf.iloc[0]['speed_index_ms']) / 1000 
    
    texto_delta = f"⏱️ Carga en {speed_idx:.1f}s" if score_speed >= 50 else f"- ⏱️ {speed_idx:.1f}s (Lento)"
    help_speed = f"La experiencia de los usuarios desde sus celulares. Si la página tarda más de 3 segundos en cargar, el 50% de los visitantes se va. (Evaluado en: {df_perf.iloc[0]['url_analizada']})"
    
    c2.metric("Velocidad Móvil", f"{score_speed}/100", delta=texto_delta, delta_color="normal", help=help_speed)
else:
    c2.metric("Velocidad Móvil", "N/A")

if not df_back.empty and pd.notna(df_back.iloc[0]['rank_domain']):
    help_autoridad = "Es la 'reputación' de tu web (de 0 a 1000). A mayor número, más fácil es aparecer en el primer lugar de Google frente a webs más débiles."
    valor_autoridad = int(round(float(df_back.iloc[0]['rank_domain'])))
    c3.metric("Autoridad de Dominio", f"{valor_autoridad}/1000", help=help_autoridad)
else:
    c3.metric("Autoridad de Dominio", "N/A")

st.markdown("---")

# --- 3. SECCIÓN DE MERCADO Y COMPETENCIA ---
st.subheader("⚔️ Posicionamiento en el Mercado")
st.caption("Analizamos cuántos sitios hablan de ti en internet (tu popularidad) y quién te está robando clientes en las búsquedas.")

col_mercado1, col_mercado2, col_mercado3 = st.columns(3)

if not df_back.empty and pd.notna(df_back.iloc[0]['total_backlinks']):
    help_links = "La cantidad de páginas web externas que tienen un enlace hacia tu página. Funcionan como 'votos de confianza' en internet."
    col_mercado1.metric("Enlaces Externos", f"{df_back.iloc[0]['total_backlinks']:,.0f}", help=help_links)
else:
    col_mercado1.metric("Enlaces Externos", "N/A")

# Lógica para encontrar al peor enemigo leyendo el JSON
rival_principal = "N/A"
max_palabras = 0

if not df_comp.empty:
    for index, row in df_comp.iterrows():
        try:
            datos_json = row['keywords_oportunidad']
            if isinstance(datos_json, str):
                datos_json = json.loads(datos_json)
                
            lista_kws = datos_json.get('lista', [])
            total_kws = len(lista_kws)
            
            if total_kws > max_palabras:
                max_palabras = total_kws
                rival_principal = row['dominio_competidor']
                
        except Exception:
            pass 

if max_palabras > 0:
    help_rival = "El competidor que está atrayendo tráfico en internet con los mismos servicios que tú ofreces."
    help_kws = f"Cantidad de términos de búsqueda donde {rival_principal} aparece en Google y tú no. ¡Son oportunidades de venta perdidas!"
    
    col_mercado2.metric("Principal Competencia", rival_principal, help=help_rival)
    col_mercado3.metric("Oportunidades de Venta", max_palabras, help=help_kws)
else:
    col_mercado2.info("Aún no se ha detectado el principal competidor.")

st.markdown("---")

# --- 4. ZONA DE CONCLUSIONES Y ESTRATEGIA (IA / GERENCIA) ---
st.subheader("🤖 Diagnóstico y Plan de Acción")
st.caption("Resumen ejecutivo generado por IA para comprender el estado actual y los siguientes pasos.")

# Consultamos el resumen de la IA en la tabla principal
df_ia = fetch_data(f"SELECT resumen_ia FROM auditorias_historico WHERE auditoria_id = '{id_actual}'")

resumen_ia_db = ""
if not df_ia.empty and pd.notna(df_ia.iloc[0].get('resumen_ia')):
    resumen_crudo = str(df_ia.iloc[0]['resumen_ia']).strip()
    if resumen_crudo:
        # Limpieza de seguridad anti-bloques de código (por si acaso)
        resumen_ia_db = resumen_crudo.replace("```markdown", "").replace("```", "").strip()

# Si tenemos el texto, lo asignamos; si no, mostramos el estado de carga.
if resumen_ia_db:
    mensaje_diagnostico = resumen_ia_db
else:
    mensaje_diagnostico = "⏳ *El motor de Inteligencia Artificial está procesando los datos de esta auditoría. El resumen estratégico aparecerá aquí en breve una vez que el sistema termine de redactarlo.*"

# Contenedor del mensaje
with st.container(border=True):
    col_icono, col_texto = st.columns([1, 11])
    with col_icono:
        st.markdown("### 💡")
    with col_texto:
        st.markdown(mensaje_diagnostico)

st.write("") # Espacio en blanco

# 1. Configuración de WhatsApp
numero_whatsapp = "51912867951" 
mensaje_ws = f"Hola equipo de N16. He revisado el dashboard de la auditoría de {cliente} y me gustaría agendar una reunión estratégica para conversar sobre los siguientes pasos."

# 2. Codificamos el mensaje
mensaje_codificado = urllib.parse.quote(mensaje_ws)

# 3. Construimos el enlace
link_whatsapp = f"https://wa.me/{numero_whatsapp}?text={mensaje_codificado}"

# 4. Diseño del Botón
col_vacia, col_boton = st.columns([7, 3]) 
with col_boton:
    st.link_button("💬 Agendar Reunión por WhatsApp", url=link_whatsapp, type="primary", use_container_width=True)