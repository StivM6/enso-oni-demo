

import streamlit as st

_RED = "#c8192e"
_RED_DARK = "#8f1220"
_PINK_BG = "#f4e7e6"
_MUTED = "#6b7280"


def _inject_css():
    st.markdown(
        f"""
        <style>
            /* Header: reusa el mismo look de "contenedor blanco con borde"
               que ya usan las tarjetas del resto del proyecto (no es un div
               custom aparte, es un st.container(border=True) real). */
            .ese-topbar-brand {{
                display:flex; align-items:center; gap:8px;
                font-weight:700; font-size:15px; color:#111827;
            }}
            .ese-topbar-back {{
                width:34px; height:34px; border:1px solid #e5e7eb; border-radius:8px;
                display:flex; align-items:center; justify-content:center;
                color:#111827; font-size:16px; margin-left:auto;
            }}

            .ese-badge {{
                display:inline-flex; align-items:center; gap:6px;
                background: {_PINK_BG}; color: {_RED};
                font-size:11px; font-weight:700; letter-spacing:.04em;
                padding:5px 12px; border-radius:999px; margin-bottom:16px;
            }}
            .ese-title {{ font-size:26px; font-weight:700; color:#111827; margin:0 0 6px 0; }}
            .ese-subtitle {{ font-size:13px; color:{_MUTED}; margin:0 0 20px 0; line-height:1.45; }}

            .ese-label {{
                font-size:11px; font-weight:700; letter-spacing:.06em;
                color:#374151; text-transform:uppercase;
            }}
            .ese-link {{ font-size:12px; color:{_RED}; font-weight:600; text-decoration:none; }}

            div[data-testid="stTextInput"] label p {{
                font-size:11px !important; font-weight:700 !important;
                letter-spacing:.06em !important; color:#374151 !important;
                text-transform:uppercase !important;
            }}
            div[data-testid="stTextInput"] input {{
                background:#f7f8fb; border:1px solid #e5e7eb; border-radius:10px;
                padding:10px 14px;
            }}

            div[data-testid="stButton"] button,
            button[kind="primary"],
            button[data-testid="stBaseButton-primary"] {{
                background: linear-gradient(180deg, {_RED} 0%, {_RED_DARK} 100%) !important;
                color: #ffffff !important;
                border:none !important; border-radius:10px !important;
                font-weight:700 !important; padding:10px 0 !important;
            }}

            .ese-divider {{ text-align:center; color:#d1d5db; margin: 18px 0 14px 0; font-size:11px; }}
            .ese-footer-text {{ text-align:center; font-size:13px; color:#4b5563; margin-top:14px; }}
            .ese-footer-text b {{ color:{_RED}; }}
            .ese-watermark {{
                text-align:center; font-size:11px; letter-spacing:.15em;
                color:#c7cbd4; margin-top:26px;
            }}

            /* Centra SOLO la tarjeta de login por ancho máximo + margin:auto,
               en vez de columnas vacías -> evita "cajas" blancas fantasma
               a los costados (los st.columns heredan el fondo blanco global
               del proyecto aunque estén vacíos). */
            div.st-key-login_card {{
                max-width: 460px;
                margin-left: auto;
                margin-right: auto;
            }}
            div.st-key-login_topbar {{
                margin-bottom: 20px;
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def _render_topbar():

    with st.container(border=True, key="login_topbar"):
        pass


def render():
    _inject_css()
    _render_topbar()
    st.write("")
    with st.container(border=True, key="login_card"):
        st.markdown(
            f"""
            <div class="ese-badge">⭐ ACCESO PREMIUM</div>
            <div class="ese-title">Iniciar sesión</div>
            <div class="ese-subtitle">
                Ingresa tus credenciales para acceder a la plataforma completa.
            </div>
            """,
            unsafe_allow_html=True,
        )

        email = st.text_input(
            "CORREO ELECTRÓNICO", placeholder="usuario@ejemplo.com"
        )

        label_col, link_col = st.columns([2, 1.4])
        with label_col:
            st.markdown("<div class='ese-label'>Contraseña</div>", unsafe_allow_html=True)
        with link_col:
            st.markdown(
                "<div style='text-align:right'>"
                "<a class='ese-link' href='#'>¿Olvidaste tu contraseña?</a></div>",
                unsafe_allow_html=True,
            )

        password = st.text_input(
            "Contraseña",
            placeholder="••••••••••••",
            type="password",
            label_visibility="collapsed",
            key="login_password",
        )

        st.write("")
        submitted = st.button(
            "🛡️  Iniciar sesión", type="primary", use_container_width=True
        )

        st.markdown("<div class='ese-divider'>●</div>", unsafe_allow_html=True)
        st.markdown(
            "<div class='ese-footer-text'>"
            "¿No tienes cuenta? <b>Solicitar acceso institucional</b></div>",
            unsafe_allow_html=True,
        )
        if submitted:
            if email and password:
                st.session_state["authenticated"] = True
                st.session_state["user"] = email
                st.rerun()
            else:
                st.error("Ingresá usuario y contraseña.")

    st.markdown("<div class='ese-watermark'>INAMHI</div>", unsafe_allow_html=True)
