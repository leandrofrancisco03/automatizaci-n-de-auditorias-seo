"""import streamlit as st
from db_manager import fetch_data
import pandas as pd
import json
import re # <-- ¡NUEVO! Importamos la librería de Expresiones Regulares

st.set_page_config(page_title="Reputación IA | An16", page_icon="🤖", layout="wide")

# Validar seguridad/sesión
if 'auditoria_id_actual' not in st.session_state:
    st.warning("👈 Por favor, selecciona un cliente o inicia sesión en la página principal primero.")
    st.stop()

id_actual = st.session_state['auditoria_id_actual']
cliente = st.session_state['cliente_actual']

st.title(f"🤖 Auditoría de Reputación IA (SGE / LLMs)")
st.markdown(f"**Cliente:** {cliente} | Análisis de las respuestas de motores generativos ante búsquedas clave.")
st.write("---")

# --- 1. EXTRAER DATOS DE LA BD ---
query = f"SELECT fecha_auditoria, menciones_detalle FROM seo_menciones_ia WHERE auditoria_id = '{id_actual}'"
df_ia = fetch_data(query)

if df_ia.empty:
    st.info("Aún no hay datos de menciones de Inteligencia Artificial para este cliente.")
    st.stop()

row = df_ia.iloc[0]
fecha = row['fecha_auditoria'].strftime('%d de %B, %Y')

# --- FUNCIÓN DE LIMPIEZA DE MARKDOWN SGE ---
def limpiar_respuesta_sge(texto):
    #Limpia las citas hipervinculadas estilo [[1]](url) del texto crudo.
    if not texto: return "No hay respuesta."
    # Esta regex busca patrones como [[1]](https://...) o [1](https://...) y deja solo el [1]
    texto_limpio = re.sub(r'\[\[?(\d+)\]?\]\([^\)]+\)', r' [\1]', texto)
    return texto_limpio

try:
    # --- 2. PROCESAMIENTO DEL JSON ---
    datos_ia = row['menciones_detalle']
    
    # Manejar caso en el que la BD devuelve una lista envuelta en string o JSON directo
    if isinstance(datos_ia, str):
        # A veces n8n inserta un string literal "[Object: {...}]", intentamos limpiarlo si es necesario
        if datos_ia.startswith("[Object:"):
             st.error("⚠️ Error de n8n: El JSON se guardó como string literal '[Object...]'. Debes usar JSON.stringify() en n8n antes de insertarlo en SQL.")
             st.stop()
        datos_ia = json.loads(datos_ia)

    # Si viene como lista (ej: tu ejemplo empezaba con '[' en el texto crudo)
    if isinstance(datos_ia, list) and len(datos_ia) > 0:
        datos_ia = datos_ia[0]

    # --- 3. DISEÑO BASADO EN PREGUNTA / RESPUESTA ---
    menciones_marca = datos_ia.get('menciones_marca', [])
    menciones_dominio = datos_ia.get('menciones_dominio', [])
    
    # Unificamos ambas listas por si tienes datos en las dos
    todas_las_menciones = menciones_marca + menciones_dominio

    if todas_las_menciones:
        st.markdown(f"*(Reporte extraído por el motor de IA de An16 el {fecha})*")
        st.write("A continuación, se muestran las respuestas literales generadas por la IA ante consultas de usuarios reales.")
        st.write("") 

        for idx, item in enumerate(todas_las_menciones):
            pregunta = item.get('pregunta', 'Consulta Desconocida')
            respuesta_cruda = item.get('respuesta', '')
            links = item.get('links', [])
            
            # Limpiamos el texto usando nuestra función Regex
            respuesta_limpia = limpiar_respuesta_sge(respuesta_cruda)
            
            with st.expander(f"💬 Búsqueda simulada: « {pregunta.title()} »", expanded=(idx == 0)):
                
                # Renderizamos el texto ya limpio de la basura de los enlaces
                st.markdown(respuesta_limpia)
                
                # Renderizar los enlaces (Fuentes) al final
                if links:
                    st.markdown("---")
                    st.markdown("📚 **Fuentes citadas por la IA:**")
                    
                    for i, link in enumerate(links):
                        url_limpia = link.split("#:~:text")[0] 
                        texto_enlace = url_limpia
                        if len(texto_enlace) > 70:
                            texto_enlace = texto_enlace[:70] + "..."
                            
                        st.markdown(f"**[{i+1}]** [{texto_enlace}]({link})")
    else:
        st.info("El JSON se procesó correctamente, pero las listas de menciones están vacías.")

    # --- 4. ZONA DE INGENIERÍA ---
    st.write("---")
    with st.expander("🛠️ Ver Datos Crudos (Solo Agencia)"):
        st.json(datos_ia)

except json.JSONDecodeError:
     st.error("Error crítico: El campo en la base de datos no es un JSON válido. Verifica el nodo de inserción SQL en n8n.")
except Exception as e:
    st.error(f"Error procesando la respuesta de la IA: {e}")

"""