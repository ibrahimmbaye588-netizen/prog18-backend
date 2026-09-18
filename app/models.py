from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Text
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


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    utilisateur_id = Column(Integer, ForeignKey("utilisateurs.id"), nullable=False, index=True)
    nom = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    prix = Column(Numeric(10, 2), nullable=False, default=0)
    quantite_stock = Column(Integer, nullable=False, default=0)
    photo_url = Column(String, nullable=True)
    cree_le = Column(DateTime(timezone=True), server_default=func.now())
    modifie_le = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    proprietaire = relationship("Utilisateur", back_populates="articles")
