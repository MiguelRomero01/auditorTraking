import pandas as pd
import re
from typing import List
from app.analytics.models import ValidationResult
from app.utils.helpers import _val

# Map of 'Bad' ratings (fragments in AR) to 'Forbidden' positive words in AV
# We use regex word boundaries \b to ensure "inoportuna" doesn't match "oportuna".
_NEGATIVE_COHERENCE_MAP = {
    "inoportun": [r"\boportuna\b", r"\boportunidad\b"],
    "insuficiente": [r"\bsuficiente\b"],
    "no adecuada": [r"\badecuada\b"],
    "no adecuado": [r"\badecuado\b"],
}

def rule_comment_coherence(row: pd.Series, df: pd.DataFrame) -> List[ValidationResult]:
    """C28: Inverted coherence check.
    If the rating in AR is negative (Bad), the comment in AV must NOT contain
    positive words that contradict that rating."""

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
        for ar_bad_fragment, forbidden_patterns in _NEGATIVE_COHERENCE_MAP.items():
            if ar_bad_fragment in ar_lower:
                for pattern in forbidden_patterns:
                    # Search using word boundaries so "inoportuna" != hit for "oportuna"
                    if re.search(pattern, av_val, re.IGNORECASE):
                        errors.append(ValidationResult(
                            False,
                            "Coherencia de comentario",
                            f"La columna '{ar_col}' dice '{ar_val}', pero el comentario contiene '{pattern.strip(r'\\b')}', lo cual es contradictorio."
                        ))
                        break

    return errors
