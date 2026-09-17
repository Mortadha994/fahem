"""Chat history, per account.

Discussions live in chat_sessions / chat_messages, owned by a user, and every
route here is scoped to the signed-in user's own rows.

  GET    /chat/sessions         the list, light: titles, dates, a version, and
                                a skeleton of each message (id, role, status,
                                the student's text) - never the answers or the
                                course excerpts, which weighed several times
                                the text and were sent for up to 200
                                discussions at every page load
  GET    /chat/sessions/{id}    one discussion in full, loaded when opened
  PUT    /chat/sessions/{id}    save a discussion: messages are upserted by the
                                chat's own id (client_id) instead of the whole
                                discussion being deleted and re-inserted;
                                `baseVersion` makes a save from a stale copy
                                (another tab or device) a 409, not an
                                overwrite of messages it never saw
  DELETE /chat/sessions/{id}    delete one
  POST   /chat/feedback         a student's 👍 / 👎 on an answer

record_exchange() is the server-side save of one finished exchange, called by
/solve/stream at the end of an answer: an answer the student paid tokens for is
kept even if the tab is closed before the chat saves it.

Ownership is the point of this module:
  - every read filters on user_id;
  - a PUT to an id that belongs to someone else is a 404, never an overwrite
    and never a hint that the id exists;
  - the id comes from the client (a UUID it generated when the discussion
    started), so the insert races are handled with ON CONFLICT.

Not rate-limited: nothing here reaches a model. The size caps below keep one
account from turning the tables into free storage.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import case, delete, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

import auth
import runtime_settings
from db import session_scope
from models import AnswerFeedback, ChatMessage, ChatSession, User

log = logging.getLogger("fahem.chat_history")

MAX_SESSIONS_LISTED = 200
MAX_SESSIONS_PER_USER = 500
MAX_MESSAGES = 400
MAX_CONTENT_CHARS = 60_000
MAX_EXCERPTS = 40
DEFAULT_TITLE = "Nouvelle discussion"

# Statuses that only make sense while the page that started them is open. A
# discussion saved in one of them (a tab closed mid-answer) comes back as
# stopped, which is what it is.
_TRANSIENT = {"streaming", "reading", "checking", "waiting"}


class MessageIn(BaseModel):
    id: str | None = Field(default=None, max_length=80)
    role: Literal["user", "assistant"]
    content: str = Field(default="", max_length=MAX_CONTENT_CHARS)
    status: str | None = Field(default=None, max_length=32)
    warnings: list[str] = Field(default_factory=list, max_length=50)
    pinned: list[Any] = Field(default_factory=list, max_length=MAX_EXCERPTS)
    retrieved: list[Any] = Field(default_factory=list, max_length=MAX_EXCERPTS)
    error: str | None = Field(default=None, max_length=500)
    attachment: dict[str, Any] | None = None
    note: str | None = Field(default=None, max_length=500)
    readingKind: str | None = Field(default=None, max_length=16)
    route: str | None = Field(default=None, max_length=16)
    # Mode guidé: {"step": 1-4, "exerciseId": the user message it started from}.
    guided: dict[str, Any] | None = None
    # Vérifier ma réponse: {"verdict": correct|presque|a_revoir|None, "findings": [kinds]}.
    check: dict[str, Any] | None = None
    # How the student sent it: "guided" or "check" (absent: a normal message).
    mode: str | None = Field(default=None, max_length=16)
    # Exercice similaire: {"difficulty": easier|same|harder}.
    practice: dict[str, Any] | None = None


def _practice(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    level = value.get("difficulty")
    return {"difficulty": level if level in ("easier", "same", "harder") else "same"}


def _guided(value: dict[str, Any] | None) -> dict[str, Any] | None:
    """Only the known keys, bounded - these rows are written by the browser."""
    if not isinstance(value, dict):
        return None
    step = value.get("step")
    if not isinstance(step, int) or not 1 <= step <= 4:
        return None
    out: dict[str, Any] = {"step": step}
    if isinstance(value.get("exerciseId"), str):
        out["exerciseId"] = value["exerciseId"][:80]
    if value.get("leak") is True:
        out["leak"] = True  # a hint step that gave the whole solution (api.solve_stream)
    return out


def _check(value: dict[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    verdict = value.get("verdict")
    findings = value.get("findings")
    return {
        "verdict": verdict if verdict in ("correct", "presque", "a_revoir") else None,
        "findings": [str(k)[:16] for k in findings[:20]] if isinstance(findings, list) else [],
    }


class SessionIn(BaseModel):
    title: str = Field(default=DEFAULT_TITLE, max_length=200)
    niveau: str = Field(default="2eme", max_length=32)
    chapitre: str = Field(default="1", max_length=32)
    createdAt: int | None = None
    # The version the client's copy was loaded or last saved at. Absent: an
    # older client, saved without the check.
    baseVersion: int | None = None
    messages: list[MessageIn] = Field(default_factory=list, max_length=MAX_MESSAGES)


class FeedbackIn(BaseModel):
    session_id: uuid.UUID
    message_id: str = Field(min_length=1, max_length=80)
    # 1 = 👍, -1 = 👎, 0 = take the feedback back.
    rating: Literal[-1, 0, 1]
    comment: str | None = Field(default=None, max_length=500)


def _ms(value: datetime) -> int:
    return int(value.timestamp() * 1000)


def _client_id(m: ChatMessage) -> str:
    return m.client_id or (m.extra or {}).get("id") or f"m_{m.id}"


def _message_out(m: ChatMessage, feedback: dict[str, int]) -> dict[str, Any]:
    extra = m.extra or {}
    grounding = m.grounding_excerpts or {}
    cid = _client_id(m)
    msg: dict[str, Any] = {"id": cid, "role": m.role, "content": m.content}
    if m.role == "assistant":
        msg.update(
            status=m.checker_status,
            warnings=m.checker_warnings or [],
            pinned=grounding.get("pinned", []),
            retrieved=grounding.get("retrieved", []),
        )
        for key in ("readingKind", "route", "guided", "check", "practice"):
            if extra.get(key):
                msg[key] = extra[key]
        if cid in feedback:
            msg["feedback"] = feedback[cid]
    for key in ("error", "attachment", "note", "mode"):
        if extra.get(key):
            msg[key] = extra[key]
    return msg


def _session_head(row: ChatSession) -> dict[str, Any]:
    return {
        "id": str(row.id),
        "title": row.title or DEFAULT_TITLE,
        "niveau": row.niveau,
        "chapitre": row.chapitre,
        "createdAt": _ms(row.created_at),
        "updatedAt": _ms(row.updated_at),
        "version": row.version,
    }


def _attachment(value: dict[str, Any] | None) -> dict[str, str] | None:
    """Only the two fields the bubble shows - never the file itself."""
    if not value:
        return None
    name = str(value.get("name", ""))[:200]
    kind = value.get("kind")
    return {"name": name, "kind": kind if kind in ("image", "pdf") else "image"}


def _owned_session(db, session_id: uuid.UUID, user_id: uuid.UUID) -> ChatSession:
    row = db.get(ChatSession, session_id)
    if row is None or row.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
    return row


def _apply_message(row: ChatMessage, m: MessageIn, position: int) -> bool:
    """Write one incoming message onto its row. Returns whether anything changed."""
    status_value = m.status
    if m.role == "assistant" and status_value in _TRANSIENT:
        status_value = "stopped"
    content = m.content
    # A copy of the discussion that never loaded the answers (a bug, an old
    # client) must not erase them: an empty answer does not replace a written
    # one, unless it is an error.
    if m.role == "assistant" and not content and row.content and status_value != "error":
        content = row.content
    extra = {
        k: v
        for k, v in {
            "id": m.id,
            "error": m.error,
            "attachment": _attachment(m.attachment),
            "note": m.note,
            "readingKind": m.readingKind,
            "route": m.route,
            "guided": _guided(m.guided),
            "check": _check(m.check),
            "practice": _practice(m.practice),
            "mode": m.mode if m.mode in ("guided", "check", "practice") else None,
        }.items()
        if v
    } or None
    grounding = {"pinned": m.pinned, "retrieved": m.retrieved} if m.role == "assistant" else None
    if m.role == "assistant" and not m.pinned and not m.retrieved and row.grounding_excerpts:
        grounding = row.grounding_excerpts  # same protection as the content
    values = {
        "role": m.role,
        "content": content,
        "position": position,
        "checker_status": status_value if m.role == "assistant" else None,
        "checker_warnings": m.warnings if m.role == "assistant" else None,
        "grounding_excerpts": grounding,
        "extra": extra,
    }
    changed = False
    for key, value in values.items():
        if getattr(row, key) != value:
            setattr(row, key, value)
            changed = True
    return changed


# --- routes --------------------------------------------------------------------------

router = APIRouter(prefix="/chat", tags=["chat history"])


@router.get("/features")
def chat_features(_user: User = Depends(auth.get_current_user)) -> dict[str, Any]:
    """What the chat offers right now, as the admin set it: Mode guidé,
    Vérifier ma réponse, and the mode a new discussion starts in."""
    guided = bool(runtime_settings.get("guided_mode_enabled"))
    return {
        "guided": guided,
        "check": bool(runtime_settings.get("check_answer_enabled")),
        "attachments": bool(runtime_settings.get("attachments_enabled")),
        "practice": bool(runtime_settings.get("practice_enabled")),
        "defaultMode": runtime_settings.get("default_chat_mode") if guided else "full",
    }


@router.get("/sessions")
def list_sessions(user: User = Depends(auth.get_current_user)) -> list[dict]:
    """The signed-in user's discussions, newest first, without their answers.

    Each carries `loaded: false` and a skeleton of its messages - enough for
    the history panel, the home screen and the progress cards (who spoke,
    each answer's status, the student's own text) - and the chat fetches the
    full discussion when it is opened."""
    with session_scope() as db:
        rows = (
            db.execute(
                select(ChatSession)
                .where(ChatSession.user_id == user.id)
                .order_by(ChatSession.updated_at.desc())
                .limit(MAX_SESSIONS_LISTED)
            )
            .scalars()
            .all()
        )
        ids = [r.id for r in rows]
        skeleton: dict[uuid.UUID, list[dict]] = {i: [] for i in ids}
        if ids:
            for sid, mid, cid, extra_id, role, st, text in db.execute(
                select(
                    ChatMessage.session_id,
                    ChatMessage.id,
                    ChatMessage.client_id,
                    ChatMessage.extra["id"].astext,
                    ChatMessage.role,
                    ChatMessage.checker_status,
                    case((ChatMessage.role == "user", ChatMessage.content), else_=""),
                )
                .where(ChatMessage.session_id.in_(ids))
                .order_by(ChatMessage.session_id, ChatMessage.position)
            ):
                item = {"id": cid or extra_id or f"m_{mid}", "role": role, "content": text}
                if role == "assistant":
                    item["status"] = st
                skeleton[sid].append(item)
        return [{**_session_head(r), "loaded": False, "messages": skeleton[r.id]} for r in rows]


@router.get("/sessions/{session_id}")
def read_session(session_id: uuid.UUID, user: User = Depends(auth.get_current_user)) -> dict:
    """One of the signed-in user's discussions, in full."""
    with session_scope() as db:
        row = _owned_session(db, session_id, user.id)
        feedback = dict(
            db.execute(
                select(AnswerFeedback.message_client_id, AnswerFeedback.rating).where(
                    AnswerFeedback.session_id == row.id
                )
            ).all()
        )
        return {
            **_session_head(row),
            "loaded": True,
            "messages": [_message_out(m, feedback) for m in row.messages],
        }


def _create_session_row(
    db, session_id, user_id, *, niveau, chapitre, title, created
) -> ChatSession:
    count = db.scalar(
        select(ChatSession.id)
        .where(ChatSession.user_id == user_id)
        .limit(1)
        .offset(MAX_SESSIONS_PER_USER - 1)
    )
    if count is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Trop de discussions enregistrées. Supprimes-en quelques-unes.",
        )
    # ON CONFLICT: two tabs saving the same new discussion at once must not
    # turn into a 500 on the primary key.
    db.execute(
        pg_insert(ChatSession)
        .values(
            id=session_id,
            user_id=user_id,
            niveau=niveau,
            chapitre=chapitre,
            title=title,
            created_at=created,
        )
        .on_conflict_do_nothing(index_elements=["id"])
    )
    return db.execute(
        select(ChatSession).where(ChatSession.id == session_id).with_for_update()
    ).scalar_one()


@router.put("/sessions/{session_id}")
def save_session(
    session_id: uuid.UUID,
    payload: SessionIn,
    user: User = Depends(auth.get_current_user),
) -> dict:
    """Create or update one of the signed-in user's discussions."""
    created = (
        datetime.fromtimestamp(payload.createdAt / 1000, tz=timezone.utc)
        if payload.createdAt
        else datetime.now(timezone.utc)
    )
    with session_scope() as db:
        row = db.execute(
            select(ChatSession).where(ChatSession.id == session_id).with_for_update()
        ).scalar_one_or_none()
        is_new = row is None
        if is_new:
            row = _create_session_row(
                db,
                session_id,
                user.id,
                niveau=payload.niveau,
                chapitre=payload.chapitre,
                title=payload.title,
                created=created,
            )

        # Someone else's id: the same answer as an id that does not exist.
        if row.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")

        if not is_new and payload.baseVersion is not None and payload.baseVersion != row.version:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"code": "stale", "version": row.version},
            )

        existing = {_client_id(m): m for m in row.messages}
        keep: set[str] = set()
        changed = is_new
        for position, m in enumerate(payload.messages):
            cid = m.id or f"p_{position}"
            keep.add(cid)
            target = existing.get(cid)
            if target is None:
                target = ChatMessage(session_id=row.id, client_id=cid)
                db.add(target)
                changed = True
            elif target.client_id != cid:
                target.client_id = cid
            if _apply_message(target, m, position):
                changed = True
        for cid, m in existing.items():
            if cid not in keep:
                db.delete(m)
                changed = True

        for key in ("title", "niveau", "chapitre"):
            if getattr(row, key) != getattr(payload, key):
                setattr(row, key, getattr(payload, key))
                changed = True
        if changed:
            row.version += 1
            row.updated_at = datetime.now(timezone.utc)
        db.flush()
        return {"id": str(row.id), "updatedAt": _ms(row.updated_at), "version": row.version}


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: uuid.UUID,
    user: User = Depends(auth.get_current_user),
) -> Response:
    """Delete one of the signed-in user's discussions. Idempotent, and
    silent about ids that belong to someone else."""
    with session_scope() as db:
        db.execute(
            delete(ChatSession).where(ChatSession.id == session_id, ChatSession.user_id == user.id)
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/feedback", status_code=status.HTTP_204_NO_CONTENT)
def give_feedback(payload: FeedbackIn, user: User = Depends(auth.get_current_user)) -> Response:
    """A 👍 / 👎 on one answer of the student's own discussion (0 removes it)."""
    with session_scope() as db:
        row = _owned_session(db, payload.session_id, user.id)
        # Matched like a save matches (_client_id): a row written before the
        # client_id column only carries its id in `extra`; it gets one now.
        answer = next(
            (
                m
                for m in row.messages
                if m.role == "assistant" and _client_id(m) == payload.message_id
            ),
            None,
        )
        if answer is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")
        if answer.client_id is None:
            answer.client_id = payload.message_id
        if payload.rating == 0:
            db.execute(
                delete(AnswerFeedback).where(
                    AnswerFeedback.session_id == row.id,
                    AnswerFeedback.message_client_id == payload.message_id,
                )
            )
        else:
            db.execute(
                pg_insert(AnswerFeedback)
                .values(
                    user_id=user.id,
                    session_id=row.id,
                    message_client_id=payload.message_id,
                    rating=payload.rating,
                    comment=(payload.comment or "").strip() or None,
                )
                .on_conflict_do_update(
                    index_elements=["session_id", "message_client_id"],
                    set_={
                        "rating": payload.rating,
                        "comment": (payload.comment or "").strip() or None,
                        "updated_at": func.now(),
                    },
                )
            )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# --- the server-side save of an exchange (/solve/stream) ---------------------------------


def record_exchange(
    user_id: uuid.UUID,
    session_id: uuid.UUID,
    *,
    niveau: str,
    chapitre: str,
    title: str | None,
    user_message: dict[str, Any],
    assistant_message: dict[str, Any],
) -> int | None:
    """Save the student's message and the answer at the end of an answer.

    Both are upserted by their client ids and placed at the end of the
    discussion if they are new; the discussion is created if the chat had not
    saved it yet. Returns the discussion's new version (the chat saves on top
    of it), or None when it could not be saved - someone else's id, the
    per-account cap - which the answer itself never depends on."""
    try:
        with session_scope() as db:
            row = db.execute(
                select(ChatSession).where(ChatSession.id == session_id).with_for_update()
            ).scalar_one_or_none()
            if row is None:
                row = _create_session_row(
                    db,
                    session_id,
                    user_id,
                    niveau=niveau,
                    chapitre=chapitre,
                    title=(title or DEFAULT_TITLE)[:200],
                    created=datetime.now(timezone.utc),
                )
            if row.user_id != user_id:
                return None
            if title and (row.title or DEFAULT_TITLE) == DEFAULT_TITLE:
                row.title = title[:200]
            existing = {_client_id(m): m for m in row.messages}
            last = max((m.position for m in row.messages), default=-1)
            for data in (user_message, assistant_message):
                incoming = MessageIn(**data)
                target = existing.get(incoming.id)
                if target is None:
                    last += 1
                    target = ChatMessage(session_id=row.id, client_id=incoming.id)
                    db.add(target)
                    position = last
                else:
                    position = target.position
                _apply_message(target, incoming, position)
            row.version += 1
            row.updated_at = datetime.now(timezone.utc)
            db.flush()
            return row.version
    except HTTPException:
        return None
    except Exception:
        log.warning("could not save the exchange of session %s", session_id, exc_info=True)
        return None
