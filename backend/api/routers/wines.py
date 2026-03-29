import base64
import json

import anthropic
from tavily import TavilyClient
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from backend.core.config import settings
from backend.db.session import get_db
from backend.api.deps import get_current_user
from backend.db import crud
from backend.api.schemas import WineCreateIn, WineUpdateIn, WineOut

router = APIRouter(prefix="/wines", tags=["wines"])


def _check_ownership(wine, user_id: str):
    if not wine:
        raise HTTPException(status_code=404, detail="Wine not found")
    if wine["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not enough permissions")


@router.get("", response_model=list[WineOut])
def list_wines(
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return crud.list_wines_by_user(db, str(user.user_id))


@router.post("", response_model=WineOut, status_code=201)
def create_wine(
    payload: WineCreateIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    return crud.create_wine(
        db,
        user_id=str(user.user_id),
        winery=payload.winery,
        varietal=payload.varietal,
        vintage=payload.vintage,
        region=payload.region,
        notes=payload.notes,
        quantity=payload.quantity,
    )


@router.get("/{wine_id}", response_model=WineOut)
def get_wine(
    wine_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    wine = crud.get_wine_by_id(db, wine_id)
    _check_ownership(wine, str(user.user_id))
    return wine


@router.patch("/{wine_id}", response_model=WineOut)
def update_wine(
    wine_id: str,
    payload: WineUpdateIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    wine = crud.get_wine_by_id(db, wine_id)
    _check_ownership(wine, str(user.user_id))
    updated = crud.update_wine(
        db,
        wine_id=wine_id,
        winery=payload.winery,
        varietal=payload.varietal,
        vintage=payload.vintage,
        region=payload.region,
        notes=payload.notes,
        quantity=payload.quantity,
    )
    return updated


def _parse_json(raw: str) -> dict:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


@router.post("/analyze-photo")
async def analyze_wine_photo(
    files: list[UploadFile] = File(...),
    user=Depends(get_current_user),
):
    if not settings.ANTHROPIC_API_KEY:
        raise HTTPException(status_code=503, detail="Claude Vision not configured")
    if not files:
        raise HTTPException(status_code=400, detail="At least one image is required")

    claude = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    # ── Step 1: read the label from the images ────────────────────────────────
    content = []
    for f in files:
        image_bytes = await f.read()
        media_type = f.content_type or "image/jpeg"
        image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")
        content.append({
            "type": "image",
            "source": {"type": "base64", "media_type": media_type, "data": image_b64},
        })

    content.append({
        "type": "text",
        "text": (
            "Look at the wine bottle label(s) and extract exactly what is written. "
            "Do not guess or infer anything not visible. "
            "Respond with ONLY a valid JSON object:\n"
            "{\n"
            '  "winery": "<producer name as written, or null>",\n'
            '  "varietal": "<grape variety or blend as written, or null>",\n'
            '  "vintage": <year as integer, or null>,\n'
            '  "region": "<region/appellation as written, or null>"\n'
            "}"
        ),
    })

    msg1 = claude.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=256,
        messages=[{"role": "user", "content": content}],
    )

    try:
        draft = _parse_json(msg1.content[0].text)
    except (json.JSONDecodeError, IndexError):
        raise HTTPException(status_code=422, detail="Could not parse image analysis")

    # ── Step 2: verify with web search (if Tavily is configured) ─────────────
    search_context = ""
    if settings.TAVILY_API_KEY:
        query_parts = [
            draft.get("winery") or "",
            draft.get("varietal") or "",
            str(draft.get("vintage")) if draft.get("vintage") else "",
            "wine",
        ]
        query = " ".join(p for p in query_parts if p).strip()

        if query and query != "wine":
            try:
                tavily = TavilyClient(api_key=settings.TAVILY_API_KEY)
                results = tavily.search(query=query, max_results=3, search_depth="basic")
                snippets = [
                    r.get("content", "") for r in results.get("results", []) if r.get("content")
                ]
                if snippets:
                    search_context = "\n\n".join(snippets[:3])
            except Exception:
                pass  # search failed — continue without it

    # ── Step 3: reconcile image data + web results ────────────────────────────
    if search_context:
        reconcile_prompt = (
            f"I analyzed a wine label from an image and got this draft data:\n"
            f"{json.dumps(draft, ensure_ascii=False)}\n\n"
            f"I also searched the web and found the following information about this wine:\n"
            f"{search_context}\n\n"
            "Using both sources, produce the most accurate wine data. "
            "Prefer what is clearly visible in the label; use web results only to correct obvious errors or fill gaps. "
            "Respond with ONLY a valid JSON object:\n"
            "{\n"
            '  "winery": "<corrected winery name, or null>",\n'
            '  "varietal": "<corrected varietal, or null>",\n'
            '  "vintage": <corrected year as integer, or null>,\n'
            '  "region": "<corrected region, or null>"\n'
            "}"
        )

        msg2 = claude.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            messages=[{"role": "user", "content": reconcile_prompt}],
        )

        try:
            final = _parse_json(msg2.content[0].text)
        except (json.JSONDecodeError, IndexError):
            final = draft  # fall back to image-only result
    else:
        final = draft

    return {
        "winery":   final.get("winery"),
        "varietal": final.get("varietal"),
        "vintage":  final.get("vintage"),
        "region":   final.get("region"),
    }


@router.delete("/{wine_id}")
def delete_wine(
    wine_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    wine = crud.get_wine_by_id(db, wine_id)
    _check_ownership(wine, str(user.user_id))
    crud.delete_wine(db, wine_id)
    return {"ok": True}
