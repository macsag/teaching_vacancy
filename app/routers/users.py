from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorClient

from app.commons.mongo_helpers.db import get_mongo_client
from app.commons.mongo_helpers.crud import do_insert_one
from app.models.users import UserBase


router = APIRouter(tags=["users"])


@router.post("/api/users/", response_model=UserBase)
async def create_user(user: UserBase, mongo_client: AsyncIOMotorClient = Depends(get_mongo_client)):
    async with await mongo_client.start_session() as s:
        result = await do_insert_one(mongo_client,
                                     s,
                                     'mbop',
                                     'users',
                                     user.dict())
        return user
