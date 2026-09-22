import os
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import requests
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session, joinedload

from app.database import engine, get_db, Base
from app.models import (
    Utilisateur,
    Article,
    Devis,
    LigneDevis,
    MouvementStock,
    Client,
    Paiement,
    Vente,
    LigneVente,
    Facture,
    LigneFacture,
    PaiementFacture,
)
from app.schemas import (
    InscriptionEntree,
    ConnexionEntree,
    UtilisateurSortie,
    UtilisateurMiseAJour,
    TokenSortie,
    ArticleEntree,
    ArticleMiseAJour,
    ArticleSortie,
    PhotoResultat,
    DevisEntree,
    DevisMiseAJour,
    DevisSortie,
    MouvementStockEntree,
    MouvementStockSortie,
    ClientEntree,
    ClientMiseAJour,
    ClientSortie,
    PaiementEntree,
    PaiementSortie,
    VenteEntree,
    VenteSortie,
    FactureEntree,
    FactureMiseAJour,
    FactureSortie,
    FacturePaiementEntree,
    FacturePaiementSortie,
    TableauDeBordResume,
    ArticleAlerte,
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
    description="API multi-entreprise : ventes/caisse, stock, clients, devis.",
    version="0.6.0",
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


@app.put("/auth/moi", response_model=UtilisateurSortie)
def modifier_profil(
    donnees: UtilisateurMiseAJour,
    db: Session = Depends(get_db),
    utilisateur_courant: Utilisateur = Depends(obtenir_utilisateur_courant),
):
    for champ, valeur in donnees.model_dump(exclude_unset=True).items():
        setattr(utilisateur_courant, champ, valeur)
    db.commit()
    db.refresh(utilisateur_courant)
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


# --- Recherche de photos (Pexels) -----------------------------------------

@app.get("/articles-photos", response_model=list[PhotoResultat])
def rechercher_photos(
    q: str,
    utilisateur_courant: Utilisateur = Depends(obtenir_utilisateur_courant),
):
    cle_api = os.environ.get("PEXELS_API_KEY")
    if not cle_api:
        raise HTTPException(
            status_code=503,
            detail="La recherche de photos n'est pas configurée sur le serveur",
        )
    try:
        reponse = requests.get(
            "https://api.pexels.com/v1/search",
            headers={"Authorization": cle_api},
            params={"query": q, "per_page": 8},
            timeout=10,
        )
        reponse.raise_for_status()
    except requests.RequestException:
        raise HTTPException(status_code=502, detail="Impossible de contacter le service de photos")

    donnees = reponse.json()
    return [
        PhotoResultat(
            url=photo["src"]["medium"],
            miniature=photo["src"]["small"],
            photographe=photo.get("photographer"),
        )
        for photo in donnees.get("photos", [])
    ]


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
    try:
        db.flush()
        if devis.statut == "accepte":
            _appliquer_deduction_stock(devis, db, utilisateur_courant)
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(devis)
    return devis


def _obtenir_devis_ou_404(devis_id: int, db: Session, utilisateur_courant: Utilisateur) -> Devis:
    devis = _requete_devis(db, utilisateur_courant).filter(Devis.id == devis_id).first()
    if not devis:
        raise HTTPException(status_code=404, detail="Devis introuvable")
    return devis


def _appliquer_deduction_stock(devis: Devis, db: Session, utilisateur_courant: Utilisateur):
    """Déduit le stock d'un devis accepté.

    Ne fait PAS de commit : c'est l'appelant qui valide la transaction, pour que
    le changement de statut et la déduction réussissent ou échouent ensemble.
    Lève une 400 si le stock est insuffisant.
    """
    if devis.stock_deduit:
        return

    besoins: dict[int, int] = {}
    for ligne in devis.lignes:
        if ligne.article_id:
            besoins[ligne.article_id] = besoins.get(ligne.article_id, 0) + ligne.quantite

    # Ordre stable + verrou de ligne : évite les courses et les deadlocks
    for article_id in sorted(besoins):
        article = (
            db.query(Article)
            .filter(Article.id == article_id, Article.utilisateur_id == utilisateur_courant.id)
            .with_for_update()
            .first()
        )
        if not article:
            continue
        quantite = besoins[article_id]
        if article.quantite_stock < quantite:
            raise HTTPException(
                status_code=400,
                detail=f"Stock insuffisant pour '{article.nom}' : {article.quantite_stock} disponible(s), {quantite} demandé(s)",
            )
        article.quantite_stock -= quantite
        db.add(
            MouvementStock(
                utilisateur_id=utilisateur_courant.id,
                article_id=article.id,
                type="sortie",
                quantite=quantite,
                motif=f"Devis accepté — {devis.client_nom}",
            )
        )
    devis.stock_deduit = True


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

    try:
        if devis.statut == "accepte":
            _appliquer_deduction_stock(devis, db, utilisateur_courant)
        db.commit()
    except Exception:
        db.rollback()
        raise
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


# --- Stock ----------------------------------------------------------------

def _mouvement_vers_sortie(mouvement: MouvementStock) -> MouvementStockSortie:
    return MouvementStockSortie(
        id=mouvement.id,
        article_id=mouvement.article_id,
        article_nom=mouvement.article.nom if mouvement.article else None,
        type=mouvement.type,
        quantite=mouvement.quantite,
        motif=mouvement.motif,
        cree_le=mouvement.cree_le,
    )


@app.get("/stock/mouvements", response_model=list[MouvementStockSortie])
def lister_mouvements(
    article_id: int | None = None,
    db: Session = Depends(get_db),
    utilisateur_courant: Utilisateur = Depends(obtenir_utilisateur_courant),
):
    requete = (
        db.query(MouvementStock)
        .options(joinedload(MouvementStock.article))
        .filter(MouvementStock.utilisateur_id == utilisateur_courant.id)
    )
    if article_id is not None:
        requete = requete.filter(MouvementStock.article_id == article_id)

    mouvements = requete.order_by(MouvementStock.cree_le.desc()).limit(200).all()
    return [_mouvement_vers_sortie(m) for m in mouvements]


@app.post("/stock/mouvements", response_model=MouvementStockSortie, status_code=status.HTTP_201_CREATED)
def creer_mouvement(
    donnees: MouvementStockEntree,
    db: Session = Depends(get_db),
    utilisateur_courant: Utilisateur = Depends(obtenir_utilisateur_courant),
):
    article = _obtenir_article_ou_404(donnees.article_id, db, utilisateur_courant)

    if donnees.type == "sortie" and article.quantite_stock < donnees.quantite:
        raise HTTPException(
            status_code=400,
            detail=f"Stock insuffisant : {article.quantite_stock} unité(s) disponible(s)",
        )

    delta = donnees.quantite if donnees.type == "entree" else -donnees.quantite
    article.quantite_stock += delta

    mouvement = MouvementStock(
        utilisateur_id=utilisateur_courant.id,
        article_id=article.id,
        type=donnees.type,
        quantite=donnees.quantite,
        motif=donnees.motif,
    )
    db.add(mouvement)
    db.commit()
    db.refresh(mouvement)
    mouvement.article = article
    return _mouvement_vers_sortie(mouvement)


# --- Clients ----------------------------------------------------------------

def _calculer_solde_du(client: Client) -> float:
    total_ventes = sum(
        sum(float(l.quantite) * float(l.prix_unitaire) for l in v.lignes) for v in client.ventes
    )
    total_paye_sur_ventes = sum(float(v.montant_paye) for v in client.ventes)
    total_paiements = sum(float(p.montant) for p in client.paiements)
    return round(total_ventes - total_paye_sur_ventes - total_paiements, 2)


def _client_vers_sortie(client: Client) -> ClientSortie:
    return ClientSortie(
        id=client.id,
        nom=client.nom,
        telephone=client.telephone,
        adresse=client.adresse,
        notes=client.notes,
        solde_du=_calculer_solde_du(client),
        cree_le=client.cree_le,
    )


def _requete_clients(db: Session, utilisateur_courant: Utilisateur):
    return (
        db.query(Client)
        .options(joinedload(Client.ventes).joinedload(Vente.lignes), joinedload(Client.paiements))
        .filter(Client.utilisateur_id == utilisateur_courant.id)
    )


@app.get("/clients", response_model=list[ClientSortie])
def lister_clients(
    db: Session = Depends(get_db),
    utilisateur_courant: Utilisateur = Depends(obtenir_utilisateur_courant),
):
    clients = _requete_clients(db, utilisateur_courant).order_by(Client.nom).all()
    return [_client_vers_sortie(c) for c in clients]


@app.post("/clients", response_model=ClientSortie, status_code=status.HTTP_201_CREATED)
def creer_client(
    donnees: ClientEntree,
    db: Session = Depends(get_db),
    utilisateur_courant: Utilisateur = Depends(obtenir_utilisateur_courant),
):
    client = Client(**donnees.model_dump(), utilisateur_id=utilisateur_courant.id)
    db.add(client)
    db.commit()
    db.refresh(client)
    return _client_vers_sortie(client)


def _obtenir_client_ou_404(client_id: int, db: Session, utilisateur_courant: Utilisateur) -> Client:
    client = _requete_clients(db, utilisateur_courant).filter(Client.id == client_id).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client introuvable")
    return client


@app.get("/clients/{client_id}", response_model=ClientSortie)
def obtenir_client(
    client_id: int,
    db: Session = Depends(get_db),
    utilisateur_courant: Utilisateur = Depends(obtenir_utilisateur_courant),
):
    return _client_vers_sortie(_obtenir_client_ou_404(client_id, db, utilisateur_courant))


@app.put("/clients/{client_id}", response_model=ClientSortie)
def modifier_client(
    client_id: int,
    donnees: ClientMiseAJour,
    db: Session = Depends(get_db),
    utilisateur_courant: Utilisateur = Depends(obtenir_utilisateur_courant),
):
    client = _obtenir_client_ou_404(client_id, db, utilisateur_courant)
    for champ, valeur in donnees.model_dump(exclude_unset=True).items():
        setattr(client, champ, valeur)
    db.commit()
    db.refresh(client)
    return _client_vers_sortie(client)


@app.delete("/clients/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_client(
    client_id: int,
    db: Session = Depends(get_db),
    utilisateur_courant: Utilisateur = Depends(obtenir_utilisateur_courant),
):
    client = _obtenir_client_ou_404(client_id, db, utilisateur_courant)
    db.delete(client)
    db.commit()
    return None


@app.post("/clients/{client_id}/paiements", response_model=PaiementSortie, status_code=status.HTTP_201_CREATED)
def enregistrer_paiement(
    client_id: int,
    donnees: PaiementEntree,
    db: Session = Depends(get_db),
    utilisateur_courant: Utilisateur = Depends(obtenir_utilisateur_courant),
):
    client = _obtenir_client_ou_404(client_id, db, utilisateur_courant)
    paiement = Paiement(
        utilisateur_id=utilisateur_courant.id,
        client_id=client.id,
        montant=donnees.montant,
        moyen_paiement=donnees.moyen_paiement,
        motif=donnees.motif,
    )
    db.add(paiement)
    db.commit()
    db.refresh(paiement)
    return paiement


# --- Ventes (caisse) --------------------------------------------------------

def _requete_ventes(db: Session, utilisateur_courant: Utilisateur):
    return (
        db.query(Vente)
        .options(joinedload(Vente.lignes))
        .filter(Vente.utilisateur_id == utilisateur_courant.id)
    )


@app.get("/ventes", response_model=list[VenteSortie])
def lister_ventes(
    db: Session = Depends(get_db),
    utilisateur_courant: Utilisateur = Depends(obtenir_utilisateur_courant),
):
    return _requete_ventes(db, utilisateur_courant).order_by(Vente.cree_le.desc()).limit(200).all()


@app.post("/ventes", response_model=VenteSortie, status_code=status.HTTP_201_CREATED)
def creer_vente(
    donnees: VenteEntree,
    db: Session = Depends(get_db),
    utilisateur_courant: Utilisateur = Depends(obtenir_utilisateur_courant),
):
    if not donnees.lignes:
        raise HTTPException(status_code=400, detail="La vente doit contenir au moins une ligne")
    if any(l.quantite <= 0 for l in donnees.lignes):
        raise HTTPException(status_code=400, detail="Chaque quantité doit être positive")

    if donnees.client_id:
        _obtenir_client_ou_404(donnees.client_id, db, utilisateur_courant)
    if donnees.mode_paiement == "credit" and not donnees.client_id:
        raise HTTPException(status_code=400, detail="Une vente à crédit nécessite un client enregistré")

    total = sum((Decimal(l.quantite) * l.prix_unitaire for l in donnees.lignes), Decimal("0"))
    montant_paye = donnees.montant_paye
    if donnees.mode_paiement == "comptant" and montant_paye == 0:
        montant_paye = total
    if montant_paye < 0 or montant_paye > total:
        raise HTTPException(
            status_code=400, detail="Le montant payé doit être compris entre 0 et le total de la vente"
        )

    # Stock : besoins cumulés par article (un même article peut apparaître sur plusieurs lignes)
    besoins: dict[int, int] = {}
    for ligne in donnees.lignes:
        if ligne.article_id:
            besoins[ligne.article_id] = besoins.get(ligne.article_id, 0) + ligne.quantite

    articles: dict[int, Article] = {}
    try:
        for article_id in sorted(besoins):
            article = (
                db.query(Article)
                .filter(Article.id == article_id, Article.utilisateur_id == utilisateur_courant.id)
                .with_for_update()
                .first()
            )
            if not article:
                raise HTTPException(status_code=404, detail="Article introuvable")
            if article.quantite_stock < besoins[article_id]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Stock insuffisant pour '{article.nom}' : {article.quantite_stock} disponible(s)",
                )
            articles[article_id] = article

        vente = Vente(
            utilisateur_id=utilisateur_courant.id,
            client_id=donnees.client_id,
            client_nom_libre=donnees.client_nom_libre,
            mode_paiement=donnees.mode_paiement,
            moyen_paiement=donnees.moyen_paiement,
            montant_paye=montant_paye,
        )
        for ligne in donnees.lignes:
            article = articles.get(ligne.article_id) if ligne.article_id else None
            vente.lignes.append(
                LigneVente(
                    article_id=ligne.article_id,
                    designation=ligne.designation,
                    quantite=ligne.quantite,
                    prix_unitaire=ligne.prix_unitaire,
                    prix_achat_unitaire=article.prix_achat if article else 0,
                )
            )
        db.add(vente)
        db.flush()  # obtient vente.id pour le motif des mouvements

        for article_id in sorted(besoins):
            article = articles[article_id]
            article.quantite_stock -= besoins[article_id]
            db.add(
                MouvementStock(
                    utilisateur_id=utilisateur_courant.id,
                    article_id=article.id,
                    type="sortie",
                    quantite=besoins[article_id],
                    motif=f"Vente #{vente.id}",
                )
            )

        db.commit()  # vente + lignes + stock + mouvements : tout ou rien
    except Exception:
        db.rollback()
        raise

    db.refresh(vente)
    return vente


@app.get("/ventes/{vente_id}", response_model=VenteSortie)
def obtenir_vente(
    vente_id: int,
    db: Session = Depends(get_db),
    utilisateur_courant: Utilisateur = Depends(obtenir_utilisateur_courant),
):
    vente = _requete_ventes(db, utilisateur_courant).filter(Vente.id == vente_id).first()
    if not vente:
        raise HTTPException(status_code=404, detail="Vente introuvable")
    return vente


# --- Factures ---------------------------------------------------------------

def _generer_numero_facture(db: Session, utilisateur_courant: Utilisateur) -> str:
    """Numéro séquentiel par entreprise et par année : FAC-2026-0001, ...

    Best-effort (pas de verrou dédié) : suffisant pour ce volume de facturation ;
    une collision improbable serait de toute façon rejetée par la contrainte
    d'unicité posée par la migration.
    """
    annee = datetime.now(timezone.utc).year
    prefixe = f"FAC-{annee}-"
    derniere = (
        db.query(Facture)
        .filter(Facture.utilisateur_id == utilisateur_courant.id, Facture.numero.like(f"{prefixe}%"))
        .order_by(Facture.numero.desc())
        .first()
    )
    dernier_sequence = 0
    if derniere:
        try:
            dernier_sequence = int(derniere.numero.rsplit("-", 1)[-1])
        except ValueError:
            dernier_sequence = 0
    return f"{prefixe}{dernier_sequence + 1:04d}"


def _obtenir_vente_ou_404(vente_id: int, db: Session, utilisateur_courant: Utilisateur) -> Vente:
    vente = _requete_ventes(db, utilisateur_courant).filter(Vente.id == vente_id).first()
    if not vente:
        raise HTTPException(status_code=404, detail="Vente introuvable")
    return vente


def _facture_vers_sortie(facture: Facture) -> FactureSortie:
    montant_total = sum(float(l.quantite) * float(l.prix_unitaire) for l in facture.lignes)
    montant_paye = sum(float(p.montant) for p in facture.paiements)
    return FactureSortie(
        id=facture.id,
        numero=facture.numero,
        client_id=facture.client_id,
        client_nom_libre=facture.client_nom_libre,
        devis_id=facture.devis_id,
        vente_id=facture.vente_id,
        statut=facture.statut,
        notes=facture.notes,
        lignes=[LigneFactureSortie.model_validate(l) for l in facture.lignes],
        paiements=[FacturePaiementSortie.model_validate(p) for p in facture.paiements],
        montant_total=round(montant_total, 2),
        montant_paye=round(montant_paye, 2),
        montant_du=round(montant_total - montant_paye, 2),
        cree_le=facture.cree_le,
        modifie_le=facture.modifie_le,
    )


def _requete_factures(db: Session, utilisateur_courant: Utilisateur):
    return (
        db.query(Facture)
        .options(joinedload(Facture.lignes), joinedload(Facture.paiements))
        .filter(Facture.utilisateur_id == utilisateur_courant.id)
    )


@app.get("/factures", response_model=list[FactureSortie])
def lister_factures(
    db: Session = Depends(get_db),
    utilisateur_courant: Utilisateur = Depends(obtenir_utilisateur_courant),
):
    factures = _requete_factures(db, utilisateur_courant).order_by(Facture.cree_le.desc()).all()
    return [_facture_vers_sortie(f) for f in factures]


@app.post("/factures", response_model=FactureSortie, status_code=status.HTTP_201_CREATED)
def creer_facture(
    donnees: FactureEntree,
    db: Session = Depends(get_db),
    utilisateur_courant: Utilisateur = Depends(obtenir_utilisateur_courant),
):
    client_nom_libre = donnees.client_nom_libre
    lignes_entree = list(donnees.lignes)

    if donnees.client_id:
        _obtenir_client_ou_404(donnees.client_id, db, utilisateur_courant)

    devis_source = None
    if donnees.devis_id:
        devis_source = _obtenir_devis_ou_404(donnees.devis_id, db, utilisateur_courant)
        if not lignes_entree:
            lignes_entree = [
                LigneFactureEntree(
                    article_id=l.article_id,
                    designation=l.designation,
                    quantite=l.quantite,
                    prix_unitaire=l.prix_unitaire,
                )
                for l in devis_source.lignes
            ]
        if not client_nom_libre:
            client_nom_libre = devis_source.client_nom

    vente_source = None
    if donnees.vente_id:
        vente_source = _obtenir_vente_ou_404(donnees.vente_id, db, utilisateur_courant)
        if not lignes_entree:
            lignes_entree = [
                LigneFactureEntree(
                    article_id=l.article_id,
                    designation=l.designation,
                    quantite=l.quantite,
                    prix_unitaire=l.prix_unitaire,
                )
                for l in vente_source.lignes
            ]
        if not client_nom_libre and not donnees.client_id:
            client_nom_libre = vente_source.client_nom_libre

    if not lignes_entree:
        raise HTTPException(status_code=400, detail="La facture doit contenir au moins une ligne")

    facture = Facture(
        utilisateur_id=utilisateur_courant.id,
        numero=_generer_numero_facture(db, utilisateur_courant),
        client_id=donnees.client_id or (vente_source.client_id if vente_source else None),
        client_nom_libre=client_nom_libre,
        devis_id=donnees.devis_id,
        vente_id=donnees.vente_id,
        statut=donnees.statut,
        notes=donnees.notes,
    )
    for ligne in lignes_entree:
        facture.lignes.append(LigneFacture(**ligne.model_dump()))

    db.add(facture)
    db.commit()
    db.refresh(facture)
    return _facture_vers_sortie(facture)


def _obtenir_facture_ou_404(facture_id: int, db: Session, utilisateur_courant: Utilisateur) -> Facture:
    facture = _requete_factures(db, utilisateur_courant).filter(Facture.id == facture_id).first()
    if not facture:
        raise HTTPException(status_code=404, detail="Facture introuvable")
    return facture


@app.get("/factures/{facture_id}", response_model=FactureSortie)
def obtenir_facture(
    facture_id: int,
    db: Session = Depends(get_db),
    utilisateur_courant: Utilisateur = Depends(obtenir_utilisateur_courant),
):
    return _facture_vers_sortie(_obtenir_facture_ou_404(facture_id, db, utilisateur_courant))


@app.put("/factures/{facture_id}", response_model=FactureSortie)
def modifier_facture(
    facture_id: int,
    donnees: FactureMiseAJour,
    db: Session = Depends(get_db),
    utilisateur_courant: Utilisateur = Depends(obtenir_utilisateur_courant),
):
    facture = _obtenir_facture_ou_404(facture_id, db, utilisateur_courant)
    champs = donnees.model_dump(exclude_unset=True, exclude={"lignes"})
    if "client_id" in champs and champs["client_id"]:
        _obtenir_client_ou_404(champs["client_id"], db, utilisateur_courant)
    for champ, valeur in champs.items():
        setattr(facture, champ, valeur)
    if donnees.lignes is not None:
        facture.lignes.clear()
        for ligne in donnees.lignes:
            facture.lignes.append(LigneFacture(**ligne.model_dump()))

    db.commit()
    db.refresh(facture)
    return _facture_vers_sortie(facture)


@app.delete("/factures/{facture_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_facture(
    facture_id: int,
    db: Session = Depends(get_db),
    utilisateur_courant: Utilisateur = Depends(obtenir_utilisateur_courant),
):
    facture = _obtenir_facture_ou_404(facture_id, db, utilisateur_courant)
    db.delete(facture)
    db.commit()
    return None


@app.post(
    "/factures/{facture_id}/paiements",
    response_model=FacturePaiementSortie,
    status_code=status.HTTP_201_CREATED,
)
def enregistrer_paiement_facture(
    facture_id: int,
    donnees: FacturePaiementEntree,
    db: Session = Depends(get_db),
    utilisateur_courant: Utilisateur = Depends(obtenir_utilisateur_courant),
):
    facture = _obtenir_facture_ou_404(facture_id, db, utilisateur_courant)
    paiement = PaiementFacture(
        utilisateur_id=utilisateur_courant.id,
        facture_id=facture.id,
        montant=donnees.montant,
        moyen_paiement=donnees.moyen_paiement,
        motif=donnees.motif,
    )
    db.add(paiement)
    db.commit()
    db.refresh(paiement)
    return paiement


# --- Tableau de bord ---------------------------------------------------------

@app.get("/tableau-de-bord/resume", response_model=TableauDeBordResume)
def resume_tableau_de_bord(
    db: Session = Depends(get_db),
    utilisateur_courant: Utilisateur = Depends(obtenir_utilisateur_courant),
):
    debut_jour = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    fin_jour = debut_jour + timedelta(days=1)

    ventes_du_jour = (
        db.query(Vente)
        .options(joinedload(Vente.lignes))
        .filter(
            Vente.utilisateur_id == utilisateur_courant.id,
            Vente.cree_le >= debut_jour,
            Vente.cree_le < fin_jour,
        )
        .all()
    )

    chiffre_affaires_jour = sum(
        sum(float(l.quantite) * float(l.prix_unitaire) for l in v.lignes) for v in ventes_du_jour
    )
    benefice_estime_jour = sum(
        sum(float(l.quantite) * (float(l.prix_unitaire) - float(l.prix_achat_unitaire)) for l in v.lignes)
        for v in ventes_du_jour
    )

    articles = (
        db.query(Article).filter(Article.utilisateur_id == utilisateur_courant.id).all()
    )
    produits_presque_epuises = [
        ArticleAlerte(
            id=a.id, nom=a.nom, quantite_stock=a.quantite_stock, seuil_alerte=a.seuil_alerte
        )
        for a in articles
        if a.quantite_stock <= a.seuil_alerte
    ]

    nombre_clients = (
        db.query(Client).filter(Client.utilisateur_id == utilisateur_courant.id).count()
    )

    return TableauDeBordResume(
        chiffre_affaires_jour=chiffre_affaires_jour,
        ventes_jour=len(ventes_du_jour),
        benefice_estime_jour=benefice_estime_jour,
        nombre_produits=len(articles),
        nombre_clients=nombre_clients,
        produits_presque_epuises=produits_presque_epuises[:5],
    )
