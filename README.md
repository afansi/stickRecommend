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

## 📋 Prerequisites

*   **Docker** & **Docker Compose**
*   **Node.js** v18+ & **npm**
*   **Make** (Optional, for easy commands)

## ⚡ Quick Start

### 1. Start the Backend Infrastructure
The Backend, Database, and Ollama run in Docker containers.

```bash
make up
# OR: docker-compose up --build -d
```

### 2. Initialize the AI Model
One-time setup to download the Llama 3.2 model size (approx 2GB).
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
