import pandas as pd
import numpy as np
from app.analytics.rules.logic import rule_supply_no_requires_zero_values
from app.analytics.rules.basic import rule_auditor_initials

def test_rule_supply():
    print("Testing rule_supply_no_requires_zero_values...")
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
        })
        results = rule_supply_no_requires_zero_values(row, None)
        errors = [r for r in results if not r.is_valid]
        
        if len(errors) == expected:
            print(f"  Test case {i+1} PASSED")
        else:
            print(f"  Test case {i+1} FAILED: Expected {expected} errors, got {len(errors)}")
            for e in errors:
                print(f"    Error: {e.message}")

def test_rule_initials():
    print("\nTesting rule_auditor_initials...")
    col_af = "Nombre Auditor (quien realiza seguimiento)"
    # Test cases: (SheetTitle, AuditorName, ExpectedErrors)
    test_cases = [
        ("VMV", "VMV", 0),      # OK: matches
        ("VMV", "vmv", 0),      # OK: case insensitive
        ("VMV", "ABC", 1),      # Error: mismatch
        ("ARS", "ANY", 0),      # OK: ARS is skipped
        ("MJP", "", 0),         # OK: empty is handled by rule_empty_cells
        ("MJP", "MJPP", 1),     # Error: mismatch (must be exact)
        ("MJP", "MJP", 0),      # OK
        ("MJP", "M J P", 1),    # Error: mismatch (even if letters are the same)
    ]

    for i, (sheet, name, expected) in enumerate(test_cases):
        row = pd.Series({
            "Auditor_Sheet": sheet,
            col_af: name
        })
        results = rule_auditor_initials(row, None)
        errors = [r for r in results if not r.is_valid]

        if len(errors) == expected:
            print(f"  Test case {i+1} PASSED")
        else:
            print(f"  Test case {i+1} FAILED: Expected {expected} errors, got {len(errors)}")
            for e in errors:
                print(f"    Error: {e.message}")

if __name__ == "__main__":
    test_rule_supply()
    test_rule_initials()
