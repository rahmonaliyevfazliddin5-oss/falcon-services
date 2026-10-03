from sqlalchemy.orm import Session
from database import engine, SessionLocal
import models
from auth import get_password_hash
from datetime import datetime

def seed_db():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # 1. Clear old orders, messages, history to start fresh
        db.query(models.Message).delete()
        db.query(models.OrderStatusHistory).delete()
        db.query(models.Order).delete()
        
        # 2. Preserve ONLY the main Falcon Admin account and remove old/test users
        db.query(models.User).filter(models.User.email != "falcon@admin.com").delete()
        
        admin = db.query(models.User).filter(models.User.email == "falcon@admin.com").first()
        if not admin:
            admin = models.User(
                name="Falcon Admin",
                email="falcon@admin.com",
                password_hash=get_password_hash("falconadmin777"),
                role="admin",
                avatar_url="/static/default-avatar.png",
                phone="+998998967440"
            )
            db.add(admin)
        else:
            admin.name = "Falcon Admin"
            admin.password_hash = get_password_hash("falconadmin777")
            admin.role = "admin"
            admin.phone = "+998998967440"
            if not admin.avatar_url:
                admin.avatar_url = "/static/default-avatar.png"
        db.commit()

        # 3. Clean and populate exact IT Services categories & services
        db.query(models.Service).delete()
        db.query(models.Category).delete()
        db.commit()

        categories_data = [
            models.Category(name="Web sayt yaratish", slug="web-sayt-yaratish"),
            models.Category(name="MVP qurish", slug="mvp-qurish"),
            models.Category(name="Mobil ilovalar", slug="mobil-ilovalar"),
            models.Category(name="SEO va Marketing", slug="seo-va-marketing"),
            models.Category(name="UI/UX Dizayn", slug="ui-ux-dizayn"),
            models.Category(name="DevOps va Bulut", slug="devops-va-bulut")
        ]
        db.add_all(categories_data)
        db.commit()

        cat_web = db.query(models.Category).filter(models.Category.slug == "web-sayt-yaratish").first()
        cat_mvp = db.query(models.Category).filter(models.Category.slug == "mvp-qurish").first()
        cat_mobile = db.query(models.Category).filter(models.Category.slug == "mobil-ilovalar").first()
        cat_seo = db.query(models.Category).filter(models.Category.slug == "seo-va-marketing").first()
        cat_uiux = db.query(models.Category).filter(models.Category.slug == "ui-ux-dizayn").first()
        cat_devops = db.query(models.Category).filter(models.Category.slug == "devops-va-bulut").first()

        active_working_link = "https://github.com/rahmonaliyevfazliddin5-oss/falcon-services"

        services_data = [
            models.Service(
                category_id=cat_web.id,
                title="Zamonaviy Korporativ Web sayt",
                description="Kompaniyangiz va biznesingiz uchun to'liq funksional, moslashuvchan va yuqori tezlikka ega zamonaviy veb-sayt yaratish.",
                image_url="https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=800&q=80",
                price=12500000, # $1,000
                delivery_days=7,
                included_items="Adaptiv dizayn, SEO baza, Admin boshqaruv paneli, Domen va Xosting integratsiyasi, SSL xavfsizlik",
                working_link=active_working_link
            ),
            models.Service(
                category_id=cat_mvp.id,
                title="Startaplar uchun MVP Qurish",
                description="Startapingizni tezda bozorga olib chiqish uchun eng kerakli funksiyalarga ega minimal ishchi mahsulot (MVP) ishlab chiqish.",
                image_url="https://images.unsplash.com/photo-1519389950473-47ba0277781c?auto=format&fit=crop&w=800&q=80",
                price=12500000, # $1,000
                delivery_days=14,
                included_items="Foydalanuvchi tizimi, Asosiy biznes logika, To'lov tizimlari, API arxitekturasi, Testlash",
                working_link=active_working_link
            ),
            models.Service(
                category_id=cat_mobile.id,
                title="Cross-Platform Mobil Ilova (iOS & Android)",
                description="Flutter va React Native asosida ikki operatsion tizimda ham silliq ishlaydigan professional mobil ilova yaratish.",
                image_url="https://images.unsplash.com/photo-1512941937669-90a1b58e7e9c?auto=format&fit=crop&w=800&q=80",
                price=20000000,
                delivery_days=20,
                included_items="iOS va Android versiyalar, Push-bildirishnomalar, Offline rejim, API ulash, App Store & Google Play nashri",
                working_link=active_working_link
            ),
            models.Service(
                category_id=cat_seo.id,
                title="SEO Optimizatsiya va Raqamli Marketing",
                description="Google qidiruv tizimida saytingizni Top-10 likka olib chiqish, texnik audit va konversiyani oshirish.",
                image_url="https://images.unsplash.com/photo-1460925895917-afdab827c52f?auto=format&fit=crop&w=800&q=80",
                price=6000000,
                delivery_days=10,
                included_items="Kalit so'zlar tahlili, On-page va Off-page SEO, Sayt tezligini oshirish, Google Analytics sozlash",
                working_link=active_working_link
            ),
            models.Service(
                category_id=cat_uiux.id,
                title="UI/UX Dizayn Tizimi va Figma Prototip",
                description="Foydalanuvchilar uchun qulay, jozibador va konversiyali interfeyslar, mobil va veb dizaynlar yaratish.",
                image_url="https://images.unsplash.com/photo-1581291518655-9523c932edcf?auto=format&fit=crop&w=800&q=80",
                price=7500000,
                delivery_days=5,
                included_items="Figma manba fayllari, Komponentlar kutubxonasi, Interaktiv klik prototip, Dizayn qo'llanma",
                working_link=active_working_link
            ),
            models.Service(
                category_id=cat_devops.id,
                title="CI/CD va Bulutli Infratuzilma (DevOps)",
                description="Serverlarni avtomatlashtirish, Docker konteynerlar, doimiy 24/7 ishlash kafolati va xavfsizlik monitoringi.",
                image_url="https://images.unsplash.com/photo-1607799279861-4dd421887fb3?auto=format&fit=crop&w=800&q=80",
                price=9000000,
                delivery_days=4,
                included_items="Docker & Kubernetes, GitHub Actions CI/CD, Nginx reverse proxy, Monitoring va Zaxira nusxalash",
                working_link=active_working_link
            )
        ]
        db.add_all(services_data)
        db.commit()

        print("Database successfully seeded with clean state, preserved Admin, and IT services!")

    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
