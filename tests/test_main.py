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

import main
main.MAINTENANCE_MODE = False

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

# Test 8: Ism xavfsizlik filtri va Unikallik
def test_name_profanity_and_uniqueness(db_session):
    # Try register with profanity
    res = client.post("/api/auth/register", json={
        "name": "bad_ahmoq_user",
        "email": "profane@test.uz",
        "phone": "+998901112233",
        "password": "pass123"
    })
    assert res.status_code == 400
    assert "taqiqlangan" in res.json()["detail"] or "inappropriate" in res.json()["detail"]

    # Try duplicate name (Mijoz1 already seeded)
    res2 = client.post("/api/auth/register", json={
        "name": "Mijoz1",
        "email": "unique_email@test.uz",
        "phone": "+998901112233",
        "password": "pass123"
    })
    assert res2.status_code == 400
    assert "band qilingan" in res2.json()["detail"] or "taken" in res2.json()["detail"]


# Test 9: Rasmlarni optimallashtirish (WebP) va Brauzer Kesh (Cache-Control)
def test_image_optimization_and_caching(db_session):
    from PIL import Image
    import io

    m1_token = get_token("m1@falcon.uz", "mijoz123")
    m1_headers = {"Authorization": f"Bearer {m1_token}"}

    # Create dummy image in memory
    img = Image.new("RGB", (600, 600), color="blue")
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)

    # Upload avatar
    res = client.post(
        "/api/auth/avatar",
        files={"file": ("photo.jpg", buf, "image/jpeg")},
        headers=m1_headers
    )
    assert res.status_code == 200
    data = res.json()
    assert data["avatar_url"].endswith(".webp")
    assert "/static/uploads/avatars/" in data["avatar_url"]

    # Verify static cache header
    static_res = client.get(data["avatar_url"])
    assert static_res.status_code == 200
    assert "Cache-Control" in static_res.headers
    assert "max-age=604800" in static_res.headers["Cache-Control"]


# Test 10: Maintenance Mode (Texnik sozlash rejimi va maintenance.png)
def test_maintenance_mode():
    import main

    # Initially False
    main.MAINTENANCE_MODE = False
    res_normal = client.get("/")
    assert res_normal.status_code == 200

    # Turn on Maintenance Mode
    main.MAINTENANCE_MODE = True
    try:
        # Status endpoint works
        st_res = client.get("/api/maintenance/status")
        assert st_res.status_code == 200
        assert st_res.json()["maintenance"] is True

        # Public page returns 503 and contains maintenance image
        page_res = client.get("/")
        assert page_res.status_code == 503
        assert "maintenance.png" in page_res.text

        # API returns 503 JSON
        api_res = client.get("/api/services")
        assert api_res.status_code == 503
        assert api_res.json()["maintenance"] is True

        # Static assets still accessible
        static_res = client.get("/static/maintenance.png")
        assert static_res.status_code == 200
    finally:
        # Revert back to False
        main.MAINTENANCE_MODE = False


# Test 11: Real-time jonli statistika va KPI hisob-kitoblari
def test_realtime_statistics(db_session):
    import main
    main.MAINTENANCE_MODE = False

    # 1. Public stats endpoint
    res = client.get("/api/stats")
    assert res.status_code == 200
    stats = res.json()
    assert "active_services" in stats
    assert "registered_clients" in stats
    assert "completed_projects" in stats
    assert "total_orders" in stats
    assert isinstance(stats["registered_clients"], int)

    # 2. Admin dashboard live statistics
    admin_token = get_token("admin_test@falcon.uz", "admin123")
    dash_res = client.get("/api/admin/dashboard", headers={"Authorization": f"Bearer {admin_token}"})
    assert dash_res.status_code == 200
    dash = dash_res.json()
    assert "total_orders" in dash
    assert "new_orders_count" in dash
    assert "in_progress_orders_count" in dash
    assert "completed_orders_count" in dash
    assert "cancelled_orders_count" in dash
    assert "completed_orders_sum" in dash
    assert "total_revenue_potential" in dash
    assert "total_users_count" in dash
    assert "total_services_count" in dash
    assert "average_order_value" in dash
    assert "status_distribution" in dash
    assert "top_services" in dash
    assert "recent_activity" in dash
    assert isinstance(dash["recent_activity"], list)
    if len(dash["recent_activity"]) > 0:
        act = dash["recent_activity"][0]
        assert "order_number" in act
        assert "project_name" in act
        assert "client_name" in act
        assert "price" in act
        assert "status" in act
        assert "time" in act




# Test 12: Google orqali avtorizatsiya va qurilma eslab qolishi
def test_google_auth(db_session):
    # 1. Yangi Google foydalanuvchisi kirishi
    payload = {
        "email": "google_user@gmail.com",
        "name": "Google User",
        "avatar_url": "https://lh3.googleusercontent.com/test_avatar"
    }
    res = client.post("/api/auth/google", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["email"] == "google_user@gmail.com"
    assert data["name"] == "Google User"
    
    # Cookie tekshiruvi (device persistence - access_token o'rnatilgan)
    assert "access_token" in res.cookies

    # 2. Xuddi shu Google foydalanuvchisi qayta kirganda
    res2 = client.post("/api/auth/google", json=payload)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["email"] == "google_user@gmail.com"
    assert data2["id"] == data["id"]

# Test 13: 7 kunlik HttpOnly Cookie va Logout
def test_persistent_cookie_and_logout(db_session):
    # Kirish va cookie tekshirish
    res = client.post("/api/auth/login", data={"username": "m1@falcon.uz", "password": "mijoz123"})
    assert res.status_code == 200
    assert "access_token" in res.cookies
    
    # Cookie orqali /api/auth/me chaqirish
    me_res = client.get("/api/auth/me")
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "m1@falcon.uz"
    
    # Logout chaqirish
    logout_res = client.post("/api/auth/logout")
    assert logout_res.status_code == 200

# Test 14: Slug bo'yicha xizmatni olish
def test_service_slug_retrieval(db_session):
    srv = db_session.query(models.Service).first()
    srv.slug = "test-xizmat-slug"
    db_session.commit()

    # ID bo'yicha olish
    res_id = client.get(f"/api/services/{srv.id}")
    assert res_id.status_code == 200
    assert res_id.json()["id"] == srv.id

    # Slug bo'yicha olish
    res_slug = client.get(f"/api/services/{srv.slug}")
    assert res_slug.status_code == 200
    assert res_slug.json()["title"] == srv.title

# Test 15: Bildirishnomalar (Notifications) API
def test_notifications_flow(db_session):
    user = db_session.query(models.User).filter(models.User.email == "m1@falcon.uz").first()
    login_res = client.post("/api/auth/login", data={"username": "m1@falcon.uz", "password": "mijoz123"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Yangi bildirishnoma qo'shamiz
    notif = models.Notification(
        user_id=user.id,
        title="Test xabarnoma",
        message="Sizning buyurtmangiz qabul qilindi",
        link="/dashboard",
        is_read=False
    )
    db_session.add(notif)
    db_session.commit()

    # Unread count
    count_res = client.get("/api/notifications/unread-count", headers=headers)
    assert count_res.status_code == 200
    assert count_res.json()["unread_count"] >= 1

    # Get notifications list
    list_res = client.get("/api/notifications", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # Mark as read
    patch_res = client.patch(f"/api/notifications/{notif.id}/read", headers=headers)
    assert patch_res.status_code == 200
    assert patch_res.json()["is_read"] is True

    # Mark all read
    all_res = client.patch("/api/notifications/read-all", headers=headers)
    assert all_res.status_code == 200

# Test 16: Texnik topshiriq 50 belgi va Bekor qilish sababi
def test_tt_length_and_cancel_reason(db_session):
    srv = db_session.query(models.Service).first()
    srv.is_archived = False
    db_session.commit()
    user = db_session.query(models.User).filter(models.User.email == "m1@falcon.uz").first()
    token = client.post("/api/auth/login", data={"username": "m1@falcon.uz", "password": "mijoz123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. 50 belgidan kam topshiriq xatolik berishi kerak
    short_tt_payload = {
        "service_id": srv.id,
        "project_name": "Test Qisqa TT",
        "technical_task": "Bu juda qisqa matn",
        "desired_deadline": str(date.today() + timedelta(days=srv.delivery_days + 1)),
        "contact_phone": "+998901234567"
    }
    short_res = client.post("/api/orders", json=short_tt_payload, headers=headers)
    assert short_res.status_code == 400
    assert "kamida 50 ta" in short_res.json()["detail"]

    # 2. To'g'ri topshiriq bilan yaratish
    valid_tt_payload = {
        "service_id": srv.id,
        "project_name": "Test Valid TT",
        "technical_task": "Ushbu loyiha uchun to'liq texnik topshiriq matni kamida ellikta belgidan oshiq bo'lishi kerak.",
        "desired_deadline": str(date.today() + timedelta(days=srv.delivery_days + 2)),
        "contact_phone": "+998901234567"
    }
    create_res = client.post("/api/orders", json=valid_tt_payload, headers=headers)
    assert create_res.status_code == 200
    created_order = create_res.json()

    # 3. Bekor qilish sababi bilan bekor qilish
    cancel_res = client.patch(
        f"/api/orders/{created_order['id']}/status",
        json={"status": "Bekor qilindi", "note": "Rejalar o'zgardi va loyiha to'xtatildi"},
        headers=headers
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "Bekor qilindi"
    assert cancel_res.json()["cancel_reason"] == "Rejalar o'zgardi va loyiha to'xtatildi"

# Test 17: Admin Activity Log, Settings, Reports, User Detail
def test_admin_new_features(db_session):
    admin_token = client.post("/api/auth/login", data={"username": "admin_test@falcon.uz", "password": "admin123"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Activity log
    act_res = client.get("/api/admin/activity-log", headers=headers)
    assert act_res.status_code == 200
    assert isinstance(act_res.json(), list)

    # 2. Settings update
    set_res = client.put("/api/admin/settings", json={"key": "site_name", "value": "Falcon Pro Platform"}, headers=headers)
    assert set_res.status_code == 200
    assert set_res.json()["value"] == "Falcon Pro Platform"

    get_set = client.get("/api/admin/settings", headers=headers)
    assert get_set.status_code == 200
    assert any(s["key"] == "site_name" for s in get_set.json())

    # 3. Reports
    rep_res = client.get("/api/admin/reports", headers=headers)
    assert rep_res.status_code == 200
    rep_data = rep_res.json()
    assert "total_orders" in rep_data
    assert "completed_orders" in rep_data

    # 4. User detail with orders
    user = db_session.query(models.User).filter(models.User.email == "m1@falcon.uz").first()
    user_detail_res = client.get(f"/api/admin/users/{user.id}", headers=headers)
    assert user_detail_res.status_code == 200
    ud_data = user_detail_res.json()
    assert ud_data["id"] == user.id
    assert "orders" in ud_data

# Test 18: Sahifalar (Pages) marshrutlari yuklanishi
def test_page_routes():
    pages = [
        "/",
        "/xizmatlar",
        "/portfolio",
        "/narxlar",
        "/faq",
        "/aloqa",
        "/kirish",
        "/royxatdan-otish",
        "/buyurtma/muvaffaqiyat",
        "/biz-haqimizda",
        "/yordam",
        "/parolni-tiklash",
        "/yangi-parol"
    ]
    for p in pages:
        res = client.get(p)
        assert res.status_code == 200

# Test 19: Parolni tiklash (Password Reset Flow)
def test_password_reset_flow(db_session):
    # 1. So'rov yuborish
    req_res = client.post("/api/auth/forgot-password", json={"email": "m1@falcon.uz"})
    assert req_res.status_code == 200
    assert "token" in req_res.json()
    reset_token = req_res.json()["token"]

    # 2. Yangi parol o'rnatish
    reset_res = client.post("/api/auth/reset-password", json={
        "token": reset_token,
        "new_password": "newpassword123"
    })
    assert reset_res.status_code == 200

    # 3. Yangi parol bilan kirish
    login_res = client.post("/api/auth/login", data={"username": "m1@falcon.uz", "password": "newpassword123"})
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()

    # Eski parol ishlamasligi kerak (401 Unauthorized)
    old_res = client.post("/api/auth/login", data={"username": "m1@falcon.uz", "password": "mijoz123"})
    assert old_res.status_code == 401

# Test 20: Portfolio, Jamoa va Bannerlar boshqaruvi
def test_portfolio_team_banners(db_session):
    admin_token = client.post("/api/auth/login", data={"username": "admin_test@falcon.uz", "password": "admin123"}).json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. Portfolio loyihasi qo'shish
    port_payload = {
        "title": "Avtomatlashtirilgan CRM Tizimi",
        "category_name": "Web & CRM",
        "client_name": "Global Logistika MCHJ",
        "short_desc": "Katta logistika kompaniyasi uchun buyurtma va to'lovlarni boshqarish tizimi",
        "full_desc": "To'liq avtomatlashtirilgan arxitektura, real vaqt rejimida yuklarni kuzatish va hisobotlar moduli.",
        "image_url": "/static/services/web-dev.webp",
        "technologies": "FastAPI, Vue.js, PostgreSQL",
        "results_summary": "+180% Ish unumdorligi",
        "live_url": "https://example.com/crm"
    }
    p_create = client.post("/api/admin/projects", json=port_payload, headers=admin_headers)
    assert p_create.status_code == 200
    project_data = p_create.json()
    assert project_data["title"] == port_payload["title"]

    # Public ro'yxat va tafsilot
    p_list = client.get("/api/projects")
    assert p_list.status_code == 200
    assert any(x["id"] == project_data["id"] for x in p_list.json())

    p_detail = client.get(f"/api/projects/{project_data['slug']}")
    assert p_detail.status_code == 200
    assert p_detail.json()["slug"] == project_data["slug"]

    # 2. Jamoa a'zosi qo'shish
    team_payload = {
        "name": "Alisher Usmonov",
        "role": "Senior Frontend Developer",
        "avatar_url": "/static/default-avatar.png",
        "skills": "React, Tailwind, TypeScript",
        "bio": "5 yillik tajribaga ega frontend muhandisi",
        "display_order": 1
    }
    t_create = client.post("/api/admin/team", json=team_payload, headers=admin_headers)
    assert t_create.status_code == 200
    team_id = t_create.json()["id"]

    t_list = client.get("/api/team")
    assert t_list.status_code == 200
    assert any(x["id"] == team_id for x in t_list.json())

    # 3. Banner qo'shish
    ban_payload = {
        "title": "Kuzgi chegirmalar mavsumi!",
        "subtitle": "Barcha web-loyihalarga 20% maxsus chegirma",
        "link_url": "/xizmatlar",
        "is_active": True
    }
    b_create = client.post("/api/admin/banners", json=ban_payload, headers=admin_headers)
    assert b_create.status_code == 200

    b_list = client.get("/api/banners")
    assert b_list.status_code == 200
    assert len(b_list.json()) > 0

# Test 21: Buyurtma fayllari va Sharh qoldirish
def test_order_files_and_reviews(db_session):
    m1_token = client.post("/api/auth/login", data={"username": "m1@falcon.uz", "password": "newpassword123"}).json()["access_token"]
    m1_headers = {"Authorization": f"Bearer {m1_token}"}
    admin_token = client.post("/api/auth/login", data={"username": "admin_test@falcon.uz", "password": "admin123"}).json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    srv = db_session.query(models.Service).first()
    # 1. Yangi buyurtma yaratish
    order_payload = {
        "service_id": srv.id,
        "project_name": "Fayl va Sharh Loyihasi",
        "technical_task": "Ushbu buyurtmaga fayllar biriktiriladi va yakunlangach mijoz tomonidan besh yulduzli sharh yoziladi.",
        "desired_deadline": str(date.today() + timedelta(days=12)),
        "contact_phone": "+998901234567"
    }
    ord_res = client.post("/api/orders", json=order_payload, headers=m1_headers)
    assert ord_res.status_code == 200
    order_id = ord_res.json()["id"]

    # 2. Fayl yuklash (Multipart file upload)
    file_bytes = b"PDF hujjat sinovi uchun fayl mazmuni"
    file_res = client.post(
        f"/api/orders/{order_id}/files",
        files={"file": ("texnik_topshiriq.pdf", file_bytes, "application/pdf")},
        headers=m1_headers
    )
    assert file_res.status_code == 200
    assert file_res.json()["filename"] == "texnik_topshiriq.pdf"

    files_get = client.get(f"/api/orders/{order_id}/files", headers=m1_headers)
    assert files_get.status_code == 200
    assert len(files_get.json()) >= 1

    # 3. Statusni o'zgartirish: Qabul qilindi -> Jarayonda -> Yakunlandi
    client.patch(f"/api/orders/{order_id}/status", json={"status": "Qabul qilindi"}, headers=admin_headers)
    client.patch(f"/api/orders/{order_id}/status", json={"status": "Jarayonda"}, headers=admin_headers)
    client.patch(f"/api/orders/{order_id}/status", json={"status": "Yakunlandi"}, headers=admin_headers)

    # 4. Sharh qoldirish (5 yulduz)
    review_payload = {
        "rating": 5,
        "comment": "A'lo darajada bajarildi, xizmat sifati juda yuqori!"
    }
    rev_res = client.post(f"/api/orders/{order_id}/review", json=review_payload, headers=m1_headers)
    assert rev_res.status_code == 200
    assert rev_res.json()["rating"] == 5

    # 5. Public sharhlarda ko'rinishi
    pub_revs = client.get("/api/reviews")
    assert pub_revs.status_code == 200
    assert any(r["comment"] == review_payload["comment"] for r in pub_revs.json())

# Test 22: Qabul qilish (Accept) va O'zgartirish so'rash (Revision)
def test_order_revision_and_accept(db_session):
    m1_token = client.post("/api/auth/login", data={"username": "m1@falcon.uz", "password": "newpassword123"}).json()["access_token"]
    m1_headers = {"Authorization": f"Bearer {m1_token}"}
    admin_token = client.post("/api/auth/login", data={"username": "admin_test@falcon.uz", "password": "admin123"}).json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    srv = db_session.query(models.Service).first()
    ord_res = client.post("/api/orders", json={
        "service_id": srv.id,
        "project_name": "Tahrirlash va Tasdiqlash",
        "technical_task": "Ushbu buyurtmada tahrirlash talabi va to'g'ridan-to'g'ri qabul qilish sinovdan o'tkaziladi.",
        "desired_deadline": str(date.today() + timedelta(days=15)),
        "contact_phone": "+998901234567"
    }, headers=m1_headers)
    order_id = ord_res.json()["id"]

    # Jarayonda holatiga keltirish
    client.patch(f"/api/orders/{order_id}/status", json={"status": "Qabul qilindi"}, headers=admin_headers)
    client.patch(f"/api/orders/{order_id}/status", json={"status": "Jarayonda"}, headers=admin_headers)

    # 1. Revision so'rash
    rev_res = client.post(f"/api/orders/{order_id}/revision", json={"note": "Ranglar sxemasini ko'k rangga moslang"}, headers=m1_headers)
    assert rev_res.status_code == 200
    assert rev_res.json()["status"] == "Tahrirlashda"

    # 2. Qabul qilish (Accept)
    acc_res = client.post(f"/api/orders/{order_id}/accept", headers=m1_headers)
    assert acc_res.status_code == 200
    assert acc_res.json()["status"] == "Yakunlandi"

# Test 23: Qo'llab-quvvatlash (Support Ticket) va Admin javobi
def test_support_ticket_flow(db_session):
    # 1. Mijoz ticket yaratishi
    ticket_payload = {
        "name": "Bekzod Shukurov",
        "email": "m1@falcon.uz",
        "phone": "+998901234567",
        "subject": "To'lov haqida savol",
        "category": "To'lovlar",
        "message": "Click orqali hisob-kitob qilishda chek qanday olinadi?"
    }
    t_create = client.post("/api/support", json=ticket_payload)
    assert t_create.status_code == 200
    ticket_id = t_create.json()["id"]

    # 2. Admin ro'yxatni ko'rishi
    admin_token = client.post("/api/auth/login", data={"username": "admin_test@falcon.uz", "password": "admin123"}).json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    t_list = client.get("/api/admin/support", headers=admin_headers)
    assert t_list.status_code == 200
    assert any(x["id"] == ticket_id for x in t_list.json())

    # 3. Admin javob berishi
    reply_payload = {
        "admin_reply": "Chek profilingizdagi 'To'lovlar' bo'limida avtomatik shakllanadi.",
        "status": "Hal qilindi"
    }
    reply_res = client.patch(f"/api/admin/support/{ticket_id}/reply", json=reply_payload, headers=admin_headers)
    assert reply_res.status_code == 200
    assert reply_res.json()["status"] == "Hal qilindi"
    assert reply_res.json()["admin_reply"] == reply_payload["admin_reply"]

# Test 24: Admin Broadcast bildirishnomasi
def test_admin_broadcast(db_session):
    admin_token = client.post("/api/auth/login", data={"username": "admin_test@falcon.uz", "password": "admin123"}).json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    bc_res = client.post("/api/admin/broadcast", json={
        "title": "Yangi Funksiya Ishga Tushdi!",
        "message": "Endi barcha buyurtmalaringizga to'g'ridan-to'g'ri fayllar yuklashingiz mumkin.",
        "link": "/dashboard"
    }, headers=admin_headers)
    assert bc_res.status_code == 200
    assert "foydalanuvchiga bildirishnoma yuborildi" in bc_res.json()["detail"]
