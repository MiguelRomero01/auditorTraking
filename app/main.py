from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router as api_router
from app.config import settings
import os

app = FastAPI(title=settings.APP_TITLE)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup templates and static files
# Get the directory where main.py is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))

# Mount static files - will handle static/css/ dashboard.css etc.
app.mount("/static", StaticFiles(directory=os.path.join(BASE_DIR, "static")), name="static")

# Include API routes
app.include_router(api_router, prefix="/api", tags=["api"])

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    """Render the main dashboard HTML page"""
    return templates.TemplateResponse(
        request=request, 
        name="dashboard.html", 
        context={"title": settings.APP_TITLE}
    )

@app.get("/executive-report", response_class=HTMLResponse)
async def get_executive_report_page(request: Request):
    """Render the executive report HTML page"""
    return templates.TemplateResponse(
        request=request,
        name="executive_report.html",
        context={"title": f"Informe Ejecutivo — {settings.APP_TITLE}"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
