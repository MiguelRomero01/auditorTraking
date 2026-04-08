import pandas as pd
import numpy as np
from app.analytics.processor import DataProcessor

def test_filtering():
    print("Testing filtering by 'Tipo' == 'Observación'...")
    
    # Create mock data with variations
    data = {
        "Auditor_Sheet": ["SKQR", "SKQR", "VMV", "VMV", "YSGF", "YSGF"],
        "Tipo": ["Observación", "Alerta ", "observacion", "Random", "Alertas", "ALERTAS"],
        "Periodo seguimiento": ["Marzo"] * 6,
        "ID": [f"2024-0{i}" for i in range(1, 7)],
        "Sheet_Row": list(range(1, 7))
    }
    df = pd.DataFrame(data)
    
    processor = DataProcessor()
    # Mocking rule_validacion_vs_avance_anterior (which is in self.rules) to do nothing
    # or just use the default ones and see the counts
    
    result = processor.process(df)
    
    total = result["summary"]["total_activities"]
    total_alertas = result["summary"]["total_alertas"]
    print(f"Total activities (Observación): {total}")
    print(f"Total alertas (Alertas): {total_alertas}")
    
    # Expected: 2 Observations ("Observación", "observacion"), 3 Alerts ("Alerta ", "Alertas", "ALERTAS")
    if total == 2 and total_alertas == 3:
        print("PASS: Robust filtering and Alertas counting are correct.")
    else:
        print(f"FAIL: Expected 2 Observation and 3 Alertas, got {total} and {total_alertas}")

    # Check auditor data
    per_auditor = result["per_auditor_data"]
    skqr_alertas = per_auditor.get("SKQR", {}).get("activities_alertas", 0)
    print(f"SKQR alerts: {skqr_alertas}")
    if skqr_alertas == 1:
        print("PASS: Per-auditor alert count is correct.")
    else:
        print(f"FAIL: SKQR expected 1 alert, got {skqr_alertas}")

if __name__ == "__main__":
    test_filtering()
