"""
Shari'ah-Compliant Stock Screener -- a transparent, explainable Shari'ah-compliance screener for
US-listed equities, implemented against AAOIFI Shari'ah Standard No. 21.

Every verdict is fully traceable: the app shows the exact numbers, sources, and
thresholds behind each rule. Nothing is a black box.
"""

from __future__ import annotations

import streamlit as st

from screener import screen_ticker, ThresholdConfig
from screener.constants import (
    STANDARD_NAME,
    STANDARD_DESCRIPTION,
    DISCLAIMER,
    DEBT_TO_MARKETCAP_MAX,
    CASH_SECURITIES_TO_MARKETCAP_MAX,
    NON_PERMISSIBLE_INCOME_MAX,
    BORDERLINE_BAND,
)
from screener.models import Verdict, RuleStatus

# ---------------------------------------------------------------------------
# Page config + styling
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Shari'ah-Compliant Stock Screener",
    page_icon="☪",
    layout="centered",
    initial_sidebar_state="collapsed",
)

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"]  { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }

.block-container { padding-top: 2rem; padding-bottom: 3rem; max-width: 720px; }

/* Hide default streamlit chrome for a cleaner app feel */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.app-title { font-size: 1.7rem; font-weight: 800; letter-spacing: -0.02em; margin-bottom: 0.1rem; }
.app-subtitle { color: #9aa7b2; font-size: 0.95rem; margin-bottom: 1.4rem; }

.ticker-chip {
    display: inline-block; background: #141a21; border: 1px solid #232b34;
    color: #cfd8e0; padding: 3px 11px; border-radius: 999px; font-size: 0.78rem;
    margin: 2px 4px 2px 0;
}

/* Clickable ticker chips (rendered as real st.button widgets so they're
   actually interactive, not just decorative spans). Scoped to stButton so
   the Screen form-submit button (a different widget type) is unaffected. */
div[data-testid="stButton"] > button {
    background: #141a21 !important;
    border: 1px solid #232b34 !important;
    color: #cfd8e0 !important;
    border-radius: 999px !important;
    padding: 2px 10px !important;
    font-size: 0.78rem !important;
    min-height: 1.9rem !important;
    line-height: 1.4 !important;
}
div[data-testid="stButton"] > button:hover {
    border-color: #22c55e !important;
    color: #4ade80 !important;
    background: #141a21 !important;
}
div[data-testid="stButton"] > button:focus:not(:active) {
    border-color: #22c55e !important;
    color: #4ade80 !important;
}
div[data-testid="stHorizontalBlock"] { gap: 0.35rem !important; }

/* Verdict card */
.verdict-card {
    border-radius: 20px; padding: 1.4rem 1.5rem; margin: 1rem 0 1.2rem 0;
    border: 1px solid #232b34;
}
.verdict-compliant { background: linear-gradient(135deg, rgba(34,197,94,0.16), rgba(34,197,94,0.03)); }
.verdict-noncompliant { background: linear-gradient(135deg, rgba(239,68,68,0.18), rgba(239,68,68,0.03)); }
.verdict-borderline { background: linear-gradient(135deg, rgba(245,158,11,0.18), rgba(245,158,11,0.03)); }
.verdict-insufficient { background: linear-gradient(135deg, rgba(148,163,184,0.16), rgba(148,163,184,0.03)); }

.verdict-badge {
    display: inline-block; padding: 5px 16px; border-radius: 999px;
    font-weight: 800; font-size: 0.85rem; letter-spacing: 0.04em; text-transform: uppercase;
}
.badge-compliant { background: #16a34a; color: #052e14; }
.badge-noncompliant { background: #ef4444; color: #3a0a0a; }
.badge-borderline { background: #f59e0b; color: #3a2504; }
.badge-insufficient { background: #64748b; color: #0b1220; }

.company-name { font-size: 1.35rem; font-weight: 700; margin-top: 0.6rem; }
.company-sub { color: #9aa7b2; font-size: 0.88rem; margin-bottom: 0.3rem; }

.reasons { margin-top: 0.7rem; font-size: 0.92rem; color: #d6dde3; }
.reasons li { margin-bottom: 3px; }

/* Rule rows */
.rule-card {
    border: 1px solid #232b34; border-radius: 16px; padding: 1rem 1.1rem;
    margin-bottom: 0.7rem; background: #10151b;
}
.rule-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem; }
.rule-label { font-weight: 600; font-size: 0.96rem; }
.rule-status { font-weight: 700; font-size: 0.78rem; padding: 2px 10px; border-radius: 999px; }
.status-pass { background: rgba(34,197,94,0.18); color: #4ade80; }
.status-fail { background: rgba(239,68,68,0.18); color: #f87171; }
.status-borderline { background: rgba(245,158,11,0.18); color: #fbbf24; }
.status-review { background: rgba(148,163,184,0.18); color: #cbd5e1; }

.rule-meta { color: #9aa7b2; font-size: 0.82rem; margin-bottom: 0.5rem; }
.rule-note { color: #8b98a5; font-size: 0.78rem; margin-top: 0.45rem; line-height: 1.4; }

.gauge-track {
    position: relative; height: 10px; background: #1c232b; border-radius: 6px; overflow: visible;
    margin: 0.35rem 0 0.15rem 0;
}
.gauge-fill { position: absolute; top: 0; left: 0; height: 10px; border-radius: 6px; }
.gauge-fill-pass { background: #22c55e; }
.gauge-fill-borderline { background: #f59e0b; }
.gauge-fill-fail { background: #ef4444; }
.gauge-marker {
    position: absolute; top: -3px; width: 2px; height: 16px; background: #e6edf3; opacity: 0.85;
}
.gauge-caption { display:flex; justify-content: space-between; font-size: 0.72rem; color: #7b8794; margin-top: 2px; }

.estimated-tag {
    display: inline-block; background: rgba(96,165,250,0.16); color: #93c5fd; font-size: 0.68rem;
    font-weight: 700; padding: 1px 8px; border-radius: 999px; margin-left: 6px; letter-spacing: 0.03em;
}

.footer-disclaimer {
    margin-top: 2.2rem; padding-top: 1rem; border-top: 1px solid #232b34;
    color: #7b8794; font-size: 0.76rem; line-height: 1.5;
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Cached data + screening call
# ---------------------------------------------------------------------------
@st.cache_data(ttl=1800, show_spinner=False)
def run_screen(ticker: str, debt_max: float, cash_max: float, npi_max: float, band: float):
    cfg = ThresholdConfig(
        debt_to_mcap_max=debt_max,
        cash_sec_to_mcap_max=cash_max,
        npi_to_revenue_max=npi_max,
        borderline_band=band,
    )
    return screen_ticker(ticker, cfg=cfg)


def fmt_money(v):
    if v is None:
        return "n/a"
    v = float(v)
    sign = "-" if v < 0 else ""
    v = abs(v)
    if v >= 1e12:
        return f"{sign}${v/1e12:.2f}T"
    if v >= 1e9:
        return f"{sign}${v/1e9:.2f}B"
    if v >= 1e6:
        return f"{sign}${v/1e6:.1f}M"
    if v >= 1e3:
        return f"{sign}${v/1e3:.1f}K"
    return f"{sign}${v:.0f}"


def fmt_pct(v):
    if v is None:
        return "n/a"
    return f"{v * 100:.2f}%"


VERDICT_CSS = {
    Verdict.COMPLIANT: ("verdict-compliant", "badge-compliant", "✓ COMPLIANT"),
    Verdict.NON_COMPLIANT: ("verdict-noncompliant", "badge-noncompliant", "✕ NON-COMPLIANT"),
    Verdict.BORDERLINE: ("verdict-borderline", "badge-borderline", "⚠ BORDERLINE"),
    Verdict.INSUFFICIENT_DATA: ("verdict-insufficient", "badge-insufficient", "? INSUFFICIENT DATA"),
}

STATUS_CSS = {
    RuleStatus.PASS: ("status-pass", "gauge-fill-pass", "PASS"),
    RuleStatus.FAIL: ("status-fail", "gauge-fill-fail", "FAIL"),
    RuleStatus.BORDERLINE: ("status-borderline", "gauge-fill-borderline", "BORDERLINE"),
    RuleStatus.REVIEW: ("status-review", "gauge-fill-borderline", "NEEDS REVIEW"),
    RuleStatus.NOT_APPLICABLE: ("status-review", "gauge-fill-borderline", "N/A"),
}


def _flatten_html(s: str) -> str:
    """Collapse a multi-line, indented HTML f-string to a single line with no
    leading whitespace or blank lines. Streamlit's markdown renderer runs content
    through a CommonMark parser before the raw-HTML passthrough; a blank/whitespace
    -only line followed by 4+ spaces of indentation is interpreted as an indented
    code block, which escapes the HTML instead of rendering it. Flattening avoids
    that entirely."""
    lines = [line.strip() for line in s.strip().splitlines()]
    return " ".join(line for line in lines if line)


def render_gauge(value, threshold, status):
    _, fill_class, _ = STATUS_CSS[status]
    if value is None:
        return '<div class="rule-note">No value available to plot.</div>'
    max_scale = threshold * 2.0 if threshold > 0 else max(value, 0.01) * 2
    fill_pct = max(0.0, min(value / max_scale, 1.0)) * 100
    marker_pct = max(0.0, min(threshold / max_scale, 1.0)) * 100
    return _flatten_html(f"""
    <div class="gauge-track">
        <div class="gauge-fill {fill_class}" style="width:{fill_pct:.1f}%;"></div>
        <div class="gauge-marker" style="left:{marker_pct:.1f}%;"></div>
    </div>
    <div class="gauge-caption"><span>0%</span><span>threshold {threshold*100:.0f}%</span><span>{max_scale*100:.0f}%</span></div>
    """)


def render_rule_card(rule):
    status_class, _, status_label = STATUS_CSS[rule.status]
    est_tag = '<span class="estimated-tag">ESTIMATED</span>' if rule.estimated else ""
    gauge_html = render_gauge(rule.value, rule.threshold, rule.status)
    value_str = fmt_pct(rule.value)
    html = f"""
    <div class="rule-card">
        <div class="rule-head">
            <div class="rule-label">{rule.label}{est_tag}</div>
            <div class="rule-status {status_class}">{status_label}</div>
        </div>
        <div class="rule-meta">
            {rule.numerator_label}: <b>{fmt_money(rule.numerator_value)}</b> &nbsp;/&nbsp;
            {rule.denominator_label}: <b>{fmt_money(rule.denominator_value)}</b>
            &nbsp;&rarr;&nbsp; <b>{value_str}</b> (threshold &lt; {rule.threshold*100:.0f}%)
        </div>
        {gauge_html}
        <div class="rule-note">{rule.note}</div>
    </div>
    """
    return _flatten_html(html)


def render_business_card(business):
    status_class, _, status_label = STATUS_CSS[business.status]
    sector = business.sector or "n/a"
    industry = business.industry or "n/a"
    html = f"""
    <div class="rule-card">
        <div class="rule-head">
            <div class="rule-label">Business activity screen</div>
            <div class="rule-status {status_class}">{status_label}</div>
        </div>
        <div class="rule-meta">Sector: <b>{sector}</b> &nbsp;|&nbsp; Industry: <b>{industry}</b></div>
        <div class="rule-note">{business.note}</div>
    </div>
    """
    return _flatten_html(html)


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown('<div class="app-title">☪ Shari\'ah-Compliant Stock Screener</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="app-subtitle">Transparent, rule-by-rule Shari\'ah compliance screening '
    'for US-listed stocks &mdash; every verdict shows its work.</div>',
    unsafe_allow_html=True,
)

EXAMPLE_TICKERS = [
    "AAPL", "MSFT", "GOOGL", "NVDA", "TSLA", "JPM", "BAC", "KO", "PM", "MO",
    "LVS", "WMT", "META", "AMZN", "XOM", "JNJ", "PG", "V", "LMT", "BUD",
]

with st.form(key="search_form", clear_on_submit=False):
    col1, col2 = st.columns([4, 1])
    with col1:
        ticker_input = st.text_input(
            "Ticker", value=st.session_state.get("ticker", ""),
            placeholder="e.g. AAPL, TSLA, JPM", label_visibility="collapsed",
        )
    with col2:
        submitted = st.form_submit_button("Screen", use_container_width=True)

st.caption("Try:")
CHIPS_PER_ROW = 10
chip_rows = [EXAMPLE_TICKERS[i:i + CHIPS_PER_ROW] for i in range(0, len(EXAMPLE_TICKERS), CHIPS_PER_ROW)]
for row in chip_rows:
    cols = st.columns(CHIPS_PER_ROW)
    for col, t in zip(cols, row):
        with col:
            if st.button(t, key=f"chip_{t}", use_container_width=True):
                st.session_state["ticker"] = t

with st.expander("⚙️ Advanced: adjust screening thresholds"):
    st.caption(f"Default methodology: **{STANDARD_NAME}**. Adjust below to model a different provider's rules.")
    c1, c2 = st.columns(2)
    with c1:
        debt_max = st.number_input("Debt / market cap max", 0.0, 1.0, DEBT_TO_MARKETCAP_MAX, 0.01, format="%.2f")
        cash_max = st.number_input("Cash+securities / market cap max", 0.0, 1.0, CASH_SECURITIES_TO_MARKETCAP_MAX, 0.01, format="%.2f")
    with c2:
        npi_max = st.number_input("Non-permissible income / revenue max", 0.0, 1.0, NON_PERMISSIBLE_INCOME_MAX, 0.01, format="%.2f")
        band = st.number_input("Borderline band (+/- around threshold)", 0.0, 0.5, BORDERLINE_BAND, 0.01, format="%.2f")

ticker = (ticker_input or "").strip().upper()

if submitted and ticker:
    st.session_state["ticker"] = ticker

active_ticker = st.session_state.get("ticker", "")

if active_ticker:
    with st.spinner(f"Screening {active_ticker}…"):
        try:
            result = run_screen(active_ticker, debt_max, cash_max, npi_max, band)
        except Exception as e:
            result = None
            st.error(
                f"Couldn't fetch data for **{active_ticker}**. The data provider may be "
                f"rate-limiting or the ticker may not exist. Details: {e}"
            )

    if result is not None:
        if result.company_data.fetch_error:
            st.error(result.company_data.fetch_error)
        else:
            card_class, badge_class, badge_label = VERDICT_CSS[result.verdict]
            reasons_html = "".join(f"<li>{r}</li>" for r in result.reasons)
            verdict_html = f"""
                <div class="verdict-card {card_class}">
                    <span class="verdict-badge {badge_class}">{badge_label}</span>
                    <div class="company-name">{result.company_name} ({result.ticker})</div>
                    <div class="company-sub">Screened against {STANDARD_NAME}</div>
                    <ul class="reasons">{reasons_html}</ul>
                </div>
                """
            st.markdown(_flatten_html(verdict_html), unsafe_allow_html=True)

            if result.company_data.warnings:
                with st.expander("Data quality notes for this ticker"):
                    for w in result.company_data.warnings:
                        st.write(f"- {w}")

            st.markdown("#### Stage 1 &mdash; Business activity", unsafe_allow_html=True)
            st.markdown(render_business_card(result.business_screen), unsafe_allow_html=True)

            st.markdown("#### Stage 2 &mdash; AAOIFI financial ratios", unsafe_allow_html=True)
            for rule in result.rules:
                st.markdown(render_rule_card(rule), unsafe_allow_html=True)

st.divider()

with st.expander("How this works (methodology)"):
    st.markdown(f"""
**Standard used:** {STANDARD_NAME}

{STANDARD_DESCRIPTION}

This screener runs two stages, in order:

**Stage 1 — Business activity.** A company is excluded outright if its core business is a
non-permissible activity: conventional (interest-based) banking or insurance, alcohol,
tobacco, pork, gambling, adult entertainment, or weapons/defense manufacturing. This uses
a curated list for well-known names plus keyword matching against the company's
sector/industry classification.

**Stage 2 — Financial ratios**, each denominated by market capitalization:

1. **Interest-bearing debt / market cap** must be below **{DEBT_TO_MARKETCAP_MAX:.0%}**.
2. **(Cash + interest-bearing securities) / market cap** must be below **{CASH_SECURITIES_TO_MARKETCAP_MAX:.0%}**.
3. **Non-permissible (interest) income / total revenue** must be below **{NON_PERMISSIBLE_INCOME_MAX:.0%}**.

A company that clears Stage 1 and all three Stage 2 thresholds is marked **COMPLIANT**.
Failing Stage 1, or clearly exceeding any Stage 2 threshold, marks it **NON-COMPLIANT**.
Ratios that sit close to a threshold (within {BORDERLINE_BAND:.0%} of it) are marked
**BORDERLINE** rather than a hard pass/fail, since small reporting differences or data lag
could flip the result.

**Known limitation — non-permissible income.** AAOIFI's "non-permissible income" figure is
broader than anything cleanly reported in standard US filings. This app uses disclosed
non-operating/interest income as a transparent **proxy**, clearly labeled *ESTIMATED* in
the UI, and always recommends manual analyst confirmation for that specific rule. This is
a deliberate, disclosed limitation — not a fabricated number.

**Data source:** Yahoo Finance via the `yfinance` Python library. Fundamentals reflect the
most recently reported period available from that source and may lag real-time filings.
    """)

st.markdown(
    f'<div class="footer-disclaimer">{DISCLAIMER}</div>',
    unsafe_allow_html=True,
)
