import pandas as pd
import numpy as np
import re
from typing import List
from datetime import datetime
from app.analytics.models import ValidationResult
from app.utils.helpers import (
    _val, _num, _display,
    REQUIRED_COLUMNS, VALID_MONTH_NAMES, URL_PATTERN
)

def rule_empty_cells(row: pd.Series, df: pd.DataFrame) -> List[ValidationResult]:
    """Rule 5: No empty cells in required columns."""
    errors = []
    for col in REQUIRED_COLUMNS:
        if col in row.index:
            v = _val(row, col)
            if not v:
                errors.append(ValidationResult(False, "Celdas vacías", f"Columna '{col}' está vacía"))
    return errors

def rule_unique_llave(row: pd.Series, df: pd.DataFrame) -> List[ValidationResult]:
    """Rule 1/4: LLAVE must be unique code, no duplicates."""
    val = _val(row, "LLAVE")
    if not val:
        return []
    if "LLAVE" in df.columns and (df["LLAVE"] == val).sum() > 1:
        return [ValidationResult(False, "ID Duplicado", f"LLAVE '{_display(val)}' se repite en la base")]
    return []

def rule_percentages_max_100(row: pd.Series, df: pd.DataFrame) -> List[ValidationResult]:
    """Rule 6: Percentage columns must not exceed 100%."""
    pct_cols = [
        "Porcentaje avance al corte",
        "Porcentaje de avance de los entregables",
        "Porcentaje avance periodo evaluado",
        "Porcentaje avance anterior",
    ]
    errors = []
    for col in pct_cols:
        if col in row.index:
            n = _num(row, col)
            if not np.isnan(n) and n > 100:
                errors.append(ValidationResult(
                    False, "Error en avance",
                    f"'{col}' = {n}% supera el 100%"
                ))
    return errors

def rule_url_evidence(row: pd.Series, df: pd.DataFrame) -> List[ValidationResult]:
    """Rules 7-8: Validate URL format for evidence links."""
    errors = []
    for col in ["Enlace Evidencia\n(Actividad)", "Enlace evidencia del seguimiento"]:
        if col in row.index:
            v = _val(row, col)
            if v and not URL_PATTERN.match(v):
                errors.append(ValidationResult(
                    False, "Enlaces dañados",
                    f"URL inválida en '{col}': {_display(v)[:60]}..."
                ))
    return errors

def rule_month_name(row: pd.Series, df: pd.DataFrame) -> List[ValidationResult]:
    """Rule 4: Periodo seguimiento must be a full month name."""
    val = _val(row, "Periodo seguimiento")
    if not val:
        return []
    if val.capitalize() not in VALID_MONTH_NAMES:
        return [ValidationResult(False, "Error en mes", f"Debe ser mes completo, se encontró: '{_display(val)}'")]
    return []

def rule_auditor_initials(row: pd.Series, df: pd.DataFrame) -> List[ValidationResult]:
    """Rule 5: Auditor name must be initials."""
    col_candidates = [
        "Nombre Auditor\n(quien realiza seguimiento)",
        "Nombre Auditor (quien realiza seguimiento)",
    ]
    val = ""
    for c in col_candidates:
        if c in row.index:
            val = _val(row, c)
            break
    if not val:
        return []
    if not re.match(r"^[A-Z]{2,5}$", val):
        return [ValidationResult(False, "Error en Nombre", f"Iniciales inválidas: '{_display(val)}'")]
    return []

def rule_followup_date(row: pd.Series, df: pd.DataFrame) -> List[ValidationResult]:
    """Rule 9: Fecha de seguimiento must be in current year."""
    val = _val(row, "Fecha de seguimiento por parte del auditor")
    if not val:
        return []
    current_year = str(datetime.now().year)
    if current_year not in val:
        return [ValidationResult(
            False, "Error en Fecha",
            f"Fecha de seguimiento '{_display(val)}' no corresponde al año vigente ({current_year})"
        )]
    return []
