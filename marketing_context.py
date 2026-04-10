"""Contexto común para páginas marketing / precios."""
from datetime import datetime, timezone

from config import (
    ANNUAL_PRICE,
    FREE_MAX_ANALYSES,
    FREE_MAX_DAYS,
    FREE_MAX_FILES_PER_ANALYSIS,
    FREE_REPORTS_PER_MONTH,
    MONTHLY_PRICE,
    PREMIUM_MONTHLY_PRICE,
    PRO_180_MAX_ANALYSES,
    PRO_180_MAX_DAYS,
    PRO_180_MAX_FILES,
    PRO_90_MAX_ANALYSES,
    PRO_90_MAX_DAYS,
    PRO_90_MAX_FILES,
    PRO_90_REPORTS_PER_MONTH,
    PRO_PLUS_MAX_ANALYSES,
    PRO_PLUS_REPORTS_PER_MONTH,
)


def marketing_page_context():
    return {
        "monthly_price": MONTHLY_PRICE,
        "annual_price": ANNUAL_PRICE,
        "free_max_days": FREE_MAX_DAYS,
        "free_max_files": FREE_MAX_FILES_PER_ANALYSIS,
        "free_max_analyses": FREE_MAX_ANALYSES,
        "free_reports_per_month": FREE_REPORTS_PER_MONTH,
        "premium_monthly_price": PREMIUM_MONTHLY_PRICE,
        "pro_90_max_days": PRO_90_MAX_DAYS,
        "pro_90_max_files": PRO_90_MAX_FILES,
        "pro_90_max_analyses": PRO_90_MAX_ANALYSES,
        "pro_90_reports_per_month": PRO_90_REPORTS_PER_MONTH,
        "pro_180_max_days": PRO_180_MAX_DAYS,
        "pro_180_max_files": PRO_180_MAX_FILES,
        "pro_180_max_analyses": PRO_180_MAX_ANALYSES,
        "pro_plus_max_analyses": PRO_PLUS_MAX_ANALYSES,
        "pro_plus_reports_per_month": PRO_PLUS_REPORTS_PER_MONTH,
        "current_year": datetime.now(timezone.utc).year,
    }
