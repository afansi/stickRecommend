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
1. Go to the API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)
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


