# Stock Reversal Analyzer

A web application that monitors your stock watchlist and uses technical indicators + AI to identify potential trend reversal opportunities.

## Features

- **Watchlist management** — add any Yahoo Finance ticker (US, Japan, HK, etc.)
- **Technical analysis** — RSI, MACD, EMA, Bollinger Bands, Stochastic, volume ratio, candlestick patterns
- **AI interpretation** — Claude analyzes combined signals and explains the thesis in plain English
- **Score-based pre-filter** — stocks are scored 0–150 before calling the AI, keeping costs low
- **Price chart** — candlestick chart with EMA overlays on the stock detail page
- **Signal history** — track how a stock's signals have changed across analysis runs

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11+, FastAPI, SQLAlchemy, SQLite |
| Data | yfinance (Yahoo Finance) |
| Indicators | pandas-ta |
| AI | Anthropic Claude API (`claude-sonnet-4-6`) |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS |
| Charts | lightweight-charts v4 |
| State | Zustand |

---

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- (Optional) Claude API key from [console.anthropic.com](https://console.anthropic.com)

### 1. Clone the repo

```bash
git clone <your-repo-url>
cd stock-reversal-analyzer
```

### 2. Backend setup

```bash
cd backend

# Install dependencies
pip install -r requirements.txt

# Create your .env file
copy .env.example .env
```

Edit `.env` and fill in your Claude API key (optional — the app works without it):

```env
CLAUDE_API_KEY=sk-ant-xxxxxxxxxx
DATABASE_URL=sqlite:///./stock_analyzer.db
ANALYSIS_SCORE_THRESHOLD=40
PRICE_CACHE_TTL_MINUTES=15
```

### 3. Frontend setup

```bash
cd frontend
npm install
```

### 4. Run

**Option A — one-click (Windows):**

Double-click `start.bat` in the project root.

**Option B — manual (two terminals):**

```bash
# Terminal 1 — backend
cd backend
python -m uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend
npm run dev
```

Open **http://localhost:5173** in your browser.

The backend API docs are available at **http://localhost:8000/docs**.

---

## Usage

1. **Add tickers** — go to the Watchlist page and type a stock code (`AAPL`, `NVDA`, `7203.T`, etc.)
2. **Run analysis** — go to Dashboard and click **Run Analysis**
3. **Read results** — stocks are sorted by signal strength (HIGH → NONE)
4. **Drill down** — click any card to see the full chart, all indicator values, and AI reasoning

---

## How the Analysis Works

```
For each ticker in watchlist:
  1. Fetch 6 months of OHLCV data from Yahoo Finance (cached 15 min)
  2. Compute indicators: RSI, MACD, EMA20/50, Bollinger Bands,
                         Volume ratio, Stochastic, candlestick patterns
  3. Score the signals (0–150)
  4. If score >= 40 → send to Claude API for interpretation
     If score < 40  → return "none" without calling Claude
  5. Store results in SQLite
```

### Scoring breakdown

| Signal | Points |
|---|---|
| RSI < 30 (oversold) | +20 |
| RSI bullish divergence | +25 |
| MACD bullish crossover | +20 |
| MACD histogram turned positive | +10 |
| Bollinger Band bounce | +15 |
| Price below lower BB | +10 |
| Volume spike (≥ 2× average) | +15 |
| Stochastic crossover in oversold zone | +15 |
| Bullish candlestick pattern | +10 |
| Price > 10% below EMA50 | +10 |

Scores ≥ 70 → **HIGH**, ≥ 40 → **MEDIUM**, ≥ 20 → **LOW**, < 20 → **NONE**

---

## Project Structure

```
stock-reversal-analyzer/
├── backend/
│   ├── app/
│   │   ├── main.py               # FastAPI app entry point
│   │   ├── config.py             # Settings from .env
│   │   ├── database.py           # SQLAlchemy engine + session
│   │   ├── models/               # ORM models (watchlist, analysis, price cache)
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   ├── routers/              # API endpoints
│   │   ├── services/
│   │   │   ├── price_data.py     # yfinance fetch + DB cache
│   │   │   ├── indicators.py     # All technical indicator computation
│   │   │   ├── scoring.py        # Pre-AI numeric scoring
│   │   │   ├── ai_interpreter.py # Claude API call + prompt
│   │   │   └── analysis_runner.py# Pipeline orchestration
│   │   └── utils/
│   │       └── ticker_validator.py
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── src/
│       ├── api/                  # Axios API calls
│       ├── components/           # Reusable UI components
│       ├── pages/                # Dashboard, WatchlistManager, StockDetail, Settings
│       ├── store/                # Zustand global state
│       ├── types/                # TypeScript interfaces
│       └── utils/                # Currency formatting helpers
├── start.bat                     # One-click startup (Windows)
├── PLAN.md                       # Development progress tracker
└── README.md
```

---

## Configuration

All settings can be changed in `backend/.env` or via the **Settings** page in the UI.

| Variable | Default | Description |
|---|---|---|
| `CLAUDE_API_KEY` | _(empty)_ | Anthropic API key. Without this, analysis falls back to score-only mode. |
| `ANALYSIS_SCORE_THRESHOLD` | `40` | Minimum score to trigger Claude API call. Raise to reduce API costs. |
| `PRICE_CACHE_TTL_MINUTES` | `15` | How long to reuse cached price data before re-fetching. |
| `DATABASE_URL` | `sqlite:///./stock_analyzer.db` | SQLAlchemy connection string. |

---

## Roadmap

- [ ] **Phase 2** — Scheduled daily analysis with push notifications
- [ ] **Phase 3** — Sector comparison, news context, multi-timeframe signals
- [ ] **Phase 4** — Docker deployment, PostgreSQL migration
