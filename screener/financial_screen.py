"""Stage 2: AAOIFI financial-ratio screen, plus overall verdict combination."""

from __future__ import annotations

from typing import Optional

from .constants import ThresholdConfig
from .models import CompanyData, RuleResult, RuleStatus, Verdict, BusinessScreenResult, ScreeningResult


def _classify(ratio: Optional[float], threshold: float, band: float) -> RuleStatus:
    """PASS / BORDERLINE / FAIL based on how close `ratio` is to `threshold`.

    proximity = ratio / threshold
      < (1 - band)              -> PASS
      [1 - band, 1 + band]      -> BORDERLINE (near the line, whichever side)
      > (1 + band)              -> FAIL
    """
    if ratio is None:
        return RuleStatus.REVIEW
    if threshold <= 0:
        return RuleStatus.REVIEW
    proximity = ratio / threshold
    if proximity < (1 - band):
        return RuleStatus.PASS
    if proximity > (1 + band):
        return RuleStatus.FAIL
    return RuleStatus.BORDERLINE


def compute_debt_rule(company: CompanyData, cfg: ThresholdConfig) -> RuleResult:
    mcap = company.market_cap
    debt = company.total_debt
    ratio = (debt / mcap) if (mcap and mcap > 0 and debt is not None) else None
    status = _classify(ratio, cfg.debt_to_mcap_max, cfg.borderline_band)
    return RuleResult(
        key="debt_to_mcap",
        label="Interest-bearing debt / Market cap",
        status=status,
        value=ratio,
        threshold=cfg.debt_to_mcap_max,
        numerator_label="Total debt",
        numerator_value=debt,
        denominator_label="Market capitalization",
        denominator_value=mcap,
        note="Source: " + company.sources.get("total_debt", "n/a") + " / " + company.sources.get("market_cap", "n/a"),
    )


def compute_cash_rule(company: CompanyData, cfg: ThresholdConfig) -> RuleResult:
    mcap = company.market_cap
    cash = company.cash_and_short_term_investments
    ratio = (cash / mcap) if (mcap and mcap > 0 and cash is not None) else None
    status = _classify(ratio, cfg.cash_sec_to_mcap_max, cfg.borderline_band)
    return RuleResult(
        key="cash_to_mcap",
        label="(Cash + interest-bearing securities) / Market cap",
        status=status,
        value=ratio,
        threshold=cfg.cash_sec_to_mcap_max,
        numerator_label="Cash & short-term investments",
        numerator_value=cash,
        denominator_label="Market capitalization",
        denominator_value=mcap,
        note="Source: " + company.sources.get("cash_and_short_term_investments", "n/a") + " / " + company.sources.get("market_cap", "n/a"),
    )


def compute_income_rule(company: CompanyData, cfg: ThresholdConfig) -> RuleResult:
    revenue = company.total_revenue
    npi = company.non_operating_interest_income
    ratio = (npi / revenue) if (revenue and revenue > 0 and npi is not None) else None
    status = _classify(ratio, cfg.npi_to_revenue_max, cfg.borderline_band)
    if npi is None:
        status = RuleStatus.REVIEW
    return RuleResult(
        key="npi_to_revenue",
        label="Non-permissible (interest) income / Total revenue",
        status=status,
        value=ratio,
        threshold=cfg.npi_to_revenue_max,
        numerator_label="Non-operating interest income (proxy)",
        numerator_value=npi,
        denominator_label="Total revenue",
        denominator_value=revenue,
        estimated=True,
        note=(
            "ESTIMATED: uses disclosed non-operating/interest income as a transparent proxy "
            "for AAOIFI's broader 'non-permissible income' definition, which is not cleanly "
            "reported in standard US filings. Treat as a starting point, not a final answer -- "
            "confirm with a manual review of the 10-K notes for interest and other "
            "non-Shari'ah-compliant income sources. Source: " + (company.sources.get("non_operating_interest_income") or "unavailable")
        ),
    )


def build_screening_result(company: CompanyData, business: BusinessScreenResult, cfg: ThresholdConfig) -> ScreeningResult:
    rules = [
        compute_debt_rule(company, cfg),
        compute_cash_rule(company, cfg),
        compute_income_rule(company, cfg),
    ]

    reasons = []

    # No usable market cap at all -> can't screen.
    if not company.market_cap:
        return ScreeningResult(
            ticker=company.ticker,
            company_name=company.long_name or company.ticker,
            verdict=Verdict.INSUFFICIENT_DATA,
            business_screen=business,
            rules=rules,
            company_data=company,
            reasons=["Market capitalization unavailable -- cannot compute AAOIFI ratios."],
        )

    if business.status == RuleStatus.FAIL:
        verdict = Verdict.NON_COMPLIANT
        reasons.append(f"Business activity: {business.matched_category} (excluded category).")
    else:
        fail_rules = [r for r in rules if r.status == RuleStatus.FAIL]
        borderline_rules = [r for r in rules if r.status in (RuleStatus.BORDERLINE, RuleStatus.REVIEW)]
        business_borderline = business.status in (RuleStatus.BORDERLINE, RuleStatus.REVIEW)

        if fail_rules:
            verdict = Verdict.NON_COMPLIANT
            for r in fail_rules:
                reasons.append(f"{r.label} exceeds the {r.threshold:.0%} threshold.")
        elif borderline_rules or business_borderline:
            verdict = Verdict.BORDERLINE
            for r in borderline_rules:
                if r.status == RuleStatus.REVIEW:
                    reasons.append(f"{r.label}: data unavailable / needs manual confirmation.")
                else:
                    reasons.append(f"{r.label} is close to the {r.threshold:.0%} threshold.")
            if business_borderline:
                reasons.append(business.note)
        else:
            verdict = Verdict.COMPLIANT
            reasons.append("Passes the business-activity screen and all AAOIFI financial ratio thresholds.")

    return ScreeningResult(
        ticker=company.ticker,
        company_name=company.long_name or company.ticker,
        verdict=verdict,
        business_screen=business,
        rules=rules,
        company_data=company,
        reasons=reasons,
    )
