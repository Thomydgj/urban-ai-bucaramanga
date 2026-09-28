import ee


PROJECT_ID = "urban-ai-bucaramanga"


def initialize_earth_engine() -> None:
    """Initialize the Google Earth Engine client."""
    ee.Initialize(project=PROJECT_ID)


if __name__ == "__main__":
    initialize_earth_engine()
    print("Earth Engine connection successful.")