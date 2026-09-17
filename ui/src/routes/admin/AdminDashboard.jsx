import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import * as m from "motion/react-m";
import {
  fetchAdminStats,
  fetchChaptersAdmin,
  fetchUsers,
  relativeTime,
  UnauthorizedError,
} from "../../lib/admin.js";
import { useAuth } from "../../lib/authContext.js";
import { SPRING_ENTER, rise, stagger } from "../../lib/motion.js";
import AdminAvatar from "../../components/admin/AdminAvatar.jsx";
import CountUp from "../../components/CountUp.jsx";
import { STATUS_LABELS, useAdminStatus } from "../../lib/adminStatus.js";
import {
  IconPause,
  IconPlay,
  IconShield,
  IconSliders,
} from "../../components/admin/icons.jsx";

const nf = new Intl.NumberFormat("fr-FR");

/**
 * "État du service": the first thing on the console's home - is the AI
 * answering students, and how much of today's Groq budget is used - with the
 * two ways to act on it. Reads the status the layout already polls
 * (AdminStatusContext), so it costs no extra request.
 */
function ServiceCard() {
  const { status, controls } = useAdminStatus();
  if (!controls) {
    return (
      <div
        className="adm-service adm-skel"
        aria-hidden="true"
        style={{ minHeight: 92 }}
      />
    );
  }
  const { budget, settings } = controls;
  const ratio = budget.limit ? Math.min(1, budget.used / budget.limit) : 0;
  const Icon =
    status === "paused" ? IconPause : status === "blocked" ? IconShield : IconPlay;
  const guard = settings.daily_budget_guard_pct.value;
  const sub =
    status === "paused"
      ? "Les élèves voient le message de maintenance. Aucune requête n'atteint l'IA."
      : status === "blocked"
        ? `Le garde-fou (${guard} %) arrête les nouvelles requêtes jusqu'à ce que le budget se libère.`
        : "Les élèves peuvent poser leurs questions normalement.";

  return (
    <m.section
      className={`adm-service is-${status}`}
      variants={rise}
      aria-label="État du service"
    >
      <span className="adm-service-icon" aria-hidden="true">
        <Icon size={22} />
      </span>
      <div>
        <p className="adm-service-title">{STATUS_LABELS[status]}</p>
        <p className="adm-service-sub">{sub}</p>
        <span
          className="adm-service-meter"
          role="img"
          aria-label={`${Math.round(ratio * 100)} % du budget de tokens du jour utilisé`}
        >
          <m.span
            initial={{ scaleX: 0 }}
            animate={{ scaleX: ratio }}
            transition={{ ...SPRING_ENTER, visualDuration: 0.8 }}
          />
        </span>
        <p className="adm-muted adm-small" style={{ margin: "6px 0 0" }}>
          {nf.format(budget.used)} / {nf.format(budget.limit)} tokens sur 24 h
          {guard ? ` · garde-fou à ${guard} %` : ""}
        </p>
      </div>
      <div className="adm-service-actions">
        <Link to="/admin/ia?onglet=controles" className="adm-btn adm-btn-primary">
          <IconSliders size={16} /> Contrôles
        </Link>
        <Link to="/admin/ia" className="adm-btn">
          Voir en direct
        </Link>
      </div>
    </m.section>
  );
}

/**
 * Console home: the numbers, the newest accounts, the chapters, and the way to
 * the rest.
 *
 * Every figure comes from /admin/stats, /admin/users or /admin/chapters. The
 * bars under the numbers are proportions of those same figures (active out of
 * all accounts, and so on) - there is no trend line, because the API has no
 * history to draw one from and an invented sparkline would be decoration
 * pretending to be data.
 *
 * The chapters panel is its own request and fails on its own: a broken
 * chapter list leaves that panel with a message, not the whole dashboard.
 */
export default function AdminDashboard() {
  const { onUnauthorized } = useAuth();
  const [stats, setStats] = useState(null);
  const [recent, setRecent] = useState(null);
  const [failed, setFailed] = useState(false);
  const [chapters, setChapters] = useState(null);
  const [chaptersFailed, setChaptersFailed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    const onError = (setter) => (err) => {
      if (cancelled) return;
      if (err instanceof UnauthorizedError) onUnauthorized();
      else setter(true);
    };
    Promise.all([fetchAdminStats(), fetchUsers({ limit: 6 })])
      .then(([s, page]) => {
        if (cancelled) return;
        setStats(s);
        setRecent(page.items);
      })
      .catch(onError(setFailed));
    fetchChaptersAdmin()
      .then((list) => !cancelled && setChapters(list))
      .catch(onError(setChaptersFailed));
    return () => {
      cancelled = true;
    };
  }, [onUnauthorized]);

  const ratio = (n) => (stats?.users ? n / stats.users : 0);
  const pct = (n) => Math.round(ratio(n) * 100);

  const cards = stats && [
    {
      label: "Comptes",
      icon: "◉",
      value: stats.users,
      hint: `${stats.students} élèves · ${stats.admins} admin${stats.admins > 1 ? "s" : ""}`,
      meter: ratio(stats.students),
      meterLabel: `${stats.students} élèves sur ${stats.users} comptes`,
    },
    {
      label: "Nouveaux (7 j)",
      icon: "✦",
      value: stats.new_last_7_days,
      hint: "créés cette semaine",
      meter: ratio(stats.new_last_7_days),
      meterLabel: `${pct(stats.new_last_7_days)} % des comptes créés cette semaine`,
    },
    {
      label: "Actifs (7 j)",
      icon: "↻",
      value: stats.active_last_7_days,
      hint: `${pct(stats.active_last_7_days)} % des comptes`,
      meter: ratio(stats.active_last_7_days),
      meterLabel: `${pct(stats.active_last_7_days)} % des comptes actifs`,
    },
    {
      label: "E-mail confirmé",
      icon: "✓",
      value: stats.verified,
      hint: `${pct(stats.verified)} % des comptes`,
      meter: ratio(stats.verified),
      meterLabel: `${pct(stats.verified)} % des comptes confirmés`,
    },
  ];

  // Counted from the list itself; "busy" is extraction or publication running.
  const chapterCounts = chapters && {
    published: chapters.filter((c) => c.status === "published").length,
    draft: chapters.filter((c) => c.status === "draft").length,
    busy: chapters.filter((c) => c.status === "processing" || c.status === "publishing")
      .length,
    failed: chapters.filter((c) => c.status === "failed").length,
    flagged: chapters.reduce((n, c) => n + (c.flagged_count ?? 0), 0),
  };

  return (
    <m.div
      className="adm-page"
      variants={stagger(0.06)}
      initial="hidden"
      animate="show"
    >
      <m.header className="adm-head" variants={rise}>
        <div>
          <h1 className="adm-h1">Tableau de bord</h1>
          <p className="adm-sub">Vue d'ensemble des comptes et des chapitres Fahem.</p>
        </div>
        <Link to="/admin/utilisateurs/nouveau" className="adm-btn adm-btn-primary">
          + Nouvel utilisateur
        </Link>
      </m.header>

      <ServiceCard />

      {failed && <p className="adm-alert">Impossible de charger les statistiques.</p>}

      <m.section
        className="adm-stats"
        aria-label="Statistiques"
        variants={stagger(0.06)}
      >
        {(cards ?? [0, 1, 2, 3]).map((c, i) =>
          c ? (
            <m.div className="adm-stat" key={c.label} variants={rise}>
              <span className="adm-stat-top">
                <span className="adm-stat-label">{c.label}</span>
                <span className="adm-stat-ico" aria-hidden="true">
                  {c.icon}
                </span>
              </span>
              {/* The count climbs for sighted readers; a screen reader gets
                  the number once. */}
              <span className="adm-stat-value">
                <CountUp value={c.value} delay={0.2 + i * 0.06} aria-hidden="true" />
                <span className="sr-only">{c.value}</span>
              </span>
              <span className="adm-stat-hint">{c.hint}</span>
              <span className="adm-meter" role="img" aria-label={c.meterLabel}>
                <m.span
                  className="adm-meter-fill"
                  initial={{ scaleX: 0 }}
                  animate={{
                    scaleX: c.meter,
                    transition: {
                      ...SPRING_ENTER,
                      visualDuration: 0.8,
                      delay: 0.3 + i * 0.06,
                    },
                  }}
                />
              </span>
            </m.div>
          ) : (
            <div className="adm-stat adm-skel" key={i} aria-hidden="true" />
          )
        )}
      </m.section>

      <div className="adm-grid-2">
        <m.section className="adm-panel" variants={rise}>
          <header className="adm-panel-head">
            <h2 className="adm-h2">Derniers inscrits</h2>
            <Link to="/admin/utilisateurs" className="adm-link">
              Tout voir →
            </Link>
          </header>
          {recent === null && !failed ? (
            <div className="adm-skel adm-skel-block" aria-hidden="true" />
          ) : (
            <m.ul className="adm-list" variants={stagger(0.04, 0.1)}>
              {(recent ?? []).map((u) => (
                <m.li key={u.id} variants={rise}>
                  <Link to={`/admin/utilisateurs/${u.id}`} className="adm-list-row">
                    <AdminAvatar
                      seed={u.id}
                      label={u.display_name || u.email}
                      size="sm"
                    />
                    <span className="adm-list-main">
                      {u.display_name ? (
                        <span className="adm-strong">{u.display_name}</span>
                      ) : (
                        <span className="adm-noname">Sans nom</span>
                      )}
                      <span className="adm-muted">{u.email}</span>
                    </span>
                    {u.role === "admin" && (
                      <span className="adm-tag adm-tag-admin">Admin</span>
                    )}
                    <span className="adm-muted adm-list-when">
                      {relativeTime(u.created_at)}
                    </span>
                  </Link>
                </m.li>
              ))}
              {recent?.length === 0 && <li className="adm-empty">Aucun compte.</li>}
            </m.ul>
          )}
        </m.section>

        <div className="adm-stack">
          <m.section className="adm-panel" variants={rise}>
            <header className="adm-panel-head">
              <h2 className="adm-h2">Chapitres</h2>
              <Link to="/admin/chapitres" className="adm-link">
                Gérer →
              </Link>
            </header>
            {chaptersFailed ? (
              <p className="adm-muted adm-small">
                Impossible de charger les chapitres.
              </p>
            ) : !chapterCounts ? (
              <div className="adm-skel adm-skel-row" aria-hidden="true" />
            ) : (
              <>
                <dl className="adm-kpis">
                  <div className="adm-kpi is-ok">
                    <dt>Publiés</dt>
                    <dd>{chapterCounts.published}</dd>
                  </div>
                  <div className="adm-kpi">
                    <dt>Brouillons</dt>
                    <dd>{chapterCounts.draft}</dd>
                  </div>
                  <div className={`adm-kpi${chapterCounts.busy ? " is-busy" : ""}`}>
                    <dt>En cours</dt>
                    <dd>{chapterCounts.busy}</dd>
                  </div>
                </dl>
                {/* The one thing on this panel that asks for action. */}
                {chapterCounts.flagged > 0 || chapterCounts.failed > 0 ? (
                  <p className="adm-callout is-warn">
                    {chapterCounts.flagged > 0 &&
                      `${chapterCounts.flagged} extrait${chapterCounts.flagged > 1 ? "s" : ""} à relire`}
                    {chapterCounts.flagged > 0 && chapterCounts.failed > 0 && " · "}
                    {chapterCounts.failed > 0 &&
                      `${chapterCounts.failed} extraction${chapterCounts.failed > 1 ? "s" : ""} en échec`}
                  </p>
                ) : (
                  <p className="adm-callout is-ok">Rien à relire.</p>
                )}
                <p className="adm-muted adm-small">
                  Le chapitre 1 est intégré à Fahem et n'est pas compté ici.
                </p>
              </>
            )}
          </m.section>

          <m.section className="adm-panel" variants={rise}>
            <header className="adm-panel-head">
              <h2 className="adm-h2">Méthodes de connexion</h2>
            </header>
            {stats && (
              <div className="adm-split">
                <div
                  className="adm-bar-track"
                  role="img"
                  aria-label={`${stats.password_accounts} comptes e-mail, ${stats.google_accounts} comptes Google`}
                >
                  <m.span
                    className="adm-bar-fill"
                    initial={{ scaleX: 0 }}
                    animate={{
                      scaleX: ratio(stats.password_accounts),
                      transition: { ...SPRING_ENTER, visualDuration: 0.9, delay: 0.35 },
                    }}
                  />
                </div>
                <dl className="adm-legend">
                  <div>
                    <dt>
                      <i className="adm-dot adm-dot-a" /> E-mail + mot de passe
                    </dt>
                    <dd>{stats.password_accounts}</dd>
                  </div>
                  <div>
                    <dt>
                      <i className="adm-dot adm-dot-b" /> Google
                    </dt>
                    <dd>{stats.google_accounts}</dd>
                  </div>
                </dl>
              </div>
            )}
          </m.section>

          <m.nav
            className="adm-panel adm-shortcuts"
            aria-label="Raccourcis"
            variants={rise}
          >
            <h2 className="adm-h2">Raccourcis</h2>
            <Link to="/admin/utilisateurs/nouveau" className="adm-shortcut">
              <span className="adm-shortcut-ico" aria-hidden="true">
                +
              </span>
              <span>
                <span className="adm-strong">Créer un compte</span>
                <span className="adm-muted adm-small">
                  Compte élève avec mot de passe
                </span>
              </span>
            </Link>
            <Link to="/admin/chapitres" className="adm-shortcut">
              <span className="adm-shortcut-ico" aria-hidden="true">
                ⇪
              </span>
              <span>
                <span className="adm-strong">Importer un chapitre</span>
                <span className="adm-muted adm-small">Markdown Fahem ou PDF</span>
              </span>
            </Link>
            <Link to="/chat" className="adm-shortcut">
              <span className="adm-shortcut-ico" aria-hidden="true">
                ←
              </span>
              <span>
                <span className="adm-strong">Tester dans le chat</span>
                <span className="adm-muted adm-small">
                  Voir ce que voient les élèves
                </span>
              </span>
            </Link>
          </m.nav>
        </div>
      </div>
    </m.div>
  );
}
