from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database import init_db
from routers import auth, portfolio, analysis, user_settings, alerts, macro, risk, journal, reporting

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    
    # Start the scheduler
    from services.scheduler_service import start_scheduler, stop_scheduler
    start_scheduler()
    
    yield
    
    # Shutdown
    stop_scheduler()

app = FastAPI(
    title="Stock Intelligence API",
    description="Backend for Stock Recommendation App",
    version="0.1.0",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:3000"],  # Frontend URLs
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

app.include_router(auth.router)
app.include_router(portfolio.router)
app.include_router(analysis.router)
app.include_router(user_settings.router)
app.include_router(alerts.router)
app.include_router(macro.router)
app.include_router(risk.router)
app.include_router(journal.router)
app.include_router(reporting.router)

@app.get("/")
async def root():
    return {"message": "Stock Intelligence API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
