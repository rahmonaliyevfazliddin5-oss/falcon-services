from pydantic import BaseModel, EmailStr
from typing import Optional, List, Any
from datetime import datetime, date

# --- Auth & User ---
class UserBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    avatar_url: Optional[str] = "/static/default-avatar.png"

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None

class UserOut(UserBase):
    id: int
    role: str
    created_at: datetime
    class Config: from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str

# --- Categories ---
class CategoryBase(BaseModel):
    name: str
    slug: str

class CategoryOut(CategoryBase):
    id: int
    created_at: datetime
    class Config: from_attributes = True

# --- Services ---
class ServiceBase(BaseModel):
    category_id: int
    title: str
    description: str
    image_url: str
    price: int
    delivery_days: int
    included_items: Optional[str] = None
    working_link: Optional[str] = None
    is_archived: bool = False

class ServiceCreate(ServiceBase):
    pass

class ServiceUpdate(BaseModel):
    category_id: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    price: Optional[int] = None
    delivery_days: Optional[int] = None
    included_items: Optional[str] = None
    working_link: Optional[str] = None

class ServiceOut(ServiceBase):
    id: int
    created_at: datetime
    class Config: from_attributes = True

class ServiceDetailOut(ServiceOut):
    related_services: List[ServiceOut] = []

class PaginatedServices(BaseModel):
    items: List[ServiceOut]
    total: int
    page: int
    pages: int

# --- Orders ---
class OrderCreate(BaseModel):
    service_id: int
    project_name: str
    technical_task: str
    desired_deadline: date
    contact_phone: str

class OrderStatusUpdate(BaseModel):
    status: str

class OrderStatusHistoryOut(BaseModel):
    id: int
    old_status: Optional[str]
    new_status: str
    changed_by_user_id: int
    changed_at: datetime
    class Config: from_attributes = True

class MessageCreate(BaseModel):
    text: str

class MessageOut(BaseModel):
    id: int
    sender_id: int
    text: str
    created_at: datetime
    class Config: from_attributes = True

class OrderOut(BaseModel):
    id: int
    order_number: str
    user_id: int
    service_id: int
    service_title_snapshot: str
    price_snapshot: int
    project_name: str
    technical_task: str
    desired_deadline: date
    contact_phone: str
    status: str
    created_at: datetime
    class Config: from_attributes = True

class OrderDetailOut(OrderOut):
    status_history: List[OrderStatusHistoryOut] = []
    messages: List[MessageOut] = []

# --- Admin ---
class DashboardStats(BaseModel):
    total_orders: int
    new_orders_count: int
    in_progress_orders_count: int
    completed_orders_sum: int
    completed_orders_count: int = 0
    cancelled_orders_count: int = 0
    total_revenue_potential: int = 0
    total_users_count: int = 0
    total_services_count: int = 0
    average_order_value: int = 0
    status_distribution: dict
    top_services: List[dict]
    recent_activity: List[dict] = []

class OrderAdminOut(OrderOut):
    user_name: str
    user_email: str

class UserAdminOut(UserOut):
    orders_count: int

