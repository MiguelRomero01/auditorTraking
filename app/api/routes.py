from fastapi import APIRouter, HTTPException, Depends
from app.services.sheets_service import sheets_service
from app.analytics.processor import processor
from app.cache.data_cache import data_cache
import logging
from typing import Dict, Any

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "Audit Dashboard API"}

import time

@router.get("/data")
async def get_data():
    """Returns analytics data (from cache or fetching if empty)"""
    start_time = time.perf_counter()
    
    if data_cache.is_empty():
        logger.info("[PERF] Cache empty, fetching from Google Sheets...")
        try:
             fetch_start = time.perf_counter()
             df = await sheets_service.fetch_all_data()
             fetch_end = time.perf_counter()
             logger.info(f"[PERF] Fetching from Sheets took {fetch_end - fetch_start:.4f} seconds")
             
             processed_data = processor.process(df)
             data_cache.set_data(processed_data, df)
        except Exception as e:
            logger.error(f"Error fetching data: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    response = data_cache.get_data()
    end_time = time.perf_counter()
    logger.info(f"[PERF] Total /api/data request took {end_time - start_time:.4f} seconds")
    return response

@router.post("/refresh")
async def refresh_data():
    """Forces a refresh of the data from Google Sheets"""
    start_time = time.perf_counter()
    logger.info("Force refresh triggered")
    try:
        df = await sheets_service.fetch_all_data()
        processed_data = processor.process(df)
        data_cache.set_data(processed_data, df)
        
        end_time = time.perf_counter()
        logger.info(f"[PERF] Refresh request completed in {end_time - start_time:.4f} seconds")
        
        return {"status": "success", "message": "Datos actualizados", "timestamp": data_cache.last_updated_str()}
    except Exception as e:
        logger.error(f"Refresh failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al refrescar datos: {str(e)}")
