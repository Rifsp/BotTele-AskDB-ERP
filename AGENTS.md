# AGENTS.md — Panduan AI Agent untuk Proyek DB-Chat

Dokumen ini berisi panduan untuk AI agent (seperti Claude, GPT, atau Cursor) agar memahami arsitektur dan konvensi proyek **DB-Chat**. Gunakan file ini sebagai referensi saat mengerjakan kode atau memberikan saran.

---

## Ringkasan Proyek

**DB-Chat** adalah aplikasi yang memungkinkan user bertanya tentang database PostgreSQL menggunakan bahasa natural melalui **Telegram bot** atau **API REST**. Jawaban diproses oleh AI (Konektika/OpenAI-compatible).

- **Bahasa**: Python 3.11+
- **Framework**: FastAPI (async)
- **Database**: PostgreSQL via asyncpg
- **AI**: Konektika / OpenAI API
- **Bot**: Telegram (python-telegram-bot)

---

## Arsitektur

### 1. Database Layer (`app/database/`)

| File | Fungsi |
|---|---|
| `connection.py` | Membuat & mengelola koneksi pool async ke PostgreSQL |
| `schema.py` | Mengintrospeksi skema database (tabel, kolom, tipe data, foreign keys, indexes) |

**Aturan:**
- Semua koneksi database WAJIB menggunakan asyncpg (bukan psycopg2)
- Gunakan connection pool, jangan bikin koneksi baru tiap request
- Pool dibuat sekali saat startup FastAPI, di-share via `app.state`
- Fungsi di `schema.py` harus mengembalikan dictionary/list of dicts, bukan ORM objects

### 2. Agent System (`app/agents/`)

Setiap agent adalah class yang mewarisi `BaseAgent`:

| File | Class | Tugas |
|---|---|---|
| `base_agent.py` | `BaseAgent` | Parent class: setup OpenAI client, system prompt, function calling |
| `sql_agent.py` | `SQLAgent` | Mengubah natural language → SQL query, explain hasil query |
| `schema_agent.py` | `SchemaAgent` | Menganalisis struktur database, relasi, indexing |
| `analysis_agent.py` | `AnalysisAgent` | Mencari anomali, agregasi data, pola |
| `report_agent.py` | `ReportAgent` | Membuat laporan terstruktur dari data |
| `chat_agent.py` | `ChatAgent` | Mempertahankan konteks percakapan multi-turn |
| `\__init\__.py` | — | Factory function untuk routing ke agent yang sesuai |

**Pola desain:**
```python
class BaseAgent:
    def __init__(self, openai_client, db_pool, system_prompt: str):
        self.client = openai_client
        self.db_pool = db_pool
        self.system_prompt = system_prompt

    async def run(self, message: str, context: dict = None) -> dict:
        # 1. Dapatkan response dari OpenAI dengan function calling
        # 2. Eksekusi function (misal: jalankan SQL)
        # 3. Kembalikan hasil ke user
        pass
```

**Aturan:**
- Setiap agent harus punya **system prompt** khusus dalam bahasa Indonesia atau bilingual (Indonesia-Inggris)
- Gunakan **OpenAI Function Calling** untuk eksekusi SQL, jangan generate SQL string lalu eval
- Semua method agent harus `async`
- Context (riwayat chat) dilewatkan sebagai parameter, bukan disimpan di class

### 3. API Layer (`app/api/`)

| File | Fungsi |
|---|---|
| `models.py` | Pydantic models untuk request & response |
| `routes.py` | Endpoints FastAPI |

**Endpoints utama:**
- `POST /api/chat` — Kirim pesan, dapat respons AI
- `POST /api/chat/history` — Ambil riwayat chat session
- `POST /api/schema` — Dapatkan skema database terbaru
- `GET /api/health` — Cek status aplikasi & koneksi DB

### 4. Telegram Bot (`app/bot.py`)

| Fungsi | Detail |
|---|---|
| `start_bot()` | Inisialisasi & jalankan bot polling |
| `stop_bot()` | Hentikan bot |
| `build_bot()` | Setup handler untuk /start, /clear, dan pesan teks |

- Bot menggunakan **polling** (tidak perlu webhook/public URL)
- Context percakapan disimpan per `chat_id` di dictionary in-memory
- Bot di-start/di-stop otomatis via FastAPI lifespan
- Token bot diatur via `TELEGRAM_BOT_TOKEN` di `.env`
- Jika token kosong, bot tidak aktif (log warning)

---

## Konfigurasi & Environment

File `.env`:

```
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
OPENAI_API_KEY=ktk-...
OPENAI_BASE_URL=https://konektikacloud.web.id/v1
OPENAI_MODEL=konektika-pro
APP_NAME=DB-Chat
DEBUG=true
MAX_ROWS=100
QUERY_TIMEOUT=30
TELEGRAM_BOT_TOKEN=your-bot-token
```

**Aturan:**
- Jangan hardcode credential di kode
- Gunakan `app/config.py` untuk load environment variables via `os.getenv` atau `pydantic-settings`
- Default value harus aman (production-safe)

---

## Function Calling (OpenAI Tools)

Setiap agent mendefinisikan `tools` (function schemas) yang bisa dipanggil oleh OpenAI. Contoh untuk SQL Agent:

```json
{
  "type": "function",
  "function": {
    "name": "execute_sql",
    "description": "Jalankan SQL query ke database",
    "parameters": {
      "type": "object",
      "properties": {
        "query": {
          "type": "string",
          "description": "SQL query yang akan dijalankan (hanya SELECT)"
        }
      },
      "required": ["query"]
    }
  }
}
```

**Aturan function calling:**
- Setiap function harus divalidasi sebelum dieksekusi (misal: hanya SELECT, cek keyword DANGER)
- Function `execute_sql` WAJIB menambahkan LIMIT secara default
- Jangan izinkan DDL (CREATE, DROP, ALTER, TRUNCATE) atau DML (INSERT, UPDATE, DELETE) di mode read-only

---

## Alur Percakapan

```
User: "Tampilkan 10 produk terlaris"
  ↓
Router → detect intent → SQLAgent
  ↓
SQLAgent.system_prompt = "Kamu asisten database..."
  ↓
OpenAI → function_call → execute_sql("SELECT ... LIMIT 10")
  ↓
execute_sql mengembalikan results (list of dicts)
  ↓
OpenAI → response teks: ringkasan hasil
  ↓
Kirim balik ke user: { response: "...", sql: "...", results: [...] }
```

Untuk chat multi-turn, context (riwayat pesan) dikirim ulang setiap request ke OpenAI.

---

## Panduan Coding

### Gaya Kode
- **Type hints** WAJIB untuk semua fungsi
- **Async/await** untuk semua I/O (DB, HTTP, API calls)
- **Docstrings** — gunakan Google style
- **Error handling** — gunakan custom exception classes, jangan raise `Exception`
- **Logging** — gunakan `logging` module, print statement hanya untuk debugging lokal

### Convention
- Imports: stdlib → third-party → local (dipisah baris kosong)
- Naming: `snake_case` untuk fungsi & variabel, `PascalCase` untuk class
- Constant: `UPPER_CASE`
- File encoding: UTF-8

### Testing
- Gunakan `pytest` dengan `pytest-asyncio`
- Mock OpenAI API (jangan panggil API beneran di test)
- Test dengan database test terpisah atau SQLite in-memory

---

## Keamanan

1. **SQL Injection** — dicegah dengan parameterized query (asyncpg built-in)
2. **Read-only** — filter query hanya SELECT; tolak INSERT/UPDATE/DELETE/DROP/ALTER/TRUNCATE/CREATE
3. **Query timeout** — semua query asyncpg harus pakai timeout
4. **Row limit** — maksimal 1000 rows per query (bisa dikonfigurasi via MAX_ROWS)
5. **API Key** — OpenAI key disimpan di env, tidak boleh ekspos ke client
6. **CORS** — batasi origin yang bisa akses API

---

## Cara Menambahkan Agent Baru

1. Buat file `app/agents/new_agent.py`
2. Buat class `NewAgent(BaseAgent)` di file tersebut
3. Definisikan `system_prompt` yang sesuai
4. Definisikan `tools` (function calling schemas)
5. Implement method `run()` — panggil OpenAI, proses function call, return hasil
6. Daftarkan di `app/agents/__init__.py` factory
7. Tambahkan route baru di `app/api/routes.py` jika perlu
