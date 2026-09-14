"""Reading an exercise from a photo or a PDF the student attaches in the chat.

The output is plain text - the exercise statement - and nothing else. The
chat then sends that text through /solve/stream exactly as if the student had
typed it: the gatekeeper classifies it, the grounded pipeline answers it, the
checker runs. So an attachment adds no new path to the solver; the only new
thing is turning pixels or a PDF into words.

  PDF with a text layer   pdfplumber, no model call - instant and free.
  scanned PDF, or image   a vision model on Groq transcribes it.

The vision model is asked to transcribe, never to solve. Its reply is still
treated as untrusted text (it is what the student sent, after all): it goes
through the same classifier as a typed message, so a photo of "ignore your
instructions" is exactly as harmless as typing it.

Types are recognised from the bytes, never from the filename or the
Content-Type header - both are whatever the client says.
"""

from __future__ import annotations

import base64
import io
import json
import os
import re
import urllib.error
import urllib.request
from dataclasses import dataclass

from config import (
    ATTACHMENT_MAX_BYTES,
    ATTACHMENT_MAX_PDF_PAGES,
    ATTACHMENT_MAX_TEXT_CHARS,
    GROQ_URL,
    GROQ_VISION_MODEL,
    load_env,
)

load_env()

PDF_MAGIC = b"%PDF"
PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"

# A PDF whose text layer holds fewer characters than this is treated as a
# scan: a real exercise statement is longer, and a scanned PDF's "text" is
# usually empty or a few stray glyphs.
_MIN_PDF_TEXT_CHARS = 40

# The longest side sent to the vision model. Enough to read a phone photo of
# a page; keeps the base64 payload well under Groq's request size limit.
_VISION_MAX_SIDE = 1600

UNREADABLE = "ILLISIBLE"

TRANSCRIBE_PROMPT = f"""Tu transcris un exercice d'algorithmique photographié ou scanné par un
élève. Recopie fidèlement, en français, tout le texte de l'exercice visible
sur l'image : le titre, l'énoncé, les données, les questions, et s'il y en a
les lignes d'algorithme ou de code telles qu'elles sont écrites, et les
tableaux (ligne par ligne).

Règles :
- Ne résous rien, n'explique rien, n'ajoute aucun commentaire.
- Ne corrige pas les fautes : recopie ce qui est écrit.
- Garde les symboles tels quels (←, ≤, ≥, ≠, %, ...).
- Si l'image ne contient aucun texte d'exercice lisible, réponds
  uniquement : {UNREADABLE}"""


class AttachmentError(Exception):
    """A problem the student can act on. `status` maps to the HTTP code."""

    def __init__(self, message: str, status: int = 422):
        super().__init__(message)
        self.message = message
        self.status = status


@dataclass
class Extraction:
    text: str
    source: str  # "image" | "pdf" (text layer) | "pdf-scan"
    pages: int


def sniff(data: bytes) -> str | None:
    """'pdf', 'png', 'jpeg', 'webp', or None."""
    if data.startswith(PDF_MAGIC):
        return "pdf"
    if data.startswith(PNG_MAGIC):
        return "png"
    if data.startswith(JPEG_MAGIC):
        return "jpeg"
    if len(data) >= 12 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp"
    return None


def extract(data: bytes) -> Extraction:
    if not data:
        raise AttachmentError("Le fichier est vide.")
    if len(data) > ATTACHMENT_MAX_BYTES:
        raise AttachmentError(
            f"Le fichier est trop volumineux (maximum {ATTACHMENT_MAX_BYTES // (1024 * 1024)} Mo).",
            status=413,
        )
    kind = sniff(data)
    if kind is None:
        raise AttachmentError(
            "Envoie une photo (JPEG, PNG ou WebP) ou un PDF.", status=415
        )
    if kind == "pdf":
        return _from_pdf(data)
    return Extraction(text=_finish(_transcribe([_prepare_image(data)])), source="image", pages=1)


# --- PDF ---------------------------------------------------------------------


def _from_pdf(data: bytes) -> Extraction:
    import pdfplumber

    try:
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            total = len(pdf.pages)
            pages = pdf.pages[:ATTACHMENT_MAX_PDF_PAGES]
            text = "\n\n".join((page.extract_text() or "").strip() for page in pages).strip()
            if len(text) >= _MIN_PDF_TEXT_CHARS:
                return Extraction(text=_finish(text), source="pdf", pages=min(total, len(pages)))
            # No usable text layer: a scan. Render the pages and read them.
            images = [
                _encode_jpeg(page.to_image(resolution=150).original) for page in pages
            ]
    except AttachmentError:
        raise
    except Exception as exc:  # corrupt or encrypted PDF
        raise AttachmentError("Impossible d'ouvrir ce PDF. Essaie une photo de l'exercice.") from exc

    return Extraction(text=_finish(_transcribe(images)), source="pdf-scan", pages=len(images))


# --- images ------------------------------------------------------------------


def _prepare_image(data: bytes) -> str:
    """Decode, normalise orientation, shrink, re-encode as JPEG base64."""
    from PIL import Image, ImageOps

    try:
        image = Image.open(io.BytesIO(data))
        image = ImageOps.exif_transpose(image)  # phone photos taken sideways
    except Exception as exc:
        raise AttachmentError("Impossible de lire cette image.") from exc
    return _encode_jpeg(image)


def _encode_jpeg(image) -> str:
    image = image.convert("RGB")
    image.thumbnail((_VISION_MAX_SIDE, _VISION_MAX_SIDE))
    buffer = io.BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


# --- vision model --------------------------------------------------------------

_THINK = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def _transcribe(images_b64: list[str]) -> str:
    content = [{"type": "text", "text": TRANSCRIBE_PROMPT}]
    for image in images_b64:
        content.append(
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image}"}}
        )
    payload = json.dumps(
        {
            "model": GROQ_VISION_MODEL,
            "temperature": 0,
            "max_tokens": 1500,
            "messages": [{"role": "user", "content": content}],
        }
    ).encode("utf-8")
    request = urllib.request.Request(
        GROQ_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {os.environ['GROQ_API_KEY']}",
            "Content-Type": "application/json",
            # Groq's edge rejects urllib's default agent (see generate.py).
            "User-Agent": "algo-rag/0.1",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 429:
            raise AttachmentError(
                "Le service est très sollicité. Réessaie dans une minute.", status=429
            ) from exc
        raise AttachmentError(
            "La lecture de l'image a échoué. Réessaie, ou recopie l'énoncé.", status=502
        ) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise AttachmentError(
            "La lecture de l'image a échoué. Réessaie, ou recopie l'énoncé.", status=502
        ) from exc

    message = body["choices"][0]["message"]
    # Some Qwen releases inline their reasoning in <think> tags; only the
    # transcription after it is wanted.
    return _THINK.sub("", message.get("content") or "").strip()


def _finish(text: str) -> str:
    text = text.strip()
    # A vision model sometimes wraps the transcription in a sentence of its
    # own ("Voici le texte exact :"); that is not the student's exercise.
    text = re.sub(r"^(voici|here is)[^\n]{0,60}:\s*\n", "", text, flags=re.IGNORECASE).strip()
    if not text or UNREADABLE in text.upper()[:40]:
        raise AttachmentError(
            "Je n'arrive pas à lire d'exercice sur ce fichier. Essaie une photo plus nette, "
            "bien éclairée et de face."
        )
    return text[:ATTACHMENT_MAX_TEXT_CHARS]
