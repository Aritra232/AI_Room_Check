from motor.motor_asyncio import AsyncIOMotorClient

from service.app.config import settings


client = AsyncIOMotorClient(
    settings.database_url,
    serverSelectionTimeoutMS=10000,
    connectTimeoutMS=10000,
    socketTimeoutMS=20000,
)
db = client[settings.database_name]


async def save_room_analysis(user_id: str, room_id: str, payload: dict) -> None:
    await db.room_analyses.update_one(
        {"userId": user_id, "roomId": room_id},
        {"$set": payload},
        upsert=True,
    )


async def get_room_analysis(user_id: str, room_id: str) -> dict | None:
    return await db.room_analyses.find_one(
        {"userId": user_id, "roomId": room_id},
        {"_id": 0},
    )


async def save_room_confirmation(user_id: str, room_id: str, payload: dict) -> None:
    confirmation = {"userId": user_id, "roomId": room_id, **payload}
    await db.room_confirmations.update_one(
        {"userId": user_id, "roomId": room_id},
        {"$set": confirmation},
        upsert=True,
    )
