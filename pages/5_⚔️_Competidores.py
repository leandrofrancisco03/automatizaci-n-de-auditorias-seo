import streamlit as st
from db_manager import fetch_data
import pandas as pd
import json
import altair as alt

st.set_page_config(page_title="Competencia | An16", page_icon="⚔️", layout="wide")

# Validar seguridad/sesión
if 'auditoria_id_actual' not in st.session_state:
    st.warning("👈 Por favor, selecciona un cliente o inicia sesión en la página principal primero.")
    st.stop()

id_actual = st.session_state['auditoria_id_actual']
cliente = st.session_state['cliente_actual']

st.title(f"⚔️ Análisis de Competencia (Mercado Perdido)")
st.markdown(f"**Cliente:** {cliente} | Analizamos las búsquedas exactas que hacen tus clientes en Google y descubrimos quién se está llevando las ventas.")
st.write("---")

# --- 1. EXTRAER TUS DATOS REALES (Con las nuevas columnas) ---
nombre_tabla = "seo_brecha_competidores" 

# Añadimos tipo_competidor y trafico_competidor a la consulta
query = f"SELECT dominio_competidor, keywords_oportunidad, tipo_competidor, trafico_competidor FROM {nombre_tabla} WHERE auditoria_id = '{id_actual}'"
df_comp = fetch_data(query)

if df_comp.empty:
    st.info(f"Aún no hay datos de competidores orgánicos cargados.")
    st.stop()

# --- 2. RENDERIZAR DATOS POR COMPETIDOR ---
st.subheader("🥊 Enfrentamientos Estratégicos")
st.write("Selecciona a un competidor en las pestañas de abajo para ver el reporte de daños y oportunidades.")

# Creamos títulos de pestañas dinámicos e inteligentes
titulos_pestañas = []
for index, row in df_comp.iterrows():
    tipo = str(row.get('tipo_competidor', 'Competidor'))
    dom = row['dominio_competidor']
    if tipo == "Referente":
        titulos_pestañas.append(f"👑 Líder: {dom}")
    elif tipo == "Directo":
        titulos_pestañas.append(f"🥊 Rival: {dom}")
    else:
        titulos_pestañas.append(f"🆚 {dom}")

pestañas = st.tabs(titulos_pestañas)

for index, row in df_comp.iterrows():
    with pestañas[index]:
        competidor = row['dominio_competidor']
        tipo = str(row.get('tipo_competidor', ''))
        trafico_total = float(row.get('trafico_competidor') or 0)
        
        # --- MENSAJE ESTRATÉGICO SEGÚN EL TIPO DE COMPETIDOR ---
        if tipo == "Referente":
            st.info(f"👑 **El Gigante del Mercado:** Analizamos a `{competidor}` porque es el líder actual de tu nicho con un tráfico total estimado de **{trafico_total:,.0f} visitas al mes**. ¡Esta es la meta a largo plazo para tu negocio!")
        elif tipo == "Directo":
            st.warning(f"🥊 **Tu Amenaza Inmediata:** `{competidor}` es tu rival más cercano en la búsqueda de clientes (Tráfico: **{trafico_total:,.0f} visitas/mes**). Tienen un tamaño similar al tuyo, pero te están robando clics clave todos los días.")
        else:
            st.markdown(f"### Análisis de Brecha: `{cliente}` 🆚 `{competidor}`")
            
        try:
            datos_json = row['keywords_oportunidad']
            if isinstance(datos_json, str):
                datos_json = json.loads(datos_json)
                
            lista_kws = datos_json.get('lista', [])
            
            if lista_kws:
                df_kws = pd.DataFrame(lista_kws)
                
                # Forzar datos numéricos y redondear
                df_kws['volumen'] = pd.to_numeric(df_kws['volumen'], errors='coerce').fillna(0).astype(int)
                df_kws['cpc'] = pd.to_numeric(df_kws['cpc'], errors='coerce').fillna(0).round(2)
                df_kws['pos_cliente'] = pd.to_numeric(df_kws['pos_cliente'], errors='coerce').fillna(100).astype(int)
                df_kws['pos_competidor'] = pd.to_numeric(df_kws['pos_competidor'], errors='coerce').fillna(100).astype(int)
                
                # --- LÓGICA DE NEGOCIO (QUIÉN GANA) ---
                def determinar_ganador(fila):
                    if fila['pos_cliente'] < fila['pos_competidor']:
                        return "🟢 Ganamos"
                    elif fila['pos_cliente'] > fila['pos_competidor']:
                        return "🔴 Perdiendo"
                    else:
                        return "🟡 Empate"

                df_kws['Estado'] = df_kws.apply(determinar_ganador, axis=1)
                
                # --- PANEL DE URGENCIA (MÉTRICAS) ---
                batallas_perdidas = len(df_kws[df_kws['Estado'] == "🔴 Perdiendo"])
                total_batallas = len(df_kws)
                volumen_perdido = df_kws[df_kws['Estado'] == "🔴 Perdiendo"]['volumen'].sum()
                
                st.markdown("#### 🚨 Resumen de Daños Comerciales")
                col_m1, col_m2, col_m3 = st.columns(3)
                
                col_m1.metric(
                    "Servicios en los que te superan", 
                    f"{batallas_perdidas} de {total_batallas}",
                    delta="- Urgente recuperar" if batallas_perdidas > (total_batallas/2) else "Competitivo",
                    delta_color="inverse" if batallas_perdidas > (total_batallas/2) else "normal",
                    help="Cantidad de palabras (servicios/productos) donde este competidor aparece MÁS ARRIBA que tú en Google."
                )
                
                col_m2.metric(
                    "Tráfico Compartido en Riesgo", 
                    f"{volumen_perdido:,} búsquedas",
                    delta="Clientes potenciales yéndose a la competencia",
                    delta_color="off",
                    help="La suma total de personas al mes que buscan estos servicios compartidos y terminan viendo a tu competidor primero."
                )
                
                # Gráfico de barras simple para impacto visual
                conteo_estados = df_kws['Estado'].value_counts()
                
                with col_m3:
                    st.caption("Balance del Enfrentamiento")
                    
                    # 1. Convertimos los datos a un formato que Altair entiende mejor (DataFrame)
                    df_chart = conteo_estados.reset_index()
                    df_chart.columns = ["Estado", "Cantidad"]

                    # 2. Construimos el gráfico controlando el ángulo del texto
                    chart = alt.Chart(df_chart).mark_bar().encode(
                        x=alt.X("Estado", axis=alt.Axis(labelAngle=0, title=None)), # 🔥 MAGIA: labelAngle=0 hace el texto horizontal
                        y=alt.Y("Cantidad", axis=alt.Axis(title=None, tickMinStep=1)), # tickMinStep=1 evita números decimales raros en el eje Y
                        color=alt.Color(
                            "Estado",
                            scale=alt.Scale(
                                domain=["🔴 Perdiendo", "🟢 Ganamos"],
                                range=["#ff4b4b", "#00c04b"] # Asignamos los colores exactos
                            ),
                            legend=None # Ocultamos la leyenda para mantenerlo limpio
                        )
                    ).properties(height=150)

                    # 3. Mostramos el gráfico avanzado en lugar del básico
                    st.altair_chart(chart, use_container_width=True)
                    
                    st.markdown("---")

                # --- TABLA DE OPORTUNIDADES ---
                st.markdown("#### 📋 Detalle de Palabras Clave (El Botín)")
                st.write("Si logramos superar a la competencia en estas palabras exactas, esos clientes serán tuyos.")
                
                # Ordenamos para mostrar primero donde estamos perdiendo con mayor volumen
                df_kws = df_kws.sort_values(by=['Estado', 'volumen'], ascending=[False, False])
                
                df_mostrar = df_kws[['keyword', 'volumen', 'cpc', 'pos_cliente', 'pos_competidor', 'Estado']]
                df_mostrar = df_mostrar.rename(columns={
                    'keyword': 'Servicio Buscado (Palabra Clave)',
                    'volumen': 'Búsquedas al Mes',
                    'cpc': 'Costo en Google Ads ($)',
                    'pos_cliente': 'Tu Posición',
                    'pos_competidor': 'Posición del Rival'
                })
                
                st.dataframe(
                    df_mostrar,
                    use_container_width=True,
                    hide_index=True,
                    column_config={
                        "Servicio Buscado (Palabra Clave)": st.column_config.TextColumn(width="large"),
                        "Búsquedas al Mes": st.column_config.NumberColumn(
                            help="Cuántas personas escriben esto en Google cada mes.",
                            format="%d 🔍"
                        ),
                        "Costo en Google Ads ($)": st.column_config.NumberColumn(
                            help="Lo que tendrías que pagarle a Google por CADA CLIC si quisieras aparecer ahí. Te ahorras este dinero con SEO.",
                            format="$%.2f"
                        ),
                        "Tu Posición": st.column_config.NumberColumn(
                            help="Tu lugar en la lista de resultados (1 es el primero)."
                        ),
                        "Posición del Rival": st.column_config.NumberColumn(
                            help="Lugar del competidor. Si es menor al tuyo, ¡te están robando clics!"
                        )
                    }
                )
            else:
                st.success("No se detectó un cruce de palabras clave con este competidor.")
                
        except Exception as e:
            st.error(f"Error procesando el reporte de mercado: {e}")