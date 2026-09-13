from service.app.prompts.base import build_module_analysis_prompt, build_module_annotation_prompt


DISPLAY_NAME = "HVAC"
AREAS = ("Outdoor unit", "Indoor unit", "Ducting", "Thermostat/wiring", "Visible leaks/rust/damage")
DEFECTS = (
    "Outdoor unit: damaged condenser fins, rust, missing panels, unstable pad, blocked airflow, crushed casing, loose lines.",
    "Indoor unit: visible leaks, rust, damaged cabinet, missing panels, clogged filter access, unsafe installation.",
    "Ducting: crushed, disconnected, leaking, torn, unsealed, sagging, kinked, or poorly supported ducting.",
    "Thermostat/wiring: exposed wiring, damaged disconnect, unsafe thermostat wiring, loose or missing electrical covers.",
    "Visible leaks/rust/damage: water leaks, condensate leaks, refrigerant line insulation damage, rust, corrosion, broken panels, physical damage.",
)
IGNORE_RULES = (
    "Do not report normal dust, equipment age, brand labels, or cosmetic wear unless visible damage or unsafe condition exists.",
    "Do not infer internal mechanical failure that is not visible in the photo.",
    "Do not box an entire HVAC unit unless most of the visible unit is damaged; box the damaged panel, rusted section, leak, wire, duct, or connection.",
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
