"""
Configurable constants for the Shari'ah-compliant stock screener.

Methodology: AAOIFI Shari'ah Standard No. 21 ("Financial Paper (Shares and Bonds)"),
as commonly operationalized by Islamic index providers (e.g. Dow Jones Islamic Market
Index, MSCI Islamic, S&P Shariah) and Islamic banks/screening services.

IMPORTANT: There is no single universally-binding numeric standard body for retail
screening. AAOIFI's 30% / 30% / 5% (market-cap-denominated) thresholds are the most
widely cited and are what this tool implements. Other providers (e.g. some versions of
the Dow Jones Islamic Market methodology) use total-assets as the denominator instead of
market cap, and some use 33% instead of 30%. This app is explicit about which standard it
follows so results are reproducible and auditable.
"""

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Standard identification (shown in the UI so the methodology is never a black box)
# ---------------------------------------------------------------------------
STANDARD_NAME = "AAOIFI Shari'ah Standard No. 21"
STANDARD_DESCRIPTION = (
    "Accounting and Auditing Organization for Islamic Financial Institutions (AAOIFI), "
    "Shari'ah Standard No. 21: Financial Paper (Shares and Bonds). Thresholds below reflect "
    "the market-cap-denominated variant of the AAOIFI ratios most commonly used by Islamic "
    "index and screening providers."
)

# ---------------------------------------------------------------------------
# Stage 2: Financial ratio thresholds (all denominated by market capitalization)
# Configurable -- change these to model a different provider's methodology.
# ---------------------------------------------------------------------------
DEBT_TO_MARKETCAP_MAX = 0.30              # Interest-bearing debt / market cap < 30%
CASH_SECURITIES_TO_MARKETCAP_MAX = 0.30   # (Cash + interest-bearing securities) / market cap < 30%
NON_PERMISSIBLE_INCOME_MAX = 0.05         # Non-permissible (interest/other impermissible) income / revenue < 5%

# Borderline band: how close (as a fraction of the threshold) a ratio must be to the
# cut-off before we flag it as BORDERLINE instead of a clean PASS/FAIL.
# e.g. 0.15 means: within +/-15% of the threshold value counts as borderline.
BORDERLINE_BAND = 0.15

# ---------------------------------------------------------------------------
# Stage 1: Business-activity screen
# ---------------------------------------------------------------------------
# Industry keyword matches (case-insensitive substring match against yfinance's
# `industry` field). Each entry maps a keyword to the excluded category name shown
# in the UI. This is the primary signal -- sector alone is too coarse (e.g.
# "Financial Services" contains both conventional banks AND asset managers/exchanges).
NON_COMPLIANT_INDUSTRY_KEYWORDS = {
    "bank": "Conventional (interest-based) banking",
    "insurance": "Conventional insurance",
    "credit services": "Conventional consumer lending / credit",
    "mortgage": "Conventional mortgage lending",
    "brewer": "Alcohol production",
    "wineries": "Alcohol production",
    "distiller": "Alcohol production",
    "tobacco": "Tobacco",
    "gambling": "Gambling",
    "resorts & casinos": "Gambling",
    "casino": "Gambling",
    "aerospace & defense": "Weapons / defense manufacturing",
}

# Sub-industries that legitimately sit inside a "Financial Services" sector but are
# NOT automatically excluded (documented for transparency; not currently used to
# override a keyword hit).
FINANCIAL_SERVICES_ALLOWED_INDUSTRIES = {
    "asset management",
    "capital markets",
    "financial data & stock exchanges",
}

# Curated ticker-level overrides. Data-provider sector/industry classification is
# sometimes too coarse, or a company is a well-known edge case. Entries here take
# precedence over the sector/industry keyword match.
# status: "exclude" | "borderline"
TICKER_OVERRIDES = {
    # Conventional banks / diversified financials
    "JPM": ("exclude", "Conventional (interest-based) banking"),
    "BAC": ("exclude", "Conventional (interest-based) banking"),
    "WFC": ("exclude", "Conventional (interest-based) banking"),
    "C": ("exclude", "Conventional (interest-based) banking"),
    "GS": ("exclude", "Conventional (interest-based) banking"),
    "MS": ("exclude", "Conventional (interest-based) banking"),
    "USB": ("exclude", "Conventional (interest-based) banking"),
    "PNC": ("exclude", "Conventional (interest-based) banking"),
    # Insurance
    "AIG": ("exclude", "Conventional insurance"),
    "MET": ("exclude", "Conventional insurance"),
    "PRU": ("exclude", "Conventional insurance"),
    "ALL": ("exclude", "Conventional insurance"),
    "TRV": ("exclude", "Conventional insurance"),
    "PGR": ("exclude", "Conventional insurance"),
    # Alcohol
    "BUD": ("exclude", "Alcohol production"),
    "STZ": ("exclude", "Alcohol production"),
    "TAP": ("exclude", "Alcohol production"),
    "DEO": ("exclude", "Alcohol production"),
    # Tobacco
    "MO": ("exclude", "Tobacco"),
    "PM": ("exclude", "Tobacco"),
    "BTI": ("exclude", "Tobacco"),
    # Gambling
    "LVS": ("exclude", "Gambling"),
    "WYNN": ("exclude", "Gambling"),
    "MGM": ("exclude", "Gambling"),
    "DKNG": ("exclude", "Gambling"),
    "CZR": ("exclude", "Gambling"),
    # Defense / weapons
    "LMT": ("exclude", "Weapons / defense manufacturing"),
    "RTX": ("exclude", "Weapons / defense manufacturing"),
    "NOC": ("exclude", "Weapons / defense manufacturing"),
    "GD": ("exclude", "Weapons / defense manufacturing"),
    # Mixed-activity edge cases: meaningful revenue from pork/meat processing alongside
    # other products -- flagged borderline rather than a hard exclude, since public
    # data doesn't cleanly break out the pork-specific revenue share.
    "TSN": ("borderline", "Meat processing includes pork products (revenue mix not "
            "publicly broken out) -- analyst review recommended"),
    "HRL": ("borderline", "Meat processing includes pork products (revenue mix not "
            "publicly broken out) -- analyst review recommended"),
}

DISCLAIMER = (
    "This tool is an independent educational and portfolio project. It is NOT investment "
    "advice, NOT a fatwa, and NOT affiliated with, endorsed by, or representative of any "
    "brokerage, bank, or Shari'ah board. Screening results are informational only, may "
    "contain data errors or lag reported financials, and should not be relied upon for "
    "actual investment or religious-compliance decisions. Always verify against a "
    "qualified Shari'ah board or a licensed Islamic screening provider before investing."
)


@dataclass(frozen=True)
class ThresholdConfig:
    debt_to_mcap_max: float = DEBT_TO_MARKETCAP_MAX
    cash_sec_to_mcap_max: float = CASH_SECURITIES_TO_MARKETCAP_MAX
    npi_to_revenue_max: float = NON_PERMISSIBLE_INCOME_MAX
    borderline_band: float = BORDERLINE_BAND
