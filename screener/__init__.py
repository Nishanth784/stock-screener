"""Shari'ah-compliant stock screener package.

Public entrypoint: `screen_ticker(ticker, cfg=None) -> ScreeningResult`
"""

from .constants import ThresholdConfig
from .data_provider import get_company_data
from .business_screen import screen_business_activity
from .financial_screen import build_screening_result
from .models import ScreeningResult


def screen_ticker(ticker: str, cfg: ThresholdConfig | None = None) -> ScreeningResult:
    cfg = cfg or ThresholdConfig()
    company = get_company_data(ticker)
    business = screen_business_activity(company)
    return build_screening_result(company, business, cfg)


__all__ = ["screen_ticker", "ThresholdConfig", "ScreeningResult"]
