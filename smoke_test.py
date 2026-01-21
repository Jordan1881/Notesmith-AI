from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

from agent.agent import summarize_file_for_exam


def main() -> None:
    # Load .env from project root (safe; file is ignored by git)
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing. Make sure .env exists in project root.")

    # Pick a test file from project root (change if needed)
    root = Path(__file__).resolve().parent
    test_txt = root / "testText.txt"

    if not test_txt.exists():
        raise FileNotFoundError(f"Test file not found: {test_txt}")

    # Run an end-to-end summarization
    res = summarize_file_for_exam(str(test_txt), length="one_page")

    if not res.ok:
        raise RuntimeError(f"Summarization failed: {res.reason}")

    print("✅ E2E smoke test passed")
    print(f"Used chunking: {res.used_chunking}")
    print(f"Chars: {res.char_count}")
    print(f"Tokens: {res.input_tokens}")
    print(f"Chunks: {res.chunks_count}")
    print(f"Words: {res.actual_words}/{res.target_words}")
    print("\n--- SUMMARY (first 600 chars) ---\n")
    print(res.summary_md[:600])
    print("\n--- END ---\n")


if __name__ == "__main__":
    main()