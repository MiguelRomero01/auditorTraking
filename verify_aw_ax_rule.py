import pandas as pd
import numpy as np
from app.analytics.rules.logic import rule_progress_comparison, rule_validacion_vs_avance_anterior

def test_aw_ax_rules():
    print("Testing AW vs AX rules (C6 and C7)...")
    
    # Test cases: (AW, AX, AC, ExpectedErrors_C6, ExpectedErrors_C7)
    test_cases = [
        (0, 10, 50, 0, 0),    # AW=0 is valid (even if AX=10)
        (15, 10, 50, 0, 0),   # AW > AX is valid
        (10, 10, 50, 0, 0),   # AW = AX is valid
        (5, 10, 50, 1, 1),    # AW < AX and AW!=0 is INVALID
        (0, 0, 50, 0, 0),     # AW=0, AX=0 is valid
        (5, 10, 95, 0, 1),    # C6 should skip if AC >= 90, but C7 still checks
    ]
    
    for i, (aw, ax, ac, exp_c6, exp_c7) in enumerate(test_cases):
        row = pd.Series({
            "Porcentaje avance periodo evaluado": aw,
            "Porcentaje avance anterior": ax,
            "Porcentaje avance al corte": ac
        })
        
        # Add Validation % (AY) if needed for C7 (though we are focused on AW vs AX)
        row["Validación %"] = 100 

        res_c6 = rule_progress_comparison(row, None)
        err_c6 = [r for r in res_c6 if not r.is_valid]
        
        res_c7 = rule_validacion_vs_avance_anterior(row, None)
        err_c7 = [r for r in res_c7 if not r.is_valid]
        
        passed = True
        if len(err_c6) != exp_c6:
            print(f"FAIL C6: Case {i+1} Expected {exp_c6}, got {len(err_c6)}")
            passed = False
        if len(err_c7) != exp_c7:
            print(f"FAIL C7: Case {i+1} Expected {exp_c7}, got {len(err_c7)}")
            passed = False
        
        if passed:
            print(f"PASS: Case {i+1} (AW={aw}, AX={ax}, AC={ac})")

if __name__ == "__main__":
    test_aw_ax_rules()
