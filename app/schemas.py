from pydantic import BaseModel, EmailStr
from datetime import datetime


class InscriptionEntree(BaseModel):
    email: EmailStr
    mot_de_passe: str
    nom_entreprise: str | None = None


class ConnexionEntree(BaseModel):
    email: EmailStr
    mot_de_passe: str


class UtilisateurSortie(BaseModel):
    id: int
    email: EmailStr
    nom_entreprise: str | None = None
    cree_le: datetime

    class Config:
        from_attributes = True


class TokenSortie(BaseModel):
    access_token: str
    token_type: str = "bearer"
