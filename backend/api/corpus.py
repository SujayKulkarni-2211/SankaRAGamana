from fastapi import APIRouter, Depends

from backend.auth.admin import require_admin

router = APIRouter()


@router.get("/api/admin/corpus")
async def get_corpus(_admin=Depends(require_admin)):
    # TODO: implement in Step 4
    # Returns corpus_tracker rows from Supabase
    pass
