# DB-Chat

AI-powered database analysis assistant using natural language via Telegram bot or REST API. Built with Python, FastAPI, PostgreSQL, and Konektika AI (OpenAI-compatible).

## Fitur

- **Natural Language Query** — Tanya database pakai bahasa Indonesia/Inggris, dapat SQL & hasilnya
- **Analisis Skema DB** — AI menganalisis struktur tabel, relasi, indexing, dan constraints
- **Deteksi Anomali Data** — Menemukan outlier dan pola mencurigakan dalam data
- **Generate Laporan** — Membuat ringkasan dan laporan dari data database
- **Chat dengan Database** — Multi-turn conversation tentang database Anda

## Tech Stack

| Komponen | Teknologi |
|---|---|
| Backend | Python 3.11+ / FastAPI / Uvicorn |
| Database | PostgreSQL (asyncpg) |
| AI | OpenAI GPT-4 / GPT-3.5 |
| Frontend | Jinja2 + Tailwind CSS + Vanilla JS |

## Struktur Proyek

```
DB-Chat/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI entry point
│   ├── config.py               # Environment variables & settings
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py       # Koneksi & pool PostgreSQL (asyncpg)
│   │   └── schema.py           # Introspection skema DB
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── base_agent.py       # Base class agent
│   │   ├── sql_agent.py        # Natural language → SQL
│   │   ├── schema_agent.py     # Analisis skema & relasi
│   │   ├── analysis_agent.py   # Analisis data & deteksi anomali
│   │   ├── report_agent.py     # Generate laporan
│   │   └── chat_agent.py       # Multi-turn conversation
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py           # API endpoints
│   │   └── models.py           # Pydantic models
│   ├── static/
│   │   ├── css/
│   │   │   └── style.css
│   │   └── js/
│   │       └── app.js
│   └── templates/
│       └── index.html
├── .env.example
├── AGENTS.md                   # Panduan AI agent
├── requirements.txt
└── README.md
```

## Instalasi

1. **Clone & masuk direktori**
   ```bash
   git clone <repo-url>
   cd DB-Chat
   ```

2. **Buat virtual environment**
   ```bash
   python -m venv venv
   .\venv\Scripts\Activate   # Windows
   source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Konfigurasi environment**
   ```bash
   cp .env.example .env
   # Isi .env dengan konfigurasi database & OpenAI key
   ```

5. **Jalankan aplikasi**
   ```bash
   uvicorn app.main:app --reload
   ```

6. **Buka browser**
   ```
   http://localhost:8000
   ```

## Konfigurasi

Buat file `.env` berdasarkan `.env.example`:

| Variable | Deskripsi |
|---|---|
| `DATABASE_URL` | Connection string PostgreSQL |
| `OPENAI_API_KEY` | API key OpenAI |
| `OPENAI_MODEL` | Model OpenAI (default: gpt-4) |
| `APP_NAME` | Nama aplikasi |
| `DEBUG` | Mode debug (true/false) |
| `MAX_ROWS` | Batas baris hasil query (default: 100) |
| `QUERY_TIMEOUT` | Timeout query dalam detik (default: 30) |

## Penggunaan

1. Buka `http://localhost:8000`
2. Masukkan pertanyaan dalam bahasa natural
3. AI akan menggenerate SQL, menjalankannya, dan memberikan analisis

Contoh pertanyaan:
- "Tampilkan 10 pelanggan dengan total pembelian tertinggi"
- "Apa saja tabel yang ada di database?"
- "Analisis struktur tabel orders"
- "Buat laporan penjualan bulan ini"
- "Apakah ada anomali dalam data transaksi?"

## Keamanan

- **Read-only mode** — secara default hanya SELECT queries yang diizinkan
- **Query timeout** — mencegah query berat berjalan terlalu lama
- **Row limit** — membatasi jumlah baris yang dikembalikan
- **Logging** — semua query dicatat untuk audit
