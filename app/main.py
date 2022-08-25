import logging

from fastapi import FastAPI
from fastapi_utils.tasks import repeat_every
import uvicorn

from motor.motor_asyncio import AsyncIOMotorClient

from app.applog.utils import read_logging_config, setup_logging
from app.commons.mongo_helpers.db_utils import connect_to_mongo, close_mongo_connection
from app.commons.mongo_helpers.db import get_mongo_client
from app.synchronizers.mbop import MbopSynchronizer
from app.senders.notification import MailNotificationSender
from app.routers import offers as offers_router
from app.routers import users as users_router

logger = logging.getLogger(__name__)

app = FastAPI()


app.include_router(offers_router.router)
app.include_router(users_router.router)


@app.on_event("startup")
async def startup():
    # setup logging
    logconfig_dict = read_logging_config('applog/logging.yml')
    setup_logging(logconfig_dict)

    # setup async mongodb connection
    await connect_to_mongo()

    # instantiate synchronizers
    global mbop_synchronizer
    mbop_synchronizer = MbopSynchronizer(await get_mongo_client())

    # instantiate senders
    global mail_notification_sender
    mail_notification_sender = MailNotificationSender(await get_mongo_client())


@app.on_event("startup")
@repeat_every(seconds=60 * 30, raise_exceptions=True)  # 30 minutes
async def synchronize_with_mbop_task() -> None:
    #await mbop_synchronizer.synchronize()
    pass

@app.on_event("startup")
@repeat_every(seconds=60, raise_exceptions=True)  # 24 hours
async def send_notifications():
    await mail_notification_sender.send_notifications()


@app.on_event("shutdown")
async def shutdown():
    await close_mongo_connection()


@app.get("/")
async def root():
    return {"message": "Hello Bigger Applications!"}

if __name__ == '__main__':

    uvicorn.run('main:app', host='localhost', port=9999, log_config=None)
