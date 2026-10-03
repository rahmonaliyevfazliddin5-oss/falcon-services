from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
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
@router.get("/orders", response_model=list[schemas.OrderAdminOut])
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
        
    orders = query.all()
    res = []
    for o in orders:
        res.append({
            'id': o.id, 'order_number': o.order_number, 'user_id': o.user_id,
            'service_id': o.service_id, 'service_title_snapshot': o.service_title_snapshot,
            'price_snapshot': o.price_snapshot, 'project_name': o.project_name,
            'technical_task': o.technical_task, 'desired_deadline': o.desired_deadline,
            'contact_phone': o.contact_phone, 'status': o.status, 'created_at': o.created_at,
            'user_name': o.user.name, 'user_email': o.user.email
        })
    return res

# --- Users Management ---
@router.get("/users", response_model=list[schemas.UserAdminOut])
def admin_get_users(db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin)):
    users = db.query(models.User).all()
    res = []
    for u in users:
        res.append({
            'id': u.id, 'name': u.name, 'email': u.email,
            'phone': u.phone, 'role': u.role, 'created_at': u.created_at,
            'orders_count': db.query(models.Order).filter(models.Order.user_id == u.id).count()
        })
    return res

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
    completed_orders_count = query.filter(models.Order.status == "Yakunlandi").count()
    cancelled_orders_count = query.filter(models.Order.status == "Bekor qilindi").count()
    
    completed_sum = query.filter(models.Order.status == "Yakunlandi").with_entities(func.sum(models.Order.price_snapshot)).scalar() or 0
    total_potential = query.filter(models.Order.status != "Bekor qilindi").with_entities(func.sum(models.Order.price_snapshot)).scalar() or 0
    
    total_users_count = db.query(models.User).filter(models.User.role == "client").count()
    total_services_count = db.query(models.Service).filter(models.Service.is_archived == False).count()
    
    average_order_value = int(completed_sum / completed_orders_count) if completed_orders_count > 0 else (int(total_potential / total_orders) if total_orders > 0 else 0)

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

    # Real-time recent activity stream
    recent_orders = query.order_by(desc(models.Order.created_at)).limit(6).all()
    recent_activity = [
        {
            "order_number": o.order_number,
            "project_name": o.project_name,
            "service_title": o.service_title_snapshot,
            "client_name": o.user.name,
            "price": o.price_snapshot,
            "status": o.status,
            "time": o.created_at.strftime("%Y-%m-%d %H:%M")
        } for o in recent_orders
    ]

    return schemas.DashboardStats(
        total_orders=total_orders,
        new_orders_count=new_orders,
        in_progress_orders_count=in_progress,
        completed_orders_count=completed_orders_count,
        cancelled_orders_count=cancelled_orders_count,
        completed_orders_sum=completed_sum,
        total_revenue_potential=total_potential,
        total_users_count=total_users_count,
        total_services_count=total_services_count,
        average_order_value=average_order_value,
        status_distribution=dist,
        top_services=top_services_list,
        recent_activity=recent_activity
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
