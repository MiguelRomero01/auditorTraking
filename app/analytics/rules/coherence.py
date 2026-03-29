import pandas as pd
import numpy as np
from typing import List
from app.analytics.models import ValidationResult
from app.utils.helpers import _val, _num

def rule_comment_coherence(row: pd.Series, df: pd.DataFrame) -> List[ValidationResult]:
    """Rule 15: Check coherence between data and auditor comment."""
    comment = _val(row, "Comentarios del Auditor").lower()
    if not comment: return []
    errors = []
    entregables = _num(row, "No. de entregables asociados a la Actividad")
    if not np.isnan(entregables) and entregables == 0:
        keywords_no_evidence = ["no se evidencia", "no aportó", "no realizó el cargue"]
        if not any(kw in comment for kw in keywords_no_evidence):
            errors.append(ValidationResult(False, "Coherencia de comentario", "Entregables=0, pero el comentario no menciona falta de evidencias"))
    suf_candidates = [c for c in row.index if "Suficiente" in str(c)]
    if suf_candidates:
        suf = _val(row, suf_candidates[0]).upper()
        if suf == "SI":
            keywords_compliance = ["cumplimiento", "se cumplió", "cumplió"]
            if not any(kw in comment for kw in keywords_compliance):
                errors.append(ValidationResult(False, "Coherencia de comentario", "Suficiente=SI, pero el comentario no menciona cumplimiento"))
    oport_candidates = [c for c in row.index if "Oportunidad" in str(c) and "Fecha" not in str(c)]
    for oc in oport_candidates:
        op = _val(row, oc).lower()
        if "inoportuna" in op:
            if "inoportuna" not in comment and "falta de oportunidad" not in comment:
                errors.append(ValidationResult(False, "Coherencia de comentario", "Oportunidad='Inoportuna', pero el comentario no lo menciona"))
            break
    return errors
