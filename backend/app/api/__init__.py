from .auth import router as auth_router, get_current_user
from .portfolio import router as portfolio_router
from .alerts import router as alerts_router
from .market import router as market_router
from .research import router as research_router
from .ipo import router as ipo_router
from . import import_holdings

auth = type('auth', (), {'router': auth_router})()
portfolio = type('portfolio', (), {'router': portfolio_router})()
alerts = type('alerts', (), {'router': alerts_router})()
market = type('market', (), {'router': market_router})()
research = type('research', (), {'router': research_router})()
ipo = type('ipo', (), {'router': ipo_router})()
