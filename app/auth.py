import os
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Utilisateur

# La clé secrète DOIT être définie en variable d'environnement sur Render.
# Génère-en une avec : python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "La variable d'environnement SECRET_KEY n'est pas définie. "
        "Configure-la dans les paramètres Render (Environment)."
    )

ALGORITHME = "HS256"
DUREE_TOKEN_MINUTES = 60 * 24 * 7  # 7 jours

contexte_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/connexion")


def hacher_mot_de_passe(mot_de_passe: str) -> str:
    return contexte_pwd.hash(mot_de_passe)


def verifier_mot_de_passe(mot_de_passe: str, hash_stocke: str) -> bool:
    return contexte_pwd.verify(mot_de_passe, hash_stocke)


def creer_token_acces(donnees: dict) -> str:
    a_encoder = donnees.copy()
    expiration = datetime.now(timezone.utc) + timedelta(minutes=DUREE_TOKEN_MINUTES)
    a_encoder.update({"exp": expiration})
    return jwt.encode(a_encoder, SECRET_KEY, algorithm=ALGORITHME)


def obtenir_utilisateur_courant(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> Utilisateur:
    exception_identifiants = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Identifiants invalides ou expirés",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHME])
        email: str = payload.get("sub")
        if email is None:
            raise exception_identifiants
    except JWTError:
        raise exception_identifiants

    utilisateur = db.query(Utilisateur).filter(Utilisateur.email == email).first()
    if utilisateur is None:
        raise exception_identifiants
    return utilisateur
