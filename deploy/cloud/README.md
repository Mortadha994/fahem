# Fahem gratuit sur Render (+ Neon + Qdrant Cloud)

Un seul conteneur (nginx + backend + Redis) sur un *web service* gratuit de
**Render** (512 Mo, sans carte bancaire). La base de données est chez **Neon**,
l'index des cours chez **Qdrant Cloud**, le LLM chez **Groq** (inchangé).
Plus besoin du PC allumé.

```
élève ──https──> Render (nginx :$PORT)
                    ├─ /      → interface (fichiers statiques)
                    └─ /api/  → FastAPI :8000 ──> Neon (Postgres)
                                     │         └─> Qdrant Cloud
                                     └─> Redis (dans le conteneur) / Groq
```

Le modèle d'embeddings tourne sur onnxruntime (int8, sans torch) pour tenir
dans 512 Mo ; ses vecteurs sont compatibles avec l'index existant
(`tests/test_onnx_embedder.py` : cosinus 0,99, 94 % des extraits identiques).

## 0. Comptes (gratuits)

| Service | Quoi créer | À noter |
|---|---|---|
| **Neon** (neon.tech) | un projet Postgres | la *connection string* (`postgresql://…?sslmode=require`) |
| **Qdrant Cloud** (cloud.qdrant.io) | un cluster gratuit | l'URL du cluster + une *API key* |
| **Render** (render.com) | un compte (connexion avec GitHub) | rien : on crée le service à l'étape 3 |

Le code déployé vit dans un dépôt GitHub **privé** séparé (`fahem-deploy`),
construit par `make_bundle.py` : il contient les fichiers du chapitre 1 qui ne
sont pas dans le dépôt principal.

## 1. Migrer les données (une seule fois, depuis le PC, Docker lancé)

Utiliser l'adresse **directe** de Neon : retirer `-pooler` du nom d'hôte.
Par le pooler, `pg_restore` laisse un `search_path` vide collé à une connexion
partagée (« relation users does not exist » ensuite), et l'application n'a
pas besoin du pooler. Après la restauration, passer le schéma à jour
(`alembic upgrade head` avec `DATABASE_URL` = Neon) avant l'étape c). Le script
Qdrant recopie aussi les index de champs, sans lesquels Qdrant Cloud (mode
strict) refuse les recherches filtrées.

```powershell
# a) Postgres : sauvegarde locale -> Neon
docker exec fahem-postgres-1 pg_dump -U fahem -d fahem --no-owner --no-privileges -Fc -f /tmp/fahem.dump
docker cp fahem-postgres-1:/tmp/fahem.dump fahem.dump
docker run --rm -v "${PWD}:/d" postgres:16-alpine pg_restore --no-owner --no-privileges --clean --if-exists -d "<NEON>" /d/fahem.dump

# b) Qdrant : tous les points, vecteurs compris
python -m scripts.migrate_to_cloud qdrant --target "<URL_QDRANT>:6333" --target-key "<CLE_QDRANT>"

# c) PDF et fichiers des chapitres importés
docker cp fahem-backend-1:/app/uploads/chapters ./uploads-chapters
python -m scripts.migrate_to_cloud uploads --folder ./uploads-chapters --database "<NEON>"
```

## 2. Pousser le paquet dans le dépôt privé

```powershell
gh repo create fahem-deploy --private
git clone https://github.com/<vous>/fahem-deploy build/cloud
python deploy/cloud/make_bundle.py --out build/cloud
cd build/cloud; git add -A; git commit -m "Fahem"; git push
```

## 3. Créer le service sur Render

1. *New* → **Web Service** → connecter GitHub → choisir `fahem-deploy`.
2. **Runtime** : Docker. **Instance type** : **Free**. Région : Frankfurt.
3. **Health check path** : `/api/health`.
4. *Environment* :

   | Clé | Valeur |
   |---|---|
   | `GROQ_API_KEY` | votre clé Groq |
   | `DATABASE_URL` | la connection string Neon |
   | `QDRANT_URL` | `https://…cloud.qdrant.io:6333` |
   | `QDRANT_API_KEY` | la clé Qdrant |
   | `SESSION_SECRET_KEY` | une valeur aléatoire longue |
   | `RESEND_API_KEY`, `GOOGLE_CLIENT_ID` | si vous les utilisez |

5. *Create Web Service*. Le premier build prend 5 à 10 minutes ; l'adresse est
   `https://<nom>.onrender.com`.
6. Connexion Google : ajouter cette adresse aux « origines JavaScript
   autorisées » du client OAuth, et `VITE_GOOGLE_CLIENT_ID` comme variable de
   build si besoin.

## 4. Mise à jour

`make_bundle.py` puis `git push` dans `build/cloud` : Render redéploie seul.

## Limites à connaître

- **Veille** : le service gratuit s'endort après 15 minutes sans visite et met
  environ une minute à se réveiller. Un ping gratuit toutes les 10 minutes
  (UptimeRobot ou cron-job.org sur `/api/health`) le garde éveillé ; 750 h
  gratuites par mois couvrent un service allumé en continu.
- **Disque** : effacé à chaque déploiement ; les PDF téléversés sont aussi
  gardés dans Postgres (`MIRROR_UPLOADS_TO_DB`) et remis en place au démarrage.
- **Quotas** : Neon 0,5 Go ; Qdrant Cloud 1 Go, cluster suspendu après une
  longue inactivité (le ping l'évite aussi).
- **CPU** : l'offre gratuite est lente au démarrage (environ 1 minute) ; une
  question passe surtout son temps chez Groq, limité à 8 000 tokens/minute.
