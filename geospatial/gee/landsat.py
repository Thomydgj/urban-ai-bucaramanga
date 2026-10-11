import ee


LANDSAT_START_DATE = "2026-01-01"
LANDSAT_END_DATE = "2026-09-01"


def get_landsat_collection(
    region: ee.Geometry,
) -> ee.ImageCollection:
    """
    Return Landsat 8 and Landsat 9 Collection 2 Tier 1
    Level 2 imagery with Surface Temperature.
    """

    landsat8 = (
        ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
        .filterBounds(region)
        .filterDate(
            LANDSAT_START_DATE,
            LANDSAT_END_DATE,
        )
        .filter(
            ee.Filter.eq(
                "PROCESSING_LEVEL",
                "L2SP",
            )
        )
    )

    landsat9 = (
        ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")
        .filterBounds(region)
        .filterDate(
            LANDSAT_START_DATE,
            LANDSAT_END_DATE,
        )
        .filter(
            ee.Filter.eq(
                "PROCESSING_LEVEL",
                "L2SP",
            )
        )
    )

    return landsat8.merge(landsat9)


def mask_landsat_lst(image: ee.Image) -> ee.Image:
    """
    Mask invalid, cloudy, shadowed and saturated pixels
    for Landsat Surface Temperature.
    """

    qa_pixel = image.select("QA_PIXEL")
    qa_radsat = image.select("QA_RADSAT")
    st_b10 = image.select("ST_B10")

    # QA_PIXEL bit 0 = Fill
    fill = qa_pixel.bitwiseAnd(1 << 0).eq(0)

    # QA_PIXEL bit 1 = Dilated cloud
    dilated_cloud = qa_pixel.bitwiseAnd(1 << 1).eq(0)

    # QA_PIXEL bit 2 = Cirrus
    cirrus = qa_pixel.bitwiseAnd(1 << 2).eq(0)

    # QA_PIXEL bit 3 = Cloud
    cloud = qa_pixel.bitwiseAnd(1 << 3).eq(0)

    # QA_PIXEL bit 4 = Cloud shadow
    cloud_shadow = qa_pixel.bitwiseAnd(1 << 4).eq(0)

    # QA_PIXEL bit 5 = Snow
    snow = qa_pixel.bitwiseAnd(1 << 5).eq(0)

    # QA_RADSAT bit 11 = terrain occlusion
    terrain_occlusion = qa_radsat.bitwiseAnd(1 << 11).eq(0)

    # ST_B10 must contain valid data
    valid_temperature = st_b10.gt(0)

    mask = (
        fill
        .And(dilated_cloud)
        .And(cirrus)
        .And(cloud)
        .And(cloud_shadow)
        .And(snow)
        .And(terrain_occlusion)
        .And(valid_temperature)
    )

    return image.updateMask(mask)

def calculate_lst(image: ee.Image) -> ee.Image:
    """
    Convert Landsat ST_B10 to Land Surface Temperature in Celsius
    and remove physically invalid temperature values.
    """

    image = mask_landsat_lst(image)

    lst_kelvin = (
        image
        .select("ST_B10")
        .multiply(0.00341802)
        .add(149.0)
    )

    lst_celsius = (
        lst_kelvin
        .subtract(273.15)
        .rename("LST")
    )

    # Physical quality-control range.
    valid_temperature = (
        lst_celsius.gt(-20)
        .And(lst_celsius.lt(80))
    )

    return (
        lst_celsius
        .updateMask(valid_temperature)
        .copyProperties(
            image,
            image.propertyNames(),
        )
    )

def build_lst_composite(
    collection: ee.ImageCollection,
    region: ee.Geometry,
) -> ee.Image:
    """
    Build a temporal median LST composite.
    """

    lst_collection = collection.map(calculate_lst)

    return lst_collection.median().clip(region)