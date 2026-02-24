"""
app.py — FinRAG Streamlit UI
─────────────────────────────────────────────────────────────────
Преміальний темний дизайн, адаптований під вказані скріншоти.
─────────────────────────────────────────────────────────────────
"""

import sys
import streamlit as st

st.set_page_config(
    page_title="FinRAG — Асистент з банківських тарифів",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

sys.path.insert(0, ".")
from src.generator import ask_bot, GROQ_MODEL

# ════
# CSS
# ════

st.markdown("""
<style>
/* ── Шрифти ─────────────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,400;0,600;0,700;1,400&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Змінні ─────────────────────────────────────────────────── */
:root {
    --bg-main:       #0F111A;
    --bg-sidebar:    #161824;
    --bg-card:       #1E2336;
    --bg-source:     #131620;
    --bg-input:      #1A1D2D;
    
    --accent-gold:   #E5B25C;
    --accent-gold-h: #F6C879;
    --accent-green:  #10B981;
    --border-dim:    rgba(255, 255, 255, 0.08);
    
    --text-main:     #E2E8F0;
    --text-muted:    #94A3B8;
    --text-dark:     #0F111A;
    
    --font-serif:    'Playfair Display', serif;
    --font-sans:     'Inter', sans-serif;
    --font-mono:     'JetBrains Mono', monospace;
}

/* ── Глобальні налаштування ─────────────────────────────────── */
html, body, [data-testid="stAppViewContainer"] {
    background-color: var(--bg-main) !important;
    font-family: var(--font-sans) !important;
    color: var(--text-main) !important;
}

[data-testid="stHeader"] {
    display: none !important; /* Ховаємо дефолтний хедер Streamlit */
}

/* Ховаємо можливість згортати сайдбар (бургер-меню та хрестик/стрілку) */
[data-testid="collapsedControl"],
[data-testid="stSidebarCollapseButton"] {
    display: none !important;
}

/* ── САЙДБАР ────────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: var(--bg-sidebar) !important;
    border-right: 1px solid var(--border-dim) !important;
}

/* Ховаємо прихований хедер сайдбару Streamlit, який займає місце зверху */
[data-testid="stSidebarHeader"] {
    display: none !important;
}

/* Прибираємо гігантський пробіл від верхнього краю самого контенту */
[data-testid="stSidebarUserContent"] {
    padding-top: 1.5rem !important;
}

[data-testid="stSidebar"] * {
    color: var(--text-main);
}

/* Логотип */
.sidebar-logo {
    display: flex;
    flex-direction: column;
    margin-bottom: 2rem;
}
.sidebar-title-row {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin-bottom: 0.3rem;
}
.sidebar-icon {
    font-size: 1.8rem;
    color: var(--accent-gold);
}
.sidebar-title {
    font-family: var(--font-serif);
    font-size: 1.8rem;
    font-weight: 700;
    color: var(--accent-gold);
    margin: 0;
    letter-spacing: 0.5px;
}
.sidebar-subtitle {
    font-size: 0.65rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin: 0;
}

/* Секції сайдбару */
.sidebar-section-title {
    font-size: 0.7rem;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin: 1.5rem 0 1rem 0;
}

/* Баджі статусу */
.status-item {
    margin-bottom: 1rem;
}
.status-label {
    font-size: 0.75rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.4rem;
}
.status-badge {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 6px 14px;
    font-family: var(--font-mono);
    font-size: 0.75rem;
    color: var(--text-muted);
}
.status-dot {
    width: 6px;
    height: 6px;
    background-color: var(--accent-green);
    border-radius: 50%;
    box-shadow: 0 0 8px var(--accent-green);
}

/* Лічильник запитів */
.queries-count {
    font-family: var(--font-serif);
    font-size: 2.5rem;
    font-weight: 700;
    color: var(--accent-gold);
    line-height: 1;
    margin-top: 0.5rem;
}

/* Слайдер (K) */
.stSlider {
    padding-top: 1rem;
}
.stSlider > div[data-baseweb="slider"] > div > div {
    background: var(--bg-card) !important;
}
.stSlider > div[data-baseweb="slider"] > div > div > div {
    background: var(--accent-gold) !important;
}
.stSlider label {
    font-size: 0.85rem !important;
    color: var(--text-main) !important;
}

/* Кнопка "Очистити чат" */
button[kind="secondary"] {
    background-color: transparent !important;
    border: 1px solid var(--border-dim) !important;
    color: var(--text-muted) !important;
    border-radius: 8px !important;
    transition: all 0.2s;
}
button[kind="secondary"]:hover {
    border-color: var(--accent-gold) !important;
    color: var(--accent-gold) !important;
}

/* Expander "Як це працює?" */
.streamlit-expanderHeader {
    background: var(--bg-card) !important;
    border-radius: 8px !important;
    border: 1px solid var(--border-dim) !important;
}

/* ── ГОЛОВНА ЗОНА ───────────────────────────────────────────── */

/* Хедер (Запитай про тарифи...) */
.main-title-container {
    text-align: center;
    padding: 2rem 0;
    margin-bottom: 2rem;
    border-bottom: 1px solid var(--border-dim);
}
.main-title {
    font-family: var(--font-serif);
    font-size: 1.8rem;
    font-weight: 600;
    color: var(--text-main);
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 10px;
    margin: 0 0 0.5rem 0;
}
.main-subtitle {
    font-size: 0.85rem;
    color: var(--text-muted);
    font-style: italic;
    margin: 0;
}

/* Welcome скрін */
.welcome-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    margin-top: 4rem;
    margin-bottom: 3rem;
}
.welcome-icon-box {
    width: 64px;
    height: 64px;
    border: 1px solid var(--accent-gold);
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 2rem;
    color: var(--accent-gold);
    margin-bottom: 1.5rem;
}
.welcome-heading {
    font-family: var(--font-serif);
    font-size: 2.2rem;
    font-weight: 600;
    margin: 0 0 1rem 0;
}
.welcome-text {
    font-size: 0.95rem;
    color: var(--text-muted);
    text-align: center;
    max-width: 600px;
    line-height: 1.6;
}

/* Чіпи з підказками (кнопки) */
.stButton>button {
    background-color: var(--bg-input) !important;
    border: 1px solid var(--border-dim) !important;
    color: var(--text-muted) !important;
    border-radius: 8px !important;
    padding: 0.5rem 1rem !important;
    font-size: 0.85rem !important;
    white-space: nowrap;
    transition: all 0.2s !important;
}
.stButton>button:hover {
    border-color: var(--accent-gold) !important;
    color: var(--accent-gold) !important;
}

/* ── ЧАТ (ПОВІДОМЛЕННЯ) ─────────────────────────────────────── */

/* Забираємо дефолтні аватарки Streamlit, бо зробимо свої/приховаємо */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    padding: 0.5rem 0 !important;
}
[data-testid="stChatMessageAvatarUser"] { display: none !important; }
[data-testid="stChatMessageAvatarAssistant"] { display: none !important; }

/* Кастомний User Bubble (жовтий фон, справа) */
.msg-user-container {
    display: flex;
    justify-content: flex-end;
    margin: 1rem 0;
}
.msg-user-bubble {
    background-color: var(--accent-gold);
    color: var(--text-dark);
    padding: 1rem 1.5rem;
    border-radius: 12px 12px 0 12px;
    font-weight: 500;
    max-width: 80%;
    font-size: 0.95rem;
    line-height: 1.5;
    box-shadow: 0 4px 15px rgba(229, 178, 92, 0.1);
}

/* Кастомний Assistant Bubble (темний фон, зліва) */
.msg-bot-container {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    margin: 1.5rem 0;
}
.msg-bot-icon {
    flex-shrink: 0;
    width: 40px;
    height: 40px;
    border: 1px solid var(--accent-gold);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.1rem;
    color: var(--accent-gold);
    background: transparent;
}
.msg-bot-content-wrap {
    flex-grow: 1;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    max-width: 85%;
}
.msg-bot-bubble {
    background-color: var(--bg-card);
    border-radius: 0 12px 12px 12px;
    padding: 1.25rem 1.5rem;
    color: var(--text-main);
    font-size: 0.95rem;
    line-height: 1.6;
}

/* Карточка джерела */
.source-card {
    background-color: var(--bg-source);
    border-left: 3px solid var(--accent-green);
    border-radius: 0 8px 8px 0;
    padding: 1rem 1.25rem;
    margin-top: 0.3rem;
}
.source-title {
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--text-main);
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 0.5rem;
}
.source-icon {
    font-size: 1rem;
    color: var(--accent-green);
}
.source-pages {
    color: var(--text-muted);
    font-weight: 400;
}
.source-excerpt {
    font-size: 0.85rem;
    color: var(--accent-green);
    font-style: italic;
    opacity: 0.8;
}

/* ── ПОЛЕ ВВОДУ ─────────────────────────────────────────────── */
/* Native Streamlit Chat Input styling trick */
.stChatFloatingInputContainer {
    padding-bottom: 25px !important; /* Робимо місце тільки для тексту лічильника */
    background: transparent !important;
}

[data-testid="stChatInput"] {
    background-color: transparent !important;
    padding-bottom: 0 !important;
}
[data-testid="stChatInput"] > div {
    background-color: var(--bg-input) !important;
    border: 1px solid var(--border-dim) !important;
    border-radius: 12px !important;
    padding: 0 0.4rem 0 0.8rem !important;
    align-items: center !important; /* Центруємо текст і кнопку по вертикалі */
}
[data-testid="stChatInput"] > div:focus-within {
    border-color: var(--accent-gold) !important;
    box-shadow: 0 0 0 1px var(--accent-gold) !important;
}

/* Скидаємо стилі самого внутрішнього компонента BaseWeb */
[data-testid="stChatInput"] [data-baseweb="textarea"] {
    background-color: transparent !important;
}
[data-testid="stChatInput"] div[data-baseweb="base-input"] {
    background-color: transparent !important;
}
[data-testid="stChatInput"] textarea {
    background-color: transparent !important;
    color: var(--text-main) !important;
    font-size: 0.95rem !important;
    padding-top: 14px !important;
    padding-bottom: 14px !important;
}
[data-testid="stChatInput"] textarea::placeholder {
    color: var(--text-muted) !important;
}

/* Кнопка Send (Arrow Up) */
[data-testid="stChatInputSubmitButton"] {
    background-color: var(--accent-gold) !important;
    border-radius: 50% !important;
    color: var(--text-dark) !important;
    width: 36px !important;
    height: 36px !important;
    min-width: 36px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    align-self: center !important; /* Вирівнюємо суворо по центру */
    margin: 0 0.2rem 0 0.5rem !important; /* Прибираємо криві відступи Streamlit */
    transition: transform 0.2s;
}
[data-testid="stChatInputSubmitButton"]:hover {
    background-color: var(--accent-gold-h) !important;
    transform: scale(1.05);
}
[data-testid="stChatInputSubmitButton"] svg {
    fill: var(--text-dark) !important;
}

</style>
""", unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════
# Збереження стану 
# ═════════════════════════════════════════════════════════════════

if "messages" not in st.session_state:
    st.session_state.messages = []
if "total_queries" not in st.session_state:
    st.session_state.total_queries = 0
if "pending_suggestion" not in st.session_state:
    st.session_state.pending_suggestion = None


# ═════════════════════════════════════════════════════════════════
# Helpers (генерація HTML для чату)
# ═════════════════════════════════════════════════════════════════

def render_user_msg(text: str):
    # Захист від того, щоб парсер Streamlit не помилково закривав HTML-блоки
    safe_text = str(text).replace('\n', '<br>')
    html = f'<div class="msg-user-container"><div class="msg-user-bubble">{safe_text}</div></div>'
    st.markdown(html, unsafe_allow_html=True)

def render_bot_msg(text: str, sources: list = None, error: str = None):
    import re
    # Конвертуємо markdown-переноси та жирний шрифт у HTML теги
    safe_text = str(text).replace('\n', '<br>')
    safe_text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', safe_text)
    safe_text = re.sub(r'\*(.*?)\*', r'<i>\1</i>', safe_text)

    # Спочатку сам текст у темній бульбашці
    content_html = f'<div class="msg-bot-bubble">{safe_text}</div>'
    
    # Якщо є джерела — генеруємо картку джерела під текстом
    if sources and not error:
        # Для дизайну беремо перше джерело, щоб не перевантажувати
        first_source = sources[0]
        fname = first_source["source"]
        pages = ", ".join(str(p) for p in first_source["pages"])
        
        # Відобразимо стилізовану зелену картку
        content_html += (
            f'<div class="source-card">'
            f'<div class="source-title"><span class="source-icon">📄</span> {fname} <span class="source-pages">· с. {pages}</span></div>'
            f'<div class="source-excerpt">«Інформація знайдена у відповідному розділі документу»</div>'
            f'</div>'
        )
        
    html = (
        f'<div class="msg-bot-container">'
        f'<div class="msg-bot-icon">🏛️</div>'
        f'<div class="msg-bot-content-wrap">{content_html}</div>'
        f'</div>'
    )
    st.markdown(html, unsafe_allow_html=True)


# ═════════════════════════════════════════════════════════════════
# САЙДБАР
# ═════════════════════════════════════════════════════════════════

with st.sidebar:
    st.markdown("""
    <div class="sidebar-logo">
        <div class="sidebar-title-row">
            <span class="sidebar-icon">🏛️</span>
            <h1 class="sidebar-title">FinRAG</h1>
        </div>
        <p class="sidebar-subtitle">АСИСТЕНТ З БАНКІВСЬКИХ ТАРИФІВ</p>
    </div>
    
    <div class="sidebar-section-title">СТАТУС СИСТЕМИ</div>
    
    <div class="status-item">
        <div class="status-label">LLM МОДЕЛЬ</div>
        <div class="status-badge"><span class="status-dot"></span>{0}</div>
    </div>
    
    <div class="status-item">
        <div class="status-label">EMBEDDINGS</div>
        <div class="status-badge"><span class="status-dot"></span>multilingual-MiniLM-L12</div>
    </div>
    
    <div class="status-item">
        <div class="status-label">ВЕКТОРНА БД</div>
        <div class="status-badge"><span class="status-dot"></span>ChromaDB · локальна</div>
    </div>
    
    <div class="sidebar-section-title">ЗАПИТІВ У СЕСІЇ</div>
    <div class="queries-count">{1}</div>
    
    <hr style="border:0; border-top:1px solid rgba(255,255,255,0.08); margin: 2rem 0;">
    
    <div class="sidebar-section-title">НАЛАШТУВАННЯ</div>
    """.format(GROQ_MODEL, st.session_state.total_queries), unsafe_allow_html=True)

    k_value = st.slider(
        "Кількість фрагментів (k)",
        min_value=4, max_value=12, value=8,
        label_visibility="visible"
    )

    st.markdown("<br><br>", unsafe_allow_html=True)
    
    if st.button("🗑️ Очистити чат", use_container_width=True):
        st.session_state.messages = []
        st.session_state.total_queries = 0
        st.rerun()

    with st.expander("Як це працює?"):
        st.caption("1. Система отримує запит\n2. Шукає тарифи локально в ChromaDB (embedding + keywords)\n3. Надсилає контекст у Groq\n4. Повертає згенеровану відповідь з посиланням на сторінку.")


# ═════════════════════════════════════════════════════════════════
# ГОЛОВНА ЗОНА
# ═════════════════════════════════════════════════════════════════

# Хедер (Завжди видимий)
st.markdown("""
<div class="main-title-container">
    <h2 class="main-title">💬 Запитай про тарифи банку</h2>
    <p class="main-subtitle">Відповідаю тільки на основі завантажених документів · без галюцинацій · із джерелами</p>
</div>
""", unsafe_allow_html=True)

# ─── Welcome screen (якщо чат порожній) ──────────────
if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-container">
        <div class="welcome-icon-box">🏛️</div>
        <h3 class="welcome-heading">Привіт! Я FinRAG-асистент</h3>
        <p class="welcome-text">Я допоможу швидко знайти інформацію щодо банківських тарифів, комісій та умов обслуговування з офіційних документів банку.</p>
    </div>
    """, unsafe_allow_html=True)

    # Список кнопок в один ряд або wrap
    sug_cols = st.columns(6)
    suggestions = [
        "Яка комісія за зняття готівки?",
        "Умови кредитної картки",
        "Відсоткова ставка по кредиту",
        "Обслуговування картки",
        "Умови депозиту",
        "Ліміти переказів"
    ]
    
    for i, sug in enumerate(suggestions):
        with sug_cols[i % 6]:
            if st.button(sug, use_container_width=True):
                st.session_state.pending_suggestion = sug
                st.rerun()

# ─── ІСТОРІЯ ЧАТУ ────────────────────────────────────
for msg in st.session_state.messages:
    if msg["role"] == "user":
        # Щоб обійти обгортку st.chat_message і малювати власний HTML
        render_user_msg(msg["content"])
    else:
        render_bot_msg(msg["content"], msg.get("sources"), msg.get("error"))


# ─── ОБРОБКА ВВЕДЕННЯ (КНОПКА) ───────────────────────
if st.session_state.pending_suggestion:
    query = st.session_state.pending_suggestion
    st.session_state.pending_suggestion = None

    # Відразу відображаємо запит (через Session State)
    st.session_state.messages.append({"role": "user", "content": query})
    render_user_msg(query)

    with st.spinner("FinRAG-асистент друкує..."):
        result = ask_bot(query, k=k_value)

    st.session_state.messages.append({
        "role":    "assistant",
        "content": result["answer"],
        "sources": result["sources"],
        "error":   result.get("error"),
    })
    st.session_state.total_queries += 1
    st.rerun()


# ─── ОБРОБКА ВВЕДЕННЯ (ПОЛЕ) ─────────────────────────
if query := st.chat_input("Запитай про тарифи, комісії, умови..."):
    st.session_state.messages.append({"role": "user", "content": query})
    render_user_msg(query)

    with st.spinner("FinRAG-асистент друкує..."):
        result = ask_bot(query, k=k_value)

    st.session_state.messages.append({
        "role":    "assistant",
        "content": result["answer"],
        "sources": result["sources"],
        "error":   result.get("error"),
    })
    st.session_state.total_queries += 1
    st.rerun()

# Додатковий лічильник символів κάτω (візуальний хак)
st.markdown("""<div style="font-family: var(--font-mono); font-size: 0.7rem; color: var(--text-muted); position: fixed; bottom: 5px; left: 50%; transform: translateX(-50%); width: 100%; max-width: 48rem; padding: 0 1rem;">
0 / 2000 символів
</div>""", unsafe_allow_html=True)
