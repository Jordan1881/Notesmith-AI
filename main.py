from pathlib import Path
from agent.agent import summarize_file_for_exam

file_path = Path(__file__).resolve().parent / "testText.txt"
res = summarize_file_for_exam(str(file_path), length="half_page")

if not res.ok:
    print("❌ Failed:", res.reason)
else:
    print("✅ OK")
    print("Used chunking:", res.used_chunking)
    print("Char count:", res.char_count)
    print("\n--- SUMMARY ---\n")
    print(res.summary_md)