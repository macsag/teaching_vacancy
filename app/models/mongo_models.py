from pydantic import BaseModel, BaseConfig


class MongoModel(BaseModel):

    class Config(BaseConfig):
        allow_population_by_field_name = True

    @classmethod
    def from_mongo(cls, data: dict):
        """We must convert _id into "id". """
        if not data:
            return data
        id = data.pop('_id', None)
        return cls(**dict(data, id=str(id)))