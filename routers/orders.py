from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from datetime import date, datetime, timedelta
import json
import os
import uuid

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
        note="Buyurtma mijoz tomonidan muvaffaqiyatli topshirildi",
        changed_by_user_id=current_user.id
    )
    db.add(history)

    # 8. Create Client Notification
    db.add(models.Notification(
        user_id=current_user.id,
        title="Buyurtma yaratildi",
        message=f"{order_number} raqamli buyurtmangiz muvaffaqiyatli qabul qilindi. Tez orada mutaxassislarimiz bog'lanishadi.",
        link=f"/buyurtmalar/{new_order.id}"
    ))

    # 9. Notify Admin
    admin_user = db.query(models.User).filter(models.User.role == "admin").first()
    if admin_user:
        db.add(models.Notification(
            user_id=admin_user.id,
            title="Yangi buyurtma!",
            message=f"{order_number}: '{new_order.project_name}' bo'yicha yangi buyurtma qabul qilindi.",
            link=f"/admin"
        ))
    db.commit()

    return new_order

@router.get("/my", response_model=list[schemas.OrderOut])
def get_my_orders(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(models.Order).filter(models.Order.user_id == current_user.id).order_by(models.Order.created_at.desc()).all()

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
        "Jarayonda": ["Yakunlandi", "Tahrirlashda", "Bekor qilindi"],
        "Tahrirlashda": ["Jarayonda", "Yakunlandi"],
        "Yakunlandi": ["Qabul qilindi (Mijoz)", "Tahrirlashda"],
        "Qabul qilindi (Mijoz)": [],
        "Bekor qilindi": []
    }

    if status_update.status not in valid_transitions.get(order.status, []):
        raise HTTPException(status_code=400, detail="Ushbu holatga o'tish mumkin emas")

    old_status = order.status
    order.status = status_update.status
    if status_update.status == "Bekor qilindi" and status_update.note:
        order.cancel_reason = status_update.note
    
    history = models.OrderStatusHistory(
        order_id=order.id,
        old_status=old_status,
        new_status=order.status,
        note=status_update.note,
        changed_by_user_id=current_user.id
    )
    db.add(history)

    # Bildirishnoma (Mijozga)
    if current_user.id != order.user_id:
        db.add(models.Notification(
            user_id=order.user_id,
            title="Buyurtma holati yangilandi",
            message=f"{order.order_number} buyurtmangiz holati '{order.status}' ga o'zgardi.",
            link=f"/buyurtmalar/{order.id}"
        ))

    if current_user.role == "admin":
        db.add(models.ActivityLog(
            admin_id=current_user.id,
            action=f"Buyurtma holati: {old_status} -> {order.status}",
            entity="Order",
            entity_id=order.id,
            metadata_json=json.dumps({"order_number": order.order_number, "old_status": old_status, "new_status": order.status, "note": status_update.note})
        ))

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

# --- Order Acceptance (Mijoz natijani qabul qilishi) ---
@router.post("/{id}/accept", response_model=schemas.OrderOut)
def accept_order(id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    if current_user.role != "admin" and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sizda bu buyurtmani qabul qilish huquqi yo'q")
    
    old_status = order.status
    order.status = "Yakunlandi"
    
    history = models.OrderStatusHistory(
        order_id=order.id,
        old_status=old_status,
        new_status="Yakunlandi",
        note="Mijoz topshirilgan loyihani to'liq qabul qildi",
        changed_by_user_id=current_user.id
    )
    db.add(history)
    
    # Notify admin
    admin_user = db.query(models.User).filter(models.User.role == "admin").first()
    if admin_user:
        db.add(models.Notification(
            user_id=admin_user.id,
            title="Loyiha qabul qilindi!",
            message=f"{order.order_number}: Mijoz loyihani muvaffaqiyatli qabul qildi.",
            link=f"/admin?tab=orders"
        ))
    db.commit()
    db.refresh(order)
    return order

# --- Revision Request (O'zgartirish so'rash) ---
@router.post("/{id}/revision", response_model=schemas.OrderOut)
def request_order_revision(id: int, payload: schemas.OrderStatusUpdate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    if current_user.role != "admin" and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sizda o'zgartirish so'rash huquqi yo'q")

    note_text = payload.note or "Mijoz loyihaga tahrir va o'zgartirish kiritishni so'radi"
    old_status = order.status
    order.status = "Tahrirlashda"

    history = models.OrderStatusHistory(
        order_id=order.id,
        old_status=old_status,
        new_status="Tahrirlashda",
        note=note_text,
        changed_by_user_id=current_user.id
    )
    db.add(history)

    # Chatga ham tahrir so'rovi xabarini qo'shish
    db.add(models.Message(
        order_id=order.id,
        sender_id=current_user.id,
        text=f"🔄 [O'zgartirish so'rovi]: {note_text}"
    ))

    # Notify admin
    admin_user = db.query(models.User).filter(models.User.role == "admin").first()
    if admin_user:
        db.add(models.Notification(
            user_id=admin_user.id,
            title="O'zgartirish so'rovi",
            message=f"{order.order_number}: Mijoz loyiha bo'yicha tahrir kiritishni so'radi.",
            link=f"/admin?tab=orders"
        ))

    db.commit()
    db.refresh(order)
    return order

# --- Order Files (Loyiha fayllari) ---
@router.get("/{id}/files", response_model=list[schemas.OrderFileOut])
def get_order_files(id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    if current_user.role != "admin" and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sizda boshqa mijozning buyurtma fayllarini ko'rish huquqi yo'q")
    
    return db.query(models.OrderFile).filter(models.OrderFile.order_id == id).order_by(models.OrderFile.created_at.desc()).all()

@router.post("/{id}/files", response_model=schemas.OrderFileOut)
async def upload_order_file(id: int, file: UploadFile = File(...), current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    if current_user.role != "admin" and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sizda fayl yuklash huquqi yo'q")

    upload_dir = os.path.join("static", "uploads", "orders")
    os.makedirs(upload_dir, exist_ok=True)
    
    clean_filename = os.path.basename(file.filename or "fayl")
    ext = os.path.splitext(clean_filename)[1]
    unique_name = f"order_{order.id}_{uuid.uuid4().hex[:8]}{ext}"
    file_path = os.path.join(upload_dir, unique_name)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    size_kb = len(content) / 1024
    size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{(size_kb/1024):.1f} MB"

    order_file = models.OrderFile(
        order_id=order.id,
        uploader_id=current_user.id,
        filename=clean_filename,
        file_url=f"/static/uploads/orders/{unique_name}",
        file_size=size_str
    )
    db.add(order_file)
    
    # Notify other party
    target_user_id = order.user_id if current_user.role == "admin" else (
        db.query(models.User).filter(models.User.role == "admin").first().id
    )
    db.add(models.Notification(
        user_id=target_user_id,
        title="Yangi fayl yuklandi",
        message=f"{order.order_number}: {clean_filename} fayli biriktirildi.",
        link=f"/buyurtmalar/{order.id}"
    ))

    db.commit()
    db.refresh(order_file)
    return order_file

# --- Reviews & Ratings (Baholash) ---
@router.post("/{id}/review", response_model=schemas.ReviewOut)
def create_order_review(id: int, review_in: schemas.ReviewCreate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    if current_user.role != "admin" and order.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Sizda bu buyurtmaga sharh yozish huquqi yo'q")

    if review_in.rating < 1 or review_in.rating > 5:
        raise HTTPException(status_code=400, detail="Baholash 1 dan 5 yulduzgacha bo'lishi kerak")

    existing_review = db.query(models.Review).filter(models.Review.order_id == id).first()
    if existing_review:
        existing_review.rating = review_in.rating
        existing_review.comment = review_in.comment
        db.commit()
        db.refresh(existing_review)
        rev = existing_review
    else:
        rev = models.Review(
            order_id=order.id,
            user_id=current_user.id,
            service_id=order.service_id,
            rating=review_in.rating,
            comment=review_in.comment
        )
        db.add(rev)
        db.commit()
        db.refresh(rev)

    # Notify admin
    admin_user = db.query(models.User).filter(models.User.role == "admin").first()
    if admin_user:
        db.add(models.Notification(
            user_id=admin_user.id,
            title="Yangi sharh va baho!",
            message=f"{order.order_number} uchun {review_in.rating} ⭐ baho qoldirildi: '{review_in.comment[:50]}...'",
            link="/admin?tab=reviews"
        ))
        db.commit()

    return schemas.ReviewOut(
        id=rev.id,
        order_id=rev.order_id,
        user_id=rev.user_id,
        user_name=current_user.name,
        service_id=rev.service_id,
        service_title=order.service_title_snapshot,
        rating=rev.rating,
        comment=rev.comment,
        created_at=rev.created_at
    )

@router.get("/{id}/review", response_model=schemas.ReviewOut)
def get_order_review(id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Buyurtma topilmadi")
    rev = db.query(models.Review).filter(models.Review.order_id == id).first()
    if not rev:
        raise HTTPException(status_code=404, detail="Ushbu buyurtmaga sharh topilmadi")
    return schemas.ReviewOut(
        id=rev.id,
        order_id=rev.order_id,
        user_id=rev.user_id,
        user_name=rev.user.name if rev.user else "Mijoz",
        service_id=rev.service_id,
        service_title=order.service_title_snapshot,
        rating=rev.rating,
        comment=rev.comment,
        created_at=rev.created_at
    )

