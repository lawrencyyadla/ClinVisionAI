from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.api import health, scans, version
from app.core.config import settings
from app.core.database import get_db, init_db
from app.core.logging import configure_logging
from app.core.metrics import HTTP_REQUESTS, metrics_response
from app.services.storage import ensure_storage_dirs


configure_logging()

app = FastAPI(title=settings.PROJECT_NAME, version=settings.API_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    ensure_storage_dirs()
    init_db()


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    response = await call_next(request)
    route = request.scope.get("route")
    path = getattr(route, "path", request.url.path)
    HTTP_REQUESTS.labels(method=request.method, path=path, status=str(response.status_code)).inc()
    return response


app.include_router(scans.router)
app.include_router(health.router)
app.include_router(version.router)

settings.CONVERTED_DIR.mkdir(parents=True, exist_ok=True)
settings.HEATMAP_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/data/converted", StaticFiles(directory=settings.CONVERTED_DIR), name="converted")
app.mount("/data/heatmaps", StaticFiles(directory=settings.HEATMAP_DIR), name="heatmaps")


@app.get("/metrics")
def metrics(db: Session = Depends(get_db)):
    return metrics_response(db)
