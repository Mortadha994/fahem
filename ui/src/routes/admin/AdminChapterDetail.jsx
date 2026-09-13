import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  addExercise,
  CHAPTER_STATUS,
  chapterPdfUrl,
  deleteChapter,
  deleteChunk,
  deleteExercise,
  errorMessage,
  fetchChapterAdmin,
  FLAG_LABELS,
  fullDate,
  publishChapter,
  UnauthorizedError,
  unpublishChapter,
  updateChapter,
  updateChunk,
  updateExercise,
  uploadChapterDocument,
  uploadChapterSource,
} from "../../lib/admin.js";
import { useAuth } from "../../lib/authContext.js";

const POLL_MS = 2000;
const FILTERS = [
  { key: "flagged", label: "À relire" },
  { key: "pinned", label: "Épinglés" },
  { key: "table", label: "Tableaux" },
  { key: "prose", label: "Cours" },
  { key: "exercice", label: "Série" },
  { key: "all", label: "Tout" },
];

/**
 * Review one uploaded chapter, then publish it.
 *
 * The order of the page is the order of the work: fix what the extraction got
 * wrong (flagged chunks first), mark the reference sheet (pins), check the
 * exercises, fill in the chapter's topics, publish. Nothing here reaches a
 * student until "Publier": the chat reads the publish snapshot, not these rows.
 */
export default function AdminChapterDetail() {
  const { id } = useParams();
  const { onUnauthorized } = useAuth();
  const navigate = useNavigate();

  const [ch, setCh] = useState(null);
  const [loadError, setLoadError] = useState(null);
  const [error, setError] = useState(null);
  const [notice, setNotice] = useState(null);
  const [filter, setFilter] = useState("flagged");
  const [meta, setMeta] = useState(null);
  const [busy, setBusy] = useState(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const replaceRef = useRef(null);
  const documentRef = useRef(null);

  const fail = useCallback(
    (err) => {
      if (err instanceof UnauthorizedError) onUnauthorized();
      else setError(errorMessage(err));
    },
    [onUnauthorized]
  );

  const load = useCallback(
    () =>
      fetchChapterAdmin(id)
        .then((data) => {
          setCh(data);
          setMeta((m) => m ?? { title: data.title, topics: data.topics });
          return data;
        })
        .catch((err) => {
          if (err instanceof UnauthorizedError) onUnauthorized();
          else setLoadError(errorMessage(err));
        }),
    [id, onUnauthorized]
  );

  useEffect(() => {
    load().then((data) => {
      // Nothing flagged: open on everything rather than on an empty list.
      if (data && !data.flagged_count) setFilter("all");
    });
  }, [load]);

  const running = ch?.status === "processing" || ch?.status === "publishing";
  const wasRunning = useRef(false);
  useEffect(() => {
    if (!running) {
      if (wasRunning.current) {
        wasRunning.current = false;
        setMeta(null); // pick up anything the background task changed
        load();
      }
      return undefined;
    }
    wasRunning.current = true;
    const t = setInterval(load, POLL_MS);
    return () => clearInterval(t);
  }, [running, load]);

  const chunks = useMemo(() => {
    if (!ch) return [];
    return ch.chunks.filter((c) => {
      if (filter === "flagged") return c.flags.length > 0;
      if (filter === "pinned") return c.pinned;
      if (filter === "all") return true;
      return c.type === filter;
    });
  }, [ch, filter]);

  if (loadError) {
    return (
      <div className="adm-page">
        <Link to="/admin/chapitres" className="adm-back">
          ← Chapitres
        </Link>
        <p className="adm-alert">{loadError}</p>
      </div>
    );
  }
  if (!ch || !meta) {
    return (
      <div className="adm-page">
        <div className="adm-skel adm-skel-block" aria-hidden="true" />
      </div>
    );
  }

  const st = CHAPTER_STATUS[ch.status] ?? { label: ch.status, tone: "dim" };
  const editable = !running;
  const metaDirty = meta.title !== ch.title || meta.topics !== ch.topics;

  // Keep the list in place after a chunk/exercise edit instead of refetching
  // the whole chapter (and resetting every open editor).
  const patchChunkLocal = (updated) =>
    setCh((prev) => {
      const next = prev.chunks.map((c) => (c.id === updated.id ? updated : c));
      return {
        ...prev,
        chunks: next,
        flagged_count: next.filter((c) => c.flags.length).length,
        pinned_count: next.filter((c) => c.pinned).length,
        has_unpublished_changes: prev.published_at
          ? true
          : prev.has_unpublished_changes,
      };
    });

  async function run(label, fn, success) {
    setBusy(label);
    setError(null);
    setNotice(null);
    try {
      await fn();
      if (success) setNotice(success);
    } catch (err) {
      fail(err);
    } finally {
      setBusy(null);
    }
  }

  const saveMeta = (e) => {
    e.preventDefault();
    run(
      "meta",
      async () => {
        const data = await updateChapter(id, meta);
        setCh(data);
        setMeta({ title: data.title, topics: data.topics });
      },
      "Informations enregistrées."
    );
  };

  const doPublish = () =>
    run(
      "publish",
      async () => {
        await publishChapter(id);
        await load();
      },
      null
    );

  const doUnpublish = () =>
    run(
      "unpublish",
      async () => {
        setCh(await unpublishChapter(id));
      },
      "Chapitre retiré : les élèves ne le voient plus."
    );

  const doReplace = (file) =>
    run(
      "replace",
      async () => {
        await uploadChapterSource({ id, file, replace: true });
        setMeta(null);
        await load();
      },
      null
    );

  const doDocument = (file) =>
    run(
      "document",
      async () => {
        await uploadChapterDocument(id, file);
        await load();
      },
      "PDF élève enregistré."
    );

  const doDelete = () =>
    run("delete", async () => {
      await deleteChapter(id);
      navigate("/admin/chapitres", { replace: true });
    });

  return (
    <div className="adm-page">
      <Link to="/admin/chapitres" className="adm-back">
        ← Chapitres
      </Link>

      <header className="adm-head">
        <div>
          <h1 className="adm-h1">
            Chapitre {ch.id} — {ch.title}
          </h1>
          <p className="adm-sub">
            <span className={`adm-tag adm-tag-${st.tone}`}>{st.label}</span>
            {ch.has_unpublished_changes && (
              <span className="adm-tag adm-tag-warn">Modifications non publiées</span>
            )}
            <span>
              {ch.source_kind === "markdown" ? "Cours .md" : "PDF extrait"} ·{" "}
              {ch.source_filename}
              {ch.has_document && (
                <>
                  {" · "}
                  <a
                    href={chapterPdfUrl(id)}
                    target="_blank"
                    rel="noreferrer"
                    className="adm-link"
                  >
                    ouvrir le PDF
                  </a>
                </>
              )}
            </span>
            {ch.published_at && <span>Publié le {fullDate(ch.published_at)}</span>}
          </p>
        </div>
        <div className="adm-head-actions">
          {ch.published_at && (
            <button
              className="adm-btn"
              disabled={!editable || busy}
              onClick={doUnpublish}
            >
              Retirer
            </button>
          )}
          <button
            className="adm-btn adm-btn-primary"
            disabled={!editable || busy || ch.publish_problems.length > 0}
            onClick={doPublish}
            title={ch.publish_problems.join("\n")}
          >
            {ch.status === "publishing"
              ? "Publication…"
              : ch.published_at
                ? "Republier"
                : "Publier"}
          </button>
        </div>
      </header>

      {running && (
        <p className="adm-notice adm-notice-busy" role="status">
          <span className="adm-spinner adm-spinner-sm" aria-hidden="true" />
          {ch.status === "processing"
            ? "Extraction du PDF en cours…"
            : "Indexation du chapitre pour le chat en cours…"}
        </p>
      )}
      {ch.error && <p className="adm-alert">{ch.error}</p>}
      {error && (
        <p className="adm-alert" role="alert">
          {error}
        </p>
      )}
      {notice && (
        <p className="adm-notice" role="status">
          {notice}
        </p>
      )}

      {ch.status !== "processing" && ch.status !== "failed" && (
        <>
          <section className="adm-checklist" aria-label="Avant publication">
            <Check ok={ch.flagged_count === 0}>
              {ch.flagged_count
                ? `${ch.flagged_count} extrait(s) à relire`
                : "Aucun extrait signalé"}
            </Check>
            <Check ok={ch.pinned_count > 0}>
              {ch.pinned_count
                ? `${ch.pinned_count} tableau(x) de référence épinglé(s)`
                : "Épingle la fiche de syntaxe du chapitre"}
            </Check>
            <Check ok={Boolean(ch.topics.trim())}>Notions couvertes renseignées</Check>
            <Check ok={ch.exercise_count > 0} soft>
              {ch.exercise_count} exercice(s)
            </Check>
          </section>
          {ch.publish_problems.length > 0 && (
            <ul className="adm-problems">
              {ch.publish_problems.map((p) => (
                <li key={p}>{p}</li>
              ))}
            </ul>
          )}
        </>
      )}

      <div className="adm-grid-2 adm-grid-review">
        <form className="adm-panel adm-form" onSubmit={saveMeta}>
          <h2 className="adm-h2">Informations</h2>
          <label className="adm-field">
            <span>Titre affiché aux élèves</span>
            <input
              className="adm-input"
              required
              maxLength={200}
              value={meta.title}
              disabled={!editable}
              onChange={(e) => setMeta((m) => ({ ...m, title: e.target.value }))}
            />
          </label>
          <label className="adm-field">
            <span>Notions couvertes</span>
            <textarea
              className="adm-input adm-textarea"
              rows={4}
              maxLength={2000}
              disabled={!editable}
              placeholder="la structure conditionnelle simple (Si … Alors), la forme complète (Si … Sinon), les conditions composées, le choix multiple (Selon)"
              value={meta.topics}
              onChange={(e) => setMeta((m) => ({ ...m, topics: e.target.value }))}
            />
            <small className="adm-muted">
              Une liste de sujets, pas leur contenu. L'assistant s'en sert pour dire ce
              que couvre le chapitre ; il ne l'utilise jamais pour résoudre.
            </small>
          </label>
          <div className="adm-form-actions">
            <button
              className="adm-btn adm-btn-primary"
              disabled={!editable || !metaDirty || busy}
            >
              Enregistrer
            </button>
          </div>
        </form>

        <Exercises
          chapterId={id}
          items={ch.exercises}
          editable={editable}
          onChange={(exercises) =>
            setCh((prev) => ({
              ...prev,
              exercises,
              exercise_count: exercises.length,
              has_unpublished_changes: prev.published_at
                ? true
                : prev.has_unpublished_changes,
            }))
          }
          fail={fail}
        />
      </div>

      <section className="adm-panel">
        <header className="adm-panel-head adm-wrap">
          <h2 className="adm-h2">Extraits ({ch.chunk_count})</h2>
          <div className="adm-seg" role="tablist" aria-label="Filtrer les extraits">
            {FILTERS.map((f) => {
              const count =
                f.key === "flagged"
                  ? ch.flagged_count
                  : f.key === "pinned"
                    ? ch.pinned_count
                    : null;
              return (
                <button
                  key={f.key}
                  role="tab"
                  aria-selected={filter === f.key}
                  className={`adm-seg-btn${filter === f.key ? " is-on" : ""}`}
                  onClick={() => setFilter(f.key)}
                >
                  {f.label}
                  {count ? <span className="adm-seg-count">{count}</span> : null}
                </button>
              );
            })}
          </div>
        </header>
        <p className="adm-muted adm-small">
          Le PDF de l'auteur code souvent la flèche d'affectation <code>←</code> comme
          un tiret : <code>somme - a + b</code> doit se lire <code>somme ← a + b</code>.
          Corrige-le à la main ; rien n'est remplacé automatiquement, car un vrai «
          moins » ressemble exactement à la même chose.
        </p>
        <div className="adm-chunks">
          {chunks.map((c) => (
            <ChunkCard
              key={c.id}
              chapterId={id}
              chunk={c}
              editable={editable}
              onSaved={patchChunkLocal}
              onDeleted={() =>
                setCh((prev) => {
                  const next = prev.chunks.filter((x) => x.id !== c.id);
                  return {
                    ...prev,
                    chunks: next,
                    chunk_count: next.length,
                    flagged_count: next.filter((x) => x.flags.length).length,
                    pinned_count: next.filter((x) => x.pinned).length,
                  };
                })
              }
              fail={fail}
            />
          ))}
          {chunks.length === 0 && <p className="adm-empty">Rien dans ce filtre.</p>}
        </div>
      </section>

      <section className="adm-panel adm-danger">
        <h2 className="adm-h2">Fichier et suppression</h2>
        <div className="adm-danger-row">
          <div>
            <p className="adm-strong">
              PDF pour les élèves{" "}
              <span
                className={`adm-tag ${ch.has_document ? "adm-tag-ok" : "adm-tag-warn"}`}
              >
                {ch.has_document ? "Présent" : "Absent"}
              </span>
            </p>
            <p className="adm-muted adm-small">
              {ch.source_kind === "markdown"
                ? "Le cours vient du .md ; ce PDF est seulement le document que les élèves ouvrent sur la page du chapitre."
                : "Remplace le document affiché aux élèves, sans relancer l'import."}
            </p>
          </div>
          <input
            ref={documentRef}
            type="file"
            accept="application/pdf,.pdf"
            hidden
            onChange={(e) => e.target.files?.[0] && doDocument(e.target.files[0])}
          />
          <button
            className="adm-btn"
            disabled={busy}
            onClick={() => documentRef.current?.click()}
          >
            {ch.has_document ? "Remplacer le PDF" : "Ajouter un PDF"}
          </button>
        </div>
        <div className="adm-danger-row">
          <div>
            <p className="adm-strong">Renvoyer le cours corrigé</p>
            <p className="adm-muted adm-small">
              Relance l'import et remplace le brouillon (les corrections faites ici sont
              perdues). Un chapitre publié reste en ligne jusqu'à la prochaine
              publication.
            </p>
          </div>
          <input
            ref={replaceRef}
            type="file"
            accept="application/pdf,.pdf,.md,text/markdown"
            hidden
            onChange={(e) => e.target.files?.[0] && doReplace(e.target.files[0])}
          />
          <button
            className="adm-btn"
            disabled={!editable || busy}
            onClick={() => replaceRef.current?.click()}
          >
            Choisir un fichier
          </button>
        </div>
        <div className="adm-danger-row">
          <div>
            <p className="adm-strong">Supprimer le chapitre</p>
            <p className="adm-muted adm-small">
              Retire le chapitre du chat et du catalogue, et efface le PDF et la
              relecture.
            </p>
          </div>
          {confirmDelete ? (
            <span className="adm-confirm">
              <button className="adm-btn" onClick={() => setConfirmDelete(false)}>
                Annuler
              </button>
              <button
                className="adm-btn adm-btn-danger"
                disabled={busy === "delete"}
                onClick={doDelete}
              >
                Supprimer le chapitre {ch.id}
              </button>
            </span>
          ) : (
            <button
              className="adm-btn adm-btn-danger-ghost"
              disabled={!editable}
              onClick={() => setConfirmDelete(true)}
            >
              Supprimer
            </button>
          )}
        </div>
      </section>
    </div>
  );
}

function Check({ ok, soft = false, children }) {
  return (
    <span className={`adm-check-item ${ok ? "is-ok" : soft ? "is-soft" : "is-todo"}`}>
      <span aria-hidden="true">{ok ? "✓" : soft ? "•" : "!"}</span>
      {children}
    </span>
  );
}

function ChunkCard({ chapterId, chunk, editable, onSaved, onDeleted, fail }) {
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState(chunk.content);
  const [label, setLabel] = useState(chunk.pin_label ?? "");
  const [saving, setSaving] = useState(false);

  async function save(body) {
    setSaving(true);
    try {
      const updated = await updateChunk(chapterId, chunk.id, body);
      onSaved(updated);
      setText(updated.content);
      setLabel(updated.pin_label ?? "");
      return true;
    } catch (err) {
      fail(err);
      return false;
    } finally {
      setSaving(false);
    }
  }

  return (
    <article
      className={`adm-chunk${chunk.flags.length ? " is-flagged" : ""}${chunk.pinned ? " is-pinned" : ""}`}
    >
      <header className="adm-chunk-head">
        <span className="adm-muted">
          p. {chunk.page ?? "?"} · {chunk.section || "—"} ·{" "}
          <span className="adm-chunk-type">{chunk.type}</span>
        </span>
        <span className="adm-chunk-flags">
          {chunk.flags.map((f) => (
            <span key={f} className="adm-tag adm-tag-warn">
              {FLAG_LABELS[f] ?? f}
            </span>
          ))}
          {chunk.pinned && (
            <span className="adm-tag adm-tag-admin">📌 {chunk.pin_label}</span>
          )}
        </span>
      </header>

      {editing ? (
        <textarea
          className="adm-input adm-textarea adm-mono"
          rows={Math.min(18, Math.max(4, text.split("\n").length + 1))}
          value={text}
          onChange={(e) => setText(e.target.value)}
          aria-label="Contenu de l'extrait"
        />
      ) : (
        <pre className="adm-chunk-body">{chunk.content}</pre>
      )}

      {chunk.pinned && editing && (
        <label className="adm-field">
          <span>Libellé de l'épingle</span>
          <input
            className="adm-input"
            value={label}
            onChange={(e) => setLabel(e.target.value)}
          />
        </label>
      )}

      <footer className="adm-chunk-actions">
        {editing ? (
          <>
            <button
              className="adm-btn"
              onClick={() => {
                setText(chunk.content);
                setLabel(chunk.pin_label ?? "");
                setEditing(false);
              }}
            >
              Annuler
            </button>
            <button
              className="adm-btn adm-btn-primary"
              disabled={saving || !text.trim()}
              onClick={async () => {
                const body = { content: text };
                if (chunk.pinned) body.pin_label = label;
                if (await save(body)) setEditing(false);
              }}
            >
              Enregistrer
            </button>
          </>
        ) : (
          <>
            {/* Any course chunk can be the reference sheet, not only a detected
                table: chapter 2's syntax (Si … Alors) is laid out as text, and
                restricting pins to tables left nothing pinnable. Série chunks
                are excluded - an exercise is not syntax. */}
            {chunk.type !== "exercice" || chunk.pinned ? (
              <button
                className="adm-btn"
                disabled={!editable || saving}
                onClick={() => save({ pinned: !chunk.pinned })}
              >
                {chunk.pinned ? "Désépingler" : "📌 Épingler comme référence"}
              </button>
            ) : null}
            <button
              className="adm-btn"
              disabled={!editable}
              onClick={() => setEditing(true)}
            >
              Modifier
            </button>
            <button
              className="adm-btn adm-btn-danger-ghost"
              disabled={!editable || saving}
              onClick={async () => {
                try {
                  await deleteChunk(chapterId, chunk.id);
                  onDeleted();
                } catch (err) {
                  fail(err);
                }
              }}
            >
              Retirer
            </button>
          </>
        )}
      </footer>
    </article>
  );
}

function Exercises({ chapterId, items, editable, onChange, fail }) {
  const [openId, setOpenId] = useState(null);
  const [draft, setDraft] = useState({ title: "", question: "" });

  async function saveExisting(ex) {
    try {
      const updated = await updateExercise(chapterId, ex.id, {
        title: draft.title,
        question: draft.question,
      });
      onChange(items.map((e) => (e.id === ex.id ? updated : e)));
      setOpenId(null);
    } catch (err) {
      fail(err);
    }
  }

  async function create() {
    try {
      const created = await addExercise(chapterId, draft);
      onChange([...items, created]);
      setOpenId(null);
    } catch (err) {
      fail(err);
    }
  }

  return (
    <section className="adm-panel">
      <header className="adm-panel-head">
        <h2 className="adm-h2">Exercices ({items.length})</h2>
        <button
          className="adm-btn"
          disabled={!editable}
          onClick={() => {
            setDraft({ title: `Exercice ${items.length + 1}`, question: "" });
            setOpenId("new");
          }}
        >
          + Ajouter
        </button>
      </header>
      <ul className="adm-ex-list">
        {openId === "new" && (
          <li className="adm-ex is-open">
            <ExerciseEditor
              draft={draft}
              setDraft={setDraft}
              onCancel={() => setOpenId(null)}
              onSave={create}
            />
          </li>
        )}
        {items.map((ex) => (
          <li key={ex.id} className={`adm-ex${openId === ex.id ? " is-open" : ""}`}>
            {openId === ex.id ? (
              <ExerciseEditor
                draft={draft}
                setDraft={setDraft}
                onCancel={() => setOpenId(null)}
                onSave={() => saveExisting(ex)}
              />
            ) : (
              <div className="adm-ex-row">
                <div className="adm-list-main">
                  <span className="adm-strong">{ex.title}</span>
                  <span className="adm-muted adm-clamp">{ex.question}</span>
                </div>
                <span className="adm-confirm">
                  <button
                    className="adm-btn"
                    disabled={!editable}
                    onClick={() => {
                      setDraft({ title: ex.title, question: ex.question });
                      setOpenId(ex.id);
                    }}
                  >
                    Modifier
                  </button>
                  <button
                    className="adm-btn adm-btn-danger-ghost"
                    disabled={!editable}
                    aria-label={`Supprimer ${ex.title}`}
                    onClick={async () => {
                      try {
                        await deleteExercise(chapterId, ex.id);
                        onChange(items.filter((e) => e.id !== ex.id));
                      } catch (err) {
                        fail(err);
                      }
                    }}
                  >
                    ✕
                  </button>
                </span>
              </div>
            )}
          </li>
        ))}
        {items.length === 0 && openId !== "new" && (
          <li className="adm-empty">Aucun exercice détecté.</li>
        )}
      </ul>
    </section>
  );
}

function ExerciseEditor({ draft, setDraft, onCancel, onSave }) {
  return (
    <div className="adm-form">
      <input
        className="adm-input"
        value={draft.title}
        maxLength={120}
        aria-label="Titre de l'exercice"
        onChange={(e) => setDraft((d) => ({ ...d, title: e.target.value }))}
      />
      <textarea
        className="adm-input adm-textarea"
        rows={5}
        value={draft.question}
        aria-label="Énoncé"
        placeholder="Énoncé de l'exercice"
        onChange={(e) => setDraft((d) => ({ ...d, question: e.target.value }))}
      />
      <div className="adm-form-actions">
        <button className="adm-btn" onClick={onCancel}>
          Annuler
        </button>
        <button
          className="adm-btn adm-btn-primary"
          disabled={!draft.title.trim() || !draft.question.trim()}
          onClick={onSave}
        >
          Enregistrer
        </button>
      </div>
    </div>
  );
}
