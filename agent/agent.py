from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from tools.files import extract_document_text
from tools.study import summarize_exam_he
from shared.token_utils import (
    count_tokens,
    split_text_into_token_chunks,
    target_words_from_length,
)


@dataclass
class AgentResult:
    ok: bool
    summary_md: str
    used_chunking: bool
    char_count: int
    input_tokens: int
    chunks_count: int
    target_words: int
    actual_words: int
    reason: Optional[str] = None


def summarize_file_for_exam(
    file_path: str,
    length: str = "one_page",
    target_words_override: int | None = None
) -> AgentResult:
    extracted = extract_document_text(file_path)

    if not extracted.meta.extraction_success:
        return AgentResult(
            ok=False,
            summary_md="",
            used_chunking=False,
            char_count=0,
            input_tokens=0,
            chunks_count=0,
            target_words=0,
            actual_words=0,
            reason=extracted.meta.reason
        )

    text = extracted.text
    char_count = len(text)

    input_tokens = count_tokens(text)
    base_target = target_words_from_length(length)
    target_words = int(target_words_override) if target_words_override else base_target

    CHUNKING_THRESHOLD = 35_000
    used_chunking = input_tokens > CHUNKING_THRESHOLD

    try:
        # -------------------------
        # Case 1: No chunking
        # -------------------------
        if not used_chunking:
            summary_md = summarize_exam_he(
                content=text,
                length=length,
                target_words=target_words
            )
            actual_words = len(summary_md.split())

            return AgentResult(
                ok=True,
                summary_md=summary_md,
                used_chunking=False,
                char_count=char_count,
                input_tokens=input_tokens,
                chunks_count=1,
                target_words=target_words,
                actual_words=actual_words,
                reason=None
            )

        # -------------------------
        # Case 2: Chunking
        # -------------------------
        chunks = split_text_into_token_chunks(
            text,
            max_tokens_per_chunk=20_000,
            overlap_tokens=250
        )

        per_chunk_words = max(160, target_words // max(1, len(chunks)))

        chunk_summaries: list[str] = []

        for i, ch in enumerate(chunks, start=1):
            chunk_summary = summarize_exam_he(
                content=ch,
                length=length,
                target_words=per_chunk_words
            )
            chunk_summaries.append(f"## Chunk {i}\n{chunk_summary}")

        merged_notes = "\n\n".join(chunk_summaries)

        final_summary = summarize_exam_he(
            content=merged_notes,
            length=length,
            target_words=target_words
        )

        actual_words = len(final_summary.split())

        return AgentResult(
            ok=True,
            summary_md=final_summary,
            used_chunking=True,
            char_count=char_count,
            input_tokens=input_tokens,
            chunks_count=len(chunks),
            target_words=target_words,
            actual_words=actual_words,
            reason=None
        )

    except Exception as e:
        return AgentResult(
            ok=False,
            summary_md="",
            used_chunking=used_chunking,
            char_count=char_count,
            input_tokens=input_tokens,
            chunks_count=0,
            target_words=target_words,
            actual_words=0,
            reason=f"exception: {type(e).__name__}: {e}"
        )