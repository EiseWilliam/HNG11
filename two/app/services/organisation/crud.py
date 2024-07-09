from fastcrud import FastCRUD

from app.services.organisation.model import Organisation



CRUDORG = FastCRUD
org_handler = CRUDORG(Organisation)
