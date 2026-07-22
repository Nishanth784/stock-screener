"""Stage 1: business-activity screen.

Excludes companies whose core business is a non-permissible activity: conventional
(interest-based) banking & insurance, alcohol, tobacco, pork, gambling, adult
entertainment, and weapons/defense. Uses a curated ticker override list first (most
reliable), then falls back to keyword matching against the data provider's
sector/industry classification.
"""

from __future__ import annotations

from .constants import NON_COMPLIANT_INDUSTRY_KEYWORDS, TICKER_OVERRIDES
from .models import BusinessScreenResult, CompanyData, RuleStatus


def screen_business_activity(company: CompanyData) -> BusinessScreenResult:
    ticker = company.ticker.upper()

    # 1) Curated ticker-level override -- highest precedence.
    if ticker in TICKER_OVERRIDES:
        status_str, note = TICKER_OVERRIDES[ticker]
        status = RuleStatus.FAIL if status_str == "exclude" else RuleStatus.BORDERLINE
        return BusinessScreenResult(
            status=status,
            sector=company.sector,
            industry=company.industry,
            matched_category=note,
            note=(
                f"Curated override: {note}."
                if status == RuleStatus.FAIL
                else f"Flagged for manual review: {note}."
            ),
        )

    # 2) Keyword match against the industry classification string.
    industry = (company.industry or "").lower()
    if industry:
        for keyword, category in NON_COMPLIANT_INDUSTRY_KEYWORDS.items():
            if keyword in industry:
                return BusinessScreenResult(
                    status=RuleStatus.FAIL,
                    sector=company.sector,
                    industry=company.industry,
                    matched_category=category,
                    note=(
                        f"Industry classification '{company.industry}' matches excluded "
                        f"category: {category}."
                    ),
                )

    # 3) No match on either signal -> pass, but be transparent if we had no
    #    classification data at all to check.
    if not industry:
        return BusinessScreenResult(
            status=RuleStatus.REVIEW,
            sector=company.sector,
            industry=company.industry,
            matched_category=None,
            note="No sector/industry classification returned by the data provider; "
                 "business-activity screen could not be automatically verified.",
        )

    return BusinessScreenResult(
        status=RuleStatus.PASS,
        sector=company.sector,
        industry=company.industry,
        matched_category=None,
        note=f"Industry classification '{company.industry}' does not match any excluded "
             f"business-activity category.",
    )
