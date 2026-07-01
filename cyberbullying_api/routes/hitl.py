"""Human-in-the-loop endpoints — categorized data, reallocate, bulk reallocate."""

import logging

from fastapi import APIRouter, HTTPException, Security
from models import BulkReallocateRequest, ReallocateRequest, ReallocateResponse
from routes.deps import get_current_user

logger = logging.getLogger("bullyguard")

router = APIRouter(prefix="/api", tags=["admin"], dependencies=[Security(get_current_user, scopes=["admin"])])


@router.get("/data/categorized")
async def api_get_categorized_data(
    limit: int = 500,
    offset: int = 0,
    confidence_min: float | None = None,
    confidence_max: float | None = None,
    decision_source: str | None = None,
    search: str | None = None
):
    try:
        from classifier import get_categorized_memory
        data = await get_categorized_memory(
            limit=limit,
            offset=offset,
            confidence_min=confidence_min,
            confidence_max=confidence_max,
            decision_source=decision_source,
            search=search
        )
        # Tambah metadata pagination
        total_per_quadrant = {k: len(v) for k, v in data.items()}
        total_all = sum(total_per_quadrant.values())
        return {
            **data,
            "_pagination": {
                "limit": limit,
                "offset": offset,
                "total_fetched": total_all,
                "per_quadrant": total_per_quadrant,
                "has_more": any(len(v) >= limit for v in data.values())
            }
        }
    except Exception as e:
        logger.error("Error fetching memory data", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Gagal mengambil memori data klasifikasi dari basis data.")


@router.post("/data/reallocate", response_model=ReallocateResponse)
async def api_reallocate_data(req: ReallocateRequest):
    try:
        from classifier import update_validation_status
        success = await update_validation_status(req.text, req.new_is_toxic, req.new_is_bully, is_validated=1)
        if success:
            return ReallocateResponse(success=True, message="Data berhasil direlokasi dan divalidasi.")
        else:
            return ReallocateResponse(success=False, message="Gagal merekam relokasi data ke basis data.")
    except Exception as e:
        logger.error("Error reallocating data", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Gagal memperbarui alokasi kategori data di database.")


@router.post("/data/reallocate/bulk", response_model=ReallocateResponse)
async def api_reallocate_data_bulk(req: BulkReallocateRequest):
    try:
        from classifier import update_validation_status
        success_count = 0
        for item in req.items:
            success = await update_validation_status(item.text, item.new_is_toxic, item.new_is_bully, is_validated=1)
            if success:
                success_count += 1

        if success_count == len(req.items):
            return ReallocateResponse(success=True, message=f"Semua ({success_count}) data berhasil direlokasi dan divalidasi.")
        elif success_count > 0:
            return ReallocateResponse(success=True, message=f"Sebagian ({success_count}/{len(req.items)}) data berhasil direlokasi dan divalidasi.")
        else:
            return ReallocateResponse(success=False, message="Gagal merekam relokasi data massal ke basis data.")
    except Exception as e:
        logger.error("Error bulk reallocating data", extra={"error": str(e)})
        raise HTTPException(status_code=500, detail="Gagal memperbarui alokasi kategori data massal di database.")
