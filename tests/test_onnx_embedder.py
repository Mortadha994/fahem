"""The ONNX embedder agrees with the sentence-transformers model the index was
built with: near-identical vectors, and the same chunks retrieved.

Needs both backends and a running Qdrant (read only):

    docker compose ... run --rm backend sh -c "pip install -q onnxruntime && python -m tests.test_onnx_embedder"
"""

from __future__ import annotations

import numpy as np

from app.rag import rag_store
from app.rag.onnx_embedder import OnnxEmbedder

QUERIES = [
    "Ecrire un programme qui lit deux entiers et affiche leur somme.",
    "Écrire un algorithme qui lit un entier N et affiche s'il est pair ou impair.",
    "Calculer la somme des entiers de 1 à N avec une boucle Pour.",
    "Trier un tableau de N entiers par la méthode de sélection.",
    "Remplir une matrice de 3 lignes et 4 colonnes.",
    "Écrire une fonction récursive qui calcule la factorielle.",
    "Chercher un élément dans un tableau trié par dichotomie.",
    "Déclarer un enregistrement Élève avec nom, prénom et moyenne.",
    "Ouvrir un fichier texte et compter ses lignes.",
    "Vérifier si une chaîne est un palindrome.",
]
SCOPES = [("2eme", "1"), ("2eme", "3"), ("3eme", "31"), ("bac", "62"), ("bac", "66")]

failures = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global failures
    print(f"[{'PASS' if ok else 'FAIL'}] {name}  {detail}")
    failures += 0 if ok else 1


def main() -> None:
    st = rag_store.get_model()  # the default backend: sentence-transformers
    onnx = OnnxEmbedder()

    client = rag_store.get_client()
    points, _ = client.scroll(rag_store.COLLECTION_NAME, limit=60, with_payload=True)
    texts = QUERIES + [str(p.payload.get(rag_store.TEXT_KEY, ""))[:2000] for p in points]

    hf = st.tokenizer
    same = [
        onnx.token_ids(t) == hf(t, truncation=True, max_length=128)["input_ids"] for t in texts
    ]
    check("SentencePiece ids equal the model's tokenizer", all(same), f"{sum(same)}/{len(same)} texts")

    a = st.encode(texts, normalize_embeddings=True, show_progress_bar=False)
    b = onnx.encode(texts, normalize_embeddings=True)
    cos = (a * b).sum(axis=1)
    check("same vector size", a.shape == b.shape, str(b.shape))
    check("average cosine to the indexed model >= 0.99", cos.mean() >= 0.99, f"{cos.mean():.4f}")
    check("worst cosine >= 0.97", cos.min() >= 0.97, f"{cos.min():.4f}")

    overlaps = []
    for niveau, chapitre in SCOPES:
        flt = rag_store.qmodels.Filter(
            must=[
                rag_store.qmodels.FieldCondition(key="niveau", match=rag_store.qmodels.MatchValue(value=niveau)),
                rag_store.qmodels.FieldCondition(key="chapitre", match=rag_store.qmodels.MatchValue(value=chapitre)),
            ]
        )
        for q in QUERIES:
            hits = []
            for model in (st, onnx):
                vec = model.encode([q], normalize_embeddings=True)[0].tolist()
                res = client.query_points(rag_store.COLLECTION_NAME, query=vec, query_filter=flt, limit=5)
                hits.append([p.id for p in res.points])
            if hits[0]:
                overlaps.append(len(set(hits[0]) & set(hits[1])) / len(hits[0]))
    mean = float(np.mean(overlaps)) if overlaps else 0.0
    check("top-5 retrieved chunks agree (average overlap >= 0.8)", mean >= 0.8, f"{mean:.2f} over {len(overlaps)} searches")

    print(f"\n{failures} failure(s)")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
