# Shari'ah-Compliant Stock Screener

A transparent, fully explainable Shari'ah-compliance screener for US-listed stocks.
Search a ticker, get a **COMPLIANT / NON-COMPLIANT / BORDERLINE** verdict, and see the
exact numbers and sources behind every rule — nothing is a black box.

Built as a portfolio project to demonstrate rule-based financial screening with genuine
explainability, using a real, citable Islamic finance standard rather than an ad-hoc
heuristic.

## Live demo

`<INSERT DEPLOYED URL HERE AFTER DEPLOYMENT>`

## Methodology

This screener implements **AAOIFI Shari'ah Standard No. 21** ("Financial Paper — Shares
and Bonds"), published by the Accounting and Auditing Organization for Islamic Financial
Institutions, the most widely cited standard behind commercial Islamic index/screening
products (e.g. Dow Jones Islamic Market Index, MSCI Islamic, S&P Shariah use variants of
the same two-stage approach).

### Stage 1 — Business activity screen

A company is excluded outright if its core business is a non-permissible activity:

- Conventional (interest-based) banking, lending, or credit services
- Conventional insurance
- Alcohol production
- Tobacco
- Pork / non-Shari'ah-compliant food production
- Gambling
- Adult entertainment
- Weapons / defense manufacturing

Classification uses a curated ticker override list for well-known names (most reliable),
falling back to keyword matching against the sector/industry classification returned by
the data provider. Mixed-activity companies where public data can't cleanly separate the
non-permissible revenue share (e.g. diversified food producers with some pork products)
are flagged **BORDERLINE** rather than silently passed or failed.

### Stage 2 — Financial ratios (market-cap denominated)

| Rule | Threshold |
|---|---|
| Interest-bearing debt / market cap | < 30% |
| (Cash + interest-bearing securities) / market cap | < 30% |
| Non-permissible (interest) income / total revenue | < 5% |

All three thresholds, and the "how close counts as borderline" band, are configurable
constants in `screener/constants.py` (and adjustable live in the app's "Advanced" panel) —
this is deliberate, since different providers use slightly different numbers (some use
33% instead of 30%, or total assets instead of market cap as the denominator).

**Borderline logic.** A ratio isn't just PASS/FAIL — if it's within a configurable band
(default ±15%) of the threshold, it's marked BORDERLINE so a reporting lag or data quirk
doesn't produce a false sense of certainty in either direction.

### Known limitation: non-permissible income (by design, not oversight)

AAOIFI's "non-permissible income" figure is broader than anything cleanly reported in
standard US filings — it can include interest income, non-Shari'ah-compliant investment
gains, and other impermissible sources that aren't broken out as a single line item.

Rather than fabricate this number, the app uses **disclosed non-operating/interest
income** as a transparent proxy, always labeled **ESTIMATED** in the UI, with an explicit
note recommending manual/analyst confirmation. If no interest-income line item is
disclosed at all, the rule is marked **NEEDS REVIEW** and the overall verdict is capped at
BORDERLINE — the app will never claim COMPLIANT on the strength of a number it can't
actually verify.

### Data source

[`yfinance`](https://github.com/ranaroussi/yfinance), pulling from Yahoo Finance. Fields
used: market cap (`fast_info` / `info`), total debt, cash & short-term investments,
total revenue, sector/industry classification, and non-operating interest income —
with documented fallbacks across `.info`, `.balance_sheet`, and `.income_stmt` for
each figure (see `screener/data_provider.py`), because Yahoo doesn't consistently expose
every field for every ticker. Every number shown in the UI records exactly which field it
came from.

Fundamentals reflect the most recently reported period available from Yahoo Finance and
may lag real-time filings by a quarter or more. Yahoo Finance is an unofficial data source
and is occasionally rate-limited on shared hosting IPs — if a lookup fails, wait a minute
and retry.

## Project structure

```
stock-screener/
├── app.py                       # Streamlit UI / entrypoint
├── screener/
│   ├── constants.py              # AAOIFI thresholds, exclusion lists, disclaimer text
│   ├── models.py                 # dataclasses: CompanyData, RuleResult, ScreeningResult
│   ├── data_provider.py           # yfinance fetch + field-fallback logic
│   ├── business_screen.py         # Stage 1 logic
│   └── financial_screen.py        # Stage 2 ratio math + verdict combination
├── tests/
│   └── test_screening_logic.py    # unit tests over synthetic data (no network needed)
├── .streamlit/config.toml         # dark theme
└── requirements.txt
```

## Running locally

```bash
git clone <this-repo-url>
cd stock-screener
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL Streamlit prints (typically `http://localhost:8501`).

## Running the tests

```bash
python tests/test_screening_logic.py
```

These are pure unit tests against synthetic `CompanyData` objects — they verify the ratio
math and verdict-combination rules without hitting the network, so they run anywhere.

## Deploying (Streamlit Community Cloud)

1. Push this repo to GitHub (public).
2. Go to [share.streamlit.io](https://share.streamlit.io), sign in with GitHub.
3. Click **New app**, select this repo/branch, set the main file path to `app.py`.
4. Deploy. Streamlit Cloud installs `requirements.txt` automatically.

The app has no secrets/API keys to configure — Yahoo Finance access via `yfinance` is
unauthenticated.

## Adjusting the methodology

Every threshold is a named constant in `screener/constants.py` (`DEBT_TO_MARKETCAP_MAX`,
`CASH_SECURITIES_TO_MARKETCAP_MAX`, `NON_PERMISSIBLE_INCOME_MAX`, `BORDERLINE_BAND`), and
can also be tuned live from the app's "Advanced" panel without touching code — useful for
modeling a different provider's methodology (e.g. Dow Jones Islamic Market's variant) side
by side.

## Disclaimer

This tool is an independent educational and portfolio project. It is **not** investment
advice, **not** a fatwa, and **not** affiliated with, endorsed by, or representative of
any brokerage, bank, or Shari'ah board. Screening results are informational only, may
contain data errors or lag reported financials, and should not be relied upon for actual
investment or religious-compliance decisions. Always verify against a qualified Shari'ah
board or a licensed Islamic screening provider before investing.

## License

MIT — see `LICENSE`.
