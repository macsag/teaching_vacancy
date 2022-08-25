from app.models.mongo_models import MongoModel


class OfferBase(MongoModel):
    ext_id: str
    type: str
    administration: str
    name: str
    city: str
    street: str
    house_number: str
    postal_code: str
    phone_number: str
    email: str
    subject: str
    time: str
    type_of_employment: str
    date_added: str
    date_of_expiration: str

    def to_notification_string(self):
        return f'{self.subject} | {self.type} | {self.name} | {self.city}, {self.street} {self.house_number}\n' \
               f'<a href="https://mbopn.kuratorium.waw.pl/#/oferta/{self.ext_id}">Przejdź do oferty</a>'


class OfferOut(OfferBase):
    id: str
