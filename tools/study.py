from __future__ import annotations

from typing import Optional

from openai import OpenAI
from dotenv import load_dotenv
load_dotenv()

from shared.token_utils import (
    count_tokens,
    split_text_into_token_chunks,
)
from shared.length_utils import target_words_from_length


client = OpenAI()

# -------------------------
# Core summarization prompt
# -------------------------

def _build_summary_prompt(
    content: str,
    target_words: int,
) -> str:
    return f"""
You are an expert academic study assistant.

Task:
Summarize the following content for exam preparation.

Rules:
- Write in Hebrew.
- Output must be in Markdown.
- Target length: approximately {target_words} words (±10%).
- Be structured and clear.
- Prefer definitions, key principles, comparisons, advantages/disadvantages, and examples.
- Do NOT invent information not present in the source.
- Avoid repetition and unnecessary filler.

Content:
-----
{content}
-----
""".strip()


def _call_llm(prompt: str) -> str:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You summarize academic material in Hebrew for exams."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    return (response.choices[0].message.content or "").strip()


# -------------------------
# Public API
# -------------------------

def summarize_exam_he(content: str, length: str = "one_page", target_words: int | None = None) -> str:
    """
    Summarize academic content in Hebrew for exam preparation.

    Uses token-based chunking automatically for large inputs.
    """
    text = (content or "").strip()
    if not text:
        return "❗ לא התקבל טקסט לסיכום."

    # Use override if provided, otherwise fall back to preset mapping
    base_target = target_words_from_length(length)
    TARGET_WORDS = int(target_words) if target_words and int(target_words) > 0 else base_target

    input_tokens = count_tokens(text)

    CHUNKING_THRESHOLD = 35_000
    used_chunking = input_tokens > CHUNKING_THRESHOLD

    # -------------------------
    # Case 1: Direct summary
    # -------------------------
    if not used_chunking:
        prompt = _build_summary_prompt(
            content=text,
            target_words=TARGET_WORDS,
        )
        summary_md = _call_llm(prompt)
        summary_md = _fix_length_second_pass(summary_md, TARGET_WORDS)
        return summary_md

    # -------------------------
    # Case 2: Chunked summary
    # -------------------------
    chunks = split_text_into_token_chunks(
        text,
        max_tokens_per_chunk=20_000,
        overlap_tokens=250,
    )

    per_chunk_words = max(160, TARGET_WORDS // max(1, len(chunks)))

    chunk_summaries: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        chunk_prompt = _build_summary_prompt(
            content=chunk,
            target_words=per_chunk_words,
        )
        chunk_summary = _call_llm(chunk_prompt)
        chunk_summaries.append(f"## חלק {i}\n{chunk_summary}")

    merged_notes = "\n\n".join(chunk_summaries)

    final_prompt = _build_summary_prompt(
        content=merged_notes,
        target_words=TARGET_WORDS,
    )
    final_summary = _call_llm(final_prompt)
    final_summary = _fix_length_second_pass(final_summary, TARGET_WORDS)
    return final_summary
def _count_words_he(text: str) -> int:
    return len([w for w in text.replace("\n", " ").split(" ") if w.strip()])


def _fix_length_second_pass(summary_md: str, target_words: int) -> str:
    # Expand or compress if the result is far from target
    words = _count_words_he(summary_md)
    if target_words <= 0 or words == 0:
        return summary_md

    low = int(target_words * 0.85)
    high = int(target_words * 1.15)

    if low <= words <= high:
        return summary_md

    if words < low:
        instruction = (
            f"Expand the summary to approximately {target_words} words (±10%). "
            "Keep Hebrew, keep Markdown, keep the same structure, "
            "add missing key details and examples if available, avoid repetition."
        )
    else:
        instruction = (
            f"Compress the summary to approximately {target_words} words (±10%). "
            "Keep Hebrew, keep Markdown, keep headings, remove redundancy."
        )

    prompt = f"""
{instruction}

Here is the current summary:
-----
{summary_md}
-----
""".strip()

    return _call_llm(prompt)