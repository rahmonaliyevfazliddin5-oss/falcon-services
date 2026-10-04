import os
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
import auth
from jose import jwt, JWTError

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@router.get("/services", response_class=HTMLResponse)
async def services(request: Request):
    return templates.TemplateResponse(request=request, name="services.html")

@router.get("/services/{id}", response_class=HTMLResponse)
async def service_detail(request: Request, id: int):
    return templates.TemplateResponse(request=request, name="service_detail.html", context={"service_id": id})

@router.get("/login", response_class=HTMLResponse)
async def login(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if token:
        try:
            payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
            email = payload.get("sub")
            if email:
                user = auth.get_user(db, email=email)
                if user:
                    return RedirectResponse(url="/admin" if user.role == "admin" else "/profile", status_code=302)
        except Exception:
            pass
    google_client_id = os.getenv("GOOGLE_CLIENT_ID", "354347783742-g8fsuo6iathr7s7un3dddic44874nid0.apps.googleusercontent.com")
    return templates.TemplateResponse(request=request, name="login.html", context={"google_client_id": google_client_id})

@router.get("/register", response_class=HTMLResponse)
async def register(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if token:
        try:
            payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
            email = payload.get("sub")
            if email:
                user = auth.get_user(db, email=email)
                if user:
                    return RedirectResponse(url="/profile", status_code=302)
        except Exception:
            pass
    google_client_id = os.getenv("GOOGLE_CLIENT_ID", "354347783742-g8fsuo6iathr7s7un3dddic44874nid0.apps.googleusercontent.com")
    return templates.TemplateResponse(request=request, name="register.html", context={"google_client_id": google_client_id})

@router.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):
    return templates.TemplateResponse(request=request, name="profile.html")

@router.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/login?next=/admin", status_code=302)
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            return RedirectResponse(url="/login?next=/admin", status_code=302)
        user = auth.get_user(db, email=email)
        if not user or user.role != "admin":
            return RedirectResponse(url="/login?next=/admin", status_code=302)
    except (JWTError, Exception):
        return RedirectResponse(url="/login?next=/admin", status_code=302)
        
    return templates.TemplateResponse(request=request, name="admin.html")

@router.get("/logout")
async def logout_page():
    res = RedirectResponse(url="/login", status_code=302)
    res.delete_cookie(key="access_token", path="/")
    return res
