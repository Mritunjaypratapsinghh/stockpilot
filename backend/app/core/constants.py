# Sector mapping for NSE stocks
SECTOR_MAP = {
    # Oil & Gas
    "RELIANCE": "Oil & Gas",
    "ONGC": "Oil & Gas",
    "IOC": "Oil & Gas",
    "BPCL": "Oil & Gas",
    "GAIL": "Oil & Gas",
    "HINDPETRO": "Oil & Gas",
    "PETRONET": "Oil & Gas",
    "MGL": "Oil & Gas",
    "IGL": "Oil & Gas",
    "GUJGASLTD": "Oil & Gas",
    "OIL": "Oil & Gas",
    # IT
    "TCS": "IT",
    "INFY": "IT",
    "WIPRO": "IT",
    "HCLTECH": "IT",
    "TECHM": "IT",
    "LTI": "IT",
    "LTIM": "IT",
    "COFORGE": "IT",
    "MPHASIS": "IT",
    "PERSISTENT": "IT",
    "KPITTECH": "IT",
    "HAPPSTMNDS": "IT",
    "ROUTE": "IT",
    "TATAELXSI": "IT",
    "ZENSAR": "IT",
    "BIRLASOFT": "IT",
    "MASTEK": "IT",
    "CYIENT": "IT",
    "SONATA": "IT",
    "NEWGEN": "IT",
    # Banking
    "HDFCBANK": "Banking",
    "ICICIBANK": "Banking",
    "KOTAKBANK": "Banking",
    "AXISBANK": "Banking",
    "SBIN": "Banking",
    "INDUSINDBK": "Banking",
    "BANDHANBNK": "Banking",
    "FEDERALBNK": "Banking",
    "IDFCFIRSTB": "Banking",
    "PNB": "Banking",
    "BANKBARODA": "Banking",
    "CANBK": "Banking",
    "UNIONBANK": "Banking",
    "INDIANB": "Banking",
    "AUBANK": "Banking",
    "RBLBANK": "Banking",
    "CUB": "Banking",
    "KARURVYSYA": "Banking",
    # Finance / NBFC
    "BAJFINANCE": "Finance",
    "BAJAJFINSV": "Finance",
    "SBILIFE": "Finance",
    "HDFCLIFE": "Finance",
    "ICICIPRULI": "Finance",
    "CHOLAFIN": "Finance",
    "M&MFIN": "Finance",
    "SHRIRAMFIN": "Finance",
    "MUTHOOTFIN": "Finance",
    "MANAPPURAM": "Finance",
    "LICHSGFIN": "Finance",
    "PFC": "Finance",
    "RECLTD": "Finance",
    "IRFC": "Finance",
    "CANFINHOME": "Finance",
    "IIFL": "Finance",
    "POONAWALLA": "Finance",
    "SUNDARMFIN": "Finance",
    "DAMCAPITAL": "Finance",
    "ANGELONE": "Finance",
    "BSE": "Finance",
    "CDSL": "Finance",
    "CAMS": "Finance",
    "MCX": "Finance",
    # Pharma / Healthcare
    "SUNPHARMA": "Pharma",
    "DRREDDY": "Pharma",
    "CIPLA": "Pharma",
    "DIVISLAB": "Pharma",
    "APOLLOHOSP": "Pharma",
    "BIOCON": "Pharma",
    "LUPIN": "Pharma",
    "AUROPHARMA": "Pharma",
    "TORNTPHARM": "Pharma",
    "ALKEM": "Pharma",
    "IPCALAB": "Pharma",
    "LALPATHLAB": "Pharma",
    "METROPOLIS": "Pharma",
    "MAXHEALTH": "Pharma",
    "FORTIS": "Pharma",
    "GLAND": "Pharma",
    "NATCOPHARM": "Pharma",
    "LAURUSLABS": "Pharma",
    # FMCG
    "HINDUNILVR": "FMCG",
    "ITC": "FMCG",
    "NESTLEIND": "FMCG",
    "BRITANNIA": "FMCG",
    "DABUR": "FMCG",
    "MARICO": "FMCG",
    "COLPAL": "FMCG",
    "GODREJCP": "FMCG",
    "TATACONSUM": "FMCG",
    "VBL": "FMCG",
    "UBL": "FMCG",
    "RADICO": "FMCG",
    "EMAMILTD": "FMCG",
    "JYOTHYLAB": "FMCG",
    # Auto
    "TATAMOTORS": "Auto",
    "MARUTI": "Auto",
    "M&M": "Auto",
    "BAJAJ-AUTO": "Auto",
    "HEROMOTOCO": "Auto",
    "EICHERMOT": "Auto",
    "ASHOKLEY": "Auto",
    "TVSMOTOR": "Auto",
    "TATAMTRDVR": "Auto",
    "MOTHERSON": "Auto",
    "BOSCHLTD": "Auto",
    "BALKRISIND": "Auto",
    "MRF": "Auto",
    "EXIDEIND": "Auto",
    "AMARAJABAT": "Auto",
    "OLECTRA": "Auto",
    "TIINDIA": "Auto",
    # Metals & Mining
    "TATASTEEL": "Metals",
    "JSWSTEEL": "Metals",
    "HINDALCO": "Metals",
    "VEDL": "Metals",
    "COALINDIA": "Metals",
    "NMDC": "Metals",
    "SAIL": "Metals",
    "JINDALSTEL": "Metals",
    "NATIONALUM": "Metals",
    "RATNAMANI": "Metals",
    "APLAPOLLO": "Metals",
    # Infrastructure / Construction
    "LT": "Infrastructure",
    "ULTRACEMCO": "Infrastructure",
    "GRASIM": "Infrastructure",
    "ADANIPORTS": "Infrastructure",
    "ADANIENT": "Infrastructure",
    "DLF": "Infrastructure",
    "GODREJPROP": "Infrastructure",
    "OBEROIRLTY": "Infrastructure",
    "PRESTIGE": "Infrastructure",
    "BRIGADE": "Infrastructure",
    "SHREECEM": "Infrastructure",
    "AMBUJACEM": "Infrastructure",
    "ACC": "Infrastructure",
    "RAMCOCEM": "Infrastructure",
    "IRCON": "Infrastructure",
    "RVNL": "Infrastructure",
    "NBCC": "Infrastructure",
    "BEL": "Defence",
    "HAL": "Defence",
    "MAZAGON": "Defence",
    "COCHINSHIP": "Defence",
    "BDL": "Defence",
    "GRSE": "Defence",
    # Power / Energy
    "POWERGRID": "Power",
    "NTPC": "Power",
    "TATAPOWER": "Power",
    "ADANIGREEN": "Power",
    "ADANIPOWER": "Power",
    "NHPC": "Power",
    "TORNTPOWER": "Power",
    "SJVN": "Power",
    "CESC": "Power",
    "SUZLON": "Power",
    "IREDA": "Power",
    "JPPOWER": "Power",
    "RPOWER": "Power",
    "JSPL": "Power",
    # Telecom
    "BHARTIARTL": "Telecom",
    "IDEA": "Telecom",
    "INDUSTOWER": "Telecom",
    # Paints / Chemicals
    "ASIANPAINT": "Chemicals",
    "BERGEPAINT": "Chemicals",
    "PIDILITIND": "Chemicals",
    "SRF": "Chemicals",
    "AARTI": "Chemicals",
    "DEEPAKNTR": "Chemicals",
    "CLEAN": "Chemicals",
    "ATUL": "Chemicals",
    # Consumer / Retail
    "TITAN": "Consumer",
    "PAGEIND": "Consumer",
    "RELAXO": "Consumer",
    "BATAINDIA": "Consumer",
    "TRENT": "Consumer",
    "DMART": "Consumer",
    "NYKAA": "Consumer",
    "ZOMATO": "Consumer",
    "PAYTM": "Consumer",
    "POLICYBZR": "Consumer",
    "CARTRADE": "Consumer",
    "SAFARI": "Consumer",
    "MEDPLUS": "Consumer",
    # Media / Entertainment
    "PVRINOX": "Media",
    "ZEEL": "Media",
    "SUNTV": "Media",
    # ETFs
    "GOLDBEES": "Gold ETF",
    "SILVERBEES": "Silver ETF",
    "NIFTYBEES": "Index ETF",
    "JUNIORBEES": "Index ETF",
    "BANKBEES": "Index ETF",
    "KOTAKALPHA": "Factor ETF",
    "MOM30IETF": "Factor ETF",
    "ALPHAETF": "Factor ETF",
    "MOM100": "Factor ETF",
    "MOVALUE": "Factor ETF",
}

# Tax rates for India FY 2024-25
TAX_RATES = {
    "LTCG_RATE": 0.125,  # 12.5% for gains > 1.25L
    "STCG_RATE": 0.20,  # 20% for equity
    "LTCG_EXEMPTION": 125000,  # 1.25 Lakh exemption
}

# Benchmark returns (approximate annual)
BENCHMARKS = {"NIFTY_50": {"1y": 12, "3y": 10, "5y": 11}, "INFLATION": 6.0, "FD_RATE": 7.0, "RISK_FREE_RATE": 0.07}

# Default asset allocation
DEFAULT_ALLOCATION = {"Equity": 60, "Debt": 30, "Gold": 5, "Cash": 5}

# Magic numbers - thresholds and limits
XIRR_MAX_THRESHOLD = 1000  # Cap XIRR at 1000% to avoid outliers
NEAR_52W_HIGH_PCT = 0.95  # Within 5% of 52-week high
NEAR_52W_LOW_PCT = 1.05  # Within 5% of 52-week low
REBALANCE_THRESHOLD_PCT = 5  # Trigger rebalance if allocation differs by 5%
MF_UNDERPERFORM_THRESHOLD = 5  # MF underperforming if returns < benchmark - 5%
GMP_APPLY_THRESHOLD = 15  # IPO GMP > 15% = APPLY
GMP_MAY_APPLY_THRESHOLD = 5  # IPO GMP > 5% = MAY APPLY
RATE_LIMIT_REQUESTS = 10  # Max requests per second
CACHE_TTL_SECONDS = 60  # Price cache TTL
API_TIMEOUT_SECONDS = 10  # External API timeout

# External API URLs
YAHOO_FINANCE_BASE = "https://query1.finance.yahoo.com"
YAHOO_CHART_URL = f"{YAHOO_FINANCE_BASE}/v8/finance/chart"
YAHOO_SEARCH_URL = f"{YAHOO_FINANCE_BASE}/v1/finance/search"
YAHOO_QUOTE_URL = f"{YAHOO_FINANCE_BASE}/v10/finance/quoteSummary"

# Company name mapping for news search (symbol -> readable name)
COMPANY_NAMES = {
    "RELIANCE": "Reliance Industries",
    "TCS": "TCS Tata Consultancy",
    "INFY": "Infosys",
    "HDFCBANK": "HDFC Bank",
    "ICICIBANK": "ICICI Bank",
    "SBIN": "State Bank India",
    "BHARTIARTL": "Bharti Airtel",
    "ITC": "ITC Limited",
    "KOTAKBANK": "Kotak Mahindra Bank",
    "LT": "Larsen Toubro",
    "AXISBANK": "Axis Bank",
    "HINDUNILVR": "Hindustan Unilever",
    "BAJFINANCE": "Bajaj Finance",
    "MARUTI": "Maruti Suzuki",
    "TATAMOTORS": "Tata Motors",
    "TATASTEEL": "Tata Steel",
    "WIPRO": "Wipro",
    "HCLTECH": "HCL Technologies",
    "SUNPHARMA": "Sun Pharma",
    "ADANIENT": "Adani Enterprises",
    "ADANIPORTS": "Adani Ports",
    "TECHM": "Tech Mahindra",
    "POWERGRID": "Power Grid",
    "NTPC": "NTPC",
    "ULTRACEMCO": "UltraTech Cement",
    "TITAN": "Titan Company",
    "ASIANPAINT": "Asian Paints",
    "BAJAJFINSV": "Bajaj Finserv",
    "NESTLEIND": "Nestle India",
    "JSWSTEEL": "JSW Steel",
    "ONGC": "ONGC",
    "COALINDIA": "Coal India",
    "KOTAKALPHA": "Kotak Nifty Alpha 50 ETF",
}


# Rebalance constants
REBALANCE_MAX_SELL_PCT = 0.3  # Max 30% of position to sell in one rebalance
REBALANCE_MIN_ACTION_AMOUNT = 1000  # Min ₹1000 for any buy/sell action
REBALANCE_DEVIATION_THRESHOLD = 5  # Min % deviation to trigger rebalance suggestion
