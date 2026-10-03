from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="templates")

@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/services", response_class=HTMLResponse)
async def services(request: Request):
    return templates.TemplateResponse("services.html", {"request": request})

@router.get("/services/{id}", response_class=HTMLResponse)
async def service_detail(request: Request, id: int):
    return templates.TemplateResponse("service_detail.html", {"request": request, "service_id": id})

@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/register", response_class=HTMLResponse)
async def register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.get("/profile", response_class=HTMLResponse)
async def profile(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})

@router.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    return templates.TemplateResponse("admin.html", {"request": request})
