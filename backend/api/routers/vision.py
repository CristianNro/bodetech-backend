from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, Form
from sqlalchemy.orm import Session

from backend.db.session import get_db
from backend.api.deps import get_current_user
from backend.db import crud
from backend.services.vision_wall import save_cellar_image, generate_fake_slots
from backend.services.vision_wine import identify_wine
from pathlib import Path
from fastapi.responses import FileResponse

router = APIRouter(prefix="/vision", tags=["vision"])


@router.post("/wall/analyze")
async def wall_analyze(
    cellar_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    
    print("Received file:", file.filename, "for cellar:", cellar_id, "from user:", user.email)
    role = crud.get_user_role_in_cellar(db, cellar_id, str(user.user_id))

    if role not in ("OWNER", "ADMIN"):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    image_bytes = await file.read()
    if not image_bytes:
        raise HTTPException(status_code=400, detail="Empty image")

    saved = save_cellar_image(
        image_bytes=image_bytes,
        cellar_id=cellar_id,
        original_filename=file.filename,
    )

    image = crud.create_cellar_image(
        db=db,
        cellar_id=cellar_id,
        uploaded_by=str(user.user_id),
        original_filename=file.filename,
        image_path=saved["image_path"],
        image_url=saved["image_url"],
        width=saved["width"],
        height=saved["height"],
        status="pending",
    )

    crud.mark_old_slots_inactive(db, cellar_id)

    fake_slots = generate_fake_slots(
        width=saved["width"],
        height=saved["height"],
        rows=3,
        cols=4,
    )

    created_slots = []
    for slot in fake_slots:
        created = crud.create_cellar_slot(
            db=db,
            cellar_id=cellar_id,
            image_id=image["image_id"],
            slot_index=slot["slot_index"],
            label=slot.get("label"),
            polygon_json=slot["polygon"],
            bbox_json=slot["bbox"],
            center_x=slot.get("center_x"),
            center_y=slot.get("center_y"),
            status=slot.get("status", "unknown"),
            confidence=slot.get("confidence"),
            is_active=True,
            is_user_corrected=slot.get("is_user_corrected", False),
        )
        created_slots.append(created)

    db.commit()

    crud.update_cellar_image_status(db, image["image_id"], "processed")

    return {
        "image_id": image["image_id"],
        "status": "processed",
        "image_path": image["image_path"],
        "width": image["width"],
        "height": image["height"],
        "slots_detected": len(created_slots),
        "slots": [
            {
                "slot_id": slot["slot_id"],
                "slot_index": slot["slot_index"],
                "label": slot["label"],
                "polygon": slot["polygon_json"],
                "bbox": slot["bbox_json"],
                "center_x": slot["center_x"],
                "center_y": slot["center_y"],
                "status": slot["status"],
                "confidence": slot["confidence"],
                "is_active": slot["is_active"],
                "is_user_corrected": slot["is_user_corrected"],
            }
            for slot in created_slots
        ],
    }


@router.get("/wall/{cellar_id}/slots")
def get_wall_slots(
    cellar_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    role = crud.get_user_role_in_cellar(db, cellar_id, str(user.user_id))

    if role not in ("OWNER", "ADMIN"):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    slots = crud.get_active_slots_by_cellar(db, cellar_id)

    return {
        "slots": [
            {
                "slot_id": slot["slot_id"],
                "image_id": slot["image_id"],
                "slot_index": slot["slot_index"],
                "label": slot["label"],
                "polygon": slot["polygon_json"],
                "bbox": slot["bbox_json"],
                "center_x": slot["center_x"],
                "center_y": slot["center_y"],
                "status": slot["status"],
                "confidence": slot["confidence"],
                "is_active": slot["is_active"],
                "is_user_corrected": slot["is_user_corrected"],
            }
            for slot in slots
        ]
    }


@router.patch("/wall/slots/{slot_id}")
def update_wall_slot(
    slot_id: str,
    polygon: str | None = Form(None),
    bbox: str | None = Form(None),
    label: str | None = Form(None),
    status: str | None = Form(None),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    import json

    slot = crud.get_slot_by_id(db, slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    role = crud.get_user_role_in_cellar(db, slot["cellar_id"], str(user.user_id))
    if role not in ("OWNER", "ADMIN"):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    parsed_polygon = None
    parsed_bbox = None

    try:
        if polygon is not None:
            parsed_polygon = json.loads(polygon)

        if bbox is not None:
            parsed_bbox = json.loads(bbox)
    except Exception:
        raise HTTPException(status_code=400, detail="polygon or bbox is not valid JSON")

    updated = crud.update_slot_geometry(
        db=db,
        slot_id=slot_id,
        polygon_json=parsed_polygon,
        bbox_json=parsed_bbox,
        label=label,
        status=status,
    )

    if not updated:
        raise HTTPException(status_code=404, detail="Slot not found")

    return {
        "slot_id": updated["slot_id"],
        "image_id": updated["image_id"],
        "slot_index": updated["slot_index"],
        "label": updated["label"],
        "polygon": updated["polygon_json"],
        "bbox": updated["bbox_json"],
        "center_x": updated["center_x"],
        "center_y": updated["center_y"],
        "status": updated["status"],
        "confidence": updated["confidence"],
        "is_active": updated["is_active"],
        "is_user_corrected": updated["is_user_corrected"],
    }


@router.post("/wine/identify")
async def wine_identify(
    cellar_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    role = crud.get_user_role_in_cellar(db, cellar_id, str(user.user_id))

    if role not in ("OWNER", "ADMIN"):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    return identify_wine(await file.read())


@router.get("/wall/{cellar_id}/latest")
def get_latest_wall_analysis(cellar_id: str,db: Session = Depends(get_db),
                            user=Depends(get_current_user),):
    role = crud.get_user_role_in_cellar(db, cellar_id, str(user.user_id))

    if role not in ("OWNER", "ADMIN"):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    image = crud.get_latest_cellar_image(db, cellar_id)
    if not image:
        return {
            "image": None,
            "slots": [],
        }

    slots = crud.get_active_slots_by_cellar(db, cellar_id)

    print(f"imange_url: {image['image_url']}")

    return {
        "image": image,
        "slots": [
            {
                "slot_id": slot["slot_id"],
                "image_id": slot["image_id"],
                "slot_index": slot["slot_index"],
                "label": slot["label"],
                "polygon": slot["polygon_json"],
                "bbox": slot["bbox_json"],
                "center_x": slot["center_x"],
                "center_y": slot["center_y"],
                "status": slot["status"],
                "confidence": slot["confidence"],
                "is_active": slot["is_active"],
                "is_user_corrected": slot["is_user_corrected"],
            }
            for slot in slots
        ],
    }

@router.get("/wall/image/{cellar_id}/{filename}")
def get_wall_image(cellar_id: str,filename: str):

    file_path = Path("uploads") / "cellars" / cellar_id / filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(file_path)