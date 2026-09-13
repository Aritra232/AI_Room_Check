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
    "Foundation: horizontal, vertical, stair-step, diagonal, or widening cracks; separated foundation joints; settlement gaps; exposed aggregate; spalling concrete; crumbling masonry; exposed reinforcement; damp staining along the base; efflorescence; visible water entry at foundation level.",
    "Foundation: box only the crack, spalled section, exposed reinforcement, water-stained foundation band, or settlement gap. Do not box the entire foundation wall.",
    "Siding/walls: cracked siding, warped siding, buckled panels, missing cladding, cracked stucco, cracked brick/block, failed mortar joints, peeling paint, blistered paint, rot, holes, impact damage, loose trim, damaged corner boards, open gaps, exposed sheathing.",
    "Siding/walls: separate different damaged patches when they are not connected. Include left and right facade edges, corners, porch returns, and side walls when visible.",
    "Doors/windows: broken glass, cracked panes, missing panes, rotted frames, damaged sills, failed caulk/seals, loose trim, gaps around frames, damaged exterior doors, swollen door material, cracked threshold, water damage around openings.",
    "Doors/windows: box the damaged frame, broken glass section, failed sill, failed seal, or damaged door area. Do not box normal glass reflections or the full clean opening.",
    "Drainage/gutters: loose gutters, sagging gutters, broken gutter sections, clogged gutters with visible blockage, disconnected downspouts, missing extensions, downspout discharging at foundation, water pooling, erosion channels, staining below gutter seams.",
    "Drainage/gutters: box the actual failed gutter/downspout part or visible pooling/erosion evidence, not the whole roof edge or whole yard.",
    "Exterior cracks/moisture: exterior wall cracks, damp staining, water intrusion marks, mold-like exterior growth, rot, peeling paint caused by moisture, efflorescence, staining below windows/rooflines, deteriorated caulk, moisture-damaged trim.",
    "Exterior cracks/moisture: include small clear cracks and moisture stains when boundaries are visible; ignore faint texture variation without a damage boundary.",
)
IGNORE_RULES = (
    "Do not report landscaping, dirt, parked objects, shadows, or cosmetic color variation as property defects.",
    "Report vegetation only when it visibly blocks drainage, damages the structure, or enters building openings.",
    "Do not box a whole facade; box the actual crack, damaged siding, wet area, damaged door/window part, or gutter defect.",
    "Do not report ordinary weathering, normal brick color variation, decorative joints, normal seams, clean expansion joints, or harmless surface dirt as defects.",
    "Do not infer hidden foundation movement from a photo unless visible cracks, gaps, displacement, or settlement indicators are present.",
    "Do not mark clean doors, clean windows, intact siding, normal gutters, or normal downspouts as damaged.",
    "If a defect spans multiple exterior categories, choose the category that best matches the visible damaged material. For example, rotten window sill belongs to Doors/windows; water staining below a gutter can belong to Drainage/gutters or Exterior cracks/moisture depending on evidence.",
    "If an exterior area is too far away, cropped off, blocked by vegetation, or not visible, mark it not_visible or needs_more_photo instead of guessing.",
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
