from csvImporter.model import CsvModel
# from rapidsms.models import Contact
from csvImporter.fields import *


class ContactCSvModel(CsvModel):
    college = CharField()
    name = CharField()
    cellphone = CharField()

    class Meta:
        delimiter = ";"