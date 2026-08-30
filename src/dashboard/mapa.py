import streamlit as st
from streamlit_folium import st_folium
import folium
from postgis_helpers import fetch_climate_observations


DUMMY_OBSERVACIONES = [
    {"station_id": "M001", "source": "CHIRPS", "observation_date": "2026-08-15", "precipitation_mm": 65, "lat": -0.9520, "lon": -80.7180},
    {"station_id": "M002", "source": "GPM",    "observation_date": "2026-08-15", "precipitation_mm": 28, "lat": -0.9420, "lon": -80.6980},
    {"station_id": "M003", "source": "NOAA",   "observation_date": "2026-08-15", "precipitation_mm": 8,  "lat": -0.9800, "lon": -80.7350},
    {"station_id": "M004", "source": "CHIRPS", "observation_date": "2026-08-14", "precipitation_mm": 45, "lat": -0.9650, "lon": -80.7050},
]

def agregar_observaciones_postgis(m, fecha_desde=None, fecha_hasta=None):
    try:
        gdf = fetch_climate_observations(fecha_desde, fecha_hasta)
        registros = [
            {
                "station_id": row["station_id"],
                "source": row["source"],
                "observation_date": row["observation_date"],
                "precipitation_mm": row.get("precipitation_mm"),
                "lat": row.geom.y,
                "lon": row.geom.x,
            }
            for _, row in gdf.iterrows()
        ]
    except Exception:
        st.warning("No se pudo conectar a PostGIS — mostrando datos de ejemplo.")
        registros = DUMMY_OBSERVACIONES

    for r in registros:
        precip = r["precipitation_mm"]
        color = "gray"
        if precip is not None:
            if precip >= 60:
                color = "red"
            elif precip >= 20:
                color = "orange"
            else:
                color = "green"

        folium.CircleMarker(
            location=[r["lat"], r["lon"]],
            radius=6,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            popup=(
                f'{r["station_id"]} ({r["source"]})<br>'
                f'{r["observation_date"]}<br>'
                f'Precipitación: {precip} mm'
            ),
        ).add_to(m)

    return m


MANTA_CENTER = [-0.9677, -80.7089]
MANTA_ZOOM = 13

ZONAS_MANTA = [
    {"nombre": "Tarqui",       "lat": -0.9520, "lon": -80.7180, "radio": 1200, "color": "red",    "nivel": "Alto riesgo"},
    {"nombre": "Los Esteros",  "lat": -0.9420, "lon": -80.6980, "radio": 1500, "color": "orange", "nivel": "Riesgo medio"},
    {"nombre": "Barbasquillo", "lat": -0.9800, "lon": -80.7350, "radio": 1300, "color": "blue",   "nivel": "Zona segura"},
]

MALLA_PRUEBA = [
    [-0.960, -80.718],
    [-0.958, -80.712],
    [-0.963, -80.705],
    [-0.970, -80.703],
    [-0.976, -80.708],
    [-0.974, -80.716],
    [-0.967, -80.720],
]

def construir_mapa_manta(zonas=None, center=MANTA_CENTER, zoom=MANTA_ZOOM,
                          mostrar_malla_prueba=False, malla=None):
    zonas = zonas if zonas is not None else ZONAS_MANTA
    m = folium.Map(location=center, zoom_start=zoom, tiles="OpenStreetMap")

    for z in zonas:
        folium.Circle(
            location=[z["lat"], z["lon"]],
            radius=z["radio"],
            color=z["color"],
            weight=3,
            fill=True,
            fill_color=z["color"],
            fill_opacity=0.35,
            popup=f'{z["nombre"]} — {z["nivel"]}',
        ).add_to(m)

    if mostrar_malla_prueba:
        agregar_zona_poligono(m, coords=malla or MALLA_PRUEBA)

    return m


def agregar_zona_poligono(m, coords=None, color="red",
                           fill_opacity=0.25, tooltip="Zona afectada Crítico"):
    """Agrega un polígono (malla) de zona afectada a un mapa folium existente."""
    coords = coords if coords is not None else MALLA_PRUEBA
    folium.Polygon(
        locations=coords,
        color=color,
        weight=2,
        fill=True,
        fill_color=color,
        fill_opacity=fill_opacity,
        tooltip=tooltip,
    ).add_to(m)
    return m


def render_mapa(map_obj=None, height=700, width=700,
                 titulo="Mapa de Riesgo — Ecuador Continental",
                 container_key="mapa-wrap", map_key="mapa-principal"):
    if map_obj is None:
        map_obj = construir_mapa_manta()
    with st.container(border=True, key=container_key):
        st.markdown(
            f'<div style="padding:4px 4px 10px 4px;">'
            f'<span style="font-size:12px; font-weight:700; text-transform:uppercase; '
            f'letter-spacing:0.06em; color:#3a4a6e;">{titulo}</span></div>',
            unsafe_allow_html=True,
        )
        resultado = st_folium(
            map_obj,
            height=height,
            width=width,
            returned_objects=[],
            key=map_key,
        )
    return resultado