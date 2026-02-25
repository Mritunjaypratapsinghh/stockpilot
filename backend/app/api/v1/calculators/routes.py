"""Financial Calculators routes - Asset Allocation, SIP Step-up, Portfolio Score, Retirement, SWP, Loan, Tax."""

from fastapi import APIRouter

from ....core.response_handler import StandardResponse

router = APIRouter()


@router.get("/asset-allocation", summary="Asset Allocation Calculator")
async def asset_allocation(
    age: int = 30,
    risk_appetite: str = "moderate",
    horizon: int = 10,
) -> StandardResponse:
    """Calculate recommended asset allocation based on age, risk, and horizon."""
    base_equity = 100 - age
    risk_adj = {"very_low": -20, "low": -10, "moderate": 0, "high": 10, "very_high": 20}
    equity = max(10, min(90, base_equity + risk_adj.get(risk_appetite, 0)))

    if horizon >= 15:
        equity = min(90, equity + 10)
    elif horizon <= 5:
        equity = max(10, equity - 10)

    debt = 100 - equity - 5
    gold = 5

    return StandardResponse.ok(
        {
            "recommended": {
                "equity": equity,
                "debt": debt,
                "gold": gold,
                "breakdown": {
                    "large_cap": round(equity * 0.5),
                    "mid_cap": round(equity * 0.3),
                    "small_cap": round(equity * 0.2),
                    "debt_fund": debt,
                    "gold": gold,
                },
            },
            "inputs": {"age": age, "risk_appetite": risk_appetite, "horizon": horizon},
        }
    )


@router.get("/sip-stepup", summary="SIP Step-up Calculator")
async def sip_stepup(
    monthly_amount: float = 10000,
    expected_return: float = 12,
    years: int = 10,
    annual_stepup: float = 10,
) -> StandardResponse:
    """Compare flat SIP vs step-up SIP projections."""
    r = expected_return / 100 / 12
    n = years * 12

    flat_invested = monthly_amount * n
    flat_corpus = monthly_amount * (((1 + r) ** n - 1) / r) * (1 + r)

    stepup_invested = 0
    stepup_corpus = 0
    current_sip = monthly_amount
    yearly_breakdown = []

    for year in range(1, years + 1):
        year_invested = current_sip * 12
        stepup_invested += year_invested
        months_remaining = (years - year + 1) * 12
        for month in range(12):
            stepup_corpus += current_sip * ((1 + r) ** (months_remaining - month))
        yearly_breakdown.append(
            {
                "year": year,
                "monthly_sip": round(current_sip),
                "year_invested": round(year_invested),
                "cumulative_invested": round(stepup_invested),
            }
        )
        current_sip *= 1 + (annual_stepup / 100)

    return StandardResponse.ok(
        {
            "flat": {
                "total_invested": round(flat_invested),
                "corpus": round(flat_corpus),
                "wealth_gained": round(flat_corpus - flat_invested),
            },
            "stepup": {
                "total_invested": round(stepup_invested),
                "corpus": round(stepup_corpus),
                "wealth_gained": round(stepup_corpus - stepup_invested),
                "last_monthly_sip": round(current_sip / (1 + annual_stepup / 100)),
            },
            "yearly_breakdown": yearly_breakdown,
            "inputs": {
                "monthly_amount": monthly_amount,
                "expected_return": expected_return,
                "years": years,
                "annual_stepup": annual_stepup,
            },
        }
    )


@router.get("/portfolio-score", summary="Portfolio Health Score")
async def portfolio_score(answers: str = "2,2,2,2,2,2") -> StandardResponse:
    """Calculate portfolio health score based on 6 questions (0-3 each)."""
    try:
        scores = [max(0, min(3, int(x.strip()))) for x in answers.split(",") if x.strip()][:6]
        scores = scores + [2] * (6 - len(scores))
    except (ValueError, AttributeError):
        scores = [2] * 6

    questions = [
        "Equity vs Debt awareness",
        "Diversification level",
        "Emergency fund status",
        "Investment regularity",
        "Goal alignment",
        "Review frequency",
    ]

    total = sum(scores)
    score_10 = round((total / 18) * 10, 1)

    if score_10 >= 8:
        personality, desc = "Strategic Investor", "Excellent portfolio awareness and discipline."
    elif score_10 >= 6:
        personality, desc = "Growing Investor", "Good foundation, some areas need attention."
    elif score_10 >= 4:
        personality, desc = "Casual Investor", "Consider building more structure in your approach."
    else:
        personality, desc = "Beginner Investor", "Start with basics - emergency fund and regular investing."

    return StandardResponse.ok(
        {
            "score": score_10,
            "max_score": 10,
            "personality": personality,
            "description": desc,
            "breakdown": [{"question": q, "score": s, "max": 3} for q, s in zip(questions, scores, strict=True)],
        }
    )


@router.get("/retirement", summary="Retirement Planner")
async def retirement_planner(
    current_age: int = 30,
    retirement_age: int = 60,
    monthly_expenses: float = 50000,
    current_savings: float = 1000000,
    inflation: float = 6,
    expected_return: float = 10,
) -> StandardResponse:
    """Calculate retirement corpus needed and SIP required."""
    years_to_retire = retirement_age - current_age
    future_monthly = monthly_expenses * ((1 + inflation / 100) ** years_to_retire)
    corpus_needed = future_monthly * 12 * 25
    projected_savings = current_savings * ((1 + expected_return / 100) ** years_to_retire)
    shortfall = max(0, corpus_needed - projected_savings)

    if shortfall > 0 and years_to_retire > 0:
        r = expected_return / 100 / 12
        n = years_to_retire * 12
        sip_needed = shortfall / ((((1 + r) ** n - 1) / r) * (1 + r))
    else:
        sip_needed = 0

    return StandardResponse.ok(
        {
            "corpus_needed": round(corpus_needed),
            "projected_savings": round(projected_savings),
            "shortfall": round(shortfall),
            "sip_needed": round(sip_needed),
            "achievement_pct": min(100, round((projected_savings / corpus_needed) * 100)) if corpus_needed else 100,
            "future_monthly_expenses": round(future_monthly),
            "inputs": {
                "current_age": current_age,
                "retirement_age": retirement_age,
                "monthly_expenses": monthly_expenses,
                "current_savings": current_savings,
                "inflation": inflation,
                "expected_return": expected_return,
            },
        }
    )


@router.get("/swp", summary="SWP Calculator")
async def swp_calculator(
    corpus: float = 5000000,
    monthly_withdrawal: float = 30000,
    annual_stepup: float = 0,
    expected_return: float = 10,
    years: int = 20,
) -> StandardResponse:
    """Calculate SWP sustainability and corpus trajectory."""
    r = expected_return / 100 / 12
    balance = corpus
    withdrawal = monthly_withdrawal
    trajectory = []
    total_withdrawn = 0

    for year in range(1, years + 1):
        year_start = balance
        year_withdrawn = 0
        for _ in range(12):
            if balance <= 0:
                break
            balance = balance * (1 + r) - withdrawal
            year_withdrawn += withdrawal
            total_withdrawn += withdrawal
        trajectory.append(
            {
                "year": year,
                "start_balance": round(year_start),
                "end_balance": round(max(0, balance)),
                "withdrawn": round(year_withdrawn),
            }
        )
        if balance <= 0:
            break
        withdrawal *= 1 + (annual_stepup / 100)

    return StandardResponse.ok(
        {
            "sustainable": balance > 0,
            "safe_years": len([t for t in trajectory if t["end_balance"] > 0]),
            "final_balance": round(max(0, balance)),
            "total_withdrawn": round(total_withdrawn),
            "trajectory": trajectory,
            "inputs": {
                "corpus": corpus,
                "monthly_withdrawal": monthly_withdrawal,
                "annual_stepup": annual_stepup,
                "expected_return": expected_return,
                "years": years,
            },
        }
    )


@router.get("/loan-analyzer", summary="Smart Loan Analyzer")
async def loan_analyzer(
    principal: float = 5000000,
    interest_rate: float = 8.5,
    tenure_years: int = 25,
    stepup_pct: float = 7.5,
    extra_emis: int = 1,
) -> StandardResponse:
    """Analyze loan repayment strategies."""
    r = interest_rate / 100 / 12
    n = tenure_years * 12
    emi = principal * r * ((1 + r) ** n) / (((1 + r) ** n) - 1)

    def calc_strategy(use_extra: bool, use_stepup: bool):
        balance, months, total_paid = principal, 0, 0
        current_emi = emi
        while balance > 0 and months < n * 2:
            months += 1
            balance = balance * (1 + r) - current_emi
            total_paid += current_emi
            if months % 12 == 0:
                if use_extra and extra_emis > 0:
                    extra = min(current_emi * extra_emis, max(0, balance))
                    balance -= extra
                    total_paid += extra
                if use_stepup:
                    current_emi *= 1 + (stepup_pct / 100)
        return months, total_paid

    standard_total = emi * n
    extra_m, extra_t = calc_strategy(True, False)
    stepup_m, stepup_t = calc_strategy(False, True)
    combo_m, combo_t = calc_strategy(True, True)

    def fmt(m):
        return f"{m // 12}y {m % 12}m"

    return StandardResponse.ok(
        {
            "standard_emi": round(emi),
            "strategies": {
                "standard": {
                    "tenure": fmt(n),
                    "total_paid": round(standard_total),
                    "interest_paid": round(standard_total - principal),
                },
                "extra_emi": {
                    "tenure": fmt(extra_m),
                    "tenure_saved": fmt(n - extra_m),
                    "interest_saved": round(standard_total - extra_t),
                },
                "stepup": {
                    "tenure": fmt(stepup_m),
                    "tenure_saved": fmt(n - stepup_m),
                    "interest_saved": round(standard_total - stepup_t),
                },
                "combo": {
                    "tenure": fmt(combo_m),
                    "tenure_saved": fmt(n - combo_m),
                    "interest_saved": round(standard_total - combo_t),
                },
            },
            "inputs": {
                "principal": principal,
                "interest_rate": interest_rate,
                "tenure_years": tenure_years,
                "stepup_pct": stepup_pct,
                "extra_emis": extra_emis,
            },
        }
    )


@router.get("/salary-tax", summary="Salary & Tax Calculator")
async def salary_tax(
    annual_ctc: float = 1200000,
    pf_type: str = "capped",
    regime: str = "new",
    vpf: float = 0,
) -> StandardResponse:
    """Calculate in-hand salary and tax."""
    basic = annual_ctc * 0.4
    hra = annual_ctc * 0.2
    special = annual_ctc * 0.4
    gratuity = basic * 0.0481
    pf_base = min(basic, 180000) if pf_type == "capped" else basic
    employer_pf = pf_base * 0.12
    employee_pf = pf_base * 0.12 + vpf * 12
    gross = annual_ctc - gratuity - employer_pf
    prof_tax = 2400

    if regime == "new":
        taxable = gross - 75000
        tax = 0
        slabs = [(400000, 0), (400000, 0.05), (400000, 0.10), (400000, 0.15), (400000, 0.20), (float("inf"), 0.30)]
        remaining = taxable
        for limit, rate in slabs:
            if remaining <= 0:
                break
            taxable_in_slab = min(remaining, limit)
            tax += taxable_in_slab * rate
            remaining -= limit
        if taxable <= 1275000:
            tax = 0
    else:
        taxable = gross - 50000 - min(employee_pf, 150000) - hra * 0.4
        tax = 0
        if taxable > 250000:
            tax += min(taxable - 250000, 250000) * 0.05
        if taxable > 500000:
            tax += min(taxable - 500000, 500000) * 0.20
        if taxable > 1000000:
            tax += (taxable - 1000000) * 0.30
        if taxable <= 500000:
            tax = 0

    total_tax = tax * 1.04
    annual_inhand = gross - employee_pf - prof_tax - total_tax

    return StandardResponse.ok(
        {
            "monthly_inhand": round(annual_inhand / 12),
            "annual_inhand": round(annual_inhand),
            "annual_tax": round(total_tax),
            "effective_tax_rate": round((total_tax / gross) * 100, 1) if gross else 0,
            "breakdown": {
                "annual_ctc": round(annual_ctc),
                "gratuity": round(gratuity),
                "employer_pf": round(employer_pf),
                "gross_salary": round(gross),
                "basic": round(basic),
                "hra": round(hra),
                "special_allowance": round(special),
                "employee_pf": round(employee_pf),
                "professional_tax": prof_tax,
                "income_tax": round(total_tax),
            },
            "inputs": {"annual_ctc": annual_ctc, "pf_type": pf_type, "regime": regime, "vpf": vpf},
        }
    )


@router.get("/cashflow", summary="Cashflow Planner")
async def cashflow_planner(inflows: str = "80000,20000", outflows: str = "25000,15000,5000") -> StandardResponse:
    """Calculate net surplus and savings rate."""
    try:
        inflow_list = [float(x.strip()) for x in inflows.split(",") if x.strip()]
        outflow_list = [float(x.strip()) for x in outflows.split(",") if x.strip()]
    except (ValueError, AttributeError):
        inflow_list, outflow_list = [80000], [25000]
    total_income = sum(inflow_list)
    total_expenses = sum(outflow_list)
    net_surplus = total_income - total_expenses

    return StandardResponse.ok(
        {
            "total_income": round(total_income),
            "total_expenses": round(total_expenses),
            "net_surplus": round(net_surplus),
            "savings_rate": round((net_surplus / total_income * 100), 1) if total_income else 0,
            "target_savings_rate": 20,
            "inflows": [round(x) for x in inflow_list],
            "outflows": [round(x) for x in outflow_list],
        }
    )
