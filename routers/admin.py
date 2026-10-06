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

import re
import json

def generate_slug(text: str) -> str:
    cleaned = re.sub(r'[^a-z0-9]+', '-', text.lower()).strip('-')
    return cleaned or "xizmat"

# --- Services Management ---
@router.get("/services", response_model=list[schemas.ServiceOut])
def admin_get_services(db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin)):
    return db.query(models.Service).all()

@router.post("/services", response_model=schemas.ServiceOut)
def admin_create_service(service_in: schemas.ServiceCreate, db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin)):
    data = service_in.model_dump() if hasattr(service_in, "model_dump") else service_in.dict()
    if not data.get("slug"):
        base_slug = generate_slug(data.get("title", "xizmat"))
        slug = base_slug
        count = 1
        while db.query(models.Service).filter(models.Service.slug == slug).first():
            slug = f"{base_slug}-{count}"
            count += 1
        data["slug"] = slug

    service = models.Service(**data)
    db.add(service)
    db.commit()
    db.refresh(service)

    db.add(models.ActivityLog(
        admin_id=current_admin.id,
        action="Yangi xizmat yaratildi",
        entity="Service",
        entity_id=service.id,
        metadata_json=json.dumps({"title": service.title, "price": service.price})
    ))
    db.commit()

    return service

@router.put("/services/{id}", response_model=schemas.ServiceOut)
def admin_update_service(id: int, service_in: schemas.ServiceUpdate, db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin)):
    service = db.query(models.Service).filter(models.Service.id == id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Xizmat topilmadi")
    
    update_data = service_in.model_dump(exclude_unset=True) if hasattr(service_in, "model_dump") else service_in.dict(exclude_unset=True)
    if "title" in update_data and not update_data.get("slug"):
        update_data["slug"] = generate_slug(update_data["title"])

    for k, v in update_data.items():
        setattr(service, k, v)
    
    db.commit()
    db.refresh(service)

    db.add(models.ActivityLog(
        admin_id=current_admin.id,
        action="Xizmat tahrirlandi",
        entity="Service",
        entity_id=service.id,
        metadata_json=json.dumps({"title": service.title, "price": service.price})
    ))
    db.commit()

    return service

@router.patch("/services/{id}/archive", response_model=schemas.ServiceOut)
def admin_archive_service(id: int, is_archived: bool = Query(...), db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin)):
    service = db.query(models.Service).filter(models.Service.id == id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Xizmat topilmadi")
    service.is_archived = is_archived
    db.commit()
    db.refresh(service)

    db.add(models.ActivityLog(
        admin_id=current_admin.id,
        action="Xizmat arxivlandi" if is_archived else "Xizmat faollashtirildi",
        entity="Service",
        entity_id=service.id,
        metadata_json=json.dumps({"is_archived": is_archived})
    ))
    db.commit()

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

# --- Activity Log ---
@router.get("/activity-log", response_model=list[schemas.ActivityLogOut])
def admin_get_activity_log(
    limit: int = 50, 
    db: Session = Depends(get_db), 
    current_admin: models.User = Depends(get_current_admin)
):
    logs = db.query(models.ActivityLog).order_by(desc(models.ActivityLog.created_at)).limit(limit).all()
    res = []
    for l in logs:
        admin_user = db.query(models.User).filter(models.User.id == l.admin_id).first() if l.admin_id else None
        res.append({
            "id": l.id,
            "admin_id": l.admin_id,
            "admin_name": admin_user.name if admin_user else "Tizim",
            "action": l.action,
            "entity": l.entity,
            "entity_id": l.entity_id,
            "metadata_json": l.metadata_json,
            "created_at": l.created_at
        })
    return res

# --- Settings ---
@router.get("/settings", response_model=list[schemas.SettingOut])
def admin_get_settings(
    db: Session = Depends(get_db), 
    current_admin: models.User = Depends(get_current_admin)
):
    return db.query(models.Setting).all()

@router.put("/settings")
def admin_update_setting(
    payload: schemas.SettingUpdate, 
    db: Session = Depends(get_db), 
    current_admin: models.User = Depends(get_current_admin)
):
    setting = db.query(models.Setting).filter(models.Setting.key == payload.key).first()
    if not setting:
        setting = models.Setting(key=payload.key, value=payload.value)
        db.add(setting)
    else:
        setting.value = payload.value
    db.commit()

    db.add(models.ActivityLog(
        admin_id=current_admin.id,
        action=f"Sozlama o'zgartirildi: {payload.key}",
        entity="Setting",
        entity_id=setting.id,
        metadata_json=json.dumps({"key": payload.key, "value": payload.value})
    ))
    db.commit()

    return {"detail": "Sozlama yangilandi", "key": payload.key, "value": payload.value}

# --- User Detail with Orders ---
@router.get("/users/{id}", response_model=schemas.UserDetailAdminOut)
def admin_get_user_detail(
    id: int, 
    db: Session = Depends(get_db), 
    current_admin: models.User = Depends(get_current_admin)
):
    user = db.query(models.User).filter(models.User.id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    orders = db.query(models.Order).filter(models.Order.user_id == id).order_by(desc(models.Order.created_at)).all()
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "role": user.role,
        "created_at": user.created_at,
        "orders_count": len(orders),
        "orders": orders
    }

# --- Reports ---
@router.get("/reports")
def admin_get_reports(
    start_date: date = None,
    end_date: date = None,
    db: Session = Depends(get_db),
    current_admin: models.User = Depends(get_current_admin)
):
    query = db.query(models.Order)
    if start_date:
        query = query.filter(models.Order.created_at >= start_date)
    if end_date:
        query = query.filter(models.Order.created_at <= end_date)

    orders = query.all()
    total_count = len(orders)
    completed_count = sum(1 for o in orders if o.status == "Yakunlandi")
    total_revenue = sum(o.price_snapshot for o in orders if o.status == "Yakunlandi")
    potential_revenue = sum(o.price_snapshot for o in orders if o.status != "Bekor qilindi")
    cancelled_count = sum(1 for o in orders if o.status == "Bekor qilindi")

    status_counts = {}
    for o in orders:
        status_counts[o.status] = status_counts.get(o.status, 0) + 1

    return {
        "total_orders": total_count,
        "completed_orders": completed_count,
        "cancelled_orders": cancelled_count,
        "total_revenue": total_revenue,
        "potential_revenue": potential_revenue,
        "status_counts": status_counts,
        "start_date": str(start_date) if start_date else None,
        "end_date": str(end_date) if end_date else None
    }

# --- Admin Portfolio Management ---
@router.get("/projects", response_model=list[schemas.PortfolioProjectOut])
def admin_get_projects(db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin)):
    return db.query(models.PortfolioProject).order_by(models.PortfolioProject.created_at.desc()).all()

@router.post("/projects", response_model=schemas.PortfolioProjectOut)
def admin_create_project(project_in: schemas.PortfolioProjectCreate, db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin)):
    data = project_in.model_dump() if hasattr(project_in, "model_dump") else project_in.dict()
    if not data.get("slug"):
        data["slug"] = generate_slug(data["title"])
    
    # Ensure unique slug
    base_slug = data["slug"]
    count = 1
    while db.query(models.PortfolioProject).filter(models.PortfolioProject.slug == data["slug"]).first():
        data["slug"] = f"{base_slug}-{count}"
        count += 1

    project = models.PortfolioProject(**data)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project

@router.put("/projects/{id}", response_model=schemas.PortfolioProjectOut)
def admin_update_project(id: int, project_in: schemas.PortfolioProjectUpdate, db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin)):
    project = db.query(models.PortfolioProject).filter(models.PortfolioProject.id == id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Loyiha topilmadi")
    
    update_data = project_in.model_dump(exclude_unset=True) if hasattr(project_in, "model_dump") else project_in.dict(exclude_unset=True)
    for k, v in update_data.items():
        setattr(project, k, v)
    
    db.commit()
    db.refresh(project)
    return project

@router.delete("/projects/{id}")
def admin_delete_project(id: int, db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin)):
    project = db.query(models.PortfolioProject).filter(models.PortfolioProject.id == id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Loyiha topilmadi")
    db.delete(project)
    db.commit()
    return {"detail": "Portfolio loyihasi o'chirildi"}

# --- Admin Team Management ---
@router.post("/team", response_model=schemas.TeamMemberOut)
def admin_create_team_member(member_in: schemas.TeamMemberCreate, db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin)):
    data = member_in.model_dump() if hasattr(member_in, "model_dump") else member_in.dict()
    member = models.TeamMember(**data)
    db.add(member)
    db.commit()
    db.refresh(member)
    return member

@router.put("/team/{id}", response_model=schemas.TeamMemberOut)
def admin_update_team_member(id: int, member_in: schemas.TeamMemberCreate, db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin)):
    member = db.query(models.TeamMember).filter(models.TeamMember.id == id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Jamoa a'zosi topilmadi")
    data = member_in.model_dump() if hasattr(member_in, "model_dump") else member_in.dict()
    for k, v in data.items():
        setattr(member, k, v)
    db.commit()
    db.refresh(member)
    return member

@router.delete("/team/{id}")
def admin_delete_team_member(id: int, db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin)):
    member = db.query(models.TeamMember).filter(models.TeamMember.id == id).first()
    if not member:
        raise HTTPException(status_code=404, detail="Jamoa a'zosi topilmadi")
    db.delete(member)
    db.commit()
    return {"detail": "Jamoa a'zosi o'chirildi"}

# --- Admin Banners Management ---
@router.get("/banners", response_model=list[schemas.BannerOut])
def admin_get_banners(db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin)):
    return db.query(models.Banner).order_by(models.Banner.id.desc()).all()

@router.post("/banners", response_model=schemas.BannerOut)
def admin_create_banner(banner_in: schemas.BannerCreate, db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin)):
    data = banner_in.model_dump() if hasattr(banner_in, "model_dump") else banner_in.dict()
    banner = models.Banner(**data)
    db.add(banner)
    db.commit()
    db.refresh(banner)
    return banner

@router.put("/banners/{id}", response_model=schemas.BannerOut)
def admin_update_banner(id: int, banner_in: schemas.BannerCreate, db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin)):
    banner = db.query(models.Banner).filter(models.Banner.id == id).first()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner topilmadi")
    data = banner_in.model_dump() if hasattr(banner_in, "model_dump") else banner_in.dict()
    for k, v in data.items():
        setattr(banner, k, v)
    db.commit()
    db.refresh(banner)
    return banner

@router.delete("/banners/{id}")
def admin_delete_banner(id: int, db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin)):
    banner = db.query(models.Banner).filter(models.Banner.id == id).first()
    if not banner:
        raise HTTPException(status_code=404, detail="Banner topilmadi")
    db.delete(banner)
    db.commit()
    return {"detail": "Banner o'chirildi"}

# --- Admin Support Tickets ---
@router.get("/support", response_model=list[schemas.SupportTicketOut])
def admin_get_support_tickets(status: str = None, db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin)):
    query = db.query(models.SupportTicket)
    if status:
        query = query.filter(models.SupportTicket.status == status)
    tickets = query.order_by(models.SupportTicket.created_at.desc()).all()
    res = []
    for t in tickets:
        item = schemas.SupportTicketOut.model_validate(t)
        item.user_name = t.user.name if t.user else "Foydalanuvchi"
        item.user_email = t.user.email if t.user else "user@falcon.uz"
        res.append(item)
    return res

@router.patch("/support/{id}/reply", response_model=schemas.SupportTicketOut)
def admin_reply_support_ticket(id: int, reply_in: schemas.SupportTicketReply, db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin)):
    ticket = db.query(models.SupportTicket).filter(models.SupportTicket.id == id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Murojaat topilmadi")
    ticket.admin_reply = reply_in.admin_reply
    if reply_in.status:
        ticket.status = reply_in.status
    
    # Notify user
    db.add(models.Notification(
        user_id=ticket.user_id,
        title="Yordam murojaatiga javob",
        message=f"{ticket.ticket_number} murojaatingizga javob berildi: '{reply_in.admin_reply[:60]}...'",
        link="/yordam"
    ))
    db.commit()
    db.refresh(ticket)
    
    res = schemas.SupportTicketOut.model_validate(ticket)
    res.user_name = ticket.user.name if ticket.user else "Foydalanuvchi"
    res.user_email = ticket.user.email if ticket.user else "user@falcon.uz"
    return res

# --- Admin Reviews ---
@router.get("/reviews", response_model=list[schemas.ReviewOut])
def admin_get_reviews(db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin)):
    reviews = db.query(models.Review).order_by(models.Review.created_at.desc()).all()
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

@router.delete("/reviews/{id}")
def admin_delete_review(id: int, db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin)):
    review = db.query(models.Review).filter(models.Review.id == id).first()
    if not review:
        raise HTTPException(status_code=404, detail="Sharh topilmadi")
    db.delete(review)
    db.commit()
    return {"detail": "Sharh o'chirildi"}

# --- Admin Broadcast Notification ---
@router.post("/broadcast")
def admin_broadcast_notification(b_in: schemas.BroadcastNotificationIn, db: Session = Depends(get_db), current_admin: models.User = Depends(get_current_admin)):
    if b_in.user_id:
        target_users = db.query(models.User).filter(models.User.id == b_in.user_id).all()
    else:
        target_users = db.query(models.User).filter(models.User.role == "client").all()

    for u in target_users:
        db.add(models.Notification(
            user_id=u.id,
            title=b_in.title,
            message=b_in.message,
            link=b_in.link or "/dashboard"
        ))
    db.commit()
    return {"detail": f"{len(target_users)} ta foydalanuvchiga bildirishnoma yuborildi"}

