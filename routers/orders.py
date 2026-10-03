from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta

from database import get_db
import models
import schemas
from auth import get_current_user

router = APIRouter(prefix="/api/orders", tags=["orders"])

@router.post("", response_model=schemas.OrderOut)
def create_order(order_in: schemas.OrderCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    # 1. Check Technical Task
    tt_nospaces = order_in.technical_task.replace(" ", "").replace("\n", "")
    if len(tt_nospaces) < 50:
        raise HTTPException(status_code=400, detail="Texnik topshiriq kamida 50 ta belgidan iborat bo‘lishi kerak")

    # 2. Check Service
    service = db.query(models.Service).filter(models.Service.id == order_in.service_id).first()
    if not service or service.is_archived:
        raise HTTPException(status_code=400, detail="Ushbu xizmat faol emas yoki arxivlangan")

    # 3. Check Deadline
    min_deadline = date.today() + timedelta(days=service.delivery_days)
    if order_in.desired_deadline < min_deadline:
        raise HTTPException(status_code=400, detail="Yakunlash sanasi xizmatning bajarish muddatidan oldin bo‘lishi mumkin emas")

    # 4. Duplicate prevention (Idempotency) - 10 seconds
    ten_seconds_ago = datetime.utcnow() - timedelta(seconds=10)
    duplicate = db.query(models.Order).filter(
        models.Order.user_id == current_user.id,
        models.Order.service_id == service.id,
        models.Order.project_name == order_in.project_name,
        models.Order.created_at >= ten_seconds_ago
    ).first()
    if duplicate:
        raise HTTPException(status_code=400, detail="Buyurtma allaqachon qabul qilingan, iltimos kuting")

    # 5. Order Number Generation
    last_order = db.query(models.Order).order_by(models.Order.id.desc()).first()
    next_id = (last_order.id + 1) if last_order else 1
    order_number = f"ORD-{10000 + next_id}"

    # 6. Create Order
    new_order = models.Order(
        order_number=order_number,
        user_id=current_user.id,
        service_id=service.id,
        service_title_snapshot=service.title,
        price_snapshot=service.price,
        project_name=order_in.project_name,
        technical_task=order_in.technical_task,
        desired_deadline=order_in.desired_deadline,
        contact_phone=order_in.contact_phone,
        status="Yangi"
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    # 7. Initial Status History
    history = models.OrderStatusHistory(
        order_id=new_order.id,
        old_status=None,
        new_status="Yangi",
        changed_by_user_id=current_user.id
    )
    db.add(history)
    db.commit()

    return new_order

@router.get("/my", response_model=list[schemas.OrderOut])
def get_my_orders(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.Order).filter(models.Order.user_id == current_user.id).all()

@router.get("/{id}", response_model=schemas.OrderDetailOut)
def get_order_detail(id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    
    if current_user.role != "admin" and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sizda boshqa mijozning buyurtmasini ko'rish huquqi yo'q")
    
    return order

@router.patch("/{id}/status", response_model=schemas.OrderOut)
def change_order_status(id: int, status_update: schemas.OrderStatusUpdate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")

    # Authorization
    if current_user.role == "client":
        if order.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Sizda boshqa mijozning buyurtmasini o'zgartirish huquqi yo'q")
        if order.status != "Yangi" or status_update.status != "Bekor qilindi":
            raise HTTPException(status_code=403, detail="Mijoz faqat 'Yangi' holatdagi buyurtmani bekor qila oladi")

    # State Machine Rules
    valid_transitions = {
        "Yangi": ["Qabul qilindi", "Bekor qilindi"],
        "Qabul qilindi": ["Jarayonda", "Bekor qilindi"],
        "Jarayonda": ["Yakunlandi"],
        "Yakunlandi": [],
        "Bekor qilindi": []
    }

    if status_update.status not in valid_transitions.get(order.status, []):
        raise HTTPException(status_code=400, detail="Ushbu holatga o'tish mumkin emas")

    old_status = order.status
    order.status = status_update.status
    
    history = models.OrderStatusHistory(
        order_id=order.id,
        old_status=old_status,
        new_status=order.status,
        changed_by_user_id=current_user.id
    )
    db.add(history)
    db.commit()
    db.refresh(order)
    return order

@router.get("/{id}/messages", response_model=list[schemas.MessageOut])
def get_order_messages(id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    if current_user.role != "admin" and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sizda boshqa mijozning buyurtmasini ko'rish huquqi yo'q")
    
    return db.query(models.Message).filter(models.Message.order_id == id).order_by(models.Message.created_at.asc()).all()

@router.post("/{id}/messages", response_model=schemas.MessageOut)
def send_message(id: int, msg_in: schemas.MessageCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    if current_user.role != "admin" and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sizda boshqa mijozning buyurtmasiga xabar yozish huquqi yo'q")
    
    msg = models.Message(
        order_id=id,
        sender_id=current_user.id,
        text=msg_in.text
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg
