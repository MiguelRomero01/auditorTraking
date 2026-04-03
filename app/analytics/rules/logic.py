import pandas as pd
import numpy as np
from typing import List
from app.analytics.models import ValidationResult
from app.utils.helpers import _val, _num, _display, GRAY_COLUMNS


def rule_evidence_supply_logic(row: pd.Series, df: pd.DataFrame) -> List[ValidationResult]:
    """Logic between suministró info and fecha de cargue."""
    supply = _val(row, "¿La dependencia suministro información?").upper()
    load_date = _val(row, "Fecha de Cargue de la evidencia (Dependencia)").upper()
    if not supply: return []
    if "SI" in supply:
        if "NO APLICA" in load_date or not load_date:
            return [ValidationResult(False, "Error en Fecha", "Suministró información = SI, pero Fecha de Cargue es 'No aplica' o vacía")]
    elif "NO" in supply:
        if load_date and "NO APLICA" not in load_date:
            return [ValidationResult(False, "Error en Fecha", f"Suministró información = NO, pero Fecha de Cargue no dice 'No aplica' (dice: '{_display(load_date)}')" )]
    return []


def rule_supply_si_requires_soportes(row: pd.Series, df: pd.DataFrame) -> List[ValidationResult]:
    """If suministró = SI, Cantidad de Soportes (AJ) must be > 0."""
    supply = _val(row, "¿La dependencia suministro información?").upper()
    if "SI" not in supply: return []
    soportes = _num(row, "Cantidad de Soportes cargados por la Dependencia")
    if np.isnan(soportes) or soportes <= 0:
        return [ValidationResult(False, "Error en entregable", f"Suministró información = SI, pero Cantidad de Soportes = {_display(_val(row, 'Cantidad de Soportes cargados por la Dependencia'))}")]
    return []


def rule_soportes_vs_entregables(row: pd.Series, df: pd.DataFrame) -> List[ValidationResult]:
    """Soportes vs Entregables: 
    AL (Entregables asociados) cannot exceed AJ (Soportes cargados).
    AL cannot be less than zero."""
    errors = []

    soportes = _num(row, "Cantidad de Soportes cargados por la Dependencia")
    entregables_asociados = _num(row, "No. de entregables asociados a la Actividad")

    # AL >= 0 check
    if not np.isnan(entregables_asociados) and entregables_asociados < 0:
        errors.append(ValidationResult(
            False, "Error en entregable",
            f"No. de entregables asociados (AL={int(entregables_asociados)}) no puede ser inferior a cero"
        ))

    # AL <= AJ check
    if not np.isnan(entregables_asociados) and not np.isnan(soportes):
        if entregables_asociados > soportes:
            errors.append(ValidationResult(
                False, "Error en entregable",
                f"No. de entregables asociados (AL={int(entregables_asociados)}) > Soportes cargados (AJ={int(soportes)})"
            ))

    # C2: AL (Entregables asociados) <= X (Cantidad de Entregables)
    cantidad_entregables = _num(row, "Cantidad de Entregables")
    if not np.isnan(entregables_asociados) and not np.isnan(cantidad_entregables):
        if entregables_asociados > cantidad_entregables:
            errors.append(ValidationResult(
                False, "Error en entregable",
                f"Entregables asociados (AL={int(entregables_asociados)}) supera Cantidad de Entregables (X={int(cantidad_entregables)})"
            ))

    return errors


def rule_suficiente_no_consistency(row: pd.Series, df: pd.DataFrame) -> List[ValidationResult]:
    """If Suficiente=NO, then Relevante and Fiable must also be NO."""
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
    """C2: Entregables asociados (AL) must not exceed Cantidad de Entregables (X). 
    (Kept for backwards compatibility — main logic is now in rule_soportes_vs_entregables)"""
    return []


def rule_progress_comparison(row: pd.Series, df: pd.DataFrame) -> List[ValidationResult]:
    """C6: Previous progress (AX) cannot be greater than current (AW).
    Exception: if AC (avance al corte) >= 90, skip this check — activity is considered complete."""
    avance_corte = _num(row, "Porcentaje avance al corte")
    # C6 exception: if activity is at or above 90%, skip progress comparison
    if not np.isnan(avance_corte) and avance_corte >= 90:
        return []

    current = _num(row, "Porcentaje avance periodo evaluado")
    previous = _num(row, "Porcentaje avance anterior")
    if np.isnan(current) or np.isnan(previous): return []
    if previous > current:
        return [ValidationResult(False, "Error en avance", f"Avance anterior (AX={previous}%) es mayor que el actual (AW={current}%)")]
    return []


def rule_followup_at_90(row: pd.Series, df: pd.DataFrame) -> List[ValidationResult]:
    """C3: When AC (Porcentaje avance al corte) >= 90, AD (¿El Auditor debe hacer Seguimiento?)
    must be 'NO'. If AC > 100 that is caught elsewhere."""
    avance_corte = _num(row, "Porcentaje avance al corte")
    if np.isnan(avance_corte) or avance_corte < 90:
        return []
    followup = _val(row, "¿El Auditor debe hacer Seguimiento en este Periodo?").upper()
    if followup and followup != "NO":
        return [ValidationResult(
            False, "Seguimiento no requerido",
            f"Avance al corte (AC={avance_corte}%) ≥ 90%, pero la columna AD dice '{_display(followup)}' en vez de 'NO'"
        )]
    return []


def rule_validacion_vs_avance_anterior(row: pd.Series, df: pd.DataFrame) -> List[ValidationResult]:
    """C7: AW (avance periodo evaluado) cannot be less than AX (avance anterior).
    Additionally, when AW = 0, AY (Validación %) cannot be less than AX."""
    errors = []
    aw = _num(row, "Porcentaje avance periodo evaluado")
    ax = _num(row, "Porcentaje avance anterior")
    ay_candidates = [c for c in row.index if "Validación %" in str(c)]

    # AW >= AX always (AW can be 0)
    if not np.isnan(aw) and not np.isnan(ax):
        if aw < ax and aw != 0:
            # Only flag if AW is not zero (zero is always allowed)
            errors.append(ValidationResult(
                False, "Error en avance",
                f"Avance periodo evaluado (AW={aw}%) es menor que avance anterior (AX={ax}%)"
            ))

    # When AW = 0, AY >= AX
    if not np.isnan(aw) and aw == 0 and not np.isnan(ax):
        if ay_candidates:
            ay = _num(row, ay_candidates[0])
            if not np.isnan(ay) and ay < ax:
                errors.append(ValidationResult(
                    False, "Error en avance",
                    f"AW=0 pero Validación % (AY={ay}%) es menor que Avance anterior (AX={ax}%)"
                ))

    return errors


def rule_progress_90_empty_ranges(row: pd.Series, df: pd.DataFrame) -> List[ValidationResult]:
    """When AC (avance al corte) >= 90, AE to AU must be empty except for GRAY_COLUMNS.
    AV (Comentarios del auditor) is explicitly allowed to have data."""
    avance_corte = _num(row, "Porcentaje avance al corte")
    if np.isnan(avance_corte) or avance_corte < 90:
        return []

    # Map AE to AU column names
    # AE: Periodo seguimiento
    # AF: Nombre Auditor (quien realiza seguimiento)
    # AG: Fecha de seguimiento por parte del auditor externo
    # AH: Evidencia de Seguimiento
    # AI: Pertinencia
    # AJ: Cantidad de Soportes cargados por la Dependencia
    # AK: Suficiencia de Soportes
    # AL: No. de entregables asociados a la Actividad
    # AM: Cantidad entregables presentados
    # AN: Tipo de Error
    # AO: Identificación de posibles errores (Cualitativo)
    # AP: No. De entregables pendientes (GREY)
    # AQ: Porcentaje de avance de los entregables (GREY)
    # AR: Calificación Parcial (GREY)
    # AS: Oportunidad (GREY)
    # AT: Porcentaje avance periodo evaluado (GREY)
    # AU: Enlace evidencia del seguimiento
    
    range_cols = [
        "Periodo seguimiento",
        "Nombre Auditor (quien realiza seguimiento)",
        "Fecha de seguimiento por parte del auditor externo",
        "Evidencia de Seguimiento",
        "Pertinencia",
        "Cantidad de Soportes cargados por la Dependencia",
        "Suficiencia de Soportes",
        "No. de entregables asociados a la Actividad",
        "Cantidad entregables presentados",
        "Tipo de Error",
        "Identificación de posibles errores (Cualitativo)",
        "No. De entregables pendientes",
        "Porcentaje de avance de los entregables",
        "Calificación Parcial",
        "Oportunidad",
        "Porcentaje avance periodo evaluado",
        "Enlace evidencia del seguimiento"
    ]

    errors = []
    for col in range_cols:
        # If the column name is NOT in GRAY_COLUMNS (it's a 'white' column that must be empty)
        if col not in GRAY_COLUMNS:
            val = _val(row, col)
            if val and val.lower() not in ("nan", "none", ""):
                errors.append(ValidationResult(
                    False, "Inconsistencia en actividad terminada",
                    f"Avance al corte (AC={avance_corte}%) >= 90%, pero la columna '{col}' no está vacía (contiene: {_display(val)})"
                ))
    
    # AV: Comentarios del auditor (MUST have a comment if AC >= 90)
    av_col = "Comentarios del auditor"
    av_val = _val(row, av_col)
    if not av_val or av_val.lower() in ("nan", "none", ""):
        errors.append(ValidationResult(
            False, "Falta comentario",
            f"Avance al corte (AC={avance_corte}%) >= 90%, por lo tanto la columna '{av_col}' debe contener el comentario final del auditor."
        ))
    else:
        # C28 style: check for keywords "completada" or "cumplida"
        comment_low = av_val.lower()
        if "completada" not in comment_low and "cumplida" not in comment_low:
            errors.append(ValidationResult(
                False, "Coherencia de comentario",
                f"Avance al corte (AC={avance_corte}%) >= 90%, el comentario en '{av_col}' debe incluir 'completada' o 'cumplida."
            ))

    return errors
