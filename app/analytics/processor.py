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
        rows_with_errors = len(set(e["row_index"] for e in all_errors))
        total_error_count = len(all_errors)

        auditor_load = df.groupby("Auditor_Sheet").size().to_dict()

        # Progress — find column with fuzzy matching
        progress_col = find_column_fuzzy(df, "Porcentaje avance al corte")
        if progress_col:
            df[progress_col] = pd.to_numeric(
                df[progress_col].astype(str).str.replace("%", ""), errors="coerce"
            ).fillna(0)
            avg_progress = df[progress_col].mean()
        else:
            avg_progress = 0
            logger.warning("Column 'Porcentaje avance al corte' not found in data")

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

            prog = 0
            if progress_col and progress_col in a_df.columns:
                prog = a_df[progress_col].mean()

            per_auditor_data[auditor_str] = {
                "total": len(a_df),
                "errors": a_total_errors,
                "rows_with_errors": a_rows_with_errors,
                "progress": round(prog, 2),
            }

        response = {
            "summary": {
                "total_activities": total_activities,
                "activities_with_errors": total_error_count,
                "rows_with_errors": rows_with_errors,
                "clean_activities": total_activities - rows_with_errors,
                "avg_progress": round(avg_progress, 2),
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
