from sqlalchemy.orm import Session
from database import engine, SessionLocal
import models
from auth import get_password_hash
from datetime import datetime, timedelta

def seed_db():
    models.Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # Check if users already exist
        admin = db.query(models.User).filter(models.User.email == "admin@falcon.uz").first()
        if not admin:
            users_data = [
                models.User(name="Admin", email="admin@falcon.uz", password_hash=get_password_hash("admin123"), role="admin"),
                models.User(name="Mijoz 1", email="mijoz1@falcon.uz", password_hash=get_password_hash("mijoz123"), role="client"),
                models.User(name="Mijoz 2", email="mijoz2@falcon.uz", password_hash=get_password_hash("mijoz123"), role="client")
            ]
            db.add_all(users_data)
            db.commit()

        # Categories
        cat_count = db.query(models.Category).count()
        if cat_count == 0:
            categories = [
                models.Category(name="Veb dasturlash", slug="veb-dasturlash"),
                models.Category(name="Grafik dizayn", slug="grafik-dizayn"),
                models.Category(name="Video montaj", slug="video-montaj"),
                models.Category(name="SMM va Marketing", slug="smm-va-marketing")
            ]
            db.add_all(categories)
            db.commit()

            # Services
            cat_web = db.query(models.Category).filter(models.Category.name == "Veb dasturlash").first()
            cat_design = db.query(models.Category).filter(models.Category.name == "Grafik dizayn").first()
            cat_video = db.query(models.Category).filter(models.Category.name == "Video montaj").first()
            cat_smm = db.query(models.Category).filter(models.Category.name == "SMM va Marketing").first()

            services = [
                models.Service(category_id=cat_web.id, title="Landing Page Yaratish", description="Zamonaviy va konversiyali landing page.", image_url="https://images.unsplash.com/photo-1517694712202-14dd9538aa97", price=1500000, delivery_days=5, included_items="Dizayn, Frontend, Backend ulash, Domen va Xosting setup"),
                models.Service(category_id=cat_web.id, title="Korporativ Veb-sayt", description="Kompaniya uchun to'liq funksional sayt.", image_url="https://images.unsplash.com/photo-1498050108023-c5249f4df085", price=3000000, delivery_days=10, included_items="Ko'p sahifali dizayn, Admin panel, SEO optimizatsiya"),
                models.Service(category_id=cat_web.id, title="E-commerce Do'kon", description="Onlayn savdo uchun internet do'kon.", image_url="https://images.unsplash.com/photo-1556742049-0cfed4f6a45d", price=5000000, delivery_days=14, included_items="Katalog, Savat, To'lov tizimlari, Admin panel"),
                
                models.Service(category_id=cat_design.id, title="Logotip Dizayni", description="Kompaniyangiz uchun unikal logotip.", image_url="https://images.unsplash.com/photo-1626785774573-4b799315345d", price=500000, delivery_days=3, included_items="3 xil variant, Vektor formatlar, Brandbook (qisqacha)"),
                models.Service(category_id=cat_design.id, title="Ijtimoiy Tarmoq Postlari", description="Instagram va Telegram uchun postlar dizayni.", image_url="https://images.unsplash.com/photo-1611162617213-7d7a39e9b1d7", price=800000, delivery_days=5, included_items="10 ta post dizayni, 5 ta story dizayni"),
                models.Service(category_id=cat_design.id, title="Qadoq Dizayni", description="Mahsulot uchun jozibador qadoq dizayni.", image_url="https://images.unsplash.com/photo-1589939705384-5185137a7f0f", price=1200000, delivery_days=7, included_items="3D render, Printga tayyor fayllar"),

                models.Service(category_id=cat_video.id, title="Reels/TikTok Montaj", description="Trenddagi qisqa videolar montaji.", image_url="https://images.unsplash.com/photo-1574717024653-61fd2cf4d44d", price=300000, delivery_days=3, included_items="Ovoz ustida ishlash, Subtitr, Effektlar, 3 ta video"),
                models.Service(category_id=cat_video.id, title="YouTube Vlog Montaj", description="Uzun formatli YouTube videolari.", image_url="https://images.unsplash.com/photo-1536240478700-b869070f9279", price=800000, delivery_days=5, included_items="Rang korreksiyasi, Musiqa tanlash, O'tishlar, 1 ta video (15-20 min)"),
                models.Service(category_id=cat_video.id, title="Reklama Roligi", description="Mahsulot yoki xizmat uchun professional reklama.", image_url="https://images.unsplash.com/photo-1535016120720-40c74676578c", price=2000000, delivery_days=7, included_items="Ssenariy, Ovoz yozish, Infografika, 1 ta rolik (1 min)"),

                models.Service(category_id=cat_smm.id, title="SMM Start", description="Kichik bizneslar uchun SMM yuritish.", image_url="https://images.unsplash.com/photo-1611926653458-09294b3142bf", price=1500000, delivery_days=30, included_items="15 ta post, 15 ta story, Reels g'oyalar, Kopirayting"),
                models.Service(category_id=cat_smm.id, title="Targeting Sozlash", description="Facebook va Instagram reklamalari.", image_url="https://images.unsplash.com/photo-1533750516457-a7f992034fec", price=1000000, delivery_days=7, included_items="Auditoriya tahlili, Kreativlar, Pixel o'rnatish, 1 oylik nazorat"),
                models.Service(category_id=cat_smm.id, title="Kompleks Marketing", description="To'liq SMM va Marketing strategiyasi.", image_url="https://images.unsplash.com/photo-1460925895917-afdab827c52f", price=4000000, delivery_days=30, included_items="Brending, SMM, Target, Influencer marketing, Oy yakuni hisoboti"),
            ]
            db.add_all(services)
            db.commit()

            # Test Orders
            user = db.query(models.User).filter(models.User.email == "mijoz1@falcon.uz").first()
            admin = db.query(models.User).filter(models.User.email == "admin@falcon.uz").first()
            service = db.query(models.Service).first()

            if user and admin and service:
                order1 = models.Order(
                    order_number="ORD-10001",
                    user_id=user.id,
                    service_id=service.id,
                    service_title_snapshot=service.title,
                    price_snapshot=service.price,
                    project_name="Mening yangi proyektim",
                    technical_task="Juda zo'r, ko'k rangli, tez ishlaydigan landing page kerak. Quyidagi talablar: 1. Tezkor yuklanish 2. Mobil moslashuv",
                    desired_deadline=datetime.utcnow().date() + timedelta(days=10),
                    contact_phone="+998901234567",
                    status="Yangi"
                )
                db.add(order1)
                db.commit()

                hist1 = models.OrderStatusHistory(
                    order_id=order1.id,
                    old_status=None,
                    new_status="Yangi",
                    changed_by_user_id=user.id
                )
                db.add(hist1)
                
                msg1 = models.Message(
                    order_id=order1.id,
                    sender_id=user.id,
                    text="Assalomu alaykum, buyurtma qoldirdim!"
                )
                db.add(msg1)
                db.commit()

                # Order 2
                order2 = models.Order(
                    order_number="ORD-10002",
                    user_id=user.id,
                    service_id=service.id,
                    service_title_snapshot=service.title,
                    price_snapshot=service.price,
                    project_name="Yana bir proyekt",
                    technical_task="Bu gal boshqacha dizayn qiling, qizil va oq ranglarda, animatsiyali bo'lsin. Juda muhim proyekt.",
                    desired_deadline=datetime.utcnow().date() + timedelta(days=15),
                    contact_phone="+998901234567",
                    status="Jarayonda"
                )
                db.add(order2)
                db.commit()

                hist2 = models.OrderStatusHistory(
                    order_id=order2.id,
                    old_status="Yangi",
                    new_status="Jarayonda",
                    changed_by_user_id=admin.id
                )
                db.add(hist2)
                
                msg2 = models.Message(
                    order_id=order2.id,
                    sender_id=admin.id,
                    text="Buyurtmangiz qabul qilindi, ishni boshladik."
                )
                db.add(msg2)
                db.commit()

    finally:
        db.close()

if __name__ == "__main__":
    seed_db()
