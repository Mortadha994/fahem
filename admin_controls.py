"""The admin console's AI controls: read and change the live settings.

  GET  /admin/controls                  settings (value, default, last change),
                                        the daily budget, the queues, the
                                        recent admin actions
  PUT  /admin/controls                  change one or more settings; validated
                                        all together, logged in admin_audit
  POST /admin/controls/queues/reset     empty one model's Groq queue

What each setting does is in runtime_settings.py; where it takes effect is in
ai_control.py. Same router-level admin gate as admin.py.

Resetting a queue is an emergency tool, for a line that looks stuck: it drops
every ticket and lease. Requests still waiting simply re-enter the line on
their next poll; a request holding a slot finishes its call, so for a moment
one more call than max_concurrent may run. Leases expire on their own, so it
is rarely needed.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException
from pydantic import BaseModel

import ai_control
import auth
import llm_queue
import public_overview
import runtime_settings
from config import GROQ_MODEL, GROQ_VISION_MODEL
from models import User

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_current_admin)],
)


class SettingOut(BaseModel):
    value: Any
    default: Any
    updated_at: datetime | None
    updated_by: str | None


class BudgetOut(BaseModel):
    used: int
    limit: int
    guard_pct: int
    threshold: int | None
    blocking: bool


class QueueOut(BaseModel):
    model: str
    label: str
    waiting: int | None
    active: int | None
    max_concurrent: int


class AuditOut(BaseModel):
    at: datetime
    admin_email: str
    action: str
    target: str | None
    detail: dict | None


class ControlsOut(BaseModel):
    settings: dict[str, SettingOut]
    budget: BudgetOut
    queues: list[QueueOut]
    audit: list[AuditOut]


class QueueReset(BaseModel):
    model: str


def _models() -> list[tuple[str, str]]:
    models = [(GROQ_MODEL, "Texte")]
    if GROQ_VISION_MODEL != GROQ_MODEL:
        models.append((GROQ_VISION_MODEL, "Vision"))
    return models


def _queues() -> list[QueueOut]:
    out = []
    for model, label in _models():
        try:
            snap = llm_queue.snapshot_sync(llm_queue.groq_queue_key(model))
            waiting, active = snap.waiting, snap.active
        except Exception:
            waiting = active = None
        out.append(
            QueueOut(
                model=model,
                label=label,
                waiting=waiting,
                active=active,
                max_concurrent=llm_queue.groq_max_concurrent(model),
            )
        )
    return out


def _controls() -> ControlsOut:
    return ControlsOut(
        settings={k: SettingOut(**v) for k, v in runtime_settings.snapshot().items()},
        budget=BudgetOut(**ai_control.budget_status(fresh=True)),
        queues=_queues(),
        audit=[AuditOut(**a) for a in runtime_settings.recent_audit()],
    )


@router.get("/controls", response_model=ControlsOut)
def read_controls() -> ControlsOut:
    return _controls()


@router.put("/controls", response_model=ControlsOut)
def update_controls(
    values: dict[str, Any] = Body(..., examples=[{"ai_paused": True}]),
    me: User = Depends(auth.get_current_admin),
) -> ControlsOut:
    try:
        changed = runtime_settings.set_many(values, me.email)
    except runtime_settings.InvalidSetting as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if "daily_budget_guard_pct" in changed:
        ai_control.clear_budget_cache()
    if "attachments_enabled" in changed:
        public_overview.clear_cache()  # the landing page stops/starts claiming photos
    return _controls()


@router.post("/controls/queues/reset", response_model=ControlsOut)
def reset_queue(payload: QueueReset, me: User = Depends(auth.get_current_admin)) -> ControlsOut:
    if payload.model not in dict(_models()):
        raise HTTPException(status_code=404, detail="Modèle inconnu.")
    key = llm_queue.groq_queue_key(payload.model)
    llm_queue._sync_client().delete(*llm_queue.all_keys(key))
    runtime_settings.audit(me.email, "queue.reset", payload.model)
    return _controls()
