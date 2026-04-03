from .basic import (
    rule_empty_cells,
    rule_unique_llave,
    rule_percentages_max_100,
    rule_url_evidence,
    rule_month_name,
    rule_auditor_initials,
    rule_followup_date
)
from .logic import (
    rule_evidence_supply_logic,
    rule_supply_si_requires_soportes,
    rule_soportes_vs_entregables,
    rule_suficiente_no_consistency,
    rule_entregables_vs_cantidad,
    rule_progress_comparison,
    rule_followup_at_90,
    rule_validacion_vs_avance_anterior,
    rule_progress_90_empty_ranges,
)
# C28: rule_comment_coherence is DISABLED pending keyword review
# from .coherence import rule_comment_coherence

ALL_RULES = [
    rule_empty_cells,
    rule_unique_llave,
    rule_percentages_max_100,
    rule_url_evidence,
    rule_month_name,
    rule_auditor_initials,
    rule_followup_date,
    rule_evidence_supply_logic,
    rule_supply_si_requires_soportes,
    rule_soportes_vs_entregables,
    rule_suficiente_no_consistency,
    rule_entregables_vs_cantidad,
    rule_progress_comparison,
    rule_followup_at_90,           # C3: AC>=90 -> AD must be "NO"
    rule_validacion_vs_avance_anterior,  # C7: AW vs AX, AY vs AX when AW=0
    rule_progress_90_empty_ranges, # AC>=90 -> AE-AU must be empty
    # rule_comment_coherence,     # C28: DISABLED
]
