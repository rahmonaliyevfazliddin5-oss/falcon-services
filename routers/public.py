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

@router.get("/services/{id}", response_model=schemas.ServiceDetailOut)
def get_service_detail(id: int, db: Session = Depends(get_db)):
    service = db.query(models.Service).filter(models.Service.id == id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Xizmat topilmadi")

    related = db.query(models.Service).filter(
        models.Service.category_id == service.category_id,
        models.Service.id != id,
        models.Service.is_archived == False
    ).limit(4).all()

    response = schemas.ServiceDetailOut.model_validate(service)
    response.related_services = [schemas.ServiceOut.model_validate(r) for r in related]
    return response

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
