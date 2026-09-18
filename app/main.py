import os

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database import engine, get_db, Base
from app.models import Utilisateur
from app.schemas import InscriptionEntree, ConnexionEntree, UtilisateurSortie, TokenSortie
from app.auth import (
    hacher_mot_de_passe,
    verifier_mot_de_passe,
    creer_token_acces,
    obtenir_utilisateur_courant,
)

# Crée les tables si elles n'existent pas encore
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Prog 1.8 API",
    description="API multi-entreprise pour catalogue, devis et stock (quincaillerie/vitrerie).",
    version="0.1.0",
)

# --- CORS ---------------------------------------------------------------
# Liste des origines autorisées. En local (Vite/CRA) + le frontend Vercel.
# Ajoute ici toute nouvelle URL de prévisualisation Vercel si besoin,
# ou utilise une regex pour couvrir tous les sous-domaines de prévisualisation.
ORIGINES_AUTORISEES = [
    "http://localhost:5173",
    "http://localhost:3000",
    os.environ.get("FRONTEND_URL", ""),  # ex: https://prog18-frontend.vercel.app
]
ORIGINES_AUTORISEES = [o for o in ORIGINES_AUTORISEES if o]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINES_AUTORISEES,
    allow_origin_regex=r"https://prog18-frontend.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    """Endpoint simple pour vérifier que le service est réveillé et répond."""
    return {"status": "ok"}


@app.post("/auth/inscription", response_model=UtilisateurSortie, status_code=status.HTTP_201_CREATED)
def inscription(donnees: InscriptionEntree, db: Session = Depends(get_db)):
    existant = db.query(Utilisateur).filter(Utilisateur.email == donnees.email).first()
    if existant:
        raise HTTPException(status_code=400, detail="Un compte existe déjà avec cet email")

    utilisateur = Utilisateur(
        email=donnees.email,
        mot_de_passe_hash=hacher_mot_de_passe(donnees.mot_de_passe),
        nom_entreprise=donnees.nom_entreprise,
    )
    db.add(utilisateur)
    db.commit()
    db.refresh(utilisateur)
    return utilisateur


@app.post("/auth/connexion", response_model=TokenSortie)
def connexion(donnees: ConnexionEntree, db: Session = Depends(get_db)):
    utilisateur = db.query(Utilisateur).filter(Utilisateur.email == donnees.email).first()
    if not utilisateur or not verifier_mot_de_passe(donnees.mot_de_passe, utilisateur.mot_de_passe_hash):
        raise HTTPException(status_code=401, detail="Email ou mot de passe incorrect")

    token = creer_token_acces({"sub": utilisateur.email})
    return TokenSortie(access_token=token)


@app.get("/auth/moi", response_model=UtilisateurSortie)
def moi(utilisateur_courant: Utilisateur = Depends(obtenir_utilisateur_courant)):
    return utilisateur_courant
