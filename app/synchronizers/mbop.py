import logging
from typing import List
import time

from selenium import webdriver
from bs4 import BeautifulSoup
from motor.motor_asyncio import AsyncIOMotorClient

from app.commons.mongo_helpers.crud import do_upsert_many
from app.models.offers import OfferBase


BASE_URL = 'https://mbopn.kuratorium.waw.pl/'
FIRST_PAGE = 'https://mbopn.kuratorium.waw.pl/#/'
NEXT_PAGE_PATTERN_SUFFIX = 'page/'


logger = logging.getLogger(__name__)


class MbopSynchronizer(object):
    def __init__(self, mongo_client: AsyncIOMotorClient):
        self._mongo_client = mongo_client
        self._driver = webdriver.Chrome(executable_path=r'C:\WebDriver\bin\chromedriver.exe')

    async def _get_synchronization_state(self) -> bool:
        return False

    async def _set_synchronization_state(self, state: bool) -> None:
        pass

    @staticmethod
    def _parse_single_offer(source_html: str, offer_ext_id: str) -> OfferBase:
        soup = BeautifulSoup(source_html, 'lxml')
        offer_metadata = [td.string.strip() for td in soup.select('fieldset td') if td.string]

        return OfferBase(ext_id=offer_ext_id,
                         type=offer_metadata[1],
                         administration=offer_metadata[3],
                         name=offer_metadata[5],
                         city=offer_metadata[7],
                         street=offer_metadata[9],
                         house_number=offer_metadata[11],
                         postal_code=offer_metadata[13],
                         phone_number=offer_metadata[15],
                         email=offer_metadata[17],
                         subject=offer_metadata[19],
                         time=(offer_metadata[21]),
                         type_of_employment=offer_metadata[23],
                         date_added=offer_metadata[25],
                         date_of_expiration=offer_metadata[27])

    def _get_page(self, url: str) -> str:
        self._driver.get(url)
        time.sleep(1)
        return self._driver.page_source

    @staticmethod
    def _get_list_of_offers_links(source_html: str) -> List[str]:
        soup = BeautifulSoup(source_html, 'lxml')
        offers_links = [a['href'] for a in soup.find_all('a', href=True) if 'oferta' in a['href']]
        return offers_links

    def _get_first_page(self) -> str:
        return self._get_page(FIRST_PAGE)

    def _get_next_page(self, counter: int) -> str:
        return self._get_page(f'{FIRST_PAGE}{NEXT_PAGE_PATTERN_SUFFIX}{str(counter)}')

    async def _upsert_list_of_offers_to_db(self, list_of_offers: list) -> bool:
        async with await self._mongo_client.start_session() as s:
            result = await do_upsert_many(self._mongo_client,
                                          s,
                                          'mbop',
                                          'offers',
                                          [offer.dict() for offer in list_of_offers])

        # return True if some offers were already in db
        # return False if all of the offers were new
        return True if result.modified_count != 0 else False

    async def synchronize(self):
        is_synchronization_in_progress = await self._get_synchronization_state()

        if is_synchronization_in_progress:
            logger.info('Synchronization in progress...')
        else:
            logger.info('Starting synchronization...')
            await self._set_synchronization_state(True)
            logger.info('Synchronization state set to true.')

            counter = 1
            is_there_any_links = True
            is_already_in_db = False

            # fetch and insert only the new offers, update only as few as possible
            # first synchronization should fetch all existing offers
            while is_there_any_links and not is_already_in_db:
                list_of_offers_links = []
                parsed_offers = []

                logger.info(f'Fetching links from page {counter}...')
                if counter == 1:
                    first_page = self._get_first_page()
                    list_of_offers_links.extend(self._get_list_of_offers_links(first_page))
                    for num, link_to_offer in enumerate(list_of_offers_links):
                        logger.info(f'Fetching and parsing single offer {counter}/{num}...')
                        offer_page = self._get_page(f'{BASE_URL}{link_to_offer}')
                        parsed_offer = self._parse_single_offer(offer_page, link_to_offer.split('/')[-1])
                        parsed_offers.append(parsed_offer)
                    logger.info('Upserting in database...')
                    is_already_in_db = await self._upsert_list_of_offers_to_db(parsed_offers)
                    logger.info('Done.')

                if counter > 1:
                    next_page = self._get_next_page(counter)
                    list_of_offers_links.extend(self._get_list_of_offers_links(next_page))
                    for num, link_to_offer in enumerate(list_of_offers_links):
                        logger.info(f'Fetching and parsing single offer {counter}/{num}...')
                        offer_page = self._get_page(f'{BASE_URL}{link_to_offer}')
                        parsed_offers.append(self._parse_single_offer(offer_page, link_to_offer.split('/')[-1]))
                    logger.info('Upserting in database...')
                    is_already_in_db = await self._upsert_list_of_offers_to_db(parsed_offers)
                    logger.info('Done.')

                counter += 1
                if 0 <= len(list_of_offers_links) < 10:
                    is_there_any_links = False
