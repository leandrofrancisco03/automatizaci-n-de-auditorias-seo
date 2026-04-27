import psycopg2
import psycopg2.extras
import markdown2
import datetime
import os
import base64
import re
import io
import json
import sys
import toml
import requests
import matplotlib.pyplot as plt
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

# --- 1. LECTURA SEGURA DE CREDENCIALES ---
ruta_base = os.path.dirname(os.path.abspath(__file__))
ruta_secrets = os.path.join(os.path.dirname(ruta_base), ".streamlit", "secrets.toml")

try:
    secrets = toml.load(ruta_secrets)
    DB_URL = f"postgresql://{secrets['DB_USER']}:{secrets['DB_PASS']}@{secrets.get('DB_HOST', '178.18.254.186')}:{secrets['DB_PORT']}/{secrets['DB_NAME']}"
    
    # CARGAMOS LA URL DEL WEBHOOK DESDE EL TOML
    WEBHOOK_URL = secrets.get('WEBHOOK_N8N') 
    
except Exception as e:
    print(f"❌ Error leyendo secrets.toml: {e}")
    sys.exit(1)

# --- 2. FUNCIONES DE APOYO Y GRÁFICOS ---
def generar_grafico_posiciones(lista_kws):
    if not lista_kws: return ""
    keywords = [(k['keyword'][:15] + '..') if len(k['keyword']) > 15 else k['keyword'] for k in lista_kws][:6]
    pos_cliente = [k['pos_cliente'] or 100 for k in lista_kws][:6]
    pos_comp = [k['pos_competidor'] or 100 for k in lista_kws][:6]

    fig, ax = plt.subplots(figsize=(10, 4.5), dpi=200)
    fig.patch.set_facecolor('#ffffff')
    ax.set_facecolor('#ffffff')

    x = range(len(keywords))
    width = 0.35
    
    bars1 = ax.bar(x, pos_cliente, width, label='Tu Posición', color='#0f3082', zorder=3)
    bars2 = ax.bar([i + width for i in x], pos_comp, width, label='Competidor', color='#f06c00', zorder=3)

    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_color('#dddddd')
    ax.spines['bottom'].set_color('#dddddd')
    ax.yaxis.grid(True, linestyle='-', color='#eeeeee', zorder=0)
    ax.set_axisbelow(True)

    ax.set_xticks([i + width/2 for i in x])
    ax.set_xticklabels(keywords, rotation=15, ha='right', fontsize=9)
    ax.set_ylabel('Posición en Google (Menor es mejor)', fontsize=10, color='#666666', labelpad=10)
    ax.invert_yaxis() 
    ax.legend(loc='lower center', bbox_to_anchor=(0.5, -0.3), ncol=2, frameon=False)
    
    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() - 5, f"{int(bar.get_height())}", ha='center', va='bottom', color='white', fontsize=8, fontweight='bold')
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() - 5, f"{int(bar.get_height())}", ha='center', va='bottom', color='white', fontsize=8, fontweight='bold')

    plt.tight_layout()
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight')
    plt.close()
    return base64.b64encode(img.getvalue()).decode()

def generar_grafico_distribucion_kw(top3, pag1, pag2, mas20):
    labels_completas = ['Top 3 (Líder)', 'Pos 4-10 (Pág 1)', 'Pos 11-20 (Pág 2)', 'Pos 21+ (Invisibles)']
    sizes_completos = [top3, pag1, pag2, mas20]
    colors_completos = ['#0f3082', '#00c04b', '#f06c00', '#dc3545']
    
    labels = [l for l, s in zip(labels_completas, sizes_completos) if s > 0]
    colors = [c for c, s in zip(colors_completos, sizes_completos) if s > 0]
    sizes = [s for s in sizes_completos if s > 0]
    
    if not sizes: return ""
    
    fig, ax = plt.subplots(figsize=(6, 4), dpi=200)
    wedges, texts, autotexts = ax.pie(
        sizes, colors=colors, startangle=90, 
        autopct='%1.1f%%', textprops=dict(color="w", weight="bold", fontsize=9),
        wedgeprops=dict(width=0.4, edgecolor='w', linewidth=2)
    )
    
    ax.legend(wedges, labels, title="Zonas de Google", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1), frameon=False, fontsize=9)
    plt.tight_layout()
    
    img = io.BytesIO()
    plt.savefig(img, format='png', bbox_inches='tight', transparent=True)
    plt.close()
    return base64.b64encode(img.getvalue()).decode()

def limpiar_respuesta_sge(texto):
    if not texto: return "No hay respuesta detectada."
    return re.sub(r'\[\[?(\d+)\]?\]\([^\)]+\)', r' [\1]', texto)

def procesar_lighthouse(lh_row):
    if not lh_row: return None
    lh = dict(lh_row)
    perf = int(round(float(lh.get('score_performance') or 0)))
    lh['perf_int'] = perf
    if perf < 50:
        lh['perf_color'], lh['perf_msg'] = "#dc3545", "🚨 Alerta Crítica: Tu página carga muy lento. Estás perdiendo clientes."
    elif perf < 90:
        lh['perf_color'], lh['perf_msg'] = "#f06c00", "⚠️ Precaución: Velocidad aceptable, pero hay 'cuellos de botella'."
    else:
        lh['perf_color'], lh['perf_msg'] = "#28a745", "✅ Excelente: Tu sitio está altamente optimizado."

    lcp = float(lh.get('largest_contentful_paint') or 0) / 1000
    lh['lcp_sec'], lh['lcp_color'] = f"{lcp:.1f}", "#28a745" if lcp <= 2.5 else "#dc3545" if lcp > 4.0 else "#f06c00"
    fcp = float(lh.get('first_contentful_paint') or 0) / 1000
    lh['fcp_sec'], lh['fcp_color'] = f"{fcp:.1f}", "#28a745" if fcp <= 1.8 else "#dc3545" if fcp > 3.0 else "#f06c00"
    si = float(lh.get('speed_index_ms') or 0) / 1000
    lh['si_sec'], lh['si_color'] = f"{si:.1f}", "#28a745" if si <= 3.4 else "#dc3545" if si > 5.8 else "#f06c00"
    cls = float(lh.get('cumulative_layout_shift') or 0)
    lh['cls_val'], lh['cls_color'] = f"{cls:.3f}", "#28a745" if cls <= 0.1 else "#dc3545" if cls > 0.25 else "#f06c00"
    return lh

def procesar_competidor(comp_data):
    if not comp_data: return None
    lista_kws = comp_data['keywords_oportunidad']['lista'] if (comp_data and comp_data['keywords_oportunidad']) else []
    batallas_perdidas = 0
    volumen_perdido = 0
    for kw in lista_kws:
        pos_cli = kw.get('pos_cliente') or 100
        pos_comp = kw.get('pos_competidor') or 100
        kw['cpc_limpio'] = f"{float(kw.get('cpc') or 0):.2f}"
        if pos_cli > pos_comp:
            batallas_perdidas += 1
            volumen_perdido += kw.get('volumen') or 0
    return {
        "dominio": comp_data['dominio_competidor'],
        "trafico": f"{int(float(comp_data['trafico_competidor'] or 0)):,}",
        "batallas_perdidas": batallas_perdidas,
        "total_batallas": len(lista_kws),
        "volumen_perdido": f"{volumen_perdido:,}",
        "es_critico": batallas_perdidas > (len(lista_kws) / 2) if lista_kws else False,
        "grafico": generar_grafico_posiciones(lista_kws),
        "lista_keywords": lista_kws[:6]
    }

# --- 3. MOTOR PRINCIPAL ---
def generar_auditoria_completa_pdf(auditoria_id):
    conn = None
    try:
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # 1. Histórico e IA
        cursor.execute("SELECT * FROM auditorias_historico WHERE auditoria_id = %s", (auditoria_id,))
        hist = cursor.fetchone()
        if not hist: return print("❌ Auditoría no encontrada.")
        texto_ia = re.sub(r'[\$]', '', hist['resumen_ia'] or '')
        diagnostico_html = markdown2.markdown(texto_ia)

        # 2. Competidores
        cursor.execute("SELECT dominio_competidor, tipo_competidor, trafico_competidor, keywords_oportunidad FROM seo_brecha_competidores WHERE auditoria_id = %s", (auditoria_id,))
        comps = cursor.fetchall()
        comp_directo = next((c for c in comps if c['tipo_competidor'] == 'Directo'), None)
        comp_referente = next((c for c in comps if c['tipo_competidor'] == 'Referente'), None)
        if not comp_directo and comps: comp_directo = comps[0]
        metricas_directo = procesar_competidor(comp_directo)
        metricas_referente = procesar_competidor(comp_referente)

        # 3. Keywords Propias
        cursor.execute("SELECT keywords_top FROM seo_keywords_posicionadas WHERE auditoria_id = %s", (auditoria_id,))
        kw_propias_row = cursor.fetchone()
        kw_metrics = {"total": 0, "top3": 0, "pag1": 0, "pag2": 0, "mas20": 0, "ahorro": 0}
        kw_top_lista, kw_urgentes_lista, graf_kw_dist = [], [], ""
        if kw_propias_row and kw_propias_row['keywords_top']:
            data_propias = kw_propias_row['keywords_top']
            if isinstance(data_propias, str):
                try: data_propias = json.loads(data_propias)
                except: data_propias = {}
            lista_propias = data_propias.get('lista', [])
            if lista_propias:
                kw_metrics["total"] = len(lista_propias)
                for kw in lista_propias:
                    pos = int(float(kw.get('posicion') or 100))
                    kw['posicion'] = pos
                    kw['volumen'] = int(float(kw.get('volumen') or 0))
                    kw['cpc_limpio'] = f"{float(kw.get('cpc') or 0):.2f}"
                    kw['trafico_estimado'] = float(kw.get('trafico_estimado') or 0)
                    kw_metrics["ahorro"] += kw['trafico_estimado']
                    if pos <= 3: kw_metrics["top3"] += 1
                    elif pos <= 10: kw_metrics["pag1"] += 1
                    elif pos <= 20: kw_metrics["pag2"] += 1
                    else: kw_metrics["mas20"] += 1
                kw_metrics["ahorro_str"] = f"{int(round(kw_metrics['ahorro'])):,}"
                kw_top_lista = sorted(lista_propias, key=lambda x: x['posicion'])[:5]
                lista_urgentes = [k for k in lista_propias if 11 <= k['posicion'] <= 20]
                kw_urgentes_lista = sorted(lista_urgentes, key=lambda x: x['volumen'], reverse=True)[:5]
                graf_kw_dist = generar_grafico_distribucion_kw(kw_metrics["top3"], kw_metrics["pag1"], kw_metrics["pag2"], kw_metrics["mas20"])

        # 4. OnPage General
        cursor.execute("SELECT * FROM seo_tecnico_onpage WHERE auditoria_id = %s", (auditoria_id,))
        onpage_row = cursor.fetchone()
        onpage = dict(onpage_row) if onpage_row else {}
        if onpage:
            onpage['onpage_score'] = int(round(float(onpage.get('onpage_score', 0))))

        # 5. RENDIMIENTO LIGHTHOUSE (MULTI-URL Y MÚLTIPLES DISPOSITIVOS)
        cursor.execute("SELECT * FROM seo_rendimiento_lighthouse WHERE auditoria_id = %s", (auditoria_id,))
        lh_rows = cursor.fetchall()
        lh_agrupado = {}
        for row in lh_rows:
            url = row['url_analizada']
            disp = str(row['dispositivo']).lower()
            if url not in lh_agrupado:
                lh_agrupado[url] = {"url": url, "mobile": None, "desktop": None}
            if disp == 'mobile':
                lh_agrupado[url]["mobile"] = procesar_lighthouse(row)
            elif disp == 'desktop':
                lh_agrupado[url]["desktop"] = procesar_lighthouse(row)
        lh_urls_lista = list(lh_agrupado.values())

        # 6. DETALLES TÉCNICOS (ERRORES Y URLs)
        cursor.execute("SELECT * FROM seo_errores_detalle WHERE auditoria_id = %s", (auditoria_id,))
        errores_detalle = cursor.fetchall()
        
        def agrupar_errores(condicion):
            urls = [e['url_pagina'] for e in errores_detalle if e.get(condicion)]
            return {"count": len(urls), "urls": urls[:5], "hay_mas": len(urls) > 5, "restantes": len(urls) - 5}

        detalles_seo = {
            "e404": agrupar_errores('es_error_404'),
            "e5xx": agrupar_errores('es_error_5xx'),
            "e3xx": agrupar_errores('es_error_3xx'),
            "h1": agrupar_errores('falta_h1'),
            "h2": agrupar_errores('falta_h2'),
            "alt": agrupar_errores('imagenes_sin_alt'),
            "meta": agrupar_errores('meta_duplicados'),
            "og": agrupar_errores('falta_open_graph'),
            "lenta": agrupar_errores('es_lenta'),
            "pobre": agrupar_errores('contenido_pobre')
        }

        # 7. Backlinks
        cursor.execute("SELECT * FROM seo_backlinks WHERE auditoria_id = %s", (auditoria_id,))
        bl_row = cursor.fetchone()
        bl_dict = dict(bl_row) if bl_row else {}
        bl_spam = int(round(float(bl_dict.get('spam_score_general') or 0)))
        bl_metrics = {
            "rank": int(round(float(bl_dict.get('rank_domain') or 0))),
            "dominios": f"{int(float(bl_dict.get('total_referring_domains') or 0)):,}",
            "enlaces": f"{int(float(bl_dict.get('total_backlinks') or 0)):,}",
            "spam": bl_spam,
            "spam_color": "#dc3545" if bl_spam > 30 else "#f06c00" if bl_spam > 10 else "#28a745",
            "spam_text": "Peligro" if bl_spam > 30 else "Revisar" if bl_spam > 10 else "Limpio"
        }
        top_links = bl_dict.get('top_backlinks')
        top_links_lista = []
        if top_links:
            if isinstance(top_links, str):
                try: top_links = json.loads(top_links)
                except: top_links = {}
            for link in top_links.get('enlaces', [])[:5]:
                rank_val = int(round(float(link.get('rank') or 0)))
                top_links_lista.append({"origen": link.get('url_origen', '')[:45] + '...', "anchor": link.get('anchor', 'Sin texto'), "rank": rank_val, "rank_pct": (rank_val / 1000) * 100, "ubicacion": link.get('ubicacion', 'Desconocida')})

        # 8. Reputación IA
        cursor.execute("SELECT menciones_detalle FROM seo_menciones_ia WHERE auditoria_id = %s", (auditoria_id,))
        ia_mentions = cursor.fetchone()
        menciones_limpias = []
        if ia_mentions and ia_mentions['menciones_detalle']:
            d_ia = ia_mentions['menciones_detalle']
            if isinstance(d_ia, str): d_ia = json.loads(d_ia.replace("[Object:", "").replace("]", ""))
            if isinstance(d_ia, list) and len(d_ia) > 0: d_ia = d_ia[0]
            for item in (d_ia.get('menciones_marca', []) + d_ia.get('menciones_dominio', []))[:3]:
                menciones_limpias.append({"pregunta": item.get('pregunta', ''), "respuesta": limpiar_respuesta_sge(item.get('respuesta', ''))})

        # --- PREPARAR PLANTILLA ---
        datos_plantilla = {
            "nombre_cliente": hist['cliente_nombre'],
            "dominio": hist['dominio'],
            "fecha": datetime.date.today().strftime("%d/%m/%Y"),
            "diagnostico_ia": diagnostico_html,
            "directo": metricas_directo,
            "referente": metricas_referente,
            "kw_metrics": kw_metrics,
            "kw_grafico": graf_kw_dist,
            "kw_top": kw_top_lista,
            "kw_urgentes": kw_urgentes_lista,
            "onpage": onpage,
            "detalles_seo": detalles_seo, # <--- ENVIAMOS LOS DETALLES CON URLs
            "lh_urls": lh_urls_lista,
            "bl_metrics": bl_metrics,      
            "top_links": top_links_lista,
            "menciones_ia": menciones_limpias
        }

        # --- RENDERIZAR ---
        env = Environment(loader=FileSystemLoader(ruta_base))
        template = env.get_template('plantilla_n16.html')
        html_content = template.render(datos_plantilla)

        output_dir = os.path.join(ruta_base, "reports")
        os.makedirs(output_dir, exist_ok=True)
        
        # 🔥 NUEVO: Limpiamos el nombre del cliente para que sea un archivo válido en Windows/Linux
        # Esto quitará símbolos raros y cambiará los espacios por guiones bajos.
        nombre_limpio = re.sub(r'[\\/*?:"<>|]', "", hist['cliente_nombre']).replace(" ", "_")
        
        # Creamos el nombre dinámico (Ej: Auditoria_N16_Cerrajeria_Nacional_2707.pdf)
        nombre_archivo = f"Auditoria_N16_{nombre_limpio}_{auditoria_id}.pdf"
        output_path = os.path.join(output_dir, nombre_archivo)
        
        # ... (código anterior) ...
        HTML(string=html_content, base_url=ruta_base).write_pdf(output_path)
        print(f"✅ ¡Éxito! Reporte corporativo generado localmente: {output_path}")

        # --- 9. ENVIAR EL PDF A n8n VÍA WEBHOOK ---
        if WEBHOOK_URL:
            print("🚀 Enviando reporte a n8n...")
            
            datos_post = {
                "cliente": hist['cliente_nombre'],
                "dominio": hist['dominio'],
                "auditoria_id": auditoria_id,
                "nombre_archivo": nombre_archivo
            }

            with open(output_path, 'rb') as archivo_pdf:
                archivos_post = {
                    'pdf_reporte': (nombre_archivo, archivo_pdf, 'application/pdf')
                }
                
                try:
                    # 🔥 AHORA USA LA VARIABLE DINÁMICA
                    respuesta = requests.post(WEBHOOK_URL, data=datos_post, files=archivos_post)
                    
                    if respuesta.status_code == 200:
                        print("✅ ¡PDF enviado exitosamente al webhook de n8n!")
                    else:
                        print(f"⚠️ Error en webhook (Código {respuesta.status_code}): {respuesta.text}")
                except Exception as err_req:
                    print(f"❌ Error de conexión con n8n: {err_req}")
        else:
            print("⚠️ No se encontró la URL del webhook en el secrets.toml, saltando envío.")

    except Exception as e:
        print(f"❌ Error fatal: {e}")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    id_input = sys.argv[1] if len(sys.argv) > 1 else input("Introduce auditoria_id: ")
    generar_auditoria_completa_pdf(id_input)