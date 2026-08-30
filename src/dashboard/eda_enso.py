# src/dashboard/eda_enso.py
import math
import streamlit as st
import pandas as pd
import plotly.graph_objects as go

COLOR_EL_NINO = "#E8912B"
COLOR_LA_NINA = "#3B82F6"
COLOR_LINEA = "#1e2942"
COLOR_TEXTO_MUTED = "#9aa4ba"
FONT_FAMILY = "sans-serif"


def clasificar_fase(oni: float) -> str:
    """Clasifica la fase ENSO según el valor del índice ONI."""
    if oni >= 0.5:
        return "El Niño"
    elif oni <= -0.5:
        return "La Niña"
    return "Neutral"


def _generar_oni_dummy() -> pd.DataFrame:
    seas_orden = [
        "DJF", "JFM", "FMA", "MAM", "AMJ", "MJJ",
        "JJA", "JAS", "ASO", "SON", "OND", "NDJ"
    ]
    seas_a_mes = {s: i + 1 for i, s in enumerate(seas_orden)}
    filas = []
    t = 0
    for anio in range(2015, 2025):
        for seas in seas_orden:
            oni = round(1.6 * math.sin(2 * math.pi * t / 42), 2)
            filas.append({
                "fecha": pd.Timestamp(
                    year=anio,
                    month=seas_a_mes[seas],
                    day=1
                ),
                "anio": anio,
                "trimestre": seas,
                "oni": oni
            })
            t += 1
    return pd.DataFrame(filas)


@st.cache_data
def cargar_enso() -> tuple[pd.DataFrame, bool]:
    """Carga temporalmente datos sintéticos de ENSO."""
    df = _generar_oni_dummy()
    df["fase"] = df["oni"].apply(clasificar_fase)
    return df, True


def grafico_oni(
    df: pd.DataFrame,
    desde: str = "1990-01-01"
) -> go.Figure:
    d = df[df["fecha"] >= pd.to_datetime(desde)]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=d["fecha"],
            y=d["oni"],
            mode="lines",
            line=dict(
                color=COLOR_LINEA,
                width=1.5
            ),
            name="ONI",
            hovertemplate="%{x|%b %Y}<br>ONI: %{y:.2f}<extra></extra>",
        )
    )
    fig.add_hrect(
        y0=0.5,
        y1=d["oni"].max() + 0.3,
        fillcolor=COLOR_EL_NINO,
        opacity=0.08,
        line_width=0
    )
    fig.add_hrect(
        y0=d["oni"].min() - 0.3,
        y1=-0.5,
        fillcolor=COLOR_LA_NINA,
        opacity=0.08,
        line_width=0
    )
    fig.add_hline(
        y=0.5,
        line_dash="dash",
        line_color=COLOR_EL_NINO,
        line_width=1
    )
    fig.add_hline(
        y=-0.5,
        line_dash="dash",
        line_color=COLOR_LA_NINA,
        line_width=1
    )
    fig.update_layout(
        title=dict(
            text="Índice ONI (ENSO) — Datos de prueba",
            font=dict(
                size=13,
                color="#3a4a6e",
                family=FONT_FAMILY
            )
        ),
        font=dict(
            family=FONT_FAMILY,
            color=COLOR_TEXTO_MUTED,
            size=11
        ),
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        margin=dict(l=40, r=20, t=40, b=30),
        height=320,
        showlegend=False,
        yaxis=dict(
            title="ONI (°C)",
            gridcolor="rgba(30,50,120,0.06)"
        ),
        xaxis=dict(
            gridcolor="rgba(30,50,120,0.06)"
        ),
    )
    return fig


def render_seccion_eda():
    with st.container(border=True, key="eda-enso-wrap"):
        df, es_dummy = cargar_enso()
        fig = grafico_oni(df)
        st.plotly_chart(
            fig,
            use_container_width=True,
            config={"displaylogo": False}
        )
        if es_dummy:
            st.caption(
                "⚠️ Datos de prueba (sintéticos) — "
                "pendiente integración con el pipeline real de NOAA"
            )