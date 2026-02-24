"""
src/generator.py
─────────────────────────────────────────────────────────────────
Generation-модуль: виклик Groq API (LLaMA 3),
формування відповіді та об'єднання з метаданими джерел.

Публічний API: функція ask_bot(query) → dict
─────────────────────────────────────────────────────────────────
"""

import logging
import os
from functools import lru_cache

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from src.prompts import RAG_PROMPT, format_context
from src.retrieval import retrieve, extract_sources

load_dotenv()

log = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────
# Конфігурація Groq (Llama 3)
# ─────────────────────────────────────────────────────────────────

GROQ_MODEL         = "llama-3.3-70b-versatile"
GROQ_TEMPERATURE   = 0.0   # 0 = детермінований, мінімум вигадок
GROQ_MAX_TOKENS    = 1024


# ─────────────────────────────────────────────────────────────────
# Singleton LLM
# ─────────────────────────────────────────────────────────────────

@lru_cache(maxsize=1)
def _get_llm() -> ChatGroq:
    """Повертає singleton-підключення до Groq."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY не знайдено.\n"
            "-> Скопіюй .env.example -> .env і встав свій ключ з "
            "https://console.groq.com/keys"
        )
    log.info("Ініціалізація Groq: %s (temp=%.1f)", GROQ_MODEL, GROQ_TEMPERATURE)
    
    return ChatGroq(
        model_name=GROQ_MODEL,
        groq_api_key=api_key,
        temperature=GROQ_TEMPERATURE,
        max_tokens=GROQ_MAX_TOKENS,
    )


# ─────────────────────────────────────────────────────────────────
# RAG-ланцюжок
# ─────────────────────────────────────────────────────────────────

def _build_chain():
    """
    Будує LangChain LCEL-ланцюжок:
      question -> retrieval -> prompt -> LLM -> str
    """
    llm = _get_llm()
    chain = (
        RunnablePassthrough()
        | RAG_PROMPT
        | llm
        | StrOutputParser()
    )
    return chain


# ─────────────────────────────────────────────────────────────────
# Публічний API
# ─────────────────────────────────────────────────────────────────

def ask_bot(query: str, k: int = 4) -> dict:
    """
    Головна функція FinRAG-асистента.

    Args:
        query: Питання користувача.
        k:     Кількість чанків для RAG-контексту.

    Returns:
        dict із ключами:
          - "answer"  (str):       Відповідь від LLM
          - "sources" (list):      [{"source": "file.pdf", "pages": [3, 4]}, ...]
          - "docs"    (list):      Оригінальні Document-об'єкти (для дебагу)
          - "error"   (str|None):  Опис помилки якщо вона сталася
    """
    log.info("Запит: %s", query[:80])

    # 1. Retrieval (verbose=False у production, True тільки для debug-скриптів)
    docs = retrieve(query, k=k, verbose=False)

    if not docs:
        return {
            "answer":  "На жаль, я не знайшов жодної релевантної інформації в тарифах банку.",
            "sources": [],
            "docs":    [],
            "error":   None,
        }

    # 2. Формуємо контекст
    context = format_context(docs)

    # 3. LLM — з обробкою помилок
    try:
        chain  = _build_chain()
        answer = chain.invoke({"question": query, "context": context})

    except EnvironmentError as exc:
        log.error("Помилка конфігурації: %s", exc)
        return {
            "answer":  "API ключ не налаштовано. Перевір наявність GROQ_API_KEY у файлі .env",
            "sources": [],
            "docs":    docs,
            "error":   f"EnvironmentError: {exc}",
        }

    except Exception as exc:
        err_str = str(exc)

        if "429" in err_str or "rate limit" in err_str.lower():
            log.warning("Rate limit exceeded: %s", err_str[:200])
            return {
                "answer": (
                    "Перевищено ліміт запитів до Groq API.\n\n"
                    "Будь ласка, зачекайте хвилину і спробуйте знову."
                ),
                "sources": [],
                "docs":    docs,
                "error":   "RATE_LIMIT_EXCEEDED",
            }
            
        elif "authentication" in err_str.lower() or "401" in err_str:
            log.warning("Invalid API Key: %s", err_str[:200])
            return {
                "answer": "Невірний ключ Groq API. Перевірте GROQ_API_KEY в .env",
                "sources": [],
                "docs":    docs,
                "error":   "INVALID_API_KEY"
            }

        log.error("Невідома помилка: %s", err_str[:300])
        return {
            "answer":  f"Помилка при зверненні до Groq API: {err_str[:150]}",
            "sources": [],
            "docs":    docs,
            "error":   err_str,
        }

    # 4. Витягуємо джерела
    sources = extract_sources(docs)

    log.info(
        "Відповідь сформовано. Джерел: %d, символів: %d",
        len(sources), len(answer),
    )

    return {
        "answer":  answer.strip(),
        "sources": sources,
        "docs":    docs,
        "error":   None,
    }
