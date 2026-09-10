import asyncio
from dataclasses import dataclass
from io import BytesIO
import json
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image

from service.app.config import settings
from service.app.prompt import build_damage_annotation_prompt, build_room_analysis_prompt
from service.app.schemas import RoomAnalysis


INSPECTION_AREAS = {"Ceiling", "Walls", "Windows", "Floor", "Electrical outlets"}
RISK_LEVELS = {"Safe", "Low Risk", "Medium Risk", "High Risk", "Critical Risk"}


@dataclass(frozen=True)
class AnnotationView:
    original_photo_index: int
    crop_box: tuple[int, int, int, int]
    image_size: tuple[int, int]
    data: bytes
    label: str


ROOM_ANALYSIS_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "roomName": {"type": "string"},
        "severitySummary": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "critical": {"type": "integer"},
                "high": {"type": "integer"},
                "medium": {"type": "integer"},
                "low": {"type": "integer"},
                "safe": {"type": "integer"},
            },
            "required": ["critical", "high", "medium", "low", "safe"],
        },
        "overallRisk": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "score": {"type": "integer"},
                "level": {
                    "type": "string",
                    "enum": ["Safe", "Low Risk", "Medium Risk", "High Risk", "Critical Risk"],
                },
                "breakdown": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "high": {"type": "integer"},
                        "medium": {"type": "integer"},
                        "low": {"type": "integer"},
                        "safe": {"type": "integer"},
                    },
                    "required": ["high", "medium", "low", "safe"],
                },
            },
            "required": ["score", "level", "breakdown"],
        },
        "aiInsightSummary": {"type": "array", "items": {"type": "string"}},
        "recommendedActions": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "issueType": {"type": "string"},
                    "area": {
                        "type": "string",
                        "enum": ["Ceiling", "Walls", "Windows", "Floor", "Electrical outlets"],
                    },
                    "riskLevel": {
                        "type": "string",
                        "enum": ["Safe", "Low Risk", "Medium Risk", "High Risk", "Critical Risk"],
                    },
                    "description": {"type": "string"},
                    "action": {"type": "string"},
                },
                "required": ["issueType", "area", "riskLevel", "description", "action"],
            },
        },
        "detectedIssues": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "id": {"type": "string"},
                    "photoIndex": {"type": "integer"},
                    "area": {
                        "type": "string",
                        "enum": ["Ceiling", "Walls", "Windows", "Floor", "Electrical outlets"],
                    },
                    "issueType": {"type": "string"},
                    "riskLevel": {
                        "type": "string",
                        "enum": ["Safe", "Low Risk", "Medium Risk", "High Risk", "Critical Risk"],
                    },
                    "confidence": {"type": "integer"},
                    "location": {"type": "string"},
                    "description": {"type": "string"},
                    "details": {"type": "string"},
                    "recommendation": {"type": "string"},
                    "bbox": {
                        "type": "object",
                        "additionalProperties": False,
                        "properties": {
                            "x": {"type": "integer"},
                            "y": {"type": "integer"},
                            "width": {"type": "integer"},
                            "height": {"type": "integer"},
                        },
                        "required": ["x", "y", "width", "height"],
                    },
                    "annotations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "markerNumber": {"type": "integer"},
                                "bbox": {
                                    "type": "object",
                                    "additionalProperties": False,
                                    "properties": {
                                        "x": {"type": "integer"},
                                        "y": {"type": "integer"},
                                        "width": {"type": "integer"},
                                        "height": {"type": "integer"},
                                    },
                                    "required": ["x", "y", "width", "height"],
                                },
                            },
                            "required": ["markerNumber", "bbox"],
                        },
                    },
                },
                "required": [
                    "id",
                    "photoIndex",
                    "area",
                    "issueType",
                    "riskLevel",
                    "confidence",
                    "location",
                    "description",
                    "details",
                    "recommendation",
                    "annotations",
                ],
            },
        },
        "areas": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "name": {
                        "type": "string",
                        "enum": ["Ceiling", "Walls", "Windows", "Floor", "Electrical outlets"],
                    },
                    "visible": {"type": "boolean"},
                    "status": {
                        "type": "string",
                        "enum": ["checked", "issue_found", "not_visible", "needs_more_photo"],
                    },
                    "confidence": {"type": "integer"},
                    "note": {"type": "string"},
                },
                "required": ["name", "visible", "status", "confidence", "note"],
            },
        },
    },
    "required": [
        "roomName",
        "severitySummary",
        "overallRisk",
        "aiInsightSummary",
        "recommendedActions",
        "detectedIssues",
        "areas",
    ],
}


DAMAGE_ANNOTATION_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "damageAnnotations": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "photoIndex": {"type": "integer"},
                    "area": {
                        "type": "string",
                        "enum": ["Ceiling", "Walls", "Windows", "Floor", "Electrical outlets"],
                    },
                    "issueType": {"type": "string"},
                    "riskLevel": {
                        "type": "string",
                        "enum": ["Low Risk", "Medium Risk", "High Risk", "Critical Risk"],
                    },
                    "confidence": {"type": "integer"},
                    "evidence": {"type": "string"},
                    "box_2d": {
                        "type": "array",
                        "items": {"type": "integer"},
                    },
                },
                "required": [
                    "photoIndex",
                    "area",
                    "issueType",
                    "riskLevel",
                    "confidence",
                    "evidence",
                    "box_2d",
                ],
            },
        }
    },
    "required": ["damageAnnotations"],
}


async def analyze_room_photos(
    user_id: str,
    room_id: str,
    image_paths: list[Path],
    analysis_id: str,
) -> RoomAnalysis:
    payload, annotation_payload = await asyncio.gather(
        asyncio.to_thread(
            _generate_gemini_analysis,
            user_id,
            room_id,
            image_paths,
            analysis_id,
        ),
        asyncio.to_thread(_generate_gemini_damage_annotations, image_paths),
    )

    payload["analysisId"] = analysis_id
    payload["userId"] = user_id
    payload["roomId"] = room_id
    payload["status"] = "completed"
    payload["photosAnalyzed"] = len(image_paths)
    payload["originalImageUrls"] = []
    payload["annotatedImageUrl"] = None
    payload["annotatedImages"] = []
    _attach_damage_annotations(payload, annotation_payload, image_paths)
    _normalize_annotations(payload, image_paths)
    _normalize_detected_issues(payload)
    _normalize_recommended_actions(payload)
    _normalize_area_statuses(payload)
    _normalize_risk_summary(payload)
    payload["issuesFound"] = len(payload.get("detectedIssues", []))
    return RoomAnalysis(**payload)


def _generate_gemini_analysis(
    user_id: str,
    room_id: str,
    image_paths: list[Path],
    analysis_id: str,
) -> dict:
    client = genai.Client(api_key=settings.gemini_api_key)
    contents = [
        build_room_analysis_prompt(user_id, room_id, len(image_paths), analysis_id),
        *_gemini_image_parts(image_paths),
    ]

    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=_gemini_compatible_schema(ROOM_ANALYSIS_SCHEMA),
        ),
    )

    return json.loads(_response_text(response))


def _generate_gemini_damage_annotations(image_paths: list[Path]) -> dict:
    client = genai.Client(api_key=settings.gemini_api_key)
    annotation_views = _build_annotation_views(image_paths)
    contents = [
        build_damage_annotation_prompt(len(annotation_views)),
        *_gemini_annotation_view_contents(annotation_views),
    ]

    response = client.models.generate_content(
        model=settings.gemini_model,
        contents=contents,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=_gemini_compatible_schema(DAMAGE_ANNOTATION_SCHEMA),
        ),
    )

    return _map_annotation_payload_to_original(json.loads(_response_text(response)), annotation_views)


def _build_annotation_views(image_paths: list[Path]) -> list[AnnotationView]:
    views = []

    for photo_index, path in enumerate(image_paths):
        with Image.open(path) as image:
            image = image.convert("RGB")
            width, height = image.size
            regions = _annotation_regions(width, height)

            for label, crop_box in regions:
                views.append(
                    AnnotationView(
                        original_photo_index=photo_index,
                        crop_box=crop_box,
                        image_size=(crop_box[2] - crop_box[0], crop_box[3] - crop_box[1]),
                        data=_crop_to_jpeg_bytes(image, crop_box),
                        label=label,
                    )
                )

    return views


def _annotation_regions(width: int, height: int) -> list[tuple[str, tuple[int, int, int, int]]]:
    x_mid = round(width * 0.5)
    x_left = round(width * 0.42)
    y_top = round(height * 0.48)
    y_bottom = round(height * 0.42)

    regions = [
        ("full room view", (0, 0, width, height)),
        ("ceiling and upper wall view", (0, 0, width, max(y_top, 1))),
        ("left wall detail view", (0, 0, max(x_mid, 1), height)),
        ("center wall/window detail view", (max(0, x_left // 2), 0, min(width, width - x_left // 2), height)),
        ("right wall detail view", (min(x_mid, width - 1), 0, width, height)),
        ("floor and lower wall view", (0, min(y_bottom, height - 1), width, height)),
    ]

    return _dedupe_regions(regions)


def _dedupe_regions(
    regions: list[tuple[str, tuple[int, int, int, int]]],
) -> list[tuple[str, tuple[int, int, int, int]]]:
    seen = set()
    result = []

    for label, crop_box in regions:
        left, top, right, bottom = crop_box
        if right - left < 80 or bottom - top < 80 or crop_box in seen:
            continue
        seen.add(crop_box)
        result.append((label, crop_box))

    return result


def _crop_to_jpeg_bytes(image: Image.Image, crop_box: tuple[int, int, int, int]) -> bytes:
    buffer = BytesIO()
    image.crop(crop_box).save(buffer, format="JPEG", quality=92)
    return buffer.getvalue()


def _gemini_annotation_view_contents(annotation_views: list[AnnotationView]) -> list[str | types.Part]:
    contents: list[str | types.Part] = [
        "The uploaded images below are annotation views, not separate rooms. "
        "If the same damage appears in multiple views, return the best/tightest visible box."
    ]

    for index, view in enumerate(annotation_views):
        contents.extend(
            [
                (
                    f"Annotation view {index}. Use photoIndex {index}. "
                    f"Original photo {view.original_photo_index}. {view.label}. "
                    f"Crop box in original pixels: {view.crop_box}."
                ),
                types.Part.from_bytes(data=view.data, mime_type="image/jpeg"),
            ]
        )

    return contents


def _map_annotation_payload_to_original(
    annotation_payload: dict,
    annotation_views: list[AnnotationView],
) -> dict:
    mapped_annotations = []

    for annotation in annotation_payload.get("damageAnnotations", []):
        view_index = _safe_photo_index(annotation.get("photoIndex"), len(annotation_views))
        if view_index >= len(annotation_views):
            continue

        view = annotation_views[view_index]
        crop_bbox = _box_2d_to_bbox(annotation.get("box_2d"), view.image_size)
        if not crop_bbox:
            continue

        left, top, _, _ = view.crop_box
        annotation["photoIndex"] = view.original_photo_index
        annotation["bbox"] = {
            "x": left + crop_bbox["x"],
            "y": top + crop_bbox["y"],
            "width": crop_bbox["width"],
            "height": crop_bbox["height"],
        }
        mapped_annotations.append(annotation)

    annotation_payload["damageAnnotations"] = mapped_annotations
    return annotation_payload


def _attach_damage_annotations(
    payload: dict,
    annotation_payload: dict,
    image_paths: list[Path],
) -> None:
    for issue in payload.get("detectedIssues", []):
        issue["annotations"] = []
        issue["bbox"] = None

    image_sizes = [_image_size(path) for path in image_paths]
    fallback_issues: dict[tuple[int, str], dict] = {}

    for annotation in annotation_payload.get("damageAnnotations", []):
        area = annotation.get("area")
        if area not in INSPECTION_AREAS:
            continue

        photo_index = _safe_photo_index(annotation.get("photoIndex"), len(image_paths))
        image_size = image_sizes[photo_index] if photo_index < len(image_sizes) else None
        bbox = annotation.get("bbox") or _box_2d_to_bbox(annotation.get("box_2d"), image_size)
        if not bbox:
            continue

        target_issue = _find_issue_for_annotation(payload, annotation)
        if not target_issue:
            target_issue = _fallback_issue_for_annotation(
                payload,
                fallback_issues,
                annotation,
                photo_index,
            )

        target_issue.setdefault("annotations", []).append({"markerNumber": 1, "bbox": bbox})


def _safe_photo_index(value: object, photo_count: int) -> int:
    try:
        photo_index = int(value)
    except (TypeError, ValueError):
        return 0

    if photo_count <= 0:
        return 0
    return min(max(photo_index, 0), photo_count - 1)


def _box_2d_to_bbox(
    box_2d: list[int] | None,
    image_size: tuple[int, int] | None,
) -> dict | None:
    if not image_size or not isinstance(box_2d, list) or len(box_2d) != 4:
        return None

    image_width, image_height = image_size
    try:
        ymin, xmin, ymax, xmax = [int(value) for value in box_2d]
    except (TypeError, ValueError):
        return None

    ymin = min(max(ymin, 0), 1000)
    xmin = min(max(xmin, 0), 1000)
    ymax = min(max(ymax, 0), 1000)
    xmax = min(max(xmax, 0), 1000)

    if xmax <= xmin or ymax <= ymin:
        return None

    x = round(xmin * image_width / 1000)
    y = round(ymin * image_height / 1000)
    width = round((xmax - xmin) * image_width / 1000)
    height = round((ymax - ymin) * image_height / 1000)

    return _clamp_bbox(
        {"x": x, "y": y, "width": width, "height": height},
        image_width,
        image_height,
    )


def _find_issue_for_annotation(payload: dict, annotation: dict) -> dict | None:
    area = annotation.get("area")
    issue_type = _normalize_text(annotation.get("issueType", ""))
    candidates = [
        issue
        for issue in payload.get("detectedIssues", [])
        if issue.get("area") == area
        and issue.get("photoIndex", 0) == annotation.get("photoIndex", 0)
    ]

    if not candidates:
        candidates = [
            issue
            for issue in payload.get("detectedIssues", [])
            if issue.get("area") == area
        ]

    if not candidates:
        return None

    for issue in candidates:
        existing_type = _normalize_text(issue.get("issueType", ""))
        if issue_type and (
            issue_type in existing_type
            or existing_type in issue_type
            or any(token in existing_type for token in issue_type.split())
        ):
            return issue

    return candidates[0]


def _fallback_issue_for_annotation(
    payload: dict,
    fallback_issues: dict[tuple[int, str], dict],
    annotation: dict,
    photo_index: int,
) -> dict:
    area = annotation["area"]
    key = (photo_index, area)
    if key in fallback_issues:
        return fallback_issues[key]

    issue_type = annotation.get("issueType") or f"{area} damage"
    risk_level = annotation.get("riskLevel")
    if risk_level not in RISK_LEVELS:
        risk_level = "High Risk" if area in {"Ceiling", "Electrical outlets"} else "Medium Risk"

    confidence = _clamp_confidence(annotation.get("confidence"))
    issue_id = f"issue_{_area_slug(area)}_{len(payload.get('detectedIssues', [])) + 1:03d}"
    issue = {
        "id": issue_id,
        "photoIndex": photo_index,
        "area": area,
        "issueType": issue_type,
        "riskLevel": risk_level,
        "confidence": confidence,
        "location": f"Detected near {area.lower()}",
        "description": annotation.get("evidence") or f"Visible {issue_type.lower()} detected.",
        "details": annotation.get("evidence") or f"Visible {issue_type.lower()} detected.",
        "recommendation": _default_recommendation(area),
        "bbox": None,
        "annotations": [],
    }
    payload.setdefault("detectedIssues", []).append(issue)
    _append_fallback_recommendation(payload, issue)
    fallback_issues[key] = issue
    return issue


def _append_fallback_recommendation(payload: dict, issue: dict) -> None:
    actions = payload.setdefault("recommendedActions", [])
    issue_type = _normalize_text(issue["issueType"])

    for action in actions:
        if action.get("area") != issue["area"]:
            continue
        action_type = _normalize_text(action.get("issueType", ""))
        if issue_type in action_type or action_type in issue_type:
            return

    actions.append(
        {
            "issueType": issue["issueType"],
            "area": issue["area"],
            "riskLevel": issue["riskLevel"],
            "description": issue["description"],
            "action": issue["recommendation"],
        }
    )


def _clamp_confidence(value: object) -> int:
    try:
        confidence = int(value)
    except (TypeError, ValueError):
        return 85
    return min(max(confidence, 0), 100)


def _area_slug(area: str) -> str:
    return area.lower().replace(" ", "_")


def _default_recommendation(area: str) -> str:
    if area == "Ceiling":
        return "Inspect the damaged ceiling area, repair the source of moisture or structural failure, and replace unstable material."
    if area == "Walls":
        return "Inspect the wall damage source, remove loose material, and repair plaster or finish."
    if area == "Windows":
        return "Inspect the damaged frame, sill, glass, and seals, then repair or replace affected parts."
    if area == "Floor":
        return "Inspect the damaged floor surface and repair cracks, holes, unevenness, or water damage."
    if area == "Electrical outlets":
        return "Turn off power to the affected circuit and have a licensed electrician inspect and repair it."
    return "Inspect and repair the visible damage."


def _gemini_compatible_schema(schema: dict) -> dict:
    unsupported_keys = {"additionalProperties"}
    converted = {}

    for key, value in schema.items():
        if key in unsupported_keys:
            continue

        if isinstance(value, dict):
            converted[key] = _gemini_compatible_schema(value)
        elif isinstance(value, list):
            converted[key] = [
                _gemini_compatible_schema(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            converted[key] = value

    return converted


def _response_text(response) -> str:
    text_parts: list[str] = []

    for candidate in response.candidates or []:
        if not candidate.content:
            continue

        for part in candidate.content.parts or []:
            if getattr(part, "text", None):
                text_parts.append(part.text)

    return "".join(text_parts)


def _normalize_annotations(payload: dict, image_paths: list[Path]) -> None:
    image_sizes = [_image_size(path) for path in image_paths]
    marker_number = 1
    normalized_issues = []

    for issue in payload.get("detectedIssues", []):
        annotations = issue.get("annotations") or []
        if not annotations and issue.get("bbox"):
            annotations = [{"markerNumber": marker_number, "bbox": issue["bbox"]}]

        photo_index = issue.get("photoIndex", 0)
        image_size = image_sizes[photo_index] if photo_index < len(image_sizes) else None
        annotations = _clean_annotations(annotations, image_size, issue.get("area", ""))

        for annotation in annotations:
            annotation["markerNumber"] = marker_number
            marker_number += 1

        issue["annotations"] = annotations
        if annotations:
            issue["bbox"] = annotations[0]["bbox"]
        else:
            issue["bbox"] = None
        issue.setdefault("location", f"Detected near {issue.get('area', 'room area')}")
        issue.setdefault("details", issue.get("description", "Visible damage detected."))
        normalized_issues.append(issue)

    payload["detectedIssues"] = normalized_issues


def _normalize_detected_issues(payload: dict) -> None:
    payload["detectedIssues"] = [
        issue
        for issue in payload.get("detectedIssues", [])
        if _is_valid_detected_issue(issue)
    ]


def _is_valid_detected_issue(issue: dict) -> bool:
    area = issue.get("area", "")
    text = _issue_text(issue)

    if area == "Floor" and not _mentions_actual_floor_damage(text):
        return False

    if area == "Windows" and _is_only_whole_window_description(text):
        issue["annotations"] = []
        issue["bbox"] = None

    return True


def _issue_text(issue: dict) -> str:
    return " ".join(
        str(issue.get(key, ""))
        for key in ("issueType", "location", "description", "details", "recommendation")
    ).lower()


def _mentions_actual_floor_damage(text: str) -> bool:
    floor_damage_terms = (
        "crack",
        "cracked",
        "broken tile",
        "broken flooring",
        "warped",
        "water-damaged floor",
        "water damaged floor",
        "floor stain",
        "floor hole",
        "uneven floor",
        "damaged floor surface",
        "floor surface damage",
        "subfloor damage",
        "slab crack",
    )
    debris_terms = ("debris", "rubble", "fallen plaster", "plaster chunks", "loose material")

    has_floor_damage = any(term in text for term in floor_damage_terms)
    has_debris_only_language = any(term in text for term in debris_terms)
    return has_floor_damage and not (has_debris_only_language and "crack" not in text)


def _is_only_whole_window_description(text: str) -> bool:
    whole_window_terms = ("window glass", "multi-pane window", "whole window", "window structure")
    specific_damage_terms = (
        "broken glass",
        "cracked glass",
        "damaged frame",
        "rotted frame",
        "seal failure",
        "damaged seal",
        "crumbling sill",
        "missing sill",
    )
    return any(term in text for term in whole_window_terms) and not any(
        term in text for term in specific_damage_terms
    )


def _normalize_recommended_actions(payload: dict) -> None:
    issue_areas = {issue["area"] for issue in payload.get("detectedIssues", [])}
    issue_types = {_normalize_text(issue["issueType"]) for issue in payload.get("detectedIssues", [])}
    actions = []

    for action in payload.get("recommendedActions", []):
        area = action.get("area")
        issue_type = _normalize_text(action.get("issueType", ""))
        if area not in issue_areas:
            continue
        if not any(issue_type in existing or existing in issue_type for existing in issue_types):
            if area == "Floor":
                continue
        actions.append(action)

    payload["recommendedActions"] = actions


def _normalize_area_statuses(payload: dict) -> None:
    issue_areas = {issue["area"] for issue in payload.get("detectedIssues", [])}

    for area in payload.get("areas", []):
        if not area.get("visible"):
            area["status"] = "not_visible"
            continue
        if area["name"] in issue_areas:
            area["status"] = "issue_found"
        elif area.get("status") == "issue_found":
            area["status"] = "checked"
            area["note"] = "Visible area checked; no reportable issue confirmed."


def _normalize_risk_summary(payload: dict) -> None:
    severity = {"critical": 0, "high": 0, "medium": 0, "low": 0, "safe": 0}

    for issue in payload.get("detectedIssues", []):
        key = _risk_key(issue.get("riskLevel", "Safe"))
        severity[key] += 1

    if not payload.get("detectedIssues"):
        severity["safe"] = 1

    payload["severitySummary"] = severity
    severity_percentages = _risk_percentages(severity)
    payload["severityLevelSummary"] = [
        {
            "key": key,
            "label": label,
            "count": severity[key],
            "percentage": severity_percentages[key],
        }
        for key, label in (
            ("critical", "Critical Risk"),
            ("high", "High Risk"),
            ("medium", "Medium Risk"),
            ("low", "Low Risk"),
            ("safe", "Safe"),
        )
    ]
    risk_score = _risk_score(severity)
    payload["overallRisk"] = {
        "score": risk_score,
        "level": _risk_level(risk_score),
        "breakdown": {
            "critical": severity["critical"],
            "high": severity["high"],
            "medium": severity["medium"],
            "low": severity["low"],
            "safe": severity["safe"],
        },
        "breakdownPercentages": severity_percentages,
    }


def _risk_key(risk_level: str) -> str:
    if risk_level == "Critical Risk":
        return "critical"
    if risk_level == "High Risk":
        return "high"
    if risk_level == "Medium Risk":
        return "medium"
    if risk_level == "Low Risk":
        return "low"
    return "safe"


def _risk_score(severity: dict[str, int]) -> int:
    total = sum(severity.values()) or 1
    weighted = (
        severity["critical"] * 100
        + severity["high"] * 80
        + severity["medium"] * 50
        + severity["low"] * 25
        + severity["safe"] * 0
    )
    return round(weighted / total)


def _risk_percentages(severity: dict[str, int]) -> dict[str, int]:
    total = sum(severity.values()) or 1
    percentages = {
        key: round((value / total) * 100)
        for key, value in severity.items()
    }
    drift = 100 - sum(percentages.values())
    if drift and severity:
        largest_key = max(severity, key=lambda key: severity[key])
        percentages[largest_key] += drift
    return percentages


def _risk_level(score: int) -> str:
    if score >= 90:
        return "Critical Risk"
    if score >= 70:
        return "High Risk"
    if score >= 40:
        return "Medium Risk"
    if score > 0:
        return "Low Risk"
    return "Safe"


def _normalize_text(value: str) -> str:
    return " ".join(value.lower().replace("/", " ").replace("-", " ").split())


def _image_size(path: Path) -> tuple[int, int] | None:
    try:
        with Image.open(path) as image:
            return image.size
    except OSError:
        return None


def _clean_annotations(
    annotations: list[dict],
    image_size: tuple[int, int] | None,
    area: str,
) -> list[dict]:
    if not image_size:
        return annotations

    image_width, image_height = image_size
    cleaned = []

    for annotation in annotations:
        bbox = _clamp_bbox(annotation.get("bbox"), image_width, image_height)
        if not bbox or _is_oversized_bbox(bbox, image_width, image_height, area):
            continue
        cleaned.append({"markerNumber": annotation.get("markerNumber", 1), "bbox": bbox})

    if area not in {"Ceiling", "Walls"}:
        cleaned = _remove_containing_boxes(cleaned)

    prefer_larger_boxes = area in {"Ceiling", "Walls"}
    cleaned.sort(
        key=lambda item: item["bbox"]["width"] * item["bbox"]["height"],
        reverse=prefer_larger_boxes,
    )
    selected = []
    for annotation in cleaned:
        if any(_overlaps_too_much(annotation["bbox"], kept["bbox"]) for kept in selected):
            continue
        selected.append(annotation)

    selected.sort(key=lambda item: (item["bbox"]["y"], item["bbox"]["x"]))
    return selected


def _clamp_bbox(bbox: dict | None, image_width: int, image_height: int) -> dict | None:
    if not bbox:
        return None

    x = max(0, int(bbox.get("x", 0)))
    y = max(0, int(bbox.get("y", 0)))
    width = max(0, int(bbox.get("width", 0)))
    height = max(0, int(bbox.get("height", 0)))

    if _looks_normalized_bbox(x, y, width, height, image_width, image_height):
        x = round(x * image_width / 1000)
        y = round(y * image_height / 1000)
        width = round(width * image_width / 1000)
        height = round(height * image_height / 1000)

    x2 = min(image_width, x + width)
    y2 = min(image_height, y + height)
    width = x2 - x
    height = y2 - y

    if width < 8 or height < 8:
        return None

    return {"x": x, "y": y, "width": width, "height": height}


def _looks_normalized_bbox(
    x: int,
    y: int,
    width: int,
    height: int,
    image_width: int,
    image_height: int,
) -> bool:
    values = [x, y, width, height]
    fits_normalized_range = all(0 <= value <= 1000 for value in values)
    exceeds_image_bounds = x + width > image_width or y + height > image_height
    return fits_normalized_range and exceeds_image_bounds


def _is_oversized_bbox(bbox: dict, image_width: int, image_height: int, area: str) -> bool:
    area_ratio = (bbox["width"] * bbox["height"]) / (image_width * image_height)
    width_ratio = bbox["width"] / image_width
    height_ratio = bbox["height"] / image_height
    touches_left_or_right = bbox["x"] <= 2 or bbox["x"] + bbox["width"] >= image_width - 2
    touches_top_or_bottom = bbox["y"] <= 2 or bbox["y"] + bbox["height"] >= image_height - 2

    if area == "Ceiling":
        max_area_ratio = 0.32
        max_width_ratio = 0.9
        max_height_ratio = 0.55
        edge_area_ratio = 0.18
    elif area == "Walls":
        max_area_ratio = 0.26
        max_width_ratio = 0.72
        max_height_ratio = 0.58
        edge_area_ratio = 0.18
    elif area == "Floor":
        max_area_ratio = 0.16
        max_width_ratio = 0.65
        max_height_ratio = 0.5
        edge_area_ratio = 0.09
    elif area == "Windows":
        max_area_ratio = 0.08
        max_width_ratio = 0.42
        max_height_ratio = 0.42
        edge_area_ratio = 0.05
    else:
        max_area_ratio = 0.06
        max_width_ratio = 0.35
        max_height_ratio = 0.35
        edge_area_ratio = 0.04

    clipped_large_box = (
        (touches_left_or_right or touches_top_or_bottom)
        and area_ratio > edge_area_ratio
    )

    return (
        area_ratio > max_area_ratio
        or width_ratio > max_width_ratio
        or height_ratio > max_height_ratio
        or clipped_large_box
    )


def _remove_containing_boxes(annotations: list[dict]) -> list[dict]:
    result = []
    for annotation in annotations:
        bbox = annotation["bbox"]
        contains_smaller = False

        for other in annotations:
            other_bbox = other["bbox"]
            if bbox == other_bbox:
                continue

            bbox_area = bbox["width"] * bbox["height"]
            other_area = other_bbox["width"] * other_bbox["height"]
            if other_area >= bbox_area or bbox_area / other_area < 2.5:
                continue

            if _intersection_area(bbox, other_bbox) / other_area > 0.9:
                contains_smaller = True
                break

        if not contains_smaller:
            result.append(annotation)

    return result


def _overlaps_too_much(first: dict, second: dict) -> bool:
    intersection = _intersection_area(first, second)
    if intersection == 0:
        return False

    first_area = first["width"] * first["height"]
    second_area = second["width"] * second["height"]
    smaller_area = min(first_area, second_area)
    union_area = first_area + second_area - intersection

    return intersection / union_area > 0.28 or intersection / smaller_area > 0.68


def _intersection_area(first: dict, second: dict) -> int:
    left = max(first["x"], second["x"])
    top = max(first["y"], second["y"])
    right = min(first["x"] + first["width"], second["x"] + second["width"])
    bottom = min(first["y"] + first["height"], second["y"] + second["height"])

    if right <= left or bottom <= top:
        return 0
    return (right - left) * (bottom - top)


def _gemini_image_parts(image_paths: list[Path]) -> list[types.Part]:
    return [
        types.Part.from_bytes(data=path.read_bytes(), mime_type=_mime_type(path))
        for path in image_paths
    ]


def _mime_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".png":
        return "image/png"
    if suffix == ".webp":
        return "image/webp"
    return "image/jpeg"
