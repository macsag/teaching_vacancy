import logging
from typing import List
import time
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from motor.motor_asyncio import AsyncIOMotorClient

from app.commons.mongo_helpers.crud import do_find
from app.models.offers import OfferOut
from app.models.users import UserOut


logger = logging.getLogger(__name__)

PORT = 465


class MailNotificationSender(object):
    def __init__(self, mongo_client: AsyncIOMotorClient):
        self._mongo_client = mongo_client
        self._last_sent = None

    async def _get_notification_sender_state(self) -> bool:
        return False

    async def _set_notification_sender_state(self, state: bool) -> None:
        pass

    async def _get_users(self):
        async with await self._mongo_client.start_session() as s:
            result = await do_find(self._mongo_client,
                                   s,
                                   'mbop',
                                   'users',
                                   limit=100)

            return [UserOut.from_mongo(user) for user in result]

    async def _get_offers_for_user(self, user: UserOut):
        async with await self._mongo_client.start_session() as s:
            result = await do_find(self._mongo_client,
                                   s,
                                   'mbop',
                                   'offers',
                                   {'subject': {'$in': user.subjects}},
                                   limit=100)

            return [OfferOut.from_mongo(offer) for offer in result]

    @staticmethod
    def _create_mail_message(user, list_of_new_offers_for_user):
        newline = '\n'

        offers_string = newline.join([offer.to_notification_string() for offer in list_of_new_offers_for_user])

        message_content_plain = f'Pojawiły się nowe oferty pracy, które mogą Cię zainteresować:<br><br>' \
                                f'{offers_string}<br><br>' \
                                f'Z poważaniem<br>Twoja Powiadamiaczka<br><br>' \
                                f'Zrezygnuj z subskrypcji'

        ending = '</p></body></html>'
        message_content_html = f'<html><body><p>{message_content_plain}{ending}'

        message = MIMEMultipart("alternative")
        message['Subject'] = 'nowe oferty w Mazowieckim Banku Ofert Pracy dla Nauczycieli'
        message['From'] = MAIL
        message['To'] = user.email

        part1 = MIMEText(message_content_plain, "plain")
        part2 = MIMEText(message_content_html, "html")

        message.attach(part1)
        message.attach(part2)

        return message

    def _send_mail(self, user, list_of_new_offers_for_user):
        context = ssl.create_default_context()

        with smtplib.SMTP_SSL("smtp.gmail.com", PORT, context=context) as server:
            server.login(MAIL, PASSWORD)
            server.send_message(self._create_mail_message(user, list_of_new_offers_for_user))

    async def send_notifications(self):
        is_sending_notifications_in_progress = await self._get_notification_sender_state()

        if is_sending_notifications_in_progress:
            logger.info('Sending mail notifications in progress... Maybe another time.')
        else:
            logger.info('Starting sending mail notifications...')
            await self._set_notification_sender_state(True)
            logger.info('Mail notification sender state set to true.')

            logger.info('Fetching users list...')
            users_to_process = await self._get_users()
            logger.info('Done.')

            for user in users_to_process:
                logger.info(f'Fetching offers for user {user.email}...')
                list_of_new_offers_for_user = await self._get_offers_for_user(user)
                logger.info(f'Done. {list_of_new_offers_for_user}')
                self._send_mail(user, list_of_new_offers_for_user)
