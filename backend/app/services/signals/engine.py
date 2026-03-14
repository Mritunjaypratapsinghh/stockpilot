"""
Enhanced Signal Engine - Fundamentals + Technicals + Portfolio Context + LLM Insights
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from ...core.config import settings
from ...core.constants import SECTOR_MAP
from ...utils.logger import logger


class Confidence(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class MarketRegime(str, Enum):
    BULL = "BULL"
    BEAR = "BEAR"
    NEUTRAL = "NEUTRAL"
    CRASH = "CRASH"  # Nifty down > 2% today


@dataclass
class Fundamentals:
    pe: Optional[float] = None
    pb: Optional[float] = None
    roe: Optional[float] = None
    roce: Optional[float] = None
    debt_equity: Optional[float] = None
    profit_growth_3yr: Optional[float] = None
    promoter_holding: Optional[float] = None
    promoter_pledge: Optional[float] = None

    @property
    def is_quality(self) -> bool:
        """Check if fundamentals indicate quality stock"""
        checks = 0
        if self.roe and self.roe > 12:  # Lowered from 15
            checks += 1
        if self.roce and self.roce > 12:
            checks += 1
        if self.debt_equity is not None and self.debt_equity < 1:
            checks += 1
        if self.profit_growth_3yr and self.profit_growth_3yr > 0:
            checks += 1
        if self.pe and 5 < self.pe < 40:  # Reasonable PE
            checks += 1
        return checks >= 2

    @property
    def is_risky(self) -> bool:
        """Check for red flags"""
        if self.debt_equity and self.debt_equity > 2:
            return True
        if self.promoter_pledge and self.promoter_pledge > 20:
            return True
        if self.profit_growth_3yr and self.profit_growth_3yr < -20:
            return True
        return False

    @property
    def has_data(self) -> bool:
        """Check if we have any fundamental data"""
        return any([self.pe, self.roe, self.roce, self.debt_equity])


class SignalEngine:
    """Enhanced signal generation with fundamentals and context"""

    def __init__(self):
        self._nifty_cache: dict = {}
        self._fundamentals_cache: dict = {}

    async def get_market_regime(self) -> tuple[MarketRegime, float]:
        """Detect current market regime from Nifty 50"""
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(
                    "https://query1.finance.yahoo.com/v8/finance/chart/%5ENSEI?interval=1d&range=5d",
                    headers={"User-Agent": "Mozilla/5.0"},
                )
                if resp.status_code == 200:
                    result = resp.json()["chart"]["result"][0]
                    closes = [c for c in result["indicators"]["quote"][0]["close"] if c]
                    if len(closes) >= 2:
                        today_change = (closes[-1] - closes[-2]) / closes[-2] * 100
                        # 5-day trend
                        week_change = (closes[-1] - closes[0]) / closes[0] * 100 if len(closes) >= 5 else today_change

                        if today_change < -2:
                            return MarketRegime.CRASH, today_change
                        if week_change > 2:
                            return MarketRegime.BULL, today_change
                        if week_change < -2:
                            return MarketRegime.BEAR, today_change
                        return MarketRegime.NEUTRAL, today_change
        except Exception as e:
            logger.debug(f"Market regime check failed: {e}")
        return MarketRegime.NEUTRAL, 0.0

    async def get_fundamentals(self, symbol: str) -> Fundamentals:
        """Fetch fundamentals from Screener.in with caching"""
        if symbol in self._fundamentals_cache:
            return self._fundamentals_cache[symbol]

        fundamentals = Fundamentals()
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                resp = await client.get(
                    f"https://www.screener.in/company/{symbol}/consolidated/",
                    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                )
                if resp.status_code != 200:
                    # Try standalone
                    resp = await client.get(
                        f"https://www.screener.in/company/{symbol}/",
                        headers={"User-Agent": "Mozilla/5.0"},
                    )

                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "lxml")
                    ratios = {}

                    # Extract from ratio list
                    for li in soup.find_all("li", class_="flex flex-space-between"):
                        name = li.find("span", class_="name")
                        value = li.find("span", class_="number")
                        if name and value:
                            ratios[name.text.strip().lower()] = value.text.strip()

                    def parse_num(val: str) -> Optional[float]:
                        try:
                            return float(val.replace(",", "").replace("%", ""))
                        except (ValueError, AttributeError):
                            return None

                    fundamentals.pe = parse_num(ratios.get("stock p/e", ""))
                    fundamentals.pb = parse_num(ratios.get("price to book value", ""))
                    fundamentals.roe = parse_num(ratios.get("roe", ""))
                    fundamentals.roce = parse_num(ratios.get("roce", ""))
                    fundamentals.debt_equity = parse_num(ratios.get("debt to equity", ""))

                    # Try to get profit growth from quarters section
                    profit_growth = soup.find("span", string=lambda t: t and "Profit growth" in t if t else False)
                    if profit_growth:
                        parent = profit_growth.find_parent("li")
                        if parent:
                            num = parent.find("span", class_="number")
                            if num:
                                fundamentals.profit_growth_3yr = parse_num(num.text)

                    # Shareholding
                    for row in soup.find_all("tr"):
                        cells = row.find_all("td")
                        if len(cells) >= 2:
                            label = cells[0].text.strip().lower()
                            if "promoter" in label and "pledge" not in label:
                                fundamentals.promoter_holding = parse_num(cells[-1].text)
                            elif "pledge" in label:
                                fundamentals.promoter_pledge = parse_num(cells[-1].text)

        except Exception as e:
            logger.debug(f"Fundamentals fetch failed for {symbol}: {e}")

        self._fundamentals_cache[symbol] = fundamentals
        return fundamentals

    def calculate_sector_concentration(self, holdings: list, current_symbol: str) -> tuple[str, float]:
        """Calculate sector concentration for a symbol"""
        # Better sector detection for ETFs
        symbol_upper = current_symbol.upper()
        if "GOLD" in symbol_upper:
            sector = "Gold"
        elif "SILVER" in symbol_upper:
            sector = "Silver"
        elif "NIFTY" in symbol_upper or "SENSEX" in symbol_upper or "INDEX" in symbol_upper:
            sector = "Index ETF"
        elif "MOM" in symbol_upper or "ALPHA" in symbol_upper or "FACTOR" in symbol_upper:
            sector = "Factor ETF"
        else:
            sector = SECTOR_MAP.get(current_symbol, "Others")

        sector_value = 0
        total_value = 0

        for h in holdings:
            value = h.quantity * (h.current_price or h.avg_price)
            total_value += value
            h_sector = SECTOR_MAP.get(h.symbol, "Others")
            # Apply same ETF logic
            h_upper = h.symbol.upper()
            if "GOLD" in h_upper:
                h_sector = "Gold"
            elif "SILVER" in h_upper:
                h_sector = "Silver"
            elif "NIFTY" in h_upper or "SENSEX" in h_upper or "INDEX" in h_upper:
                h_sector = "Index ETF"
            elif "MOM" in h_upper or "ALPHA" in h_upper or "FACTOR" in h_upper:
                h_sector = "Factor ETF"

            if h_sector == sector:
                sector_value += value

        concentration = (sector_value / total_value * 100) if total_value > 0 else 0
        return sector, concentration

    async def generate_signal(
        self,
        symbol: str,
        avg_price: float,
        quantity: float,
        current_price: float,
        technicals: dict,
        holdings: list,
        market_regime: MarketRegime,
        nifty_change: float,
    ) -> dict:
        """Generate enhanced signal with fundamentals and context"""

        pnl_pct = ((current_price - avg_price) / avg_price * 100) if avg_price > 0 else 0
        rsi = technicals.get("rsi", 50)
        above_sma20 = technicals.get("above_sma20", True)
        above_sma50 = technicals.get("above_sma50", True)
        range_position = technicals.get("range_position", 50)

        # Fetch fundamentals
        fundamentals = await self.get_fundamentals(symbol)

        # Calculate sector concentration
        sector, concentration = self.calculate_sector_concentration(holdings, symbol)

        # Initialize signal
        action = "HOLD"
        reasons = []
        warnings = []
        confidence = Confidence.MEDIUM
        confidence_factors = []
        target = None
        stop_loss = None

        # === MARKET CONTEXT CHECK ===
        if market_regime == MarketRegime.CRASH:
            warnings.append(f"⚠️ Market down {nifty_change:.1f}% today - avoid panic decisions")

        # === CONCENTRATION WARNING ===
        if concentration > 25:
            warnings.append(f"⚠️ High {sector} exposure ({concentration:.0f}%) - diversify")

        # === FUNDAMENTAL RED FLAGS ===
        if fundamentals.is_risky:
            warnings.append("⚠️ Fundamental concerns detected")
            if fundamentals.debt_equity and fundamentals.debt_equity > 2:
                warnings.append(f"High debt (D/E: {fundamentals.debt_equity:.1f})")
            if fundamentals.promoter_pledge and fundamentals.promoter_pledge > 20:
                warnings.append(f"Promoter pledge: {fundamentals.promoter_pledge:.0f}%")

        # === SIGNAL GENERATION ===

        # STRONG BUY: Oversold + Quality fundamentals + Not concentrated
        if rsi < 30 and range_position < 20 and fundamentals.is_quality and not fundamentals.is_risky:
            action = "STRONG BUY"
            reasons.append(f"Oversold (RSI {rsi:.0f}) near 52W low + Strong fundamentals")
            if fundamentals.roe:
                reasons.append(f"ROE {fundamentals.roe:.0f}% shows good profitability")
            confidence = Confidence.HIGH
            confidence_factors = ["RSI oversold", "Near 52W low", "Quality fundamentals"]
            target = technicals.get("sma_20")

        # BUY MORE: Oversold with quality fundamentals
        elif rsi < 35 and fundamentals.is_quality and not fundamentals.is_risky:
            action = "BUY MORE"
            reasons.append(f"Oversold (RSI {rsi:.0f}) with solid fundamentals")
            if pnl_pct < -10:
                reasons.append(f"Good chance to average down (currently {pnl_pct:.0f}%)")
            confidence = Confidence.MEDIUM
            confidence_factors = ["RSI oversold", "Fundamentals OK"]
            target = technicals.get("sma_50")

        # ADD: Quality stock in loss but not oversold - average down opportunity
        elif pnl_pct < -15 and fundamentals.is_quality and not fundamentals.is_risky and above_sma50:
            action = "ADD"
            reasons.append(f"Quality stock down {abs(pnl_pct):.0f}% - averaging opportunity")
            reasons.append("Long-term trend intact, fundamentals strong")
            confidence = Confidence.MEDIUM
            confidence_factors = ["Quality fundamentals", "Good entry vs avg price"]
            target = avg_price  # Target is to recover to avg

        # WAIT: Oversold but can't verify fundamentals
        elif rsi < 35 and not fundamentals.has_data:
            action = "WAIT"
            reasons.append(f"Technically oversold (RSI {rsi:.0f})")
            reasons.append("Can't verify fundamentals - research before buying")
            confidence = Confidence.LOW
            target = technicals.get("sma_50")

        # AVOID: Oversold but risky fundamentals
        elif rsi < 35 and fundamentals.is_risky:
            action = "AVOID"
            reasons.append("Price falling for a reason - weak fundamentals")
            if fundamentals.debt_equity and fundamentals.debt_equity > 2:
                reasons.append(f"High debt (D/E {fundamentals.debt_equity:.1f}) is concerning")
            confidence = Confidence.MEDIUM

        # PARTIAL SELL: Overbought + Good profit
        elif rsi > 70 and pnl_pct > 20:
            action = "PARTIAL SELL"
            reasons.append(f"Up {pnl_pct:.0f}% and RSI {rsi:.0f} shows overbought")
            reasons.append("Book 25-50% profits to lock in gains")
            confidence = Confidence.HIGH if rsi > 75 else Confidence.MEDIUM
            confidence_factors = ["RSI overbought", "Good profit"]

        # PARTIAL SELL: Near 52W high with big profit
        elif range_position > 90 and pnl_pct > 30:
            action = "PARTIAL SELL"
            reasons.append(f"Near 52-week high with {pnl_pct:.0f}% profit")
            reasons.append("Consider booking 25-50% - protect your gains")
            confidence = Confidence.MEDIUM

        # TRIM: Overweight position with profit
        elif concentration > 25 and pnl_pct > 15:
            action = "TRIM"
            reasons.append(f"{sector} is {concentration:.0f}% of portfolio - overweight")
            reasons.append(f"Up {pnl_pct:.0f}% - good time to rebalance")
            confidence = Confidence.MEDIUM

        # EXIT: Big loss + Weak fundamentals + Downtrend
        elif pnl_pct < -25 and not above_sma50 and fundamentals.is_risky:
            action = "EXIT"
            reasons.append(f"Down {abs(pnl_pct):.0f}% with weak fundamentals")
            reasons.append("Cut losses - this money can work better elsewhere")
            confidence = Confidence.MEDIUM
            confidence_factors = ["Deep loss", "Weak fundamentals", "Downtrend"]

        # EXIT: Huge loss regardless of fundamentals
        elif pnl_pct < -40 and not above_sma50:
            action = "EXIT"
            reasons.append(f"Down {abs(pnl_pct):.0f}% in downtrend")
            reasons.append("Consider tax-loss harvesting and reinvesting")
            confidence = Confidence.LOW

        # HOLD with stop-loss: Profit but weakening momentum
        elif pnl_pct > 10 and not above_sma20:
            action = "HOLD"
            reasons.append(f"Up {pnl_pct:.0f}% but momentum slowing")
            stop_loss = technicals.get("support")
            if stop_loss:
                reasons.append(f"Set stop-loss at ₹{stop_loss:.0f} to protect gains")
            confidence = Confidence.MEDIUM

        # HOLD: Quality stock, no action needed
        elif fundamentals.is_quality and -10 < pnl_pct < 20:
            action = "HOLD"
            reasons.append("Quality stock performing as expected")
            if pnl_pct >= 0:
                reasons.append(f"Up {pnl_pct:.0f}% - let winners run")
            else:
                reasons.append(f"Down {abs(pnl_pct):.0f}% but fundamentals intact")
            confidence = Confidence.MEDIUM

        # DEFAULT HOLD
        else:
            action = "HOLD"
            if pnl_pct > 0:
                reasons.append(f"Up {pnl_pct:.0f}% - no action needed")
            elif pnl_pct > -10:
                reasons.append(f"Down {abs(pnl_pct):.0f}% - minor fluctuation")
            else:
                reasons.append(f"Down {abs(pnl_pct):.0f}% - wait for clearer signal")
                reasons.append("Not oversold enough to buy, not weak enough to sell")
            confidence = Confidence.LOW

        # === OVERRIDES ===

        # Don't recommend buying in crash if not quality
        if action in ["BUY MORE", "STRONG BUY", "ADD"] and market_regime == MarketRegime.CRASH:
            if not fundamentals.is_quality:
                action = "WAIT"
                reasons = ["Market crashing - wait for dust to settle"]
                confidence = Confidence.LOW

        # Don't recommend buying if concentration too high
        if action in ["BUY MORE", "STRONG BUY", "ADD"] and concentration > 30:
            original_action = action
            action = "HOLD"
            reasons = [f"Would be {original_action} but {sector} already at {concentration:.0f}%"]
            reasons.append("Diversify first, then consider adding")
            confidence = Confidence.MEDIUM

        return {
            "symbol": symbol,
            "action": action,
            "reasons": reasons,
            "warnings": warnings,
            "confidence": confidence.value,
            "confidence_factors": confidence_factors,
            "current_price": round(current_price, 2),
            "avg_price": round(avg_price, 2),
            "pnl_pct": round(pnl_pct, 1),
            "quantity": quantity,
            "target": round(target, 2) if target else None,
            "target_label": self._get_target_label(action, target, avg_price, technicals),
            "stop_loss": round(stop_loss, 2) if stop_loss else None,
            "rsi": round(rsi, 1),
            "fundamentals": {
                "pe": fundamentals.pe,
                "roe": fundamentals.roe,
                "debt_equity": fundamentals.debt_equity,
                "quality": fundamentals.is_quality,
                "risky": fundamentals.is_risky,
            },
            "sector": sector,
            "sector_concentration": round(concentration, 1),
        }

    def _get_target_label(self, action: str, target: float, avg_price: float, technicals: dict) -> str:
        """Get human-readable label for target price"""
        if not target:
            return None
        if action in ["STRONG BUY", "BUY MORE", "ADD"]:
            if target == avg_price:
                return "Break-even"
            elif target == technicals.get("sma_20"):
                return "Short-term target (SMA20)"
            elif target == technicals.get("sma_50"):
                return "Medium-term target (SMA50)"
            return "Upside target"
        elif action in ["HOLD"]:
            return "Resistance level"
        return None

    async def analyze_portfolio(self, holdings: list, stock_data: dict) -> dict:
        """Analyze entire portfolio and generate signals"""
        # Get market regime once
        market_regime, nifty_change = await self.get_market_regime()

        signals = []
        for h in holdings:
            if h.holding_type == "MF":
                continue

            data = stock_data.get(h.symbol)
            if not data:
                continue

            technicals = self._calculate_technicals(data)
            current_price = data.get("current_price", h.avg_price)

            signal = await self.generate_signal(
                symbol=h.symbol,
                avg_price=h.avg_price,
                quantity=h.quantity,
                current_price=current_price,
                technicals=technicals,
                holdings=holdings,
                market_regime=market_regime,
                nifty_change=nifty_change,
            )
            signals.append(signal)

        # Sort: Actionable first, then by confidence
        action_priority = {
            "STRONG BUY": 0,
            "BUY MORE": 1,
            "ADD": 2,
            "EXIT": 3,
            "PARTIAL SELL": 4,
            "TRIM": 5,
            "AVOID": 6,
            "WAIT": 7,
            "HOLD": 8,
        }
        signals.sort(key=lambda x: (action_priority.get(x["action"], 99), x["confidence"] != "HIGH"))

        # Enhance top signals with LLM insights
        signals = await self._enhance_with_llm(signals, market_regime.value, nifty_change)

        # Score news sentiment
        signals = await self._score_news_sentiment(signals)

        return {
            "signals": signals,
            "market_regime": market_regime.value,
            "nifty_change": round(nifty_change, 2),
            "summary": self._generate_summary(signals, market_regime),
        }

    async def _enhance_with_llm(self, signals: list, market_regime: str, nifty_change: float) -> list:
        """Enhance top actionable signals with LLM insights (single API call)."""
        if not settings.groq_api_key:
            return signals

        # Only enhance actionable signals (not HOLD/WAIT)
        actionable = [s for s in signals if s["action"] not in ("HOLD", "WAIT")][:5]
        if not actionable:
            return signals

        prompt_data = "\n".join(
            f"- {s['symbol']}: {s['action']} | P&L:{s['pnl_pct']:+.1f}% | RSI:{s['rsi']:.0f} | "
            f"PE:{s['fundamentals'].get('pe') or 'N/A'} | Sector:{s['sector']} | "
            f"Reasons: {'; '.join(s['reasons'])}"
            for s in actionable
        )

        try:
            from groq import Groq

            client = Groq(api_key=settings.groq_api_key)
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a concise Indian stock market analyst. "
                            "For each stock below, write ONE sentence (max 25 words) of actionable insight "
                            "that adds context beyond the technical signal. Consider market conditions, "
                            "sector trends, or risk factors. Format: SYMBOL: insight"
                        ),
                    },
                    {
                        "role": "user",
                        "content": f"Market: {market_regime} (Nifty {nifty_change:+.1f}%)\n\n{prompt_data}",
                    },
                ],
                temperature=0.3,
                max_completion_tokens=300,
            )

            # Parse LLM response into per-symbol insights
            insights = {}
            for line in resp.choices[0].message.content.strip().split("\n"):
                line = line.strip("- •*")
                if ":" in line:
                    sym, insight = line.split(":", 1)
                    sym = sym.strip().upper().replace("**", "")
                    insights[sym] = insight.strip()

            # Attach insights to signals
            for s in signals:
                if s["symbol"] in insights:
                    s["ai_insight"] = insights[s["symbol"]]

            logger.info(f"LLM enhanced {len(insights)} signals")
        except Exception as e:
            logger.warning(f"LLM enhancement failed: {e}")

        return signals

    async def _score_news_sentiment(self, signals: list) -> list:
        """Score news sentiment for top holdings using Groq."""
        if not settings.groq_api_key:
            return signals

        # Fetch news for actionable signals
        from ...tasks.portfolio_advisor import fetch_stock_news

        news_map = {}
        for s in signals[:8]:
            news = await fetch_stock_news(s["symbol"])
            if news:
                news_map[s["symbol"]] = [n["title"] for n in news]

        if not news_map:
            return signals

        news_str = "\n".join(f"{sym}: {'; '.join(titles)}" for sym, titles in news_map.items())

        try:
            from groq import Groq

            client = Groq(api_key=settings.groq_api_key)
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Score each stock's news sentiment as "
                            "bullish/neutral/bearish. "
                            "Format: SYMBOL:sentiment "
                            "(one per line, nothing else)"
                        ),
                    },
                    {"role": "user", "content": news_str},
                ],
                temperature=0.1,
                max_completion_tokens=100,
            )

            for line in resp.choices[0].message.content.strip().split("\n"):
                if ":" in line:
                    sym, sent = line.split(":", 1)
                    sym = sym.strip().upper().replace("**", "")
                    sent = sent.strip().lower()
                    for s in signals:
                        if s["symbol"] == sym:
                            s["news_sentiment"] = sent
                            s["news_headlines"] = news_map.get(sym, [])
                            break
        except Exception as e:
            logger.warning(f"News sentiment scoring failed: {e}")

        return signals

    def _calculate_technicals(self, data: dict) -> dict:
        """Calculate technical indicators from stock data"""
        closes = data.get("closes", [])
        if len(closes) < 20:
            return {}

        current = data.get("current_price", closes[-1])

        # SMAs
        sma_20 = sum(closes[-20:]) / 20
        sma_50 = sum(closes[-50:]) / 50 if len(closes) >= 50 else sma_20
        sma_200 = sum(closes[-200:]) / 200 if len(closes) >= 200 else None

        # RSI
        gains, losses = [], []
        for i in range(1, min(15, len(closes))):
            diff = closes[-i] - closes[-i - 1]
            gains.append(max(diff, 0))
            losses.append(abs(min(diff, 0)))
        avg_gain = sum(gains) / 14 if gains else 0
        avg_loss = sum(losses) / 14 if losses else 0.001
        rsi = 100 - (100 / (1 + avg_gain / avg_loss))

        # 52W range
        highs = data.get("highs", closes)
        lows = data.get("lows", closes)
        high_52w = max(highs[-252:]) if len(highs) >= 252 else max(highs)
        low_52w = min(lows[-252:]) if len(lows) >= 252 else min(lows)
        range_position = ((current - low_52w) / (high_52w - low_52w) * 100) if high_52w != low_52w else 50

        return {
            "current": current,
            "sma_20": sma_20,
            "sma_50": sma_50,
            "sma_200": sma_200,
            "rsi": rsi,
            "range_position": range_position,
            "above_sma20": current > sma_20,
            "above_sma50": current > sma_50,
            "support": min(closes[-20:]),
            "resistance": max(closes[-20:]),
        }

    def _generate_summary(self, signals: list, market_regime: MarketRegime) -> dict:
        """Generate portfolio summary"""
        actions = {}
        for s in signals:
            actions[s["action"]] = actions.get(s["action"], 0) + 1

        high_confidence = len([s for s in signals if s["confidence"] == "HIGH"])

        return {
            "total_signals": len(signals),
            "actionable": len([s for s in signals if s["action"] not in ["HOLD", "WAIT"]]),
            "high_confidence": high_confidence,
            "action_breakdown": actions,
            "market_note": {
                MarketRegime.CRASH: "Market crash - be cautious with buys",
                MarketRegime.BEAR: "Bearish market - focus on quality",
                MarketRegime.BULL: "Bullish market - ride the trend",
                MarketRegime.NEUTRAL: "Neutral market - stock-specific approach",
            }.get(market_regime, ""),
        }
