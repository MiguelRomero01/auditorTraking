import pandas as pd
import io
import logging
from typing import Optional, Dict, Any
from app.services.sheets_service import sheets_service

logger = logging.getLogger(__name__)

class DataLoaderService:
    def __init__(self):
        pass

    async def load_from_xlsx(self, file_content: bytes) -> pd.DataFrame:
        """Parses an XLSX file and returns a unified DataFrame."""
        try:
            # Read all sheets from the XLSX
            xl = pd.ExcelFile(io.BytesIO(file_content))
            all_dfs = []
            
            for sheet_name in xl.sheet_names:
                # Basic read to find headers
                # We follow the same logic as sheets_service: header is at row 10 (or 12 for ARS)
                header_row = 12 if sheet_name == "ARS" else 10
                
                # Load data starting from header_row
                df_sheet = pd.read_excel(xl, sheet_name=sheet_name, header=header_row-1)
                
                if df_sheet.empty:
                    continue
                
                # Cleanup headers
                df_sheet.columns = [str(c).strip() for c in df_sheet.columns]

                # --- PERCENTAGE NORMALIZATION ---
                # Excel stores percentage-formatted cells as decimals (e.g., 90% -> 0.9).
                # Google Sheets returns them as strings "90%". Rules compare against 0-100 scale.
                # We detect percentage columns by checking if their numeric max is <= 1.5
                # (a valid percentage would never be 0.9 naturally in this dataset).
                PCT_KEYWORDS = [
                    "porcentaje", "avance", "validación %", "calificación"
                ]
                for col in df_sheet.columns:
                    col_lower = col.lower()
                    if any(kw in col_lower for kw in PCT_KEYWORDS):
                        numeric_series = pd.to_numeric(df_sheet[col], errors="coerce")
                        col_max = numeric_series.max()
                        if pd.notna(col_max) and col_max <= 1.5:
                            logger.info(f"[XLSX] Scaling percentage column '{col}' from decimal (max={col_max:.4f}) to 0-100")
                            df_sheet[col] = (numeric_series * 100).fillna(df_sheet[col])

                # Convert all cells to clean strings (matching gspread output format)
                for col in df_sheet.columns:
                    df_sheet[col] = df_sheet[col].apply(
                        lambda x: "" if pd.isna(x) else str(x).strip()
                    )

                df_sheet["Sheet_Row"] = range(header_row + 1, header_row + 1 + len(df_sheet))
                df_sheet["Auditor_Sheet"] = sheet_name
                
                all_dfs.append(df_sheet)

            
            if not all_dfs:
                return pd.DataFrame()
                
            return pd.concat(all_dfs, ignore_index=True, sort=False)
        except Exception as e:
            logger.error(f"Error parsing XLSX: {str(e)}")
            raise Exception(f"Error al procesar el archivo Excel: {str(e)}")

    async def load_from_google_sheets(self, sheet_id_or_url: Optional[str] = None) -> pd.DataFrame:
        """Fetches data from Google Sheets, optionally using a specific ID/URL."""
        return await sheets_service.fetch_all_data(sheet_id_or_url)

loader_service = DataLoaderService()
