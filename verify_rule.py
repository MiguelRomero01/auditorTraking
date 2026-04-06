import pandas as pd
import numpy as np
from app.analytics.rules.logic import rule_supply_no_requires_zero_values

def test_rule():
    col_as = "Fecha de Elaboración o Formalización del Entregable evaluado Oportunidad"
    # Test cases: (Supply, Soportes, Entregables, AS_Val, ExpectedErrors)
    test_cases = [
        ("NO", 0, 0, "No aplica", 0),       # OK
        ("NO", 0, 0, "NO APLICA", 0),       # OK (Case insensitive)
        ("NO", 1, 0, "No aplica", 1),       # Error in Soportes
        ("NO", 0, 0, "2024-03-01", 1),      # Error in AS (Oportunidad)
        ("NO", 5, 2, "2024-03-01", 3),      # All three errors
    ]
    
    for i, (supply, soportes, entregables, val_as, expected) in enumerate(test_cases):
        row = pd.Series({
            "¿La dependencia suministro información?": supply,
            "Cantidad de Soportes cargados por la Dependencia": soportes,
            "No. de entregables asociados a la Actividad": entregables,
            col_as: val_as
        }, index=["¿La dependencia suministro información?", 
                  "Cantidad de Soportes cargados por la Dependencia", 
                  "No. de entregables asociados a la Actividad", 
                  col_as])
        results = rule_supply_no_requires_zero_values(row, None)
        errors = [r for r in results if not r.is_valid]
        
        if len(errors) == expected:
            print(f"Test case {i+1} PASSED")
        else:
            print(f"Test case {i+1} FAILED: Expected {expected} errors, got {len(errors)}")
            for e in errors:
                print(f"  Error: {e.message}")

if __name__ == "__main__":
    test_rule()
