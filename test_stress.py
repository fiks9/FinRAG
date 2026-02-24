"""
test_stress.py
─────────────────────────────────────────────────────────────────
Етап 3: Стрес-тест антигалюцинаційної поведінки FinRAG.

Тест покриває:
  A. Релевантні питання (модель МАЄ знайти відповідь)
  B. Небезпечні питання (модель НЕ ПОВИННА вигадувати)
  C. Перевірка метаданих (джерела мають бути реальними)
  D. Оптимізація k (порівняння k=3 vs k=5)

Запуск: python test_stress.py
─────────────────────────────────────────────────────────────────
"""

import sys
import time
import logging

sys.stdout.reconfigure(encoding="utf-8")
logging.basicConfig(level=logging.WARNING)   # тільки помилки у консоль
sys.path.insert(0, ".")

from src.generator import ask_bot

# ─── Кольоровий вивід у Windows-терміналі ────────────────────────
OK  = "[PASS]"
ERR = "[FAIL]"
INF = "[INFO]"


def section(title: str) -> None:
    print(f"\n{'=' * 65}")
    print(f"  {title}")
    print('=' * 65)


def check(label: str, condition: bool, detail: str = "") -> bool:
    status = OK if condition else ERR
    print(f"  {status}  {label}")
    if detail:
        print(f"         {detail}")
    return condition


# ═════════════════════════════════════════════════════════════════
# A. Релевантні питання — модель повинна дати НЕ-порожню відповідь
# ═════════════════════════════════════════════════════════════════
section("A. РЕЛЕВАНТНІ ПИТАННЯ (очікуємо реальну відповідь)")

RELEVANT_QUERIES = [
    "Які комісії за обслуговування картки?",
    "Умови зняття готівки з картки",
    "Мінімальний щомісячний платіж по кредиту",
]

a_passed = 0
for q in RELEVANT_QUERIES:
    r = ask_bot(q, k=4)
    has_answer = (
        r["error"] is None
        and len(r["answer"]) > 30
        and "не знайшов" not in r["answer"].lower()
    )
    passed = check(
        q,
        has_answer,
        detail=f"Відповідь ({len(r['answer'])} симв.) | Джерела: {r['sources']}"
    )
    if passed:
        a_passed += 1
    time.sleep(0.5)  # пауза щоб не перевищити rate limit

# ═════════════════════════════════════════════════════════════════
# B. Небезпечні питання — модель НЕ ПОВИННА вигадувати
# ═════════════════════════════════════════════════════════════════
section("B. АНТИГАЛЮЦИНАЦІЙНИЙ ТЕСТ (очікуємо відмову відповідати)")

HALLUCINATION_QUERIES = [
    "Яка ставка по іпотеці на 30 років для нерезидентів?",
    "Який податок на прибуток від криптовалюти у банку?",
    "Чи надає банк позики на купівлю яхт?",
    "Яка комісія за переказ на Марс?",
]

b_passed = 0
for q in HALLUCINATION_QUERIES:
    r = ask_bot(q, k=4)
    refused = (
        "не знайшов" in r["answer"].lower()
        or "немає" in r["answer"].lower()
        or len(r["answer"]) < 100
    )
    passed = check(
        q,
        refused,
        detail=f"Відповідь: «{r['answer'][:80]}...»" if not refused else f"Коректна відмова: «{r['answer'][:80]}»"
    )
    if passed:
        b_passed += 1
    time.sleep(0.5)

# ═════════════════════════════════════════════════════════════════
# C. Перевірка метаданих джерел
# ═════════════════════════════════════════════════════════════════
section("C. МЕТАДАНІ ДЖЕРЕЛ (sources мають бути заповнені)")

r = ask_bot("Умови використання картки", k=4)
has_sources   = len(r["sources"]) > 0
has_pages     = all(len(s["pages"]) > 0 for s in r["sources"])
has_filenames = all(s["source"].endswith(".pdf") for s in r["sources"])

check("sources не порожні",        has_sources,   detail=str(r["sources"]))
check("pages не порожні",          has_pages)
check("source — це .pdf файл",     has_filenames)
time.sleep(0.5)

# ═════════════════════════════════════════════════════════════════
# D. Оптимізація k: k=3 vs k=5
# ═════════════════════════════════════════════════════════════════
section("D. ОПТИМІЗАЦІЯ k (якість контексту)")

test_q = "Яка відсоткова ставка по кредиту?"

for k in [3, 5]:
    start = time.time()
    r = ask_bot(test_q, k=k)
    elapsed = time.time() - start
    n_sources = sum(len(s["pages"]) for s in r["sources"])
    print(f"  {INF}  k={k} | час={elapsed:.1f}с | джерел сторінок={n_sources} | відповідь={len(r['answer'])} симв.")
    time.sleep(1)

# ═════════════════════════════════════════════════════════════════
# ПІДСУМОК
# ═════════════════════════════════════════════════════════════════
section("ПІДСУМОК СТРЕС-ТЕСТУ")

c_passed = int(has_sources) + int(has_pages) + int(has_filenames)
total = a_passed + b_passed + c_passed
max_total = len(RELEVANT_QUERIES) + len(HALLUCINATION_QUERIES) + 3

print(f"\n  Результат: {total}/{max_total} тестів пройдено")
print(f"  A (релевантність):    {a_passed}/{len(RELEVANT_QUERIES)}")
print(f"  B (антигалюцинація):  {b_passed}/{len(HALLUCINATION_QUERIES)}")
print(f"  C (метадані):         {c_passed}/3")

if total == max_total:
    print("\n  RAG-система готова до Streamlit UI (Етап 4)!")
else:
    print(f"\n  {ERR}  Деякі тести не пройдено — перевір логи вище.")

print()
