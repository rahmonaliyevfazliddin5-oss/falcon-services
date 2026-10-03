// Falcon Services - Multi-language (i18n) Engine (UZ, RU, EN)

const translations = {
    uz: {
        // Navigation & Brand
        "nav.brand": "Falcon Services",
        "nav.home": "Bosh sahifa",
        "nav.services": "Xizmatlar katalogi",
        "nav.login": "Kirish",
        "nav.register": "Ro'yxatdan o'tish",
        "nav.admin": "Admin Panel",
        "nav.profile": "Mening kabinetim",
        "nav.logout": "Chiqish",
        "nav.contact": "Aloqa",
        
        // Theme & Lang
        "theme.dark": "Qora / Tungi rejim",
        "theme.light": "Yorug' rejim",
        "lang.label": "Til (Language)",
        
        // Home Page (Hero & Process)
        "hero.badge": "Professional IT Xizmatlar Platformasi",
        "hero.title": "Raqamli biznesingizni biz bilan o'stiring",
        "hero.subtitle": "Veb-saytlar, MVP dasturlash, mobil ilovalar va SEO xizmatlarini bir joydan tez va sifatli buyurtma qiling.",
        "hero.btn_catalog": "Xizmatlarga buyurtma berish",
        "hero.btn_explore": "Katalogni ko'rish",
        "hero.process_title": "Ishlash jarayoni",
        "hero.step1_title": "Xizmatni tanlash",
        "hero.step1_desc": "Katalogdan o'zingizga kerakli IT xizmatini tanlang",
        "hero.step2_title": "Texnik topshiriq",
        "hero.step2_desc": "Loyihangiz va talablaringiz haqida ma'lumot yuboring",
        "hero.step3_title": "Jarayonni kuzatish",
        "hero.step3_desc": "Shaxsiy kabinet orqali ish holatini kuzatib boring",
        "hero.step4_title": "Natijani qabul qilish",
        "hero.step4_desc": "Tayyor bo'lgan yuqori sifatli natijani qabul qilib oling",
        "hero.recommended_title": "Tavsiya etilgan IT xizmatlar",
        "hero.stat_services": "Faol IT xizmatlar",
        "hero.stat_clients": "Ro'yxatdan o'tgan mijozlar",
        "hero.stat_orders": "Qabul qilingan loyihalar",
        "hero.stat_guarantee": "Sifat kafolati",
        
        // Services Catalog & Filters
        "services.title": "Xizmatlar katalogi",
        "services.filter_title": "Filtrlash",
        "services.search_label": "Qidiruv",
        "services.search_placeholder": "Xizmat nomi bo'yicha qidirish...",
        "services.category_label": "Kategoriya",
        "services.all_categories": "Barcha kategoriyalar",
        "services.min_price": "Min narx",
        "services.max_price": "Max narx",
        "services.sort_label": "Saralash",
        "services.sort_newest": "Yangi qo'shilganlar",
        "services.sort_price_asc": "Arzonidan qimmatiga",
        "services.sort_price_desc": "Qimmatidan arzoniga",
        "services.btn_search": "Izlash",
        "services.btn_clear": "Tozalash",
        "services.price": "Narxi",
        "services.delivery": "Bajarish muddati",
        "services.days": "kun",
        "services.empty_title": "Ma'lumot topilmadi",
        "services.empty_desc": "Kiritilgan filtrlar bo'yicha hech qanday xizmat topilmadi.",
        "services.working_link": "Faol Ishchi Havola ↗",
        "services.working_link_badge": "Faol Ishchi Havola / Demo",
        "services.working_link_desc": "Ushbu xizmatning amaldagi faol loyiha havolasi",
        "services.open_link": "Havolani ochish ↗",
        "services.details": "Batafsil ko'rish",
        "services.order_btn": "Buyurtma berish",
        "services.includes_title": "Tarkibiga kiruvchi ishlar",
        "services.related_title": "Tegishli boshqa xizmatlar",
        
        // Order Form
        "order.title": "Buyurtma berish",
        "order.project_name": "Loyiha nomi",
        "order.project_placeholder": "Masalan: Onlayn do'kon veb-sayti",
        "order.tt_label": "Texnik topshiriq",
        "order.tt_placeholder": "Loyiha vazifalari va talablari haqida batafsil yozing (kamida 50 belgi)...",
        "order.deadline_label": "Istalgan yakunlash sanasi",
        "order.phone_label": "Aloqa telefoni",
        "order.submit": "Buyurtmani tasdiqlash",
        
        // Auth (Login & Register)
        "login.title": "Tizimga kiring",
        "login.email": "Elektron pochta",
        "login.password": "Parol",
        "login.submit": "Kirish",
        "login.no_account": "Akkauntingiz yo'qmi?",
        "login.register_link": "Ro'yxatdan o'tish",
        
        "register.title": "Ro'yxatdan o'tish",
        "register.name": "Ism (Unikal)",
        "register.name_placeholder": "Haqiqiy ismingizni kiriting",
        "register.email": "Elektron pochta",
        "register.phone": "Telefon raqami",
        "register.password": "Parol",
        "register.submit": "Ro'yxatdan o'tish",
        "register.have_account": "Akkauntingiz bormi?",
        "register.login_link": "Tizimga kirish",
        "register.profanity_warn": "Ism odobli va haqoratsiz bo'lishi shart",
        
        // Profile
        "profile.title": "Foydalanuvchi Profili",
        "profile.avatar_title": "Profil Rasmi (Dumaloq format)",
        "profile.avatar_upload": "Yangi rasm yuklash",
        "profile.name": "To'liq ism (Unikal)",
        "profile.email": "Elektron pochta",
        "profile.phone": "Telefon",
        "profile.save": "O'zgarishlarni saqlash",
        "profile.settings": "Sozlamalar",
        "profile.orders": "Mening buyurtmalarim",
        "profile.no_orders": "Sizda hali buyurtmalar mavjud emas.",
        "profile.order_details": "Buyurtma tafsilotlari",
        
        // Admin Panel
        "admin.title": "Falcon Admin Panel",
        "admin.tab_dash": "Dashboard",
        "admin.tab_orders": "Buyurtmalar",
        "admin.tab_services": "Xizmatlar",
        "admin.tab_users": "Foydalanuvchilar",
        "admin.stat_total": "Jami buyurtmalar",
        "admin.stat_new": "Yangi buyurtmalar",
        "admin.stat_progress": "Jarayondagi buyurtmalar",
        "admin.stat_sum": "Umumiy qiymat (Yakunlangan)",
        "admin.chart_title": "Holatlar bo'yicha ulush",
        "admin.top_services": "Top-5 Xizmatlar",
        "admin.new_service": "+ Yangi xizmat qo'shish",
        "admin.working_link_label": "Faol havola (Working Link URL)",
        "admin.edit_price": "Narxni tahrirlash",
        "admin.export_csv": "CSV formatda yuklab olish",
        "admin.filter_btn": "Filtrlash",
        "admin.start_date": "Boshlanish sanasi",
        "admin.end_date": "Tugash sanasi",
        
        // Table Headers
        "th.id": "ID",
        "th.service": "Xizmat",
        "th.client": "Mijoz (Ism, Email)",
        "th.project": "Loyiha Nomi",
        "th.price": "Narx (UZS)",
        "th.status": "Holat",
        "th.date": "Sana",
        "th.action": "Amal",
        "th.category": "Kategoriya",
        "th.delivery": "Muddati",
        "th.working_link": "Ishchi Havola",
        
        // Footer
        "footer.rights": "Barcha huquqlar himoyalangan.",
        "footer.contact": "Aloqa:",
        "footer.address": "Toshkent, O'zbekiston"
    },
    
    ru: {
        // Navigation & Brand
        "nav.brand": "Falcon Services",
        "nav.home": "Главная",
        "nav.services": "Каталог услуг",
        "nav.login": "Войти",
        "nav.register": "Регистрация",
        "nav.admin": "Админ-панель",
        "nav.profile": "Мой кабинет",
        "nav.logout": "Выйти",
        "nav.contact": "Связь",
        
        // Theme & Lang
        "theme.dark": "Темная тема",
        "theme.light": "Светлая тема",
        "lang.label": "Язык (Language)",
        
        // Home Page (Hero & Process)
        "hero.badge": "Профессиональная платформа IT-услуг",
        "hero.title": "Развивайте свой цифровой бизнес вместе с нами",
        "hero.subtitle": "Заказывайте разработку сайтов, MVP, мобильных приложений и SEO быстро и качественно в одном месте.",
        "hero.btn_catalog": "Заказать IT-услуги",
        "hero.btn_explore": "Смотреть каталог",
        "hero.process_title": "Процесс работы",
        "hero.step1_title": "Выбор услуги",
        "hero.step1_desc": "Выберите подходящую IT-услугу из каталога",
        "hero.step2_title": "Техническое задание",
        "hero.step2_desc": "Опишите требования и задачи вашего проекта",
        "hero.step3_title": "Контроль процесса",
        "hero.step3_desc": "Отслеживайте статус проекта в личном кабинете",
        "hero.step4_title": "Получение результата",
        "hero.step4_desc": "Примите готовый качественный IT-продукт",
        "hero.recommended_title": "Рекомендуемые IT-услуги",
        "hero.stat_services": "Активные IT-услуги",
        "hero.stat_clients": "Зарегистрированные клиенты",
        "hero.stat_orders": "Принятые проекты",
        "hero.stat_guarantee": "Гарантия качества",
        
        // Services Catalog & Filters
        "services.title": "Каталог IT-услуг",
        "services.filter_title": "Фильтры",
        "services.search_label": "Поиск",
        "services.search_placeholder": "Поиск по названию услуги...",
        "services.category_label": "Категория",
        "services.all_categories": "Все категории",
        "services.min_price": "Мин. цена",
        "services.max_price": "Макс. цена",
        "services.sort_label": "Сортировка",
        "services.sort_newest": "Сначала новые",
        "services.sort_price_asc": "От дешевых к дорогим",
        "services.sort_price_desc": "От дорогих к дешевым",
        "services.btn_search": "Искать",
        "services.btn_clear": "Очистить",
        "services.price": "Цена",
        "services.delivery": "Срок выполнения",
        "services.days": "дней",
        "services.empty_title": "Ничего не найдено",
        "services.empty_desc": "По заданным фильтрам услуг не найдено.",
        "services.working_link": "Рабочая ссылка ↗",
        "services.working_link_badge": "Рабочая ссылка / Демо",
        "services.working_link_desc": "Действующая ссылка на проект данной услуги",
        "services.open_link": "Открыть ссылку ↗",
        "services.details": "Подробнее",
        "services.order_btn": "Заказать услугу",
        "services.includes_title": "Что входит в услугу",
        "services.related_title": "Другие похожие услуги",
        
        // Order Form
        "order.title": "Оформление заказа",
        "order.project_name": "Название проекта",
        "order.project_placeholder": "Например: Веб-сайт интернет-магазина",
        "order.tt_label": "Техническое задание",
        "order.tt_placeholder": "Подробно опишите требования к проекту (минимум 50 символов)...",
        "order.deadline_label": "Желаемый срок завершения",
        "order.phone_label": "Контактный телефон",
        "order.submit": "Подтвердить заказ",
        
        // Auth (Login & Register)
        "login.title": "Вход в систему",
        "login.email": "Электронная почта",
        "login.password": "Пароль",
        "login.submit": "Войти",
        "login.no_account": "Нет аккаунта?",
        "login.register_link": "Регистрация",
        
        "register.title": "Регистрация",
        "register.name": "Имя (Уникальное)",
        "register.name_placeholder": "Введите ваше настоящее имя",
        "register.email": "Электронная почта",
        "register.phone": "Номер телефона",
        "register.password": "Пароль",
        "register.submit": "Зарегистрироваться",
        "register.have_account": "Уже есть аккаунт?",
        "register.login_link": "Войти",
        "register.profanity_warn": "Имя не должно содержать оскорбительных слов",
        
        // Profile
        "profile.title": "Профиль пользователя",
        "profile.avatar_title": "Фото профиля (Круглый формат)",
        "profile.avatar_upload": "Загрузить новое фото",
        "profile.name": "Полное имя (Уникальное)",
        "profile.email": "Электронная почта",
        "profile.phone": "Телефон",
        "profile.save": "Сохранить изменения",
        "profile.settings": "Настройки",
        "profile.orders": "Мои заказы",
        "profile.no_orders": "У вас пока нет активных заказов.",
        "profile.order_details": "Детали заказа",
        
        // Admin Panel
        "admin.title": "Falcon Админ-панель",
        "admin.tab_dash": "Дашборд",
        "admin.tab_orders": "Заказы",
        "admin.tab_services": "Услуги",
        "admin.tab_users": "Пользователи",
        "admin.stat_total": "Всего заказов",
        "admin.stat_new": "Новые заказы",
        "admin.stat_progress": "Заказы в работе",
        "admin.stat_sum": "Общий объем (Завершенные)",
        "admin.chart_title": "Доля по статусам",
        "admin.top_services": "Топ-5 Услуг",
        "admin.new_service": "+ Добавить услугу",
        "admin.working_link_label": "Рабочая ссылка (Working Link URL)",
        "admin.edit_price": "Редактировать цену",
        "admin.export_csv": "Скачать в формате CSV",
        "admin.filter_btn": "Фильтровать",
        "admin.start_date": "Дата начала",
        "admin.end_date": "Дата окончания",
        
        // Table Headers
        "th.id": "ID",
        "th.service": "Услуга",
        "th.client": "Клиент (Имя, Email)",
        "th.project": "Название проекта",
        "th.price": "Цена (UZS)",
        "th.status": "Статус",
        "th.date": "Дата",
        "th.action": "Действие",
        "th.category": "Категория",
        "th.delivery": "Срок",
        "th.working_link": "Рабочая ссылка",
        
        // Footer
        "footer.rights": "Все права защищены.",
        "footer.contact": "Контакты:",
        "footer.address": "Ташкент, Узбекистан"
    },
    
    en: {
        // Navigation & Brand
        "nav.brand": "Falcon Services",
        "nav.home": "Home",
        "nav.services": "Services Catalog",
        "nav.login": "Sign In",
        "nav.register": "Register",
        "nav.admin": "Admin Panel",
        "nav.profile": "My Profile",
        "nav.logout": "Logout",
        "nav.contact": "Contact",
        
        // Theme & Lang
        "theme.dark": "Dark Mode",
        "theme.light": "Light Mode",
        "lang.label": "Language",
        
        // Home Page (Hero & Process)
        "hero.badge": "Professional IT Services Platform",
        "hero.title": "Scale Your Digital Business With Us",
        "hero.subtitle": "Order professional web development, MVP creation, mobile apps, and SEO quickly and reliably in one place.",
        "hero.btn_catalog": "Order IT Services",
        "hero.btn_explore": "Explore Catalog",
        "hero.process_title": "How It Works",
        "hero.step1_title": "Choose Service",
        "hero.step1_desc": "Select the IT service you need from our catalog",
        "hero.step2_title": "Submit Brief",
        "hero.step2_desc": "Provide requirements and scope for your project",
        "hero.step3_title": "Track Progress",
        "hero.step3_desc": "Monitor project progress in your personal cabinet",
        "hero.step4_title": "Receive Results",
        "hero.step4_desc": "Get top-tier completed digital results on time",
        "hero.recommended_title": "Recommended IT Services",
        "hero.stat_services": "Active IT Services",
        "hero.stat_clients": "Registered Clients",
        "hero.stat_orders": "Received Projects",
        "hero.stat_guarantee": "Quality Guarantee",
        
        // Services Catalog & Filters
        "services.title": "IT Services Catalog",
        "services.filter_title": "Filter Services",
        "services.search_label": "Search",
        "services.search_placeholder": "Search services by title...",
        "services.category_label": "Category",
        "services.all_categories": "All Categories",
        "services.min_price": "Min Price",
        "services.max_price": "Max Price",
        "services.sort_label": "Sort By",
        "services.sort_newest": "Newest First",
        "services.sort_price_asc": "Price: Low to High",
        "services.sort_price_desc": "Price: High to Low",
        "services.btn_search": "Search",
        "services.btn_clear": "Clear",
        "services.price": "Price",
        "services.delivery": "Delivery Time",
        "services.days": "days",
        "services.empty_title": "No Results Found",
        "services.empty_desc": "No services match your selected filters.",
        "services.working_link": "Working Link ↗",
        "services.working_link_badge": "Working Link / Live Demo",
        "services.working_link_desc": "Active verified project link for this service",
        "services.open_link": "Open Link ↗",
        "services.details": "View Details",
        "services.order_btn": "Order Service",
        "services.includes_title": "What's Included",
        "services.related_title": "Related Services",
        
        // Order Form
        "order.title": "Place an Order",
        "order.project_name": "Project Name",
        "order.project_placeholder": "E.g., Online E-commerce Store",
        "order.tt_label": "Technical Specifications",
        "order.tt_placeholder": "Describe your project requirements and scope (at least 50 chars)...",
        "order.deadline_label": "Desired Deadline",
        "order.phone_label": "Contact Phone",
        "order.submit": "Submit Order",
        
        // Auth (Login & Register)
        "login.title": "Sign In",
        "login.email": "Email Address",
        "login.password": "Password",
        "login.submit": "Sign In",
        "login.no_account": "Don't have an account?",
        "login.register_link": "Register",
        
        "register.title": "Create Account",
        "register.name": "Name (Unique)",
        "register.name_placeholder": "Enter your real name",
        "register.email": "Email Address",
        "register.phone": "Phone Number",
        "register.password": "Password",
        "register.submit": "Register",
        "register.have_account": "Already have an account?",
        "register.login_link": "Sign In",
        "register.profanity_warn": "Name must be polite and appropriate",
        
        // Profile
        "profile.title": "User Profile",
        "profile.avatar_title": "Profile Photo (Circular)",
        "profile.avatar_upload": "Upload New Photo",
        "profile.name": "Full Name (Unique)",
        "profile.email": "Email Address",
        "profile.phone": "Phone",
        "profile.save": "Save Changes",
        "profile.settings": "Settings",
        "profile.orders": "My Orders",
        "profile.no_orders": "You do not have any orders yet.",
        "profile.order_details": "Order Details",
        
        // Admin Panel
        "admin.title": "Falcon Admin Panel",
        "admin.tab_dash": "Dashboard",
        "admin.tab_orders": "Orders",
        "admin.tab_services": "Services",
        "admin.tab_users": "Users",
        "admin.stat_total": "Total Orders",
        "admin.stat_new": "New Orders",
        "admin.stat_progress": "Orders in Progress",
        "admin.stat_sum": "Total Revenue (Completed)",
        "admin.chart_title": "Status Breakdown",
        "admin.top_services": "Top-5 Services",
        "admin.new_service": "+ Add New Service",
        "admin.working_link_label": "Working Link (Project URL)",
        "admin.edit_price": "Edit Price",
        "admin.export_csv": "Download as CSV",
        "admin.filter_btn": "Filter",
        "admin.start_date": "Start Date",
        "admin.end_date": "End Date",
        
        // Table Headers
        "th.id": "ID",
        "th.service": "Service",
        "th.client": "Client (Name, Email)",
        "th.project": "Project Name",
        "th.price": "Price (UZS)",
        "th.status": "Status",
        "th.date": "Date",
        "th.action": "Action",
        "th.category": "Category",
        "th.delivery": "Delivery",
        "th.working_link": "Working Link",
        
        // Footer
        "footer.rights": "All rights reserved.",
        "footer.contact": "Contact:",
        "footer.address": "Tashkent, Uzbekistan"
    }
};

// Dynamic Categories Translations
const categoryTranslations = {
    ru: {
        "Web sayt yaratish": "Создание веб-сайтов",
        "MVP qurish": "Разработка MVP",
        "Mobil ilovalar": "Мобильные приложения",
        "SEO va Marketing": "SEO и Маркетинг",
        "UI/UX Dizayn": "UI/UX Дизайн",
        "DevOps va Bulut": "DevOps и Cloud"
    },
    en: {
        "Web sayt yaratish": "Website Development",
        "MVP qurish": "MVP Development",
        "Mobil ilovalar": "Mobile Applications",
        "SEO va Marketing": "SEO & Marketing",
        "UI/UX Dizayn": "UI/UX Design",
        "DevOps va Bulut": "DevOps & Cloud"
    }
};

// Dynamic IT Services Translations (Titles, Descriptions, Included Items)
const serviceTranslations = {
    ru: {
        "Zamonaviy Korporativ Web sayt": {
            title: "Современный корпоративный веб-сайт",
            description: "Разработка полнофункционального, адаптивного и высокоскоростного современного веб-сайта для вашей компании и бизнеса.",
            included_items: "Адаптивный дизайн, Базовое SEO, Панель управления (Admin), Интеграция домена и хостинга, SSL безопасность"
        },
        "Startaplar uchun MVP Qurish": {
            title: "Разработка MVP для стартапов",
            description: "Разработка минимально жизнеспособного продукта (MVP) с ключевым функционалом для быстрого запуска вашего стартапа на рынок.",
            included_items: "Система пользователей, Основная бизнес-логика, Платежные системы, Архитектура API, Тестирование"
        },
        "Cross-Platform Mobil Ilova (iOS & Android)": {
            title: "Кроссплатформенное мобильное приложение (iOS & Android)",
            description: "Создание профессионального мобильного приложения на Flutter и React Native, плавно работающего на обеих операционных системах.",
            included_items: "Версии iOS и Android, Push-уведомления, Офлайн-режим, Подключение API, Публикация в App Store & Google Play"
        },
        "SEO Optimizatsiya va Raqamli Marketing": {
            title: "SEO Оптимизация и Цифровой Маркетинг",
            description: "Вывод вашего сайта в Топ-10 Google, технический аудит и повышение конверсии.",
            included_items: "Технический аудит, Анализ ключевых слов, Внутреннее и внешнее SEO, Google Search Console, Ежемесячные отчеты"
        },
        "Zamonaviy UI/UX Dizayn va Prototip": {
            title: "Современный UI/UX Дизайн и Прототипирование",
            description: "Создание удобных, привлекательных и высококонверсионных интерфейсов для пользователей в Figma.",
            included_items: "Дизайн-система Figma, Wireframes и прототипы, Адаптивность для Mobile и Web, User Flow карты"
        },
        "DevOps, CI/CD va Bulutli Infratuzilma": {
            title: "DevOps, CI/CD и Облачная Инфраструктура",
            description: "Автоматизация серверов, контейнеризация Docker и Kubernetes, непрерывная интеграция (CI/CD).",
            included_items: "Контейнеризация Docker, CI/CD через GitHub Actions, Настройка Nginx, SSL сертификаты, Круглосуточный мониторинг"
        }
    },
    en: {
        "Zamonaviy Korporativ Web sayt": {
            title: "Modern Corporate Website",
            description: "Development of a fully functional, responsive, and high-speed modern website for your company and business.",
            included_items: "Responsive Design, Basic SEO, Admin Dashboard, Domain & Hosting Integration, SSL Security"
        },
        "Startaplar uchun MVP Qurish": {
            title: "MVP Development for Startups",
            description: "Building a minimum viable product (MVP) with core features to rapidly launch your startup to market.",
            included_items: "User System, Core Business Logic, Payment Gateways, API Architecture, Testing"
        },
        "Cross-Platform Mobil Ilova (iOS & Android)": {
            title: "Cross-Platform Mobile App (iOS & Android)",
            description: "Professional mobile app development with Flutter and React Native running smoothly on both operating systems.",
            included_items: "iOS and Android versions, Push Notifications, Offline Mode, API Integration, App Store & Google Play Publishing"
        },
        "SEO Optimizatsiya va Raqamli Marketing": {
            title: "SEO Optimization & Digital Marketing",
            description: "Rank your website in the Google Top-10, comprehensive technical audit, and conversion rate optimization.",
            included_items: "Technical Audit, Keyword Research, On-page & Off-page SEO, Google Search Console, Monthly Reports"
        },
        "Zamonaviy UI/UX Dizayn va Prototip": {
            title: "Modern UI/UX Design & Prototyping",
            description: "Creating intuitive, attractive, and high-converting interfaces for users in Figma.",
            included_items: "Figma Design System, Wireframes & Prototypes, Mobile & Web Responsiveness, User Flow Maps"
        },
        "DevOps, CI/CD va Bulutli Infratuzilma": {
            title: "DevOps, CI/CD & Cloud Infrastructure",
            description: "Server automation, Docker and Kubernetes containerization, continuous integration & delivery (CI/CD).",
            included_items: "Docker Containerization, GitHub Actions CI/CD, Nginx Configuration, SSL Certificates, 24/7 Monitoring"
        }
    }
};

// Dynamic Order Status Translations
const statusTranslations = {
    ru: {
        "Yangi": "Новый",
        "Qabul qilindi": "Принят",
        "Jarayonda": "В процессе",
        "Yakunlandi": "Завершен",
        "Bekor qilindi": "Отменен"
    },
    en: {
        "Yangi": "New",
        "Qabul qilindi": "Accepted",
        "Jarayonda": "In Progress",
        "Yakunlandi": "Completed",
        "Bekor qilindi": "Cancelled"
    }
};

// Global Helpers
function getLanguage() {
    return localStorage.getItem('falcon_lang') || 'uz';
}

function setLanguage(lang) {
    if (!translations[lang]) lang = 'uz';
    localStorage.setItem('falcon_lang', lang);
    
    // 1. Update elements with data-i18n
    document.querySelectorAll('[data-i18n]').forEach(el => {
        const key = el.getAttribute('data-i18n');
        if (translations[lang] && translations[lang][key]) {
            el.innerText = translations[lang][key];
        }
    });

    // 2. Update placeholders with data-i18n-placeholder
    document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
        const key = el.getAttribute('data-i18n-placeholder');
        if (translations[lang] && translations[lang][key]) {
            el.setAttribute('placeholder', translations[lang][key]);
        }
    });

    // 3. Update title attributes with data-i18n-title
    document.querySelectorAll('[data-i18n-title]').forEach(el => {
        const key = el.getAttribute('data-i18n-title');
        if (translations[lang] && translations[lang][key]) {
            el.setAttribute('title', translations[lang][key]);
        }
    });

    // 4. Update language select dropdowns on all pages
    document.querySelectorAll('#languageSelect, select[data-lang-picker]').forEach(select => {
        select.value = lang;
    });

    // 5. Notify active components to re-render dynamic content
    window.dispatchEvent(new CustomEvent('languageChanged', { detail: { lang } }));
}

function t(key) {
    const lang = getLanguage();
    return (translations[lang] && translations[lang][key]) || key;
}

function localizeService(service) {
    if (!service) return service;
    const lang = getLanguage();
    if (lang === 'uz') return service;
    
    const lookup = serviceTranslations[lang] && serviceTranslations[lang][service.title];
    if (lookup) {
        return {
            ...service,
            title: lookup.title || service.title,
            description: lookup.description || service.description,
            included_items: lookup.included_items || service.included_items
        };
    }
    return service;
}

function localizeCategory(catName) {
    const lang = getLanguage();
    if (lang === 'uz') return catName;
    return (categoryTranslations[lang] && categoryTranslations[lang][catName]) || catName;
}

function localizeStatus(status) {
    const lang = getLanguage();
    if (lang === 'uz') return status;
    return (statusTranslations[lang] && statusTranslations[lang][status]) || status;
}

function formatDays(days) {
    const lang = getLanguage();
    if (lang === 'ru') return `${days} дней`;
    if (lang === 'en') return `${days} days`;
    return `${days} kun`;
}

document.addEventListener('DOMContentLoaded', () => {
    setLanguage(getLanguage());
});
