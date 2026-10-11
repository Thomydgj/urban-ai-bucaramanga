from fastapi import APIRouter

from ..data import load_master_layer


router = APIRouter(
    prefix="/api",
    tags=["Health"],
)


@router.get("/health")
def health():

    try:

        gdf = load_master_layer()

        return {
            "status": "healthy",
            "dataset": "urban_ai_master_intervention",
            "zones": len(gdf),
            "crs": str(gdf.crs),
        }

    except Exception as exc:

        return {
            "status": "error",
            "message": str(exc),
        }