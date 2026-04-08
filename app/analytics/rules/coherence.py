import pandas as pd
import re
from typing import List
from app.analytics.models import ValidationResult
from app.utils.helpers import _val

# 1. Contradiction Map: If rating is X, these words are FORBIDDEN in AV.
# Tuples: (regex_pattern, display_name)
_FORBIDDEN_WORDS_MAP = {
    "inoportun": [
        (r"\boportuna\b", "oportuna"), 
        (r"\boportunidad\b", "oportunidad")
    ],
    "insuficiente": [
        (r"\bsuficiente\b", "suficiente")
    ],
    "parcialmente adecuado": [
        (r"(?<!parcialmente\s+)\badecuada\b", "adecuada"), 
        (r"(?<!parcialmente\s+)\badecuado\b", "adecuado"), 
        (r"\bno adecuada\b", "no adecuada"), 
        (r"\bno adecuado\b", "no adecuado")
    ],
}

# 2. Requirement Map (Currently empty per user feedback)
_REQUIRED_PHRASES = {}

def rule_comment_coherence(row: pd.Series, df: pd.DataFrame) -> List[ValidationResult]:
    """C28: Coherence check between AR (Rating) and AV (Comment).
    - Checks for contradictions (e.g. Inoportuna vs Oportuna).
    - Checks for mandatory mentions (e.g. Parcialmente Adecuado)."""

    av_val = _val(row, "Comentarios del auditor").lower()
    if not av_val:
        av_val = _val(row, "Comentarios del Auditor").lower()
    
    if not av_val or av_val.lower() in ("nan", "none", ""):
        return []

    errors = []

    # Search for column AR: Calificacion or Oportunidad (not Fecha)
    ar_candidates = [
        c for c in row.index
        if (
            "calificaci" in str(c).lower() or
            ("oportunidad" in str(c).lower() and "fecha" not in str(c).lower())
        )
    ]

    for ar_col in ar_candidates:
        ar_val = _val(row, ar_col).strip()
        if not ar_val:
            continue

        ar_lower = ar_val.lower()

        # Check for contradictions
        if "inoportun" in ar_lower:
            for pattern, name in _FORBIDDEN_WORDS_MAP["inoportun"]:
                if re.search(pattern, av_val, re.IGNORECASE):
                    errors.append(ValidationResult(False, "Coherencia de comentario", f"'{ar_col}' dice '{ar_val}', pero el comentario contiene '{name}'."))
        
        if "insuficiente" in ar_lower:
            for pattern, name in _FORBIDDEN_WORDS_MAP["insuficiente"]:
                if re.search(pattern, av_val, re.IGNORECASE):
                    errors.append(ValidationResult(False, "Coherencia de comentario", f"'{ar_col}' dice '{ar_val}', pero el comentario contiene '{name}'."))
        
        if "parcialmente adecuado" in ar_lower:
            # Mask valid phrase first to allow absolute check
            masked_av = av_val.lower().replace("parcialmente adecuada", "[MASK]").replace("parcialmente adecuado", "[MASK]")
            
            # Check for absolute terms
            if re.search(r"\badecuada\b", masked_av) or re.search(r"\badecuado\b", masked_av):
                errors.append(ValidationResult(
                    False, "Coherencia de comentario", 
                    f"'{ar_col}' es Parcialmente adecuado, pero el comentario usa 'adecuada/o' de forma absoluta (sin 'parcialmente')."
                ))
            
            if re.search(r"\bno adecuada\b", masked_av) or re.search(r"\bno adecuado\b", masked_av):
                 errors.append(ValidationResult(
                    False, "Coherencia de comentario", 
                    f"'{ar_col}' es Parcialmente adecuado, pero el comentario contiene 'no adecuada/o' (contradicción absoluta)."
                ))

    return errors
