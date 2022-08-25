from typing import List, Tuple

from pymongo import ReplaceOne, ASCENDING, DESCENDING
from pymongo.results import BulkWriteResult
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorClientSession


def prepare_requests_for_bulk_operation(
        list_of_tuples_with_request_type_and_documents: List[Tuple[type, List[Tuple]]]
        ):

    result = []

    for tuple_with_request_type_and_documents in list_of_tuples_with_request_type_and_documents:
        for args_tuple in tuple_with_request_type_and_documents[1]:
            operation_to_add = tuple_with_request_type_and_documents[0](*args_tuple)
            result.append(operation_to_add)

    return result


async def do_find(
        mongo_client: AsyncIOMotorClient,
        session: AsyncIOMotorClientSession,
        db_to_get: str,
        collection_to_get: str,
        query: dict = None,
        sort: str = '_id',
        sort_direction: str = 'ASC',
        skip: int = 0,
        limit: int = 10
        ):

    db = mongo_client[db_to_get]
    collection = db[collection_to_get]

    if query:
        cursor = collection.find(query,
                                 session=session,
                                 skip=skip).sort(sort,
                                                 ASCENDING if sort_direction == 'ASC' else DESCENDING)
    else:
        cursor = collection.find(session=session,
                                 skip=skip).sort(sort,
                                                 ASCENDING if sort_direction == 'ASC' else DESCENDING)

    return await cursor.to_list(length=limit)


async def do_insert_one(
        mongo_client: AsyncIOMotorClient,
        session: AsyncIOMotorClientSession,
        db_to_get: str,
        collection_to_get: str,
        document: dict
        ):

    db = mongo_client[db_to_get]
    collection = db[collection_to_get]

    result = await collection.insert_one(document, session=session)
    return result


async def do_upsert_many(
        mongo_client: AsyncIOMotorClient,
        session: AsyncIOMotorClientSession,
        db_to_get: str,
        collection_to_get: str,
        list_of_documents: List[dict]
        ) -> BulkWriteResult:

    db = mongo_client[db_to_get]
    collection = db[collection_to_get]

    list_of_args_tuples = [({'ext_id': document.get('ext_id')}, document, True) for document in list_of_documents]
    requests_to_prepare = [(ReplaceOne, list_of_args_tuples)]
    prepared_requests = prepare_requests_for_bulk_operation(requests_to_prepare)

    result = await collection.bulk_write(prepared_requests, session=session)

    return result
