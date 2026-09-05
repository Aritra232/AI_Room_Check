import asyncio
import json
from pathlib import Path

from google import genai
from google.genai import types
from PIL import Image

from service.app.config import settings
from service.app.prompt import build_room_analysis_prompt
from service.app.schemas import RoomAnalysis


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


async def analyze_room_photos(
    user_id: str,
    room_id: str,
    image_paths: list[Path],
    analysis_id: str,
) -> RoomAnalysis:
    payload = await asyncio.to_thread(
        _generate_gemini_analysis,
        user_id,
        room_id,
        image_paths,
        analysis_id,
    )

    payload["analysisId"] = analysis_id
    payload["userId"] = user_id
    payload["roomId"] = room_id
    payload["status"] = "completed"
    payload["photosAnalyzed"] = len(image_paths)
    payload["originalImageUrls"] = []
    payload["annotatedImageUrl"] = None
    payload["annotatedImages"] = []
    _normalize_annotations(payload, image_paths)
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

    return json.loads(response.text)


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

    cleaned = _remove_containing_boxes(cleaned)
    cleaned.sort(key=lambda item: item["bbox"]["width"] * item["bbox"]["height"])
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

    if area in {"Ceiling", "Walls"}:
        max_area_ratio = 0.28
        max_width_ratio = 0.82
        max_height_ratio = 0.7
        edge_area_ratio = 0.18
    elif area == "Floor":
        max_area_ratio = 0.16
        max_width_ratio = 0.65
        max_height_ratio = 0.5
        edge_area_ratio = 0.09
    else:
        max_area_ratio = 0.14
        max_width_ratio = 0.55
        max_height_ratio = 0.55
        edge_area_ratio = 0.08

    clipped_large_box = (
        touches_left_or_right
        and touches_top_or_bottom
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
