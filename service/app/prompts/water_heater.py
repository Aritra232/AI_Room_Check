from service.app.prompts.base import build_module_analysis_prompt, build_module_annotation_prompt


DISPLAY_NAME = "Water Heater"
AREAS = (
    "Tank condition",
    "Pipe connections",
    "Pressure relief valve",
    "Rust/corrosion",
    "Leakage/drain pan/venting",
)
DEFECTS = (
    "Tank condition: tank rust, bulging, dents, leakage, missing covers, damaged insulation, visible casing damage.",
    "Pipe connections: leaking pipes, corroded fittings, loose joints, damaged shutoff valve, unsafe or deteriorated connections.",
    "Pressure relief valve: damaged pressure relief valve, missing discharge pipe, blocked discharge, unsafe discharge routing.",
    "Rust/corrosion: rust, corrosion, mineral deposits, staining, or deterioration on tank, pipes, valves, fittings, or nearby parts.",
    "Leakage/drain pan/venting: water in drain pan, floor staining around heater, active leak evidence, damaged or disconnected vent/flue.",
)
IGNORE_RULES = (
    "Do not report brand, labels, normal pipe layout, or age as defects by themselves.",
    "Do not infer combustion, pressure, or hidden internal problems unless visible evidence exists.",
    "Do not box the full water heater unless most of the tank is visibly damaged; box the rust, leak, damaged valve, pipe connection, drain pan issue, or venting defect.",
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
