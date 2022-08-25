from motor.motor_asyncio import AsyncIOMotorClient

from app.commons.mongo_helpers.db import db


async def connect_to_mongo():

async def close_mongo_connection():
    db.client.close()