"""Unit tests for the screening logic. These use synthetic CompanyData objects so they
run with zero network access -- pure verification of the ratio math and verdict rules.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from screener.constants import ThresholdConfig
from screener.models import CompanyData, RuleStatus, Verdict
from screener.business_screen import screen_business_activity
from screener.financial_screen import build_screening_result


def make_company(**kwargs) -> CompanyData:
    defaults = dict(
        ticker="TEST",
        long_name="Test Co",
        sector="Technology",
        industry="Software - Infrastructure",
        market_cap=1_000_000_000.0,
        total_debt=50_000_000.0,
        cash_and_short_term_investments=100_000_000.0,
        total_revenue=500_000_000.0,
        non_operating_interest_income=2_000_000.0,
    )
    defaults.update(kwargs)
    return CompanyData(**{k: v for k, v in defaults.items() if k in CompanyData.__dataclass_fields__})


def run(company, cfg=None):
    cfg = cfg or ThresholdConfig()
    business = screen_business_activity(company)
    return build_screening_result(company, business, cfg)


def test_clean_compliant_company():
    company = make_company()  # debt 5%, cash 10%, npi 0.4% -- all well clear
    result = run(company)
    assert result.verdict == Verdict.COMPLIANT, result.reasons


def test_bank_ticker_override_excluded():
    company = make_company(ticker="JPM", industry="Banks - Diversified")
    result = run(company)
    assert result.verdict == Verdict.NON_COMPLIANT
    assert result.business_screen.status == RuleStatus.FAIL
    assert "banking" in result.business_screen.matched_category.lower()


def test_industry_keyword_alcohol_excluded():
    company = make_company(ticker="ZZZZ", industry="Beverages - Brewers")
    result = run(company)
    assert result.verdict == Verdict.NON_COMPLIANT
    assert result.business_screen.status == RuleStatus.FAIL


def test_debt_ratio_clear_fail():
    company = make_company(total_debt=600_000_000.0)  # 60% of mcap, way over 30%
    result = run(company)
    assert result.verdict == Verdict.NON_COMPLIANT
    debt_rule = next(r for r in result.rules if r.key == "debt_to_mcap")
    assert debt_rule.status == RuleStatus.FAIL


def test_debt_ratio_borderline():
    # 30% threshold, band 0.15 -> borderline zone is proximity in [0.85, 1.15]
    # i.e. ratio in [0.255, 0.345]
    company = make_company(total_debt=300_000_000.0)  # exactly 30% -> proximity 1.0 -> borderline
    result = run(company)
    debt_rule = next(r for r in result.rules if r.key == "debt_to_mcap")
    assert debt_rule.status == RuleStatus.BORDERLINE
    assert result.verdict == Verdict.BORDERLINE


def test_debt_ratio_clear_pass():
    company = make_company(total_debt=100_000_000.0)  # 10% of mcap
    result = run(company)
    debt_rule = next(r for r in result.rules if r.key == "debt_to_mcap")
    assert debt_rule.status == RuleStatus.PASS


def test_missing_market_cap_insufficient_data():
    company = make_company(market_cap=None)
    result = run(company)
    assert result.verdict == Verdict.INSUFFICIENT_DATA


def test_missing_interest_income_flags_review_and_borderline():
    company = make_company(non_operating_interest_income=None)
    result = run(company)
    npi_rule = next(r for r in result.rules if r.key == "npi_to_revenue")
    assert npi_rule.status == RuleStatus.REVIEW
    assert result.verdict == Verdict.BORDERLINE


def test_income_ratio_clear_fail():
    company = make_company(non_operating_interest_income=100_000_000.0)  # 20% of revenue
    result = run(company)
    npi_rule = next(r for r in result.rules if r.key == "npi_to_revenue")
    assert npi_rule.status == RuleStatus.FAIL
    assert result.verdict == Verdict.NON_COMPLIANT


def test_mixed_activity_ticker_borderline_override():
    company = make_company(ticker="TSN", industry="Packaged Foods")
    result = run(company)
    assert result.business_screen.status == RuleStatus.BORDERLINE
    assert result.verdict == Verdict.BORDERLINE


def test_custom_threshold_config():
    cfg = ThresholdConfig(debt_to_mcap_max=0.10, cash_sec_to_mcap_max=0.10, npi_to_revenue_max=0.02, borderline_band=0.10)
    company = make_company(total_debt=50_000_000.0)  # 5% of mcap -- fails a 10% threshold? no, 5% < 10%*0.9=9% -> pass
    result = run(company, cfg=cfg)
    debt_rule = next(r for r in result.rules if r.key == "debt_to_mcap")
    assert debt_rule.status == RuleStatus.PASS


if __name__ == "__main__":
    import inspect
    tests = [obj for name, obj in list(globals().items()) if name.startswith("test_") and inspect.isfunction(obj)]
    passed, failed = 0, 0
    for t in tests:
        try:
            t()
            print(f"PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"FAIL  {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"ERROR {t.__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed out of {len(tests)}")
    sys.exit(1 if failed else 0)
