import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import {
  CHAPTER_STATUS,
  errorMessage,
  fetchChaptersAdmin,
  relativeTime,
  UnauthorizedError,
  isMarkdown,
  uploadChapterSource,
} from "../../lib/admin.js";
import { useAuth } from "../../lib/authContext.js";

const POLL_MS = 2500;

/**
 * Uploaded chapters: the list, and the form that starts a new one.
 *
 * Chapter 1 is not listed: it is built into Fahem and managed in code, not
 * here (see app/rag/chapter_store.py). The note under the heading says so, so its
 * absence does not read as a bug.
 */
export default function AdminChapters() {
  const { onUnauthorized } = useAuth();
  const navigate = useNavigate();
  const [rows, setRows] = useState(null);
  const [failed, setFailed] = useState(false);
  const [form, setForm] = useState({ id: "", title: "", file: null });
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const fileRef = useRef(null);
  // A .md course names itself in its header; only a PDF needs a typed title.
  const mdFile = Boolean(form.file && isMarkdown(form.file));

  const load = useCallback(() => {
    return fetchChaptersAdmin()
      .then((list) => {
        setRows(list);
        setFailed(false);
        return list;
      })
      .catch((err) => {
        if (err instanceof UnauthorizedError) onUnauthorized();
        else setFailed(true);
        return null;
      });
  }, [onUnauthorized]);

  useEffect(() => {
    load();
  }, [load]);

  // Poll only while something is running, so an idle list costs nothing.
  const running = rows?.some(
    (r) => r.status === "processing" || r.status === "publishing"
  );
  useEffect(() => {
    if (!running) return undefined;
    const t = setInterval(load, POLL_MS);
    return () => clearInterval(t);
  }, [running, load]);

  async function submit(e) {
    e.preventDefault();
    if (!form.file) return;
    setBusy(true);
    setError(null);
    try {
      const created = await uploadChapterSource(form);
      navigate(`/admin/chapitres/${created.id}`);
    } catch (err) {
      if (err instanceof UnauthorizedError) onUnauthorized();
      else setError(errorMessage(err));
      setBusy(false);
    }
  }

  return (
    <div className="adm-page">
      <header className="adm-head">
        <div>
          <h1 className="adm-h1">Chapitres</h1>
          <p className="adm-sub">
            Envoie le PDF d'un chapitre, relis l'extraction, puis publie-le pour les
            élèves. Le chapitre 1 est intégré à Fahem et n'apparaît pas ici.
          </p>
        </div>
      </header>

      <form className="adm-panel adm-form adm-upload" onSubmit={submit}>
        <h2 className="adm-h2">Nouveau chapitre</h2>
        {error && (
          <p className="adm-alert" role="alert">
            {error}
          </p>
        )}
        <div className="adm-upload-row">
          <label className="adm-field adm-field-num">
            <span>N°</span>
            <input
              className="adm-input"
              required
              inputMode="numeric"
              pattern="[0-9]{1,3}"
              placeholder="2"
              value={form.id}
              onChange={(e) => setForm((f) => ({ ...f, id: e.target.value.trim() }))}
            />
          </label>
          <label className="adm-field adm-grow">
            <span>Titre</span>
            <input
              className="adm-input"
              required={!mdFile}
              disabled={mdFile}
              maxLength={200}
              placeholder={
                mdFile
                  ? "Lu depuis l'en-tête du .md"
                  : "Les structures de contrôle conditionnelles"
              }
              value={form.title}
              onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
            />
          </label>
        </div>
        <label
          className={`adm-drop${form.file ? " has-file" : ""}`}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            const file = e.dataTransfer.files?.[0];
            if (file) setForm((f) => ({ ...f, file }));
          }}
        >
          <input
            ref={fileRef}
            type="file"
            accept="application/pdf,.pdf,.md,text/markdown"
            required
            onChange={(e) =>
              setForm((f) => ({ ...f, file: e.target.files?.[0] ?? null }))
            }
          />
          <span className="adm-drop-icon" aria-hidden="true">
            ⇪
          </span>
          {form.file ? (
            <span>
              <strong>{form.file.name}</strong> ·{" "}
              {(form.file.size / 1048576).toFixed(1)} Mo
            </span>
          ) : (
            <span>
              Glisse le cours ici ou <u>choisis un fichier</u> : un .md au modèle Fahem
              (recommandé) ou un PDF
            </span>
          )}
        </label>
        <div className="adm-form-actions">
          <button className="adm-btn adm-btn-primary" disabled={busy || !form.file}>
            {busy ? "Envoi…" : mdFile ? "Importer le cours" : "Envoyer et extraire"}
          </button>
        </div>
      </form>

      {failed && <p className="adm-alert">Impossible de charger les chapitres.</p>}

      <div className="adm-table-wrap">
        <table className="adm-table adm-table-cards">
          <thead>
            <tr>
              <th>N°</th>
              <th>Titre</th>
              <th>Statut</th>
              <th>À relire</th>
              <th>Extraits</th>
              <th>Exercices</th>
              <th>Modifié</th>
            </tr>
          </thead>
          <tbody>
            {rows?.map((c) => {
              const st = CHAPTER_STATUS[c.status] ?? { label: c.status, tone: "dim" };
              return (
                <tr
                  key={c.id}
                  className="adm-row-link"
                  tabIndex={0}
                  onClick={() => navigate(`/admin/chapitres/${c.id}`)}
                  onKeyDown={(e) =>
                    e.key === "Enter" && navigate(`/admin/chapitres/${c.id}`)
                  }
                >
                  <td data-label="N°" className="adm-strong adm-cell-num">
                    {c.id}
                  </td>
                  <td data-label="Titre">
                    <span className="adm-list-main">
                      <span className="adm-strong">{c.title}</span>
                      <span className="adm-muted">{c.source_filename}</span>
                    </span>
                  </td>
                  <td data-label="Statut">
                    <span className={`adm-tag adm-tag-${st.tone}`}>{st.label}</span>
                    {c.has_unpublished_changes && (
                      <span className="adm-tag adm-tag-warn">Modifié</span>
                    )}
                  </td>
                  <td data-label="À relire">
                    {c.flagged_count ? (
                      <span className="adm-tag adm-tag-warn">{c.flagged_count}</span>
                    ) : (
                      <span className="adm-muted">—</span>
                    )}
                  </td>
                  <td data-label="Extraits">{c.chunk_count}</td>
                  <td data-label="Exercices">{c.exercise_count}</td>
                  <td data-label="Modifié" className="adm-muted">
                    {relativeTime(c.updated_at)}
                  </td>
                </tr>
              );
            })}
            {rows?.length === 0 && (
              <tr>
                <td colSpan={7} className="adm-empty">
                  Aucun chapitre envoyé pour l'instant.
                </td>
              </tr>
            )}
            {!rows && !failed && (
              <tr aria-hidden="true">
                <td colSpan={7}>
                  <div className="adm-skel adm-skel-row" />
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {/* A tip, set apart as one, instead of a stray sentence under the table. */}
      <p className="adm-tip">
        <span className="adm-tip-ico" aria-hidden="true">
          ↗
        </span>
        <span>
          Un chapitre publié apparaît tout de suite dans le chat des élèves.{" "}
          <Link to="/chat" className="adm-link">
            Le tester dans le chat
          </Link>
        </span>
      </p>
    </div>
  );
}
