"""Chat history, per account.

Discussions used to live in the browser's localStorage under one key that
knew nothing about who was signed in, so everyone using a browser saw each
other's history. They now live in chat_sessions / chat_messages, owned by a
user, and every route here is scoped to the signed-in user's own rows.

The client keeps the discussion in memory while it is being written (the
answer streams in token by token) and saves the whole discussion here once it
settles - one PUT per discussion, not one request per token. So the write is
an upsert of the session and a replacement of its messages.

Ownership is the point of this module:
  - every read filters on user_id;
  - a PUT to an id that belongs to someone else is a 404, never an overwrite
    and never a hint that the id exists;
  - the id comes from the client (a UUID it generated when the discussion
    started), which is what lets a discussion be saved before the server has
    ever seen it - so the insert races are handled with ON CONFLICT.

Not rate-limited: nothing here reaches a model (same reasoning as
chapters.py), and the client already debounces its saves. The size caps below
keep one account from turning the table into free storage.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

import auth
from db import session_scope
from models import ChatMessage, ChatSession, User

MAX_SESSIONS_LISTED = 200
MAX_SESSIONS_PER_USER = 500
MAX_MESSAGES = 400
MAX_CONTENT_CHARS = 60_000
MAX_EXCERPTS = 40

# Statuses that only make sense while the page that started them is open. A
# discussion saved in one of them (a tab closed mid-answer) comes back as
# stopped, which is what it is.
_TRANSIENT = {"streaming", "reading", "checking"}


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
    readingKind: str | None = Field(default=None, max_length=16)


class SessionIn(BaseModel):
    title: str = Field(default="Nouvelle discussion", max_length=200)
    niveau: str = Field(default="2eme", max_length=32)
    chapitre: str = Field(default="1", max_length=32)
    createdAt: int | None = None
    messages: list[MessageIn] = Field(default_factory=list, max_length=MAX_MESSAGES)


def _ms(value: datetime) -> int:
    return int(value.timestamp() * 1000)


def _session_out(row: ChatSession) -> dict:
    """The shape the chat already uses in memory (lib/sessions.js)."""
    messages = []
    for m in row.messages:
        extra = m.extra or {}
        grounding = m.grounding_excerpts or {}
        msg: dict[str, Any] = {
            "id": extra.get("id") or f"m_{m.id}",
            "role": m.role,
            "content": m.content,
        }
        if m.role == "assistant":
            msg.update(
                status=m.checker_status,
                warnings=m.checker_warnings or [],
                pinned=grounding.get("pinned", []),
                retrieved=grounding.get("retrieved", []),
            )
            if extra.get("readingKind"):
                msg["readingKind"] = extra["readingKind"]
        if extra.get("error"):
            msg["error"] = extra["error"]
        if extra.get("attachment"):
            msg["attachment"] = extra["attachment"]
        messages.append(msg)
    return {
        "id": str(row.id),
        "title": row.title or "Nouvelle discussion",
        "niveau": row.niveau,
        "chapitre": row.chapitre,
        "createdAt": _ms(row.created_at),
        "updatedAt": _ms(row.updated_at),
        "messages": messages,
    }


def _attachment(value: dict[str, Any] | None) -> dict[str, str] | None:
    """Only the two fields the bubble shows - never the file itself."""
    if not value:
        return None
    name = str(value.get("name", ""))[:200]
    kind = value.get("kind")
    return {"name": name, "kind": kind if kind in ("image", "pdf") else "image"}


router = APIRouter(prefix="/chat/sessions", tags=["chat history"])


@router.get("")
def list_sessions(user: User = Depends(auth.get_current_user)) -> list[dict]:
    """The signed-in user's discussions, newest first."""
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
        return [_session_out(r) for r in rows]


@router.put("/{session_id}")
def save_session(
    session_id: uuid.UUID,
    payload: SessionIn,
    user: User = Depends(auth.get_current_user),
) -> dict:
    """Create or replace one of the signed-in user's discussions."""
    created = (
        datetime.fromtimestamp(payload.createdAt / 1000, tz=timezone.utc)
        if payload.createdAt
        else datetime.now(timezone.utc)
    )
    with session_scope() as db:
        row = db.execute(
            select(ChatSession).where(ChatSession.id == session_id).with_for_update()
        ).scalar_one_or_none()

        if row is None:
            count = db.scalar(
                select(ChatSession.id).where(ChatSession.user_id == user.id).limit(1).offset(
                    MAX_SESSIONS_PER_USER - 1
                )
            )
            if count is not None:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Trop de discussions enregistrées. Supprimes-en quelques-unes.",
                )
            # ON CONFLICT: two tabs saving the same new discussion at once must
            # not turn into a 500 on the primary key.
            db.execute(
                pg_insert(ChatSession)
                .values(
                    id=session_id,
                    user_id=user.id,
                    niveau=payload.niveau,
                    chapitre=payload.chapitre,
                    title=payload.title,
                    created_at=created,
                )
                .on_conflict_do_nothing(index_elements=["id"])
            )
            row = db.execute(
                select(ChatSession).where(ChatSession.id == session_id).with_for_update()
            ).scalar_one()

        # Someone else's id: the same answer as an id that does not exist.
        if row.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not found")

        row.title = payload.title
        row.niveau = payload.niveau
        row.chapitre = payload.chapitre
        row.updated_at = datetime.now(timezone.utc)

        db.execute(delete(ChatMessage).where(ChatMessage.session_id == row.id))
        for position, m in enumerate(payload.messages):
            status_value = m.status
            if m.role == "assistant" and status_value in _TRANSIENT:
                status_value = "stopped"
            extra = {
                k: v
                for k, v in {
                    "id": m.id,
                    "error": m.error,
                    "attachment": _attachment(m.attachment),
                    "readingKind": m.readingKind,
                }.items()
                if v
            }
            db.add(
                ChatMessage(
                    session_id=row.id,
                    role=m.role,
                    content=m.content,
                    position=position,
                    checker_status=status_value if m.role == "assistant" else None,
                    checker_warnings=m.warnings if m.role == "assistant" else None,
                    grounding_excerpts=(
                        {"pinned": m.pinned, "retrieved": m.retrieved}
                        if m.role == "assistant"
                        else None
                    ),
                    extra=extra or None,
                )
            )
        db.flush()
        return {"id": str(row.id), "updatedAt": _ms(row.updated_at)}


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_session(
    session_id: uuid.UUID,
    user: User = Depends(auth.get_current_user),
) -> Response:
    """Delete one of the signed-in user's discussions. Idempotent, and
    silent about ids that belong to someone else."""
    with session_scope() as db:
        db.execute(
            delete(ChatSession).where(
                ChatSession.id == session_id, ChatSession.user_id == user.id
            )
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)
