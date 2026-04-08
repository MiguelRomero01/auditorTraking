from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from app.services.sheets_service import sheets_service
from app.services.loader_service import loader_service
from app.analytics.processor import processor
from app.cache.data_cache import data_cache
import logging
from typing import Dict, Any, Optional
import pandas as pd
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "Audit Dashboard API"}

@router.get("/status")
async def get_status():
    """Returns the current data source status"""
    return {
        "is_loaded": not data_cache.is_empty(),
        "source": data_cache.metadata.get("source", "None"),
        "last_updated": data_cache.last_updated_str() if not data_cache.is_empty() else None,
        "filename": data_cache.metadata.get("filename")
    }

@router.get("/data")
async def get_data():
    """Returns analytics data (from cache). Does NOT auto-fetch if empty to allow Landing Page."""
    if data_cache.is_empty():
        return {"is_loaded": False, "message": "No hay datos cargados. Por favor selecciona una fuente."}
    
    return data_cache.get_data()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """Handles XLSX file upload"""
    if not file.filename.lower().endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Solo se permiten archivos Excel (.xlsx, .xls)")
    
    try:
        content = await file.read()
        df = await loader_service.load_from_xlsx(content)
        
        if df.empty:
            raise HTTPException(status_code=400, detail="El archivo está vacío o no tiene el formato esperado")
            
        processed_data = processor.process(df)
        data_cache.set_data(processed_data, df)
        data_cache.metadata["source"] = "upload"
        data_cache.metadata["filename"] = file.filename
        
        return {"status": "success", "message": f"Archivo '{file.filename}' cargado correctamente"}
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/load-link")
async def load_link(url: str = Form(...)):
    """Handles loading from a Google Sheets link"""
    try:
        df = await loader_service.load_from_google_sheets(url)
        processed_data = processor.process(df)
        data_cache.set_data(processed_data, df)
        data_cache.metadata["source"] = "google_link"
        data_cache.metadata["url"] = url
        
        return {"status": "success", "message": "Datos cargados desde el link correctamente"}
    except Exception as e:
        logger.error(f"Link load failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al cargar el link: {str(e)}")

@router.post("/refresh")
async def refresh_data():
    """Forces a refresh of the data from the current source if possible"""
    source = data_cache.metadata.get("source")
    
    try:
        if source == "google_link":
            url = data_cache.metadata.get("url")
            df = await loader_service.load_from_google_sheets(url)
        elif source == "upload":
            raise HTTPException(status_code=400, detail="No se puede refrescar un archivo cargado manualmente. Por favor cárgalo de nuevo.")
        else:
            # Default to predefined
            df = await loader_service.load_from_google_sheets()
            data_cache.metadata["source"] = "predefined"

        processed_data = processor.process(df)
        data_cache.set_data(processed_data, df)
        
        return {"status": "success", "message": "Datos actualizados", "timestamp": data_cache.last_updated_str()}
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Refresh failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al refrescar: {str(e)}")

@router.post("/reset")
async def reset_data():
    """Clears the current data cache and force show landing page"""
    data_cache.clear()
    return {"status": "success", "message": "Sesión reiniciada"}

from fastapi.responses import StreamingResponse
import io

@router.get("/export/findings")
async def export_findings(auditor: Optional[str] = None):
    """Exports findings to Excel, splitting by auditor into different sheets if 'all' is selected."""
    if data_cache.is_empty():
        raise HTTPException(status_code=400, detail="No hay datos cargados")
    
    data = data_cache.get_data()
    all_errors = data.get("error_list", [])
    
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        if auditor and auditor != "all":
            # Single auditor export
            errors = [e for e in all_errors if e["auditor"] == auditor]
            export_list = [{
                "Fila": e["row_index"],
                "Auditor": e["auditor"],
                "Tipo Error": e["type"],
                "Descripción / Observación": e["message"]
            } for e in errors]
            
            df = pd.DataFrame(export_list)
            # Empty check
            if df.empty:
                df = pd.DataFrame(columns=["Fila", "Auditor", "Tipo Error", "Descripción / Observación"])
            
            df.to_excel(writer, index=False, sheet_name=f"Hallazgos_{auditor}")
        else:
            # Multi-auditor export: one sheet per auditor
            auditors = sorted(list(set(e["auditor"] for e in all_errors)))
            
            if not auditors:
                 # If no errors at all, create one empty sheet
                 pd.DataFrame(columns=["Fila", "Auditor", "Tipo Error", "Descripción / Observación"]).to_excel(writer, index=False, sheet_name="Sin Hallazgos")
            else:
                for a_name in auditors:
                    errors = [e for e in all_errors if e["auditor"] == a_name]
                    export_list = [{
                        "Fila": e["row_index"],
                        "Auditor": e["auditor"],
                        "Tipo Error": e["type"],
                        "Descripción / Observación": e["message"]
                    } for e in errors]
                    
                    df = pd.DataFrame(export_list)
                    # Sheet names must be <= 31 chars
                    sheet_name = str(a_name)[:31]
                    df.to_excel(writer, index=False, sheet_name=sheet_name)

    output.seek(0)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M')
    auditor_label = auditor if auditor and auditor != 'all' else 'Global'
    filename = f"Hallazgos_{auditor_label}_{timestamp}.xlsx"
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Access-Control-Expose-Headers": "Content-Disposition"
        }
    )


