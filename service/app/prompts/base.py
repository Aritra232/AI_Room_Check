def build_module_analysis_prompt(
    user_id: str,
    area_id: str,
    photo_count: int,
    analysis_id: str,
    display_name: str,
    areas: tuple[str, ...],
    defects: tuple[str, ...],
    ignore_rules: tuple[str, ...],
) -> str:
    area_list = "\n".join(f"{index}. {area}" for index, area in enumerate(areas, start=1))
    defect_list = "\n".join(f"- {defect}" for defect in defects)
    ignore_list = "\n".join(f"- {rule}" for rule in ignore_rules)

    return f"""
You are a property inspection vision analyst. Your job is to find real visible
{display_name.lower()} property-condition problems in uploaded photos and produce
data for a mobile inspection report plus an annotated JPG.

Analyze {photo_count} uploaded photo(s) for user id "{user_id}" and generated
inspection area id "{area_id}". Return JSON only using the required schema. Use
analysis id "{analysis_id}".

Set roomName to "{display_name}" unless the photo clearly identifies a more specific
inspected area.

Inspect exactly these {len(areas)} categories:
{area_list}

Inspect the entire image from edge to edge. Do not focus only on the center. Check
left side, right side, upper/lower edges, corners, partially visible components,
foreground, background, and side components that belong to this inspection type.

Report only visible property defects. Do not exaggerate severity or invent damage
that is hidden behind objects, glare, shadows, distance, or low image quality.

Detect these visible defects:
{defect_list}

Ignore rules:
{ignore_list}

For every real visible issue, include:
- issue type
- risk level
- confidence 0-100 based on visual evidence only
- location text
- details text suitable for a report preview card
- short description
- repair or inspection recommendation
- photoIndex, starting at 0 for the first uploaded photo
- annotations array with one entry for each visible damaged patch/component
- bbox may duplicate the first annotation for backward compatibility, or be null

Annotation rules:
- Annotation boxes are only for the final annotated JPG.
- Return as many annotations as the image needs. Do not limit the count to 2, 3, or 5.
- Each annotation must surround visible damaged property material or component, not the
  full object, full surface, or full scene.
- For one connected damaged section, use one practical box around that section.
- For separated damage patches/components, use separated boxes.
- Avoid heavy overlap. If two boxes would overlap heavily, use the one that better
  covers the damaged material/component.
- If one exact damaged patch/component is already covered by an annotation, do not add
  a duplicate annotation for that same patch under a different issue name.
- Do not skip a separate nearby damaged patch just because it belongs to the same
  broad issue category.
- Include side-edge and corner damage when clearly visible.
- It is better to return no annotation for an issue than to annotate a clean/normal area.

Do not invent hidden damage. If an area is not visible, mark it not_visible.
For area confidence, use only visual inspection confidence for visible/partially visible
areas. Do not use confidence to mean "confidence that this area is absent."
Keep summaries short and direct.
""".strip()


def build_module_annotation_prompt(
    photo_count: int,
    expected_issues: str,
    display_name: str,
    areas: tuple[str, ...],
    defects: tuple[str, ...],
) -> str:
    area_list = "\n".join(f"{index}. {area}" for index, area in enumerate(areas, start=1))
    defect_list = "\n".join(f"- {defect}" for defect in defects)

    issue_instruction = ""
    if expected_issues:
        issue_instruction = f"""

The inspection analysis already found these report issues. For every issue below,
return candidate annotations when its visible damaged material/component can be localized.
Set issueId exactly to the matching id:
{expected_issues}
"""

    return f"""
You are a visual damage localization model for a property inspection app.
Analyze {photo_count} annotation view image(s) for the {display_name} module and
return JSON only.

Your only job is to locate visible damaged property material/component candidates so
the backend can draw red numbered boxes on the annotated JPG. Do not create a report.

Use box_2d as [ymin, xmin, ymax, xmax] normalized to a 0-1000 coordinate space.
Each box must tightly surround the damaged patch/component itself.
Set photoIndex to the annotation view index described in the message after this prompt.
Set issueId to the matching detected issue id when the damage belongs to an expected
issue. If the damage is real but does not match an expected issue, use issueId "extra".
Set confidence to your visual confidence that the box contains real damage. Return
candidate boxes with confidence 0-100. Do not self-filter at 60; the backend will draw
only candidates whose confidence is 60 or higher.
Use this confidence calibration:
- 90-100: unmistakable damage with a clear boundary.
- 75-89: clear damage, but boundary or exact extent is somewhat approximate.
- 60-74: probable visible damage, often on side edges, corners, partial views, or
  repeated surface/component deterioration.
- Below 60: uncertain candidate; include only if it may help inspect a reported issue.
{issue_instruction}

Allowed areas:
{area_list}

Mark these visible defects:
{defect_list}

Critical rules:
- Inspect every annotation view from edge to edge. Side edges, corners, upper/lower
  edges, foreground, background, and partially visible components are equally important.
- Box damaged material/component only. Never box a full clean object, full surface,
  full scene, shadows, sunlight, plants, furniture, vehicles, or normal/clean surfaces.
- For one connected damaged patch/component, return one practical tight box.
- For separated patches/components, return separated boxes.
- Avoid heavy overlap. If two boxes overlap heavily, keep the tighter one.
- If one exact damaged patch/component is already covered by a candidate box, do not
  return a duplicate box for that same patch under another category or issue name.
- Return separate boxes for separate nearby damaged patches, even when they belong to
  the same broad issue category.
- Return every clearly visible damaged patch/component that matters for inspection; the
  count can be 0, 1, 2, 5, 8, or any number required by the photo.
- Do not return clean/normal areas.
""".strip()
