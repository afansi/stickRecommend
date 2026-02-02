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

# Regional Overrides for Sector Benchmarks
# Europe: Using iShares STOXX Europe 600 Sector ETFs
# Canada: Using iShares S&P/TSX Capped Sector ETFs
REGIONAL_SECTOR_MAPS = {
    "EU": {
        "Technology": "EXV3.DE", "Information Technology": "EXV3.DE",
        "Healthcare": "EXV4.DE",
        "Financial Services": "EXV5.DE", "Financials": "EXV1.DE",
        "Energy": "EXW1.DE",
        "Consumer Defensive": "EXV7.DE", "Consumer Staples": "EXV7.DE",
        "Industrials": "EXV9.DE",
        "Basic Materials": "EXV6.DE", "Materials": "EXV6.DE",
        "Consumer Cyclical": "EXV2.DE", "Consumer Discretionary": "EXV2.DE",
        "Utilities": "EXV8.DE",
        "Real Estate": "EXV4.DE", # Fallback
        "Communication Services": "EXV10.DE",
    },
    "CA": {
        "Technology": "XIT.TO", "Information Technology": "XIT.TO",
        "Healthcare": "XLV", # Canada fallback to US
        "Financial Services": "XFN.TO", "Financials": "XFN.TO",
        "Energy": "XEG.TO",
        "Consumer Defensive": "XST.TO", "Consumer Staples": "XST.TO",
        "Industrials": "XLI", # Fallback
        "Basic Materials": "XMA.TO", "Materials": "XMA.TO",
        "Consumer Cyclical": "XCD.TO", "Consumer Discretionary": "XCD.TO",
        "Utilities": "XUT.TO",
        "Real Estate": "XRE.TO",
        "Communication Services": "XLC", # Fallback
    }
}

COUNTRY_BENCHMARKS = {
    "default": "SPY",
    ".DE": "^GDAXI",  # Germany (DAX)
    ".PA": "^FCHI",   # France (CAC 40)
    ".L": "^FTSE",    # UK (FTSE 100)
    ".TO": "^GSPTSE", # Canada (TSX)
}

# Static Fallback Map (Mini version)
ETF_HOLDINGS_FALLBACK_MAP = {
    # US Favorites
    "XLK": ["NVDA", "MSFT", "AAPL", "AVGO", "ORCL", "CRM", "AMD", "ADBE", "QCOM", "TXN"],
    "XLF": ["JPM", "V", "MA", "BAC", "WFC", "MS", "GS", "AXP", "BLK", "C"],
    "XLV": ["LLY", "UNH", "JNJ", "ABBV", "MRK", "TMO", "AMGN", "PFE", "ISRG", "DHR"],
    "XLE": ["XOM", "CVX", "COP", "EOG", "SLB", "MPC", "PSX", "VLO", "WMB", "OKE"],
    "XLY": ["AMZN", "TSLA", "HD", "MCD", "NKE", "LOW", "SBUX", "BKNG", "TJX", "MAR"],
    "SOXX": ["NVDA", "AVGO", "AMD", "QCOM", "TXN", "MU", "INTC", "AMAT", "LRCX", "ADI"],
    "ITA": ["RTX", "LMT", "GD", "NOC", "BA", "TDG", "LHX", "HWM", "TXT", "AXON"],
    "XLC": ["GOOGL", "META", "NFLX", "DIS", "TMUS", "CMCSA", "VZ", "T", "CHTR", "WBD"],
    'XLP': ['WMT', 'COST', 'PG', 'KO', 'PM', 'PEP', 'MDLZ', 'MO', 'CL', 'MNST'],
    'XLI': ['GE', 'CAT', 'RTX', 'BA', 'UBER', 'GEV', 'UNP', 'HON', 'ETN', 'DE'],
    'XLB': ['LIN', 'NEM', 'CRH', 'SHW', 'FCX', 'ECL', 'APD', 'CTVA', 'MLM', 'NUE'],
    'XLU': ['NEE', 'CEG', 'SO', 'DUK', 'AEP', 'SRE', 'VST', 'D', 'EXC', 'XEL'],

    # EU Favorites (STOXX 600)
    "EXV3.DE": ["ASML.AS", "SAP.DE", "PRX.AS", "IFX.DE", "CAP.PA", "STM.PA", "DSY.PA", "AMS.MC", "SGE.L", "ASM.AS"],
    "EXV4.DE": ["NOVO-B.CO", "NOVN.SW", "ROG.SW", "AZN.L", "SAN.PA", "GSK.L", "EL.PA", "MC.PA", "OR.PA", "BAYN.DE"],
    "EXV1.DE": ["HSBA.L", "BNP.PA", "SAN.MC", "UCG.MI", "ISP.MI", "INGA.AS", "BBVA.MC", "NDA-FI.HE", "GLE.PA", "DNB.OL"],
    "EXW1.DE": ["SHEL.L", "TTE.PA", "BP.L", "ENI.MI", "EQNR.OL", "REP.MC", "SNAM.MI", "NES1V.HE", "GALP.LS", "OMV.VI"],
    "EXV7.DE": ["NESN.SW", "DGE.L", "ABF.L", "HEIA.AS", "RI.PA", "DNLM.ST", "HEIO.AS", "JDE.AS", "GIVN.SW", "BEI.DE"],
    "EXV9.DE": ["SIE.DE", "AIR.PA", "SCHN.PA", "REL.L", "ABB.SW", "VOW3.DE", "DHL.DE", "BAE.L", "DSV.CO", "ALV.DE"],
    "EXV6.DE": ["RIO.L", "GLEN.L", "AAL.L", "UPM.HE", "ANTO.L", "BOL.ST", "STE.HE", "SKF-B.ST", "NHY.OL", "SSAB-B.ST"],
    "EXV2.DE": ["MC.PA", "OR.PA", "RMS.PA", "CFR.SW", "KER.PA", "ADS.DE", "MONC.MI", "PUM.DE", "SWON.SW", "BMB.L"],
    "EXV8.DE": ["IBE.MC", "ENEL.MI", "NG.L", "RWE.DE", "EDP.LS", "SSE.L", "EOAN.DE", "ORSTED.CO", "TRN.MI", "REE.MC"],
    "EXV10.DE": ["DTE.DE", "VOD.L", "ORAN.PA", "TEF.MC", "TEL.OL", "BT-A.L", "TKA.DE", "SWISSCH.SW", "TLC.ST", "TEF.DE"],

    # Canada Favorites (S&P/TSX)
    "XIT.TO": ["CSU.TO", "SHOP.TO", "GIB-A.TO", "OTEX.TO", "DSG.TO", "LSPD.TO", "KXS.TO", "CTS.TO", "BB.TO", "ENGH.TO"],
    "XFN.TO": ["RY.TO", "TD.TO", "BN.TO", "BMO.TO", "BNS.TO", "CM.TO", "MFC.TO", "SLF.TO", "IFC.TO", "POW.TO"],
    "XEG.TO": ["CNQ.TO", "SU.TO", "CVE.TO", "IMO.TO", "TOU.TO", "ARX.TO", "CPG.TO", "WCP.TO", "MEG.TO", "ERF.TO"],
    "XST.TO": ["ATD.TO", "L.TO", "WN.TO", "MRU.TO", "DOL.TO", "SAP.TO", "EMP-A.TO", "PWF.TO", "PBH.TO", "LNF.TO"],
    "XMA.TO": ["NTR.TO", "ABX.TO", "FM.TO", "WPM.TO", "AEM.TO", "TECK-B.TO", "FNV.TO", "IVN.TO", "CCO.TO", "WFG.TO"],
    "XCD.TO": ["MRE.TO", "CTC-A.TO", "DOO.TO", "GIL.TO", "PET.TO", "ATZ.TO", "LNR.TO", "TOY.TO", "RCH.TO", "ZZZ.TO"],
    "XUT.TO": ["FTS.TO", "EMA.TO", "H.TO", "CPX.TO", "AQN.TO", "CU.TO", "ACO-X.TO", "BEP-UN.TO", "RNW.TO", "NPI.TO"],
    "XRE.TO": ["CAR-UN.TO", "REI-UN.TO", "GRT-UN.TO", "SRU-UN.TO", "AP-UN.TO", "DIR-UN.TO", "HR-UN.TO", "CHP-UN.TO", "KMP-UN.TO", "CAR.UN.TO"]
}

MAX_YF_WORKERS = 3

# Scheduler Configuration
SCAN_SCHEDULE = os.getenv("SCAN_SCHEDULE", "0 1 * * 0")  # Default: Sunday at 1 AM (cron format)
ENABLE_SCHEDULED_SCAN = os.getenv("ENABLE_SCHEDULED_SCAN", "true").lower() == "true"