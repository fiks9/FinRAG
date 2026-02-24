"""
src/ingest.py
─────────────────────────────────────────────────────────────────
Ingestion Pipeline (Етап 1):
  PDF-файли → Chunks з метаданими → Embeddings → ChromaDB

Запуск:
    python -m src.ingest
    # або з кастомною теченою:
    python -m src.ingest --pdf_dir data/raw --db_dir data/chromadb
─────────────────────────────────────────────────────────────────
"""

import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

# ─────────────────────────────────────────────────────────────────
# Конфігурація
# ─────────────────────────────────────────────────────────────────

load_dotenv()

# Розташування директорій (відносно кореня проекту)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PDF_DIR = PROJECT_ROOT / "data" / "raw"
DEFAULT_DB_DIR  = PROJECT_ROOT / "data" / "chromadb"

# Параметри чанкінгу (відповідно до Design Doc)
CHUNK_SIZE    = 900   # символів — достатньо для одного логічного блоку тарифів
CHUNK_OVERLAP = 200   # символів — не даємо розривати речення / рядки таблиць

# Мультилінгвальна embedding-модель (підтримує українську, безкоштовна)
EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# Назва колекції у ChromaDB
CHROMA_COLLECTION = "finrag_tariffs"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# Допоміжні функції
# ─────────────────────────────────────────────────────────────────

def load_pdfs(pdf_dir: Path) -> list[Document]:
    """
    Завантажує всі PDF з зазначеної директорії.
    Додає до метаданих: source (ім'я файлу) та page (номер сторінки).
    Повертає список об'єктів Document.
    """
    if not pdf_dir.exists():
        log.error("Директорія з PDF не знайдена: %s", pdf_dir)
        sys.exit(1)

    pdf_files = list(pdf_dir.glob("*.pdf"))

    if not pdf_files:
        log.warning(
            "У директорії '%s' немає PDF-файлів.\n"
            "→ Поклади хоча б один .pdf-файл у data/raw/ і запусти скрипт знову.",
            pdf_dir,
        )
        sys.exit(0)

    all_docs: list[Document] = []

    for pdf_path in pdf_files:
        log.info("📄  Завантаження: %s", pdf_path.name)
        try:
            loader = PyPDFLoader(str(pdf_path))
            docs = loader.load()  # кожен елемент = одна сторінка PDF

            # Нормалізуємо метадані — залишаємо тільки те, що нам потрібно
            for doc in docs:
                doc.metadata = {
                    "source": pdf_path.name,          # напр. "Tariff_Credit_Card.pdf"
                    "page":   doc.metadata.get("page", 0) + 1,  # 1-indexed
                }

            all_docs.extend(docs)
            log.info("   ✔ Завантажено сторінок: %d", len(docs))

        except Exception as exc:
            log.error("   ✘ Помилка при завантаженні %s: %s", pdf_path.name, exc)

    log.info("─" * 50)
    log.info("Всього завантажено сторінок: %d з %d PDF-файлів", len(all_docs), len(pdf_files))
    return all_docs


def split_documents(docs: list[Document]) -> list[Document]:
    """
    Розбиває документи на чанки за стратегією з Design Doc:
    - size=900 / overlap=200
    - Пріоритет розбиття: абзаци → рядки → речення
    - Зберігає оригінальні метадані (source, page) у кожному чанку
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", "! ", "? ", " ", ""],
        length_function=len,
        add_start_index=True,   # додає позицію початку чанку в метадані
    )

    chunks = splitter.split_documents(docs)

    log.info(
        "Чанкінг завершено: %d сторінок → %d чанків (size=%d, overlap=%d)",
        len(docs), len(chunks), CHUNK_SIZE, CHUNK_OVERLAP,
    )

    # Статистика для дебагу
    if chunks:
        sizes = [len(c.page_content) for c in chunks]
        log.info(
            "Розміри чанків: мін=%d, макс=%d, середній=%d символів",
            min(sizes), max(sizes), int(sum(sizes) / len(sizes)),
        )

    return chunks


def build_vector_store(chunks: list[Document], db_dir: Path) -> Chroma:
    """
    Ініціалізує локальну ChromaDB і зберігає вектори.
    Завжди очищує стару колекцію перед записом — запобігає дублікатам.
    """
    db_dir.mkdir(parents=True, exist_ok=True)

    log.info("Завантаження embedding-моделі: %s", EMBEDDING_MODEL)
    log.info("    (Перший запуск може зайняти 1-2 хвилини)")

    embeddings = HuggingFaceEmbeddings(
        model_name=EMBEDDING_MODEL,
        model_kwargs={"device": "cpu"},
        encode_kwargs={"normalize_embeddings": True},
    )

    # Видаляємо стару колекцію якщо вона є — запобігаємо дублікатам
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(db_dir))
        existing = [c.name for c in client.list_collections()]
        if CHROMA_COLLECTION in existing:
            client.delete_collection(CHROMA_COLLECTION)
            log.info("Стару колекцію '%s' видалено", CHROMA_COLLECTION)
    except Exception as e:
        log.warning("Не вдалося видалити стару колекцію: %s", e)

    log.info("Збереження %d чанків у ChromaDB: %s", len(chunks), db_dir)

    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=CHROMA_COLLECTION,
        persist_directory=str(db_dir),
    )

    count = vector_store._collection.count()
    log.info("ChromaDB готова. Збережено векторів: %d", count)

    return vector_store


def verify_store(vector_store: Chroma) -> None:
    """
    Швидка перевірка: виконує один тестовий запит до бази
    і виводить найрелевантніший чанк.
    """
    test_query = "комісія за зняття готівки"
    log.info("─" * 50)
    log.info("🔍  Тестовий пошук: '%s'", test_query)

    results = vector_store.similarity_search(test_query, k=2)

    if not results:
        log.warning("   Нічого не знайдено. Перевір, чи PDF містить текст (не скан).")
        return

    for i, doc in enumerate(results, 1):
        meta = doc.metadata
        preview = doc.page_content[:200].replace("\n", " ")
        log.info(
            "   [%d] %s, стор. %s | «%s...»",
            i, meta.get("source"), meta.get("page"), preview,
        )


# ─────────────────────────────────────────────────────────────────
# Точка входу
# ─────────────────────────────────────────────────────────────────

def run_ingestion(pdf_dir: Path, db_dir: Path) -> None:
    """Головний пайплайн інгестії."""
    log.info("=" * 50)
    log.info("🚀  FinRAG Ingestion Pipeline — старт")
    log.info("   PDF:    %s", pdf_dir)
    log.info("   DB:     %s", db_dir)
    log.info("=" * 50)

    # Крок 1: Завантажити PDF
    docs = load_pdfs(pdf_dir)

    # Крок 2: Розбити на чанки
    chunks = split_documents(docs)

    # Крок 3: Зберегти у ChromaDB
    vector_store = build_vector_store(chunks, db_dir)

    # Крок 4: Верифікація
    verify_store(vector_store)

    log.info("=" * 50)
    log.info("🎉  Ingestion завершено успішно!")
    log.info("   Далі: запусти Етап 2 — src/retrieval.py")
    log.info("=" * 50)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="FinRAG — Ingestion Pipeline: PDF → ChromaDB"
    )
    parser.add_argument(
        "--pdf_dir",
        type=Path,
        default=DEFAULT_PDF_DIR,
        help=f"Директорія з PDF-файлами (за замовч.: {DEFAULT_PDF_DIR})",
    )
    parser.add_argument(
        "--db_dir",
        type=Path,
        default=DEFAULT_DB_DIR,
        help=f"Директорія для ChromaDB (за замовч.: {DEFAULT_DB_DIR})",
    )
    args = parser.parse_args()
    run_ingestion(args.pdf_dir, args.db_dir)
