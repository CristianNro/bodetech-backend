from pathlib import Path
import logging
import json
import os

from fastapi import APIRouter, File, UploadFile, Depends, HTTPException, Form, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.api.deps import get_current_user
from backend.db import crud
from backend.db.session import get_db
from backend.services.vision_wall import save_cellar_image, generate_fake_slots
from backend.services.vision_wine import identify_wine
from backend.schemas.vision_slots import SaveSlotsBatchRequest
from backend.services.slot_geometry import (
    bbox_center,
    bbox_to_polygon,
    normalize_slot_indexes,
    validate_slots_batch,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vision", tags=["vision"])


def serialize_slot(slot: dict):
    return {
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


def ensure_cellar_access(db: Session, cellar_id: str, user_id: str):
    role = crud.get_user_role_in_cellar(db, cellar_id, user_id)
    if role not in ("OWNER", "ADMIN"):
        raise HTTPException(status_code=403, detail="Not enough permissions")


@router.post("/wall/analyze")
async def wall_analyze(
    cellar_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    ensure_cellar_access(db, cellar_id, str(user.user_id))

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
        commit=False,
    )

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
            commit=False,
        )
        created_slots.append(created)

    crud.update_cellar_image_status(db, image["image_id"], "processed", commit=False)
    db.commit()

    logger.info(
        "Wall analyzed successfully",
        extra={
            "cellar_id": cellar_id,
            "image_id": image["image_id"],
            "slots_detected": len(created_slots),
        },
    )

    return {
        "image_id": image["image_id"],
        "status": "processed",
        "image_path": image["image_path"],
        "image_url": image["image_url"],
        "width": image["width"],
        "height": image["height"],
        "slots_detected": len(created_slots),
        "slots": [serialize_slot(slot) for slot in created_slots],
    }


@router.get("/wall/{cellar_id}/images")
def list_wall_images(
    cellar_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    ensure_cellar_access(db, cellar_id, str(user.user_id))

    images = crud.list_cellar_images(db, cellar_id)

    return {
        "items": images
    }


@router.get("/wall/{cellar_id}/images/{image_id}")
def get_wall_image_analysis(
    cellar_id: str,
    image_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    ensure_cellar_access(db, cellar_id, str(user.user_id))

    image = crud.get_cellar_image_in_cellar(db, cellar_id, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    slots = crud.get_slots_by_image_id(db, image_id)

    return {
        "image": image,
        "slots": [serialize_slot(slot) for slot in slots],
    }


@router.delete("/wall/{cellar_id}/images/{image_id}")
def delete_wall_image(
    cellar_id: str,
    image_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    ensure_cellar_access(db, cellar_id, str(user.user_id))

    image = crud.get_cellar_image_in_cellar(db, cellar_id, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    try:
        crud.delete_slots_by_image(db, image_id, commit=False)
        deleted = crud.delete_cellar_image(db, cellar_id, image_id, commit=False)

        if not deleted:
            raise HTTPException(status_code=404, detail="Image not found")

        db.commit()

        image_path = deleted.get("image_path")
        if image_path and os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception:
                logger.warning(f"Could not remove image file: {image_path}")

        return {
            "ok": True,
            "image_id": image_id,
        }

    except Exception:
        db.rollback()
        raise


@router.put("/wall/{cellar_id}/images/{image_id}/slots")
def save_wall_slots_batch(
    cellar_id: str,
    image_id: str,
    payload: SaveSlotsBatchRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    ensure_cellar_access(db, cellar_id, str(user.user_id))

    image = crud.get_cellar_image_in_cellar(db, cellar_id, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    existing_slots = crud.get_slots_by_image_id(db, image_id)
    existing_by_id = {slot["slot_id"]: slot for slot in existing_slots}

    deleted_slot_ids = payload.deleted_slot_ids or []

    for deleted_id in deleted_slot_ids:
        slot = existing_by_id.get(deleted_id)
        if not slot:
            raise HTTPException(
                status_code=400,
                detail=f"Deleted slot does not belong to image: {deleted_id}",
            )

    raw_slots = []
    for item in payload.slots:
        if item.slot_id:
            existing = existing_by_id.get(item.slot_id)
            if not existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Slot does not belong to image: {item.slot_id}",
                )

        raw_slots.append(
            {
                "slot_id": item.slot_id,
                "temp_id": item.temp_id,
                "slot_index": item.slot_index,
                "label": item.label,
                "bbox": {
                    "x": item.bbox.x,
                    "y": item.bbox.y,
                    "w": item.bbox.w,
                    "h": item.bbox.h,
                },
                "status": item.status,
                "is_active": item.is_active,
                "is_user_corrected": item.is_user_corrected,
            }
        )

    # normalize → validate → write (order matters)
    normalized_slots = normalize_slot_indexes(raw_slots)

    try:
        validate_slots_batch(
            normalized_slots,
            image_width=image["width"],
            image_height=image["height"],
            max_slots=40,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    try:
        if deleted_slot_ids:
            crud.delete_slots_by_ids(
                db=db,
                image_id=image_id,
                slot_ids=deleted_slot_ids,
                commit=False,
            )

        for slot in normalized_slots:
            bbox = slot["bbox"]
            polygon = bbox_to_polygon(bbox)
            center_x, center_y = bbox_center(bbox)

            if slot["slot_id"]:
                crud.update_slot_geometry(
                    db=db,
                    slot_id=slot["slot_id"],
                    polygon_json=polygon,
                    bbox_json=bbox,
                    center_x=center_x,
                    center_y=center_y,
                    label=slot["label"],
                    status=slot["status"],
                    is_active=slot["is_active"],
                    is_user_corrected=slot["is_user_corrected"],
                    commit=False,
                )
            else:
                crud.create_cellar_slot(
                    db=db,
                    cellar_id=cellar_id,
                    image_id=image_id,
                    slot_index=slot["slot_index"],
                    polygon_json=polygon,
                    bbox_json=bbox,
                    center_x=center_x,
                    center_y=center_y,
                    label=slot["label"],
                    status=slot["status"],
                    confidence=1.0,
                    is_active=slot["is_active"],
                    is_user_corrected=slot["is_user_corrected"],
                    commit=False,
                )

        db.commit()

    except Exception:
        db.rollback()
        raise

    final_slots = crud.get_slots_by_image_id(db, image_id)

    return {
        "image_id": image_id,
        "slots": [serialize_slot(slot) for slot in final_slots],
    }


@router.get("/wall/{cellar_id}/slots")
def get_wall_slots(
    cellar_id: str,
    image_id: str = Query(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    ensure_cellar_access(db, cellar_id, str(user.user_id))

    image = crud.get_cellar_image_in_cellar(db, cellar_id, image_id)
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    slots = crud.get_slots_by_image_id(db, image_id)

    return {
        "image_id": image_id,
        "slots": [serialize_slot(slot) for slot in slots],
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
    slot = crud.get_slot_by_id(db, slot_id)
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    ensure_cellar_access(db, slot["cellar_id"], str(user.user_id))

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

    return serialize_slot(updated)


@router.post("/wine/identify")
async def wine_identify(
    cellar_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    ensure_cellar_access(db, cellar_id, str(user.user_id))
    return identify_wine(await file.read())


@router.get("/wall/{cellar_id}/latest")
def get_latest_wall_analysis(
    cellar_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    ensure_cellar_access(db, cellar_id, str(user.user_id))

    image = crud.get_latest_cellar_image(db, cellar_id)
    if not image:
        return {
            "image": None,
            "slots": [],
        }

    slots = crud.get_slots_by_image_id(db, image["image_id"])

    return {
        "image": image,
        "slots": [serialize_slot(slot) for slot in slots],
    }


@router.get("/wall/image/{cellar_id}/{filename}")
def get_wall_image(cellar_id: str, filename: str):
    file_path = Path("uploads") / "cellars" / cellar_id / filename

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(file_path)