# Prog 1.8 — Backend

API FastAPI pour la gestion catalogue/devis/stock (quincaillerie/vitrerie).

## Lancer en local

```bash
python -m venv venv
source venv/bin/activate  # Windows : venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env      # puis remplis DATABASE_URL et SECRET_KEY
uvicorn app.main:app --reload
```

Ouvre ensuite http://localhost:8000/docs

## Déployer sur Render

1. Push ce code sur GitHub (repo `prog18-backend`)
2. Sur Render : **New > Web Service**, connecte le repo
3. Configuration :
   - **Build Command** : `pip install -r requirements.txt`
   - **Start Command** : `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Dans **Environment**, ajoute :
   - `DATABASE_URL` → l'URL de connexion Neon
   - `SECRET_KEY` → génère-la avec `python -c "import secrets; print(secrets.token_hex(32))"`
   - `FRONTEND_URL` → l'URL de ton frontend Vercel (ex: `https://prog18-frontend.vercel.app`)
5. Déploie, puis vérifie `https://ton-service.onrender.com/health` et `/docs`

## Notes importantes

- Le plan Render Free met le service en veille après 15 min d'inactivité :
  le premier appel après une pause peut prendre 30-60 secondes.
- Le CORS est déjà configuré pour accepter `FRONTEND_URL` et les sous-domaines
  de prévisualisation Vercel (`*.vercel.app`).
