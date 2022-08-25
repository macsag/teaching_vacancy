from typing import List, Optional

from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorClient

from app.commons.mongo_helpers.db import get_mongo_client
from app.commons.mongo_helpers.crud import do_find
from app.models.offers import OfferOut


router = APIRouter(tags=["offers"])


@router.get("/api/offers", response_model=List[OfferOut])
async def get_offers(
        subject: Optional[str] = None,
        limit: int = 10,
        mongo_client: AsyncIOMotorClient = Depends(get_mongo_client)
        ):

    async with await mongo_client.start_session() as s:
        result = await do_find(mongo_client,
                               s,
                               'mbop',
                               'offers',
                               {'subject': subject} if subject else None,
                               limit=limit)

        return [OfferOut.from_mongo(offer) for offer in result]
