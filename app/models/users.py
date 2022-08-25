from typing import List

from app.models.mongo_models import MongoModel


class UserBase(MongoModel):
    email: str
    subjects: List[str]
    postal_code: str
    radius: int


class UserOut(UserBase):
    id: str
