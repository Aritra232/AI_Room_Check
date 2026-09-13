from dataclasses import dataclass


@dataclass(frozen=True)
class InspectionModule:
    key: str
    display_name: str
    subject_name: str
    areas: tuple[str, ...]
    defects: tuple[str, ...]
    ignore_rules: tuple[str, ...]


INSPECTION_MODULES = {
    "interior": InspectionModule(
        key="interior",
        display_name="Interior",
        subject_name="room",
        areas=("Ceiling", "Walls", "Windows", "Floor", "Electrical outlets"),
        defects=(),
        ignore_rules=(),
    ),
    "exterior": InspectionModule(
        key="exterior",
        display_name="Exterior",
        subject_name="exterior area",
        areas=(
            "Foundation",
            "Siding/walls",
            "Doors/windows",
            "Drainage/gutters",
            "Exterior cracks/moisture",
        ),
        defects=(
            "foundation cracks, settlement signs, spalling, exposed reinforcement",
            "siding, stucco, brick, or exterior wall cracks, missing cladding, peeling paint, moisture staining",
            "damaged exterior doors, damaged window frames, broken glass, failed seals",
            "loose or clogged gutters, poor drainage, water pooling, downspout problems",
            "visible exterior cracks, moisture intrusion, damp staining, rot, or water-damaged exterior material",
        ),
        ignore_rules=(
            "Do not report landscaping, dirt, parked objects, shadows, or cosmetic color variation as property defects.",
            "Report vegetation only when it visibly blocks drainage, damages the structure, or enters building openings.",
        ),
    ),
    "roof": InspectionModule(
        key="roof",
        display_name="Roof",
        subject_name="roof",
        areas=("Shingles/tiles", "Flashing", "Gutters", "Chimney/vents", "Sagging/leaks"),
        defects=(
            "missing, cracked, curled, loose, or broken shingles/tiles",
            "damaged flashing around roof edges, valleys, walls, chimneys, skylights, or vents",
            "damaged or clogged gutters, loose downspouts, poor drainage from roof edge",
            "cracked chimney, damaged vent boots, loose caps, blocked or damaged roof penetrations",
            "sagging roof planes, holes, rot, structural deformation, visible water damage",
        ),
        ignore_rules=(
            "Do not report normal roof color variation, light dirt, leaves, or shadows as defects.",
            "If the roof is too distant or partly hidden, use needs_more_photo for unclear areas.",
        ),
    ),
    "hvac": InspectionModule(
        key="hvac",
        display_name="HVAC",
        subject_name="HVAC equipment",
        areas=("Outdoor unit", "Indoor unit", "Ducting", "Thermostat/wiring", "Visible leaks/rust/damage"),
        defects=(
            "damaged condenser fins, rust, missing panels, unstable pad, blocked airflow",
            "visible indoor unit leaks, rust, damaged cabinet, clogged filter access, unsafe installation",
            "crushed, disconnected, leaking, torn, or poorly supported ducting",
            "exposed wiring, damaged disconnect, unsafe thermostat wiring, missing covers",
            "visible water leaks, refrigerant line damage, rust, corrosion, broken panels, or physical equipment damage",
        ),
        ignore_rules=(
            "Do not report normal dust or equipment age unless visible damage or unsafe condition exists.",
            "Do not infer internal mechanical failure that is not visible in the photo.",
        ),
    ),
    "water_heater": InspectionModule(
        key="water_heater",
        display_name="Water Heater",
        subject_name="water heater",
        areas=(
            "Tank condition",
            "Pipe connections",
            "Pressure relief valve",
            "Rust/corrosion",
            "Leakage/drain pan/venting",
        ),
        defects=(
            "tank rust, corrosion, bulging, leakage, missing covers, damaged insulation",
            "leaking or corroded pipe connections, loose fittings, damaged shutoff connections",
            "damaged pressure relief valve, missing discharge pipe, unsafe discharge routing",
            "rust, corrosion, staining, mineral deposits, or visible deterioration on tank, fittings, or nearby parts",
            "water in drain pan, floor staining around heater, active leak evidence, damaged or disconnected venting",
        ),
        ignore_rules=(
            "Do not report brand, labels, normal pipe layout, or age as defects by themselves.",
            "Do not infer combustion or pressure problems unless visible evidence exists.",
        ),
    ),
}


def get_inspection_module(inspection_type: str) -> InspectionModule:
    key = inspection_type.lower().replace("-", "_")
    if key not in INSPECTION_MODULES:
        allowed = ", ".join(INSPECTION_MODULES)
        raise ValueError(f"Unsupported inspection type '{inspection_type}'. Allowed: {allowed}.")
    return INSPECTION_MODULES[key]
