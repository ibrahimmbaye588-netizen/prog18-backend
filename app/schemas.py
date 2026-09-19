from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from decimal import Decimal


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


class ArticleEntree(BaseModel):
    nom: str
    description: str | None = None
    prix: Decimal = Decimal("0")
    quantite_stock: int = 0
    photo_url: str | None = None


class ArticleMiseAJour(BaseModel):
    nom: str | None = None
    description: str | None = None
    prix: Decimal | None = None
    quantite_stock: int | None = None
    photo_url: str | None = None


class ArticleSortie(BaseModel):
    id: int
    nom: str
    description: str | None = None
    prix: Decimal
    quantite_stock: int
    photo_url: str | None = None
    cree_le: datetime
    modifie_le: datetime

    class Config:
        from_attributes = True


# --- Devis ------------------------------------------------------------

class LigneDevisEntree(BaseModel):
    article_id: int | None = None
    designation: str
    quantite: int = 1
    prix_unitaire: Decimal = Decimal("0")


class LigneDevisSortie(BaseModel):
    id: int
    article_id: int | None = None
    designation: str
    quantite: int
    prix_unitaire: Decimal

    class Config:
        from_attributes = True


class DevisEntree(BaseModel):
    client_nom: str
    statut: str = "brouillon"
    notes: str | None = None
    lignes: list[LigneDevisEntree] = []


class DevisMiseAJour(BaseModel):
    client_nom: str | None = None
    statut: str | None = None
    notes: str | None = None
    lignes: list[LigneDevisEntree] | None = None


class DevisSortie(BaseModel):
    id: int
    client_nom: str
    statut: str
    notes: str | None = None
    lignes: list[LigneDevisSortie]
    cree_le: datetime
    modifie_le: datetime

    class Config:
        from_attributes = True


# --- Stock ------------------------------------------------------------

class MouvementStockEntree(BaseModel):
    article_id: int
    type: str  # entree | sortie
    quantite: int
    motif: str | None = None

    @field_validator("type")
    @classmethod
    def valider_type(cls, valeur: str) -> str:
        if valeur not in ("entree", "sortie"):
            raise ValueError("type doit être 'entree' ou 'sortie'")
        return valeur

    @field_validator("quantite")
    @classmethod
    def valider_quantite(cls, valeur: int) -> int:
        if valeur <= 0:
            raise ValueError("quantite doit être positive")
        return valeur


class MouvementStockSortie(BaseModel):
    id: int
    article_id: int
    article_nom: str | None = None
    type: str
    quantite: int
    motif: str | None = None
    cree_le: datetime

    class Config:
        from_attributes = True
