# Fahem gratuit sur Hugging Face Spaces

Un seul conteneur (nginx + backend + Redis) sur un Space Docker gratuit.
La base de données est chez **Neon**, l'index des cours chez **Qdrant Cloud**,
le LLM chez **Groq** (inchangé). Aucun PC allumé, aucun paiement.

```
élève ──https──> Space (nginx :7860)
                    ├─ /      → interface (fichiers statiques)
                    └─ /api/  → FastAPI :8000 ──> Neon (Postgres)
                                     │         └─> Qdrant Cloud
                                     └─> Redis (dans le conteneur) / Groq
```

## 0. Ce qu'il faut créer (gratuit, 3 comptes)

| Service | Quoi créer | Ce qu'il faut me donner / noter |
|---|---|---|
| **Neon** (neon.tech) | un projet Postgres | la *connection string* (`postgresql://…?sslmode=require`) |
| **Qdrant Cloud** (cloud.qdrant.io) | un cluster gratuit | l'URL du cluster + une *API key* |
| **Hugging Face** (huggingface.co) | un Space **Docker**, **privé** | un *token d'écriture* (Settings → Access Tokens) |

## 1. Migrer les données (une seule fois, depuis votre PC)

Docker Desktop doit tourner. Dans le dossier du projet :

```powershell
# a) Postgres : sauvegarde locale -> Neon
docker exec fahem-postgres-1 pg_dump -U fahem -d fahem --no-owner --no-privileges -Fc -f /tmp/fahem.dump
docker cp fahem-postgres-1:/tmp/fahem.dump fahem.dump
docker run --rm -v "${PWD}:/d" postgres:16-alpine pg_restore --no-owner --no-privileges --clean --if-exists -d "<CONNECTION_STRING_NEON>" /d/fahem.dump

# b) Qdrant : tous les points, vecteurs compris
python -m scripts.migrate_to_cloud qdrant --target "<URL_QDRANT_CLOUD>:6333" --target-key "<API_KEY>"

# c) PDF et fichiers des chapitres importés
docker cp fahem-backend-1:/app/uploads/chapters ./uploads-chapters
python -m scripts.migrate_to_cloud uploads --folder ./uploads-chapters --database "<CONNECTION_STRING_NEON>"
```

Les scripts sont répétables sans risque.

## 2. Créer le Space et le configurer

1. Hugging Face → *New Space* → SDK **Docker** → visibilité **Private**.
2. Dans *Settings → Variables and secrets*, ajouter :

   **Secrets** (jamais en clair dans le dépôt) :
   `GROQ_API_KEY`, `DATABASE_URL` (Neon), `QDRANT_URL`, `QDRANT_API_KEY`,
   `SESSION_SECRET_KEY` (`python -c "import secrets; print(secrets.token_urlsafe(48))"`),
   et si vous les utilisez : `RESEND_API_KEY`, `GOOGLE_CLIENT_ID`.

   **Variables** : `VITE_GOOGLE_CLIENT_ID` (même valeur que `GOOGLE_CLIENT_ID`),
   `APP_BASE_URL` = `https://<utilisateur>-<space>.hf.space` (facultatif :
   déduit de `SPACE_HOST` sinon).

3. Google : ajouter l'adresse `https://<utilisateur>-<space>.hf.space` aux
   « origines JavaScript autorisées » du client OAuth.

## 3. Déployer

```powershell
python deploy/space/make_bundle.py --out build/space
cd build/space
git init; git remote add space https://huggingface.co/spaces/<utilisateur>/<space>
git add -A; git commit -m "Fahem"; git push space HEAD:main --force
```

Le premier build prend 10 à 15 minutes (torch, modèle d'embeddings). Le Space
dort après environ 48 h sans visite et se réveille à la requête suivante ; un
ping gratuit (UptimeRobot / cron-job.org sur `/api/health`) l'évite.

## 4. Mise à jour

Relancer `make_bundle.py` puis le `git push` de l'étape 3.

## Limites à connaître

- Le disque du Space est effacé à chaque redémarrage : les PDF envoyés par la
  console admin sont donc aussi gardés dans Postgres (`MIRROR_UPLOADS_TO_DB`)
  et remis en place au démarrage.
- Neon gratuit : 0,5 Go. Qdrant Cloud gratuit : 1 Go, cluster suspendu après
  environ 4 semaines sans activité (le ping ci-dessus évite aussi cela).
- Groq reste limité à 8 000 tokens/minute sur le palier gratuit.
