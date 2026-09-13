from service.app.prompts.base import build_module_analysis_prompt, build_module_annotation_prompt


DISPLAY_NAME = "Roof"
AREAS = ("Shingles/tiles", "Flashing", "Gutters", "Chimney/vents", "Sagging/leaks")
DEFECTS = (
    "Shingles/tiles: missing shingles/tiles, cracked pieces, curled edges, lifted tabs, loose/slipped tiles, broken corners, exposed underlayment, bare patches, granule loss with clear boundary, punctures, storm or impact damage.",
    "Shingles/tiles: box the damaged group or missing section. Do not box the entire roof plane when only a small group is defective.",
    "Flashing: missing, lifted, bent, rusted, cracked, separated, poorly sealed, or displaced flashing at valleys, eaves, rakes, roof-wall intersections, chimneys, skylights, vents, dormers, and penetrations.",
    "Flashing: include failed sealant lines, gaps at flashing edges, visible lifted metal, rust holes, and cracked boot/flashing collars.",
    "Gutters: clogged gutters with visible debris blockage, sagging runs, broken sections, separated seams, loose hangers, missing gutters, disconnected downspouts, leaking joints, overflow staining below gutters.",
    "Gutters: box the failed gutter or downspout segment, visible clog, separated seam, or sagging portion. Do not box a clean roof edge.",
    "Chimney/vents: cracked chimney masonry, missing mortar, leaning chimney, damaged caps, loose caps, blocked flue openings, damaged vent boots, cracked rubber boots, loose vent pipes, missing storm collars, failed seals around penetrations.",
    "Chimney/vents: box the damaged chimney section, vent boot, cap, seal, or penetration defect, not the whole chimney if only a small area is damaged.",
    "Sagging/leaks: sagging roof planes, dips, deformation lines, holes, soft-looking rotten decking, water staining, leak trails, exposed sheathing, daylight through roof holes, collapsed roof areas.",
    "Sagging/leaks: if sagging is broad but clearly visible, box the visible sag/deformation area. If a leak is only inferred and no visible stain/hole/deformation exists, do not report it.",
)
IGNORE_RULES = (
    "Do not report normal roof color variation, light dirt, leaves, reflections, or shadows as defects.",
    "If the roof is too distant or partly hidden, use needs_more_photo for unclear areas.",
    "Do not box the entire roof plane; box the damaged shingle/tile group, flashing defect, gutter defect, chimney/vent defect, sagging area, or leak evidence.",
    "Do not report normal roof pattern lines, ridge lines, overlaps, clean valleys, or expected shingle/tile seams as cracks.",
    "Do not report leaf piles as roof damage unless they visibly clog gutters or trap moisture against roof components.",
    "Do not confuse glare, sun highlights, wet shine, moss color, or tree shadows with missing shingles or leaks unless a clear damage boundary is visible.",
    "Do not infer roof leaks from interior damage in this module unless exterior roof leak evidence is visible in the uploaded roof photo.",
    "If roof covering is hidden by snow, tarps, heavy vegetation, distance, or image blur, mark affected areas needs_more_photo instead of guessing.",
    "For multi-slope roofs, inspect every visible slope, ridge, valley, edge, dormer, chimney, vent, and gutter run from left to right.",
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
