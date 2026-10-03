import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import date, timedelta
import os

from main import app
from database import Base, get_db
import models
from auth import get_password_hash

# Setup Test Database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_falcon.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module")
def db_session():
    db = TestingSessionLocal()
    # Seed minimal data for tests
    cat = models.Category(name="Test Kategoriya", slug="test-kat")
    db.add(cat)
    db.commit()
    
    srv = models.Service(category_id=cat.id, title="Test Xizmat", description="Test", image_url="http://t.co", price=1000000, delivery_days=5)
    db.add(srv)
    db.commit()

    admin = models.User(name="Admin", email="admin_test@falcon.uz", password_hash=get_password_hash("admin123"), role="admin")
    db.add(admin)
    
    mijoz1 = models.User(name="Mijoz1", email="m1@falcon.uz", password_hash=get_password_hash("mijoz123"), role="client")
    mijoz2 = models.User(name="Mijoz2", email="m2@falcon.uz", password_hash=get_password_hash("mijoz123"), role="client")
    db.add(mijoz1)
    db.add(mijoz2)
    db.commit()

    yield db
    db.close()
    # Teardown
    Base.metadata.drop_all(bind=engine)
    engine.dispose()
    if os.path.exists("./test_falcon.db"):
        os.remove("./test_falcon.db")

def get_token(email, password):
    res = client.post("/api/auth/login", data={"username": email, "password": password})
    return res.json()["access_token"]


# Test 1: Ro'yxatdan o'tish va Admin rolidan himoya
def test_register_and_role_protection(db_session):
    # Try to register as admin
    payload = {
        "name": "Xaker",
        "email": "xaker@falcon.uz",
        "phone": "+998900000000",
        "password": "password123",
        "role": "admin" # this should be ignored
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 200
    assert res.json()["role"] == "client"

    # Duplicate email
    res2 = client.post("/api/auth/register", json=payload)
    assert res2.status_code == 400


# Test 2: Buyurtma yaratish va Validatsiya
def test_order_creation_validation(db_session):
    token = get_token("m1@falcon.uz", "mijoz123")
    headers = {"Authorization": f"Bearer {token}"}
    
    srv = db_session.query(models.Service).first()
    
    # TT < 50 chars
    payload = {
        "service_id": srv.id,
        "project_name": "My Project",
        "technical_task": "Short task",
        "desired_deadline": str(date.today() + timedelta(days=10)),
        "contact_phone": "+998901234567"
    }
    res = client.post("/api/orders", json=payload, headers=headers)
    assert res.status_code == 400
    assert "Texnik topshiriq" in res.json()["detail"]

    # Deadline earlier than delivery_days
    payload["technical_task"] = "This is a very long technical task description that exceeds fifty characters easily to pass validation check."
    payload["desired_deadline"] = str(date.today() + timedelta(days=1)) # 1 < 5
    res2 = client.post("/api/orders", json=payload, headers=headers)
    assert res2.status_code == 400
    assert "muddatidan oldin" in res2.json()["detail"]

    # Success
    payload["desired_deadline"] = str(date.today() + timedelta(days=10))
    res3 = client.post("/api/orders", json=payload, headers=headers)
    assert res3.status_code == 200
    assert res3.json()["order_number"].startswith("ORD-")


# Test 3: Narxni saqlash (Price Snapshot)
def test_price_snapshot(db_session):
    # 1. Mijoz 1 order beradi
    m1_token = get_token("m1@falcon.uz", "mijoz123")
    m1_headers = {"Authorization": f"Bearer {m1_token}"}
    srv = db_session.query(models.Service).first()
    original_price = srv.price
    
    payload = {
        "service_id": srv.id,
        "project_name": "Snapshot Test",
        "technical_task": "This is a very long technical task description that exceeds fifty characters easily to pass validation check for snapshot.",
        "desired_deadline": str(date.today() + timedelta(days=10)),
        "contact_phone": "+123456789"
    }
    order_res = client.post("/api/orders", json=payload, headers=m1_headers)
    order_id = order_res.json()["id"]
    
    assert order_res.json()["price_snapshot"] == original_price

    # 2. Admin narxni o'zgartiradi
    admin_token = get_token("admin_test@falcon.uz", "admin123")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    new_price = original_price + 500000
    update_res = client.put(f"/api/admin/services/{srv.id}", json={"price": new_price}, headers=admin_headers)
    assert update_res.status_code == 200

    # 3. Eski buyurtma narxi o'zgarganmi tekshiramiz
    check_res = client.get(f"/api/orders/{order_id}", headers=m1_headers)
    assert check_res.json()["price_snapshot"] == original_price
    assert check_res.json()["price_snapshot"] != new_price


# Test 4: Mijozlararo huquqlar himoyasi (IDOR)
def test_idor_protection(db_session):
    m1_token = get_token("m1@falcon.uz", "mijoz123")
    m1_headers = {"Authorization": f"Bearer {m1_token}"}
    
    # Create order for m1
    srv = db_session.query(models.Service).first()
    payload = {
        "service_id": srv.id,
        "project_name": "IDOR Test",
        "technical_task": "This is a very long technical task description that exceeds fifty characters easily to pass validation check for snapshot.",
        "desired_deadline": str(date.today() + timedelta(days=10)),
        "contact_phone": "+123456789"
    }
    order_res = client.post("/api/orders", json=payload, headers=m1_headers)
    order_id = order_res.json()["id"]

    # Try access with m2
    m2_token = get_token("m2@falcon.uz", "mijoz123")
    m2_headers = {"Authorization": f"Bearer {m2_token}"}
    
    get_res = client.get(f"/api/orders/{order_id}", headers=m2_headers)
    assert get_res.status_code == 403

    msg_res = client.post(f"/api/orders/{order_id}/messages", json={"text": "Hello"}, headers=m2_headers)
    assert msg_res.status_code == 403


# Test 5: Admin API himoyasi
def test_admin_api_protection(db_session):
    m1_token = get_token("m1@falcon.uz", "mijoz123")
    m1_headers = {"Authorization": f"Bearer {m1_token}"}

    res = client.get("/api/admin/orders", headers=m1_headers)
    assert res.status_code == 403

    res2 = client.get("/api/admin/dashboard", headers=m1_headers)
    assert res2.status_code == 403


# Test 6: Buyurtma holatlari zanjiri (State Machine)
def test_state_machine(db_session):
    m1_token = get_token("m1@falcon.uz", "mijoz123")
    m1_headers = {"Authorization": f"Bearer {m1_token}"}
    admin_token = get_token("admin_test@falcon.uz", "admin123")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    srv = db_session.query(models.Service).first()
    payload = {
        "service_id": srv.id,
        "project_name": "State Test",
        "technical_task": "This is a very long technical task description that exceeds fifty characters easily to pass validation check.",
        "desired_deadline": str(date.today() + timedelta(days=10)),
        "contact_phone": "+123"
    }
    order_res = client.post("/api/orders", json=payload, headers=m1_headers)
    order_id = order_res.json()["id"]

    # 1. Yangi -> Yakunlandi (Must Fail)
    res = client.patch(f"/api/orders/{order_id}/status", json={"status": "Yakunlandi"}, headers=admin_headers)
    assert res.status_code == 400

    # 2. Mijoz Qabul qilindi qila olmasligi (Must fail 403)
    res2 = client.patch(f"/api/orders/{order_id}/status", json={"status": "Qabul qilindi"}, headers=m1_headers)
    assert res2.status_code == 403

    # 3. Admin to'g'ri zanjir bo'yicha o'zgartirishi
    steps = ["Qabul qilindi", "Jarayonda", "Yakunlandi"]
    for s in steps:
        r = client.patch(f"/api/orders/{order_id}/status", json={"status": s}, headers=admin_headers)
        assert r.status_code == 200
        assert r.json()["status"] == s
    
    # 4. Yakunlangan holatni qaytarib bo'lmasligi
    r2 = client.patch(f"/api/orders/{order_id}/status", json={"status": "Bekor qilindi"}, headers=admin_headers)
    assert r2.status_code == 400


# Test 7: Xizmatni arxivlash (Soft Delete)
def test_archive_service(db_session):
    admin_token = get_token("admin_test@falcon.uz", "admin123")
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    srv = db_session.query(models.Service).first()
    
    # Archive
    res = client.patch(f"/api/admin/services/{srv.id}/archive?is_archived=true", headers=admin_headers)
    assert res.status_code == 200

    # Verify hidden from public catalog
    res_public = client.get("/api/services")
    items = res_public.json()["items"]
    assert len(items) == 0

    # Old order should still exist and fetchable
    # We created orders previously
    orders = db_session.query(models.Order).all()
    assert len(orders) > 0
    assert orders[0].service_title_snapshot == srv.title
