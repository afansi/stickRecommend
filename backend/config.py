import os

class Settings:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@localhost:5432/stock_app")
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkeychangeinproduction")
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # LLM Settings
    # Options: "openai", "anthropic", "gemini", "deepseek", "ollama"
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower() 
    
    # Models: "gpt-4", "claude-3-opus", "gemini-pro", "llama3.2" (default for ollama)
    LLM_MODEL = os.getenv("LLM_MODEL", "llama3.2")
    
    # API Key (Required for Cloud Providers)
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    
    @property
    def USE_CLOUD(self) -> bool:
        return self.LLM_PROVIDER != "ollama"

settings = Settings()

SECTOR_2_ETF_MAP = {
    "Technology": "XLK", "Information Technology": "XLK",
    "Healthcare": "XLV",
    "Financial Services": "XLF", "Financials": "XLF",
    "Energy": "XLE",
    "Consumer Defensive": "XLP", "Consumer Staples": "XLP",
    "Industrials": "XLI",
    "Basic Materials": "XLB", "Materials": "XLB",
    "Consumer Cyclical": "XLY", "Consumer Discretionary": "XLY",
    "Utilities": "XLU",
    "Real Estate": "XLRE",
    "Communication Services": "XLC",
    "Defense": "ITA", "Defence": "ITA",
    "Semiconductor": "SOXX",
    "Biotech": "IBB",
    "Clean Energy": "ICLN", 
    "Transport": "IYT", "Transportation": "IYT",
    "Retail": "XRT",
    "Bank": "KRE", "Regional Banking": "KRE",
    "Gold": "GDX", "Gold Miners": "GDX",
    "Cybersecurity": "CIBR",
    "Solar": "TAN",
    "Critical Materials": "SETM",
    "Strategic Metals": "REMX",
    "Homebuilders": "XHB",
    "Cloud Computing": "SKYY",
    "Robotics & AI": "BOTZ",
    "Oil & Gas Exploration": "XOP",
}

COUNTRY_BENCHMARKS = {
    "default": "SPY",
    ".DE": "^GDAXI",  # Germany (DAX)
    ".PA": "^FCHI",   # France (CAC 40)
    ".L": "^FTSE",    # UK (FTSE 100)
    ".TO": "^GSPTSE", # Canada (TSX)
}

# Scheduler Configuration
SCAN_SCHEDULE = os.getenv("SCAN_SCHEDULE", "0 1 * * 0")  # Default: Sunday at 1 AM (cron format)
ENABLE_SCHEDULED_SCAN = os.getenv("ENABLE_SCHEDULED_SCAN", "true").lower() == "true"