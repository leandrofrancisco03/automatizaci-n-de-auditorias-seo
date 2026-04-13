-- =============================================================================
-- SCRIPT DE INICIALIZACIÓN - AGENCIA N16
-- Ejecutar en PostgreSQL para crear la estructura de auditorías desde cero.
-- =============================================================================

CREATE TABLE IF NOT EXISTS auditorias_historico (
    id SERIAL PRIMARY KEY,
    auditoria_id VARCHAR(50) UNIQUE,
    cliente_nombre VARCHAR(255) NOT NULL,
    dominio VARCHAR(255) NOT NULL,
    fecha_auditoria TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    tipo_ejecucion VARCHAR(100),
    pin_acceso VARCHAR(10)
);

CREATE TABLE IF NOT EXISTS seo_rendimiento_lighthouse (
    id SERIAL PRIMARY KEY,
    auditoria_id VARCHAR(50),
    url_analizada VARCHAR(255) NOT NULL,
    dispositivo VARCHAR(50) NOT NULL,
    score_performance INTEGER,
    score_seo INTEGER,
    first_contentful_paint INTEGER,
    largest_contentful_paint INTEGER,
    cumulative_layout_shift NUMERIC,
    score_accesibilidad NUMERIC,
    score_buenas_practicas NUMERIC,
    speed_index_ms NUMERIC
);

CREATE TABLE IF NOT EXISTS seo_tecnico_onpage (
    id SERIAL PRIMARY KEY,
    auditoria_id VARCHAR(50),
    onpage_score NUMERIC,
    paginas_rastreadas INTEGER,
    tiene_sitemap BOOLEAN,
    tiene_robots_txt BOOLEAN,
    certificado_ssl_valido BOOLEAN,
    errores_4xx INTEGER,
    errores_5xx INTEGER,
    enlaces_rotos INTEGER,
    falta_h1 INTEGER,
    falta_meta_description INTEGER,
    falta_alt_imagenes INTEGER,
    meta_tags_duplicados INTEGER,
    paginas_lentas INTEGER
);

CREATE TABLE IF NOT EXISTS seo_errores_detalle (
    id SERIAL PRIMARY KEY,
    auditoria_id VARCHAR(50),
    url_pagina VARCHAR(500) NOT NULL,
    titulo_pagina VARCHAR(500),
    onpage_score NUMERIC,
    es_error_404 BOOLEAN,
    falta_h1 BOOLEAN,
    meta_duplicados BOOLEAN,
    contenido_duplicado BOOLEAN,
    imagenes_sin_alt BOOLEAN,
    es_lenta BOOLEAN
);

CREATE TABLE IF NOT EXISTS seo_brecha_competidores (
    id SERIAL PRIMARY KEY,
    auditoria_id VARCHAR(50),
    dominio_cliente VARCHAR(255) NOT NULL,
    dominio_competidor VARCHAR(255) NOT NULL,
    fecha_auditoria TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    keywords_oportunidad JSONB
);

CREATE TABLE IF NOT EXISTS seo_backlinks (
    id SERIAL PRIMARY KEY,
    auditoria_id VARCHAR(50),
    dominio_auditado VARCHAR(255) NOT NULL,
    fecha_auditoria TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rank_domain NUMERIC,
    total_backlinks NUMERIC,
    total_referring_domains NUMERIC,
    top_backlinks JSONB
);

CREATE TABLE IF NOT EXISTS seo_menciones_ia (
    id SERIAL PRIMARY KEY,
    auditoria_id VARCHAR(50),
    dominio_auditado VARCHAR(255) NOT NULL,
    fecha_auditoria TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    menciones_detalle JSONB
);