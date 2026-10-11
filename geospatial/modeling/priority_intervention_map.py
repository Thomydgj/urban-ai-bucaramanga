from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


# ============================================================
# CONFIGURACIÓN
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

INPUT_GPKG = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "modeling"
    / "urban_ai_intervention_zones.gpkg"
)

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "modeling"
)

OUTPUT_PNG = OUTPUT_DIR / "urban_ai_intervention_map.png"
OUTPUT_GPKG = OUTPUT_DIR / "urban_ai_intervention_map.gpkg"
OUTPUT_GEOJSON = OUTPUT_DIR / "urban_ai_intervention_map.geojson"


# ============================================================
# CONSTANTES
# ============================================================

REQUIRED_COLUMNS = [
    "zone_id",
    "operational_rank",
    "observations",
    "area_ha",
    "mean_probability",
    "hotspot_score",
    "operational_score",
    "dominant_condition",
    "intervention_level",
    "intervention_type",
]

EXPECTED_LEVELS = {
    "CRITICA",
    "ALTA",
    "MEDIA",
}

EXPECTED_TYPES = {
    "INTERVENCION_INTEGRAL",
    "MITIGACION_TERMICA",
    "DIAGNOSTICO_COMPLEMENTARIO",
    "INFRAESTRUCTURA_VERDE",
    "GESTION_SUPERFICIES",
}


# ============================================================
# FUNCIONES AUXILIARES
# ============================================================

def validate_input(gdf: gpd.GeoDataFrame) -> None:
    """Valida la estructura básica de la capa."""

    print("\n=== VALIDACIÓN DE ENTRADA ===")

    missing = [
        column
        for column in REQUIRED_COLUMNS
        if column not in gdf.columns
    ]

    if missing:
        raise ValueError(
            f"Faltan columnas requeridas: {missing}"
        )

    print("[OK] Todas las columnas requeridas existen")

    if gdf.empty:
        raise ValueError("La capa de intervención está vacía.")

    print(f"[OK] Zonas: {len(gdf)}")

    if gdf.crs is None:
        raise ValueError("La capa no tiene CRS definido.")

    print(f"[OK] CRS: {gdf.crs}")

    invalid = int((~gdf.geometry.is_valid).sum())
    empty = int(gdf.geometry.is_empty.sum())
    null = int(gdf.geometry.isna().sum())

    print(f"Geometrías inválidas: {invalid}")
    print(f"Geometrías vacías:    {empty}")
    print(f"Geometrías nulas:     {null}")

    if invalid > 0:
        raise ValueError("Existen geometrías inválidas.")

    if empty > 0:
        raise ValueError("Existen geometrías vacías.")

    if null > 0:
        raise ValueError("Existen geometrías nulas.")

    print("[OK] Geometrías válidas")


def validate_values(gdf: gpd.GeoDataFrame) -> None:
    """Valida categorías y variables numéricas."""

    print("\n=== VALIDACIÓN NUMÉRICA ===")

    numeric_columns = [
        "operational_rank",
        "observations",
        "area_ha",
        "mean_probability",
        "hotspot_score",
        "operational_score",
    ]

    for column in numeric_columns:

        if gdf[column].isna().any():
            raise ValueError(
                f"La columna {column} contiene valores nulos."
            )

        if not gdf[column].map(
            lambda value: isinstance(value, (int, float))
        ).all():
            raise ValueError(
                f"La columna {column} contiene valores no numéricos."
            )

    print("[OK] Variables numéricas válidas")

    for column in [
        "mean_probability",
        "hotspot_score",
        "operational_score",
    ]:

        minimum = float(gdf[column].min())
        maximum = float(gdf[column].max())

        if minimum < 0 or maximum > 1:
            raise ValueError(
                f"{column} fuera del rango [0,1]."
            )

    print("[OK] Scores dentro del rango [0,1]")

    levels = set(
        gdf["intervention_level"]
        .dropna()
        .astype(str)
        .unique()
    )

    unexpected_levels = levels - EXPECTED_LEVELS

    if unexpected_levels:
        raise ValueError(
            f"Niveles de intervención desconocidos: "
            f"{unexpected_levels}"
        )

    print("[OK] Niveles de intervención válidos")

    types = set(
        gdf["intervention_type"]
        .dropna()
        .astype(str)
        .unique()
    )

    unexpected_types = types - EXPECTED_TYPES

    if unexpected_types:
        raise ValueError(
            f"Tipos de intervención desconocidos: "
            f"{unexpected_types}"
        )

    print("[OK] Tipos de intervención válidos")


# ============================================================
# MAPA POR NIVEL
# ============================================================

def create_level_map(gdf: gpd.GeoDataFrame) -> None:
    """Genera mapa de niveles de intervención."""

    print("\n=== GENERANDO MAPA POR NIVEL ===")

    level_colors = {
        "CRITICA": "#8B0000",
        "ALTA": "#E67E22",
        "MEDIA": "#F1C40F",
    }

    fig, ax = plt.subplots(
        figsize=(12, 10)
    )

    for level in [
        "MEDIA",
        "ALTA",
        "CRITICA",
    ]:

        subset = gdf[
            gdf["intervention_level"] == level
        ]

        if subset.empty:
            continue

        subset.plot(
            ax=ax,
            color=level_colors[level],
            edgecolor="black",
            linewidth=0.35,
            alpha=0.75,
        )

    ax.set_title(
        "Urban AI Bucaramanga\n"
        "Zonas Prioritarias de Intervención",
        fontsize=16,
        fontweight="bold",
    )

    ax.set_xlabel("Longitud")
    ax.set_ylabel("Latitud")

    ax.grid(
        True,
        linestyle="--",
        linewidth=0.5,
        alpha=0.35,
    )

    legend_elements = [
        Patch(
            facecolor=level_colors["CRITICA"],
            edgecolor="black",
            label="Crítica",
        ),
        Patch(
            facecolor=level_colors["ALTA"],
            edgecolor="black",
            label="Alta",
        ),
        Patch(
            facecolor=level_colors["MEDIA"],
            edgecolor="black",
            label="Media",
        ),
    ]

    ax.legend(
        handles=legend_elements,
        title="Nivel de intervención",
        loc="best",
    )

    ax.text(
        0.01,
        0.01,
        (
            f"Zonas: {len(gdf):,}\n"
            f"Observaciones: "
            f"{int(gdf['observations'].sum()):,}\n"
            f"Área: {gdf['area_ha'].sum():,.1f} ha"
        ),
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="bottom",
        bbox=dict(
            boxstyle="round",
            facecolor="white",
            alpha=0.85,
        ),
    )

    plt.tight_layout()

    plt.savefig(
        OUTPUT_PNG,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close()

    print(f"Mapa PNG: {OUTPUT_PNG}")


# ============================================================
# MAPA POR TIPO
# ============================================================

def create_type_map(gdf: gpd.GeoDataFrame) -> Path:
    """Genera mapa según tipo de intervención."""

    print("\n=== GENERANDO MAPA POR TIPO ===")

    output = OUTPUT_DIR / "urban_ai_intervention_type_map.png"

    type_colors = {
        "INTERVENCION_INTEGRAL": "#7B1FA2",
        "MITIGACION_TERMICA": "#D32F2F",
        "DIAGNOSTICO_COMPLEMENTARIO": "#1976D2",
        "INFRAESTRUCTURA_VERDE": "#388E3C",
        "GESTION_SUPERFICIES": "#F57C00",
    }

    fig, ax = plt.subplots(
        figsize=(13, 10)
    )

    for intervention_type, color in type_colors.items():

        subset = gdf[
            gdf["intervention_type"] == intervention_type
        ]

        if subset.empty:
            continue

        subset.plot(
            ax=ax,
            color=color,
            edgecolor="black",
            linewidth=0.3,
            alpha=0.75,
        )

    ax.set_title(
        "Urban AI Bucaramanga\n"
        "Tipos de Intervención Territorial",
        fontsize=16,
        fontweight="bold",
    )

    ax.set_xlabel("Longitud")
    ax.set_ylabel("Latitud")

    ax.grid(
        True,
        linestyle="--",
        linewidth=0.5,
        alpha=0.35,
    )

    legend_elements = []

    labels = {
        "INTERVENCION_INTEGRAL":
            "Intervención integral",
        "MITIGACION_TERMICA":
            "Mitigación térmica",
        "DIAGNOSTICO_COMPLEMENTARIO":
            "Diagnóstico complementario",
        "INFRAESTRUCTURA_VERDE":
            "Infraestructura verde",
        "GESTION_SUPERFICIES":
            "Gestión de superficies",
    }

    for intervention_type, color in type_colors.items():

        if intervention_type not in set(
            gdf["intervention_type"]
        ):
            continue

        legend_elements.append(
            Patch(
                facecolor=color,
                edgecolor="black",
                label=labels[intervention_type],
            )
        )

    ax.legend(
        handles=legend_elements,
        title="Tipo de intervención",
        loc="best",
        fontsize=8,
    )

    plt.tight_layout()

    plt.savefig(
        output,
        dpi=300,
        bbox_inches="tight",
    )

    plt.close()

    print(f"Mapa PNG: {output}")

    return output


# ============================================================
# EXPORTACIÓN ESPACIAL
# ============================================================

def export_layers(gdf: gpd.GeoDataFrame) -> None:
    """Exporta GeoPackage y GeoJSON."""

    print("\n=== EXPORTANDO CAPAS ===")

    export_gdf = gdf.copy()

    export_gdf.to_file(
        OUTPUT_GPKG,
        layer="intervention_map",
        driver="GPKG",
    )

    print(
        f"GeoPackage: {OUTPUT_GPKG}"
    )

    export_gdf.to_file(
        OUTPUT_GEOJSON,
        driver="GeoJSON",
    )

    print(
        f"GeoJSON: {OUTPUT_GEOJSON}"
    )


# ============================================================
# RESUMEN
# ============================================================

def print_summary(gdf: gpd.GeoDataFrame) -> None:

    print("\n" + "=" * 60)
    print("RESUMEN DEL MAPA DE INTERVENCIÓN")
    print("=" * 60)

    print(
        f"Zonas: {len(gdf):,}"
    )

    print(
        f"Observaciones: "
        f"{int(gdf['observations'].sum()):,}"
    )

    print(
        f"Área total: "
        f"{gdf['area_ha'].sum():,.2f} ha"
    )

    print(
        f"Probability media: "
        f"{gdf['mean_probability'].mean():.6f}"
    )

    print(
        f"Hotspot score medio: "
        f"{gdf['hotspot_score'].mean():.6f}"
    )

    print(
        f"Operational score medio: "
        f"{gdf['operational_score'].mean():.6f}"
    )

    print("\n=== NIVELES ===")

    print(
        gdf["intervention_level"]
        .value_counts()
    )

    print("\n=== TIPOS ===")

    print(
        gdf["intervention_type"]
        .value_counts()
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("PRIORITY INTERVENTION MAP")
    print("Urban AI Bucaramanga")
    print("=" * 60)

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not INPUT_GPKG.exists():
        raise FileNotFoundError(
            f"No existe el archivo:\n{INPUT_GPKG}"
        )

    print("\n=== CARGANDO DATOS ===")

    gdf = gpd.read_file(
        INPUT_GPKG,
        layer="intervention_zones",
    )

    print(
        f"Zonas cargadas: {len(gdf):,}"
    )

    validate_input(gdf)
    validate_values(gdf)

    print_summary(gdf)

    create_level_map(gdf)
    create_type_map(gdf)

    export_layers(gdf)

    print("\n" + "=" * 60)
    print("MAPA DE INTERVENCIÓN GENERADO")
    print("=" * 60)

    print(
        "[OK] Capa espacial validada"
    )

    print(
        "[OK] Mapa por nivel generado"
    )

    print(
        "[OK] Mapa por tipo generado"
    )

    print(
        "[OK] GeoPackage exportado"
    )

    print(
        "[OK] GeoJSON exportado"
    )

    print("\nProceso completado correctamente.")


if __name__ == "__main__":
    main()