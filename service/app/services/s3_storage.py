import asyncio
from pathlib import Path

from service.app.config import settings


def _client():
    import boto3

    return boto3.client(
        "s3",
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.s3_region,
    )


async def upload_annotated_images(
    paths: list[Path],
    user_id: str,
    room_id: str,
    analysis_id: str,
) -> list[str]:
    return await asyncio.to_thread(
        _upload_annotated_images,
        paths,
        user_id,
        room_id,
        analysis_id,
    )


def _upload_annotated_images(
    paths: list[Path],
    user_id: str,
    room_id: str,
    analysis_id: str,
) -> list[str]:
    client = _client()
    urls = []

    for index, path in enumerate(paths, start=1):
        key = f"users/{user_id}/rooms/{room_id}/{analysis_id}/annotated/photo-{index}.jpg"
        client.upload_file(
            str(path),
            settings.aws_s3_bucket_name,
            key,
            ExtraArgs={"ContentType": "image/jpeg"},
        )
        urls.append(_s3_url(key))

    return urls


def _s3_url(key: str) -> str:
    return (
        f"https://{settings.aws_s3_bucket_name}.s3."
        f"{settings.s3_region}.amazonaws.com/{key}"
    )
