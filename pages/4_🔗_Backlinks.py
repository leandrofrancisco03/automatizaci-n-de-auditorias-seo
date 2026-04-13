import streamlit as st
from db_manager import fetch_data
import pandas as pd
import json

st.set_page_config(page_title="Autoridad Web | An16", page_icon="🔗", layout="wide")

# Validar seguridad/sesión
if 'auditoria_id_actual' not in st.session_state:
    st.warning("👈 Por favor, selecciona un cliente o inicia sesión en la página principal primero.")
    st.stop()

id_actual = st.session_state['auditoria_id_actual']
cliente = st.session_state['cliente_actual']

st.title(f"🔗 Autoridad y Relaciones Públicas Digitales")
st.markdown(f"**Cliente:** {cliente} | Analizamos qué otras páginas web te están recomendando. Para Google, cada enlace hacia tu web es un 'voto de confianza'.")
st.write("---")

# --- 1. EXTRAER DATOS DE LA BASE DE DATOS ---
query = f"SELECT * FROM seo_backlinks WHERE auditoria_id = '{id_actual}'"
df_backlinks = fetch_data(query)

if df_backlinks.empty:
    st.info("Aún no hay datos de Enlaces para este cliente.")
    st.stop()

row = df_backlinks.iloc[0]

# --- 2. MÉTRICAS GENERALES DE AUTORIDAD ---
st.subheader("📊 Nivel de Prestigio en Internet")
st.caption("Resumen de tu popularidad frente al algoritmo de Google.")

col1, col2, col3, col4 = st.columns(4)

# 1. Autoridad (Redondeada a entero y sobre 1000)
autoridad = int(round(float(row['rank_domain'] or 0)))
help_autoridad = "La 'reputación' general de tu dominio (de 0 a 1000). Se calcula en base a la cantidad y calidad de páginas que hablan de ti. A mayor número, más fácil posicionar."
col1.metric("Autoridad Web (Reputación)", f"{autoridad}/1000", help=help_autoridad)

# 2. Votos Únicos (Dominios)
dominios = int(row['total_referring_domains'] or 0)
help_dominios = "La cantidad de páginas web DIFERENTES que te mencionan. Es mejor tener 100 votos de 100 webs distintas, que 1000 votos de una sola web."
col2.metric("Webs que te recomiendan", f"{dominios:,.0f}", help=help_dominios)

# 3. Total de Enlaces
enlaces = int(row['total_backlinks'] or 0)
help_enlaces = "El volumen total de links que apuntan hacia ti. Si este número es gigantesco pero las 'Webs que te recomiendan' son muy pocas, Google podría considerarlo trampa."
col3.metric("Total de Votos (Enlaces)", f"{enlaces:,.0f}", help=help_enlaces)

# 4. Spam Score General (Nuevo campo) - Usamos .get por si acaso auditan webs viejas
spam_score = int(round(float(row.get('spam_score_general', 0))))
help_spam = "Mide si los enlaces que recibes vienen de sitios basura, rusos o peligrosos. Un número alto significa que necesitamos hacer una 'limpieza' urgente para evitar penalizaciones."

# Diagnóstico de Spam
if spam_score > 30:
    spam_delta = "- Peligro de Penalización"
    spam_color = "inverse"
elif spam_score > 10:
    spam_delta = "- Requiere Revisión"
    spam_color = "off"
else:
    spam_delta = "Perfil Limpio"
    spam_color = "normal"

col4.metric("Nivel de Toxicidad (Spam)", f"{spam_score}/100", delta=spam_delta, delta_color=spam_color, help=help_spam)


st.markdown("---")

# --- 3. DESGLOSE DEL JSONB (TOP BACKLINKS) ---
st.subheader("🏆 Tus Enlaces Más Poderosos (Top 5)")
st.write("Analizamos los sitios web de mayor calidad que actualmente dirigen clientes (y autoridad SEO) hacia tu negocio.")

try:
    # Extraemos el campo JSONB
    top_links_data = row['top_backlinks']
    
    if isinstance(top_links_data, str):
        top_links_data = json.loads(top_links_data)
        
    lista_enlaces = top_links_data.get('enlaces', [])
    
    if lista_enlaces:
        df_links = pd.DataFrame(lista_enlaces)
        
        # Procesamos los datos nuevos para que el cliente los entienda
        if 'ubicacion' in df_links.columns:
            # Traducimos las ubicaciones técnicas
            diccionario_ubicacion = {
                'article': 'En un Artículo (¡Excelente!)',
                'main': 'Cuerpo Principal',
                'footer': 'Pie de página (Poco valor)',
                'header': 'Cabecera del sitio',
                'sidebar': 'Barra lateral',
                'Desconocida': 'Desconocida'
            }
            df_links['ubicacion'] = df_links['ubicacion'].replace(diccionario_ubicacion)

        # Redondeamos la fuerza del enlace
        if 'rank' in df_links.columns:
            df_links['rank'] = pd.to_numeric(df_links['rank'], errors='coerce').fillna(0).round(0).astype(int)
            
        # Renombramos las columnas
        df_links = df_links.rename(columns={
            'url_origen': 'Web que te enlaza',
            'url_destino': 'Página tuya que recibe el link',
            'anchor': 'Texto del enlace (Lo que el cliente lee)',
            'rank': 'Fuerza del Voto (/1000)',
            'ubicacion': 'Ubicación en la web enemiga',
            'spam_score': 'Nivel de Riesgo'
        })
        
        # Filtramos solo las columnas que queremos mostrar para no marear al cliente
        columnas_mostrar = ['Web que te enlaza', 'Página tuya que recibe el link', 'Texto del enlace (Lo que el cliente lee)', 'Fuerza del Voto (/1000)', 'Ubicación en la web enemiga']
        
        # Si la columna existe en el dataframe, la mantenemos
        columnas_finales = [col for col in columnas_mostrar if col in df_links.columns]
        df_final = df_links[columnas_finales]
        
        # Renderizamos la tabla interactiva
        st.dataframe(
            df_final,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Web que te enlaza": st.column_config.LinkColumn(max_chars=50),
                "Página tuya que recibe el link": st.column_config.LinkColumn(max_chars=40),
                "Fuerza del Voto (/1000)": st.column_config.ProgressColumn(
                    "Fuerza del Voto (/1000)",
                    help="Qué tanta autoridad SEO te está regalando esta página web.",
                    format="%d",
                    min_value=0,
                    max_value=1000 
                )
            }
        )
        
        # Mensaje final de educación para el cliente
        st.info("💡 **Nota Estratégica:** Si la 'Ubicación' dice *Pie de página*, significa que el enlace probablemente fue comprado o es un directorio automático. Google le da **mucho más valor** a los enlaces que están de forma natural dentro de un *Artículo*.")
        
    else:
        st.info("No se encontraron enlaces de alta calidad apuntando a tu sitio web. ¡Es una gran oportunidad para iniciar una campaña de PR Digital!")

except Exception as e:
    st.error(f"El sistema está procesando el detalle de los enlaces. Por favor, recargue en unos minutos. (Log: {e})")