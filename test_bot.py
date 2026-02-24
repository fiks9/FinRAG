"""
test_bot.py
End-to-end тест FinRAG: Retrieval → Groq Llama → Відповідь + Джерела
Запуск: python test_bot.py
"""
import sys
import logging

sys.stdout.reconfigure(encoding='utf-8')

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
sys.path.insert(0, ".")

from src.generator import ask_bot

# ─── Тест 1: Питання, що є в документі ───────────────────────────
print("\n" + "=" * 65)
print("ТЕСТ 1: Питання про комісію (відповідь має бути в документі)")
print("=" * 65)

result = ask_bot("Яка комісія за зняття готівки?")

print(f"\n📝 ВІДПОВІДЬ:\n{result['answer']}")
print(f"\n🔗 ДЖЕРЕЛА:")
for s in result["sources"]:
    pages = ", ".join(str(p) for p in s["pages"])
    print(f"   📄 {s['source']} | стор. {pages}")

# ─── Тест 2: Питання, якого НЕ МАЄ в документі (антигалюцинація) ──
print("\n" + "=" * 65)
print("ТЕСТ 2: Питання якого НЕМАЄ в документі (тест антигалюцинації)")
print("=" * 65)

result2 = ask_bot("Яка ставка по іпотеці на 30 років для нерезидентів?")

print(f"\n📝 ВІДПОВІДЬ:\n{result2['answer']}")
print(f"\n🔗 ДЖЕРЕЛА:")
for s in result2["sources"]:
    pages = ", ".join(str(p) for p in s["pages"])
    print(f"   📄 {s['source']} | стор. {pages}")

print("\n" + "=" * 65)
print("✅ End-to-end тест завершено")
print("=" * 65)
