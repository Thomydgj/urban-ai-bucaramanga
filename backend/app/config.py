from pathlib import Path


# Raíz del proyecto
BASE_DIR = Path(__file__).resolve().parents[2]

# Datos procesados por el motor geoespacial
DATA_DIR = BASE_DIR / "data" / "processed" / "modeling"

# Capa maestra validada
MASTER_GPKG = DATA_DIR / "urban_ai_master_intervention.gpkg"

# Nombre real de la capa dentro del GeoPackage
MASTER_LAYER = "master_intervention"