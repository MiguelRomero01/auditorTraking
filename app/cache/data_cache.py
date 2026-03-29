import time
from typing import Any, Optional, Dict
import pandas as pd

class DataCache:
    _instance = None
    _cached_data: Optional[Dict[str, Any]] = None
    _last_updated: float = 0
    _raw_df: Optional[pd.DataFrame] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataCache, cls).__new__(cls)
        return cls._instance

    def get_data(self) -> Optional[Dict[str, Any]]:
        return self._cached_data

    def set_data(self, data: Dict[str, Any], raw_df: pd.DataFrame):
        self._cached_data = data
        self._raw_df = raw_df
        self._last_updated = time.time()

    def is_empty(self) -> bool:
        return self._cached_data is None

    def last_updated_str(self) -> str:
        if self._last_updated == 0:
            return "Nunca"
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self._last_updated))

data_cache = DataCache()
