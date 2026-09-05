import json
from pathlib import Path

from motor.motor_asyncio import AsyncIOMotorClient

from service.app.config import settings


client = AsyncIOMotorClient(settings.database_url, serverSelectionTimeoutMS=1000)
db = client[settings.database_name]
fallback_dir = settings.storage_dir / "db-fallback"


async def save_room_analysis(user_id: str, room_id: str, payload: dict) -> None:
    try:
        await db.room_analyses.update_one(
            {"userId": user_id, "roomId": room_id},
            {"$set": payload},
            upsert=True,
        )
    except Exception:
        _write_json(_fallback_path("analysis", user_id, room_id), payload)


async def get_room_analysis(user_id: str, room_id: str) -> dict | None:
    try:
        analysis = await db.room_analyses.find_one(
            {"userId": user_id, "roomId": room_id},
            {"_id": 0},
        )
        if analysis:
            return analysis
    except Exception:
        pass

    path = _fallback_path("analysis", user_id, room_id)
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


async def save_room_confirmation(user_id: str, room_id: str, payload: dict) -> None:
    confirmation = {"userId": user_id, "roomId": room_id, **payload}
    try:
        await db.room_confirmations.update_one(
            {"userId": user_id, "roomId": room_id},
            {"$set": confirmation},
            upsert=True,
        )
    except Exception:
        _write_json(_fallback_path("confirmation", user_id, room_id), confirmation)


def _fallback_path(kind: str, user_id: str, room_id: str) -> Path:
    return fallback_dir / kind / user_id / f"{room_id}.json"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
