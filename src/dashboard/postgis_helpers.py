import streamlit as st
import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine


@st.cache_resource
def get_postgis_engine():
    connection_string = st.secrets["postgis"]["connection_string"]
    return create_engine(connection_string)


def _marcar_modo_demo():
    st.session_state["modo_demo"] = True


@st.cache_data(ttl=300)
def fetch_climate_observations(fecha_desde=None, fecha_hasta=None):
    engine = get_postgis_engine()
    query = "SELECT * FROM climate_observations WHERE 1=1"
    params = {}
    if fecha_desde:
        query += " AND observation_date >= %(fecha_desde)s"
        params["fecha_desde"] = fecha_desde
    if fecha_hasta:
        query += " AND observation_date <= %(fecha_hasta)s"
        params["fecha_hasta"] = fecha_hasta
    gdf = gpd.read_postgis(query, engine, geom_col="geom", params=params or None)
    return gdf


@st.cache_data(ttl=300)
def fetch_ultimo_indice_enso():
    engine = get_postgis_engine()
    query = "SELECT * FROM enso_indices ORDER BY index_date DESC LIMIT 1"
    df = pd.read_sql(query, engine)
    return df.iloc[0] if not df.empty else None


DUMMY_RIOS_RIESGO = [
    {"rio_nombre": "Río Portoviejo", "nivel_riesgo": "Alto"},
    {"rio_nombre": "Río Babahoyo",   "nivel_riesgo": "Alto"},
    {"rio_nombre": "Río Daule",      "nivel_riesgo": "Medio"},
    {"rio_nombre": "Río Guayas",     "nivel_riesgo": "Medio"},
    {"rio_nombre": "Río Esmeraldas", "nivel_riesgo": "Bajo"},
    {"rio_nombre": "Río Cañar",      "nivel_riesgo": "Bajo"},
]


@st.cache_data(ttl=300)
def fetch_rios_riesgo(n=6):
    try:
        engine = get_postgis_engine()
        df = pd.read_sql(
            "SELECT rio_nombre, nivel_riesgo FROM rios_riesgo ORDER BY RANDOM() LIMIT %(n)s",
            engine,
            params={"n": n},
        )
        return df.to_dict("records")
    except Exception as e:
        print(f"[fetch_rios_riesgo] fallback a dummy data: {e}")
        _marcar_modo_demo()
        return DUMMY_RIOS_RIESGO[:n]


DUMMY_ZONAS_AFECTADAS = [
    {"provincia": "Manabí",     "zona": "Manta",      "area_km2": 12.4, "precipitacion_mm": 68, "nivel": "Alto"},
    {"provincia": "Guayas",     "zona": "Durán",      "area_km2": 8.1,  "precipitacion_mm": 45, "nivel": "Medio"},
    {"provincia": "Los Ríos",   "zona": "Babahoyo",   "area_km2": 15.7, "precipitacion_mm": 71, "nivel": "Alto"},
    {"provincia": "El Oro",     "zona": "Machala",    "area_km2": 6.3,  "precipitacion_mm": 32, "nivel": "Medio"},
    {"provincia": "Esmeraldas", "zona": "Esmeraldas", "area_km2": 9.8,  "precipitacion_mm": 25, "nivel": "Bajo"},
]


@st.cache_data(ttl=300)
def fetch_zonas_afectadas(n=5):
    try:
        engine = get_postgis_engine()
        df = pd.read_sql(
            """
            SELECT provincia, zona, area_km2, precipitacion_mm, nivel
            FROM zonas_afectadas
            ORDER BY RANDOM()
            LIMIT %(n)s
            """,
            engine,
            params={"n": n},
        )
        return df.to_dict("records")
    except Exception as e:
        print(f"[fetch_zonas_afectadas] fallback a dummy data: {e}")
        _marcar_modo_demo()
        return DUMMY_ZONAS_AFECTADAS[:n]


DUMMY_ZONAS_RIESGO = [
    {"provincia": "Manabí",     "zona": "Manta",      "irc": 0.82, "personas": 15400, "nivel": "Alto",  "trend": "up"},
    {"provincia": "Guayas",     "zona": "Durán",      "irc": 0.71, "personas": 9800,  "nivel": "Alto",  "trend": "stable"},
    {"provincia": "Los Ríos",   "zona": "Babahoyo",   "irc": 0.65, "personas": 12200, "nivel": "Medio", "trend": "up"},
    {"provincia": "El Oro",     "zona": "Machala",    "irc": 0.48, "personas": 7300,  "nivel": "Medio", "trend": "down"},
    {"provincia": "Esmeraldas", "zona": "Esmeraldas", "irc": 0.33, "personas": 5100,  "nivel": "Bajo",  "trend": "stable"},
]


@st.cache_data(ttl=300)
def fetch_zonas_riesgo():
    try:
        engine = get_postgis_engine()
        df = pd.read_sql(
            """
            SELECT provincia, zona, irc, personas, nivel, trend
            FROM zonas_riesgo
            ORDER BY irc DESC
            LIMIT 10
            """,
            engine,
        )
        return df.to_dict("records")
    except Exception as e:
        print(f"[fetch_zonas_riesgo] fallback a dummy data: {e}")
        _marcar_modo_demo()
        return DUMMY_ZONAS_RIESGO