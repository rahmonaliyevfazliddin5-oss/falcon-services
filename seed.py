from sqlalchemy.orm import Session
from database import engine, SessionLocal
import models
from auth import get_password_hash
from datetime import datetime

def seed_db():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # 1. Tizim ishga tushganda eski oddiy foydalanuvchilar va buyurtmalarni tozalash (Talab 2)
        # Barcha buyurtmalar, status tarixi va xabarlar tozalanadi:
        db.query(models.OrderStatusHistory).delete()
        db.query(models.Message).delete()
        db.query(models.Order).delete()
        # Admin bo'lmagan barcha eski foydalanuvchilar tozalanadi:
        db.query(models.User).filter(models.User.email != "falcon@admin.com").delete()
        db.commit()

        # 2. Bitta asosiy Falcon Admin akkauntini o'zgarmasdan saqlash
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
            admin.role = "admin"
            admin.name = "Falcon Admin"
            admin.password_hash = get_password_hash("falconadmin777")
            if not admin.avatar_url:
                admin.avatar_url = "/static/default-avatar.png"
            if not admin.phone:
                admin.phone = "+998998967440"
        db.commit()

        # 2. IT Xizmatlari kategoriyalari bo'sh bo'lsa kiritish
        if db.query(models.Category).count() == 0:
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

        # 3. IT Xizmatlari bo'sh bo'lsa kiritish
        if db.query(models.Service).count() == 0:
            cat_web = db.query(models.Category).filter(models.Category.slug == "web-sayt-yaratish").first()
            cat_mvp = db.query(models.Category).filter(models.Category.slug == "mvp-qurish").first()
            cat_mobile = db.query(models.Category).filter(models.Category.slug == "mobil-ilovalar").first()
            cat_seo = db.query(models.Category).filter(models.Category.slug == "seo-va-marketing").first()
            cat_uiux = db.query(models.Category).filter(models.Category.slug == "ui-ux-dizayn").first()
            cat_devops = db.query(models.Category).filter(models.Category.slug == "devops-va-bulut").first()

            active_working_link = "https://www.eventmindai.uz/"

            services_data = [
                models.Service(
                    category_id=cat_web.id,
                    slug="zamonaviy-korporativ-web-sayt",
                    title="Zamonaviy Korporativ Web sayt",
                    description="Kompaniyangiz va biznesingiz uchun to'liq funksional, moslashuvchan va yuqori tezlikka ega zamonaviy veb-sayt yaratish.",
                    image_url="/static/services/web-dev.webp",
                    price=12500000, # $1,000
                    delivery_days=7,
                    included_items="Adaptiv dizayn, SEO baza, Admin boshqaruv paneli, Domen va Xosting integratsiyasi, SSL xavfsizlik",
                    working_link=active_working_link
                ),
                models.Service(
                    category_id=cat_mvp.id,
                    slug="startaplar-uchun-mvp-qurish",
                    title="Startaplar uchun MVP Qurish",
                    description="Startapingizni tezda bozorga olib chiqish uchun eng kerakli funksiyalarga ega minimal ishchi mahsulot (MVP) ishlab chiqish.",
                    image_url="/static/services/mvp.webp",
                    price=12500000, # $1,000
                    delivery_days=14,
                    included_items="Foydalanuvchi tizimi, Asosiy biznes logika, To'lov tizimlari, API arxitekturasi, Testlash",
                    working_link=active_working_link
                ),
                models.Service(
                    category_id=cat_mobile.id,
                    slug="cross-platform-mobil-ilova",
                    title="Cross-Platform Mobil Ilova (iOS & Android)",
                    description="Flutter va React Native asosida ikki operatsion tizimda ham silliq ishlaydigan professional mobil ilova yaratish.",
                    image_url="/static/services/mobile.webp",
                    price=20000000,
                    delivery_days=20,
                    included_items="iOS va Android versiyalar, Push-bildirishnomalar, Offline rejim, API ulash, App Store & Google Play nashri",
                    working_link=active_working_link
                ),
                models.Service(
                    category_id=cat_seo.id,
                    slug="seo-optimizatsiya-va-raqamli-marketing",
                    title="SEO Optimizatsiya va Raqamli Marketing",
                    description="Google qidiruv tizimida saytingizni Top-10 likka olib chiqish, texnik audit va konversiyani oshirish.",
                    image_url="/static/services/seo.webp",
                    price=6000000,
                    delivery_days=10,
                    included_items="Kalit so'zlar tahlili, On-page va Off-page SEO, Sayt tezligini oshirish, Google Analytics sozlash",
                    working_link=active_working_link
                ),
                models.Service(
                    category_id=cat_uiux.id,
                    slug="ui-ux-dizayn-tizimi-va-figma-prototip",
                    title="UI/UX Dizayn Tizimi va Figma Prototip",
                    description="Foydalanuvchilar uchun qulay, jozibador va konversiyali interfeyslar, mobil va veb dizaynlar yaratish.",
                    image_url="/static/services/uiux.webp",
                    price=7500000,
                    delivery_days=5,
                    included_items="Figma manba fayllari, Komponentlar kutubxonasi, Interaktiv klik prototip, Dizayn qo'llanma",
                    working_link=active_working_link
                ),
                models.Service(
                    category_id=cat_devops.id,
                    slug="ci-cd-va-bulutli-infratuzilma",
                    title="CI/CD va Bulutli Infratuzilma (DevOps)",
                    description="Serverlarni avtomatlashtirish, Docker konteynerlar, doimiy 24/7 ishlash kafolati va xavfsizlik monitoringi.",
                    image_url="/static/services/devops.webp",
                    price=9000000,
                    delivery_days=4,
                    included_items="Docker & Kubernetes, GitHub Actions CI/CD, Nginx reverse proxy, Monitoring va Zaxira nusxalash",
                    working_link=active_working_link
                )
            ]
            db.add_all(services_data)
            db.commit()

        # Mavjud xizmatlarning slugi bo'sh bo'lsa yangilash
        services = db.query(models.Service).all()
        slug_map = {
            "Zamonaviy Korporativ Web sayt": "zamonaviy-korporativ-web-sayt",
            "Startaplar uchun MVP Qurish": "startaplar-uchun-mvp-qurish",
            "Cross-Platform Mobil Ilova (iOS & Android)": "cross-platform-mobil-ilova",
            "SEO Optimizatsiya va Raqamli Marketing": "seo-optimizatsiya-va-raqamli-marketing",
            "UI/UX Dizayn Tizimi va Figma Prototip": "ui-ux-dizayn-tizimi-va-figma-prototip",
            "CI/CD va Bulutli Infratuzilma (DevOps)": "ci-cd-va-bulutli-infratuzilma"
        }
        for s in services:
            if not s.slug:
                s.slug = slug_map.get(s.title, f"xizmat-{s.id}")
        db.commit()

        # 4. Standart sozlamalar (Settings)
        default_settings = {
            "site_name": "Falcon Services",
            "contact_phone": "+998 99 896 74 40",
            "contact_email": "info@falcon.uz",
            "social_telegram": "https://t.me/falcon_services",
            "system_status": "Barcha xizmatlar barqaror ishlamoqda"
        }
        for k, v in default_settings.items():
            st = db.query(models.Setting).filter(models.Setting.key == k).first()
            if not st:
                db.add(models.Setting(key=k, value=v))
        db.commit()

        # 5. Bildirishnomalar (Notifications) tekshiruvi
        if admin:
            notif_count = db.query(models.Notification).filter(models.Notification.user_id == admin.id).count()
            if notif_count == 0:
                db.add(models.Notification(
                    user_id=admin.id,
                    title="Xush kelibsiz!",
                    message="Falcon Services boshqaruv paneliga xush kelibsiz. Barcha buyurtmalar va statistikalar shu yerda ko'rinadi.",
                    link="/admin",
                    is_read=False
                ))
                db.commit()

        print("Database initialized: Admin verified, service slugs, settings and notifications ready.")

    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
