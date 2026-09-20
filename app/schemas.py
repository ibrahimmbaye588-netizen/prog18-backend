from pydantic import BaseModel, EmailStr, field_validator
from datetime import datetime
from decimal import Decimal

# Moyens de paiement acceptés (distinct de mode_paiement : comptant | credit)
MOYENS_PAIEMENT = ("especes", "mobile_money", "carte", "virement", "cheque")


def _valider_moyen_paiement(valeur: str) -> str:
    if valeur not in MOYENS_PAIEMENT:
        raise ValueError(f"moyen_paiement doit être l'un de : {', '.join(MOYENS_PAIEMENT)}")
    return valeur


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


class UtilisateurMiseAJour(BaseModel):
    nom_entreprise: str | None = None


class TokenSortie(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ArticleEntree(BaseModel):
    reference: str | None = None
    nom: str
    description: str | None = None
    prix_achat: Decimal = Decimal("0")
    prix: Decimal = Decimal("0")
    quantite_stock: int = 0
    seuil_alerte: int = 5
    photo_url: str | None = None


class ArticleMiseAJour(BaseModel):
    reference: str | None = None
    nom: str | None = None
    description: str | None = None
    prix_achat: Decimal | None = None
    prix: Decimal | None = None
    quantite_stock: int | None = None
    seuil_alerte: int | None = None
    photo_url: str | None = None


class ArticleSortie(BaseModel):
    id: int
    reference: str | None = None
    nom: str
    description: str | None = None
    prix_achat: Decimal
    prix: Decimal
    quantite_stock: int
    seuil_alerte: int
    photo_url: str | None = None
    cree_le: datetime
    modifie_le: datetime

    class Config:
        from_attributes = True


class PhotoResultat(BaseModel):
    url: str
    miniature: str
    photographe: str | None = None


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
    stock_deduit: bool
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


# --- Clients ------------------------------------------------------------

class ClientEntree(BaseModel):
    nom: str
    telephone: str | None = None
    adresse: str | None = None
    notes: str | None = None


class ClientMiseAJour(BaseModel):
    nom: str | None = None
    telephone: str | None = None
    adresse: str | None = None
    notes: str | None = None


class ClientSortie(BaseModel):
    id: int
    nom: str
    telephone: str | None = None
    adresse: str | None = None
    notes: str | None = None
    solde_du: Decimal = Decimal("0")
    cree_le: datetime

    class Config:
        from_attributes = True


class PaiementEntree(BaseModel):
    montant: Decimal
    moyen_paiement: str = "especes"
    motif: str | None = None

    @field_validator("moyen_paiement")
    @classmethod
    def valider_moyen(cls, valeur: str) -> str:
        return _valider_moyen_paiement(valeur)

    @field_validator("montant")
    @classmethod
    def valider_montant(cls, valeur: Decimal) -> Decimal:
        if valeur <= 0:
            raise ValueError("montant doit être positif")
        return valeur


class PaiementSortie(BaseModel):
    id: int
    client_id: int
    montant: Decimal
    moyen_paiement: str
    motif: str | None = None
    cree_le: datetime

    class Config:
        from_attributes = True


# --- Ventes (caisse) ------------------------------------------------------

class LigneVenteEntree(BaseModel):
    article_id: int | None = None
    designation: str
    quantite: int = 1
    prix_unitaire: Decimal = Decimal("0")


class LigneVenteSortie(BaseModel):
    id: int
    article_id: int | None = None
    designation: str
    quantite: int
    prix_unitaire: Decimal
    prix_achat_unitaire: Decimal

    class Config:
        from_attributes = True


class VenteEntree(BaseModel):
    client_id: int | None = None
    client_nom_libre: str | None = None
    mode_paiement: str = "comptant"  # comptant | credit
    montant_paye: Decimal = Decimal("0")
    moyen_paiement: str = "especes"
    lignes: list[LigneVenteEntree]

    @field_validator("moyen_paiement")
    @classmethod
    def valider_moyen(cls, valeur: str) -> str:
        return _valider_moyen_paiement(valeur)

    @field_validator("mode_paiement")
    @classmethod
    def valider_mode(cls, valeur: str) -> str:
        if valeur not in ("comptant", "credit"):
            raise ValueError("mode_paiement doit être 'comptant' ou 'credit'")
        return valeur


class VenteSortie(BaseModel):
    id: int
    client_id: int | None = None
    client_nom_libre: str | None = None
    mode_paiement: str
    montant_paye: Decimal
    moyen_paiement: str
    lignes: list[LigneVenteSortie]
    cree_le: datetime

    class Config:
        from_attributes = True


# --- Tableau de bord ------------------------------------------------------

class ArticleAlerte(BaseModel):
    id: int
    nom: str
    quantite_stock: int
    seuil_alerte: int


class TableauDeBordResume(BaseModel):
    chiffre_affaires_jour: Decimal
    ventes_jour: int
    benefice_estime_jour: Decimal
    nombre_produits: int
    nombre_clients: int
    produits_presque_epuises: list[ArticleAlerte]
