"""Data models shared across the screening pipeline."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Verdict(str, Enum):
    COMPLIANT = "COMPLIANT"
    NON_COMPLIANT = "NON-COMPLIANT"
    BORDERLINE = "BORDERLINE"
    INSUFFICIENT_DATA = "INSUFFICIENT DATA"


class RuleStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    BORDERLINE = "BORDERLINE"
    REVIEW = "REVIEW"          # data unavailable / needs manual/analyst confirmation
    NOT_APPLICABLE = "N/A"


@dataclass
class CompanyData:
    """Raw + normalized inputs pulled from the data provider for one ticker."""
    ticker: str
    long_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None

    market_cap: Optional[float] = None
    total_debt: Optional[float] = None
    cash_and_short_term_investments: Optional[float] = None
    total_revenue: Optional[float] = None
    non_operating_interest_income: Optional[float] = None

    # bookkeeping on where each number actually came from, for the "show your work" UI
    sources: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)
    fetch_error: Optional[str] = None


@dataclass
class RuleResult:
    key: str                    # machine key, e.g. "debt_to_mcap"
    label: str                  # human label, e.g. "Interest-bearing debt / Market cap"
    status: RuleStatus
    value: Optional[float]      # the computed ratio (0-1), None if unavailable
    threshold: float            # the max allowed ratio
    numerator_label: str
    numerator_value: Optional[float]
    denominator_label: str
    denominator_value: Optional[float]
    note: str = ""              # explanatory / caveat text shown under the row
    estimated: bool = False     # True => value is a transparent estimate/proxy


@dataclass
class BusinessScreenResult:
    status: RuleStatus           # PASS, FAIL, or BORDERLINE
    sector: Optional[str]
    industry: Optional[str]
    matched_category: Optional[str] = None   # e.g. "Conventional (interest-based) banking"
    note: str = ""


@dataclass
class ScreeningResult:
    ticker: str
    company_name: str
    verdict: Verdict
    business_screen: BusinessScreenResult
    rules: list  # list[RuleResult]
    company_data: CompanyData
    reasons: list = field(default_factory=list)  # short bullet reasons behind the verdict
