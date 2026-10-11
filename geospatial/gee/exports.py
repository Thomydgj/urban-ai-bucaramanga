import ee


def export_image_to_drive(
    image: ee.Image,
    description: str,
    folder: str,
    region: ee.Geometry,
    scale: int = 10,
) -> ee.batch.Task:
    """Export an Earth Engine image to Google Drive."""

    task = ee.batch.Export.image.toDrive(
        image=image,
        description=description,
        folder=folder,
        region=region,
        scale=scale,
        maxPixels=1e10,
        fileFormat="GeoTIFF",
    )

    task.start()

    return task

def export_lst(
    lst: ee.Image,
    region: ee.Geometry,
) -> ee.batch.Task:
    """
    Export the LST composite to Google Drive as GeoTIFF.
    """

    task = ee.batch.Export.image.toDrive(
        image=lst,
        description="urban_ai_bucaramanga_lst",
        folder="urban_ai_bucaramanga",
        fileNamePrefix="urban_ai_bucaramanga_lst",
        region=region,
        scale=30,
        maxPixels=1e10,
        fileFormat="GeoTIFF",
    )

    task.start()

    return task

def export_ndvi(
    ndvi: ee.Image,
    region: ee.Geometry,
) -> ee.batch.Task:
    """Export the NDVI composite to Google Drive as GeoTIFF."""

    task = ee.batch.Export.image.toDrive(
        image=ndvi,
        description="urban_ai_bucaramanga_ndvi",
        folder="urban_ai_bucaramanga",
        fileNamePrefix="urban_ai_bucaramanga_ndvi",
        region=region,
        scale=10,
        maxPixels=1e10,
        fileFormat="GeoTIFF",
    )

    task.start()

    return task


def export_ndbi(
    ndbi: ee.Image,
    region: ee.Geometry,
) -> ee.batch.Task:
    """Export the NDBI composite to Google Drive as GeoTIFF."""

    task = ee.batch.Export.image.toDrive(
        image=ndbi,
        description="urban_ai_bucaramanga_ndbi",
        folder="urban_ai_bucaramanga",
        fileNamePrefix="urban_ai_bucaramanga_ndbi",
        region=region,
        scale=10,
        maxPixels=1e10,
        fileFormat="GeoTIFF",
    )

    task.start()

    return task