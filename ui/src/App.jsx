import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./App.css";

// The corpus holds exactly one niveau/chapitre, so this is a fixed label
// rather than a selector. Add a dropdown when a second chapter is ingested.
const NIVEAU = "2eme";
const CHAPITRE = "1";
const SCOPE_LABEL =
  "2ème — Chapitre 1 : Les structures de données et les structures simples";

const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";

// The student never sees an API error body. The endpoint still returns verbose
// detail (see the pre-launch items in README_API.md), and none of it belongs
// in front of a student either way.
const GENERIC_ERROR =
  "Une erreur est survenue. Merci de réessayer dans un instant.";
const BUSY_ERROR =
  "Le service est très sollicité en ce moment. Merci de réessayer dans une minute.";

export default function App() {
  const [problem, setProblem] = useState("");
  const [solution, setSolution] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleSubmit(event) {
    event.preventDefault();
    if (!problem.trim() || loading) return;

    setLoading(true);
    setError("");
    setSolution("");

    try {
      const response = await fetch(`${API_URL}/solve`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          problem: problem.trim(),
          niveau: NIVEAU,
          chapitre: CHAPITRE,
        }),
      });

      if (!response.ok) {
        setError(response.status === 429 ? BUSY_ERROR : GENERIC_ERROR);
        return;
      }

      const data = await response.json();
      setSolution(data.solution);
    } catch {
      // Network failure, API down, CORS - all the same to the student.
      setError(GENERIC_ERROR);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="app">
      <header className="header">
        <h1>Assistant d'algorithmique</h1>
        <p className="scope">{SCOPE_LABEL}</p>
      </header>

      <form onSubmit={handleSubmit}>
        <label htmlFor="problem">Colle ton énoncé ici :</label>
        <textarea
          id="problem"
          value={problem}
          onChange={(e) => setProblem(e.target.value)}
          placeholder="Exemple : Ecrire un programme qui demande un nombre à l'utilisateur, puis qui calcule et affiche le carré de ce nombre."
          rows={7}
          disabled={loading}
        />
        <button type="submit" disabled={loading || !problem.trim()}>
          {loading ? "Résolution en cours…" : "Résoudre"}
        </button>
      </form>

      {loading && (
        <p className="status" role="status">
          L'assistant rédige la solution et vérifie sa trace. Cela prend
          quelques secondes.
        </p>
      )}

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      {solution && (
        <section className="solution" aria-label="Solution">
          {/* Rendered as returned - remark-gfm is what makes the
              Algorithme | Python tables display as tables. */}
          <ReactMarkdown remarkPlugins={[remarkGfm]}>{solution}</ReactMarkdown>
        </section>
      )}
    </main>
  );
}
