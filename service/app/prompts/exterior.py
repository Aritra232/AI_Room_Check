from service.app.prompts.base import build_module_analysis_prompt, build_module_annotation_prompt


DISPLAY_NAME = "Exterior"
AREAS = (
    "Foundation",
    "Siding/walls",
    "Doors/windows",
    "Drainage/gutters",
    "Exterior cracks/moisture",
)
DEFECTS = (
    "Foundation: cracks, settlement signs, spalling, exposed reinforcement, moisture staining at the base.",
    "Siding/walls: cracked siding, cracked stucco/brick, missing cladding, peeling paint, rot, holes, impact damage.",
    "Doors/windows: damaged exterior doors, broken glass, damaged window frames, damaged sills, failed seals.",
    "Drainage/gutters: loose, broken, clogged, disconnected, or missing gutters/downspouts; water pooling or poor drainage.",
    "Exterior cracks/moisture: visible cracks, damp staining, water intrusion, mold-like exterior growth, rot, efflorescence.",
)
IGNORE_RULES = (
    "Do not report landscaping, dirt, parked objects, shadows, or cosmetic color variation as property defects.",
    "Report vegetation only when it visibly blocks drainage, damages the structure, or enters building openings.",
    "Do not box a whole facade; box the actual crack, damaged siding, wet area, damaged door/window part, or gutter defect.",
)


def build_room_analysis_prompt(
    user_id: str,
    room_id: str,
    photo_count: int,
    analysis_id: str,
) -> str:
    return build_module_analysis_prompt(
        user_id,
        room_id,
        photo_count,
        analysis_id,
        DISPLAY_NAME,
        AREAS,
        DEFECTS,
        IGNORE_RULES,
    )


def build_damage_annotation_prompt(photo_count: int, expected_issues: str = "") -> str:
    return build_module_annotation_prompt(photo_count, expected_issues, DISPLAY_NAME, AREAS, DEFECTS)
