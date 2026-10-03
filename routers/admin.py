from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
import io
import csv

from database import get_db
import models
import schemas
from auth import get_current_admin

router = APIRouter(prefix="/api/admin", tags=["admin"])

# --- Services Management ---
@router.get("/services", response_model=list[schemas.ServiceOut])
def admin_get_services(db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin)):
    return db.query(models.Service).all()

@router.post("/services", response_model=schemas.ServiceOut)
def admin_create_service(service_in: schemas.ServiceCreate, db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin)):
    service = models.Service(**service_in.dict())
    db.add(service)
    db.commit()
    db.refresh(service)
    return service

@router.put("/services/{id}", response_model=schemas.ServiceOut)
def admin_update_service(id: int, service_in: schemas.ServiceUpdate, db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin)):
    service = db.query(models.Service).filter(models.Service.id == id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Xizmat topilmadi")
    
    update_data = service_in.dict(exclude_unset=True)
    for k, v in update_data.items():
        setattr(service, k, v)
    
    db.commit()
    db.refresh(service)
    return service

@router.patch("/services/{id}/archive", response_model=schemas.ServiceOut)
def admin_archive_service(id: int, is_archived: bool = Query(...), db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin)):
    service = db.query(models.Service).filter(models.Service.id == id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Xizmat topilmadi")
    service.is_archived = is_archived
    db.commit()
    db.refresh(service)
    return service

# --- Categories Management ---
@router.post("/categories", response_model=schemas.CategoryOut)
def admin_create_category(category_in: schemas.CategoryBase, db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin)):
    cat = models.Category(**category_in.dict())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat

@router.put("/categories/{id}", response_model=schemas.CategoryOut)
def admin_update_category(id: int, category_in: schemas.CategoryBase, db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin)):
    cat = db.query(models.Category).filter(models.Category.id == id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Kategoriya topilmadi")
    cat.name = category_in.name
    cat.slug = category_in.slug
    db.commit()
    db.refresh(cat)
    return cat

@router.delete("/categories/{id}")
def admin_delete_category(id: int, db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin)):
    cat = db.query(models.Category).filter(models.Category.id == id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Kategoriya topilmadi")
    db.delete(cat)
    db.commit()
    return {"detail": "Kategoriya o'chirildi"}

# --- Orders Management ---
@router.get("/orders", response_model=list[schemas.OrderOut])
def admin_get_orders(
    search: str = None,
    status: str = None,
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db), 
    current_admin: models.User = Depends(get_current_admin)
):
    query = db.query(models.Order).join(models.User)
    
    if search:
        query = query.filter(
            models.Order.order_number.ilike(f"%{search}%") | 
            models.Order.project_name.ilike(f"%{search}%") |
            models.User.name.ilike(f"%{search}%")
        )
    if status:
        query = query.filter(models.Order.status == status)
    if start_date:
        query = query.filter(models.Order.created_at >= start_date)
    if end_date:
        query = query.filter(models.Order.created_at <= end_date)
        
    return query.all()

# --- Users Management ---
@router.get("/users", response_model=list[schemas.UserOut])
def admin_get_users(db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin)):
    return db.query(models.User).all()

# --- Dashboard & Reports ---
@router.get("/dashboard", response_model=schemas.DashboardStats)
def admin_dashboard(start_date: date = None, end_date: date = None, db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin)):
    query = db.query(models.Order)
    if start_date:
        query = query.filter(models.Order.created_at >= start_date)
    if end_date:
        query = query.filter(models.Order.created_at <= end_date)

    total_orders = query.count()
    new_orders = query.filter(models.Order.status == "Yangi").count()
    in_progress = query.filter(models.Order.status.in_(["Qabul qilindi", "Jarayonda"])).count()
    
    completed_sum = db.query(func.sum(models.Order.price_snapshot)).filter(
        models.Order.status == "Yakunlandi"
    ).scalar() or 0

    # Status distribution
    dist = {}
    statuses = ["Yangi", "Qabul qilindi", "Jarayonda", "Yakunlandi", "Bekor qilindi"]
    for s in statuses:
        dist[s] = query.filter(models.Order.status == s).count()

    # Top services
    top_services = db.query(
        models.Order.service_title_snapshot, 
        func.count(models.Order.id).label('count')
    ).group_by(models.Order.service_title_snapshot).order_by(desc('count')).limit(5).all()

    top_services_list = [{"title": t[0], "count": t[1]} for t in top_services]

    return schemas.DashboardStats(
        total_orders=total_orders,
        new_orders_count=new_orders,
        in_progress_orders_count=in_progress,
        completed_orders_sum=completed_sum,
        status_distribution=dist,
        top_services=top_services_list
    )

# --- CSV Export ---
@router.get("/orders/export-csv")
def export_orders_csv(
    start_date: date = None, 
    end_date: date = None, 
    status: str = None, 
    db: Session = Depends(get_db), 
    current_admin: models.User = Depends(get_current_admin)
):
    query = db.query(models.Order).join(models.User)
    if start_date:
        query = query.filter(models.Order.created_at >= start_date)
    if end_date:
        query = query.filter(models.Order.created_at <= end_date)
    if status:
        query = query.filter(models.Order.status == status)
        
    orders = query.all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Buyurtma Raqami', 'Mijoz', 'Xizmat', 'Narx', 'Holat', 'Sana'])

    for order in orders:
        writer.writerow([
            order.id, 
            order.order_number, 
            order.user.name, 
            order.service_title_snapshot,
            order.price_snapshot,
            order.status,
            order.created_at.strftime('%Y-%m-%d %H:%M:%S')
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]), 
        media_type="text/csv", 
        headers={"Content-Disposition": "attachment; filename=orders.csv"}
    )
