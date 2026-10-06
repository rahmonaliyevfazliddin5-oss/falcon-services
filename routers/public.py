from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_, desc, asc
import math

from database import get_db
import models
import schemas

router = APIRouter(prefix="/api", tags=["public"])

@router.get("/categories", response_model=list[schemas.CategoryOut])
def get_categories(db: Session = Depends(get_db)):
    return db.query(models.Category).all()

@router.get("/services", response_model=schemas.PaginatedServices)
def get_services(
    search: str = None,
    category_id: int = None,
    min_price: int = None,
    max_price: int = None,
    sort_by: str = "newest",
    page: int = Query(1, ge=1),
    limit: int = Query(6, ge=1, le=100),
    db: Session = Depends(get_db)
):
    query = db.query(models.Service).filter(models.Service.is_archived == False)

    if search:
        query = query.filter(models.Service.title.ilike(f"%{search}%"))
    if category_id:
        query = query.filter(models.Service.category_id == category_id)
    if min_price is not None:
        query = query.filter(models.Service.price >= min_price)
    if max_price is not None:
        query = query.filter(models.Service.price <= max_price)

    if sort_by == "price_asc":
        query = query.order_by(asc(models.Service.price))
    elif sort_by == "price_desc":
        query = query.order_by(desc(models.Service.price))
    else:
        query = query.order_by(desc(models.Service.created_at))

    total = query.count()
    pages = math.ceil(total / limit) if total > 0 else 1
    offset = (page - 1) * limit
    items = query.offset(offset).limit(limit).all()

    return {
        "items": items,
        "total": total,
        "page": page,
        "pages": pages
    }

@router.get("/services/{slug_or_id}", response_model=schemas.ServiceDetailOut)
def get_service_detail(slug_or_id: str, db: Session = Depends(get_db)):
    service = None
    if slug_or_id.isdigit():
        service = db.query(models.Service).filter(models.Service.id == int(slug_or_id)).first()
    if not service:
        service = db.query(models.Service).filter(models.Service.slug == slug_or_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Xizmat topilmadi")

    related = db.query(models.Service).filter(
        models.Service.category_id == service.category_id,
        models.Service.id != service.id,
        models.Service.is_archived == False
    ).limit(4).all()

    response = schemas.ServiceDetailOut.model_validate(service)
    response.related_services = [schemas.ServiceOut.model_validate(r) for r in related]
    return response

@router.get("/settings")
def get_public_settings(db: Session = Depends(get_db)):
    settings_list = db.query(models.Setting).all()
    return {s.key: s.value for s in settings_list}

@router.get("/stats")
def get_public_platform_stats(db: Session = Depends(get_db)):
    active_services = db.query(models.Service).filter(models.Service.is_archived == False).count()
    registered_clients = db.query(models.User).filter(models.User.role == "client").count()
    completed_projects = db.query(models.Order).filter(models.Order.status == "Yakunlandi").count()
    total_orders = db.query(models.Order).count()
    
    return {
        "active_services": active_services,
        "registered_clients": registered_clients,
        "completed_projects": completed_projects,
        "total_orders": total_orders
    }

# --- Portfolio Projects ---
@router.get("/projects", response_model=list[schemas.PortfolioProjectOut])
def get_portfolio_projects(category: str = None, db: Session = Depends(get_db)):
    query = db.query(models.PortfolioProject)
    if category and category != "Barchasi":
        query = query.filter(models.PortfolioProject.category_name.ilike(f"%{category}%"))
    return query.order_by(models.PortfolioProject.created_at.desc()).all()

@router.get("/projects/{slug_or_id}", response_model=schemas.PortfolioProjectOut)
def get_portfolio_project_detail(slug_or_id: str, db: Session = Depends(get_db)):
    project = None
    if slug_or_id.isdigit():
        project = db.query(models.PortfolioProject).filter(models.PortfolioProject.id == int(slug_or_id)).first()
    if not project:
        project = db.query(models.PortfolioProject).filter(models.PortfolioProject.slug == slug_or_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Portfolio loyihasi topilmadi")
    return project

# --- Team Members ---
@router.get("/team", response_model=list[schemas.TeamMemberOut])
def get_team_members(db: Session = Depends(get_db)):
    return db.query(models.TeamMember).order_by(models.TeamMember.display_order.asc()).all()

# --- Reviews ---
@router.get("/reviews", response_model=list[schemas.ReviewOut])
def get_public_reviews(limit: int = 10, db: Session = Depends(get_db)):
    reviews = db.query(models.Review).order_by(models.Review.created_at.desc()).limit(limit).all()
    out = []
    for r in reviews:
        user_name = r.user.name if r.user else "Mijoz"
        service_title = r.service.title if r.service else (r.order.service_title_snapshot if r.order else "IT Xizmat")
        out.append(schemas.ReviewOut(
            id=r.id,
            order_id=r.order_id,
            user_id=r.user_id,
            user_name=user_name,
            service_id=r.service_id,
            service_title=service_title,
            rating=r.rating,
            comment=r.comment,
            created_at=r.created_at
        ))
    return out

# --- Banners ---
@router.get("/banners", response_model=list[schemas.BannerOut])
def get_active_banners(db: Session = Depends(get_db)):
    return db.query(models.Banner).filter(models.Banner.is_active == True).all()

# --- Support Tickets (Public create ticket) ---
import uuid

@router.post("/support", response_model=schemas.SupportTicketOut)
def create_support_ticket(ticket_in: schemas.SupportTicketCreate, db: Session = Depends(get_db)):
    # Mehmon yoki tizim foydalanuvchisi uchun ticket
    # Birlamchi foydalanuvchi sifatida birinchi mijoz yoki admin tanlanadi
    user = db.query(models.User).filter(models.User.role == "client").first() or db.query(models.User).first()
    if not user:
        raise HTTPException(status_code=400, detail="Tizimda foydalanuvchi mavjud emas")
    
    last_ticket = db.query(models.SupportTicket).order_by(models.SupportTicket.id.desc()).first()
    next_num = (last_ticket.id + 1) if last_ticket else 1
    ticket_number = f"TCK-{1000 + next_num}"

    ticket = models.SupportTicket(
        ticket_number=ticket_number,
        user_id=user.id,
        subject=ticket_in.subject,
        message=ticket_in.message,
        category=ticket_in.category or "Umumiy",
        status="Ochiq"
    )
    db.add(ticket)
    
    # Notify admin
    admin_user = db.query(models.User).filter(models.User.role == "admin").first()
    if admin_user:
        db.add(models.Notification(
            user_id=admin_user.id,
            title="Yangi yordam murojaati",
            message=f"{ticket_number}: {ticket_in.subject}",
            link="/admin?tab=support"
        ))
    
    db.commit()
    db.refresh(ticket)
    
    res = schemas.SupportTicketOut.model_validate(ticket)
    res.user_name = user.name
    res.user_email = user.email
    return res

