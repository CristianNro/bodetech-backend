import io
import uuid
from pathlib import Path
from typing import Any

from PIL import Image

UPLOAD_ROOT = Path("uploads/cellars")


def save_cellar_image(
    image_bytes: bytes,
    cellar_id: str,
    original_filename: str | None = None,
) -> dict[str, Any]:
    image_id = str(uuid.uuid4())

    ext = ".jpg"
    if original_filename and "." in original_filename:
        detected_ext = Path(original_filename).suffix.lower()
        if detected_ext:
            ext = detected_ext

    cellar_dir = UPLOAD_ROOT / cellar_id
    cellar_dir.mkdir(parents=True, exist_ok=True)

    file_path = cellar_dir / f"{image_id}{ext}"

    with open(file_path, "wb") as f:
        f.write(image_bytes)

    with Image.open(io.BytesIO(image_bytes)) as img:
        width, height = img.size

    image_url = f"/vision/wall/image/{cellar_id}/{image_id}{ext}"

    return {
        "image_id": image_id,
        "image_path": str(file_path),
        "image_url": image_url,
        "width": width,
        "height": height,
    }


def generate_fake_slots(
    width: int,
    height: int,
    rows: int = 3,
    cols: int = 4,
) -> list[dict[str, Any]]:
    slots: list[dict[str, Any]] = []

    margin_x = int(width * 0.06)
    margin_y = int(height * 0.08)
    gap_x = int(width * 0.02)
    gap_y = int(height * 0.03)

    usable_width = width - (margin_x * 2) - (gap_x * (cols - 1))
    usable_height = height - (margin_y * 2) - (gap_y * (rows - 1))

    slot_w = max(40, usable_width // cols)
    slot_h = max(60, usable_height // rows)

    slot_index = 1
    for row in range(rows):
        for col in range(cols):
            x = margin_x + col * (slot_w + gap_x)
            y = margin_y + row * (slot_h + gap_y)

            polygon = [
                [x, y],
                [x + slot_w, y],
                [x + slot_w, y + slot_h],
                [x, y + slot_h],
            ]

            slots.append(
                {
                    "slot_index": slot_index,
                    "label": f"S{slot_index}",
                    "bbox": {
                        "x": x,
                        "y": y,
                        "w": slot_w,
                        "h": slot_h,
                    },
                    "polygon": polygon,
                    "center_x": x + slot_w / 2,
                    "center_y": y + slot_h / 2,
                    "status": "unknown",
                    "confidence": 0.35,
                    "is_user_corrected": False,
                }
            )
            slot_index += 1

    return slots