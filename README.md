# Stock Intelligence App

A local-first, AI-powered Stock Recommendation App offering technical analysis, news sentiment tracking, and smart fund allocation strategies. Built for privacy and performance.

## 🚀 Features

*   **Hybrid Analysis Engine**: Uses **Llama 3.2 (Ollama)** locally for free, private analysis, with architecture to switch to Cloud APIs (OpenAI/Claude).
*   **Smart Allocation**: "Inject Funds" feature that intelligently splits capital between existing winners and new opportunities based on sector caps and momentum.
*   **Mission Control Dashboard**: Premium UI with real-time portfolio health, smart alerts, and verified news sources.
*   **Sector Management**: Filter analysis by specific sectors (Tech, Finance, etc.).
*   **Privacy First**: All data (Portfolio, Notes) is stored in a local PostgreSQL database.

## 🛠 Tech Stack

*   **Backend**: Python (FastAPI), SQLModel (ORM), Alembic
*   **Database**: PostgreSQL 15 (Dockerized)
*   **AI**: Ollama (Llama 3.2), Docker
*   **Frontend**: React (Vite), TailwindCSS, Lucide Icons

## 📋 Performance & Hardware Acceleration

The AI Analysis performance depends heavily on where **Ollama** is running.

### 🏎️ Case 1: MacOS / Apple Silicon (Recommended)
**Speed: ~2-5 seconds per analysis**
For high performance, run Ollama natively on your Mac to utilize the **Metal GPU**.
1.  Download and install [Ollama for Mac](https://ollama.com).
2.  Open the Ollama app or run `ollama serve`.
3.  In `docker-compose.yml`, ensure `OLLAMA_HOST` is set to `http://host.docker.internal:11434` (This is the default).

### 🐢 Case 2: Docker-only (Standard)
**Speed: ~5-10 minutes per analysis**
Use this if you don't want to install extra apps. The AI will run on your CPU inside the container.
1.  In `docker-compose.yml`, change `OLLAMA_HOST` to `http://ollama:11434`.
2.  The `stock_ollama` container will handle everything.

## 📋 Prerequisites

*   **Docker** & **Docker Compose**
*   **Node.js** v18+ & **npm**
*   **Ollama** (Optional, for high performance on Mac/Windows)

## ⚡ Quick Start

### 1. Start the Backend Infrastructure
The Backend, Database, and Ollama run in Docker containers.

```bash
make up
# OR: docker-compose up --build -d
```

### 2. Initialize the AI Model
One-time setup to download the Llama 3.2 model size (approx 2GB). Only in Case 2 settings: Docker-only (Standard)
*(Ensure containers are running first)*

```bash
make model
# OR: docker exec -it stock_ollama ollama run llama3.2
```

### 3. Start the Frontend
Open a new terminal window.

```bash
make frontend-install
make frontend-run
```
Visit **http://localhost:3000** in your browser.

## 👤 First Time Login
Since the database starts empty, you need to create an initial user.
1. Go to the API Docs: [http://localhost:8050/docs](http://localhost:8050/docs)
2. Use the **POST /auth/register** endpoint.
   ```json
   {
     "username": "admin",
     "hashed_password": "password"
   }
   ```
3. Login on the Frontend with `admin` / `password`.

## 📂 Project Structure

```
├── backend/            # FastAPI Application
│   ├── auth/           # JWT & Security
│   ├── models/         # SQLModel Database Tables
│   ├── routers/        # API Endpoints
│   ├── services/       # Business Logic (Analysis, News, Allocation)
│   └── main.py         # Entry Point
├── frontend/           # React Application
│   ├── src/
│   │   ├── components/ # Reusable UI components
│   │   ├── pages/      # Main Screens (Dashboard, Portfolio, etc.)
│   │   └── api.js      # Axios Setup
├── docker-compose.yml  # Container Orchestration
└── Makefile            # Shortcut Commands
```

## Trading view

1. Who creates the Trade Plan?
Currently, it is a collaborative flow:

The Market Scan (Discovery Engine): This runs automatically (or via manual trigger). It "discovers" high-conviction setups and places them in the Alpha Discovery Grid. These are Suggestions, not yet plans.
The User: You review the discovery grid. If you see a setup you like (e.g., "NVDA VCP breakout"), you would (ideally) click a button to "Commit to Plan." This is where you finalize the Entry (the buy price), Stop (the sell price), and Target (the target price).
The Conclusion: Once you finalize it, the system creates the 
TradePlan
 record, locks it (if it's the weekend), and the R-Manager immediately calculates the shares for you.
[!NOTE] In the current UI, the discovery items and trade plans are displayed separately. We can add a "Create Plan from Discovery" button to make this link even smoother!

## Inte-Market Correlation

When the r-coefficient (correlation) stays above 0.70 (or below -0.70), it means the market has entered a "Macro-Driven Regime." In these periods, your individual stock analysis (VCP, RSI, Earnings) becomes secondary to the "Big Waves."

Here are the concrete actions you should take based on the institutional playbook:

1. The "Tide" Check (Position Sizing)
Action: Reduce your Risk per Trade in the R-Manager.
Logic: When correlations are high $(\pm 0.70)$, individual stock setups are likely to fail if the index moves against them. Cut your risk from 1.0% to 0.5% until correlations drop below 0.50. This protects you from "systemic flushes."

2. DXY (US Dollar) Correlation
If $r < -0.70$ (Strong Inverse):
Action: Watch the Dollar Index (DXY) as your primary "Stop Light."
Strategy: If the DXY is rising, do not buy breakouts, even if they look perfect. Wait for the DXY to hit a daily ceiling (resistance) before committing to a VCP setup.

3. TNX (10Y Yield) Correlation
If $r > 0.70$ (Strong Positive) or $r < -0.70$:
Action: Rotate your sector exposure.
Strategy: High rate-sensitivity means High-PE Growth (Tech/AI) will be volatile. If yields are rising and correlation is high, shift your "Alpha Scan" toward Financials (XLF) or Energy (XLE), which often benefit from higher rates.

4. VIX (Volatility) Correlation
If $r < -0.80$ (Standard Inverse):
Action: Use the VIX as a "Contrarian Entry-Trigger."
Strategy: When the VIX spikes into the 20-25 range and correlations are locked, look for your Alpha Setups to be "Oversold." This is often the best time to enter a Relative Strength (RS) leader that is holding up better than the SPY.

5. Stop Being a "Hero"
Action: Do not buy "Sore Thumbs" (stocks moving opposite to the market).
Logic: In high-correlation regimes, "divergence" is often a trap. If the market is dumping and your stock is holding green, it will likely "catch up" to the downside eventually once the correlation snaps back.


Pro Tip: Look for the "Correlation Divergence." When a stock's correlation to the SPY drops while its Relative Strength increases, you have found a true institutional leader that is being accumulated regardless of the macro noise. That is where the real money is made. 

## Weekend Performance Review

The Institutional Weekend Performance Review is now fully operational! 🛡️📊✨

How to use it: In your Trading Hub, scroll down to the bottom. You will now see a new section: "Weekend Performance Post-Mortem."

Generate Review: Click the "GENERATE NEW REVIEW" button. The system will immediately:
Fetch the latest closing prices for every stock in your active Trade Plans.
Compare the weekly close to your Entry and Targets.
Calculate your Total Portfolio Exposure and Cumulative Risk % (the "Sleep Well" factor).
AI Verdict: An AI Risk Manager will analyze the weekly price action and generate a structured 3-part report covering Position Performance, Risk Management, and Learning/Archiving.
Risk Gauges: You'll see high-level metrics for your total dollar exposure and cumulative risk percentage, flagged as "Acceptable" or "Caution" depending on your portfolio density.
This completes the institutional loop: from Alpha Discovery to R-Manager Execution and finally Post-Mortem Review. 🚀📉📡