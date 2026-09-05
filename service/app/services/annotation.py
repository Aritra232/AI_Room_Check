from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from service.app.schemas import BoundingBox, DetectedIssue


ANNOTATION_COLOR = "#DC2626"


def create_annotated_images(
    original_paths: list[Path],
    issues: list[DetectedIssue],
    output_dir: Path,
    filename_prefix: str = "annotated",
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    annotated_paths: list[Path] = []

    issues_by_photo: dict[int, list[DetectedIssue]] = {}
    for issue in issues:
        if issue.annotations or issue.bbox:
            issues_by_photo.setdefault(issue.photoIndex, []).append(issue)

    for index, original_path in enumerate(original_paths):
        output_path = output_dir / f"{filename_prefix}_photo-{index + 1}.jpg"
        with Image.open(original_path) as image:
            canvas = image.convert("RGB")
            draw = ImageDraw.Draw(canvas)
            marker_font = _load_font(16)

            for marker_number, issue in enumerate(issues_by_photo.get(index, []), start=1):
                _draw_issue(draw, issue, marker_number, marker_font)

            canvas.save(output_path, format="JPEG", quality=92, optimize=True)
        annotated_paths.append(output_path)

    return annotated_paths


def _draw_issue(
    draw: ImageDraw.ImageDraw,
    issue: DetectedIssue,
    marker_number: int,
    marker_font: ImageFont.ImageFont,
) -> None:
    if issue.annotations:
        for annotation in issue.annotations:
            _draw_box_with_marker(draw, annotation.bbox, annotation.markerNumber, marker_font)
        return

    if not issue.bbox:
        return

    _draw_box_with_marker(draw, issue.bbox, marker_number, marker_font)


def _draw_box_with_marker(
    draw: ImageDraw.ImageDraw,
    bbox: BoundingBox,
    marker_number: int,
    marker_font: ImageFont.ImageFont,
) -> None:
    x1 = bbox.x
    y1 = bbox.y
    x2 = bbox.x + bbox.width
    y2 = bbox.y + bbox.height

    _draw_dashed_rectangle(draw, (x1, y1, x2, y2), ANNOTATION_COLOR)

    marker_radius = 13
    marker_x = max(x1, marker_radius + 2)
    marker_y = max(y1, marker_radius + 2)
    draw.ellipse(
        (
            marker_x - marker_radius,
            marker_y - marker_radius,
            marker_x + marker_radius,
            marker_y + marker_radius,
        ),
        fill=ANNOTATION_COLOR,
    )
    draw.text((marker_x - 5, marker_y - 9), str(marker_number), fill="white", font=marker_font)


def _draw_dashed_rectangle(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    color: str,
    dash_length: int = 6,
    gap_length: int = 4,
    width: int = 2,
) -> None:
    x1, y1, x2, y2 = box
    _draw_dashed_line(draw, (x1, y1), (x2, y1), color, dash_length, gap_length, width)
    _draw_dashed_line(draw, (x2, y1), (x2, y2), color, dash_length, gap_length, width)
    _draw_dashed_line(draw, (x2, y2), (x1, y2), color, dash_length, gap_length, width)
    _draw_dashed_line(draw, (x1, y2), (x1, y1), color, dash_length, gap_length, width)


def _draw_dashed_line(
    draw: ImageDraw.ImageDraw,
    start: tuple[int, int],
    end: tuple[int, int],
    color: str,
    dash_length: int,
    gap_length: int,
    width: int,
) -> None:
    x1, y1 = start
    x2, y2 = end
    horizontal = y1 == y2
    total_length = abs(x2 - x1) if horizontal else abs(y2 - y1)
    direction = 1 if (x2 >= x1 if horizontal else y2 >= y1) else -1
    position = 0

    while position < total_length:
        dash_end = min(position + dash_length, total_length)
        if horizontal:
            draw.line(
                ((x1 + direction * position, y1), (x1 + direction * dash_end, y1)),
                fill=color,
                width=width,
            )
        else:
            draw.line(
                ((x1, y1 + direction * position), (x1, y1 + direction * dash_end)),
                fill=color,
                width=width,
            )
        position += dash_length + gap_length


def _load_font(size: int) -> ImageFont.ImageFont:
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        return ImageFont.load_default()
