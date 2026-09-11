"""Fahem's transactional email: three templates and one way to send them.

These are security emails (a reset link, "someone asked about your account"),
so the design goal is *recognisability*, not decoration:

- One layout for all three - same header, same footer, same closing line - so
  a student who has seen one real Fahem email can tell when another is not.
- Inline styles, a single 480px column, table-based button, system fonts.
  Email clients strip <style> blocks and ignore most modern CSS; this is the
  subset every client renders the same way.
- Light palette only, taken from the live tokens in ui/src/App.css. Clients
  that force dark mode recolour inconsistently; `color-scheme: light` asks
  them not to.
- French, in the app's own voice ("tu", short direct sentences), and every
  email has a plain-text part as well as HTML.

Anything a user typed (display_name) is HTML-escaped before it reaches a
template - an email body is an injection target like any other page.

Sending goes to Resend's HTTP API with `requests` (already a dependency via
google-auth) rather than their SDK: it is one POST, and one fewer package on
the auth path is one fewer thing to keep patched.
"""

from __future__ import annotations

import html
import logging
from dataclasses import dataclass

import requests

from config import (
    APP_BASE_URL,
    EMAIL_FROM,
    RESEND_API_KEY,
    RESET_TOKEN_TTL_SECONDS,
    VERIFY_TOKEN_TTL_SECONDS,
)

log = logging.getLogger("fahem.email")

RESEND_URL = "https://api.resend.com/emails"

# ui/src/App.css, :root (light). Duplicated rather than parsed out of the CSS:
# an email must not break because the stylesheet was refactored.
ACCENT = "#3f6fb5"
ACCENT_FG = "#ffffff"  # 5.06:1 on ACCENT
FG = "#18181b"
FG_DIM = "#6b7280"  # 4.83:1 on white
BG = "#ffffff"
BG_ALT = "#f7f7f8"
LINE = "#e4e4e7"
FONT = "system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"

# Identical on every email, word for word. Consistency is part of what makes a
# genuine email recognisable next to an imitation.
IGNORE_LINE = "Si tu n'es pas à l'origine de cette demande, ignore cet e-mail."
FOOTER_LINE = "Fahem — ton tuteur d'algorithmique"


class EmailConfigurationError(RuntimeError):
    """RESEND_API_KEY is not set."""


class EmailSendError(RuntimeError):
    """The provider refused or could not be reached."""


@dataclass(frozen=True)
class Email:
    to: str
    subject: str
    html: str
    text: str


def duration_fr(seconds: int) -> str:
    """3600 -> '1 heure', 86400 -> '24 heures', 900 -> '15 minutes'.

    Derived from the configured TTL so an email can never promise a lifetime
    the token does not actually have.
    """
    if seconds % 3600 == 0:
        hours = seconds // 3600
        return f"{hours} heure" + ("s" if hours > 1 else "")
    minutes = max(1, seconds // 60)
    return f"{minutes} minute" + ("s" if minutes > 1 else "")


# --- layout -------------------------------------------------------------------


def _p(content_html: str) -> str:
    return (
        f'<p style="margin:0 0 14px;font-family:{FONT};font-size:16px;'
        f'line-height:1.55;color:{FG};">{content_html}</p>'
    )


def _layout(
    *,
    title: str,
    preheader: str,
    paragraphs_html: list[str],
    cta_label: str,
    cta_url: str,
    notice: str | None,
    show_link_fallback: bool,
) -> str:
    """The one HTML shell every Fahem email uses. Arguments are plain text
    except paragraphs_html, which the caller has already escaped."""
    t = html.escape(title)
    url_attr = html.escape(cta_url, quote=True)
    body = "".join(_p(p) for p in paragraphs_html)

    notice_row = (
        f'<tr><td style="padding:4px 32px 0;font-family:{FONT};font-size:14px;'
        f'line-height:1.5;color:{FG};"><strong>{html.escape(notice)}</strong></td></tr>'
        if notice
        else ""
    )
    fallback_row = (
        f'<tr><td style="padding:16px 32px 0;font-family:{FONT};font-size:13px;'
        f'line-height:1.5;color:{FG_DIM};">Si le bouton ne fonctionne pas, copie ce lien '
        f'dans ton navigateur :<br><a href="{url_attr}" style="color:{ACCENT};'
        f'word-break:break-all;">{html.escape(cta_url)}</a></td></tr>'
        if show_link_fallback
        else ""
    )

    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<meta name="supported-color-schemes" content="light">
<title>{t}</title>
</head>
<body style="margin:0;padding:0;background:{BG_ALT};">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;">{html.escape(preheader)}</div>
<table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:{BG_ALT};">
<tr><td align="center" style="padding:32px 16px;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="max-width:480px;background:{BG};border:1px solid {LINE};border-radius:14px;">
    <tr><td style="padding:28px 32px 0;font-family:{FONT};font-size:20px;font-weight:700;color:{ACCENT};">Fahem</td></tr>
    <tr><td style="padding:18px 32px 4px;">
      <h1 style="margin:0 0 14px;font-family:{FONT};font-size:22px;line-height:1.3;font-weight:700;color:{FG};">{t}</h1>
      {body}
    </td></tr>
    <tr><td style="padding:6px 32px 14px;">
      <table role="presentation" cellpadding="0" cellspacing="0" border="0"><tr>
        <td style="border-radius:10px;background:{ACCENT};">
          <a href="{url_attr}" style="display:inline-block;padding:13px 22px;font-family:{FONT};font-size:16px;font-weight:600;line-height:1.2;color:{ACCENT_FG};text-decoration:none;border-radius:10px;">{html.escape(cta_label)}</a>
        </td>
      </tr></table>
    </td></tr>
    {notice_row}
    {fallback_row}
    <tr><td style="padding:24px 32px 28px;">
      <div style="border-top:1px solid {LINE};padding-top:16px;font-family:{FONT};font-size:13px;line-height:1.5;color:{FG_DIM};">{html.escape(IGNORE_LINE)}</div>
    </td></tr>
  </table>
  <p style="margin:16px 0 0;font-family:{FONT};font-size:12px;color:{FG_DIM};">{html.escape(FOOTER_LINE)}</p>
</td></tr>
</table>
</body>
</html>"""


def _plain(
    *, title: str, paragraphs: list[str], cta_label: str, cta_url: str, notice: str | None
) -> str:
    parts = ["Fahem", "", title, "", *[p + "\n" for p in paragraphs]]
    parts += [f"{cta_label} :", cta_url, ""]
    if notice:
        parts += [notice, ""]
    parts += ["--", IGNORE_LINE, FOOTER_LINE]
    return "\n".join(parts)


# --- the three emails ---------------------------------------------------------


def verification_email(to: str, display_name: str, url: str) -> Email:
    title = "Confirme ton adresse e-mail"
    name = display_name.strip()
    lines = [
        f"Bienvenue sur Fahem, {name} !",
        "Confirme ton adresse e-mail : c'est elle qui te permettra de récupérer "
        "ton compte si tu oublies ton mot de passe.",
    ]
    notice = f"Ce lien expire dans {duration_fr(VERIFY_TOKEN_TTL_SECONDS)}."
    cta = "Confirmer mon adresse"
    return Email(
        to=to,
        subject=f"{title} – Fahem",
        html=_layout(
            title=title,
            preheader="Un clic pour confirmer ton adresse sur Fahem.",
            paragraphs_html=[html.escape(line) for line in lines],
            cta_label=cta,
            cta_url=url,
            notice=notice,
            show_link_fallback=True,
        ),
        text=_plain(title=title, paragraphs=lines, cta_label=cta, cta_url=url, notice=notice),
    )


def reset_email(to: str, url: str) -> Email:
    title = "Réinitialise ton mot de passe"
    lines = [
        "Quelqu'un — probablement toi — a demandé à réinitialiser le mot de passe "
        "du compte Fahem lié à cette adresse.",
        "Ton mot de passe actuel reste valable tant que tu n'en choisis pas un nouveau.",
    ]
    notice = (
        f"Ce lien expire dans {duration_fr(RESET_TOKEN_TTL_SECONDS)} "
        "et ne fonctionne qu'une seule fois."
    )
    cta = "Choisir un nouveau mot de passe"
    return Email(
        to=to,
        subject=f"{title} – Fahem",
        html=_layout(
            title=title,
            preheader="Ton lien pour choisir un nouveau mot de passe.",
            paragraphs_html=[html.escape(line) for line in lines],
            cta_label=cta,
            cta_url=url,
            notice=notice,
            show_link_fallback=True,
        ),
        text=_plain(title=title, paragraphs=lines, cta_label=cta, cta_url=url, notice=notice),
    )


def google_account_email(to: str) -> Email:
    """Sent instead of a reset link when the address belongs to a Google
    account. The API caller sees the same generic response either way; only
    the real inbox owner learns which kind of account it is."""
    title = "Ton compte Fahem utilise Google"
    lines = [
        "Quelqu'un — probablement toi — a demandé à réinitialiser le mot de passe "
        "du compte Fahem lié à cette adresse.",
        "Ce compte a été créé avec Google : il n'a pas de mot de passe Fahem. "
        "Pour te connecter, utilise le bouton « Se connecter avec Google ».",
        "Aucun lien de réinitialisation n'a été créé.",
    ]
    cta = "Aller sur Fahem"
    return Email(
        to=to,
        subject=f"{title} – Fahem",
        html=_layout(
            title=title,
            preheader="Ce compte se connecte avec Google, pas avec un mot de passe.",
            paragraphs_html=[html.escape(line) for line in lines],
            cta_label=cta,
            cta_url=APP_BASE_URL,
            notice=None,
            show_link_fallback=False,
        ),
        text=_plain(
            title=title, paragraphs=lines, cta_label=cta, cta_url=APP_BASE_URL, notice=None
        ),
    )


# --- sending --------------------------------------------------------------------


def send(email: Email) -> str:
    """Send through Resend and return the provider's message id. Raises on any
    failure - callers that must not fail use send_quietly()."""
    if not RESEND_API_KEY:
        raise EmailConfigurationError("RESEND_API_KEY is not set; refusing to pretend to send")
    try:
        resp = requests.post(
            RESEND_URL,
            headers={"Authorization": f"Bearer {RESEND_API_KEY}"},
            json={
                "from": EMAIL_FROM,
                "to": [email.to],
                "subject": email.subject,
                "html": email.html,
                "text": email.text,
            },
            timeout=10,
        )
    except requests.RequestException as exc:
        raise EmailSendError(f"could not reach Resend: {type(exc).__name__}") from None
    if resp.status_code >= 300:
        # Resend's error body describes the problem (bad key, unverified
        # domain); it never echoes the message we sent, so it is safe to keep.
        raise EmailSendError(f"Resend answered {resp.status_code}: {resp.text[:300]}")
    return resp.json().get("id", "")


def send_quietly(email: Email, kind: str) -> None:
    """For background tasks after the response has gone out: never raises.

    Logs the kind and the provider id or the failure - never the body, the
    subject line's recipient-specific parts, or the link, which is a live
    credential until it is spent or expires.
    """
    try:
        message_id = send(email)
        log.warning("email sent: kind=%s id=%s", kind, message_id)
    except Exception as exc:  # noqa: BLE001 - a background send must not crash the worker
        log.error("email NOT sent: kind=%s reason=%s", kind, exc)
