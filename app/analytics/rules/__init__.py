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
    rule_progress_comparison
)
from .coherence import rule_comment_coherence

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
    rule_comment_coherence
]
