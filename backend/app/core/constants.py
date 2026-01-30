# Sector mapping for NSE stocks
SECTOR_MAP = {
    "RELIANCE": "Oil & Gas", "ONGC": "Oil & Gas", "IOC": "Oil & Gas", "BPCL": "Oil & Gas", "GAIL": "Oil & Gas",
    "TCS": "IT", "INFY": "IT", "WIPRO": "IT", "HCLTECH": "IT", "TECHM": "IT", "LTI": "IT", "LTIM": "IT", "COFORGE": "IT", "MPHASIS": "IT", "PERSISTENT": "IT",
    "HDFCBANK": "Banking", "ICICIBANK": "Banking", "KOTAKBANK": "Banking", "AXISBANK": "Banking", "SBIN": "Banking", "INDUSINDBK": "Banking", "BANDHANBNK": "Banking", "FEDERALBNK": "Banking", "IDFCFIRSTB": "Banking", "PNB": "Banking",
    "HDFC": "Finance", "BAJFINANCE": "Finance", "BAJAJFINSV": "Finance", "SBILIFE": "Finance", "HDFCLIFE": "Finance", "ICICIPRULI": "Finance", "CHOLAFIN": "Finance", "M&MFIN": "Finance", "SHRIRAMFIN": "Finance",
    "SUNPHARMA": "Pharma", "DRREDDY": "Pharma", "CIPLA": "Pharma", "DIVISLAB": "Pharma", "APOLLOHOSP": "Pharma", "BIOCON": "Pharma", "LUPIN": "Pharma", "AUROPHARMA": "Pharma", "TORNTPHARM": "Pharma",
    "HINDUNILVR": "FMCG", "ITC": "FMCG", "NESTLEIND": "FMCG", "BRITANNIA": "FMCG", "DABUR": "FMCG", "MARICO": "FMCG", "COLPAL": "FMCG", "GODREJCP": "FMCG", "TATACONSUM": "FMCG",
    "TATAMOTORS": "Auto", "MARUTI": "Auto", "M&M": "Auto", "BAJAJ-AUTO": "Auto", "HEROMOTOCO": "Auto", "EICHERMOT": "Auto", "ASHOKLEY": "Auto", "TVSMOTOR": "Auto", "TATAMTRDVR": "Auto",
    "TATASTEEL": "Metals", "JSWSTEEL": "Metals", "HINDALCO": "Metals", "VEDL": "Metals", "COALINDIA": "Metals", "NMDC": "Metals", "SAIL": "Metals", "JINDALSTEL": "Metals",
    "LT": "Infrastructure", "ULTRACEMCO": "Infrastructure", "GRASIM": "Infrastructure", "ADANIPORTS": "Infrastructure", "ADANIENT": "Infrastructure", "DLF": "Infrastructure", "GODREJPROP": "Infrastructure",
    "POWERGRID": "Power", "NTPC": "Power", "TATAPOWER": "Power", "ADANIGREEN": "Power", "ADANIPOWER": "Power", "NHPC": "Power", "TORNTPOWER": "Power",
    "BHARTIARTL": "Telecom", "IDEA": "Telecom", "INDUSTOWER": "Telecom",
    "ASIANPAINT": "Paints", "BERGEPAINT": "Paints", "PIDILITIND": "Paints",
    "TITAN": "Consumer", "PAGEIND": "Consumer", "RELAXO": "Consumer", "BATAINDIA": "Consumer", "TRENT": "Consumer",
}

# Tax rates for India FY 2024-25
TAX_RATES = {
    "LTCG_RATE": 0.125,      # 12.5% for gains > 1.25L
    "STCG_RATE": 0.20,       # 20% for equity
    "LTCG_EXEMPTION": 125000  # 1.25 Lakh exemption
}

# Benchmark returns (approximate annual)
BENCHMARKS = {
    "NIFTY_50": {"1y": 12, "3y": 10, "5y": 11},
    "INFLATION": 6.0,
    "FD_RATE": 7.0,
    "RISK_FREE_RATE": 0.07
}

# Default asset allocation
DEFAULT_ALLOCATION = {"Equity": 60, "Debt": 30, "Gold": 5, "Cash": 5}

# External API URLs
YAHOO_FINANCE_BASE = "https://query1.finance.yahoo.com"
YAHOO_CHART_URL = f"{YAHOO_FINANCE_BASE}/v8/finance/chart"
YAHOO_SEARCH_URL = f"{YAHOO_FINANCE_BASE}/v1/finance/search"
YAHOO_QUOTE_URL = f"{YAHOO_FINANCE_BASE}/v10/finance/quoteSummary"
