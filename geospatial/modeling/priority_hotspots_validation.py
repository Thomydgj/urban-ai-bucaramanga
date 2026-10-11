from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd


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

ANALYSIS_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "analysis"
)

HOTSPOTS_GPKG = (
    MODELING_DIR
    / "urban_priority_hotspots.gpkg"
)

HOTSPOTS_GEOJSON = (
    MODELING_DIR
    / "urban_priority_hotspots.geojson"
)

HOTSPOTS_CSV = (
    MODELING_DIR
    / "urban_priority_hotspots.csv"
)

FINAL_PRIORITY_GPKG = (
    MODELING_DIR
    / "urban_ai_final_priority.gpkg"
)

OUTPUT_CSV = (
    MODELING_DIR
    / "priority_hotspots_validation.csv"
)

SOURCE_CRS = "EPSG:4326"
METRIC_CRS = "EPSG:32618"

EXPECTED_PRIORITY = 17_434
EXPECTED_HOTSPOTS = 224

TOLERANCE = 1e-6


# ============================================================
# UTILIDADES
# ============================================================

def check(condition, message, results):
    """
    Registra una validación.
    """
    status = bool(condition)

    results.append(
        {
            "check": message,
            "status": "OK" if status else "ERROR",
        }
    )

    print(
        f"[{'OK' if status else 'ERROR'}] {message}"
    )

    return status


def numeric_series(gdf, column):
    """
    Convierte una columna a numérica de forma segura.
    """
    return pd.to_numeric(
        gdf[column],
        errors="coerce"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 60)
    print("PRIORITY HOTSPOTS VALIDATION")
    print("Urban AI Bucaramanga")
    print("=" * 60)

    results = []

    # --------------------------------------------------------
    # 1. EXISTENCIA DE ARCHIVOS
    # --------------------------------------------------------

    print("\n=== ARCHIVOS ===")

    check(
        HOTSPOTS_GPKG.exists(),
        "GeoPackage existe",
        results,
    )

    check(
        HOTSPOTS_GEOJSON.exists(),
        "GeoJSON existe",
        results,
    )

    check(
        HOTSPOTS_CSV.exists(),
        "CSV existe",
        results,
    )

    # --------------------------------------------------------
    # 2. CARGA
    # --------------------------------------------------------

    print("\n=== CARGANDO HOTSPOTS ===")

    hotspots = gpd.read_file(HOTSPOTS_GPKG)

    print(
        f"Hotspots cargados: {len(hotspots):,}"
    )

    # --------------------------------------------------------
    # 3. VALIDACIÓN BÁSICA
    # --------------------------------------------------------

    print("\n=== ESTRUCTURA ===")

    required_columns = [
        "hotspot_rank",
        "observations",
        "mean_probability",
        "max_probability",
        "mean_ndvi",
        "mean_ndbi",
        "mean_lst",
        "area_ha",
        "priority_density",
        "hotspot_score",
        "longitude",
        "latitude",
        "geometry",
    ]

    missing_columns = [
        c
        for c in required_columns
        if c not in hotspots.columns
    ]

    check(
        len(missing_columns) == 0,
        "Todas las columnas requeridas existen",
        results,
    )

    if missing_columns:
        print(
            "Columnas faltantes:",
            missing_columns,
        )
        raise ValueError(
            "El GeoPackage no contiene todas "
            "las columnas requeridas."
        )

    # --------------------------------------------------------
    # 4. CANTIDAD DE HOTSPOTS
    # --------------------------------------------------------

    print("\n=== CANTIDAD ===")

    check(
        len(hotspots) == EXPECTED_HOTSPOTS,
        (
            f"Cantidad de hotspots: "
            f"{len(hotspots):,} "
            f"(esperados {EXPECTED_HOTSPOTS:,})"
        ),
        results,
    )

    # --------------------------------------------------------
    # 5. CRS
    # --------------------------------------------------------

    print("\n=== CRS ===")

    print(
        f"CRS: {hotspots.crs}"
    )

    check(
        hotspots.crs is not None,
        "CRS definido",
        results,
    )

    if hotspots.crs is not None:

        check(
            hotspots.crs.to_string() == SOURCE_CRS,
            f"CRS correcto: {SOURCE_CRS}",
            results,
        )

    # --------------------------------------------------------
    # 6. GEOMETRÍAS
    # --------------------------------------------------------

    print("\n=== GEOMETRÍAS ===")

    invalid = (~hotspots.geometry.is_valid).sum()
    empty = hotspots.geometry.is_empty.sum()
    null = hotspots.geometry.isna().sum()

    print(
        f"Geometrías inválidas: {invalid:,}"
    )

    print(
        f"Geometrías vacías:    {empty:,}"
    )

    print(
        f"Geometrías nulas:     {null:,}"
    )

    check(
        invalid == 0,
        "Todas las geometrías son válidas",
        results,
    )

    check(
        empty == 0,
        "Sin geometrías vacías",
        results,
    )

    check(
        null == 0,
        "Sin geometrías nulas",
        results,
    )

    # --------------------------------------------------------
    # 7. PROYECCIÓN MÉTRICA
    # --------------------------------------------------------

    print("\n=== PROYECCIÓN MÉTRICA ===")

    hotspots_metric = hotspots.to_crs(
        METRIC_CRS
    )

    print(
        f"CRS métrico: {METRIC_CRS}"
    )

    # --------------------------------------------------------
    # 8. ÁREAS
    # --------------------------------------------------------

    print("\n=== ÁREAS ===")

    calculated_area_ha = (
        hotspots_metric.geometry.area
        / 10_000.0
    )

    stored_area_ha = numeric_series(
        hotspots,
        "area_ha",
    )

    area_error = (
        calculated_area_ha
        - stored_area_ha
    ).abs()

    print(
        f"Área calculada total: "
        f"{calculated_area_ha.sum():,.2f} ha"
    )

    print(
        f"Área registrada total: "
        f"{stored_area_ha.sum():,.2f} ha"
    )

    print(
        f"Error máximo de área: "
        f"{area_error.max():.8f} ha"
    )

    check(
        area_error.max() < 0.01,
        "Áreas registradas coinciden con geometrías",
        results,
    )

    check(
        (stored_area_ha > 0).all(),
        "Todas las áreas son mayores que cero",
        results,
    )

    # --------------------------------------------------------
    # 9. DENSIDAD
    # --------------------------------------------------------

    print("\n=== DENSIDAD ===")

    observations = numeric_series(
        hotspots,
        "observations",
    )

    density = numeric_series(
        hotspots,
        "priority_density",
    )

    calculated_density = (
        observations
        / stored_area_ha
    )

    density_error = (
        calculated_density
        - density
    ).abs()

    print(
        f"Densidad mínima: "
        f"{density.min():.6f}"
    )

    print(
        f"Densidad máxima: "
        f"{density.max():.6f}"
    )

    print(
        f"Error máximo: "
        f"{density_error.max():.8f}"
    )

    check(
        density_error.max() < 1e-5,
        "Densidad coincide con observaciones / área",
        results,
    )

    check(
        (density > 0).all(),
        "Todas las densidades son mayores que cero",
        results,
    )

    # --------------------------------------------------------
    # 10. OBSERVACIONES
    # --------------------------------------------------------

    print("\n=== OBSERVACIONES ===")

    total_observations = int(
        observations.sum()
    )

    print(
        f"Observaciones agrupadas: "
        f"{total_observations:,}"
    )

    print(
        f"Esperadas: "
        f"{EXPECTED_PRIORITY:,}"
    )

    check(
        total_observations == EXPECTED_PRIORITY,
        (
            "Todas las observaciones prioritarias "
            "están agrupadas"
        ),
        results,
    )

    check(
        (observations > 0).all(),
        "Todos los hotspots tienen observaciones",
        results,
    )

    # --------------------------------------------------------
    # 11. RANKING
    # --------------------------------------------------------

    print("\n=== RANKING ===")

    ranks = numeric_series(
        hotspots,
        "hotspot_rank",
    ).astype(int)

    expected_ranks = set(
        range(
            1,
            len(hotspots) + 1,
        )
    )

    actual_ranks = set(ranks)

    check(
        actual_ranks == expected_ranks,
        "Ranking completo y sin duplicados",
        results,
    )

    check(
        ranks.is_unique,
        "Ranking único",
        results,
    )

    # --------------------------------------------------------
    # 12. SCORES
    # --------------------------------------------------------

    print("\n=== SCORES ===")

    score = numeric_series(
        hotspots,
        "hotspot_score",
    )

    probability = numeric_series(
        hotspots,
        "mean_probability",
    )

    max_probability = numeric_series(
        hotspots,
        "max_probability",
    )

    print(
        f"Hotspot score mínimo: "
        f"{score.min():.6f}"
    )

    print(
        f"Hotspot score máximo: "
        f"{score.max():.6f}"
    )

    check(
        score.between(
            0,
            1,
            inclusive="both",
        ).all(),
        "Hotspot score entre 0 y 1",
        results,
    )

    check(
        probability.between(
            0,
            1,
            inclusive="both",
        ).all(),
        "Mean probability entre 0 y 1",
        results,
    )

    check(
        max_probability.between(
            0,
            1,
            inclusive="both",
        ).all(),
        "Max probability entre 0 y 1",
        results,
    )

    check(
        (max_probability >= probability).all(),
        "Max probability >= mean probability",
        results,
    )

    # --------------------------------------------------------
    # 13. COORDENADAS
    # --------------------------------------------------------

    print("\n=== COORDENADAS ===")

    longitude = numeric_series(
        hotspots,
        "longitude",
    )

    latitude = numeric_series(
        hotspots,
        "latitude",
    )

    check(
        longitude.notna().all(),
        "Longitudes sin valores nulos",
        results,
    )

    check(
        latitude.notna().all(),
        "Latitudes sin valores nulos",
        results,
    )

    # Centroides métricos -> WGS84
    centroids_wgs84 = (
        hotspots_metric
        .geometry
        .centroid
        .to_crs(SOURCE_CRS)
    )

    centroid_lon = centroids_wgs84.x
    centroid_lat = centroids_wgs84.y

    longitude_error = (
        longitude
        - centroid_lon
    ).abs()

    latitude_error = (
        latitude
        - centroid_lat
    ).abs()

    print(
        f"Error máximo longitud: "
        f"{longitude_error.max():.8f}"
    )

    print(
        f"Error máximo latitud: "
        f"{latitude_error.max():.8f}"
    )

    check(
        longitude_error.max() < 0.001,
        "Longitudes consistentes con centroides",
        results,
    )

    check(
        latitude_error.max() < 0.001,
        "Latitudes consistentes con centroides",
        results,
    )

     # --------------------------------------------------------
    # 14. SOLAPAMIENTOS REALES
    # --------------------------------------------------------

    print("\n=== SOLAPAMIENTOS REALES ===")

    real_overlap_count = 0
    touching_count = 0

    try:

        spatial_index = hotspots_metric.sindex

        checked_pairs = set()

        for idx, geom in enumerate(
            hotspots_metric.geometry
        ):

            candidates = spatial_index.query(
                geom,
                predicate="intersects",
            )

            for candidate in candidates:

                candidate = int(candidate)

                if candidate == idx:
                    continue

                pair = tuple(
                    sorted(
                        (
                            idx,
                            candidate,
                        )
                    )
                )

                if pair in checked_pairs:
                    continue

                checked_pairs.add(pair)

                other_geom = (
                    hotspots_metric
                    .geometry
                    .iloc[candidate]
                )

                intersection = geom.intersection(
                    other_geom
                )

                # Área de intersección en m²
                intersection_area = (
                    intersection.area
                )

                if intersection_area > 1e-6:

                    real_overlap_count += 1

                else:

                    # Las geometrías se tocan,
                    # pero no comparten superficie.
                    if geom.touches(other_geom):
                        touching_count += 1

        print(
            f"Solapamientos reales: "
            f"{real_overlap_count:,}"
        )

        print(
            f"Contactos entre celdas: "
            f"{touching_count:,}"
        )

    except Exception as exc:

        print(
            "No fue posible realizar "
            f"la prueba espacial: {exc}"
        )

        real_overlap_count = -1

    check(
        real_overlap_count == 0,
        "Sin solapamientos reales entre hotspots",
        results,
    )

    # --------------------------------------------------------
    # 15. CONSISTENCIA DEL CSV
    # --------------------------------------------------------

    print("\n=== CONSISTENCIA CSV ===")

    csv = pd.read_csv(
        HOTSPOTS_CSV
    )

    print(
        f"Hotspots CSV: "
        f"{len(csv):,}"
    )

    check(
        len(csv) == len(hotspots),
        "CSV y GeoPackage tienen la misma cantidad",
        results,
    )

    csv_required = [
        "hotspot_rank",
        "observations",
        "mean_probability",
        "max_probability",
        "mean_ndvi",
        "mean_ndbi",
        "mean_lst",
        "area_ha",
        "priority_density",
        "hotspot_score",
    ]

    csv_missing = [
        c
        for c in csv_required
        if c not in csv.columns
    ]

    check(
        len(csv_missing) == 0,
        "CSV contiene las variables principales",
        results,
    )

    if len(csv_missing) == 0:

        gpkg_rank = (
            hotspots
            .sort_values("hotspot_rank")
            .reset_index(drop=True)
        )

        csv_rank = (
            csv
            .sort_values("hotspot_rank")
            .reset_index(drop=True)
        )

        comparison_columns = [
            "hotspot_rank",
            "observations",
            "mean_probability",
            "max_probability",
            "mean_ndvi",
            "mean_ndbi",
            "mean_lst",
            "area_ha",
            "priority_density",
            "hotspot_score",
        ]

        csv_match = True

        for column in comparison_columns:

            a = pd.to_numeric(
                gpkg_rank[column],
                errors="coerce",
            )

            b = pd.to_numeric(
                csv_rank[column],
                errors="coerce",
            )

            if not np.allclose(
                a,
                b,
                equal_nan=True,
                atol=1e-6,
            ):
                csv_match = False
                break

        check(
            csv_match,
            "Variables CSV y GeoPackage coinciden",
            results,
        )

    # --------------------------------------------------------
    # 16. GEOJSON
    # --------------------------------------------------------

    print("\n=== CONSISTENCIA GEOJSON ===")

    geojson = gpd.read_file(
        HOTSPOTS_GEOJSON
    )

    print(
        f"Hotspots GeoJSON: "
        f"{len(geojson):,}"
    )

    check(
        len(geojson) == len(hotspots),
        "GeoJSON y GeoPackage tienen la misma cantidad",
        results,
    )

    check(
        geojson.crs is not None,
        "GeoJSON tiene CRS definido",
        results,
    )

    # --------------------------------------------------------
    # 17. CONSISTENCIA CON CAPA FINAL
    # --------------------------------------------------------

    print("\n=== CONSISTENCIA CON CAPA FINAL ===")

    if FINAL_PRIORITY_GPKG.exists():

        final_layer = gpd.read_file(
            FINAL_PRIORITY_GPKG
        )

        final_priority_count = int(
            final_layer[
                "final_priority"
            ]
            .isin(
                [
                    "MUY_ALTA",
                    "ALTA",
                ]
            )
            .sum()
        )

        print(
            f"Observaciones prioritarias "
            f"capa final: "
            f"{final_priority_count:,}"
        )

        check(
            final_priority_count
            == EXPECTED_PRIORITY,
            (
                "Hotspots coinciden con "
                "la cantidad prioritaria final"
            ),
            results,
        )

    else:

        print(
            "Capa final no encontrada. "
            "Se omite esta validación."
        )

    # --------------------------------------------------------
    # 18. RESUMEN
    # --------------------------------------------------------

    print("\n" + "=" * 60)
    print("RESUMEN DE VALIDACIÓN")
    print("=" * 60)

    total_checks = len(results)

    passed = sum(
        r["status"] == "OK"
        for r in results
    )

    failed = total_checks - passed

    print(
        f"Validaciones: {total_checks}"
    )

    print(
        f"Correctas:    {passed}"
    )

    print(
        f"Errores:      {failed}"
    )

    # --------------------------------------------------------
    # 19. GUARDAR RESULTADOS
    # --------------------------------------------------------

    validation_df = pd.DataFrame(
        results
    )

    OUTPUT_CSV.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    validation_df.to_csv(
        OUTPUT_CSV,
        index=False,
        encoding="utf-8",
    )

    print(
        "\nResultado guardado en:"
    )

    print(
        OUTPUT_CSV
    )

    # --------------------------------------------------------
    # 20. RESULTADO FINAL
    # --------------------------------------------------------

    print("\n" + "=" * 60)

    if failed == 0:

        print(
            "HOTSPOTS VALIDADOS CORRECTAMENTE"
        )

        print(
            "La capa está lista para "
            "el siguiente análisis."
        )

    else:

        print(
            "VALIDACIÓN CON ERRORES"
        )

        print(
            "Revisar las validaciones "
            "marcadas como ERROR."
        )

    print("=" * 60)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()