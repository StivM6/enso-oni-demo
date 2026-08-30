import streamlit as st
from streamlit_folium import st_folium
import folium
import datetime

import base64
from pathlib import Path

_LOGO_PATH = Path(__file__).resolve().parents[1] / "assets" / "logo_enso.webp"

from mapa import construir_mapa_manta, render_mapa, agregar_observaciones_postgis
from postgis_helpers import fetch_rios_riesgo, fetch_zonas_afectadas, fetch_zonas_riesgo
from eda_enso import render_seccion_eda


def _espaciador(px=20):
    st.markdown(f'<div style="height:{px}px;"></div>', unsafe_allow_html=True)


def _inject_theme_css():
    st.markdown("""
    <style>

    .stApp {
        background-color: #F0F2F6;
    }


    .st-key-header-card,
    .st-key-kpi-wrap,
    .st-key-kpi-box-1,
    .st-key-kpi-box-2,
    .st-key-listas-wrap,
    .st-key-mapa-wrap,
    .st-key-kpi-final-wrap,
    .st-key-kpi-final-box-1,
    .st-key-kpi-final-box-2,
    .st-key-eda-enso-wrap,
    div[class*="st-key-lista-row-"] {
        background-color: #FFFFFF;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

@st.cache_resource
def _cargar_logo_base64():
    with open(_LOGO_PATH, "rb") as f:
        return base64.b64encode(f.read()).decode()


def _render_header_logo():
    logo_b64 = _cargar_logo_base64()
    st.markdown(
        f'<div style="white-space:nowrap; line-height:38px;">'
        f'<img src="data:image/webp;base64,{logo_b64}" '
        f'style="height:34px; vertical-align:middle;">'
        f'</div>',
        unsafe_allow_html=True,
    )

def _render_header_nav():

    return st.segmented_control(
        "Vista",
        options=["Dashboard", "Por Provincia"],
        format_func=lambda x: (
            f":material/dashboard: {x}" if x == "Dashboard"
            else f":material/location_on: {x}"
        ),
        default="Dashboard",
        label_visibility="collapsed",
        key="nav_view",
    )

def _render_header_actions():

    a1, a2, a3 = st.columns([2, 2, 1])
    with a1:
        pass
    with a2:
        pass
    with a3:
        pass


def _render_header():
    with st.container(border=True, key="header-card"):

        col_logo, gap, col_nav, col_spacer, col_actions = st.columns(
            [1, 2, 4, 3, 2]
        )

        with col_logo:
            _render_header_logo()

        with gap:
            pass

        with col_nav:
            vista = _render_header_nav()

        with col_spacer:
            pass

        with col_actions:
            _render_header_actions()

    return vista

NIVEL_A_STEP = {
    "bajo": 1,
    "medio": 2,
    "alto": 3,
    "critico": 4,
    "crítico": 4,
}

def _render_listas():
    col_izq, col_der = st.columns(2)
    with col_izq:
        _render_kpi_card()

    rios_data = fetch_rios_riesgo()

    if rios_data:
        rios = [r["rio_nombre"] for r in rios_data]
        progreso_filas = [
            NIVEL_A_STEP.get(str(r["nivel_riesgo"]).strip().lower(), 1)
            for r in rios_data
        ]
    else:
        rios = ["Guayas", "Babahoyo", "Daule", "Esmeraldas", "Portoviejo", "Pastaza"]
        progreso_filas = [1, 3, 2, 4, 1, 3]

    steps = ["BAJO", "MEDIO", "ALTO", "CRITICO"]
    colores = ["#F5A623", "#F16B2E", "#D0202F", "#4A1D6E"]

    filas_html = ""
    for i, (rio, step_actual) in enumerate(zip(rios, progreso_filas)):
        bg = "#ffffff" if i % 2 == 0 else "#f7f8fb"

        segmentos = ""
        for idx, (nombre, color) in enumerate(zip(steps, colores)):
            opacidad = "1" if (idx + 1) <= step_actual else "0.3"
            segmentos += f'<div style="background-color:{color}; opacity:{opacidad};">{nombre}</div>'

        filas_html += f"""
        <div class="step-row" style="background:{bg};">
            <div class="step-river">{rio}</div>
            <div class="step-bar">{segmentos}</div>
        </div>
        """

    with col_der:
        st.markdown(f"""
        <style>
        .step-card {{
            border-radius: 12px;
            border: 1px solid rgba(30,50,120,0.1);
            background: #ffffff;
            box-shadow: 0 1px 6px rgba(30,50,120,0.06);
            overflow: hidden;
            font-family: sans-serif;
            margin-bottom: 20px;
        }}
        .step-card-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px 16px;
            border-bottom: 1px solid rgba(30,50,120,0.08);
            background: #f7f8fb;
        }}
        .step-card-title {{
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 11px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #3a4a6e;
        }}
        .step-row {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 16px;
            border-bottom: 1px solid rgba(30,50,120,0.06);
        }}
        .step-river {{
            width: 92px;
            flex-shrink: 0;
            font-size: 12px;
            font-weight: 600;
            color: #2c3554;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .step-bar {{
            display: flex;
            flex: 1;
            height: 22px;
            border-radius: 11px;
            overflow: hidden;
        }}
        .step-bar div {{
            flex: 1;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 9px;
        }}
        </style>
        <div class="step-card">
            <div class="step-card-header">
                <span class="step-card-title">
                    <span style="width:8px;height:8px;border-radius:50%;background:#2563eb;display:inline-block;"></span>
                    Ríos Desbordados
                </span>
            </div>
            {filas_html}
        </div>
        """, unsafe_allow_html=True)


NIVEL_STYLES = {
    "CRITICO": {"bar": "#E5484D", "num": "#DC2626", "badge_bg": "#FDEEE1", "badge_text": "#C2570C", "dot": "#E5484D"},
    "ALTO":    {"bar": "#E8912B", "num": "#E8912B", "badge_bg": "#FDF1E1", "badge_text": "#B36B0D", "dot": "#E8912B"},
    "MEDIO":   {"bar": "#3B82F6", "num": "#93A3B8", "badge_bg": "#EAF2FE", "badge_text": "#2563EB", "dot": "#3B82F6"},
    "BAJO":    {"bar": "#22A55A", "num": "#94A3B8", "badge_bg": "#E7F8EE", "badge_text": "#15803D", "dot": "#22A55A"},
}

zonas_riesgo_ejemplo = [  # TODO: reemplazar con datos reales desde data_layer
    {"zona": "Guayaquil",     "provincia": "Guayas",        "irc": 96, "personas": 48200, "nivel": "CRITICO", "trend": "up"},
    {"zona": "Babahoyo",      "provincia": "Los Ríos",      "irc": 91, "personas": 31700, "nivel": "CRITICO", "trend": "up"},
    {"zona": "Vinces",        "provincia": "Los Ríos",      "irc": 84, "personas": 18900, "nivel": "CRITICO", "trend": "up"},
    {"zona": "Portoviejo",    "provincia": "Manabí",        "irc": 78, "personas": 19500, "nivel": "ALTO",    "trend": None},
    {"zona": "Machala",       "provincia": "El Oro",        "irc": 73, "personas": 14800, "nivel": "ALTO",    "trend": "up"},
    {"zona": "Milagro",       "provincia": "Guayas",        "irc": 69, "personas": 12300, "nivel": "ALTO",    "trend": None},
    {"zona": "Esmeraldas",    "provincia": "Esmeraldas",    "irc": 61, "personas": 9600,  "nivel": "ALTO",    "trend": "down"},
    {"zona": "Chone",         "provincia": "Manabí",        "irc": 54, "personas": 7400,  "nivel": "MEDIO",   "trend": None},
    {"zona": "Santo Domingo", "provincia": "Santo Domingo", "irc": 47, "personas": 5800,  "nivel": "MEDIO",   "trend": "down"},
    {"zona": "Quevedo",       "provincia": "Los Ríos",      "irc": 41, "personas": 4200,  "nivel": "MEDIO",   "trend": None},
]


def _formatear_personas(n):
    return f"{n:,}".replace(",", ".")


def _flecha_tendencia(trend):
    if trend == "up":
        return '<span style="color:#DC2626; font-size:10px; margin-left:2px;">▲</span>'
    if trend == "down":
        return '<span style="color:#16A34A; font-size:10px; margin-left:2px;">▼</span>'
    return ""


def _render_top_zonas_riesgo():
    zonas = fetch_zonas_riesgo()
    if not zonas:
        zonas = zonas_riesgo_ejemplo

    filas_html = ""
    for i, z in enumerate(zonas):
        rank = i + 1
        style = NIVEL_STYLES.get(z["nivel"], NIVEL_STYLES["MEDIO"])
        bg = "#ffffff" if i % 2 == 0 else "#f7f8fb"
        flecha = _flecha_tendencia(z.get("trend"))

        filas_html += (
            f'<div class="riesgo-row" style="background:{bg};">'
            f'<div class="riesgo-rank" style="color:{style["num"]};">{rank:02d}{flecha}</div>'
            f'<div class="riesgo-zona">{z["zona"]}</div>'
            f'<div class="riesgo-provincia">{z["provincia"]}</div>'
            f'<div class="riesgo-irc-bar">'
            f'<div class="riesgo-bar-track"><div class="riesgo-bar-fill" style="width:{z["irc"]}%; background:{style["bar"]};"></div></div>'
            f'<span class="riesgo-irc-pct" style="color:{style["bar"]};">{z["irc"]}%</span>'
            f'</div>'
            f'<div class="riesgo-personas">{_formatear_personas(z["personas"])}</div>'
            f'<div class="riesgo-nivel"><span class="riesgo-badge" style="background:{style["badge_bg"]}; color:{style["badge_text"]};">'
            f'<span class="riesgo-dot" style="background:{style["dot"]};"></span>{z["nivel"]}</span></div>'
            f'</div>'
        )

    html = """
        <style>
        .riesgo-card {
        border-radius: 12px;
        border: 1px solid rgba(30,50,120,0.1);
        background: #ffffff;
        box-shadow: 0 1px 6px rgba(30,50,120,0.06);
        overflow: hidden;
        font-family: sans-serif;
        margin-bottom: 20px;
        }
        .riesgo-card-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 16px;
        border-bottom: 1px solid rgba(30,50,120,0.08);
        background: #f7f8fb;
        flex-wrap: wrap;
        gap: 8px;
        }
        .riesgo-card-title {
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 11px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #3a4a6e;
        white-space: nowrap;
        }
        .riesgo-card-meta {
        display: flex;
        align-items: center;
        gap: 10px;
        font-size: 11px;
        color: #8a93a8;
        }
        .riesgo-vista-btn {
        display: flex;
        align-items: center;
        gap: 4px;
        padding: 5px 10px;
        border-radius: 8px;
        border: 1px solid rgba(30,50,120,0.12);
        background: #ffffff;
        color: #3a4a6e;
        font-size: 11px;
        font-weight: 600;
        white-space: nowrap;
        }
        .riesgo-col-headers {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 8px 16px;
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: #9aa4ba;
        border-bottom: 1px solid rgba(30,50,120,0.06);
        }
        .riesgo-row {
        display: flex;
        align-items: center;
        gap: 12px;
        padding: 10px 16px;
        border-bottom: 1px solid rgba(30,50,120,0.06);
        }
        .riesgo-rank {
        width: 28px;
        flex-shrink: 0;
        font-size: 12px;
        font-weight: 700;
        white-space: nowrap;
        }
        .riesgo-zona {
        width: 112px;
        flex-shrink: 0;
        font-size: 13px;
        font-weight: 700;
        color: #1e2942;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        }
        .riesgo-provincia {
        width: 110px;
        flex-shrink: 0;
        font-size: 12px;
        font-weight: 500;
        color: #6b8fd6;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        }
        .riesgo-irc-bar {
        flex: 1;
        display: flex;
        align-items: center;
        gap: 8px;
        min-width: 60px;
        }
        .riesgo-bar-track {
        flex: 1;
        height: 5px;
        border-radius: 3px;
        background: rgba(30,50,120,0.08);
        overflow: hidden;
        }
        .riesgo-bar-fill {
        height: 100%;
        border-radius: 3px;
        }
        .riesgo-irc-pct {
        font-size: 12px;
        font-weight: 700;
        width: 32px;
        text-align: right;
        flex-shrink: 0;
        }
        .riesgo-personas {
        width: 68px;
        flex-shrink: 0;
        text-align: right;
        font-size: 12px;
        font-weight: 600;
        color: #5b6478;
        }
        .riesgo-nivel {
        width: 92px;
        flex-shrink: 0;
        display: flex;
        justify-content: flex-end;
        }
        .riesgo-badge {
        display: flex;
        align-items: center;
        gap: 5px;
        padding: 3px 9px;
        border-radius: 6px;
        font-size: 10px;
        font-weight: 700;
        white-space: nowrap;
        }
        .riesgo-dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
        display: inline-block;
        }
        </style>
        <div class="riesgo-card">
        <div class="riesgo-card-header">
        <span class="riesgo-card-title">📈 Top 10 Zonas de Mayor Riesgo — Ecuador</span>
        <div class="riesgo-card-meta">
        <span>Índice de Riesgo Compuesto (IRC)</span>
        <span class="riesgo-vista-btn">📍 Vista por Provincia</span>
        </div>
        </div>
        <div class="riesgo-col-headers">
        <div style="width:28px;">#</div>
        <div style="width:112px;">Zona</div>
        <div style="width:110px;">Provincia</div>
        <div style="flex:1;">Riesgo IRC</div>
        <div style="width:68px; text-align:right;">Personas</div>
        <div style="width:92px; text-align:right;">Nivel</div>
        </div>
        """ + filas_html + "</div>"

    st.markdown(html, unsafe_allow_html=True)

ZONAS_NIVEL_STYLES = {
    "CRITICO": {"badge_bg": "#FDEEE1", "badge_text": "#C2570C", "dot": "#E5484D"},
    "ALTO":    {"badge_bg": "#FDF1E1", "badge_text": "#B36B0D", "dot": "#E8912B"},
    "MEDIO":   {"badge_bg": "#EAF2FE", "badge_text": "#2563EB", "dot": "#3B82F6"},
    "BAJO":    {"badge_bg": "#E7F8EE", "badge_text": "#15803D", "dot": "#22A55A"},
}

zonas_afectadas_ejemplo = [  # TODO: reemplazar con datos reales desde data_layer
    {"provincia": "Guayas",     "zona": "Guayaquil",  "area_km2": 312, "precipitacion_mm": 168.4, "nivel": "CRITICO"},
    {"provincia": "Los Ríos",   "zona": "Babahoyo",   "area_km2": 204, "precipitacion_mm": 142.7, "nivel": "CRITICO"},
    {"provincia": "Manabí",     "zona": "Portoviejo", "area_km2": 178, "precipitacion_mm": 96.3,  "nivel": "ALTO"},
    {"provincia": "El Oro",     "zona": "Machala",    "area_km2": 142, "precipitacion_mm": 88.1,  "nivel": "ALTO"},
    {"provincia": "Esmeraldas", "zona": "Esmeraldas", "area_km2": 98,  "precipitacion_mm": 54.6,  "nivel": "MEDIO"},
]


def _formatear_numero(n):
    return f"{n:,}".replace(",", ".")

def _render_kpi_card():
    zonas = fetch_zonas_afectadas()
    if not zonas:
        zonas = zonas_afectadas_ejemplo

    filas_html = ""
    for z in zonas:
        style = ZONAS_NIVEL_STYLES.get(z["nivel"], ZONAS_NIVEL_STYLES["MEDIO"])
        filas_html += (
            '<div class="zonas-row">'
                '<div class="zonas-left">'
                    f'<span class="zonas-badge" style="background:{style["badge_bg"]}; color:{style["badge_text"]};">'
                        f'<span class="zonas-dot" style="background:{style["dot"]};"></span>{z["nivel"]}'
                    '</span>'
                    '<div class="zonas-info">'
                        f'<div class="zonas-nombre">{z["provincia"]} — {z["zona"]}</div>'
                        f'<div class="zonas-area">{z["area_km2"]} km²</div>'
                    '</div>'
                '</div>'
                '<div class="zonas-right">'
                    f'<div class="zonas-precip-num">{z["precipitacion_mm"]:.1f} mm</div>'
                    '<div class="zonas-precip-label">precipitación</div>'
                '</div>'
                '<div class="zonas-chevron">›</div>'
            '</div>'
        )

    html = f"""
    <style>
    .zonas-card {{
        background:white;
        border-radius:12px;
        border:1px solid rgba(30,50,120,0.1);
        box-shadow:0 1px 6px rgba(30,50,120,0.06);
        overflow:hidden;
        font-family:sans-serif;
        margin-bottom: 20px;
    }}
    .zonas-header {{
        display:flex;
        justify-content:space-between;
        align-items:center;
        padding:14px 18px;
        border-bottom:1px solid rgba(30,50,120,.08);
        background:#f7f8fb;
    }}
    .zonas-header-title {{
        font-size:12px;
        font-weight:700;
        text-transform:uppercase;
        color:#3a4a6e;
    }}
    .zonas-row {{
        display:flex;
        align-items:center;
        gap:14px;
        padding:14px 18px;
        border-bottom:1px solid rgba(30,50,120,.06);
    }}
    .zonas-row:last-child {{
        border-bottom:none;
    }}
    .zonas-left {{
        display:flex;
        align-items:center;
        gap:14px;
        flex:1;
        min-width:0;
    }}
    .zonas-badge {{
        display:flex;
        align-items:center;
        gap:5px;
        padding:3px 9px;
        border-radius:6px;
        font-size:10px;
        font-weight:700;
    }}
    .zonas-dot {{
        width:6px;
        height:6px;
        border-radius:50%;
    }}
    .zonas-info {{
        min-width:0;
    }}
    .zonas-nombre {{
        font-size:14px;
        font-weight:700;
        color:#1e2942;
    }}
    .zonas-area {{
        font-size:12px;
        color:#9aa4ba;
    }}
    .zonas-right {{
        text-align:right;
    }}
    .zonas-precip-num {{
        font-size:14px;
        font-weight:700;
        color:#E8912B;
    }}
    .zonas-precip-label {{
        font-size:11px;
        color:#3B82F6;
    }}
    .zonas-chevron {{
        font-size:18px;
        color:#c3cadb;
    }}
    </style>
    <div class="zonas-card">
        <div class="zonas-header">
            <span class="zonas-header-title">
                ⚠️ Zonas Afectadas Actualmente
            </span>
        </div>
        {filas_html}
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render():

    _inject_theme_css()

    _render_header()

    _render_listas()

    _espaciador()

    m = construir_mapa_manta()
    agregar_observaciones_postgis(m)
    render_mapa(map_obj=m)

    _espaciador()

    _render_top_zonas_riesgo()

    render_seccion_eda()