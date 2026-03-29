import pandas as pd
import numpy as np
import re
from typing import Optional, List, Dict

# --- Constants ---

GRAY_COLUMNS = {
    "Comentario",
    "Porcentaje avance al corte",
    "Validación sobre Auditor",
    "No. De entregables pendientes",
    "Porcentaje de avance de los entregables",
    "Calificación Parcial",
    "Oportunidad",
    "Porcentaje avance periodo evaluado",
    "Porcentaje avance anterior",
    "Validación %",
    "Auditor_Sheet",
    "Sheet_Row",
}

REQUIRED_COLUMNS = [
    "ID", "Titulo del Trabajo", "Proceso Origen",
    "Tipo", "Connotación Observacion", "Dependencia",
    "ID Observacion", "ID Acción", "Acción",
    "ID Actividad", "LLAVE",
    "Descripción de la actividad", "Entregable", "Cantidad de Entregables",
    "Periodo seguimiento",
]

VALID_MONTH_NAMES = [
    "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
    "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
]

URL_PATTERN = re.compile(r'^https?://.+', re.IGNORECASE)

# --- Helper Functions ---

def _val(row, col_name: str) -> str:
    """Safely get a trimmed string value from a row, returning '' if NaN.
    Uses fuzzy matching: tries exact match first, then normalized match."""
    # Try exact match
    v = row.get(col_name, None)
    if v is not None:
        if pd.isna(v):
            return ""
        return str(v).strip()
    
    # Try normalized match (collapse whitespace/newlines)
    normalized_target = " ".join(col_name.split()).lower()
    for col in row.index:
        normalized_col = " ".join(str(col).split()).lower()
        if normalized_col == normalized_target:
            v = row.get(col, "")
            if pd.isna(v):
                return ""
            return str(v).strip()
    return ""

def _num(row, col_name: str) -> float:
    """Safely parse a numeric value, stripping % signs. Returns NaN on failure."""
    v = _val(row, col_name)
    if not v:
        return float("nan")
    v = v.replace("%", "").replace(",", ".").strip()
    try:
        return float(v)
    except ValueError:
        return float("nan")

def _display(value: str) -> str:
    """Replace empty/nan values with 'Vacío' for user-facing messages."""
    if not value or value.lower() in ("nan", "none", ""):
        return "Vacío"
    return value

def find_column_fuzzy(df: pd.DataFrame, target: str) -> Optional[str]:
    """Find a column name in a DataFrame using fuzzy matching (handles newlines/spaces)."""
    if target in df.columns:
        return target
    normalized_target = " ".join(target.split()).lower()
    for col in df.columns:
        normalized_col = " ".join(str(col).split()).lower()
        if normalized_col == normalized_target:
            return col
    return None
