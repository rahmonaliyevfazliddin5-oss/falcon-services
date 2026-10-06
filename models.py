from datetime import datetime
from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, Text, DateTime, Date
from sqlalchemy.orm import relationship
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    google_id = Column(String, unique=True, index=True, nullable=True)
    name = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="client", nullable=False)
    phone = Column(String, nullable=True)
    avatar_url = Column(String, nullable=True, default="/static/default-avatar.png")
    reset_token = Column(String, nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    orders = relationship("Order", back_populates="user", foreign_keys="[Order.user_id]")
    status_changes = relationship("OrderStatusHistory", back_populates="changed_by")
    messages = relationship("Message", back_populates="sender")

class Category(Base):
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    services = relationship("Service", back_populates="category")

class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    slug = Column(String, unique=True, index=True, nullable=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    image_url = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
    delivery_days = Column(Integer, nullable=False)
    included_items = Column(Text, nullable=True)
    working_link = Column(String, nullable=True)
    is_archived = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    category = relationship("Category", back_populates="services")

class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_number = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    service_title_snapshot = Column(String, nullable=False)
    price_snapshot = Column(Integer, nullable=False)
    project_name = Column(String, nullable=False)
    technical_task = Column(Text, nullable=False)
    desired_deadline = Column(Date, nullable=False)
    contact_phone = Column(String, nullable=False)
    status = Column(String, default="Yangi", nullable=False)
    cancel_reason = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="orders", foreign_keys=[user_id])
    service = relationship("Service")
    status_history = relationship("OrderStatusHistory", back_populates="order")
    messages = relationship("Message", back_populates="order")
    files = relationship("OrderFile", back_populates="order", cascade="all, delete-orphan")
    review = relationship("Review", back_populates="order", uselist=False, cascade="all, delete-orphan")

class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    old_status = Column(String, nullable=True)
    new_status = Column(String, nullable=False)
    note = Column(Text, nullable=True)
    changed_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    changed_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="status_history")
    changed_by = relationship("User", back_populates="status_changes")

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="messages")
    sender = relationship("User", back_populates="messages")

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    link = Column(String, nullable=True)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User")

class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    entity = Column(String, nullable=False)
    entity_id = Column(Integer, nullable=True)
    metadata_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    admin = relationship("User")

class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    value = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow)

class PortfolioProject(Base):
    __tablename__ = "portfolio_projects"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    category_name = Column(String, nullable=False)
    short_desc = Column(String, nullable=False)
    full_desc = Column(Text, nullable=False)
    image_url = Column(String, nullable=False)
    gallery_json = Column(Text, nullable=True) # JSON array of image URLs
    client_name = Column(String, nullable=False)
    technologies = Column(String, nullable=False)
    results_summary = Column(Text, nullable=False)
    live_url = Column(String, nullable=True)
    is_featured = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class OrderFile(Base):
    __tablename__ = "order_files"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    file_url = Column(String, nullable=False)
    file_size = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="files")
    uploader = relationship("User")

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=True)
    rating = Column(Integer, nullable=False) # 1 - 5
    comment = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="review")
    user = relationship("User")
    service = relationship("Service")

class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String, unique=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String, nullable=False)
    message = Column(Text, nullable=False)
    category = Column(String, default="Umumiy", nullable=False)
    status = Column(String, default="Ochiq", nullable=False) # Ochiq, Jarayonda, Hal qilindi
    admin_reply = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User")

class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    avatar_url = Column(String, nullable=False)
    bio = Column(Text, nullable=True)
    skills = Column(String, nullable=True)
    display_order = Column(Integer, default=0)

class Banner(Base):
    __tablename__ = "banners"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    subtitle = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    link_url = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


