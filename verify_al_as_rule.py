import pandas as pd
import numpy as np
from app.analytics.rules.logic import rule_al_zero_requires_as_no_aplica

def test_al_as_rule():
    print("Testing rule_al_zero_requires_as_no_aplica...")
    col_as = "Fecha de Elaboración o Formalización del Entregable evaluado Oportunidad"
    col_al = "No. de entregables asociados a la Actividad"
    
    # Test cases: (AL, AS_Val, ExpectedErrors)
    test_cases = [
        (0, "No aplica", 0),       # OK
        (0, "NO APLICA", 0),       # OK (Case insensitive)
        (0, "2024-03-01", 1),      # Error: AS has a date
        (1, "2024-03-01", 0),      # OK: AL is not 0
        (0, "", 1),                # Error: AS is empty (must say No aplica)
        (0, "N/A", 1),             # Error: Not exactly "No aplica"
        (float('nan'), "2024-03-01", 0), # OK: AL is nan (not 0)
        (0, "no aplica ", 0),      # OK: Trimming handled by _val
    ]
    
    for i, (al, val_as, expected) in enumerate(test_cases):
        row = pd.Series({
            col_al: al,
            col_as: val_as
        })
        results = rule_al_zero_requires_as_no_aplica(row, None)
        errors = [r for r in results if not r.is_valid]
        
        if len(errors) == expected:
            print(f"  Test case {i+1} PASSED (AL={al}, AS='{val_as}')")
        else:
            print(f"  Test case {i+1} FAILED: Expected {expected} errors, got {len(errors)} (AL={al}, AS='{val_as}')")
            for e in errors:
                print(f"    Error: {e.message}")

if __name__ == "__main__":
    test_al_as_rule()
