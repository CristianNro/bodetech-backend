from typing import Any


def bbox_to_polygon(bbox: dict[str, Any]) -> list[list[float]]:
    x = float(bbox["x"])
    y = float(bbox["y"])
    w = float(bbox["w"])
    h = float(bbox["h"])

    return [
        [x, y],
        [x + w, y],
        [x + w, y + h],
        [x, y + h],
    ]


def bbox_center(bbox: dict[str, Any]) -> tuple[float, float]:
    x = float(bbox["x"])
    y = float(bbox["y"])
    w = float(bbox["w"])
    h = float(bbox["h"])

    return (x + w / 2, y + h / 2)


def is_valid_bbox_shape(bbox: dict[str, Any]) -> bool:
    required = ("x", "y", "w", "h")
    if not isinstance(bbox, dict):
        return False

    for key in required:
        if key not in bbox:
            return False
        if not isinstance(bbox[key], (int, float)):
            return False

    return bbox["w"] > 0 and bbox["h"] > 0


def is_bbox_inside_image(bbox: dict[str, Any], image_width: int, image_height: int) -> bool:
    x = float(bbox["x"])
    y = float(bbox["y"])
    w = float(bbox["w"])
    h = float(bbox["h"])

    return x >= 0 and y >= 0 and (x + w) <= image_width and (y + h) <= image_height


def boxes_overlap(a: dict[str, Any], b: dict[str, Any]) -> bool:
    return (
        float(a["x"]) < float(b["x"]) + float(b["w"]) and
        float(a["x"]) + float(a["w"]) > float(b["x"]) and
        float(a["y"]) < float(b["y"]) + float(b["h"]) and
        float(a["y"]) + float(a["h"]) > float(b["y"])
    )



def normalize_slot_indexes(slots: list[dict]) -> list[dict]:
    normalized = []

    for index, slot in enumerate(slots):
        new_slot = {**slot}
        new_slot["slot_index"] = index
        normalized.append(new_slot)

    return normalized


def validate_no_overlap(slots: list[dict]) -> None:
    for i in range(len(slots)):
        for j in range(i + 1, len(slots)):
            a = slots[i]["bbox"]
            b = slots[j]["bbox"]

            if boxes_overlap(a, b):
                raise ValueError(
                    f"Slots overlap: indexes {slots[i]['slot_index']} and {slots[j]['slot_index']}"
                )


def validate_slots_batch(
    slots: list[dict],
    image_width: int,
    image_height: int,
    max_slots: int = 40,
    ) -> None:
    if len(slots) > max_slots:
        raise ValueError(f"Maximum number of slots is {max_slots}")

    for slot in slots:
        bbox = slot["bbox"]

        if not is_valid_bbox_shape(bbox):
            raise ValueError(f"Invalid bbox for slot index {slot['slot_index']}")

        if not is_bbox_inside_image(bbox, image_width, image_height):
            raise ValueError(f"Slot index {slot['slot_index']} is outside image bounds")

    validate_no_overlap(slots)