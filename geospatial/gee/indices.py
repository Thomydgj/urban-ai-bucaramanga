import ee


def calculate_ndvi(image: ee.Image) -> ee.Image:
    """Calculate NDVI from Sentinel-2."""
    return image.normalizedDifference(
        ["B8", "B4"]
    ).rename("NDVI")


def calculate_ndbi(image: ee.Image) -> ee.Image:
    """Calculate NDBI from Sentinel-2."""
    return image.normalizedDifference(
        ["B11", "B8"]
    ).rename("NDBI")