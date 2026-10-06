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

class UserRegisterOut(UserOut):
    access_token: Optional[str] = None
    token_type: Optional[str] = "bearer"

class Token(BaseModel):
    access_token: str
    token_type: str

class GoogleAuthIn(BaseModel):
    credential: Optional[str] = None
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    avatar_url: Optional[str] = None

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


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
    slug: Optional[str] = None
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
    slug: Optional[str] = None
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
    status: Optional[str] = "Tahrirlashda"
    note: Optional[str] = None

class OrderStatusHistoryOut(BaseModel):
    id: int
    old_status: Optional[str]
    new_status: str
    note: Optional[str] = None
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
    cancel_reason: Optional[str] = None
    created_at: datetime
    class Config: from_attributes = True

class OrderFileOut(BaseModel):
    id: int
    order_id: int
    uploader_id: int
    filename: str
    file_url: str
    file_size: Optional[str] = None
    created_at: datetime
    class Config: from_attributes = True

class ReviewCreate(BaseModel):
    rating: int # 1 - 5
    comment: str

class ReviewOut(BaseModel):
    id: int
    order_id: int
    user_id: int
    user_name: Optional[str] = None
    service_id: Optional[int] = None
    service_title: Optional[str] = None
    rating: int
    comment: str
    created_at: datetime
    class Config: from_attributes = True

class OrderDetailOut(OrderOut):
    status_history: List[OrderStatusHistoryOut] = []
    messages: List[MessageOut] = []
    files: List[OrderFileOut] = []
    review: Optional[ReviewOut] = None

# --- Notifications ---
class NotificationOut(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    link: Optional[str] = None
    is_read: bool
    created_at: datetime
    class Config: from_attributes = True

# --- Activity Log & Settings ---
class ActivityLogOut(BaseModel):
    id: int
    admin_id: Optional[int] = None
    admin_name: Optional[str] = None
    action: str
    entity: str
    entity_id: Optional[int] = None
    metadata_json: Optional[str] = None
    created_at: datetime
    class Config: from_attributes = True

class SettingOut(BaseModel):
    key: str
    value: str
    updated_at: datetime
    class Config: from_attributes = True

class SettingUpdate(BaseModel):
    key: str
    value: str

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

class UserDetailAdminOut(UserAdminOut):
    orders: List[OrderOut] = []

# --- Portfolio Projects ---
class PortfolioProjectBase(BaseModel):
    title: str
    slug: Optional[str] = None
    category_name: str
    short_desc: str
    full_desc: str
    image_url: str
    gallery_json: Optional[str] = "[]"
    client_name: str
    technologies: str
    results_summary: str
    live_url: Optional[str] = None
    is_featured: bool = True

class PortfolioProjectCreate(PortfolioProjectBase):
    pass

class PortfolioProjectUpdate(BaseModel):
    title: Optional[str] = None
    slug: Optional[str] = None
    category_name: Optional[str] = None
    short_desc: Optional[str] = None
    full_desc: Optional[str] = None
    image_url: Optional[str] = None
    gallery_json: Optional[str] = None
    client_name: Optional[str] = None
    technologies: Optional[str] = None
    results_summary: Optional[str] = None
    live_url: Optional[str] = None
    is_featured: Optional[bool] = None

class PortfolioProjectOut(PortfolioProjectBase):
    id: int
    created_at: datetime
    class Config: from_attributes = True

# --- Support Tickets ---
class SupportTicketCreate(BaseModel):
    subject: str
    message: str
    category: Optional[str] = "Umumiy"

class SupportTicketReply(BaseModel):
    admin_reply: str
    status: Optional[str] = "Hal qilindi"

class SupportTicketStatusUpdate(BaseModel):
    status: str

class SupportTicketOut(BaseModel):
    id: int
    ticket_number: str
    user_id: int
    user_name: Optional[str] = None
    user_email: Optional[str] = None
    subject: str
    message: str
    category: str
    status: str
    admin_reply: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    class Config: from_attributes = True

# --- Team Members ---
class TeamMemberBase(BaseModel):
    name: str
    role: str
    avatar_url: str
    bio: Optional[str] = None
    skills: Optional[str] = None
    display_order: int = 0

class TeamMemberCreate(TeamMemberBase):
    pass

class TeamMemberOut(TeamMemberBase):
    id: int
    class Config: from_attributes = True

# --- Banners ---
class BannerBase(BaseModel):
    title: str
    subtitle: Optional[str] = None
    image_url: Optional[str] = None
    link_url: Optional[str] = None
    is_active: bool = True

class BannerCreate(BannerBase):
    pass

class BannerOut(BannerBase):
    id: int
    created_at: datetime
    class Config: from_attributes = True

# --- Notifications Broadcast ---
class BroadcastNotificationIn(BaseModel):
    user_id: Optional[int] = None # None means all clients
    title: str
    message: str
    link: Optional[str] = None


