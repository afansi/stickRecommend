from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import init_db
from routers import auth, portfolio, analysis, user_settings, alerts

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

app.include_router(auth.router)
app.include_router(portfolio.router)
app.include_router(analysis.router)
app.include_router(user_settings.router)
app.include_router(alerts.router)

@app.get("/")
async def root():
    return {"message": "Stock Intelligence API is running", "status": "healthy"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}
