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
    "Tank condition: tank rust, corrosion, bulging, dents, cracked casing, leaking seams, staining from leaks, missing burner/electrical covers, damaged insulation jacket, scorch marks, visible casing damage.",
    "Tank condition: box the damaged tank surface, leak stain, bulge, missing cover, scorch mark, or damaged casing section. Do not box the full tank if only a small area is defective.",
    "Pipe connections: leaking hot/cold pipe joints, corroded fittings, mineral buildup at joints, loose unions, damaged shutoff valve, kinked/flexed connector damage, unsafe or deteriorated connections, missing pipe insulation where damage is visible.",
    "Pipe connections: box the leaking/corroded joint, damaged valve, deteriorated connector, mineral deposit, or loose fitting, not the whole pipe route.",
    "Pressure relief valve: damaged TPR valve, missing discharge pipe, capped or blocked discharge, discharge pipe too short, discharge pipe routed upward, unsafe termination, corrosion around valve, evidence of leakage from relief valve.",
    "Pressure relief valve: box the valve, missing/damaged discharge pipe, blocked outlet, unsafe pipe termination, or leak evidence at the valve.",
    "Rust/corrosion: rust blooms, corrosion patches, mineral deposits, green/white deposits on copper/fittings, flaking metal, staining below joints, deteriorated valves, rust on tank bottom, rust on drain valve, corrosion on vent connector.",
    "Rust/corrosion: include small but clear corrosion deposits when visible. Do not report normal pipe color or labels as corrosion.",
    "Leakage/drain pan/venting: water in drain pan, wet floor around heater, floor staining, active drip trails, damaged drain pan, missing drain pan where leak evidence is visible, disconnected vent/flue, rusted vent, backdraft staining, loose vent joint, poor vent slope, damaged draft hood.",
    "Leakage/drain pan/venting: box visible water, stains, drip trail, damaged pan, failed vent joint, disconnected vent, rusted vent area, or unsafe visible flue section.",
)
IGNORE_RULES = (
    "Do not report brand, labels, normal pipe layout, or age as defects by themselves.",
    "Do not infer combustion, pressure, or hidden internal problems unless visible evidence exists.",
    "Do not box the full water heater unless most of the tank is visibly damaged; box the rust, leak, damaged valve, pipe connection, drain pan issue, or venting defect.",
    "Do not report normal copper patina, normal galvanized pipe texture, intact insulation, manufacturer labels, warning stickers, or clean fittings as defects.",
    "Do not infer gas leaks, carbon monoxide issues, temperature problems, or internal tank failure unless the photo shows visible damage/evidence.",
    "Do not mark shadows under the tank, normal drain pans, clean floors, normal pipe bends, or clean vent connectors as damage.",
    "If a valve, vent, drain pan, or connection is cropped out, hidden, blocked, or too blurry, mark that area not_visible or needs_more_photo instead of guessing.",
    "Inspect the top connections, side controls, bottom drain valve, drain pan/floor, nearby wall/floor stains, gas/electrical connection, and vent/flue path when visible.",
    "If multiple small rust or leak points are separated, return separate boxes. If corrosion is one connected patch, return one practical tight box.",
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
