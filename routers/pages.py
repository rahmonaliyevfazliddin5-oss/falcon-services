import os
from fastapi import APIRouter, Request, Depends, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
import auth
import models
from jose import jwt, JWTError

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="templates")

def get_optional_user(request: Request, db: Session):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email = payload.get("sub")
        if email:
            return auth.get_user(db, email=email)
    except Exception:
        pass
    return None

# =========================================================================
# 1. PUBLIC ROUTES
# =========================================================================
@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html")

@router.get("/xizmatlar", response_class=HTMLResponse)
async def services_page(request: Request):
    return templates.TemplateResponse(request=request, name="services.html")

@router.get("/services", response_class=HTMLResponse)
async def services_legacy_redirect(request: Request):
    return RedirectResponse(url="/xizmatlar", status_code=301)

@router.get("/xizmatlar/{slug_or_id}", response_class=HTMLResponse)
async def service_detail_page(request: Request, slug_or_id: str, db: Session = Depends(get_db)):
    service = None
    if slug_or_id.isdigit():
        service = db.query(models.Service).filter(models.Service.id == int(slug_or_id)).first()
    if not service:
        service = db.query(models.Service).filter(models.Service.slug == slug_or_id).first()
    
    return templates.TemplateResponse(
        request=request, 
        name="service_detail.html", 
        context={"service": service, "slug_or_id": slug_or_id}
    )

@router.get("/services/{id}", response_class=HTMLResponse)
async def service_detail_legacy(request: Request, id: int, db: Session = Depends(get_db)):
    service = db.query(models.Service).filter(models.Service.id == id).first()
    if service and service.slug:
        return RedirectResponse(url=f"/xizmatlar/{service.slug}", status_code=301)
    return templates.TemplateResponse(request=request, name="service_detail.html", context={"service": service, "slug_or_id": str(id)})

@router.get("/portfolio", response_class=HTMLResponse)
async def portfolio_page(request: Request):
    return templates.TemplateResponse(request=request, name="portfolio.html")

@router.get("/narxlar", response_class=HTMLResponse)
async def pricing_page(request: Request):
    return templates.TemplateResponse(request=request, name="pricing.html")

@router.get("/faq", response_class=HTMLResponse)
async def faq_page(request: Request):
    return templates.TemplateResponse(request=request, name="faq.html")

@router.get("/aloqa", response_class=HTMLResponse)
async def contact_page(request: Request):
    return templates.TemplateResponse(request=request, name="contact.html")

# =========================================================================
# 2. AUTHENTICATION PAGES
# =========================================================================
@router.get("/kirish", response_class=HTMLResponse)
async def login_page(request: Request, redirect: str = None, db: Session = Depends(get_db)):
    user = get_optional_user(request, db)
    if user:
        if redirect:
            return RedirectResponse(url=redirect, status_code=302)
        return RedirectResponse(url="/admin" if user.role == "admin" else "/dashboard", status_code=302)
    google_client_id = os.getenv("GOOGLE_CLIENT_ID", "354347783742-g8fsuo6iathr7s7un3dddic44874nid0.apps.googleusercontent.com")
    return templates.TemplateResponse(request=request, name="login.html", context={"google_client_id": google_client_id, "redirect_url": redirect or ""})

@router.get("/login", response_class=HTMLResponse)
async def login_legacy(request: Request, redirect: str = None, next: str = None, db: Session = Depends(get_db)):
    target = redirect or next or ""
    url = f"/kirish?redirect={target}" if target else "/kirish"
    return RedirectResponse(url=url, status_code=301)

@router.get("/royxatdan-otish", response_class=HTMLResponse)
async def register_page(request: Request, redirect: str = None, db: Session = Depends(get_db)):
    user = get_optional_user(request, db)
    if user:
        if redirect:
            return RedirectResponse(url=redirect, status_code=302)
        return RedirectResponse(url="/dashboard", status_code=302)
    google_client_id = os.getenv("GOOGLE_CLIENT_ID", "354347783742-g8fsuo6iathr7s7un3dddic44874nid0.apps.googleusercontent.com")
    return templates.TemplateResponse(request=request, name="register.html", context={"google_client_id": google_client_id, "redirect_url": redirect or ""})

@router.get("/register", response_class=HTMLResponse)
async def register_legacy(request: Request, redirect: str = None, db: Session = Depends(get_db)):
    url = f"/royxatdan-otish?redirect={redirect}" if redirect else "/royxatdan-otish"
    return RedirectResponse(url=url, status_code=301)

@router.get("/logout")
async def logout_page():
    res = RedirectResponse(url="/kirish", status_code=302)
    res.delete_cookie(key="access_token", path="/")
    return res

# =========================================================================
# 3. CLIENT PORTAL PAGES
# =========================================================================
@router.get("/dashboard", response_class=HTMLResponse)
async def client_dashboard(request: Request, db: Session = Depends(get_db)):
    user = get_optional_user(request, db)
    if not user:
        return RedirectResponse(url="/kirish?redirect=/dashboard", status_code=302)
    if user.role == "admin":
        return RedirectResponse(url="/admin", status_code=302)
    return templates.TemplateResponse(request=request, name="client_dashboard.html", context={"user": user})

@router.get("/buyurtmalarim", response_class=HTMLResponse)
async def client_orders(request: Request, db: Session = Depends(get_db)):
    user = get_optional_user(request, db)
    if not user:
        return RedirectResponse(url="/kirish?redirect=/buyurtmalarim", status_code=302)
    return templates.TemplateResponse(request=request, name="my_orders.html", context={"user": user})

@router.get("/buyurtma/{service_slug_or_id}", response_class=HTMLResponse)
async def client_order_wizard(request: Request, service_slug_or_id: str, db: Session = Depends(get_db)):
    user = get_optional_user(request, db)
    if not user:
        return RedirectResponse(url=f"/kirish?redirect=/buyurtma/{service_slug_or_id}", status_code=302)
    
    service = None
    if service_slug_or_id.isdigit():
        service = db.query(models.Service).filter(models.Service.id == int(service_slug_or_id)).first()
    if not service:
        service = db.query(models.Service).filter(models.Service.slug == service_slug_or_id).first()
    
    return templates.TemplateResponse(
        request=request, 
        name="order_create.html", 
        context={"user": user, "service": service, "service_identifier": service_slug_or_id}
    )

@router.get("/buyurtma/muvaffaqiyat", response_class=HTMLResponse)
async def client_order_success(request: Request, order_number: str = Query(None)):
    return templates.TemplateResponse(request=request, name="order_success.html", context={"order_number": order_number})

@router.get("/buyurtmalar/{order_id}", response_class=HTMLResponse)
async def client_order_detail(request: Request, order_id: int, db: Session = Depends(get_db)):
    user = get_optional_user(request, db)
    if not user:
        return RedirectResponse(url=f"/kirish?redirect=/buyurtmalar/{order_id}", status_code=302)
    return templates.TemplateResponse(request=request, name="order_detail.html", context={"user": user, "order_id": order_id})

@router.get("/buyurtmalar/{order_id}/chat", response_class=HTMLResponse)
async def client_order_chat(request: Request, order_id: int):
    return RedirectResponse(url=f"/buyurtmalar/{order_id}#chat", status_code=302)

@router.get("/profil", response_class=HTMLResponse)
async def client_profile(request: Request, db: Session = Depends(get_db)):
    user = get_optional_user(request, db)
    if not user:
        return RedirectResponse(url="/kirish?redirect=/profil", status_code=302)
    return templates.TemplateResponse(request=request, name="profile.html", context={"user": user, "edit_mode": False})

@router.get("/profile", response_class=HTMLResponse)
async def profile_legacy(request: Request):
    return RedirectResponse(url="/profil", status_code=301)

@router.get("/profil/tahrirlash", response_class=HTMLResponse)
async def client_profile_edit(request: Request, db: Session = Depends(get_db)):
    user = get_optional_user(request, db)
    if not user:
        return RedirectResponse(url="/kirish?redirect=/profil/tahrirlash", status_code=302)
    return templates.TemplateResponse(request=request, name="profile.html", context={"user": user, "edit_mode": True})

@router.get("/bildirishnomalar", response_class=HTMLResponse)
async def client_notifications(request: Request, db: Session = Depends(get_db)):
    user = get_optional_user(request, db)
    if not user:
        return RedirectResponse(url="/kirish?redirect=/bildirishnomalar", status_code=302)
    return templates.TemplateResponse(request=request, name="notifications.html", context={"user": user})

# =========================================================================
# 4. ADMIN PORTAL PAGES
# =========================================================================
@router.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request, tab: str = "dashboard", action: str = None, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return RedirectResponse(url="/kirish?redirect=/admin", status_code=302)
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email: str = payload.get("sub")
        if not email:
            return RedirectResponse(url="/kirish?redirect=/admin", status_code=302)
        user = auth.get_user(db, email=email)
        if not user or user.role != "admin":
            return RedirectResponse(url="/kirish?redirect=/admin", status_code=302)
    except (JWTError, Exception):
        return RedirectResponse(url="/kirish?redirect=/admin", status_code=302)
        
    return templates.TemplateResponse(request=request, name="admin.html", context={"active_tab": tab, "action": action, "user": user})

@router.get("/admin/login")
async def admin_login_redirect():
    return RedirectResponse(url="/kirish?redirect=/admin", status_code=302)

@router.get("/admin/services")
async def admin_services_page():
    return RedirectResponse(url="/admin?tab=services", status_code=302)

@router.get("/admin/services/new")
async def admin_services_new_page():
    return RedirectResponse(url="/admin?tab=services&action=new", status_code=302)

@router.get("/admin/categories")
async def admin_categories_page():
    return RedirectResponse(url="/admin?tab=categories", status_code=302)

@router.get("/admin/orders")
async def admin_orders_page():
    return RedirectResponse(url="/admin?tab=orders", status_code=302)

@router.get("/admin/users")
async def admin_users_page():
    return RedirectResponse(url="/admin?tab=users", status_code=302)

@router.get("/admin/reports")
async def admin_reports_page():
    return RedirectResponse(url="/admin?tab=reports", status_code=302)

@router.get("/admin/settings")
async def admin_settings_page():
    return RedirectResponse(url="/admin?tab=settings", status_code=302)

@router.get("/admin/activity-log")
async def admin_activity_log_page():
    return RedirectResponse(url="/admin?tab=activity-log", status_code=302)
