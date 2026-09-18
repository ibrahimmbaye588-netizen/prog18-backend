import os

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload

from app.database import engine, get_db, Base
from app.models import Utilisateur, Article, Devis, LigneDevis
from app.schemas import (
    InscriptionEntree,
    ConnexionEntree,
    UtilisateurSortie,
    TokenSortie,
    ArticleEntree,
    ArticleMiseAJour,
    ArticleSortie,
    DevisEntree,
    DevisMiseAJour,
    DevisSortie,
)
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
    version="0.3.0",
)

# --- CORS ---------------------------------------------------------------
ORIGINES_AUTORISEES = [
    "http://localhost:5173",
    "http://localhost:3000",
    os.environ.get("FRONTEND_URL", ""),
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
    return {"status": "ok"}


# --- Auth -----------------------------------------------------------------

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


# --- Articles ---------------------------------------------------------------

@app.get("/articles", response_model=list[ArticleSortie])
def lister_articles(
    db: Session = Depends(get_db),
    utilisateur_courant: Utilisateur = Depends(obtenir_utilisateur_courant),
):
    return (
        db.query(Article)
        .filter(Article.utilisateur_id == utilisateur_courant.id)
        .order_by(Article.nom)
        .all()
    )


@app.post("/articles", response_model=ArticleSortie, status_code=status.HTTP_201_CREATED)
def creer_article(
    donnees: ArticleEntree,
    db: Session = Depends(get_db),
    utilisateur_courant: Utilisateur = Depends(obtenir_utilisateur_courant),
):
    article = Article(**donnees.model_dump(), utilisateur_id=utilisateur_courant.id)
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


def _obtenir_article_ou_404(article_id: int, db: Session, utilisateur_courant: Utilisateur) -> Article:
    article = (
        db.query(Article)
        .filter(Article.id == article_id, Article.utilisateur_id == utilisateur_courant.id)
        .first()
    )
    if not article:
        raise HTTPException(status_code=404, detail="Article introuvable")
    return article


@app.get("/articles/{article_id}", response_model=ArticleSortie)
def obtenir_article(
    article_id: int,
    db: Session = Depends(get_db),
    utilisateur_courant: Utilisateur = Depends(obtenir_utilisateur_courant),
):
    return _obtenir_article_ou_404(article_id, db, utilisateur_courant)


@app.put("/articles/{article_id}", response_model=ArticleSortie)
def modifier_article(
    article_id: int,
    donnees: ArticleMiseAJour,
    db: Session = Depends(get_db),
    utilisateur_courant: Utilisateur = Depends(obtenir_utilisateur_courant),
):
    article = _obtenir_article_ou_404(article_id, db, utilisateur_courant)
    for champ, valeur in donnees.model_dump(exclude_unset=True).items():
        setattr(article, champ, valeur)
    db.commit()
    db.refresh(article)
    return article


@app.delete("/articles/{article_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_article(
    article_id: int,
    db: Session = Depends(get_db),
    utilisateur_courant: Utilisateur = Depends(obtenir_utilisateur_courant),
):
    article = _obtenir_article_ou_404(article_id, db, utilisateur_courant)
    db.delete(article)
    db.commit()
    return None


# --- Devis --------------------------------------------------------------

def _requete_devis(db: Session, utilisateur_courant: Utilisateur):
    return (
        db.query(Devis)
        .options(joinedload(Devis.lignes))
        .filter(Devis.utilisateur_id == utilisateur_courant.id)
    )


@app.get("/devis", response_model=list[DevisSortie])
def lister_devis(
    db: Session = Depends(get_db),
    utilisateur_courant: Utilisateur = Depends(obtenir_utilisateur_courant),
):
    return _requete_devis(db, utilisateur_courant).order_by(Devis.cree_le.desc()).all()


@app.post("/devis", response_model=DevisSortie, status_code=status.HTTP_201_CREATED)
def creer_devis(
    donnees: DevisEntree,
    db: Session = Depends(get_db),
    utilisateur_courant: Utilisateur = Depends(obtenir_utilisateur_courant),
):
    devis = Devis(
        utilisateur_id=utilisateur_courant.id,
        client_nom=donnees.client_nom,
        statut=donnees.statut,
        notes=donnees.notes,
    )
    for ligne in donnees.lignes:
        devis.lignes.append(LigneDevis(**ligne.model_dump()))

    db.add(devis)
    db.commit()
    db.refresh(devis)
    return devis


def _obtenir_devis_ou_404(devis_id: int, db: Session, utilisateur_courant: Utilisateur) -> Devis:
    devis = (
        _requete_devis(db, utilisateur_courant)
        .filter(Devis.id == devis_id)
        .first()
    )
    if not devis:
        raise HTTPException(status_code=404, detail="Devis introuvable")
    return devis


@app.get("/devis/{devis_id}", response_model=DevisSortie)
def obtenir_devis(
    devis_id: int,
    db: Session = Depends(get_db),
    utilisateur_courant: Utilisateur = Depends(obtenir_utilisateur_courant),
):
    return _obtenir_devis_ou_404(devis_id, db, utilisateur_courant)


@app.put("/devis/{devis_id}", response_model=DevisSortie)
def modifier_devis(
    devis_id: int,
    donnees: DevisMiseAJour,
    db: Session = Depends(get_db),
    utilisateur_courant: Utilisateur = Depends(obtenir_utilisateur_courant),
):
    devis = _obtenir_devis_ou_404(devis_id, db, utilisateur_courant)

    champs = donnees.model_dump(exclude_unset=True, exclude={"lignes"})
    for champ, valeur in champs.items():
        setattr(devis, champ, valeur)

    if donnees.lignes is not None:
        devis.lignes.clear()
        for ligne in donnees.lignes:
            devis.lignes.append(LigneDevis(**ligne.model_dump()))

    db.commit()
    db.refresh(devis)
    return devis


@app.delete("/devis/{devis_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_devis(
    devis_id: int,
    db: Session = Depends(get_db),
    utilisateur_courant: Utilisateur = Depends(obtenir_utilisateur_courant),
):
    devis = _obtenir_devis_ou_404(devis_id, db, utilisateur_courant)
    db.delete(devis)
    db.commit()
    return None
