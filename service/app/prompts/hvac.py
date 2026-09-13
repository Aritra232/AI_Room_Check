from service.app.prompts.base import build_module_analysis_prompt, build_module_annotation_prompt


DISPLAY_NAME = "HVAC"
AREAS = ("Outdoor unit", "Indoor unit", "Ducting", "Thermostat/wiring", "Visible leaks/rust/damage")
DEFECTS = (
    "Outdoor unit: crushed or bent condenser fins, heavily clogged fins, rusted cabinet, missing service panel, loose or broken fan grille, damaged fan blade if visible, crushed casing, unstable or sinking pad, blocked airflow from debris/vegetation, damaged refrigerant line insulation, loose line set.",
    "Outdoor unit: box the damaged fins, rusted/corroded section, missing panel, blocked airflow area, broken grille, damaged line insulation, or unstable pad evidence. Do not box the whole unit unless most of it is damaged.",
    "Indoor unit: water staining below unit, visible condensate leak, rusted cabinet, damaged access panel, missing cover, unsafe installation, disconnected drain, clogged filter access, torn insulation, visible mold-like growth on accessible HVAC surfaces.",
    "Indoor unit: box the leak, rust, damaged cabinet section, missing cover, disconnected drain, or unsafe visible component. Do not report internal failure unless visible.",
    "Ducting: crushed ducts, disconnected duct joints, torn flex duct, separated seams, missing tape/mastic, unsealed gaps, sagging runs, kinked ducts, collapsed duct sections, poor support straps, visible air leakage marks.",
    "Ducting: box the actual disconnected, torn, crushed, kinked, sagging, or unsealed section, not the entire duct network.",
    "Thermostat/wiring: exposed wiring, loose thermostat wiring, damaged thermostat body, missing electrical cover, damaged disconnect box, open junction box, burned wire marks, loose conduit, unsafe wire splices.",
    "Thermostat/wiring: box the exposed wire, damaged thermostat, open cover, damaged disconnect, missing cover plate, or unsafe visible electrical section.",
    "Visible leaks/rust/damage: active water leaks, condensate leaks, refrigerant line damage, damaged insulation, rust, corrosion, mineral staining, broken panels, impact damage, disconnected pipes or hoses, pooling water under HVAC equipment.",
    "Visible leaks/rust/damage: include small visible leak trails, rust blooms, water stains, and corrosion patches when boundaries are clear.",
)
IGNORE_RULES = (
    "Do not report normal dust, equipment age, brand labels, or cosmetic wear unless visible damage or unsafe condition exists.",
    "Do not infer internal mechanical failure that is not visible in the photo.",
    "Do not box an entire HVAC unit unless most of the visible unit is damaged; box the damaged panel, rusted section, leak, wire, duct, or connection.",
    "Do not report normal condensation on insulated lines unless there is visible dripping, staining, damaged insulation, or water accumulation.",
    "Do not report normal refrigerant line routing, normal PVC drain routing, normal ducts, normal vents, or clean electrical conduit as defects.",
    "Do not treat shadows inside grilles, normal coil darkness, manufacturer labels, screws, service stickers, or ordinary dirt as damage.",
    "Do not report blocked airflow unless obstruction is close enough to visibly restrict unit clearance or air movement.",
    "If a system component is hidden inside a cabinet, behind a wall, cropped out, or too blurry, mark it not_visible or needs_more_photo instead of guessing.",
    "Inspect left and right sides of the equipment, lower floor/pad area, nearby wall, visible pipe routes, wiring routes, duct joints, and drain outlets.",
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
