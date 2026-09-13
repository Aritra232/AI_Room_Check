from datetime import date
from enum import StrEnum
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from service.app.config import settings
from service.app.db import get_room_analysis, save_room_analysis, save_room_confirmation
from service.app.inspection_modules import get_inspection_module
from service.app.schemas import (
    ConfirmAnalysisRequest,
    ConfirmAnalysisResponse,
    RoomAnalysis,
    RoomAnalysisResponse,
)
from service.app.services.annotation import create_annotated_images
from service.app.services.gemini_room_analyzer import analyze_room_photos
from service.app.services.s3_storage import upload_annotated_images
from service.app.services.storage import save_uploads


app = FastAPI(title=settings.app_name)


class InspectionType(StrEnum):
    interior = "interior"
    exterior = "exterior"
    roof = "roof"
    hvac = "hvac"
    water_heater = "water_heater"

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/api/users/{user_id}/inspections/{inspection_type}/analyze",
    response_model=RoomAnalysisResponse,
)
async def analyze_inspection(
    user_id: str,
    inspection_type: InspectionType,
    photos: list[UploadFile] = File(...),
) -> RoomAnalysis:
    return await _analyze_inspection(user_id, inspection_type.value, photos)


async def _analyze_inspection(
    user_id: str,
    inspection_type: str,
    photos: list[UploadFile],
) -> RoomAnalysis:
    if not photos:
        raise HTTPException(status_code=400, detail="At least one inspection photo is required.")

    try:
        module = get_inspection_module(inspection_type)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    room_id = f"{module.key}_{uuid4().hex}"
    analysis_id = uuid4().hex

    with TemporaryDirectory(prefix="room-inspection-") as temp_dir:
        analysis_dir = Path(temp_dir) / "analysis"
        original_paths = await save_uploads(photos, analysis_dir / "originals")
        annotated_dir = analysis_dir / "annotated"

        ai_result = await analyze_room_photos(
            user_id,
            room_id,
            original_paths,
            analysis_id,
            module.key,
        )
        annotated_paths = create_annotated_images(
            original_paths=original_paths,
            issues=ai_result.detectedIssues,
            output_dir=annotated_dir,
            filename_prefix=f"{room_id}_{analysis_id}",
        )
        annotated_urls = await upload_annotated_images(
            annotated_paths,
            user_id,
            room_id,
            analysis_id,
        )

    analysis_data = ai_result.model_dump()
    analysis_data.update(
        {
            "userId": user_id,
            "inspectionType": module.key,
            "originalImageUrls": [],
            "annotatedImageUrl": annotated_urls[0] if annotated_urls else None,
            "annotatedImages": annotated_urls,
        }
    )
    analysis_data["reportPreview"] = _build_report_preview(analysis_data)
    analysis = RoomAnalysis(**analysis_data)

    await save_room_analysis(user_id, room_id, analysis.model_dump())
    return analysis


@app.get(
    "/api/users/{user_id}/inspections/{inspection_type}/{room_id}/analysis",
    response_model=RoomAnalysisResponse,
)
async def inspection_analysis(
    user_id: str,
    inspection_type: InspectionType,
    room_id: str,
) -> RoomAnalysis:
    try:
        module = get_inspection_module(inspection_type.value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    analysis = await get_room_analysis(user_id, room_id)
    if not analysis:
        raise HTTPException(status_code=404, detail="No analysis found for this inspection.")
    if analysis.get("inspectionType", "interior") != module.key:
        raise HTTPException(status_code=404, detail="No analysis found for this inspection type.")
    return RoomAnalysis(**analysis)


@app.post(
    "/api/users/{user_id}/inspections/{inspection_type}/{room_id}/analysis/confirm",
    response_model=ConfirmAnalysisResponse,
)
async def confirm_inspection_analysis(
    user_id: str,
    inspection_type: InspectionType,
    room_id: str,
    payload: ConfirmAnalysisRequest,
) -> ConfirmAnalysisResponse:
    try:
        get_inspection_module(inspection_type.value)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    await save_room_confirmation(user_id, room_id, payload.model_dump())
    return ConfirmAnalysisResponse(userId=user_id, roomId=room_id, status="saved")


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
