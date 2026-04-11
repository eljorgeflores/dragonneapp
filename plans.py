"""Etiquetas y límites de archivos por plan de producto."""
from config import (
    FREE_MAX_FILES_PER_ANALYSIS,
    PRO_180_MAX_FILES,
    PRO_90_MAX_FILES,
)


def plan_label(plan: str) -> str:
    if plan == "pro_plus":
        return "Pro+"
    if plan == "pro":
        return "Pro"
    if plan == "free_trial":
        return "Prueba extendida"
    return "Gratis"


def max_upload_files_for_plan(plan: str) -> int:
    if plan == "free":
        return FREE_MAX_FILES_PER_ANALYSIS
    if plan == "pro":
        return PRO_90_MAX_FILES
    if plan in ("pro_plus", "free_trial"):
        return PRO_180_MAX_FILES
    return FREE_MAX_FILES_PER_ANALYSIS
