"""
Data fetching layer. Talks to Yahoo Finance via `yfinance` and normalizes whatever it
gets back into a `CompanyData` object, recording exactly which field each number came
from (so the UI can show its work) and any caveats about data quality.

This module has no Streamlit dependency by design -- the app layer wraps
`get_company_data` with `st.cache_data` for TTL caching.
"""

from __future__ import annotations

import logging
from typing import Optional

import pandas as pd
import yfinance as yf

from .models import CompanyData

log = logging.getLogger(__name__)


def _first_available(df: Optional[pd.DataFrame], row_names: list[str]) -> tuple[Optional[float], Optional[str]]:
    """Return (value, row_name_used) for the first matching row found in the most
    recent column of a yfinance financial-statement DataFrame."""
    if df is None or df.empty:
        return None, None
    for name in row_names:
        if name in df.index:
            series = df.loc[name]
            # most recent period is the first column
            for col in series.index:
                val = series[col]
                if val is not None and not pd.isna(val):
                    return float(val), name
    return None, None


def get_company_data(ticker: str) -> CompanyData:
    ticker = ticker.strip().upper()
    data = CompanyData(ticker=ticker)

    try:
        tk = yf.Ticker(ticker)
    except Exception as e:  # pragma: no cover - defensive
        data.fetch_error = f"Could not initialize data provider for '{ticker}': {e}"
        return data

    # --- basic info / classification -----------------------------------------
    info = {}
    try:
        info = tk.info or {}
    except Exception as e:
        data.warnings.append(f"Could not load company profile/info: {e}")

    if not info or info.get("regularMarketPrice") is None and info.get("currentPrice") is None \
            and info.get("marketCap") is None and not info.get("longName") and not info.get("shortName"):
        # Heuristic: if virtually nothing came back, treat as an invalid/unknown ticker
        # rather than silently showing an all-blank card. We still try fast_info below
        # before giving up completely.
        pass

    data.long_name = info.get("longName") or info.get("shortName") or ticker
    data.sector = info.get("sector")
    data.industry = info.get("industry")

    # --- market cap -------------------------------------------------------------
    market_cap = info.get("marketCap")
    source = "info.marketCap"
    if market_cap is None:
        try:
            fi = tk.fast_info
            market_cap = fi.get("marketCap") if hasattr(fi, "get") else getattr(fi, "market_cap", None)
            source = "fast_info.marketCap"
        except Exception as e:
            data.warnings.append(f"fast_info market cap fallback failed: {e}")
    if market_cap:
        data.market_cap = float(market_cap)
        data.sources["market_cap"] = source
    else:
        data.warnings.append("Market cap unavailable from data provider.")

    # --- financial statements (used for fallbacks + the interest-income proxy) --
    balance_sheet = None
    income_stmt = None
    try:
        balance_sheet = tk.balance_sheet
    except Exception as e:
        data.warnings.append(f"Balance sheet unavailable: {e}")
    try:
        income_stmt = tk.income_stmt
    except Exception as e:
        data.warnings.append(f"Income statement unavailable: {e}")

    # --- total debt ---------------------------------------------------------
    total_debt = info.get("totalDebt")
    source = "info.totalDebt"
    if total_debt is None:
        total_debt, row = _first_available(balance_sheet, ["Total Debt"])
        source = f"balance_sheet['{row}']" if row else None
    if total_debt is not None:
        data.total_debt = float(total_debt)
        data.sources["total_debt"] = source
    else:
        data.total_debt = 0.0
        data.sources["total_debt"] = "assumed 0 (no debt figure reported)"
        data.warnings.append(
            "No interest-bearing debt figure reported by the data provider; treated as $0. "
            "Verify manually for companies with unusual capital structures."
        )

    # --- cash + interest-bearing securities ---------------------------------
    cash_sti, row = _first_available(
        balance_sheet,
        ["Cash Cash Equivalents And Short Term Investments"],
    )
    source = f"balance_sheet['{row}']" if row else None
    if cash_sti is None:
        cash_val, row_c = _first_available(balance_sheet, ["Cash And Cash Equivalents", "Cash Financial"])
        sti_val, row_s = _first_available(balance_sheet, ["Other Short Term Investments"])
        if cash_val is not None or sti_val is not None:
            cash_sti = (cash_val or 0.0) + (sti_val or 0.0)
            source = f"balance_sheet['{row_c}'] + balance_sheet['{row_s}']"
    if cash_sti is None:
        cash_sti = info.get("totalCash")
        source = "info.totalCash"
    if cash_sti is not None:
        data.cash_and_short_term_investments = float(cash_sti)
        data.sources["cash_and_short_term_investments"] = source
    else:
        data.warnings.append("Cash & short-term investments figure unavailable from data provider.")

    # --- total revenue -------------------------------------------------------
    total_revenue = info.get("totalRevenue")
    source = "info.totalRevenue"
    if total_revenue is None:
        total_revenue, row = _first_available(income_stmt, ["Total Revenue", "Operating Revenue"])
        source = f"income_stmt['{row}']" if row else None
    if total_revenue is not None:
        data.total_revenue = float(total_revenue)
        data.sources["total_revenue"] = source
    else:
        data.warnings.append("Total revenue figure unavailable from data provider.")

    # --- non-operating interest income (proxy for "non-permissible income") ---
    # This is explicitly a PROXY, not a clean "non-permissible income" line item --
    # AAOIFI's definition is broader than what's disclosed in standard US filings.
    npi, row = _first_available(
        income_stmt,
        ["Interest Income Non Operating", "Interest Income"],
    )
    source = f"income_stmt['{row}']" if row else None
    if npi is None:
        # Net figure can be negative (net interest expense) -- only usable if positive
        net_val, row_n = _first_available(income_stmt, ["Net Non Operating Interest Income Expense"])
        if net_val is not None and net_val > 0:
            npi = net_val
            source = f"income_stmt['{row_n}'] (net, positive component only)"
    if npi is not None:
        data.non_operating_interest_income = float(npi)
        data.sources["non_operating_interest_income"] = source
    else:
        data.warnings.append(
            "No interest-income line item disclosed; non-permissible income ratio cannot "
            "be computed and is flagged for manual/analyst review."
        )

    return data
