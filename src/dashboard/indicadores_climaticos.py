"""Página «Indicadores climáticos» del dashboard Enso — SMART.

Vista previa, con datos de ejemplo, de los indicadores que se conectan en
Sprint 5-6: precipitación acumulada (CHIRPS) y estado ENSO (ONI y Niño 1+2).

Se integra desde dashboard.py como una vista más:

    from indicadores_climaticos import render as render_indicadores
    ...
    if vista == "Indicadores climáticos":
        render_indicadores()
        return

Para conectar datos reales basta con reemplazar _serie_ejemplo(), _ONI_EJEMPLO
y _NINO12_EJEMPLO; todo lo que dibuja la página se queda igual.
"""

import datetime
import itertools
import math
from decimal import ROUND_HALF_UP, Decimal

import streamlit as st


# ─── Datos de ejemplo ─────────────────────────────────────────────────────
# TODO Sprint 5-6: reemplazar por CHIRPS (PostGIS) y ONI / Niño 1+2 (NOAA CPC).

FECHA_CORTE_EJEMPLO = datetime.date(2026, 9, 26)

# Forma de la lluvia diaria (mm) en 30 días; cada provincia la escala a su total.
_PATRON_DIARIO = [
    2, 0, 5, 11, 3, 0, 0, 8, 14, 22, 6, 1, 0, 0, 4,
    9, 17, 3, 0, 0, 2, 6, 12, 19, 28, 9, 4, 0, 13, 20,
]

# provincia: (lluvia total de los 30 días en mm, normal diaria en mm/día)
_PROVINCIAS_EJEMPLO = {
    "Esmeraldas": (352, 12.2),
    "Manabí": (169, 4.3),
    "Santa Elena": (121, 2.5),
    "Guayas": (218, 5.8),
    "Los Ríos": (265, 8.4),
    "El Oro": (96, 4.7),
}

REGION = "Región Costa (general)"
TERRITORIOS = [REGION, *_PROVINCIAS_EJEMPLO]

# (trimestre móvil, ONI en °C); el último es el más reciente.
_ONI_EJEMPLO = [
    ("ASO", -0.2), ("SON", 0.0), ("OND", 0.2), ("NDE", 0.3),
    ("DEF", 0.5), ("EFM", 0.6), ("FMA", 0.7), ("MAM", 0.8),
    ("AMJ", 0.9), ("MJJ", 1.0), ("JJA", 1.1), ("JAS", 1.1),
]
_NINO12_EJEMPLO = 1.6  # anomalía semanal de TSM en la región Niño 1+2 (°C)


def _serie_ejemplo(territorio):
    """Devuelve (fechas, lluvia_diaria, normal_diaria) de los últimos 30 días."""
    n = len(_PATRON_DIARIO)
    fechas = [FECHA_CORTE_EJEMPLO - datetime.timedelta(days=n - 1 - i) for i in range(n)]
    total_patron = sum(_PATRON_DIARIO)

    def serie(total, normal_diaria):
        factor = total / total_patron
        return [v * factor for v in _PATRON_DIARIO], [normal_diaria] * n

    if territorio in _PROVINCIAS_EJEMPLO:
        lluvia, normal = serie(*_PROVINCIAS_EJEMPLO[territorio])
    else:
        # Región = promedio simple día a día. Con datos reales conviene
        # ponderar por el área de cada provincia (medida en EPSG:32717).
        series = [serie(*datos) for datos in _PROVINCIAS_EJEMPLO.values()]
        lluvia = [sum(s[0][i] for s in series) / len(series) for i in range(n)]
        normal = [sum(s[1][i] for s in series) / len(series) for i in range(n)]
    return fechas, lluvia, normal


# ─── Escalas y umbrales ───────────────────────────────────────────────────

# Anomalía de lluvia (% respecto a la normal). Escala divergente:
# seco (ámbar) ↔ normal (gris) ↔ húmedo (azul); los extremos son los más oscuros.
CATEGORIAS = [  # (nombre, color del medidor, fondo del badge, texto del badge, rango)
    ("Muy seco", "#E8912B", "#FDF1E1", "#B36B0D", "menos de −50 % de la normal"),
    ("Seco", "#F5C77A", "#FDF1E1", "#B36B0D", "−50 a −25 % de la normal"),
    ("Normal", "#CBD5E1", "#EEF1F5", "#475569", "dentro de ±25 % de la normal"),
    ("Húmedo", "#93C5FD", "#EAF2FE", "#2563EB", "+25 a +100 % sobre la normal"),
    ("Muy húmedo", "#2563EB", "#EAF2FE", "#2563EB", "más de +100 % sobre la normal"),
]


def _categoria(anomalia_pct):
    """Posición en CATEGORIAS según la anomalía en %."""
    if anomalia_pct < -50:
        return 0
    if anomalia_pct < -25:
        return 1
    if anomalia_pct <= 25:
        return 2
    if anomalia_pct <= 100:
        return 3
    return 4


# Fases ENSO según el ONI (umbrales ±0,5 / ±1,0 / ±1,5 °C).
FASES_ENSO = [  # (etiqueta bajo la barra, nombre, color)
    ("Niña<br>fuerte", "La Niña fuerte", "#2563EB"),
    ("Niña<br>mod.", "La Niña moderada", "#3B82F6"),
    ("Niña<br>débil", "La Niña débil", "#93C5FD"),
    ("Neutral", "Neutral", "#CBD5E1"),
    ("Niño<br>débil", "El Niño débil", "#F5C77A"),
    ("Niño<br>mod.", "El Niño moderado", "#E8912B"),
    ("Niño<br>fuerte", "El Niño fuerte", "#E5484D"),
]


def _fase_enso(oni):
    """Posición en FASES_ENSO según el valor del ONI.

    Ojo: oficialmente un evento necesita 5 trimestres seguidos sobre el umbral;
    aquí solo se clasifica el valor más reciente.
    """
    for limite, fase in ((-1.5, 0), (-1.0, 1), (-0.5, 2)):
        if oni <= limite:
            return fase
    for limite, fase in ((0.5, 3), (1.0, 4), (1.5, 5)):
        if oni < limite:
            return fase
    return 6


def _colores_calido_frio(valor):
    """(fondo, texto, punto) del badge según el signo de la anomalía de temperatura.

    El umbral de ±0,5 °C es una simplificación para la vista previa; para
    Niño 1+2 conviene confirmar con el equipo qué criterio usar (p. ej. el ICEN).
    """
    if valor >= 0.5:
        return "#FDF1E1", "#B36B0D", "#E8912B"
    if valor <= -0.5:
        return "#EAF2FE", "#2563EB", "#3B82F6"
    return "#EEF1F5", "#475569", "#94A3B8"


# ─── Formato de números y fechas ──────────────────────────────────────────

MENOS = "−"  # signo menos tipográfico: se lee mejor que el guion "-"
_MESES = ("ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic")


def _redondear(valor, decimales):
    """Redondeo «escolar» (el 5 sube).

    round() y format() de Python redondean al par y arrastran el error de punto
    flotante: una normal de 189.5 mm llega como 189.49999999999997 y se mostraría
    como 189. Por eso se limpia el ruido y se redondea con Decimal.
    """
    paso = Decimal(1).scaleb(-decimales)
    return Decimal(repr(round(valor, 9))).quantize(paso, rounding=ROUND_HALF_UP)


def _num(valor, decimales=1):
    """Número con coma decimal: 12.5 -> "12,5"."""
    r = _redondear(valor, decimales)
    texto = f"{abs(r):.{decimales}f}".replace(".", ",")
    return MENOS + texto if r < 0 else texto


def _con_signo(valor, decimales=1):
    """Número con signo siempre visible: +1,1 / −0,2 / 0,0."""
    r = _redondear(valor, decimales)
    texto = f"{abs(r):.{decimales}f}".replace(".", ",")
    if r == 0:
        return texto
    return ("+" if r > 0 else MENOS) + texto


def _fecha_corta(fecha):
    """26 sep. Se evita strftime("%b") porque depende del idioma del servidor."""
    return f"{fecha.day} {_MESES[fecha.month - 1]}"


# ─── Estilos ──────────────────────────────────────────────────────────────
# La página trae su propio CSS para no tocar _inject_theme_css() de dashboard.py.
# Los valores de .clima-card son los mismos de las tarjetas existentes.

_CSS = """
<style>
/* Contenedores con key: Streamlit les agrega la clase st-key-<key>. */
/* app.py pinta de blanco todos los bloques verticales; en esta página eso deja
   franjas blancas bajo las tarjetas más cortas. Aquí el fondo queda gris y
   solo las tarjetas son blancas, como en el resto del dashboard. */
.st-key-clima-pagina,
.st-key-clima-pagina div[data-testid="stLayoutWrapper"] div[data-testid="stVerticalBlock"] {
    background-color: transparent !important;
}
.st-key-clima-pagina div[data-testid="stLayoutWrapper"] div.st-key-clima-titulo,
.st-key-clima-pagina div.st-key-clima-titulo {
    background-color: #FFFFFF !important;
    border-radius: 12px;
    margin-bottom: 20px;
}
.clima-titulo-pagina {
    padding-bottom: 6px;
    display: flex;
    align-items: center;
    gap: 8px;
    font-family: sans-serif;
    font-size: 12px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #3A4A6E;
}
.st-key-clima-pagina div[data-testid="stLayoutWrapper"] div.st-key-clima-card-acum,
.st-key-clima-pagina div.st-key-clima-card-acum {
    background: #FFFFFF !important;
    border: 1px solid rgba(30,50,120,0.1);
    border-radius: 12px;
    box-shadow: 0 1px 6px rgba(30,50,120,0.06);
    padding: 0 16px 12px 16px;
    overflow: hidden;
    gap: 0.5rem;
    margin-bottom: 20px;
}

.clima-card {
    background: #FFFFFF;
    border: 1px solid rgba(30,50,120,0.1);
    border-radius: 12px;
    box-shadow: 0 1px 6px rgba(30,50,120,0.06);
    overflow: hidden;
    font-family: sans-serif;
    margin-bottom: 20px;
}
.clima-kpi { height: 192px; }
.clima-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;
    padding: 10px 16px;
    border-bottom: 1px solid rgba(30,50,120,0.08);
    background: #F7F8FB;
    font-family: sans-serif;
}
/* Encabezado dentro del contenedor con padding: se estira hasta los bordes. */
.clima-header-flush { margin: 0 -16px; }
.clima-titulo-card {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #3A4A6E;
}
.clima-punto { width: 8px; height: 8px; border-radius: 50%; flex-shrink: 0; }
.clima-meta { font-size: 11px; color: #5B6478; }
.clima-body { padding: 14px 16px 16px; display: flex; flex-direction: column; gap: 10px; }
.clima-fila-valor { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
.clima-valor { font-size: 26px; font-weight: 800; line-height: 1; color: #1E2942; }
.clima-unidad { font-size: 13px; color: #5B6478; margin-left: 5px; }
.clima-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 9px;
    border-radius: 6px;
    font-size: 11px;
    font-weight: 700;
    white-space: nowrap;
}
.clima-badge-punto { width: 6px; height: 6px; border-radius: 50%; }
.clima-texto { font-size: 12px; color: #5B6478; }
.clima-categoria { font-size: 12px; color: #3A4A6E; }
.clima-medidor { display: flex; align-items: center; gap: 2px; height: 16px; }
.clima-medidor div { flex: 1; border-radius: 3px; }
.clima-etiquetas {
    display: grid;
    grid-template-columns: repeat(7, minmax(0, 1fr));
    gap: 2px;
    font-size: 10px;
    line-height: 1.2;
    text-align: center;
    color: #5B6478;
}
.clima-subtitulo {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #3A4A6E;
}
.clima-separador { height: 1px; background: rgba(30,50,120,0.08); }
.clima-leyenda {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 12px;
    flex-wrap: wrap;
    margin-bottom: 8px;
    font-family: sans-serif;
}
.clima-leyenda-items { display: flex; gap: 14px; flex-wrap: wrap; font-size: 11px; color: #3A4A6E; }
.clima-leyenda-items span { display: inline-flex; align-items: center; gap: 6px; }

/* Tabla: selectores más específicos para ganarle al estilo de tablas de Streamlit. */
.clima-tabla-wrap { max-height: 300px; overflow-y: auto; font-family: sans-serif; }
.clima-tabla-wrap table.clima-tabla {
    width: 100%;
    margin: 0;
    border: none;
    border-collapse: collapse;
    font-size: 12px;
    font-variant-numeric: tabular-nums;
    color: #1E2942;
}
.clima-tabla-wrap table.clima-tabla th,
.clima-tabla-wrap table.clima-tabla td { border: none; padding: 5px 12px; text-align: right; }
.clima-tabla-wrap table.clima-tabla th:first-child,
.clima-tabla-wrap table.clima-tabla td:first-child { text-align: left; padding-left: 0; }
.clima-tabla-wrap table.clima-tabla thead th {
    position: sticky;
    top: 0;
    background: #FFFFFF;
    font-size: 10px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #5B6478;
    border-bottom: 1px solid rgba(30,50,120,0.12);
}
.clima-tabla-wrap table.clima-tabla tbody tr:nth-child(even) { background: #F7F8FB; }
</style>
"""


# ─── Piezas HTML ──────────────────────────────────────────────────────────
# Todo el HTML se arma en una sola línea: si st.markdown ve una línea en blanco
# o una sangría de 4 espacios, deja de tratarlo como HTML y lo muestra como texto.

def _encabezado(titulo, color_punto, derecha="", extra=""):
    """Franja gris del encabezado de tarjeta, igual a las de dashboard.py."""
    return (
        f'<div class="clima-header {extra}">'
        f'<span class="clima-titulo-card">'
        f'<span class="clima-punto" style="background:{color_punto};"></span>{titulo}</span>'
        f"{derecha}</div>"
    )


def _medidor(activo, colores, alto_activo=14):
    """Barra segmentada. El segmento activo es más alto y opaco: el estado se lee
    por la altura además del color, así no depende solo de distinguir tonos."""
    segmentos = "".join(
        f'<div style="background:{color};'
        f'height:{alto_activo if i == activo else 8}px;'
        f'opacity:{1 if i == activo else 0.35};"></div>'
        for i, color in enumerate(colores)
    )
    return f'<div class="clima-medidor" aria-hidden="true">{segmentos}</div>'


def _tarjeta_kpi(titulo, color_punto, valor, unidad, badge, cuerpo):
    return (
        '<div class="clima-card clima-kpi">'
        f"{_encabezado(titulo, color_punto)}"
        '<div class="clima-body">'
        '<div class="clima-fila-valor">'
        f'<div><span class="clima-valor">{valor}</span><span class="clima-unidad">{unidad}</span></div>'
        f"{badge}</div>"
        f"{cuerpo}</div></div>"
    )


def _kpi_acumulado(lluvia, normal, dias):
    """Tarjeta de lluvia acumulada en los últimos `dias` frente a su normal."""
    observado = sum(lluvia[-dias:])
    referencia = sum(normal[-dias:])
    anomalia = (observado / referencia - 1) * 100 if referencia > 0 else 0.0
    cat = _categoria(anomalia)
    nombre, _, fondo, texto, rango = CATEGORIAS[cat]

    flecha = "▲ " if anomalia >= 0.5 else ("▼ " if anomalia <= -0.5 else "")
    badge = (
        f'<span class="clima-badge" style="background:{fondo};color:{texto};">'
        f"{flecha}{_con_signo(anomalia, 0)} % vs. normal</span>"
    )
    cuerpo = (
        f'<div class="clima-texto">Normal del periodo: {_num(referencia, 0)} mm</div>'
        f"{_medidor(cat, [c[1] for c in CATEGORIAS])}"
        f'<div class="clima-categoria"><strong>{nombre}</strong> · {rango}</div>'
    )
    return _tarjeta_kpi(
        f"Precipitación acumulada · {dias} d", "#2563EB", _num(observado, 0), "mm", badge, cuerpo
    )


def _kpi_oni(oni):
    trimestre, valor = oni[-1]
    fase = _fase_enso(valor)
    fondo, texto, punto = _colores_calido_frio(valor)
    badge = (
        f'<span class="clima-badge" style="background:{fondo};color:{texto};">'
        f'<span class="clima-badge-punto" style="background:{punto};"></span>'
        f"{FASES_ENSO[fase][1].upper()}</span>"
    )
    cuerpo = (
        f'<div class="clima-texto">Trimestre móvil {trimestre} {FECHA_CORTE_EJEMPLO.year} · NOAA CPC</div>'
        '<div class="clima-texto">Umbral El Niño: ONI ≥ +0,5 °C</div>'
    )
    return _tarjeta_kpi("Índice ONI (Niño 3.4)", "#E8912B", _con_signo(valor), "°C", badge, cuerpo)


def _kpi_nino12(anomalia):
    fondo, texto, punto = _colores_calido_frio(anomalia)
    estado = "CÁLIDO" if anomalia >= 0.5 else ("FRÍO" if anomalia <= -0.5 else "NEUTRAL")
    badge = (
        f'<span class="clima-badge" style="background:{fondo};color:{texto};">'
        f'<span class="clima-badge-punto" style="background:{punto};"></span>{estado}</span>'
    )
    cuerpo = (
        '<div class="clima-texto">Promedio semanal · región Niño 1+2</div>'
        '<div class="clima-texto">Es la región más cercana a la costa de Ecuador</div>'
    )
    return _tarjeta_kpi("Anomalía TSM · Niño 1+2", "#E8912B", _con_signo(anomalia), "°C", badge, cuerpo)


def _leyenda(ventana, n):
    dias = "1 día" if ventana == 1 else f"{ventana} días"
    return (
        '<div class="clima-leyenda">'
        f'<span class="clima-texto">Últimos {n} días · CHIRPS diario · '
        f"la franja marca la ventana de {dias}</span>"
        '<span class="clima-leyenda-items">'
        '<span><svg width="20" height="8" aria-hidden="true">'
        '<line x1="0" y1="4" x2="20" y2="4" stroke="#2563EB" stroke-width="2"></line></svg>'
        "Acumulado observado</span>"
        '<span><svg width="20" height="8" aria-hidden="true">'
        '<line x1="0" y1="4" x2="20" y2="4" stroke="#475569" stroke-width="2" stroke-dasharray="6 4"></line>'
        "</svg>Normal (climatología)</span>"
        '<span><svg width="10" height="10" aria-hidden="true">'
        '<rect width="10" height="10" rx="2" fill="#3B82F6"></rect></svg>Lluvia diaria</span>'
        '<span><svg width="14" height="10" aria-hidden="true">'
        '<rect x="0.5" y="0.5" width="13" height="9" fill="#EFF4FC" stroke="#C7D7F2"></rect></svg>'
        "Ventana</span>"
        "</span></div>"
    )


def _tabla_diaria(fechas, lluvia, normal):
    """Los mismos datos del gráfico en tabla, del día más reciente al más antiguo."""
    acum = list(itertools.accumulate(lluvia))
    acum_normal = list(itertools.accumulate(normal))
    filas = "".join(
        f"<tr><td>{_fecha_corta(f)}</td><td>{_num(v)}</td><td>{_num(a)}</td>"
        f"<td>{_num(an)}</td><td>{_con_signo(a - an)}</td></tr>"
        for f, v, a, an in reversed(list(zip(fechas, lluvia, acum, acum_normal)))
    )
    return (
        '<div class="clima-tabla-wrap"><table class="clima-tabla">'
        "<thead><tr><th>Fecha</th><th>Lluvia (mm)</th><th>Acumulado (mm)</th>"
        "<th>Normal (mm)</th><th>Diferencia (mm)</th></tr></thead>"
        f"<tbody>{filas}</tbody></table></div>"
    )


# ─── Gráficos SVG ─────────────────────────────────────────────────────────
# SVG hecho a mano (igual que el mockup) en vez de una librería de gráficos:
# queda idéntico a las tarjetas HTML y no agrega dependencias. El hover sale
# de los <title> de cada día, que el navegador muestra como tooltip.

def _paso_eje(tope):
    """Paso «redondo» para que el eje tenga entre 2 y 4 líneas de guía."""
    for paso in (5, 10, 20, 25, 50, 100, 200, 250, 500, 1000):
        if tope / paso <= 4:
            return paso
    return 1000


def _svg_acumulado(fechas, lluvia, normal, ventana):
    """Dos paneles que comparten el eje de fechas: arriba el acumulado observado
    contra la normal, abajo la lluvia de cada día.

    Se usan dos paneles con escala propia en lugar de un doble eje Y: con doble
    eje la alineación de las escalas es arbitraria y sugiere relaciones que no existen.
    """
    n = len(lluvia)
    acum = list(itertools.accumulate(lluvia))
    acum_normal = list(itertools.accumulate(normal))

    ancho = 776                      # área de datos, en unidades del viewBox
    y0, alto_acum = 20, 150          # panel superior
    y_barras, alto_barras = 196, 60  # panel inferior
    base_acum = y0 + alto_acum
    base_barras = y_barras + alto_barras
    col = ancho / n                  # ancho que le toca a cada día

    def x(i):
        return i * col + col / 2

    tope = max(acum[-1], acum_normal[-1]) * 1.2  # 20 % de aire para la etiqueta final
    paso = _paso_eje(tope)

    def y_acum(v):
        return base_acum - v / tope * alto_acum

    tope_barras = max(10, math.ceil(max(lluvia) / 10) * 10)

    partes = [
        # Franja de la ventana: va primero para quedar detrás de todo.
        f'<rect x="{ancho - ventana * col:.1f}" y="{y0}" width="{ventana * col:.1f}" '
        f'height="{alto_acum}" fill="#EFF4FC"></rect>',
        '<text x="0" y="11" font-size="11" font-weight="600" fill="#3A4A6E">Acumulado (mm)</text>',
    ]
    for v in range(0, int(tope) + 1, paso):
        yy = y_acum(v)
        guia = "#CBD5E1" if v == 0 else "#E8ECF2"
        partes.append(f'<line x1="0" y1="{yy:.1f}" x2="{ancho}" y2="{yy:.1f}" stroke="{guia}"></line>')
        partes.append(
            f'<text x="-8" y="{yy + 4:.1f}" text-anchor="end" font-size="11" fill="#5B6478">{v}</text>'
        )

    puntos_obs = " ".join(f"{x(i):.1f},{y_acum(a):.1f}" for i, a in enumerate(acum))
    puntos_normal = " ".join(f"{x(i):.1f},{y_acum(a):.1f}" for i, a in enumerate(acum_normal))
    partes += [
        f'<polygon points="{x(0):.1f},{base_acum} {puntos_obs} {x(n - 1):.1f},{base_acum}" '
        'fill="#2563EB" fill-opacity="0.1"></polygon>',
        f'<polyline points="{puntos_normal}" fill="none" stroke="#475569" stroke-width="2" '
        'stroke-dasharray="6 4" stroke-linecap="round"></polyline>',
        f'<polyline points="{puntos_obs}" fill="none" stroke="#2563EB" stroke-width="2" '
        'stroke-linejoin="round" stroke-linecap="round"></polyline>',
    ]

    # Etiqueta del valor final. Las dos curvas son acumuladas (solo suben), así
    # que arriba a la izquierda del final nunca hay línea; debajo sí puede haber.
    x_fin, y_fin = x(n - 1), y_acum(acum[-1])
    y_normal_fin = y_acum(acum_normal[-1])
    if acum[-1] >= acum_normal[-1]:
        y_texto = y_fin - 12                        # la normal queda abajo: va encima
    elif y_fin - y_normal_fin >= 22:
        y_texto = (y_fin + y_normal_fin) / 2 + 4    # hay espacio entre las dos líneas
    else:
        y_texto = y_normal_fin - 12                 # líneas muy juntas: encima de ambas
    partes += [
        f'<circle cx="{x_fin:.1f}" cy="{y_fin:.1f}" r="4" fill="#2563EB" stroke="#FFFFFF" stroke-width="2"></circle>',
        f'<text x="{x_fin - 10:.1f}" y="{y_texto:.1f}" text-anchor="end" font-size="13" '
        f'font-weight="700" fill="#1E2942">{_num(acum[-1], 0)} mm</text>',
        f'<text x="{ancho - 6}" y="{base_acum - 6}" text-anchor="end" font-size="11" '
        f'font-weight="600" fill="#3A4A6E">Ventana {ventana} d</text>',
    ]

    # Panel inferior: lluvia diaria
    partes += [
        f'<text x="0" y="{y_barras - 6}" font-size="11" font-weight="600" fill="#3A4A6E">Lluvia diaria (mm)</text>',
        f'<line x1="0" y1="{y_barras}" x2="{ancho}" y2="{y_barras}" stroke="#E8ECF2"></line>',
        f'<text x="-8" y="{y_barras + 4}" text-anchor="end" font-size="11" fill="#5B6478">{tope_barras}</text>',
    ]
    barra = min(14, col * 0.55)
    for i, v in enumerate(lluvia):
        alto = v / tope_barras * alto_barras
        if alto < 0.5:
            continue
        izq, arriba = x(i) - barra / 2, base_barras - alto
        r = min(4, alto, barra / 2)  # extremo redondeado, base recta
        partes.append(
            f'<path d="M{izq:.1f} {base_barras}V{arriba + r:.1f}'
            f'Q{izq:.1f} {arriba:.1f} {izq + r:.1f} {arriba:.1f}'
            f'H{izq + barra - r:.1f}Q{izq + barra:.1f} {arriba:.1f} {izq + barra:.1f} {arriba + r:.1f}'
            f'V{base_barras}Z" fill="#3B82F6"></path>'
        )
    partes += [
        f'<line x1="0" y1="{base_barras}" x2="{ancho}" y2="{base_barras}" stroke="#CBD5E1"></line>',
        f'<text x="-8" y="{base_barras + 4}" text-anchor="end" font-size="11" fill="#5B6478">0</text>',
    ]

    # Fechas: una por semana más el último día (se salta una que quede pegada).
    for i in [*range(0, n - 4, 7), n - 1]:
        partes.append(
            f'<text x="{x(i):.1f}" y="{base_barras + 20}" text-anchor="middle" '
            f'font-size="11" fill="#5B6478">{_fecha_corta(fechas[i])}</text>'
        )

    # Zonas invisibles de hover: una columna por día, con su tooltip.
    for i in range(n):
        partes.append(
            f'<rect x="{i * col:.1f}" y="{y0}" width="{col:.1f}" height="{base_barras - y0}" fill="transparent">'
            f"<title>{_fecha_corta(fechas[i])} · lluvia {_num(lluvia[i])} mm · "
            f"acumulado {_num(acum[i])} mm · normal {_num(acum_normal[i])} mm</title></rect>"
        )

    descripcion = (
        f"Últimos {n} días: acumulado de {_num(acum[-1], 0)} mm frente a "
        f"{_num(acum_normal[-1], 0)} mm normales"
    )
    return (
        f'<svg viewBox="0 0 832 290" width="100%" role="img" aria-label="{descripcion}" '
        'style="display:block;font-family:sans-serif;">'
        f'<g transform="translate(44,0)">{"".join(partes)}</g></svg>'
    )


def _svg_oni(oni):
    """Serie del ONI con la franja neutral (±0,5 °C) sombreada."""
    ancho, alto = 344, 116
    limite = max(1.5, math.ceil(max(abs(v) for _, v in oni) * 2) / 2)
    paso = ancho / (len(oni) - 1)

    def y(v):
        return alto / 2 - v / limite * (alto / 2)

    ultimo = oni[-1][1]
    color = "#E8912B" if ultimo >= 0.5 else ("#2563EB" if ultimo <= -0.5 else "#475569")

    partes = [
        f'<rect x="0" y="{y(0.5):.1f}" width="{ancho}" height="{y(-0.5) - y(0.5):.1f}" fill="#F1F4F8"></rect>'
    ]
    for t in range(-int(limite), int(limite) + 1):
        guia = "#CBD5E1" if t == 0 else "#E8ECF2"
        etiqueta = "0" if t == 0 else _con_signo(t)
        partes += [
            f'<line x1="0" y1="{y(t):.1f}" x2="{ancho}" y2="{y(t):.1f}" stroke="{guia}"></line>',
            f'<text x="-6" y="{y(t) + 4:.1f}" text-anchor="end" font-size="11" fill="#5B6478">{etiqueta}</text>',
        ]
    puntos = " ".join(f"{i * paso:.1f},{y(v):.1f}" for i, (_, v) in enumerate(oni))
    partes += [
        f'<text x="{ancho - 4}" y="{y(0) + 14:.1f}" text-anchor="end" font-size="10" '
        'fill="#5B6478">rango neutral ±0,5</text>',
        f'<polyline points="{puntos}" fill="none" stroke="{color}" stroke-width="2" '
        'stroke-linejoin="round" stroke-linecap="round"></polyline>',
        f'<circle cx="{ancho}" cy="{y(ultimo):.1f}" r="4" fill="{color}" stroke="#FFFFFF" stroke-width="2"></circle>',
        f'<text x="{ancho - 10}" y="{y(ultimo) - 8:.1f}" text-anchor="end" font-size="12" '
        f'font-weight="700" fill="#1E2942">{_con_signo(ultimo)}</text>',
    ]
    ultimo_i = len(oni) - 1
    for i in [*range(0, ultimo_i, 3), ultimo_i]:
        ancla = "start" if i == 0 else ("end" if i == ultimo_i else "middle")
        partes.append(
            f'<text x="{i * paso:.1f}" y="{alto + 16}" text-anchor="{ancla}" '
            f'font-size="11" fill="#5B6478">{oni[i][0]}</text>'
        )
    for i, (trimestre, v) in enumerate(oni):
        izq = max(0.0, i * paso - paso / 2)
        der = min(float(ancho), i * paso + paso / 2)
        partes.append(
            f'<rect x="{izq:.1f}" y="0" width="{der - izq:.1f}" height="{alto}" fill="transparent">'
            f"<title>{trimestre} · ONI {_con_signo(v)} °C</title></rect>"
        )

    descripcion = f"ONI de los últimos {len(oni)} trimestres móviles; el más reciente es {_con_signo(ultimo)} °C"
    return (
        f'<svg viewBox="0 0 400 152" width="100%" role="img" aria-label="{descripcion}" '
        'style="display:block;font-family:sans-serif;">'
        f'<g transform="translate(40,14)">{"".join(partes)}</g></svg>'
    )


def _html_enso(oni):
    """Tarjeta de estado ENSO: fase actual, escala de fases y serie del ONI."""
    _, valor = oni[-1]
    fase = _fase_enso(valor)
    etiquetas = "".join(
        f'<span style="font-weight:700;color:#1E2942;">{corta}</span>' if i == fase else f"<span>{corta}</span>"
        for i, (corta, _, _) in enumerate(FASES_ENSO)
    )
    return "".join([
        '<div class="clima-card">',
        _encabezado("Estado ENSO", "#E8912B", derecha='<span class="clima-meta">NOAA CPC</span>'),
        '<div class="clima-body">',
        '<div class="clima-fila-valor">',
        f'<span style="font-size:18px;font-weight:700;color:#1E2942;">{FASES_ENSO[fase][1]}</span>',
        f'<span style="font-size:13px;font-weight:600;color:#5B6478;">ONI {_con_signo(valor)} °C</span>',
        "</div>",
        _medidor(fase, [color for _, _, color in FASES_ENSO], alto_activo=16),
        f'<div class="clima-etiquetas">{etiquetas}</div>',
        '<div class="clima-meta">Umbrales ONI: ±0,5 débil · ±1,0 moderado · ±1,5 fuerte (°C)</div>',
        '<div class="clima-separador"></div>',
        f'<div class="clima-subtitulo">ONI · últimos {len(oni)} trimestres móviles</div>',
        _svg_oni(oni),
        "</div></div>",
    ])


# ─── Secciones de la página ───────────────────────────────────────────────

def _render_titulo():
    """Tarjeta de título con los filtros. Devuelve (territorio, ventana en días)."""
    with st.container(border=True, key="clima-titulo"):
        col_texto, col_territorio, col_ventana = st.columns([5, 2, 2], vertical_alignment="bottom")

        # Los filtros se crean antes que el texto porque el subtítulo usa su valor;
        # Streamlit deja escribir en las columnas en cualquier orden.
        with col_territorio:
            territorio = st.selectbox("Territorio", TERRITORIOS, key="clima_territorio")
        with col_ventana:
            ventana = st.segmented_control(
                "Ventana de acumulado",
                options=[1, 3, 7, 15],
                format_func=lambda d: f"{d} d",
                default=7,
                key="clima_ventana",
            )
        with col_texto:
            # Mismo estilo de título que las tarjetas del dashboard (mayúsculas, 12px).
            st.markdown(
                '<div class="clima-titulo-pagina">'
                '<span class="clima-punto" style="background:#2563EB;"></span>'
                "Indicadores climáticos por provincia</div>",
                unsafe_allow_html=True,
            )
            detalle = " · promedio de las 6 provincias" if territorio == REGION else ""
            corte = f"{_fecha_corta(FECHA_CORTE_EJEMPLO)} {FECHA_CORTE_EJEMPLO.year}"
            st.caption(f"{territorio}{detalle} · corte CHIRPS: {corte} (datos de ejemplo)")

    # segmented_control devuelve None si el usuario vuelve a hacer clic en la
    # opción activa (la deselecciona); en ese caso se usa la ventana por defecto.
    return territorio, ventana or 7


def _render_acumulado(territorio, fechas, lluvia, normal, ventana):
    nombre = "Región Costa" if territorio == REGION else territorio
    with st.container(key="clima-card-acum"):
        st.markdown(
            _encabezado(f"Precipitación acumulada — {nombre}", "#2563EB", extra="clima-header-flush"),
            unsafe_allow_html=True,
        )
        tab_grafico, tab_tabla = st.tabs(["Gráfico", "Tabla"])
        with tab_grafico:
            st.markdown(
                _leyenda(ventana, len(lluvia)) + _svg_acumulado(fechas, lluvia, normal, ventana),
                unsafe_allow_html=True,
            )
        with tab_tabla:
            st.markdown(_tabla_diaria(fechas, lluvia, normal), unsafe_allow_html=True)


def render():
    """Dibuja la página completa. dashboard.py la llama desde su router."""
    st.markdown(_CSS, unsafe_allow_html=True)
    with st.container(key="clima-pagina"):
        _render_pagina()


def _render_pagina():
    territorio, ventana = _render_titulo()
    fechas, lluvia, normal = _serie_ejemplo(territorio)  # TODO Sprint 5-6: datos reales

    col_1, col_2, col_3, col_4 = st.columns(4)
    with col_1:
        st.markdown(_kpi_acumulado(lluvia, normal, ventana), unsafe_allow_html=True)
    with col_2:
        st.markdown(_kpi_acumulado(lluvia, normal, len(lluvia)), unsafe_allow_html=True)
    with col_3:
        st.markdown(_kpi_oni(_ONI_EJEMPLO), unsafe_allow_html=True)
    with col_4:
        st.markdown(_kpi_nino12(_NINO12_EJEMPLO), unsafe_allow_html=True)

    col_grafico, col_enso = st.columns([2, 1])
    with col_grafico:
        _render_acumulado(territorio, fechas, lluvia, normal, ventana)
    with col_enso:
        st.markdown(_html_enso(_ONI_EJEMPLO), unsafe_allow_html=True)

    st.caption(
        ":material/info: Vista previa con datos de ejemplo: todavía no conecta "
        "CHIRPS ni ONI (conexión en Sprint 5-6)."
    )