from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from backend.db.session import get_db
from backend.api.deps import get_current_user
from backend.db import crud
from backend.services.vision_wall import analyze_wall_image
from backend.services.vision_wine import identify_wine
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, Form

router = APIRouter(prefix="/vision", tags=["vision"])

@router.post("/wall/analyze")
async def wall_analyze(
    cellar_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    role = crud.get_user_role_in_cellar(db, cellar_id, str(user.user_id))

    if role not in ("OWNER", "ADMIN"):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return analyze_wall_image(await file.read())


@router.post("/wine/identify")
async def wine_identify(
    cellar_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    role = crud.get_user_role_in_cellar(db, cellar_id, str(user.user_id))

    if role not in ("OWNER", "ADMIN"):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return identify_wine(await file.read())