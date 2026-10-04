import os
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager

from database import engine, init_db
import models
import auth
from seed import seed_db

from routers import public, orders, admin, pages

# =========================================================================
# Qoida (Rule): MAINTENANCE_MODE
# O'zgartirishlar tugatildi (False) - Sayt normal rejimda ishlamoqda
# =========================================================================
MAINTENANCE_MODE: bool = False

templates = Jinja2Templates(directory="templates")

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_db()
    yield

app = FastAPI(title="Falcon Services Platform", version="3.0.0", lifespan=lifespan)

# 1. Maintenance Mode Middleware
@app.middleware("http")
async def maintenance_middleware(request: Request, call_next):
    # Statik fayllar (maintenance.png, css, js) va holat tekshiruvi doim ochiq bo'ladi
    if request.url.path.startswith("/static/") or request.url.path == "/api/maintenance/status":
        return await call_next(request)

    # Agar Maintenance Mode yoqilgan bo'lsa
    if MAINTENANCE_MODE:
        if request.url.path.startswith("/api/"):
            return JSONResponse(
                status_code=503,
                content={"detail": "Veb-saytda tozalash hamda sozlash ishlari olib borilyabdi", "maintenance": True}
            )
        return templates.TemplateResponse(request=request, name="maintenance.html", status_code=503)

    return await call_next(request)

# 2. Brauzer kesh (caching) sozlamalari: rasmlar va statik resurslar chaqmoqdek tez ochilishi uchun
@app.middleware("http")
async def add_cache_control_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static/"):
        response.headers["Cache-Control"] = "public, max-age=604800, stale-while-revalidate=86400"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/api/maintenance/status")
def get_maintenance_status():
    return {"maintenance": MAINTENANCE_MODE}

app.include_router(auth.router)
app.include_router(public.router)
app.include_router(orders.router)
app.include_router(admin.router)
app.include_router(pages.router)
