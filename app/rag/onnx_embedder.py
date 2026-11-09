"""The embedding model without torch, for hosts with little memory.

paraphrase-multilingual-MiniLM-L12-v2 through sentence-transformers needs torch:
about 1.5 GB of RAM in the backend. The same model exported to ONNX and
quantized to int8 (Xenova/paraphrase-multilingual-MiniLM-L12-v2,
onnx/model_quantized.onnx, 118 MB) runs on onnxruntime in a few hundred MB,
which is what a free 512 MB host allows.

Same tokenizer, same mean pooling, same 128-token limit as the
sentence-transformers model, so its vectors land next to the ones already in
Qdrant (cosine > 0.99, checked by tests/test_onnx_embedder.py) and the index
does not have to be rebuilt.

Selected with EMBEDDING_BACKEND=onnx (app/rag/rag_store.get_model). Only the
encode() call the code uses is implemented.
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np

ONNX_REPO = os.environ.get("ONNX_EMBEDDING_REPO", "Xenova/paraphrase-multilingual-MiniLM-L12-v2")
ONNX_FILE = os.environ.get("ONNX_EMBEDDING_FILE", "onnx/model_quantized.onnx")
# The tokenizer as the original SentencePiece model (5 MB, ~20 MB in memory).
# tokenizer.json through the `tokenizers` library holds the 250k-piece
# vocabulary in about 280 MB - more than the model itself, and the difference
# between fitting in 512 MB or not.
SPM_REPO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
SPM_FILE = "sentencepiece.bpe.model"
MAX_TOKENS = 128  # the sentence-transformers model's max_seq_length
BATCH = 32

# XLM-RoBERTa's ids: fairseq specials first, then SentencePiece ids shifted by
# one (HF XLMRobertaTokenizer: fairseq_offset = 1; SentencePiece's own <unk>,
# id 0, becomes <unk> = 3).
BOS, PAD, EOS, UNK = 0, 1, 2, 3


def model_files() -> tuple[Path, Path]:
    """(model.onnx, sentencepiece model), downloaded once into the Hugging Face cache."""
    from huggingface_hub import hf_hub_download

    return (
        Path(hf_hub_download(ONNX_REPO, ONNX_FILE)),
        Path(hf_hub_download(SPM_REPO, SPM_FILE)),
    )


class OnnxEmbedder:
    def __init__(self) -> None:
        import onnxruntime as ort
        import sentencepiece as spm

        model_path, spm_path = model_files()
        self.sp = spm.SentencePieceProcessor(model_file=str(spm_path))
        options = ort.SessionOptions()
        # One request at a time on a shared CPU: more threads only add memory.
        options.intra_op_num_threads = int(os.environ.get("ONNX_THREADS", "1"))
        options.inter_op_num_threads = 1
        options.enable_cpu_mem_arena = False
        self.session = ort.InferenceSession(
            str(model_path), options, providers=["CPUExecutionProvider"]
        )
        self.input_names = {i.name for i in self.session.get_inputs()}

    def token_ids(self, text: str) -> list[int]:
        pieces = [p + 1 if p else UNK for p in self.sp.encode(text, out_type=int)]
        return [BOS, *pieces[: MAX_TOKENS - 2], EOS]

    def _batch(self, texts: list[str]) -> np.ndarray:
        rows = [self.token_ids(t) for t in texts]
        width = max(len(r) for r in rows)
        ids = np.full((len(rows), width), PAD, dtype=np.int64)
        mask = np.zeros((len(rows), width), dtype=np.int64)
        for i, r in enumerate(rows):
            ids[i, : len(r)] = r
            mask[i, : len(r)] = 1
        feeds = {"input_ids": ids, "attention_mask": mask}
        if "token_type_ids" in self.input_names:
            feeds["token_type_ids"] = np.zeros_like(ids)
        tokens = self.session.run(None, feeds)[0]  # (batch, seq, dim)
        weights = mask[..., None].astype(np.float32)
        return (tokens * weights).sum(axis=1) / np.clip(weights.sum(axis=1), 1e-9, None)

    def encode(
        self,
        sentences: str | list[str],
        normalize_embeddings: bool = False,
        show_progress_bar: bool = False,  # noqa: ARG002 - sentence-transformers' signature
        batch_size: int = BATCH,
        **_: object,
    ) -> np.ndarray:
        single = isinstance(sentences, str)
        texts = [sentences] if single else list(sentences)
        if not texts:
            return np.zeros((0, 384), dtype=np.float32)
        out = np.concatenate(
            [self._batch(texts[i : i + batch_size]) for i in range(0, len(texts), batch_size)]
        ).astype(np.float32)
        if normalize_embeddings:
            out /= np.clip(np.linalg.norm(out, axis=1, keepdims=True), 1e-12, None)
        return out[0] if single else out
