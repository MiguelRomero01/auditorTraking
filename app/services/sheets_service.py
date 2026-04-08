import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import logging
import time
import os
import re
import asyncio
from typing import List, Dict, Any, Optional
from app.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleSheetsService:
    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GoogleSheetsService, cls).__new__(cls)
        return cls._instance

    def _get_client(self):
        if self._client is None:
            scopes = [
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive"
            ]
            if not os.path.exists(settings.GOOGLE_CREDENTIALS_PATH):
                logger.error(f"Credentials file not found: {settings.GOOGLE_CREDENTIALS_PATH}")
                raise FileNotFoundError(f"No se encontró el archivo de credenciales en {settings.GOOGLE_CREDENTIALS_PATH}")
            
            try:
                creds = Credentials.from_service_account_file(settings.GOOGLE_CREDENTIALS_PATH, scopes=scopes)
                self._client = gspread.authorize(creds)
                logger.info("Successfully authenticated with Google Sheets API")
            except Exception as e:
                logger.error(f"Authentication failed: {str(e)}")
                raise Exception(f"Error de autenticación con Google: {str(e)}")
        return self._client

    def _extract_id(self, input_str: str) -> str:
        """Extracts the sheet ID from a full URL or returns the ID as is"""
        if not input_str: return ""
        # Matches patterns like /d/ID/ or just the ID
        match = re.search(r'/d/([a-zA-Z0-9-_]+)', input_str)
        if match:
            return match.group(1)
        # Fallback: if there is a slash, take the part before it
        return input_str.split('/')[0].strip()

    async def fetch_all_data(self, sheet_id_or_url: Optional[str] = None) -> pd.DataFrame:
        client = await asyncio.to_thread(self._get_client)
        raw_id = sheet_id_or_url or settings.GOOGLE_SHEET_ID
        if not raw_id:
            raise Exception("No se proporcionó un ID o URL del documento")
            
        target_id = self._extract_id(raw_id)
        
        try:
            logger.info(f"Fetching data from Google Sheet: {target_id} (Parallel Mode)")
            spreadsheet = await asyncio.to_thread(client.open_by_key, target_id)
            all_sheets = await asyncio.to_thread(spreadsheet.worksheets)
            
            # Create tasks for all sheets to fetch in parallel
            tasks = [asyncio.to_thread(self._fetch_single_sheet, sheet) for sheet in all_sheets]
            results = await asyncio.gather(*tasks)
            
            # Filter out None results
            all_data_frames = [df for df in results if df is not None and not df.empty]
            
            if not all_data_frames:
                return pd.DataFrame()
                
            return pd.concat(all_data_frames, ignore_index=True, sort=False)
            
        except Exception as e:
            logger.error(f"Failed to open/fetch spreadsheet {target_id}: {str(e)}")
            raise Exception(f"No se pudo acceder al Spreadsheet ID '{target_id}': {str(e)}")

    def _fetch_single_sheet(self, sheet) -> Optional[pd.DataFrame]:
        sheet_start = time.perf_counter()
        header_row = 12 if sheet.title == "ARS" else 10
        try:
            values = sheet.get_all_values()
            if len(values) < header_row: return None
            
            headers = values[header_row - 1]
            data = values[header_row:]
            if not any(headers): return None
            
            unique_headers = self._make_unique_headers(headers)
            df = pd.DataFrame(data, columns=unique_headers)
            
            # Strip whitespace
            df = df.map(lambda x: x.strip() if isinstance(x, str) else x)
            
            # Metadata
            df["Sheet_Row"] = range(header_row + 1, header_row + 1 + len(df))
            df["Auditor_Sheet"] = sheet.title
            
            sheet_end = time.perf_counter()
            logger.info(f"[PERF] Loaded {len(df)} rows from '{sheet.title}' in {sheet_end - sheet_start:.4f} seconds")
            return df
        except Exception as e:
            logger.error(f"Error fetching sheet {sheet.title}: {str(e)}")
            return None

    def _make_unique_headers(self, headers: List[str]) -> List[str]:
        """Makes a list of headers unique by appending suffixes to duplicates"""
        unique_headers = []
        counts = {}
        for h in headers:
            if not h: h = "Unnamed"
            if h in counts:
                counts[h] += 1
                unique_headers.append(f"{h}.{counts[h]}")
            else:
                counts[h] = 0
                unique_headers.append(h)
        return unique_headers

sheets_service = GoogleSheetsService()
