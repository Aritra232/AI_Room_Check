from pathlib import Path
from datetime import date
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from service.app.config import settings
from service.app.db import get_room_analysis, save_room_analysis, save_room_confirmation
from service.app.schemas import (
    ConfirmAnalysisRequest,
    ConfirmAnalysisResponse,
    RoomAnalysis,
    RoomAnalysisResponse,
)
from service.app.services.annotation import create_annotated_images
from service.app.services.openai_room_analyzer import analyze_room_photos
from service.app.services.storage import save_uploads


app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/media", StaticFiles(directory=settings.storage_dir), name="media")
app.mount("/Annotated", StaticFiles(directory=settings.annotated_dir), name="annotated")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/api/users/{user_id}/rooms/analyze",
    response_model=RoomAnalysisResponse,
)
async def analyze_room(
    user_id: str,
    photos: list[UploadFile] = File(...),
) -> RoomAnalysis:
    if not photos:
        raise HTTPException(status_code=400, detail="At least one room photo is required.")

    room_id = f"room_{uuid4().hex}"
    analysis_id = uuid4().hex
    analysis_dir = settings.storage_dir / "users" / user_id / "rooms" / room_id / analysis_id
    original_paths = await save_uploads(photos, analysis_dir / "originals")

    ai_result = await analyze_room_photos(user_id, room_id, original_paths, analysis_id)
    annotated_paths = create_annotated_images(
        original_paths=original_paths,
        issues=ai_result.detectedIssues,
        output_dir=settings.annotated_dir,
        filename_prefix=f"{room_id}_{analysis_id}",
    )

    original_urls = [_media_url(path) for path in original_paths]
    annotated_urls = [_annotated_url(path) for path in annotated_paths]

    analysis_data = ai_result.model_dump()
    analysis_data.update(
        {
            "userId": user_id,
            "originalImageUrls": original_urls,
            "annotatedImageUrl": annotated_urls[0] if annotated_urls else None,
            "annotatedImages": annotated_urls,
        }
    )
    analysis_data["reportPreview"] = _build_report_preview(analysis_data)
    analysis = RoomAnalysis(**analysis_data)

    await save_room_analysis(user_id, room_id, analysis.model_dump())
    return analysis


@app.get(
    "/api/users/{user_id}/rooms/{room_id}/analysis",
    response_model=RoomAnalysisResponse,
)
async def room_analysis(user_id: str, room_id: str) -> RoomAnalysis:
    analysis = await get_room_analysis(user_id, room_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="No analysis found for this room.")
    return RoomAnalysis(**analysis)


@app.post("/api/users/{user_id}/rooms/{room_id}/analysis/confirm", response_model=ConfirmAnalysisResponse)
async def confirm_room_analysis(
    user_id: str,
    room_id: str,
    payload: ConfirmAnalysisRequest,
) -> ConfirmAnalysisResponse:
    await save_room_confirmation(user_id, room_id, payload.model_dump())
    return ConfirmAnalysisResponse(userId=user_id, roomId=room_id, status="saved")


def _media_url(path: Path) -> str:
    relative = path.relative_to(settings.storage_dir).as_posix()
    return f"/media/{relative}"


def _annotated_url(path: Path) -> str:
    relative = path.relative_to(settings.annotated_dir).as_posix()
    return f"/Annotated/{relative}"


def _build_report_preview(analysis: dict) -> dict:
    findings = []
    original_urls = analysis["originalImageUrls"]
    annotated_urls = analysis["annotatedImages"]

    for issue in analysis["detectedIssues"]:
        photo_index = issue["photoIndex"]
        annotations = issue.get("annotations", [])
        findings.append(
            {
                "id": issue["id"],
                "area": issue["area"],
                "issueType": issue["issueType"],
                "riskLevel": issue["riskLevel"],
                "confidence": issue["confidence"],
                "location": issue["location"],
                "details": issue["details"],
                "recommendedAction": issue["recommendation"],
                "imageUrl": original_urls[photo_index] if photo_index < len(original_urls) else None,
                "annotatedImageUrl": annotated_urls[photo_index] if photo_index < len(annotated_urls) else None,
                "markerNumbers": [item["markerNumber"] for item in annotations],
            }
        )

    severity = analysis["severitySummary"]
    executive_summary = (
        f"A total of {analysis['issuesFound']} issues were identified during the inspection. "
        f"{severity['critical'] + severity['high']} high risk issues require immediate attention."
    )

    return {
        "overview": {
            "propertyName": "Property Inspection",
            "propertyAddress": "Address not provided",
            "inspectionDate": date.today().strftime("%b %d, %Y"),
            "inspector": "PropertyGuard AI",
            "executiveSummary": executive_summary,
        },
        "findings": findings,
        "recommendations": analysis["recommendedActions"],
    }
