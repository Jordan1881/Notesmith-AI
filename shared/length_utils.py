from __future__ import annotations

def target_words_from_length(length: str) -> int:
    mapping = {
        "half_page": 250,
        "one_page": 500,
        "two_three_pages": 1100,
    }
    if length not in mapping:
        raise ValueError(f"Unsupported length: {length}")
    return mapping[length]