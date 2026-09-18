import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# L'URL de connexion Neon doit être définie en variable d'environnement
# sur Render (jamais en dur dans le code).
# Format attendu : postgresql://user:password@host/dbname?sslmode=require
DATABASE_URL = os.environ.get("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError(
        "La variable d'environnement DATABASE_URL n'est pas définie. "
        "Configure-la dans les paramètres Render (Environment)."
    )

# Neon fonctionne avec psycopg2 ; certaines URLs Neon commencent par
# "postgres://" au lieu de "postgresql://" — SQLAlchemy exige ce dernier.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dépendance FastAPI : ouvre une session DB et la ferme proprement."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
