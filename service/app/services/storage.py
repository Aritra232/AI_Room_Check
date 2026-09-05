from pathlib import Path

from fastapi import HTTPException, UploadFile


ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}


async def save_uploads(files: list[UploadFile], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    saved_paths: list[Path] = []

    for index, file in enumerate(files):
        if file.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"{file.filename} must be a JPG, PNG, or WEBP image.",
            )

        extension = _extension_for(file)
        output_path = output_dir / f"photo-{index + 1}{extension}"
        contents = await file.read()
        output_path.write_bytes(contents)
        saved_paths.append(output_path)

    return saved_paths


def _extension_for(file: UploadFile) -> str:
    filename = file.filename or ""
    suffix = Path(filename).suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".webp"}:
        return ".jpg" if suffix == ".jpeg" else suffix
    if file.content_type == "image/png":
        return ".png"
    if file.content_type == "image/webp":
        return ".webp"
    return ".jpg"
