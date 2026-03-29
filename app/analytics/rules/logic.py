import pandas as pd
import numpy as np
from typing import List
from app.analytics.models import ValidationResult
from app.utils.helpers import _val, _num, _display

def rule_evidence_supply_logic(row: pd.Series, df: pd.DataFrame) -> List[ValidationResult]:
    """Rule 7: Logic between suministró info and fecha de cargue."""
    supply = _val(row, "¿La dependencia suministro información?").upper()
    load_date = _val(row, "Fecha de Cargue de la evidencia (Dependencia)").upper()
    if not supply: return []
    if "SI" in supply:
        if "NO APLICA" in load_date or not load_date:
            return [ValidationResult(False, "Error en Fecha", "Suministró información = SI, pero Fecha de Cargue es 'No aplica' o vacía")]
    elif "NO" in supply:
        if load_date and "NO APLICA" not in load_date:
            return [ValidationResult(False, "Error en Fecha", f"Suministró información = NO, pero Fecha de Cargue no dice 'No aplica' (dice: '{_display(load_date)}')")]
    return []

def rule_supply_si_requires_soportes(row: pd.Series, df: pd.DataFrame) -> List[ValidationResult]:
    """Rule 10: If suministró = SI, Cantidad de Soportes must be > 0."""
    supply = _val(row, "¿La dependencia suministro información?").upper()
    if "SI" not in supply: return []
    soportes = _num(row, "Cantidad de Soportes cargados por la Dependencia")
    if np.isnan(soportes) or soportes <= 0:
        return [ValidationResult(False, "Error en entregable", f"Suministró información = SI, pero Cantidad de Soportes = {_display(_val(row, 'Cantidad de Soportes cargados por la Dependencia'))}")]
    return []

def rule_soportes_vs_entregables(row: pd.Series, df: pd.DataFrame) -> List[ValidationResult]:
    """Rule 11: If Soportes > 0, entregables asociados must be >= Soportes."""
    soportes = _num(row, "Cantidad de Soportes cargados por la Dependencia")
    if np.isnan(soportes) or soportes <= 0: return []
    entregables = _num(row, "No. de entregables asociados a la Actividad")
    if np.isnan(entregables) or entregables < soportes:
        return [ValidationResult(False, "Error en entregable", f"Soportes cargados ({int(soportes)}) > Entregables asociados ({_display(_val(row, 'No. de entregables asociados a la Actividad'))})")]
    return []

def rule_suficiente_no_consistency(row: pd.Series, df: pd.DataFrame) -> List[ValidationResult]:
    """Rule 12: If Suficiente=NO, then Relevante and Fiable must also be NO."""
    suf_candidates = [c for c in row.index if "Suficiente" in str(c)]
    rel_candidates = [c for c in row.index if "Relevante" in str(c)]
    fia_candidates = [c for c in row.index if "Fiable" in str(c)]
    if not suf_candidates: return []
    suf = _val(row, suf_candidates[0]).upper()
    if suf != "NO": return []
    errors = []
    if rel_candidates:
        rel = _val(row, rel_candidates[0]).upper()
        if rel and rel != "NO":
            errors.append(ValidationResult(False, "Errores en base de datos", f"Suficiente=NO pero Relevante='{_display(rel)}' (debería ser NO)"))
    if fia_candidates:
        fia = _val(row, fia_candidates[0]).upper()
        if fia and fia != "NO":
            errors.append(ValidationResult(False, "Errores en base de datos", f"Suficiente=NO pero Fiable='{_display(fia)}' (debería ser NO)"))
    return errors

def rule_entregables_vs_cantidad(row: pd.Series, df: pd.DataFrame) -> List[ValidationResult]:
    """Rule 13: Entregables asociados must not exceed Cantidad de Entregables."""
    asociados = _num(row, "No. de entregables asociados a la Actividad")
    cantidad = _num(row, "Cantidad de Entregables")
    if np.isnan(asociados) or np.isnan(cantidad): return []
    if asociados > cantidad:
        return [ValidationResult(False, "Error en entregable", f"Entregables asociados ({int(asociados)}) supera Cantidad de Entregables ({int(cantidad)})")]
    return []

def rule_progress_comparison(row: pd.Series, df: pd.DataFrame) -> List[ValidationResult]:
    """Rule 14: Previous progress cannot be greater than current."""
    current = _num(row, "Porcentaje avance periodo evaluado")
    previous = _num(row, "Porcentaje avance anterior")
    if np.isnan(current) or np.isnan(previous): return []
    if previous > current:
        return [ValidationResult(False, "Error en avance", f"Avance anterior ({previous}%) es mayor que el actual ({current}%)")]
    return []
