from service.app.prompts.base import build_module_analysis_prompt, build_module_annotation_prompt


DISPLAY_NAME = "Roof"
AREAS = ("Shingles/tiles", "Flashing", "Gutters", "Chimney/vents", "Sagging/leaks")
DEFECTS = (
    "Shingles/tiles: missing, cracked, curled, loose, lifted, broken, slipped, or visibly deteriorated shingles/tiles.",
    "Flashing: damaged, missing, lifted, rusted, or poorly sealed flashing at valleys, edges, chimneys, skylights, vents, or wall intersections.",
    "Gutters: clogged, loose, broken, sagging, disconnected, leaking, or missing gutters/downspouts.",
    "Chimney/vents: cracked chimney masonry, damaged caps, damaged vent boots, loose vents, blocked penetrations, failed seals.",
    "Sagging/leaks: sagging roof planes, holes, rot, water staining, leak paths, soft/deformed roof areas.",
)
IGNORE_RULES = (
    "Do not report normal roof color variation, light dirt, leaves, reflections, or shadows as defects.",
    "If the roof is too distant or partly hidden, use needs_more_photo for unclear areas.",
    "Do not box the entire roof plane; box the damaged shingle/tile group, flashing defect, gutter defect, chimney/vent defect, sagging area, or leak evidence.",
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
