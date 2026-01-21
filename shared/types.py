from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ExtractMeta:
    char_count: int
    page_estimate: int
    extraction_success: bool
    reason: Optional[str] = None


@dataclass
class ExtractResult:
    text: str
    meta: ExtractMeta


import tiktoken

def count_tokens(text: str, model: str = "gpt-4o-mini") -> int:
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))
