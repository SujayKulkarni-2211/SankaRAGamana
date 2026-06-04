from fastapi import APIRouter, UploadFile, File, Depends

from backend.auth.admin import require_admin

router = APIRouter()


@router.post("/api/admin/upload")
async def upload(
    file: UploadFile = File(...),
    _admin=Depends(require_admin),
):
    # TODO: implement in Step 4
    # Accepts: .txt, .itx, .pdf, .json
    # Pipeline: clean → chunk → embed → Supabase
    pass
