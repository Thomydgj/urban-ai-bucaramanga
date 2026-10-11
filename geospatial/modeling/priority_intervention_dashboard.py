
"""
PRIORITY INTERVENTION DASHBOARD
Urban AI Bucaramanga

Dashboard exploratorio para visualizar la capa maestra de intervención.

Entrada principal:
    data/processed/modeling/urban_ai_master_intervention.gpkg

Salidas:
    data/processed/modeling/urban_ai_intervention_dashboard.html

Uso:

    streamlit run geospatial/modeling/priority_intervention_dashboard.py

También puede ejecutarse directamente para generar únicamente
el HTML del mapa:

    python -m geospatial.modeling.priority_intervention_dashboard
"""

from pathlib import Path
import sys
import html

import geopandas as gpd
import pandas as pd
import folium
import streamlit as st
from streamlit_folium import st_folium


# ============================================================
# CONFIGURACIÓN
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

MODELING_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "modeling"
)

MASTER_GPKG = (
    MODELING_DIR
    / "urban_ai_master_intervention.gpkg"
)

OUTPUT_HTML = (
    MODELING_DIR
    / "urban_ai_intervention_dashboard.html"
)

MASTER_LAYER = "intervention_zones"


# ============================================================
# CONFIGURACIÓN STREAMLIT
# ============================================================

st.set_page_config(
    page_title="Urban AI Bucaramanga",
    page_icon="🗺️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# ESTILOS
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 30px;
        font-weight: 700;
        color: #123b63;
        margin-bottom: 5px;
    }

    .subtitle {
        font-size: 15px;
        color: #52606d;
        margin-bottom: 20px;
    }

    .section-title {
        font-size: 21px;
        font-weight: 700;
        color: #123b63;
        margin-top: 15px;
        margin-bottom: 10px;
    }

    .info-card {
        background: #f7f9fb;
        border: 1px solid #d9e2ec;
        border-radius: 8px;
        padding: 14px;
        margin-bottom: 10px;
    }

    .info-label {
        font-size: 12px;
        color: #627d98;
        margin-bottom: 3px;
    }

    .info-value {
        font-size: 20px;
        font-weight: 700;
        color: #102a43;
    }

    .recommendation-card {
        background: #f7f9fb;
        border-left: 5px solid #123b63;
        border-radius: 5px;
        padding: 14px;
        margin-top: 10px;
        margin-bottom: 10px;
    }

    .critical {
        border-left-color: #d73027;
    }

    .high {
        border-left-color: #fc8d59;
    }

    .medium {
        border-left-color: #fee08b;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# COLUMNAS REQUERIDAS
# ============================================================

REQUIRED_COLUMNS = [
    "zone_id",
    "operational_rank",
    "hotspot_rank",
    "observations",
    "observation_percentage",
    "area_ha",
    "area_percentage",
    "mean_probability",
    "max_probability",
    "hotspot_score",
    "operational_score",
    "priority_density",
    "mean_ndvi",
    "mean_ndbi",
    "mean_lst",
    "dominant_condition",
    "density_level",
    "intervention_level",
    "priority_class",
    "intervention_type",
    "zone_description",
    "centroid_x",
    "centroid_y",
    "recommendation",
    "intervention_objective",
    "monitoring_indicator",
    "priority_timeframe",
    "priority_reason",
    "action_package",
    "geometry",
]


# ============================================================
# COLORES
# ============================================================

LEVEL_COLORS = {
    "CRITICA": "#d73027",
    "ALTA": "#fc8d59",
    "MEDIA": "#fee08b",
}


TYPE_COLORS = {
    "INTERVENCION_INTEGRAL": "#7b3294",
    "MITIGACION_TERMICA": "#d73027",
    "INFRAESTRUCTURA_VERDE": "#1a9850",
    "DIAGNOSTICO_COMPLEMENTARIO": "#3288bd",
    "GESTION_SUPERFICIES": "#fdae61",
}


TIMEFRAME_COLORS = {
    "INMEDIATO": "#d73027",
    "CORTO_PLAZO": "#fc8d59",
    "MEDIANO_PLAZO": "#91bfdb",
}


# ============================================================
# UTILIDADES
# ============================================================

def fmt_number(value, decimals=2):
    """Formatea números de manera segura."""

    if value is None:
        return "N/D"

    try:
        if pd.isna(value):
            return "N/D"
    except Exception:
        pass

    try:
        return f"{float(value):,.{decimals}f}"
    except Exception:
        return str(value)


def fmt_percent(value, decimals=2):
    """Formatea una proporción como porcentaje."""

    if value is None:
        return "N/D"

    try:
        if pd.isna(value):
            return "N/D"
    except Exception:
        pass

    try:
        return f"{float(value) * 100:.{decimals}f}%"
    except Exception:
        return str(value)


def clean_text(value):
    """Convierte valores a texto HTML seguro."""

    if value is None:
        return "N/D"

    try:
        if pd.isna(value):
            return "N/D"
    except Exception:
        pass

    return html.escape(str(value))


# ============================================================
# CARGAR DATOS
# ============================================================

@st.cache_data(show_spinner=False)
def load_master_data(path):
    """Carga la capa maestra."""

    if not path.exists():
        raise FileNotFoundError(
            f"No existe el GeoPackage maestro:\n{path}"
        )

    layers = gpd.list_layers(path)

    if layers.empty:
        raise ValueError(
            "El GeoPackage no contiene capas."
        )

    available_layers = layers["name"].tolist()

    if MASTER_LAYER in available_layers:
        layer = MASTER_LAYER
    else:
        layer = available_layers[0]

    gdf = gpd.read_file(
        path,
        layer=layer,
    )

    return gdf


# ============================================================
# VALIDAR DATOS
# ============================================================

def validate_data(gdf):
    """Valida la capa maestra antes de construir el dashboard."""

    missing = [
        column
        for column in REQUIRED_COLUMNS
        if column not in gdf.columns
    ]

    if missing:
        raise ValueError(
            "Faltan columnas requeridas:\n"
            + "\n".join(missing)
        )

    if gdf.empty:
        raise ValueError(
            "La capa maestra está vacía."
        )

    if gdf.crs is None:
        raise ValueError(
            "La capa no tiene CRS definido."
        )

    invalid = int(
        (~gdf.geometry.is_valid).sum()
    )

    empty = int(
        gdf.geometry.is_empty.sum()
    )

    null = int(
        gdf.geometry.isna().sum()
    )

    if invalid > 0:
        raise ValueError(
            f"Existen {invalid} geometrías inválidas."
        )

    if empty > 0:
        raise ValueError(
            f"Existen {empty} geometrías vacías."
        )

    if null > 0:
        raise ValueError(
            f"Existen {null} geometrías nulas."
        )

    return True


# ============================================================
# CONSTRUIR POPUP
# ============================================================

def build_popup(row):
    """
    Construye el popup completo de una zona.
    """

    level = str(
        row["intervention_level"]
    )

    level_class = {
        "CRITICA": "critical",
        "ALTA": "high",
        "MEDIA": "medium",
    }.get(level, "")

    zone_id = clean_text(row["zone_id"])

    recommendation = clean_text(
        row["recommendation"]
    )

    objective = clean_text(
        row["intervention_objective"]
    )

    indicator = clean_text(
        row["monitoring_indicator"]
    )

    reason = clean_text(
        row["priority_reason"]
    )

    action_package = clean_text(
        row["action_package"]
    )

    html_content = f"""
    <div style="
        width: 440px;
        max-height: 600px;
        overflow-y: auto;
        font-family: Arial, sans-serif;
        font-size: 13px;
    ">

        <div style="
            border-bottom: 2px solid #123b63;
            padding-bottom: 8px;
            margin-bottom: 12px;
        ">

            <div style="
                font-size: 20px;
                font-weight: 700;
                color: #123b63;
            ">
                {zone_id}
            </div>

            <div style="
                margin-top: 5px;
                color: #52606d;
            ">
                Ranking operacional:
                <b>{clean_text(row["operational_rank"])}</b>
            </div>

        </div>


        <table style="
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 12px;
        ">

            <tr>
                <td style="padding: 5px;">
                    <b>Observaciones</b>
                </td>
                <td style="padding: 5px;">
                    {fmt_number(row["observations"], 0)}
                </td>
            </tr>

            <tr>
                <td style="padding: 5px;">
                    <b>Área</b>
                </td>
                <td style="padding: 5px;">
                    {fmt_number(row["area_ha"], 2)} ha
                </td>
            </tr>

            <tr>
                <td style="padding: 5px;">
                    <b>Probability media</b>
                </td>
                <td style="padding: 5px;">
                    {fmt_number(row["mean_probability"], 4)}
                </td>
            </tr>

            <tr>
                <td style="padding: 5px;">
                    <b>Hotspot score</b>
                </td>
                <td style="padding: 5px;">
                    {fmt_number(row["hotspot_score"], 4)}
                </td>
            </tr>

            <tr>
                <td style="padding: 5px;">
                    <b>Operational score</b>
                </td>
                <td style="padding: 5px;">
                    {fmt_number(row["operational_score"], 4)}
                </td>
            </tr>

            <tr>
                <td style="padding: 5px;">
                    <b>Densidad</b>
                </td>
                <td style="padding: 5px;">
                    {fmt_number(row["priority_density"], 4)}
                </td>
            </tr>

            <tr>
                <td style="padding: 5px;">
                    <b>NDVI</b>
                </td>
                <td style="padding: 5px;">
                    {fmt_number(row["mean_ndvi"], 4)}
                </td>
            </tr>

            <tr>
                <td style="padding: 5px;">
                    <b>NDBI</b>
                </td>
                <td style="padding: 5px;">
                    {fmt_number(row["mean_ndbi"], 4)}
                </td>
            </tr>

            <tr>
                <td style="padding: 5px;">
                    <b>LST</b>
                </td>
                <td style="padding: 5px;">
                    {fmt_number(row["mean_lst"], 2)}
                </td>
            </tr>

        </table>


        <div class="{level_class}" style="
            padding: 9px;
            border-left: 5px solid;
            background: #f7f9fb;
            margin-bottom: 10px;
        ">

            <b>Nivel:</b>
            {clean_text(row["intervention_level"])}

            <br>

            <b>Tipo:</b>
            {clean_text(row["intervention_type"])}

            <br>

            <b>Plazo:</b>
            {clean_text(row["priority_timeframe"])}

        </div>


        <div style="
            padding: 10px;
            background: #eef4f8;
            border-radius: 5px;
            margin-bottom: 8px;
        ">

            <div style="
                font-weight: 700;
                color: #123b63;
                margin-bottom: 5px;
            ">
                Condición dominante
            </div>

            {clean_text(row["dominant_condition"])}

        </div>


        <div style="
            padding: 10px;
            background: #f7f9fb;
            border-radius: 5px;
            margin-bottom: 8px;
        ">

            <div style="
                font-weight: 700;
                color: #123b63;
                margin-bottom: 5px;
            ">
                Recomendación
            </div>

            {recommendation}

        </div>


        <div style="
            padding: 10px;
            background: #f7f9fb;
            border-radius: 5px;
            margin-bottom: 8px;
        ">

            <div style="
                font-weight: 700;
                color: #123b63;
                margin-bottom: 5px;
            ">
                Objetivo de intervención
            </div>

            {objective}

        </div>


        <div style="
            padding: 10px;
            background: #f7f9fb;
            border-radius: 5px;
            margin-bottom: 8px;
        ">

            <div style="
                font-weight: 700;
                color: #123b63;
                margin-bottom: 5px;
            ">
                Indicador de monitoreo
            </div>

            {indicator}

        </div>


        <div style="
            padding: 10px;
            background: #f7f9fb;
            border-radius: 5px;
            margin-bottom: 8px;
        ">

            <div style="
                font-weight: 700;
                color: #123b63;
                margin-bottom: 5px;
            ">
                Razón de prioridad
            </div>

            {reason}

        </div>


        <div style="
            padding: 10px;
            background: #f7f9fb;
            border-radius: 5px;
        ">

            <div style="
                font-weight: 700;
                color: #123b63;
                margin-bottom: 5px;
            ">
                Paquete de acción
            </div>

            {action_package}

        </div>

    </div>
    """

    return folium.Popup(
        html_content,
        max_width=480,
    )


# ============================================================
# ESTILO DE GEOMETRÍAS
# ============================================================

def make_style(color):
    """Devuelve estilo de una zona."""

    return {
        "fillColor": color,
        "color": "#263238",
        "weight": 1,
        "fillOpacity": 0.65,
    }


def make_highlight():
    """Estilo al pasar el mouse."""

    return {
        "weight": 3,
        "color": "#111111",
        "fillOpacity": 0.85,
    }


# ============================================================
# CREAR MAPA
# ============================================================

def build_map(gdf):
    """
    Construye el mapa interactivo.

    IMPORTANTE:
    No depende de OpenStreetMap.

    Se agrega un mapa base de Esri como opción visual.
    Las zonas se dibujan independientemente del mapa base,
    por lo que seguirán apareciendo si el proveedor externo
    no está disponible.
    """

    data = gdf.copy()

    # --------------------------------------------------------
    # CRS
    # --------------------------------------------------------

    if data.crs is None:
        raise ValueError(
            "La capa no tiene CRS."
        )

    if data.crs.to_epsg() != 4326:
        data = data.to_crs(4326)

    # --------------------------------------------------------
    # ELIMINAR GEOMETRÍAS PROBLEMÁTICAS
    # --------------------------------------------------------

    data = data[
        data.geometry.notna()
        & ~data.geometry.is_empty
    ].copy()

    if data.empty:
        raise ValueError(
            "No existen geometrías para visualizar."
        )

    # --------------------------------------------------------
    # BOUNDS
    # --------------------------------------------------------

    minx, miny, maxx, maxy = data.total_bounds

    center_lat = (
        miny + maxy
    ) / 2

    center_lon = (
        minx + maxx
    ) / 2

    # --------------------------------------------------------
    # MAPA
    # --------------------------------------------------------
    #
    # tiles=None es la clave:
    #
    # NO se solicita OpenStreetMap.
    #
    # Así evitamos:
    #
    # 403 Access blocked
    #
    # y el mapa no queda lleno de tarjetas de error.
    #

    m = folium.Map(
        location=[
            center_lat,
            center_lon,
        ],
        zoom_start=12,
        tiles=None,
        control_scale=True,
        prefer_canvas=True,
    )

    # --------------------------------------------------------
    # MAPA BASE ESRI
    # --------------------------------------------------------
    #
    # Tiene attribution explícita.
    #
    # Si el servidor externo no está disponible,
    # las zonas siguen funcionando.
    #

    folium.TileLayer(
        tiles=(
            "https://server.arcgisonline.com/"
            "ArcGIS/rest/services/"
            "World_Street_Map/"
            "MapServer/tile/{z}/{y}/{x}"
        ),
        attr=(
            "Tiles © Esri — "
            "Sources: Esri, Garmin, USGS, "
            "NPS, and the GIS User Community"
        ),
        name="Mapa base",
        overlay=False,
        control=True,
        show=True,
    ).add_to(m)

    # --------------------------------------------------------
    # CAPA DE NIVEL
    # --------------------------------------------------------

    level_groups = {}

    for level, color in LEVEL_COLORS.items():

        subset = data[
            data["intervention_level"]
            == level
        ].copy()

        if subset.empty:
            continue

        group = folium.FeatureGroup(
            name=f"Nivel — {level}",
            show=True,
        )

        for _, row in subset.iterrows():

            geojson = folium.GeoJson(
                row.geometry.__geo_interface__,
                style_function=(
                    lambda feature, c=color:
                    make_style(c)
                ),
                highlight_function=(
                    lambda feature:
                    make_highlight()
                ),
                tooltip=folium.GeoJsonTooltip(
                    fields=[
                        "zone_id",
                        "operational_rank",
                        "observations",
                        "area_ha",
                        "intervention_level",
                        "intervention_type",
                        "operational_score",
                    ],
                    aliases=[
                        "Zona",
                        "Ranking",
                        "Observaciones",
                        "Área (ha)",
                        "Nivel",
                        "Tipo",
                        "Operational score",
                    ],
                    localize=True,
                    sticky=False,
                    labels=True,
                ),
            )

            geojson.add_child(
                build_popup(row)
            )

            geojson.add_to(group)

        group.add_to(m)

        level_groups[level] = group

    # --------------------------------------------------------
    # CAPA POR TIPO
    # --------------------------------------------------------

    for intervention_type, color in TYPE_COLORS.items():

        subset = data[
            data["intervention_type"]
            == intervention_type
        ].copy()

        if subset.empty:
            continue

        group = folium.FeatureGroup(
            name=f"Tipo — {intervention_type}",
            show=False,
        )

        for _, row in subset.iterrows():

            geojson = folium.GeoJson(
                row.geometry.__geo_interface__,
                style_function=(
                    lambda feature, c=color:
                    make_style(c)
                ),
                highlight_function=(
                    lambda feature:
                    make_highlight()
                ),
                tooltip=folium.GeoJsonTooltip(
                    fields=[
                        "zone_id",
                        "operational_rank",
                        "observations",
                        "area_ha",
                        "intervention_level",
                        "intervention_type",
                        "operational_score",
                    ],
                    aliases=[
                        "Zona",
                        "Ranking",
                        "Observaciones",
                        "Área (ha)",
                        "Nivel",
                        "Tipo",
                        "Operational score",
                    ],
                    localize=True,
                    sticky=False,
                    labels=True,
                ),
            )

            geojson.add_child(
                build_popup(row)
            )

            geojson.add_to(group)

        group.add_to(m)

    # --------------------------------------------------------
    # CAPA POR PLAZO
    # --------------------------------------------------------

    for timeframe, color in TIMEFRAME_COLORS.items():

        subset = data[
            data["priority_timeframe"]
            == timeframe
        ].copy()

        if subset.empty:
            continue

        group = folium.FeatureGroup(
            name=f"Plazo — {timeframe}",
            show=False,
        )

        for _, row in subset.iterrows():

            geojson = folium.GeoJson(
                row.geometry.__geo_interface__,
                style_function=(
                    lambda feature, c=color:
                    make_style(c)
                ),
                highlight_function=(
                    lambda feature:
                    make_highlight()
                ),
                tooltip=folium.GeoJsonTooltip(
                    fields=[
                        "zone_id",
                        "operational_rank",
                        "priority_timeframe",
                        "operational_score",
                    ],
                    aliases=[
                        "Zona",
                        "Ranking",
                        "Plazo",
                        "Operational score",
                    ],
                    localize=True,
                    sticky=False,
                    labels=True,
                ),
            )

            geojson.add_child(
                build_popup(row)
            )

            geojson.add_to(group)

        group.add_to(m)

    # --------------------------------------------------------
    # LEYENDA
    # --------------------------------------------------------

    legend_html = """
    <div style="
        position: fixed;
        bottom: 25px;
        left: 25px;
        z-index: 9999;
        background: white;
        padding: 14px 16px;
        border-radius: 8px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.25);
        font-family: Arial, sans-serif;
        font-size: 13px;
        line-height: 1.7;
    ">

        <div style="
            font-weight: bold;
            font-size: 15px;
            margin-bottom: 7px;
        ">
            Nivel de intervención
        </div>

        <div>
            <span style="
                display:inline-block;
                width:14px;
                height:14px;
                background:#d73027;
                margin-right:7px;
                vertical-align:middle;
            "></span>
            CRÍTICA
        </div>

        <div>
            <span style="
                display:inline-block;
                width:14px;
                height:14px;
                background:#fc8d59;
                margin-right:7px;
                vertical-align:middle;
            "></span>
            ALTA
        </div>

        <div>
            <span style="
                display:inline-block;
                width:14px;
                height:14px;
                background:#fee08b;
                margin-right:7px;
                vertical-align:middle;
            "></span>
            MEDIA
        </div>

    </div>
    """

    m.get_root().html.add_child(
        folium.Element(
            legend_html
        )
    )

    # --------------------------------------------------------
    # TÍTULO DEL MAPA
    # --------------------------------------------------------

    title_html = """
    <div style="
        position: fixed;
        top: 12px;
        left: 55px;
        z-index: 9999;
        background: white;
        padding: 8px 14px;
        border-radius: 6px;
        box-shadow: 0 1px 5px rgba(0,0,0,0.2);
        font-family: Arial, sans-serif;
        font-weight: bold;
        color: #123b63;
        font-size: 15px;
    ">
        Zonas prioritarias de intervención
    </div>
    """

    m.get_root().html.add_child(
        folium.Element(
            title_html
        )
    )

    # --------------------------------------------------------
    # AJUSTAR EXTENSIÓN
    # --------------------------------------------------------

    m.fit_bounds(
        [
            [miny, minx],
            [maxy, maxx],
        ],
        padding=(25, 25),
    )

    # --------------------------------------------------------
    # CONTROL DE CAPAS
    # --------------------------------------------------------

    folium.LayerControl(
        collapsed=False,
        position="topright",
    ).add_to(m)

    return m


# ============================================================
# EXPORTAR HTML
# ============================================================

def export_map_html(map_object, output_path):
    """Guarda el mapa Folium como HTML."""

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    map_object.save(
        str(output_path)
    )

    return output_path


# ============================================================
# TARJETA KPI
# ============================================================

def metric_card(label, value):
    return f"""
    <div class="info-card">
        <div class="info-label">
            {html.escape(label)}
        </div>
        <div class="info-value">
            {html.escape(str(value))}
        </div>
    </div>
    """


# ============================================================
# DASHBOARD
# ============================================================

def run_dashboard():
    """Ejecuta el dashboard Streamlit."""

    st.markdown(
        '<div class="main-title">'
        'Mapa interactivo de intervención'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="subtitle">'
        'Seleccione una zona para consultar sus indicadores, '
        'condición dominante y recomendación operativa.'
        '</div>',
        unsafe_allow_html=True,
    )

    # --------------------------------------------------------
    # CARGA
    # --------------------------------------------------------

    try:

        gdf = load_master_data(
            MASTER_GPKG
        )

        validate_data(gdf)

    except Exception as exc:

        st.error(
            "No fue posible cargar la capa maestra."
        )

        st.code(
            str(exc)
        )

        st.stop()

    # --------------------------------------------------------
    # CRS
    # --------------------------------------------------------

    if gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(4326)

    # --------------------------------------------------------
    # SIDEBAR
    # --------------------------------------------------------

    st.sidebar.header(
        "Filtros"
    )

    levels = sorted(
        gdf[
            "intervention_level"
        ]
        .dropna()
        .unique()
        .tolist()
    )

    selected_levels = st.sidebar.multiselect(
        "Nivel de intervención",
        options=levels,
        default=levels,
    )

    types = sorted(
        gdf[
            "intervention_type"
        ]
        .dropna()
        .unique()
        .tolist()
    )

    selected_types = st.sidebar.multiselect(
        "Tipo de intervención",
        options=types,
        default=types,
    )

    timeframes = sorted(
        gdf[
            "priority_timeframe"
        ]
        .dropna()
        .unique()
        .tolist()
    )

    selected_timeframes = st.sidebar.multiselect(
        "Plazo",
        options=timeframes,
        default=timeframes,
    )

    # --------------------------------------------------------
    # RANKING
    # --------------------------------------------------------

    max_rank = int(
        gdf["operational_rank"].max()
    )

    rank_limit = st.sidebar.slider(
        "Mostrar hasta ranking operacional",
        min_value=1,
        max_value=max_rank,
        value=min(50, max_rank),
    )

    # --------------------------------------------------------
    # APLICAR FILTROS
    # --------------------------------------------------------

    filtered = gdf[
        gdf["intervention_level"].isin(
            selected_levels
        )
        &
        gdf["intervention_type"].isin(
            selected_types
        )
        &
        gdf["priority_timeframe"].isin(
            selected_timeframes
        )
        &
        (
            gdf["operational_rank"]
            <= rank_limit
        )
    ].copy()

    # --------------------------------------------------------
    # KPI
    # --------------------------------------------------------

    total_zones = len(filtered)

    total_observations = int(
        filtered["observations"].sum()
    )

    total_area = float(
        filtered["area_ha"].sum()
    )

    if total_observations > 0:

        weighted_probability = (
            (
                filtered["mean_probability"]
                * filtered["observations"]
            ).sum()
            / total_observations
        )

        weighted_operational = (
            (
                filtered["operational_score"]
                * filtered["observations"]
            ).sum()
            / total_observations
        )

    else:

        weighted_probability = 0

        weighted_operational = 0

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "Zonas",
            f"{total_zones:,}",
        )

    with col2:
        st.metric(
            "Observaciones",
            f"{total_observations:,}",
        )

    with col3:
        st.metric(
            "Área",
            f"{total_area:,.2f} ha",
        )

    with col4:
        st.metric(
            "Operational score",
            f"{weighted_operational:.4f}",
        )

    # --------------------------------------------------------
    # MAPA
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        'Mapa de zonas prioritarias'
        '</div>',
        unsafe_allow_html=True,
    )

    if filtered.empty:

        st.warning(
            "No existen zonas con los filtros seleccionados."
        )

    else:

        intervention_map = build_map(
            filtered
        )

        map_data = st_folium(
            intervention_map,
            width=None,
            height=650,
            returned_objects=[
                "last_object_clicked",
            ],
            key="intervention_map",
        )

        # ----------------------------------------------------
        # ZONA SELECCIONADA
        # ----------------------------------------------------

        clicked = (
            map_data.get(
                "last_object_clicked"
            )
            if map_data
            else None
        )

        if clicked:
            st.info(
                "Zona seleccionada en el mapa. "
                "Utilice el popup de la zona para consultar "
                "la recomendación completa."
            )

    # --------------------------------------------------------
    # TABLA
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        'Recomendaciones operativas'
        '</div>',
        unsafe_allow_html=True,
    )

    table_columns = [
        "zone_id",
        "operational_rank",
        "intervention_level",
        "intervention_type",
        "observations",
        "area_ha",
        "operational_score",
        "priority_timeframe",
        "recommendation",
        "intervention_objective",
        "monitoring_indicator",
        "action_package",
    ]

    table = (
        filtered[
            table_columns
        ]
        .sort_values(
            "operational_rank"
        )
        .copy()
    )

    table = table.rename(
        columns={
            "zone_id": "Zona",
            "operational_rank": "Rank",
            "intervention_level": "Nivel",
            "intervention_type": "Tipo",
            "observations": "Observaciones",
            "area_ha": "Área ha",
            "operational_score": "Operational score",
            "priority_timeframe": "Plazo",
            "recommendation": "Recomendación",
            "intervention_objective": "Objetivo",
            "monitoring_indicator": "Indicador",
            "action_package": "Paquete de acción",
        }
    )

    st.dataframe(
        table,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Operational score": st.column_config.NumberColumn(
                format="%.4f"
            ),
            "Área ha": st.column_config.NumberColumn(
                format="%.2f"
            ),
        },
    )

    # --------------------------------------------------------
    # RESUMEN
    # --------------------------------------------------------

    st.markdown(
        '<div class="section-title">'
        'Distribución de intervención'
        '</div>',
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        level_summary = (
            filtered[
                "intervention_level"
            ]
            .value_counts()
            .rename_axis("Nivel")
            .reset_index(
                name="Zonas"
            )
        )

        st.dataframe(
            level_summary,
            use_container_width=True,
            hide_index=True,
        )

    with col2:

        type_summary = (
            filtered[
                "intervention_type"
            ]
            .value_counts()
            .rename_axis("Tipo")
            .reset_index(
                name="Zonas"
            )
        )

        st.dataframe(
            type_summary,
            use_container_width=True,
            hide_index=True,
        )

    with col3:

        timeframe_summary = (
            filtered[
                "priority_timeframe"
            ]
            .value_counts()
            .rename_axis("Plazo")
            .reset_index(
                name="Zonas"
            )
        )

        st.dataframe(
            timeframe_summary,
            use_container_width=True,
            hide_index=True,
        )

    # --------------------------------------------------------
    # INFORMACIÓN DEL MODELO
    # --------------------------------------------------------

    with st.expander(
        "Información de la capa maestra"
    ):

        st.write(
            f"**Archivo:** `{MASTER_GPKG}`"
        )

        st.write(
            f"**CRS:** `{gdf.crs}`"
        )

        st.write(
            f"**Zonas totales:** {len(gdf):,}"
        )

        st.write(
            f"**Observaciones totales:** "
            f"{int(gdf['observations'].sum()):,}"
        )

        st.write(
            f"**Área total:** "
            f"{gdf['area_ha'].sum():,.2f} ha"
        )

        st.write(
            "**Estado:** capa maestra validada."
        )


# ============================================================
# GENERACIÓN DIRECTA DEL HTML
# ============================================================

def generate_html():
    """
    Genera solamente el mapa HTML.

    Esto permite mantener el archivo:

        urban_ai_intervention_dashboard.html

    independientemente de Streamlit.
    """

    print("=" * 60)
    print("PRIORITY INTERVENTION DASHBOARD")
    print("Urban AI Bucaramanga")
    print("=" * 60)

    print()
    print("=== ARCHIVO DE ENTRADA ===")
    print(MASTER_GPKG)

    if not MASTER_GPKG.exists():
        print()
        print("[ERROR] No existe el GeoPackage maestro.")
        sys.exit(1)

    print()
    print("=== CARGANDO DATOS ===")

    gdf = load_master_data(
        MASTER_GPKG
    )

    print(
        f"Zonas cargadas: {len(gdf):,}"
    )

    print()
    print("=== VALIDACIÓN ===")

    validate_data(gdf)

    print(
        "[OK] Todas las columnas requeridas"
    )

    print(
        f"[OK] CRS: {gdf.crs}"
    )

    print(
        "[OK] Geometrías válidas"
    )

    print()
    print("=== CONSTRUYENDO MAPA ===")

    intervention_map = build_map(
        gdf
    )

    print(
        "[OK] Mapa construido"
    )

    print()
    print("=== EXPORTANDO HTML ===")

    output = export_map_html(
        intervention_map,
        OUTPUT_HTML,
    )

    print(
        f"HTML:\n{output}"
    )

    print()
    print("=" * 60)
    print("DASHBOARD GENERADO CORRECTAMENTE")
    print("=" * 60)


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    # Si se ejecuta mediante Streamlit,
    # STREAMLIT_SERVER_PORT estará disponible.
    #
    # En ejecución normal:
    #
    # python -m geospatial.modeling.priority_intervention_dashboard
    #
    # se genera el HTML.

    if "streamlit" in sys.modules:

        run_dashboard()

    else:

        generate_html()
