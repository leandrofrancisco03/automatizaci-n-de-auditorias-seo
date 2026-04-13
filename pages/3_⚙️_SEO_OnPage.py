import streamlit as st
from db_manager import fetch_data
import pandas as pd

st.set_page_config(page_title="Auditoría Interna | An16", page_icon="⚙️", layout="wide")

# Validar seguridad/sesión
if 'auditoria_id_actual' not in st.session_state:
    st.warning("👈 Por favor, selecciona un cliente en la página principal primero.")
    st.stop()

id_actual = st.session_state['auditoria_id_actual']
cliente = st.session_state['cliente_actual']

st.title(f"⚙️ Auditoría Interna de la Página Web")
st.markdown(f"**Cliente:** {cliente} | Analizamos cada rincón de tu sitio web como si fuéramos el inspector de Google, buscando fallas que te impiden conseguir más clientes.")
st.write("---")

# --- 1. RESUMEN TÉCNICO GENERAL ---
query_resumen = f"SELECT * FROM seo_tecnico_onpage WHERE auditoria_id = '{id_actual}'"
df_resumen = fetch_data(query_resumen)

if df_resumen.empty:
    st.info("Aún no hay datos de rastreo para este cliente.")
    st.stop()

row = df_resumen.iloc[0]

st.subheader("📊 Salud General de la Web")
st.caption("Una vista rápida de los errores más críticos que pueden afectar tu negocio hoy mismo.")
col1, col2, col3 = st.columns(3) 

# Redondeamos el score general a un número entero
score_redondeado = int(round(float(row['onpage_score'])))

col1.metric("Puntuación Global de Salud", f"{score_redondeado}/100", help="Evaluación general de la estructura de tu web. Una nota por debajo de 80 requiere acción inmediata.")

enlaces_rotos = row['enlaces_rotos']
col2.metric("Enlaces Rotos (Llevan a la nada)", enlaces_rotos, delta="- Pérdida de ventas" if enlaces_rotos > 0 else "Todo en orden", delta_color="normal", help="Links dentro de tu web que no funcionan. Frustran al cliente y hacen que abandonen tu sitio.")

errores_criticos = row['errores_4xx'] + row['errores_5xx']
col3.metric("Páginas Caídas (Errores Severos)", errores_criticos, delta="- Urgente revisar" if errores_criticos > 0 else "Perfecto", delta_color="normal", help="Páginas que están completamente inaccesibles. Son un punto rojo gigante para Google.")


# --- SECCIÓN DE INDEXABILIDAD ---
st.write("### 🔎 Presencia en el Buscador de Google")
st.caption("Verificamos el volumen total de tu web en Google y analizamos una muestra técnica profunda.")
col_idx1, col_idx2 = st.columns(2)

rastreadas = int(row['paginas_rastreadas'])
indexadas = int(row.get('paginas_indexadas', 0)) 

help_rastreadas = "La cantidad de URLs que nuestro sistema escaneó a nivel técnico. Tomamos una muestra estratégica de tu web para detectar los patrones de error sin saturar tu servidor."
help_indexadas = "El total de páginas, artículos o servicios que Google tiene guardados en su memoria sobre tu negocio en este momento."

col_idx1.metric("Páginas Auditadas (Muestra)", rastreadas, help=help_rastreadas)
col_idx2.metric("Total de Páginas en Google", indexadas, help=help_indexadas)

st.write("---")

# --- SECCIÓN: ENLACES Y REDIRECCIONES ---
st.write("### 🔗 Rutas y Fugas de Tráfico")
col_link1, col_link2 = st.columns(2)

salientes = int(row.get('enlaces_salientes', 0))
redirecciones_3xx = int(row.get('errores_3xx', 0))

col_link1.metric("Enlaces que envían clientes afuera", salientes, help="Cuántos links tienes que envían a las personas a otras páginas web (como redes sociales u otras empresas). ¡Cuidado con enviar a tus clientes a la competencia!")
col_link2.metric("Redirecciones (Cambios de Ruta)", redirecciones_3xx, delta="- Hace lenta la navegación" if redirecciones_3xx > 0 else "Rutas directas", delta_color="normal", help="Páginas que envían automáticamente al usuario a otra página. Son como 'desvíos' en la carretera; si hay muchos, el cliente se cansa y Google también.")

st.write("---")

st.write("### 🛠️ Configuración Básica del Servidor")
st.caption("Los cimientos invisibles que Google exige antes de posicionarte.")
chk1, chk2, chk3, chk4 = st.columns(4)

chk1.metric("Mapa del Sitio", "✅ Encontrado" if row['tiene_sitemap'] else "❌ Faltante", help="Es el 'mapa' que le entregamos a Google para que no se pierda en tu web. Es vital tenerlo.")
chk2.metric("Permisos de Rastreo", "✅ Encontrado" if row['tiene_robots_txt'] else "❌ Faltante", help="El archivo 'Robots.txt' le dice a Google qué puede mirar y qué está prohibido ver en tu web.")
chk3.metric("Seguridad (Candadito Verde)", "✅ Válido" if row['certificado_ssl_valido'] else "❌ Peligro", help="El certificado SSL. Sin esto, el navegador dirá 'Sitio No Seguro' y los clientes huirán despavoridos.")

idioma_real = row.get('idioma_html', 'Desconocido')
chk4.metric("Idioma Principal", f"🌍 {idioma_real}", help="Le indica al navegador en qué idioma está tu web para traducciones correctas.")

# --- 2. DETALLE DE ERRORES (TABLAS) ---
st.markdown("---")
st.subheader("🔍 Listado Exacto de Tareas Pendientes")
st.write("Aquí están las direcciones exactas de las páginas que debemos arreglar. Este es el mapa de trabajo para el equipo.")

query_detalle = f"SELECT * FROM seo_errores_detalle WHERE auditoria_id = '{id_actual}'"
df_detalle = fetch_data(query_detalle)

if not df_detalle.empty:
    
    # Pestañas con lenguaje de negocio
    tabs = st.tabs([
        "🗂️ Todas las Páginas", 
        "🚨 Páginas Rotas o Caídas", 
        "🏷️ Problemas de Títulos", 
        "🖼️ Imágenes Invisibles para Google", 
        "📱 Problemas al Compartir", 
        "🐌 Servidor Lento",
        "📝 Contenido Pobre"
    ])
    
    def safe_col(df, col_name, default_val=False):
        return df.get(col_name, pd.Series([default_val]*len(df))).fillna(default_val)
    
    # --- PESTAÑA 1: TABLA MAESTRA ---
    with tabs[0]:
        st.markdown("**Vista general de todas las páginas rastreadas.**")
        df_maestra = df_detalle.drop(columns=['id', 'auditoria_id'], errors='ignore')
        
        # Redondeamos la puntuación a un número entero (opcional: usa round(1) si prefieres un decimal)
        if 'onpage_score' in df_maestra.columns:
            df_maestra['onpage_score'] = pd.to_numeric(df_maestra['onpage_score'], errors='coerce').round(0)
        
        # Diccionario masivo para traducir toda la base de datos al cliente
        diccionario_nombres = {
            'url_pagina': 'Página Web (URL)',
            'titulo_pagina': 'Título que lee Google',
            'onpage_score': 'Puntuación (/100)', # <-- Agregamos el /100 aquí
            'es_error_404': 'No Existe (404)',
            'falta_h1': 'Sin Título Principal',
            'meta_duplicados': 'Textos Repetidos',
            'contenido_duplicado': 'Contenido Copiado',
            'imagenes_sin_alt': 'Imágenes Invisibles',
            'es_lenta': 'Carga Lenta',
            'es_error_3xx': 'Desvío Automático',
            'falta_h2': 'Sin Subtítulos',
            'falta_open_graph': 'Mal en Redes Sociales',
            'contenido_pobre': 'Poca Información',
            'word_count': 'Cant. Palabras',
            'es_error_5xx': 'Servidor Caído'
        }
        
        # Renombramos usando el diccionario
        df_maestra = df_maestra.rename(columns=diccionario_nombres)
        
        # Renderizamos la tabla
        st.dataframe(df_maestra, use_container_width=True, hide_index=True)

    # --- PESTAÑA 2: ESTADOS (404, 5xx, 3xx) ---
    with tabs[1]:
        st.markdown("### 🚦 Páginas que no se pueden abrir")
        col_st1, col_st2, col_st3 = st.columns(3)
        
        with col_st1:
            df_404 = df_detalle[safe_col(df_detalle, 'es_error_404') == True]
            if not df_404.empty:
                st.error(f"**{len(df_404)} Páginas NO EXISTEN (Error 404)**\nEl cliente hace clic y ve una página de error.")
                st.dataframe(df_404[['url_pagina']], use_container_width=True, hide_index=True)
            else:
                st.success("Cero Errores 404. Ninguna página falta.")
                
        with col_st2:
            df_5xx = df_detalle[safe_col(df_detalle, 'es_error_5xx') == True]
            if not df_5xx.empty:
                st.error(f"**{len(df_5xx)} Páginas CAÍDAS (Error Servidor)**\nEl servidor colapsó al intentar abrir estas páginas.")
                st.dataframe(df_5xx[['url_pagina']], use_container_width=True, hide_index=True)
            else:
                st.success("Servidor estable. Cero caídas.")
                
        with col_st3:
            df_3xx = df_detalle[safe_col(df_detalle, 'es_error_3xx') == True]
            if not df_3xx.empty:
                st.warning(f"**{len(df_3xx)} Páginas con Desvíos (Redirecciones)**\nEl cliente es enviado a otra página automáticamente.")
                st.dataframe(df_3xx[['url_pagina']], use_container_width=True, hide_index=True)
            else:
                st.success("Rutas limpias y directas.")

    # --- PESTAÑA 3: H1 y H2 ---
    with tabs[2]:
        st.write("Google usa los títulos principales (H1) y subtítulos (H2) para entender de qué trata tu página. Si faltan, Google no sabe qué vendes.")
        col_h1, col_h2 = st.columns(2)
        with col_h1:
            st.markdown("### ❌ Falta Título Principal")
            df_h1 = df_detalle[safe_col(df_detalle, 'falta_h1') == True]
            if not df_h1.empty:
                st.error(f"¡Atención! {len(df_h1)} páginas no tienen un título principal. Es como un libro sin nombre.")
                st.dataframe(df_h1[['url_pagina']], use_container_width=True, hide_index=True)
            else:
                st.success("Todas las páginas tienen su título principal.")
                
        with col_h2:
            st.markdown("### ⚠️ Faltan Subtítulos")
            df_h2 = df_detalle[safe_col(df_detalle, 'falta_h2') == True]
            if not df_h2.empty:
                st.warning(f"{len(df_h2)} páginas están desordenadas por falta de subtítulos. Difícil de leer para el cliente.")
                st.dataframe(df_h2[['url_pagina']], use_container_width=True, hide_index=True)
            else:
                st.success("Excelente organización de texto.")

    # --- PESTAÑA 4: IMÁGENES SIN ALT ---
    with tabs[3]:
        st.write("Google es 'ciego'. Solo entiende de qué trata una imagen si le ponemos un texto descriptivo oculto. Si falta, pierdes oportunidad de aparecer en Google Imágenes.")
        df_alt = df_detalle[safe_col(df_detalle, 'imagenes_sin_alt') == True]
        if not df_alt.empty:
            st.warning(f"{len(df_alt)} páginas tienen imágenes 'invisibles' para Google. Debemos etiquetarlas.")
            st.dataframe(df_alt[['url_pagina', 'titulo_pagina']], use_container_width=True, hide_index=True)
        else:
            st.success("Todas las imágenes están correctamente descritas para Google.")

    # --- PESTAÑA 5: METAS Y OPEN GRAPH ---
    with tabs[4]:
        st.markdown("### 🌐 Qué ve el cliente antes de entrar")
        st.write("Estos errores afectan cómo se ve el 'cuadrito' de tu web cuando alguien la busca en Google o la comparte por WhatsApp/Facebook.")
        col_og1, col_og2 = st.columns(2)
        
        with col_og1:
            st.markdown("#### 📋 Textos Repetidos en Google")
            df_meta = df_detalle[safe_col(df_detalle, 'meta_duplicados') == True]
            if not df_meta.empty:
                st.warning(f"{len(df_meta)} páginas muestran el mismo título y descripción en Google. ¡Hay que diferenciarlas para que el cliente sepa a cuál entrar!")
                st.dataframe(df_meta[['url_pagina']], use_container_width=True, hide_index=True)
            else:
                st.success("Cada página tiene un mensaje único en Google.")
                
        with col_og2:
            st.markdown("#### 🔗 Se ve mal en WhatsApp/Facebook")
            df_og = df_detalle[safe_col(df_detalle, 'falta_open_graph') == True]
            if not df_og.empty:
                st.warning(f"Si alguien comparte {len(df_og)} de estas páginas en redes sociales, no saldrá imagen ni título atractivo.")
                st.dataframe(df_og[['url_pagina']], use_container_width=True, hide_index=True)
            else:
                st.success("Tu web está lista para ser compartida en redes.")

    # --- PESTAÑA 6: PÁGINAS LENTAS ---
    with tabs[5]:
        st.markdown("### 🐌 Servidor Ahogado")
        df_lentas = df_detalle[safe_col(df_detalle, 'es_lenta') == True]
        if not df_lentas.empty:
            st.error(f"¡Cuidado! Se encontraron {len(df_lentas)} páginas que tardan demasiado en responder. El cliente se irá a la competencia.")
            st.dataframe(df_lentas[['url_pagina', 'onpage_score']], use_container_width=True, hide_index=True)
        else:
            st.success("Las páginas cargan a la velocidad del rayo.")

    # --- PESTAÑA 7: CALIDAD DE CONTENIDO ---
    with tabs[6]:
        st.markdown("### 📝 Páginas 'Vacías' (Poco texto)")
        st.write("Si una página tiene menos de 300 palabras, Google piensa que es de 'baja calidad' y que no resuelve las dudas del cliente. No te posicionará bien.")
        df_pobre = df_detalle[safe_col(df_detalle, 'contenido_pobre') == True]
        if not df_pobre.empty:
            st.error(f"Se encontraron {len(df_pobre)} páginas con muy poca información. ¡Necesitamos redactar más texto de valor para el cliente!")
            columnas_a_mostrar = ['url_pagina', 'word_count'] if 'word_count' in df_pobre.columns else ['url_pagina']
            st.dataframe(df_pobre[columnas_a_mostrar], use_container_width=True, hide_index=True)
        else:
            st.success("Toda tu web tiene información abundante y útil para convencer al cliente.")

else:
    st.info("No se encontraron detalles de páginas individuales en la base de datos.")