import pandas as pd
import numpy as np
import logging
import time
import re
from typing import List, Dict, Any
from datetime import datetime
from app.utils.helpers import (
    _val, find_column_fuzzy, VALID_MONTH_NAMES
)
from app.analytics.models import ValidationResult
from app.analytics.rules import ALL_RULES

logger = logging.getLogger(__name__)

class DataProcessor:
    def __init__(self):
        self.rules = list(ALL_RULES)

    def process(self, df: pd.DataFrame) -> Dict[str, Any]:
        start_time = time.perf_counter()
        if df.empty:
            return self._empty_response()

        # Replace empty strings with NaN for consistent handling
        df = df.replace('', np.nan)

        all_errors: List[Dict[str, Any]] = []
        # Support for rows without auditor
        auditor_names = df["Auditor_Sheet"].unique()
        auditor_errors: Dict[str, int] = {str(a): 0 for a in auditor_names}

        for index, row in df.iterrows():
            for rule in self.rules:
                try:
                    results = rule(row, df)
                except Exception as e:
                    logger.warning(f"Rule {rule.__name__} failed on row {index}: {e}")
                    continue
                for res in results:
                    if not res.is_valid:
                        auditor_name = str(row.get("Auditor_Sheet", "Unknown"))
                        original_month = _val(row, "Periodo seguimiento").capitalize()
                        
                        # Extract year from "ID" column (fuzzy find)
                        id_val = _val(row, "ID")
                        year_match = re.search(r"20[2-9][0-9]", id_val)
                        year_suffix = f" {year_match.group(0)}" if year_match else ""
                        
                        # Normalization for group chart: if not a real month, it's "Sin mes"
                        month_val = original_month if original_month in VALID_MONTH_NAMES else "Sin mes"
                        month_label = f"{month_val}{year_suffix}"
                        
                        all_errors.append({
                            "row_index": int(row.get("Sheet_Row", index + 1)),
                            "type": res.error_type,
                            "message": res.message,
                            "auditor": auditor_name,
                            "month": month_label,
                        })
                        auditor_errors[auditor_name] = auditor_errors.get(auditor_name, 0) + 1

        # --- Summary calculations ---
        total_activities = len(df)
        rows_with_errors = len(set((e["auditor"], e["row_index"]) for e in all_errors))
        total_error_count = len(all_errors)

        auditor_load = df.groupby("Auditor_Sheet").size().to_dict()

        # --- C8: Activities where AC (avance al corte) >= 90 ---
        progress_90_count = 0
        # --- C9: Activities with entregable (AL No. de entregables asociados a la Actividad > 0) ---
        entregable_col = find_column_fuzzy(df, "No. de entregables asociados a la Actividad")

        # Progress — now calculated as (clean_activities / total_activities * 100)
        avg_progress = (
            (total_activities - rows_with_errors) / total_activities * 100
            if total_activities > 0
            else 0
        )
        progress_col = find_column_fuzzy(df, "Porcentaje avance al corte")
        if progress_col:
            df[progress_col] = pd.to_numeric(
                df[progress_col].astype(str).str.replace("%", ""), errors="coerce"
            ).fillna(0)
            progress_90_count = int((df[progress_col] >= 90).sum())
        else:
            logger.warning("Column 'Porcentaje avance al corte' not found in data")

        activities_with_entregable = 0
        if entregable_col:
            entregable_series = pd.to_numeric(
                df[entregable_col].astype(str).str.replace("%", ""), errors="coerce"
            ).fillna(0)
            activities_with_entregable = int((entregable_series > 0).sum())

        # Error type distribution
        error_type_dist: Dict[str, int] = {}
        for e in all_errors:
            error_type_dist[e["type"]] = error_type_dist.get(e["type"], 0) + 1

        # Per-auditor detail
        per_auditor_data: Dict[str, Dict[str, Any]] = {}
        for auditor in auditor_names:
            auditor_str = str(auditor)
            a_df = df[df["Auditor_Sheet"] == auditor]
            a_errs = [e for e in all_errors if e["auditor"] == auditor_str]
            a_rows_with_errors = len(set(e["row_index"] for e in a_errs))
            a_total_errors = len(a_errs)

            a_avg_progress = (
                (len(a_df) - a_rows_with_errors) / len(a_df) * 100
                if len(a_df) > 0
                else 0
            )

            a_with_entregable = 0
            if entregable_col and entregable_col in a_df.columns:
                a_entregable_series = pd.to_numeric(
                    a_df[entregable_col].astype(str).str.replace("%", ""), errors="coerce"
                ).fillna(0)
                a_with_entregable = int((a_entregable_series > 0).sum())

            a_at90 = 0
            if progress_col and progress_col in a_df.columns:
                a_at90 = int((a_df[progress_col] >= 90).sum())

            per_auditor_data[auditor_str] = {
                "total": len(a_df),
                "errors": a_total_errors,
                "rows_with_errors": a_rows_with_errors,
                "progress": round(a_avg_progress, 2),
                "activities_with_entregable": a_with_entregable,
                "activities_at_90_plus": a_at90,
            }

        response = {
            "summary": {
                "total_activities": total_activities,
                "activities_with_errors": total_error_count,
                "rows_with_errors": rows_with_errors,
                "clean_activities": total_activities - rows_with_errors,
                "avg_progress": round(avg_progress, 2),
                # C5: error rate
                "error_rate_pct": round((rows_with_errors / total_activities * 100), 1) if total_activities > 0 else 0,
                # C8: activities at or above 90% progress
                "activities_at_90_plus": progress_90_count,
                # C9: activities that have at least 1 entregable (AJ > 0)
                "activities_with_entregable": activities_with_entregable,
                "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            "auditors": {str(k): v for k, v in auditor_load.items()},
            "errors_by_auditor": auditor_errors,
            "errors_by_type": error_type_dist,
            "per_auditor_data": per_auditor_data,
            "error_list": all_errors,
            "columns": list(df.columns),
        }

        end_time = time.perf_counter()
        logger.info(f"Data processing completed in {end_time - start_time:.4f} seconds")
        return response

    def _empty_response(self) -> Dict[str, Any]:
        return {
            "summary": {
                "total_activities": 0,
                "activities_with_errors": 0,
                "rows_with_errors": 0,
                "clean_activities": 0,
                "avg_progress": 0,
                "error_rate_pct": 0,
                "activities_at_90_plus": 0,
                "activities_with_entregable": 0,
                "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            },
            "auditors": {},
            "errors_by_auditor": {},
            "errors_by_type": {},
            "per_auditor_data": {},
            "error_list": [],
            "columns": [],
        }

processor = DataProcessor()
