"""
Real Knowledge Pipeline project data — hardcoded snapshot.

Source files (read 2026-07-07):
  knowledge-pipeline/README.md, exceptions.py, tests/*, git log, logs/*.txt,
  RECOMMENDATIONS.md, PROJECT_STATUS.md
"""

from dataclasses import dataclass, field


# ── Git history ──────────────────────────────────────────────────────────────

@dataclass
class Commit:
    sha: str
    date: str
    message: str
    category: str   # "feat" | "refactor" | "fix" | "chore" | "security"


GIT_COMMITS: list[Commit] = [
    Commit("b6f1f1a", "2026-06-23", "Initial commit: knowledge pipeline with AI enrichment and Streamlit dashboard", "feat"),
    Commit("e5d809b", "2026-06-23", "Add Claude API token usage logging to batch summary", "feat"),
    Commit("093f873", "2026-06-23", "Add parallel article processing via ThreadPoolExecutor (--parallel N flag)", "feat"),
    Commit("ebfa811", "2026-06-24", "Add multi-page Streamlit dashboard with dark theme", "feat"),
    Commit("2e2b3b3", "2026-06-24", "Prepare repo for GitHub: README_RU, cleanup, gitignore", "chore"),
    Commit("090a054", "2026-06-24", "Remove dashboard from repo (show at interview when ready)", "security"),
    Commit("e626179", "2026-06-24", "Remove personal paths from tracked files", "security"),
    Commit("943bb8d", "2026-06-25", "refactor: move utility scripts to scripts/, clean up code and docs", "refactor"),
    Commit("0cd66a2", "2026-06-25", "fix: replace source_type == 'youtube' with 'video' in 6 places", "fix"),
]


# ── Architecture Decision Records ────────────────────────────────────────────

@dataclass
class ADR:
    id: str
    title: str
    status: str   # "accepted" | "superseded" | "proposed"
    context: str
    decision: str
    consequence: str


ADR_LIST: list[ADR] = [
    ADR(
        id="ADR-001",
        title="Prompt engineering via folder_examples.yml",
        status="accepted",
        context="Claude нужно классифицировать каждую заметку в ~50 папок. "
                "Жёстко прописанные примеры в промпте не масштабируются.",
        decision="Few-shot примеры (YES/NOT) вынесены в folder_examples.yml и "
                 "загружаются динамически при каждом вызове API. "
                 "Итерируются без правки промпта.",
        consequence="Точность классификации улучшилась на реальных ошибках; "
                    "файл можно обновлять без деплоя.",
    ),
    ADR(
        id="ADR-002",
        title="Fallback chain для YouTube: api → yt-dlp → description-only",
        status="accepted",
        context="YouTube агрессивно блокирует VPN IP (особенно из России). "
                "Единственный метод извлечения → потеря ~30% контента.",
        decision="Три уровня деградации: youtube-transcript-api (быстро) → "
                 "yt-dlp (subtitle download, медленнее) → description-only "
                 "с флагом needs_review:true. IPBlockedError поднимается явно.",
        consequence="96 IP-блоков обработаны gracefully; "
                    "пайплайн не крашится, лог структурирован по типу ошибки.",
    ),
    ADR(
        id="ADR-003",
        title="Idempotent batch via source_url lookup во frontmatter",
        status="accepted",
        context="Батч из 700+ URL работает часами. Любое прерывание "
                "(сон ноутбука, сеть) означает потерю прогресса.",
        decision="Перед обработкой URL проверяется наличие заметки с этим "
                 "source_url в frontmatter. Уже обработанные пропускаются. "
                 "--batch safe to restart anytime.",
        consequence="704 URL обработано без ручного вмешательства; "
                    "97 уже существующих корректно пропущены.",
    ),
    ADR(
        id="ADR-004",
        title="ThreadPoolExecutor для статей, видео — последовательно",
        status="accepted",
        context="Статьи не имеют rate-limit по IP. Видео YouTube блокирует "
                "при параллельных запросах с одного IP.",
        decision="--parallel N запускает статьи через ThreadPoolExecutor "
                 "(рек. 3–5 потоков). Видео всегда последовательно. "
                 "Счётчики результатов thread-safe через Lock.",
        consequence="Скорость обработки статей выросла линейно с N; "
                    "YouTube-блоки не увеличились.",
    ),
    ADR(
        id="ADR-005",
        title="DuckDB как локальный векторный стор",
        status="accepted",
        context="Нужно хранить эмбеддинги для семантического поиска. "
                "Внешний сервер (Pinecone, Qdrant) избыточен для личного проекта.",
        decision="DuckDB с расширением vss — zero-config, локально, "
                 "файл knowledge.db в .gitignore. "
                 "Эмбеддинги: paraphrase-multilingual-MiniLM-L12-v2.",
        consequence="Семантический поиск возможен без сервера; "
                    "база в .gitignore — личные данные не утекают.",
    ),
]


# ── Typed exceptions ─────────────────────────────────────────────────────────

@dataclass
class ExceptionDef:
    name: str
    description: str
    raised_by: str


EXCEPTIONS: list[ExceptionDef] = [
    ExceptionDef("VideoTooLongError",          "Видео превышает лимит длительности (>40 мин)",   "extractors/video.py"),
    ExceptionDef("IPBlockedError",             "YouTube блокирует запросы с этого IP",            "extractors/video.py"),
    ExceptionDef("SubtitlesUnavailableError",  "Субтитры/транскрипт не найдены ни одним методом","extractors/video.py"),
    ExceptionDef("NoTextError",                "Не удалось извлечь текст из источника",           "extractors/article.py"),
    ExceptionDef("URLNotFoundError",           "URL вернул 404 или недоступен",                   "router.py"),
    ExceptionDef("UnsupportedSourceError",     "Платформа не поддерживается (TikTok, Instagram)", "router.py"),
]


# ── Test suite ───────────────────────────────────────────────────────────────

@dataclass
class TestCase:
    name: str
    module: str
    what: str


TESTS: list[TestCase] = [
    TestCase("test_strip_plain_json",                      "test_enrich.py",      "Парсинг plain JSON без обёрток"),
    TestCase("test_strip_json_fences",                     "test_enrich.py",      "Удаление ```json ... ``` обёрток"),
    TestCase("test_strip_bare_fences",                     "test_enrich.py",      "Удаление ``` ... ``` без типа"),
    TestCase("test_enrich_falls_back_to_inbox_on_unknown_folder", "test_enrich.py","Fallback в inbox при неизвестной папке"),
    TestCase("test_enrich_uses_hint_title_when_no_title",  "test_enrich.py",      "hint_title используется если модель вернула null"),
    TestCase("test_enrich_retries_on_connection_error",    "test_enrich.py",      "APIConnectionError → ретрай, не краш"),
    TestCase("test_enrich_raises_after_all_retries_fail",  "test_enrich.py",      "RuntimeError после MAX_RETRIES неудач"),
    TestCase("test_enrich_valid_folder_is_kept",           "test_enrich.py",      "Правильная папка сохраняется без изменений"),
    TestCase("test_nodate_placeholder_has_no_question_marks", "test_note_writer.py","Нет ? в именах файлов (Windows-регрессия)"),
    TestCase("test_nodate_used_when_no_date",              "test_note_writer.py", "[nodate] при отсутствии даты публикации"),
    TestCase("test_date_used_when_valid",                  "test_note_writer.py", "Дата попадает в имя файла"),
    TestCase("test_filename_sanitizes_forbidden_chars",    "test_note_writer.py", r"Удаление \/:*?<>| из имён файлов"),
    TestCase("test_filename_not_empty_when_no_title",      "test_note_writer.py", "Fallback 'untitled' при пустом title"),
]


# ── Quality backlog (from RECOMMENDATIONS.md) ────────────────────────────────

@dataclass
class QualityItem:
    id: str
    title: str
    priority: str   # "high" | "medium" | "low"
    status: str     # "done" | "open" | "planned"
    detail: str


QUALITY_ITEMS: list[QualityItem] = [
    QualityItem("SEC-1",  "Вынести ANTHROPIC_API_KEY в env",            "high",   "done",    "os.environ через .env; .env.example добавлен"),
    QualityItem("SEC-2",  "Добавить .gitignore (cookies, logs, db)",    "high",   "done",    "cookies.txt, *.db, logs/, urls.txt исключены"),
    QualityItem("SEC-3",  "Убрать личные пути из tracked файлов",       "high",   "done",    "Локальные пути вынесены в env-переменные, не хранятся в коде"),
    QualityItem("SEC-4",  "Проверить историю гита на секреты",          "high",   "done",    "API-ключ не попадал в коммиты"),
    QualityItem("PROD-1", "Ретраи на сетевые ошибки Anthropic",         "high",   "done",    "exponential backoff: APIConnectionError, RateLimitError, 529"),
    QualityItem("PROD-2", "Typed exceptions вместо разбора текста",     "high",   "done",    "6 классов в exceptions.py; ловятся по типу"),
    QualityItem("PROD-3", "Вынести magic numbers в конфиг",             "medium", "done",    "TRUNCATE_CHARS, MAX_RETRIES, chunk_size в config.py"),
    QualityItem("PROD-4", "Логировать обрезку длинного текста",         "medium", "open",    "text[:12000] молча — нужно логировать потерю"),
    QualityItem("PROD-5", "Chunking транскриптов >40 мин",              "medium", "planned", "map-reduce по чанкам; 205 пропущенных URL"),
    QualityItem("PROD-6", "Честный учёт времени в batch summary",       "medium", "open",    "wall-clock включает ночной простой; нужны активное время + паузы"),
    QualityItem("PROD-7", "Async вместо time.sleep",                    "low",    "planned", "Для event-driven ботов (будущая задача)"),
]


# ── Monitoring: batch sessions ───────────────────────────────────────────────

@dataclass
class BatchSession:
    session_id: str
    date: str
    time: str
    total_urls: int
    created: int
    skipped_exists: int
    too_long: int
    ip_blocks: int
    no_text: int
    errors_total: int
    log_file: str


BATCH_SESSIONS: list[BatchSession] = [
    BatchSession("S1",  "2026-06-18", "02:03", 3,   1,  0, 0, 1, 0, 1, "2026-06-18_02-03_log.txt"),
    BatchSession("S2",  "2026-06-18", "02:07", 5,   1,  0, 0, 2, 0, 3, "2026-06-18_02-07_log.txt"),
    BatchSession("S3",  "2026-06-18", "02:13", 4,   1,  0, 0, 2, 0, 2, "2026-06-18_02-13_log.txt"),
    BatchSession("S4",  "2026-06-18", "02:15", 2,   0,  1, 0, 0, 0, 0, "2026-06-18_02-15_log.txt"),
    BatchSession("S5",  "2026-06-18", "02:17", 1,   0,  0, 0, 0, 0, 1, "2026-06-18_02-17_log.txt"),
    BatchSession("S6",  "2026-06-18", "13:12", 160, 43, 37,35, 7,18,43, "2026-06-18_13-12_log.txt"),
    BatchSession("S7",  "2026-06-18", "22:07", 704, 258,97,205,96,48,349,"2026-06-18_22-07_log.txt"),
]

# Aggregate across all sessions
TOTAL_URLS_PROCESSED   = sum(s.total_urls    for s in BATCH_SESSIONS)
TOTAL_NOTES_CREATED    = sum(s.created       for s in BATCH_SESSIONS)
TOTAL_IP_BLOCKS        = sum(s.ip_blocks     for s in BATCH_SESSIONS)
TOTAL_TOO_LONG         = sum(s.too_long      for s in BATCH_SESSIONS)
TOTAL_NO_TEXT          = sum(s.no_text       for s in BATCH_SESSIONS)
TOTAL_ERRORS           = sum(s.errors_total  for s in BATCH_SESSIONS)


# ── Project overview ─────────────────────────────────────────────────────────

PROJECT_DESCRIPTION = (
    "Python-пайплайн для автоматического создания структурированных заметок "
    "из YouTube-видео и веб-статей в Obsidian. "
    "AI-обогащение через Claude Haiku: summary, concepts, tags, folder."
)

STACK = [
    ("Python 3.13",                "Core пайплайн"),
    ("Anthropic Claude Haiku",     "AI-обогащение (JSON extraction, folder classification)"),
    ("youtube-transcript-api + yt-dlp", "Fallback chain субтитров"),
    ("trafilatura",                "Извлечение текста из статей"),
    ("sentence-transformers",      "Multilingual embeddings (MiniLM-L12-v2)"),
    ("DuckDB",                     "Локальный векторный стор"),
    ("PyYAML",                     "Obsidian-совместимый frontmatter"),
]
