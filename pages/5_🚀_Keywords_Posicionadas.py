import streamlit as st
from db_manager import fetch_data
import pandas as pd
import json

st.set_page_config(page_title="Tráfico y Posicionamiento | An16", page_icon="🚀", layout="wide")

# Validar seguridad/sesión
if 'auditoria_id_actual' not in st.session_state:
    st.warning("👈 Por favor, selecciona un cliente o inicia sesión en la página principal primero.")
    st.stop()

id_actual = st.session_state['auditoria_id_actual']
cliente = st.session_state['cliente_actual']

st.title(f"🚀 Tu Presencia Actual en Google (Tráfico Orgánico)")
st.markdown(f"**Cliente:** {cliente} | Descubrimos cómo te buscan tus clientes exactos y cuánto dinero te estás ahorrando al no pagarle a Google Ads por esos clics.")
st.write("---")

# --- EXTRAER DATOS ---
query_propias = f"SELECT * FROM seo_keywords_posicionadas WHERE auditoria_id = '{id_actual}'"
df_propias = fetch_data(query_propias)

if df_propias.empty:
    st.info("Aún no hay datos de palabras clave posicionadas procesados para este cliente.")
    st.stop()

try:
    row = df_propias.iloc[0]
    data_propias = row['keywords_top']
    
    if isinstance(data_propias, str):
        data_propias = json.loads(data_propias)
        
    lista_propias = data_propias.get('lista', [])
    
    if lista_propias:
        df_kw_propias = pd.DataFrame(lista_propias)
        
        # Limpieza y conversión estricta de números para gráficos y tablas
        df_kw_propias['volumen'] = pd.to_numeric(df_kw_propias['volumen'], errors='coerce').fillna(0).astype(int)
        df_kw_propias['posicion'] = pd.to_numeric(df_kw_propias['posicion'], errors='coerce').fillna(100).astype(int)
        df_kw_propias['cpc'] = pd.to_numeric(df_kw_propias['cpc'], errors='coerce').fillna(0.0).round(2)
        
        # Si la API no devuelve trafico_estimado, lo calculamos o lo ponemos en 0
        if 'trafico_estimado' not in df_kw_propias.columns:
            df_kw_propias['trafico_estimado'] = 0.0
        else:
            df_kw_propias['trafico_estimado'] = pd.to_numeric(df_kw_propias['trafico_estimado'], errors='coerce').fillna(0.0).round(2)
        
        # Ordenar por posición (las mejores primero en Google)
        df_kw_propias = df_kw_propias.sort_values(by='posicion', ascending=True)
        
        # --- MÉTRICAS ESTRATÉGICAS ---
        total_kw = len(df_kw_propias)
        top_3 = len(df_kw_propias[df_kw_propias['posicion'] <= 3])
        pag_1_resto = len(df_kw_propias[(df_kw_propias['posicion'] > 3) & (df_kw_propias['posicion'] <= 10)])
        pagina_2 = len(df_kw_propias[(df_kw_propias['posicion'] >= 11) & (df_kw_propias['posicion'] <= 20)])
        
        # Ahorro estimado en Ads (Redondeado a entero)
        ahorro_ads = int(round(df_kw_propias['trafico_estimado'].sum()))
        
        st.subheader("📊 Resumen del Valor de tu Tráfico")
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric("Términos Posicionados", total_kw, help="Total de frases por las que Google considera que eres relevante en el Top 100.")
        col2.metric("Líder del Mercado (Top 3)", top_3, help="Posiciones 1, 2 o 3. Aquí te llevas más del 50% de todos los clics y clientes.")
        col3.metric("A un paso del éxito (Página 2)", pagina_2, delta="¡Oportunidad Urgente!", delta_color="normal", help="Estás en las posiciones 11 al 20. Nadie pasa a la página 2. Si hacemos un empujón SEO, estas palabras subirán a la página 1 y tus ventas explotarán.")
        col4.metric("Ahorro Mensual en Ads", f"${ahorro_ads:,}", help="Si tuvieras que pagarle a Google Ads por cada clic que recibes gratis hoy, esto es lo que te costaría. ¡El SEO ya te está ahorrando dinero!")
        
        st.write("---")

        # --- SECCIÓN GRÁFICA (Visualizando el Embudo) ---
        st.subheader("📈 Distribución de tu Visibilidad en Google")
        col_graf1, col_graf2 = st.columns([1, 1])
        
        with col_graf1:
            st.caption("¿En qué página de Google estás realmente?")
            st.write("Idealmente, queremos que la mayoría de tus palabras estén en color verde (Página 1).")
            # Preparamos los datos para el gráfico de barras
            dist_data = {
                "Top 3 (Mina de oro)": top_3, 
                "Pos 4-10 (1ra Página)": pag_1_resto, 
                "Pos 11-20 (2da Página)": pagina_2, 
                "Pos 21+ (Casi Invisibles)": len(df_kw_propias[df_kw_propias['posicion'] > 20])
            }
            df_dist = pd.DataFrame(list(dist_data.items()), columns=['Zona de Google', 'Cantidad de Palabras']).set_index('Zona de Google')
            
            # Gráfico de barras de Streamlit
            st.bar_chart(df_dist, color="#00c04b", height=250)

        with col_graf2:
            st.caption("Tus Oportunidades más urgentes (A punto de caramelo)")
            st.write("Estos son los servicios muy buscados donde estás en **Página 2**. ¡Son nuestra prioridad estratégica!")
            
            # Filtramos solo página 2 y ordenamos por las que tienen MÁS búsquedas
            df_urgentes = df_kw_propias[(df_kw_propias['posicion'] >= 11) & (df_kw_propias['posicion'] <= 20)]
            df_urgentes = df_urgentes.sort_values(by='volumen', ascending=False).head(5) # Mostramos el top 5 urgente
            
            if not df_urgentes.empty:
                # Preparamos gráfico
                df_graf_urgentes = df_urgentes[['keyword', 'volumen']].set_index('keyword')
                st.bar_chart(df_graf_urgentes, color="#ffa421", height=250) # Naranja de alerta
            else:
                st.info("No tienes palabras estancadas en la página 2 en este momento.")

        st.write("---")
        
        # --- TABLA DETALLADA ---
        st.subheader("🔍 Desglose Detallado por Servicio/Palabra")
        st.write("El mapa completo de las búsquedas. Fíjate en el 'Costo por Clic' para entender cuán competitiva es esa palabra en tu sector.")
        
        df_display = df_kw_propias[['keyword', 'volumen', 'posicion', 'cpc', 'trafico_estimado']].copy()
        df_display = df_display.rename(columns={
            'keyword': 'Servicio Buscado (Qué escribe el cliente)',
            'volumen': 'Búsquedas al Mes',
            'posicion': 'Tu Lugar en Google',
            'cpc': 'Costo en Google Ads ($)',
            'trafico_estimado': 'Ahorro Estimado ($)'
        })
        
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Servicio Buscado (Qué escribe el cliente)": st.column_config.TextColumn(width="large"),
                "Tu Lugar en Google": st.column_config.NumberColumn(
                    help="Tu posición real. 1 al 10 significa que estás en la primera página.",
                    format="%d 🏆"
                ),
                "Búsquedas al Mes": st.column_config.NumberColumn(
                    help="El tamaño del pastel. Cuánta gente pide esto al mes.",
                    format="%d 🔎"
                ),
                "Costo en Google Ads ($)": st.column_config.NumberColumn(
                    help="Lo que paga tu competencia por cada clic.",
                    format="$ %.2f"
                ),
                "Ahorro Estimado ($)": st.column_config.NumberColumn(
                    help="Multiplicamos el tráfico que recibes por el costo de Ads. Esto es dinero que se queda en tu bolsillo.",
                    format="$ %.2f"
                )
            }
        )
        
    else:
        st.warning(f"No se detectaron palabras clave posicionadas en los primeros 100 resultados para el dominio {cliente}.")

except Exception as e:
    st.error(f"Ocurrió un error al procesar las palabras clave: {e}")