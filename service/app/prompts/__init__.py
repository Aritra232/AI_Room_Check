from service.app.prompts import exterior, hvac, interior, roof, water_heater


PROMPT_MODULES = {
    "interior": interior,
    "exterior": exterior,
    "roof": roof,
    "hvac": hvac,
    "water_heater": water_heater,
}


def build_room_analysis_prompt(
    user_id: str,
    room_id: str,
    photo_count: int,
    analysis_id: str,
    inspection_type: str = "interior",
) -> str:
    return PROMPT_MODULES[inspection_type].build_room_analysis_prompt(
        user_id,
        room_id,
        photo_count,
        analysis_id,
    )


def build_damage_annotation_prompt(
    photo_count: int,
    expected_issues: str = "",
    inspection_type: str = "interior",
) -> str:
    return PROMPT_MODULES[inspection_type].build_damage_annotation_prompt(
        photo_count,
        expected_issues,
    )
