from __future__ import annotations

from dataclasses import dataclass

try:
    import tiktoken
except ImportError:
    tiktoken = None


@dataclass(frozen=True)
class LengthPreset:
    name: str
    target_words: int


PRESETS = {
    "half_page": LengthPreset(name="half_page", target_words=300),
    "one_page": LengthPreset(name="one_page", target_words=550),
    "two_three_pages": LengthPreset(name="two_three_pages", target_words=1100),
}


def target_words_from_length(length: str) -> int:
    # Map UI preset to a word budget used by the prompts
    preset = PRESETS.get(length)
    if not preset:
        raise ValueError(f"unknown_length_preset: {length}")
    return preset.target_words


def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    # Count tokens using tiktoken when available; fall back to a rough estimate otherwise
    if not text:
        return 0

    if tiktoken is None:
        # Rough fallback: ~4 chars per token in English; Hebrew can vary
        return max(1, len(text) // 4)

    try:
        enc = tiktoken.encoding_for_model(model)
    except Exception:
        enc = tiktoken.get_encoding("cl100k_base")

    return len(enc.encode(text))


def split_text_into_token_chunks(
    text: str,
    max_tokens_per_chunk: int,
    overlap_tokens: int = 200,
    model: str = "gpt-4o-mini",
) -> list[str]:
    # Split text into token-bounded chunks with overlap for context continuity
    if not text.strip():
        return []

    if max_tokens_per_chunk <= 0:
        raise ValueError("max_tokens_per_chunk must be > 0")
    if overlap_tokens < 0:
        raise ValueError("overlap_tokens must be >= 0")
    if overlap_tokens >= max_tokens_per_chunk:
        raise ValueError("overlap_tokens must be < max_tokens_per_chunk")

    if tiktoken is None:
        # Fallback: chunk by characters if tiktoken is not installed
        approx_chars = max_tokens_per_chunk * 4
        overlap_chars = overlap_tokens * 4
        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = min(len(text), start + approx_chars)
            chunks.append(text[start:end])
            if end == len(text):
                break
            start = max(0, end - overlap_chars)
        return chunks

    try:
        enc = tiktoken.encoding_for_model(model)
    except Exception:
        enc = tiktoken.get_encoding("cl100k_base")

    tokens = enc.encode(text)
    chunks: list[str] = []

    start = 0
    n = len(tokens)

    while start < n:
        end = min(n, start + max_tokens_per_chunk)
        chunk_tokens = tokens[start:end]
        chunk_text = enc.decode(chunk_tokens)
        chunks.append(chunk_text)

        if end == n:
            break

        start = max(0, end - overlap_tokens)

    return chunks