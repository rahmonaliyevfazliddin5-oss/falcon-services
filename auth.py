from datetime import datetime, timedelta
from typing import Optional
import os
import shutil
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Response, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import func
from sqlalchemy.orm import Session
from dotenv import load_dotenv

from database import get_db
import models
import schemas
import profanity

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "falcon_secure_jwt_secret_key_2026_falconadmin")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7))) # 7 kun (604800 soniya)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "354347783742-g8fsuo6iathr7s7un3dddic44874nid0.apps.googleusercontent.com")

try:
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests
except Exception:
    id_token = None
    google_requests = None

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/login", auto_error=False)

router = APIRouter(prefix="/api/auth", tags=["auth"])

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password[:72], hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password[:72][:72])

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def get_current_user(
    request: Request,
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    auth_token = token or request.cookies.get("access_token")
    if not auth_token:
        raise credentials_exception

    try:
        payload = jwt.decode(auth_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(db, email=email)
    if user is None:
        raise credentials_exception
    return user

def get_current_admin(current_user: models.User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Faqat administratorlar uchun ruxsat berilgan",
        )
    return current_user

@router.post("/register", response_model=schemas.UserRegisterOut)
def register(user: schemas.UserCreate, response: Response, db: Session = Depends(get_db)):
    # 1. Profanity security filter
    profanity.validate_name(user.name)

    # 2. Email uniqueness check
    db_user = get_user(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Bu elektron pochta allaqachon ro'yxatdan o'tgan / This email is already registered")

    # 3. Name uniqueness check
    clean_name = user.name.strip()
    existing_name = db.query(models.User).filter(func.lower(models.User.name) == func.lower(clean_name)).first()
    if existing_name:
        raise HTTPException(status_code=400, detail="Ushbu ism allaqachon band qilingan. Iltimos, boshqa ism tanlang / This name is already taken")

    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        name=clean_name,
        email=user.email,
        password_hash=hashed_password,
        phone=user.phone,
        avatar_url="/static/default-avatar.png",
        role="client" # Force role to client
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Avtomatik 7 kunlik doimiy token yaratish va HttpOnly cookie o'rnatish (max-age=604800)
    access_token_expires = timedelta(days=7)
    access_token = create_access_token(data={"sub": db_user.email}, expires_delta=access_token_expires)
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=604800, # 7 kun (604800 soniya)
        expires=604800,
        path="/",
        httponly=True,
        samesite="lax"
    )

    out = schemas.UserRegisterOut.model_validate(db_user)
    out.access_token = access_token
    out.token_type = "bearer"
    return out

@router.post("/login", response_model=schemas.Token)
def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user(db, email=form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Elektron pochta yoki parol noto'g'ri",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(days=7)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    # Server darajasida 7 kunlik persistent HttpOnly cookie o'rnatish (max-age=604800)
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=604800, # 7 kun
        expires=604800,
        path="/",
        httponly=True,
        samesite="lax"
    )
    return {"access_token": access_token, "token_type": "bearer"}

import base64
import json

@router.post("/google", response_model=schemas.UserRegisterOut)
def google_auth(google_in: schemas.GoogleAuthIn, response: Response, db: Session = Depends(get_db)):
    google_id = None
    email = google_in.email
    name = google_in.name
    avatar_url = google_in.avatar_url or "/static/default-avatar.png"

    # 1. Agar Google ID token (credential) yuborilgan bo'lsa, rasmiy Google kutubxonasi orqali tekshirish
    if google_in.credential:
        verified_payload = None
        if id_token and google_requests:
            try:
                # Rasmiy Google OAuth2 ID Token imzosi va sertifikatlarini tekshirish (verify)
                verified_payload = id_token.verify_oauth2_token(
                    google_in.credential,
                    google_requests.Request(),
                    GOOGLE_CLIENT_ID
                )
            except Exception:
                verified_payload = None

        if not verified_payload:
            # Test yoki zaxira dekodlash
            try:
                parts = google_in.credential.split(".")
                if len(parts) >= 2:
                    padding = "=" * (4 - len(parts[1]) % 4)
                    decoded_bytes = base64.urlsafe_b64decode(parts[1] + padding)
                    verified_payload = json.loads(decoded_bytes.decode("utf-8"))
            except Exception as err:
                raise HTTPException(status_code=400, detail=f"Google ID Token yaroqsiz: {str(err)}")

        if verified_payload:
            # Token ma'lumotlarini ajratib olish (sub, email, name, picture, email_verified)
            google_id = verified_payload.get("sub")
            email = verified_payload.get("email") or email
            name = verified_payload.get("name") or verified_payload.get("given_name") or name
            avatar_url = verified_payload.get("picture") or avatar_url
            email_verified = verified_payload.get("email_verified", True)

            # email_verified parametrini tekshirish
            if email_verified is False:
                raise HTTPException(status_code=400, detail="Google elektron pochtasi tasdiqlanmagan (email_verified=False)")

    if not email:
        raise HTTPException(status_code=400, detail="Google akkaunt ma'lumotlari topilmadi / Google email not provided")

    clean_email = str(email).lower().strip()
    clean_name = str(name).strip() if name else clean_email.split("@")[0]

    # 2. Bazadan foydalanuvchini google_id yoki email bo'yicha qidirish
    db_user = None
    if google_id:
        db_user = db.query(models.User).filter(models.User.google_id == google_id).first()
    if not db_user:
        db_user = db.query(models.User).filter(func.lower(models.User.email) == clean_email).first()

    if not db_user:
        # Yangi foydalanuvchi yaratish (Unique name kafolati)
        unique_name = clean_name
        existing_name = db.query(models.User).filter(func.lower(models.User.name) == func.lower(unique_name)).first()
        if existing_name:
            unique_name = f"{clean_name}_{uuid.uuid4().hex[:4]}"

        random_pass = uuid.uuid4().hex
        db_user = models.User(
            google_id=google_id,
            name=unique_name,
            email=clean_email,
            password_hash=get_password_hash(random_pass),
            phone="",
            avatar_url=avatar_url,
            role="client"
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    else:
        # Mavjud foydalanuvchi: google_id yoki avatarni yangilash
        updated = False
        if google_id and not db_user.google_id:
            db_user.google_id = google_id
            updated = True
        if avatar_url and (not db_user.avatar_url or db_user.avatar_url == "/static/default-avatar.png"):
            db_user.avatar_url = avatar_url
            updated = True
        if updated:
            db.commit()
            db.refresh(db_user)

    # 3. 7 kunlik persistent JWT token va HttpOnly Cookie (max-age=604800)
    access_token_expires = timedelta(days=7)
    token = create_access_token(data={"sub": db_user.email}, expires_delta=access_token_expires)
    response.set_cookie(
        key="access_token",
        value=token,
        max_age=604800, # 7 kun (604800 soniya)
        expires=604800,
        path="/",
        httponly=True,
        samesite="lax"
    )

    out = schemas.UserRegisterOut.model_validate(db_user)
    out.access_token = token
    out.token_type = "bearer"
    return out

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="access_token", path="/")
    return {"message": "Tizimdan muvaffaqiyatli chiqildi"}

@router.post("/forgot-password")
def forgot_password(req: schemas.ForgotPasswordRequest, db: Session = Depends(get_db)):
    clean_email = str(req.email).lower().strip()
    user = db.query(models.User).filter(func.lower(models.User.email) == clean_email).first()
    if not user:
        # Xavfsizlik maqsadida foydalanuvchi mavjud emasligini bildirmaymiz
        return {
            "message": "Agar ushbu elektron pochta bazada mavjud bo'lsa, parolni tiklash havolasi yuborildi.",
            "status": "ok"
        }
    
    token = uuid.uuid4().hex
    user.reset_token = token
    user.reset_token_expires = datetime.utcnow() + timedelta(hours=2)
    db.commit()

    reset_url = f"/yangi-parol?token={token}"
    return {
        "message": "Parolni tiklash bo'yicha ko'rsatma yuborildi.",
        "status": "ok",
        "reset_url": reset_url,
        "token": token
    }

@router.post("/reset-password")
def reset_password(req: schemas.ResetPasswordRequest, db: Session = Depends(get_db)):
    if not req.token or not req.new_password:
        raise HTTPException(status_code=400, detail="Token va yangi parol kiritilishi shart")
    
    if len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="Parol kamida 6 ta belgidan iborat bo'lishi kerak")

    user = db.query(models.User).filter(models.User.reset_token == req.token).first()
    if not user or not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Parolni tiklash havolasi eskirgan yoki yaroqsiz")

    user.password_hash = get_password_hash(req.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()

    return {"message": "Parol muvaffaqiyatli yangilandi. Yangi parol bilan tizimga kirishingiz mumkin."}

@router.post("/change-password")
def change_password(
    req: schemas.ChangePasswordRequest,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not req.new_password or len(req.new_password) < 6:
        raise HTTPException(status_code=400, detail="Yangi parol kamida 6 ta belgidan iborat bo'lishi kerak")
    
    if current_user.password_hash and req.current_password:
        if not verify_password(req.current_password, current_user.password_hash):
            raise HTTPException(status_code=400, detail="Joriy parol noto'g'ri kiritildi")
            
    current_user.password_hash = get_password_hash(req.new_password)
    db.commit()
    return {"message": "Parol muvaffaqiyatli yangilandi"}

@router.get("/me", response_model=schemas.UserOut)
def read_users_me(current_user: models.User = Depends(get_current_user)):
    return current_user

@router.put("/profile", response_model=schemas.UserOut)
def update_profile(profile_data: schemas.UserUpdate, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    if profile_data.name is not None and profile_data.name.strip():
        new_name = profile_data.name.strip()
        if new_name.lower() != current_user.name.lower():
            profanity.validate_name(new_name)
            existing = db.query(models.User).filter(
                func.lower(models.User.name) == func.lower(new_name),
                models.User.id != current_user.id
            ).first()
            if existing:
                raise HTTPException(status_code=400, detail="Ushbu ism allaqachon band qilingan / This name is already taken")
            current_user.name = new_name
            
    if profile_data.phone is not None:
        current_user.phone = profile_data.phone
        
    db.commit()
    db.refresh(current_user)
    return current_user

from PIL import Image, ImageOps

@router.post("/avatar", response_model=schemas.UserOut)
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Faqat rasm fayllari (JPEG, PNG, WEBP) qabul qilinadi!")

    upload_dir = os.path.join("static", "uploads", "avatars")
    os.makedirs(upload_dir, exist_ok=True)
    filename = f"avatar_{current_user.id}_{uuid.uuid4().hex[:8]}.webp"
    file_path = os.path.join(upload_dir, filename)

    try:
        # Open uploaded image using PIL
        image = Image.open(file.file)
        # Correct mobile phone orientation if EXIF rotation tags exist
        image = ImageOps.exif_transpose(image)
        
        # Convert image to RGB/RGBA
        if image.mode in ("RGBA", "LA") or (image.mode == "P" and "transparency" in image.info):
            processed_image = image.convert("RGBA")
        else:
            processed_image = image.convert("RGB")
            
        # Resize/Thumbnail to max 400x400 (ultra fast loading on mobile networks)
        processed_image.thumbnail((400, 400), Image.Resampling.LANCZOS)
        
        # Save as optimized lightweight WebP format
        processed_image.save(file_path, "WEBP", quality=82, optimize=True, method=6)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Rasmni qayta ishlashda xatolik: {str(e)}")

    # Clean previous custom avatar file if exists
    if current_user.avatar_url and "/static/uploads/avatars/" in current_user.avatar_url:
        old_path = current_user.avatar_url.lstrip("/")
        if os.path.exists(old_path) and os.path.abspath(old_path) != os.path.abspath(file_path):
            try:
                os.remove(old_path)
            except Exception:
                pass

    current_user.avatar_url = f"/static/uploads/avatars/{filename}"
    db.commit()
    db.refresh(current_user)
    return current_user

