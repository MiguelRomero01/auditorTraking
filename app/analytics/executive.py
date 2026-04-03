import pandas as pd
import numpy as np
import re
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from app.utils.helpers import _val, _num, find_column_fuzzy, VALID_MONTH_NAMES
from app.analytics.rules import ALL_RULES
from app.analytics.models import ValidationResult

logger = logging.getLogger(__name__)


ERROR_TYPE_LABELS = {
    "ID Duplicado": "ID Duplicado",
    "Celdas vacías": "Celda Vacía",
    "Error en avance": "Avance Inválido",
    "Enlaces dañados": "Enlace Inválido",
    "Error en mes": "Mes Incorrecto",
    "Error en Nombre": "Nombre Auditor",
    "Error en Fecha": "Fecha Inválida",
    "Error en entregable": "Error Entregable",
    "Errores en base de datos": "Inconsistencia BD",
    "Coherencia de comentario": "Comentario Incoherente",
}


def build_executive_report(df: pd.DataFrame, processed_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Builds a rich per-auditor executive report dict from the raw DataFrame
    and the already-computed processed_data dict.
    """
    if df is None or df.empty:
        return {"auditors": [], "global": {}}

    df = df.replace('', np.nan)

    all_errors = processed_data.get("error_list", [])
    per_auditor_raw = processed_data.get("per_auditor_data", {})
    auditor_load = processed_data.get("auditors", {})
    progress_col = find_column_fuzzy(df, "Porcentaje avance al corte")

    auditors_report = []

    for auditor_name in sorted(auditor_load.keys()):
        a_df = df[df["Auditor_Sheet"] == auditor_name]
        a_errs = [e for e in all_errors if e["auditor"] == auditor_name]
        a_info = per_auditor_raw.get(auditor_name, {})

        # --- Progress ---
        avg_progress = a_info.get("progress", 0)
        if progress_col and progress_col in a_df.columns:
            prog_series = pd.to_numeric(
                a_df[progress_col].astype(str).str.replace("%", ""), errors="coerce"
            ).fillna(0)
            avg_progress = round(prog_series.mean(), 1)
            progress_dist = _progress_distribution(prog_series)
        else:
            progress_dist = {"0-25": 0, "26-50": 0, "51-75": 0, "76-99": 0, "100": 0}

        # --- Errors breakdown ---
        error_type_dist: Dict[str, int] = {}
        for e in a_errs:
            label = ERROR_TYPE_LABELS.get(e["type"], e["type"])
            error_type_dist[label] = error_type_dist.get(label, 0) + 1

        # --- Observation groups ---
        obs_col = find_column_fuzzy(a_df, "ID Observacion")
        obs_ids = a_df[obs_col].dropna().unique() if obs_col else []
        total_observations = len(obs_ids)

        action_col = find_column_fuzzy(a_df, "ID Acción")
        action_ids = a_df[action_col].dropna().unique() if action_col else []
        total_actions = len(action_ids)

        # --- Coherence errors ---
        coherence_errors = [e for e in a_errs if "Coherencia" in e.get("type", "") or "Comentario" in e.get("type", "")]
        coherence_count = len(coherence_errors)

        # --- Summary error list (top 50 per auditor) ---
        error_detail = []
        for e in a_errs[:50]:
            error_detail.append({
                "row": e.get("row_index", ""),
                "type": ERROR_TYPE_LABELS.get(e.get("type", ""), e.get("type", "")),
                "message": e.get("message", ""),
                "month": e.get("month", "Sin mes"),
            })

        # --- Errors by month ---
        errors_by_month: Dict[str, int] = {}
        for e in a_errs:
            m = e.get("month", "Sin mes")
            errors_by_month[m] = errors_by_month.get(m, 0) + 1

        # --- Work items: top observations with most errors ---
        obs_error_map = {}
        obs_title_col = find_column_fuzzy(a_df, "Título del Observacion")
        for e in a_errs:
            row_num = e.get("row_index")
            # find obs id for this row
            matching = a_df[a_df["Sheet_Row"] == row_num]
            if not matching.empty and obs_col:
                obs_id = _val(matching.iloc[0], obs_col)
                if obs_title_col:
                    obs_title = _val(matching.iloc[0], obs_title_col)
                else:
                    obs_title = obs_id
                key = f"{obs_id} - {obs_title}" if obs_title and obs_title != obs_id else obs_id
                obs_error_map[key] = obs_error_map.get(key, 0) + 1

        top_observations = sorted(obs_error_map.items(), key=lambda x: x[1], reverse=True)[:5]

        # --- Status badge ---
        rows_with_errors = a_info.get("rows_with_errors", 0)
        total = a_info.get("total", len(a_df))
        error_rate = (rows_with_errors / total * 100) if total > 0 else 0

        if error_rate == 0:
            status = "Excelente"
            status_color = "green"
        elif error_rate < 20:
            status = "Aceptable"
            status_color = "yellow"
        elif error_rate < 50:
            status = "Con Observaciones"
            status_color = "orange"
        else:
            status = "Crítico"
            status_color = "red"

        auditors_report.append({
            "name": auditor_name,
            "total_activities": total,
            "avg_progress": avg_progress,
            "total_errors": len(a_errs),
            "rows_with_errors": rows_with_errors,
            "error_rate": round(error_rate, 1),
            "total_observations": total_observations,
            "total_actions": total_actions,
            "coherence_errors": coherence_count,
            "status": status,
            "status_color": status_color,
            "error_type_dist": error_type_dist,
            "errors_by_month": errors_by_month,
            "progress_dist": progress_dist,
            "top_observations": [{"label": k, "count": v} for k, v in top_observations],
            "error_detail": error_detail,
        })

    # --- Global summary ---
    global_summary = processed_data.get("summary", {})
    total_auditors = len(auditors_report)
    critical = sum(1 for a in auditors_report if a["status_color"] == "red")
    with_obs = sum(1 for a in auditors_report if a["status_color"] == "orange")
    clean = sum(1 for a in auditors_report if a["status_color"] == "green")

    return {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "global": {
            "total_auditors": total_auditors,
            "total_activities": global_summary.get("total_activities", 0),
            "avg_progress": global_summary.get("avg_progress", 0),
            "total_errors": global_summary.get("activities_with_errors", 0),
            "clean_activities": global_summary.get("clean_activities", 0),
            "critical_count": critical,
            "with_obs_count": with_obs,
            "clean_count": clean,
        },
        "auditors": auditors_report,
    }


def _progress_distribution(series: pd.Series) -> Dict[str, int]:
    dist = {"0-25": 0, "26-50": 0, "51-75": 0, "76-99": 0, "100": 0}
    for v in series:
        if pd.isna(v): continue
        if v <= 25: dist["0-25"] += 1
        elif v <= 50: dist["26-50"] += 1
        elif v <= 75: dist["51-75"] += 1
        elif v < 100: dist["76-99"] += 1
        else: dist["100"] += 1
    return dist
