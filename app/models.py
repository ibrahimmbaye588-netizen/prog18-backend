from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Utilisateur(Base):
    __tablename__ = "utilisateurs"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    mot_de_passe_hash = Column(String, nullable=False)
    nom_entreprise = Column(String, nullable=True)
    cree_le = Column(DateTime(timezone=True), server_default=func.now())

    articles = relationship("Article", back_populates="proprietaire", cascade="all, delete-orphan")
    devis = relationship("Devis", back_populates="proprietaire", cascade="all, delete-orphan")
    mouvements_stock = relationship(
        "MouvementStock", back_populates="proprietaire", cascade="all, delete-orphan"
    )
    clients = relationship("Client", back_populates="proprietaire", cascade="all, delete-orphan")
    ventes = relationship("Vente", back_populates="proprietaire", cascade="all, delete-orphan")
    paiements = relationship("Paiement", back_populates="proprietaire", cascade="all, delete-orphan")


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    utilisateur_id = Column(Integer, ForeignKey("utilisateurs.id"), nullable=False, index=True)
    reference = Column(String, nullable=True)
    nom = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    prix_achat = Column(Numeric(10, 2), nullable=False, default=0)
    prix = Column(Numeric(10, 2), nullable=False, default=0)  # prix de vente
    quantite_stock = Column(Integer, nullable=False, default=0)
    seuil_alerte = Column(Integer, nullable=False, default=5)
    photo_url = Column(String, nullable=True)
    cree_le = Column(DateTime(timezone=True), server_default=func.now())
    modifie_le = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    proprietaire = relationship("Utilisateur", back_populates="articles")
    mouvements_stock = relationship(
        "MouvementStock", back_populates="article", cascade="all, delete-orphan"
    )


class Devis(Base):
    __tablename__ = "devis"

    id = Column(Integer, primary_key=True, index=True)
    utilisateur_id = Column(Integer, ForeignKey("utilisateurs.id"), nullable=False, index=True)
    client_nom = Column(String, nullable=False)
    statut = Column(String, nullable=False, default="brouillon")
    notes = Column(Text, nullable=True)
    stock_deduit = Column(Boolean, nullable=False, default=False)
    cree_le = Column(DateTime(timezone=True), server_default=func.now())
    modifie_le = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    proprietaire = relationship("Utilisateur", back_populates="devis")
    lignes = relationship(
        "LigneDevis", back_populates="devis", cascade="all, delete-orphan", order_by="LigneDevis.id"
    )


class LigneDevis(Base):
    __tablename__ = "lignes_devis"

    id = Column(Integer, primary_key=True, index=True)
    devis_id = Column(Integer, ForeignKey("devis.id"), nullable=False, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=True)
    designation = Column(String, nullable=False)
    quantite = Column(Integer, nullable=False, default=1)
    prix_unitaire = Column(Numeric(10, 2), nullable=False, default=0)

    devis = relationship("Devis", back_populates="lignes")


class MouvementStock(Base):
    __tablename__ = "mouvements_stock"

    id = Column(Integer, primary_key=True, index=True)
    utilisateur_id = Column(Integer, ForeignKey("utilisateurs.id"), nullable=False, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False, index=True)
    type = Column(String, nullable=False)  # entree | sortie
    quantite = Column(Integer, nullable=False)
    motif = Column(String, nullable=True)
    cree_le = Column(DateTime(timezone=True), server_default=func.now())

    proprietaire = relationship("Utilisateur", back_populates="mouvements_stock")
    article = relationship("Article", back_populates="mouvements_stock")


class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    utilisateur_id = Column(Integer, ForeignKey("utilisateurs.id"), nullable=False, index=True)
    nom = Column(String, nullable=False)
    telephone = Column(String, nullable=True)
    adresse = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    cree_le = Column(DateTime(timezone=True), server_default=func.now())

    proprietaire = relationship("Utilisateur", back_populates="clients")
    ventes = relationship("Vente", back_populates="client")
    paiements = relationship("Paiement", back_populates="client", cascade="all, delete-orphan")


class Paiement(Base):
    """Paiement reçu d'un client, en règlement d'une dette (vente à crédit)."""

    __tablename__ = "paiements"

    id = Column(Integer, primary_key=True, index=True)
    utilisateur_id = Column(Integer, ForeignKey("utilisateurs.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False, index=True)
    montant = Column(Numeric(10, 2), nullable=False)
    motif = Column(String, nullable=True)
    cree_le = Column(DateTime(timezone=True), server_default=func.now())

    proprietaire = relationship("Utilisateur", back_populates="paiements")
    client = relationship("Client", back_populates="paiements")


class Vente(Base):
    """Une vente réelle au comptoir (caisse) : déduit le stock immédiatement,
    à la différence d'un Devis qui reste un document proposé au client."""

    __tablename__ = "ventes"

    id = Column(Integer, primary_key=True, index=True)
    utilisateur_id = Column(Integer, ForeignKey("utilisateurs.id"), nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    client_nom_libre = Column(String, nullable=True)  # si vente sans client enregistré
    mode_paiement = Column(String, nullable=False, default="comptant")  # comptant | credit
    montant_paye = Column(Numeric(10, 2), nullable=False, default=0)
    cree_le = Column(DateTime(timezone=True), server_default=func.now())

    proprietaire = relationship("Utilisateur", back_populates="ventes")
    client = relationship("Client", back_populates="ventes")
    lignes = relationship(
        "LigneVente", back_populates="vente", cascade="all, delete-orphan", order_by="LigneVente.id"
    )


class LigneVente(Base):
    __tablename__ = "lignes_vente"

    id = Column(Integer, primary_key=True, index=True)
    vente_id = Column(Integer, ForeignKey("ventes.id"), nullable=False, index=True)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=True)
    designation = Column(String, nullable=False)
    quantite = Column(Integer, nullable=False, default=1)
    prix_unitaire = Column(Numeric(10, 2), nullable=False, default=0)
    prix_achat_unitaire = Column(Numeric(10, 2), nullable=False, default=0)  # copié au moment de la vente

    vente = relationship("Vente", back_populates="lignes")
