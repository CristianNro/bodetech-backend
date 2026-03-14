from pydantic import BaseModel, Field, model_validator
from typing import Optional


class BBoxInput(BaseModel):
    x: float
    y: float
    w: float
    h: float


class BatchSlotInput(BaseModel):
    slot_id: Optional[str] = None
    temp_id: Optional[str] = None
    slot_index: Optional[int] = None
    bbox: BBoxInput
    status: str = "empty"
    is_active: bool = True
    is_user_corrected: bool = True

    @model_validator(mode="after")
    def validate_identity(self):
        if not self.slot_id and not self.temp_id:
            raise ValueError("Each slot must include slot_id or temp_id")
        return self


class SaveSlotsBatchRequest(BaseModel):
    slots: list[BatchSlotInput] = Field(default_factory=list)
    deleted_slot_ids: list[str] = Field(default_factory=list)