import streamlit as st
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pages import login as login_page
from pages import dashboard as dashboard_page

st.set_page_config(
    page_title="Enso — SMART",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================
# PÁGINAS
# =========================

dashboard = st.Page(
    dashboard_page.render,
    title="Dashboard",
    default=True
)

climate = st.Page(
    "indicadores_climaticos.py",
    title="Indicadores climáticos"
)


# =========================
# ESTILOS
# =========================

st.markdown(
    """
    <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header[data-testid="stHeader"] {
            height: 0;
            visibility: hidden;
        }

        .stApp {
            background: #f0f2f7;
        }

        div[data-testid="stLayoutWrapper"]
        div[data-testid="stVerticalBlock"] {
            background-color: #ffffff;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================
# AUTENTICACIÓN
# =========================

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False


if not st.session_state["authenticated"]:

    pg = st.navigation(
        [
            st.Page(
                login_page.render,
                title="Login"
            )
        ],
        position="hidden"
    )

else:

    pg = st.navigation(
        [
            dashboard,
            climate,
        ],
        position="hidden"
    )


pg.run()