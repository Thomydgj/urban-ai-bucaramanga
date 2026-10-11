import time

import ee

from geospatial.gee.indices import calculate_ndbi, calculate_ndvi


PROJECT_ID = "urban-ai-bucaramanga"

START_DATE = "2026-01-01"
END_DATE = "2026-09-01"

MAX_CLOUD_PROBABILITY = 40


def initialize_earth_engine() -> None:
    """Initialize Google Earth Engine."""
    ee.Initialize(project=PROJECT_ID)


def get_bucaramanga_boundary() -> ee.Geometry:
    """Return the GAUL administrative boundary for Bucaramanga."""

    gaul = ee.FeatureCollection("FAO/GAUL/2025/level2")

    municipality = gaul.filter(
        ee.Filter.And(
            ee.Filter.eq("GAUL0_NAME", "Colombia"),
            ee.Filter.eq("GAUL1_NAME", "Santander"),
            ee.Filter.eq("GAUL2_NAME", "Bucaramanga"),
        )
    )

    return municipality.geometry()


def get_sentinel2_collection(
    region: ee.Geometry,
) -> ee.ImageCollection:
    """Return cloud-filtered Sentinel-2 SR imagery."""

    sentinel = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(region)
        .filterDate(START_DATE, END_DATE)
    )

    cloud_probability = (
        ee.ImageCollection("COPERNICUS/S2_CLOUD_PROBABILITY")
        .filterBounds(region)
        .filterDate(START_DATE, END_DATE)
    )

    joined = ee.Join.saveFirst("cloud_mask").apply(
        primary=sentinel,
        secondary=cloud_probability,
        condition=ee.Filter.equals(
            leftField="system:index",
            rightField="system:index",
        ),
    )

    def mask_clouds(image):
        cloud_mask = (
            ee.Image(image.get("cloud_mask"))
            .select("probability")
        )

        return image.updateMask(
            cloud_mask.lt(MAX_CLOUD_PROBABILITY)
        )

    return ee.ImageCollection(joined).map(mask_clouds)


def build_ndvi_composite(
    collection: ee.ImageCollection,
    region: ee.Geometry,
) -> ee.Image:
    """Build temporal NDVI composite."""

    ndvi_collection = collection.map(calculate_ndvi)

    return ndvi_collection.median().clip(region)


def build_ndbi_composite(
    collection: ee.ImageCollection,
    region: ee.Geometry,
) -> ee.Image:
    """Build temporal NDBI composite."""

    ndbi_collection = collection.map(calculate_ndbi)

    return ndbi_collection.median().clip(region)


def main() -> None:
    start = time.perf_counter()

    initialize_earth_engine()

    print(
        f"Inicialización: "
        f"{time.perf_counter() - start:.2f}s"
    )

    region = get_bucaramanga_boundary()

    collection = get_sentinel2_collection(region)

    image_count = collection.size().getInfo()

    print(
        f"Consulta de imágenes: "
        f"{time.perf_counter() - start:.2f}s"
    )

    print(
        f"Imágenes disponibles después del filtrado: "
        f"{image_count}"
    )

    ndvi = build_ndvi_composite(collection, region)
    ndbi = build_ndbi_composite(collection, region)

    print("NDVI y NDBI construidos correctamente.")

    ndbi_sample = ndbi.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=100,
        maxPixels=1e8,
    ).getInfo()

    print("\n=== NDBI BUCARAMANGA ===")
    print(
        f"NDBI medio aproximado: "
        f"{ndbi_sample.get('NDBI')}"
    )

    print(
        f"Construcción de índices: "
        f"{time.perf_counter() - start:.2f}s"
    )

    statistics = ndvi.reduceRegion(
        reducer=ee.Reducer.mean().combine(
            reducer2=ee.Reducer.minMax(),
            sharedInputs=True,
        ),
        geometry=region,
        scale=10,
        maxPixels=1e9,
    ).getInfo()

    print(
        f"Estadísticas NDVI: "
        f"{time.perf_counter() - start:.2f}s"
    )

    print("\n=== NDVI BUCARAMANGA ===")
    print(f"NDVI medio: {statistics.get('NDVI_mean')}")
    print(f"NDVI mínimo: {statistics.get('NDVI_min')}")
    print(f"NDVI máximo: {statistics.get('NDVI_max')}")


if __name__ == "__main__":
    main()