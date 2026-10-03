from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from database import engine, init_db
import models
import auth
from seed import seed_db

from routers import public, orders, admin, pages

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    seed_db()
    yield

app = FastAPI(title="Falcon Services Platform", version="3.0.0", lifespan=lifespan)

# Brauzer kesh (caching) sozlamalari middleware: rasmlar va statik resurslar darhol ochilishi uchun
@app.middleware("http")
async def add_cache_control_headers(request: Request, call_next):
    response = await call_next(request)
    if request.url.path.startswith("/static/"):
        # Rasmlar va statik fayllar uchun 7 kunlik agressiv brauzer kesh
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

app.include_router(auth.router)
app.include_router(public.router)
app.include_router(orders.router)
app.include_router(admin.router)
app.include_router(pages.router)
