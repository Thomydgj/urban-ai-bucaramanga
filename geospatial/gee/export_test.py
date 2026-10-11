import ee

from geospatial.gee.exports import (
    export_lst,
    export_ndbi,
    export_ndvi,
)

from geospatial.gee.landsat import (
    build_lst_composite,
    get_landsat_collection,
)

from geospatial.gee.sentinel2 import (
    build_ndbi_composite,
    build_ndvi_composite,
    get_bucaramanga_boundary,
    get_sentinel2_collection,
    initialize_earth_engine,
)


def main() -> None:

    initialize_earth_engine()

    region = get_bucaramanga_boundary()

    # =========================
    # SENTINEL-2
    # =========================

    sentinel_collection = get_sentinel2_collection(region)

    ndvi = build_ndvi_composite(
        sentinel_collection,
        region,
    )

    ndbi = build_ndbi_composite(
        sentinel_collection,
        region,
    )

    # =========================
    # LANDSAT
    # =========================

    landsat_collection = get_landsat_collection(
        region
    )

    lst = build_lst_composite(
        landsat_collection,
        region,
    )

    # =========================
    # EXPORTS
    # =========================

    ndvi_task = export_ndvi(
        ndvi,
        region,
    )

    ndbi_task = export_ndbi(
        ndbi,
        region,
    )

    lst_task = export_lst(
        lst,
        region,
    )

    print("\n=== EXPORTACIONES CREADAS ===")

    print(
        f"NDVI: {ndvi_task.id}"
    )

    print(
        f"NDBI: {ndbi_task.id}"
    )

    print(
        f"LST: {lst_task.id}"
    )


if __name__ == "__main__":
    main()