# -*- coding: utf-8 -*-
"""Settings catalogue.

Every group and section shown in the settings tree lives here, so the widget
stays a renderer and the data stays reviewable in one place. Section ids are
used as storage keys (``settings.<id>``) and must stay stable.
"""

from __future__ import annotations

# Field kinds: text, password, int, float, percent, bool, choice, multiline,
# path, time, money. Optional keys: options [(label, value)], hint, suffix,
# min, max, step, width.

GROUPS = [
    {
        "key": "general",
        "title": "عامة",
        "icon": "grid",
        "sections": [
            {
                "key": "subscription",
                "title": "الاشتراك",
                "kind": "subscription",
                "note": "بيانات الترخيص والخطة وحالة الصلاحية.",
                "defaults": {
                    "plan": "professional",
                    "license": "",
                    "expires": "",
                    "seats": 30,
                    "auto_renew": True,
                    "support_phone": "",
                },
                "fields": [
                    {"k": "plan", "t": "الخطة", "kind": "choice",
                     "options": [("أساسية", "basic"), ("احترافية", "professional"),
                                 ("مؤسسية", "enterprise")]},
                    {"k": "license", "t": "مفتاح الترخيص", "kind": "password",
                     "hint": "المفتاح المستلم مع الشراء"},
                    {"k": "expires", "t": "تاريخ الانتهاء", "kind": "text",
                     "hint": "اتركه فارغاً لترخيص مفتوح", "width": 190},
                    {"k": "seats", "t": "عدد الأجهزة المسموح", "kind": "int",
                     "min": 1, "max": 500, "width": 140},
                    {"k": "auto_renew", "t": "تجديد تلقائي", "kind": "bool"},
                    {"k": "support_phone", "t": "هاتف الدعم", "kind": "text"},
                ],
            },
            {
                "key": "variables",
                "title": "المتغيرات",
                "kind": "variables",
                "note": "قيم مشتركة يستخدمها النظام في الفواتير والتقارير.",
                "defaults": {
                    "rows": [
                        {"name": "center_name", "value": "Gaming Center Pro"},
                        {"name": "center_phone", "value": ""},
                        {"name": "vat_number", "value": ""},
                        {"name": "receipt_footer", "value": "شكراً لزيارتكم"},
                    ],
                },
            },
            {
                "key": "features",
                "title": "الخصائص",
                "kind": "features",
                "note": "تشغيل أو إخفاء الوحدات من الواجهة.",
                "defaults": {
                    "pos": True, "wallet": True, "library": True, "tasks": True,
                    "reports": True, "rewards": True, "tournaments": True,
                    "studio": True, "bookings": False, "kitchen": False,
                    "loyalty_points": True, "member_self_login": True,
                },
                "features": [
                    ("pos", "نقطة البيع", "شاشة الكاشير والفواتير"),
                    ("wallet", "المحفظة", "إيداع وسحب أرصدة اللاعبين"),
                    ("library", "مكتبة الألعاب", "الألعاب وملفات التشغيل"),
                    ("tasks", "المهام", "أوامر جاهزة على الأجهزة"),
                    ("reports", "التقارير", "المبيعات والجلسات"),
                    ("rewards", "المكافآت", "قواعد النقاط"),
                    ("tournaments", "البطولات", "الجدول والجوائز"),
                    ("studio", "استوديو العميل", "معاينة الشاشة والأوامر"),
                    ("bookings", "الحجوزات", "حجز الأجهزة مسبقاً"),
                    ("kitchen", "المقصف", "طلبات المشروبات والأكل"),
                    ("loyalty_points", "نقاط الولاء", "احتساب نقاط لكل جلسة"),
                    ("member_self_login", "دخول ذاتي", "تسجيل اللاعب بنفسه من الجهاز"),
                ],
            },
            {
                "key": "addons",
                "title": "الإضافات",
                "kind": "addons",
                "note": "وحدات اختيارية تُفعّل عند الحاجة.",
                "defaults": {
                    "screen_stream": False, "telegram": False, "printer": True,
                    "card_reader": False, "cameras": False, "power_relay": False,
                    "ads_screen": False, "mobile_app": False,
                },
                "addons": [
                    ("screen_stream", "بث الشاشة", "معاينة مباشرة لشاشات الأجهزة"),
                    ("telegram", "إشعارات تيليجرام", "تنبيهات الجلسات والأعطال"),
                    ("printer", "طابعة الفواتير", "طباعة الإيصال بعد الدفع"),
                    ("card_reader", "قارئ البطاقات", "دخول اللاعب بالبطاقة"),
                    ("cameras", "الكاميرات", "مراقبة الصالة من اللوحة"),
                    ("power_relay", "تحكم الكهرباء", "تشغيل وإيقاف الأجهزة عن بُعد"),
                    ("ads_screen", "شاشة الإعلانات", "عرض العروض على شاشة خارجية"),
                    ("mobile_app", "تطبيق الجوال", "متابعة الأرقام من الهاتف"),
                ],
            },
            {
                "key": "web",
                "title": "الويب",
                "kind": "form",
                "note": "لوحة الويب للحجوزات والاطلاع من خارج الصالة.",
                "defaults": {
                    "enabled": False, "port": 8090, "base_url": "",
                    "allow_booking": True, "session_minutes": 60,
                },
                "fields": [
                    {"k": "enabled", "t": "تشغيل لوحة الويب", "kind": "bool"},
                    {"k": "port", "t": "المنفذ", "kind": "int", "min": 1, "max": 65535, "width": 140},
                    {"k": "base_url", "t": "العنوان العام", "kind": "text",
                     "hint": "مثال: https://center.example.com"},
                    {"k": "allow_booking", "t": "السماح بالحجز أونلاين", "kind": "bool"},
                    {"k": "session_minutes", "t": "مدة الجلسة", "kind": "int",
                     "suffix": "دقيقة", "min": 5, "max": 480, "width": 150},
                ],
            },
            {
                "key": "work",
                "title": "العمل",
                "kind": "form",
                "note": "ساعات العمل والورديات وحساب التأخير.",
                "defaults": {
                    "open_time": "10:00", "close_time": "02:00",
                    "grace_minutes": 10, "overtime_rate": 1.5,
                    "auto_close_sessions": True, "closing_task": True,
                },
                "fields": [
                    {"k": "open_time", "t": "بداية العمل", "kind": "time", "width": 120},
                    {"k": "close_time", "t": "نهاية العمل", "kind": "time", "width": 120},
                    {"k": "grace_minutes", "t": "سماح التأخير", "kind": "int",
                     "suffix": "دقيقة", "min": 0, "max": 120, "width": 150},
                    {"k": "overtime_rate", "t": "معامل الوقت الإضافي", "kind": "float",
                     "min": 1.0, "max": 3.0, "step": 0.1, "width": 120},
                    {"k": "auto_close_sessions", "t": "إغلاق الجلسات عند الإقفال", "kind": "bool"},
                    {"k": "closing_task", "t": "مهمة تنظيف عند الإقفال", "kind": "bool"},
                ],
            },
            {
                "key": "bookings",
                "title": "الحجوزات",
                "kind": "form",
                "note": "قواعد حجز الأجهزة مقدماً.",
                "defaults": {
                    "enabled": False, "max_per_member": 2, "advance_days": 7,
                    "cancel_hours": 2, "deposit_percent": 20,
                    "require_deposit": True, "no_show_fee": 0,
                },
                "fields": [
                    {"k": "enabled", "t": "تشغيل الحجوزات", "kind": "bool"},
                    {"k": "max_per_member", "t": "أقصى حجوزات للعضو", "kind": "int",
                     "min": 1, "max": 20, "width": 120},
                    {"k": "advance_days", "t": "الحجز قبل", "kind": "int",
                     "suffix": "يوم", "min": 0, "max": 90, "width": 140},
                    {"k": "cancel_hours", "t": "إلغاء مجاني قبل", "kind": "int",
                     "suffix": "ساعة", "min": 0, "max": 72, "width": 140},
                    {"k": "require_deposit", "t": "عربون مطلوب", "kind": "bool"},
                    {"k": "deposit_percent", "t": "نسبة العربون", "kind": "percent",
                     "min": 0, "max": 100, "width": 130},
                    {"k": "no_show_fee", "t": "غرامة عدم الحضور", "kind": "money", "width": 150},
                ],
            },
        ],
    },
    {
        "key": "server",
        "title": "الخادم",
        "icon": "terminal",
        "sections": [
            {
                "key": "network",
                "title": "الشبكة",
                "kind": "network",
                "note": "عنوان السيرفر والمنفذ وإعدادات الاتصال.",
                "defaults": {
                    "host": "127.0.0.1", "port": 54321, "timeout": 6,
                    "auto_reconnect": True, "max_clients": 200,
                    "protocol": "framed", "heartbeat": 15,
                },
                "fields": [
                    {"k": "host", "t": "عنوان السيرفر", "kind": "text"},
                    {"k": "port", "t": "المنفذ", "kind": "int", "min": 1, "max": 65535, "width": 140},
                    {"k": "timeout", "t": "مهلة الاتصال", "kind": "int",
                     "suffix": "ثانية", "min": 1, "max": 60, "width": 140},
                    {"k": "auto_reconnect", "t": "إعادة اتصال تلقائية", "kind": "bool"},
                    {"k": "max_clients", "t": "أقصى اتصالات", "kind": "int",
                     "min": 1, "max": 2000, "width": 140},
                    {"k": "protocol", "t": "البروتوكول", "kind": "choice",
                     "options": [("إطارات JSON", "framed"), ("JSON مباشر", "legacy")]},
                    {"k": "heartbeat", "t": "نبضة كل", "kind": "int",
                     "suffix": "ثانية", "min": 3, "max": 120, "width": 140},
                ],
            },
            {
                "key": "database",
                "title": "قاعدة البيانات",
                "kind": "database",
                "note": "بيانات الاتصال الحالية وحالة القاعدة.",
                "defaults": {"timeout": 10, "retries": 2, "auto_migrate": True},
                "fields": [
                    {"k": "timeout", "t": "مهلة الاستعلام", "kind": "int",
                     "suffix": "ثانية", "min": 1, "max": 120, "width": 140},
                    {"k": "retries", "t": "عدد المحاولات", "kind": "int",
                     "min": 0, "max": 10, "width": 120},
                    {"k": "auto_migrate", "t": "ترحيل تلقائي عند التشغيل", "kind": "bool"},
                ],
            },
            {
                "key": "backup",
                "title": "النسخ الاحتياطي",
                "kind": "backup",
                "note": "نسخة كاملة من قاعدة البيانات كل يوم.",
                "defaults": {
                    "folder": "backups", "retention_days": 14, "keep": 20,
                    "auto_daily": True, "time": "03:00",
                },
                "fields": [
                    {"k": "folder", "t": "مجلد النسخ", "kind": "path"},
                    {"k": "retention_days", "t": "الاحتفاظ", "kind": "int",
                     "suffix": "يوم", "min": 1, "max": 365, "width": 140},
                    {"k": "keep", "t": "أقصى عدد نسخ", "kind": "int",
                     "min": 1, "max": 200, "width": 140},
                    {"k": "auto_daily", "t": "نسخة يومية تلقائية", "kind": "bool"},
                    {"k": "time", "t": "وقت النسخ", "kind": "time", "width": 120},
                ],
            },
            {
                "key": "filesystem",
                "title": "نظام الملفات",
                "kind": "filesystem",
                "note": "مسارات السجلات والنسخ وأيقونات الألعاب.",
                "defaults": {
                    "logs": "Logs", "backups": "backups", "icons": "GameIcons",
                    "max_log_mb": 10, "cleanup_days": 30,
                },
                "fields": [
                    {"k": "logs", "t": "مجلد السجلات", "kind": "path"},
                    {"k": "backups", "t": "مجلد النسخ", "kind": "path"},
                    {"k": "icons", "t": "مجلد الأيقونات", "kind": "path"},
                    {"k": "max_log_mb", "t": "أقصى حجم للسجل", "kind": "int",
                     "suffix": "MB", "min": 1, "max": 500, "width": 140},
                    {"k": "cleanup_days", "t": "حذف السجلات بعد", "kind": "int",
                     "suffix": "يوم", "min": 1, "max": 365, "width": 140},
                ],
            },
            {
                "key": "server_misc",
                "title": "متنوعة",
                "kind": "form",
                "note": "خيارات التشغيل والصيانة.",
                "defaults": {
                    "maintenance": False, "debug": False,
                    "telemetry_days": 90, "timezone": "Asia/Riyadh",
                    "language": "ar",
                },
                "fields": [
                    {"k": "maintenance", "t": "وضع الصيانة", "kind": "bool",
                     "hint": "يمنع تسجيل الدخول للاعبين"},
                    {"k": "debug", "t": "سجل تفصيلي", "kind": "bool"},
                    {"k": "telemetry_days", "t": "الاحتفاظ بقياسات العتاد", "kind": "int",
                     "suffix": "يوم", "min": 1, "max": 365, "width": 140},
                    {"k": "timezone", "t": "المنطقة الزمنية", "kind": "choice",
                     "options": [("الرياض", "Asia/Riyadh"), ("القاهرة", "Africa/Cairo"),
                                 ("دبي", "Asia/Dubai"), ("عمّان", "Asia/Amman"),
                                 ("الكويت", "Asia/Kuwait"), ("الدوحة", "Asia/Qatar")]},
                    {"k": "language", "t": "لغة الواجهة", "kind": "choice",
                     "options": [("العربية", "ar"), ("English", "en")]},
                ],
            },
        ],
    },
    {
        "key": "client",
        "title": "التابع",
        "icon": "monitor",
        "sections": [
            {
                "key": "client_ui",
                "title": "الواجهة",
                "kind": "form",
                "note": "شكل شاشة الجهاز التي يراها اللاعب.",
                "defaults": {
                    "theme": "night", "font_scale": 100, "show_clock": True,
                    "show_session": True, "lock_message": "الجهاز مقفل — يرجى مراجعة الكاشير",
                    "idle_overlay": True,
                },
                "fields": [
                    {"k": "theme", "t": "مظهر الجهاز", "kind": "choice",
                     "options": [("ليلي", "night"), ("حبر", "ink"), ("غابة", "forest"),
                                 ("توت", "plum"), ("ورقي", "paper"), ("ضباب", "mist")]},
                    {"k": "font_scale", "t": "حجم الخط", "kind": "percent",
                     "min": 80, "max": 160, "width": 130},
                    {"k": "show_clock", "t": "إظهار الساعة", "kind": "bool"},
                    {"k": "show_session", "t": "إظهار الوقت المتبقي", "kind": "bool"},
                    {"k": "lock_message", "t": "رسالة شاشة القفل", "kind": "multiline"},
                    {"k": "idle_overlay", "t": "طبقة الخمول", "kind": "bool"},
                ],
            },
            {
                "key": "client_agent",
                "title": "إعدادات التابع",
                "kind": "form",
                "note": "طريقة عمل برنامج الجهاز.",
                "defaults": {
                    "name_prefix": "PC", "autostart": True, "reconnect": 5,
                    "heartbeat": 15, "lock_idle_minutes": 10,
                    "allow_self_login": True, "screenshot_on_lock": False,
                },
                "fields": [
                    {"k": "name_prefix", "t": "بادئة اسم الجهاز", "kind": "text", "width": 150},
                    {"k": "autostart", "t": "بدء مع ويندوز", "kind": "bool"},
                    {"k": "reconnect", "t": "إعادة الاتصال كل", "kind": "int",
                     "suffix": "ثانية", "min": 1, "max": 120, "width": 140},
                    {"k": "heartbeat", "t": "إرسال النبضة كل", "kind": "int",
                     "suffix": "ثانية", "min": 3, "max": 120, "width": 140},
                    {"k": "lock_idle_minutes", "t": "قفل عند الخمول", "kind": "int",
                     "suffix": "دقيقة", "min": 1, "max": 180, "width": 140},
                    {"k": "allow_self_login", "t": "دخول اللاعب بنفسه", "kind": "bool"},
                    {"k": "screenshot_on_lock", "t": "لقطة عند القفل", "kind": "bool"},
                ],
            },
            {
                "key": "client_tasks",
                "title": "المهام",
                "kind": "form",
                "note": "ضوابط تنفيذ الأوامر على الأجهزة.",
                "defaults": {
                    "timeout": 60, "retries": 1, "run_as_admin": False,
                    "log_results": True, "allow_custom": True,
                    "allowed": "LOCK, UNLOCK, RESTART, SHUTDOWN, MESSAGE, LAUNCH",
                },
                "fields": [
                    {"k": "timeout", "t": "مهلة المهمة", "kind": "int",
                     "suffix": "ثانية", "min": 5, "max": 600, "width": 140},
                    {"k": "retries", "t": "إعادة المحاولة", "kind": "int",
                     "min": 0, "max": 5, "width": 120},
                    {"k": "run_as_admin", "t": "تشغيل بصلاحية مدير", "kind": "bool"},
                    {"k": "log_results", "t": "تسجيل النتائج", "kind": "bool"},
                    {"k": "allow_custom", "t": "السماح بأوامر مخصصة", "kind": "bool"},
                    {"k": "allowed", "t": "الأوامر المسموحة", "kind": "multiline",
                     "hint": "مفصولة بفاصلة"},
                ],
            },
            {
                "key": "client_help",
                "title": "أنواع طلبات المساعدة",
                "kind": "table",
                "note": "الطلبات التي يرسلها اللاعب من شاشته.",
                "defaults": {
                    "rows": [
                        {"name": "مشكلة في الجهاز", "minutes": 5, "priority": "عالية", "active": True},
                        {"name": "طلب مشروب", "minutes": 10, "priority": "عادية", "active": True},
                        {"name": "تغيير لعبة", "minutes": 5, "priority": "عادية", "active": True},
                        {"name": "استفسار عن الفاتورة", "minutes": 15, "priority": "منخفضة", "active": True},
                    ],
                },
                "columns": [
                    ("name", "النوع", "text", 190),
                    ("minutes", "زمن الاستجابة", "int", 110),
                    ("priority", "الأولوية", "text", 100),
                    ("active", "مفعّل", "bool", 70),
                ],
            },
            {
                "key": "client_misc",
                "title": "متنوعة",
                "kind": "form",
                "note": "التحديثات وإصدار برنامج الجهاز.",
                "defaults": {
                    "channel": "stable", "auto_update": True, "update_url": "",
                    "min_version": "3.6.0",
                },
                "fields": [
                    {"k": "channel", "t": "قناة التحديث", "kind": "choice",
                     "options": [("مستقرة", "stable"), ("تجريبية", "beta")]},
                    {"k": "auto_update", "t": "تحديث تلقائي", "kind": "bool"},
                    {"k": "update_url", "t": "مصدر التحديث", "kind": "text"},
                    {"k": "min_version", "t": "أقل إصدار مسموح", "kind": "text", "width": 150},
                ],
            },
        ],
    },
    {
        "key": "finance",
        "title": "المالية",
        "icon": "wallet",
        "sections": [
            {
                "key": "products",
                "title": "المنتجات",
                "kind": "form",
                "note": "القيم الافتراضية عند إضافة منتج أو خدمة.",
                "defaults": {
                    "default_category": "خدمات", "default_tax": 15,
                    "unit": "حبة", "allow_negative": False,
                    "require_barcode": False, "service_item": False,
                },
                "fields": [
                    {"k": "default_category", "t": "التصنيف الافتراضي", "kind": "text", "width": 190},
                    {"k": "default_tax", "t": "الضريبة الافتراضية", "kind": "percent",
                     "min": 0, "max": 100, "width": 130},
                    {"k": "unit", "t": "الوحدة", "kind": "choice",
                     "options": [("حبة", "حبة"), ("ساعة", "ساعة"), ("علبة", "علبة"), ("كوب", "كوب")]},
                    {"k": "allow_negative", "t": "السماح بمخزون سالب", "kind": "bool"},
                    {"k": "require_barcode", "t": "باركود إلزامي", "kind": "bool"},
                    {"k": "service_item", "t": "المنتجات خدمات افتراضياً", "kind": "bool"},
                ],
            },
            {
                "key": "payments",
                "title": "طرق الدفع",
                "kind": "table",
                "note": "الطرق المتاحة في نقطة البيع.",
                "defaults": {
                    "rows": [
                        {"name": "نقداً", "type": "cash", "fee": 0.0, "active": True},
                        {"name": "شبكة", "type": "card", "fee": 1.5, "active": True},
                        {"name": "محفظة", "type": "wallet", "fee": 0.0, "active": True},
                        {"name": "تحويل بنكي", "type": "transfer", "fee": 0.0, "active": False},
                    ],
                },
                "columns": [
                    ("name", "الطريقة", "text", 160),
                    ("type", "النوع", "text", 110),
                    ("fee", "العمولة %", "float", 100),
                    ("active", "مفعّل", "bool", 70),
                ],
            },
            {
                "key": "assets",
                "title": "الأصول",
                "kind": "form",
                "note": "أجهزة الصالة كأصول لها عمر وصيانة.",
                "defaults": {
                    "track": True, "lifetime_months": 36,
                    "maintenance_days": 180, "warranty_days": 365,
                },
                "fields": [
                    {"k": "track", "t": "تتبع الأصول", "kind": "bool"},
                    {"k": "lifetime_months", "t": "العمر الافتراضي", "kind": "int",
                     "suffix": "شهر", "min": 6, "max": 120, "width": 140},
                    {"k": "maintenance_days", "t": "صيانة كل", "kind": "int",
                     "suffix": "يوم", "min": 7, "max": 730, "width": 140},
                    {"k": "warranty_days", "t": "الضمان", "kind": "int",
                     "suffix": "يوم", "min": 0, "max": 1460, "width": 140},
                ],
            },
            {
                "key": "priorities",
                "title": "الأولويات",
                "kind": "table",
                "note": "أولوية الخدمة حسب فئة العضو.",
                "defaults": {
                    "rows": [
                        {"name": "VIP", "discount": 15.0, "queue": 1, "active": True},
                        {"name": "عضو دائم", "discount": 10.0, "queue": 2, "active": True},
                        {"name": "زائر", "discount": 0.0, "queue": 3, "active": True},
                    ],
                },
                "columns": [
                    ("name", "الفئة", "text", 170),
                    ("discount", "خصم %", "float", 100),
                    ("queue", "الأولوية", "int", 100),
                    ("active", "مفعّل", "bool", 70),
                ],
            },
            {
                "key": "product_groups",
                "title": "مجموعات المنتجات",
                "kind": "table",
                "note": "تجميع المنتجات مع خصم أو ضريبة مختلفة.",
                "defaults": {
                    "rows": [
                        {"name": "مشروبات", "discount": 0.0, "tax": 15.0, "active": True},
                        {"name": "سناكس", "discount": 5.0, "tax": 15.0, "active": True},
                        {"name": "ساعات لعب", "discount": 0.0, "tax": 15.0, "active": True},
                        {"name": "خدمات إضافية", "discount": 0.0, "tax": 15.0, "active": True},
                    ],
                },
                "columns": [
                    ("name", "المجموعة", "text", 180),
                    ("discount", "خصم %", "float", 100),
                    ("tax", "الضريبة %", "float", 100),
                    ("active", "مفعّل", "bool", 70),
                ],
            },
            {
                "key": "cashiers",
                "title": "الكاشيرات",
                "kind": "table",
                "note": "من يقف على الصندوق وما الوردية المسموحة له.",
                "defaults": {
                    "rows": [
                        {"name": "أحمد", "pin": "1234", "shift": "صباحية", "active": True},
                        {"name": "سارة", "pin": "2345", "shift": "مسائية", "active": True},
                        {"name": "خالد", "pin": "3456", "shift": "ليلية", "active": False},
                    ],
                },
                "columns": [
                    ("name", "الاسم", "text", 150),
                    ("pin", "الرمز", "text", 90),
                    ("shift", "الوردية", "text", 110),
                    ("active", "مفعّل", "bool", 70),
                ],
            },
            {
                "key": "tax",
                "title": "الضريبة",
                "kind": "form",
                "note": "تُطبَّق فوراً على نقطة البيع والفواتير.",
                "defaults": {
                    "enabled": True, "rate": 15.0, "inclusive": False,
                    "label": "ضريبة القيمة المضافة", "number": "",
                    "rounding": "nearest",
                },
                "fields": [
                    {"k": "enabled", "t": "تفعيل الضريبة", "kind": "bool"},
                    {"k": "rate", "t": "النسبة", "kind": "percent",
                     "min": 0, "max": 100, "width": 130},
                    {"k": "inclusive", "t": "السعر يشمل الضريبة", "kind": "bool"},
                    {"k": "label", "t": "اسم الضريبة في الفاتورة", "kind": "text"},
                    {"k": "number", "t": "الرقم الضريبي", "kind": "text"},
                    {"k": "rounding", "t": "التقريب", "kind": "choice",
                     "options": [("لأقرب", "nearest"), ("لأعلى", "up"), ("لأسفل", "down")]},
                ],
            },
            {
                "key": "currencies",
                "title": "العملات النقدية",
                "kind": "currencies",
                "note": "العملة الافتراضية وأسعار التحويل.",
                "defaults": {
                    "default": "SAR",
                    "rows": [
                        {"code": "SAR", "symbol": "ر.س", "rate": 1.0, "active": True},
                        {"code": "EGP", "symbol": "ج.م", "rate": 13.0, "active": True},
                        {"code": "USD", "symbol": "$", "rate": 0.27, "active": False},
                        {"code": "AED", "symbol": "د.إ", "rate": 0.98, "active": False},
                    ],
                },
                "columns": [
                    ("code", "الرمز", "text", 90),
                    ("symbol", "العلامة", "text", 90),
                    ("rate", "سعر التحويل", "float", 120),
                    ("active", "مفعّل", "bool", 70),
                ],
            },
            {
                "key": "price_plans",
                "title": "خطط الأسعار",
                "kind": "table",
                "note": "أسعار الساعة والحد الأدنى للجلسة.",
                "defaults": {
                    "rows": [
                        {"name": "عادي", "hourly": 15.0, "minimum": 30, "discount": 0.0, "active": True},
                        {"name": "ليلي", "hourly": 12.0, "minimum": 60, "discount": 10.0, "active": True},
                        {"name": "نهاية الأسبوع", "hourly": 20.0, "minimum": 30, "discount": 0.0, "active": True},
                        {"name": "بطولة", "hourly": 25.0, "minimum": 120, "discount": 5.0, "active": False},
                    ],
                },
                "columns": [
                    ("name", "الخطة", "text", 150),
                    ("hourly", "سعر الساعة", "float", 110),
                    ("minimum", "أدنى دقائق", "int", 110),
                    ("discount", "خصم %", "float", 90),
                    ("active", "مفعّل", "bool", 70),
                ],
            },
            {
                "key": "presets",
                "title": "الإعدادات المسبقة",
                "kind": "table",
                "note": "أزرار جاهزة تظهر في نقطة البيع والمحفظة.",
                "defaults": {
                    "rows": [
                        {"name": "ساعة لعب", "kind": "session", "value": "60", "active": True},
                        {"name": "نصف ساعة", "kind": "session", "value": "30", "active": True},
                        {"name": "شحن 50", "kind": "deposit", "value": "50", "active": True},
                        {"name": "خصم 10%", "kind": "discount", "value": "10", "active": False},
                    ],
                },
                "columns": [
                    ("name", "الاسم", "text", 160),
                    ("kind", "النوع", "text", 110),
                    ("value", "القيمة", "text", 90),
                    ("active", "مفعّل", "bool", 70),
                ],
            },
        ],
    },
    {
        "key": "profiles",
        "title": "المجموعات وملفات التعريف",
        "icon": "users",
        "sections": [
            {
                "key": "followers",
                "title": "التوابع",
                "kind": "table",
                "note": "أجهزة مساعدة تتصل بالخادم (كاشير فرعي، شاشة عرض).",
                "defaults": {
                    "rows": [
                        {"name": "كاشير 2", "host": "192.168.1.20", "port": 54321, "role": "cashier", "active": True},
                        {"name": "شاشة العرض", "host": "192.168.1.21", "port": 54321, "role": "display", "active": False},
                    ],
                },
                "columns": [
                    ("name", "الاسم", "text", 150),
                    ("host", "العنوان", "text", 140),
                    ("port", "المنفذ", "int", 80),
                    ("role", "الدور", "text", 100),
                    ("active", "مفعّل", "bool", 70),
                ],
            },
            {
                "key": "control_devices",
                "title": "أجهزة التحكم",
                "kind": "table",
                "note": "مرحّلات الكهرباء والكاميرات والطابعات.",
                "defaults": {
                    "rows": [
                        {"name": "مرحّل الصالة", "type": "relay", "address": "192.168.1.50", "active": True},
                        {"name": "كاميرا المدخل", "type": "camera", "address": "192.168.1.60", "active": True},
                        {"name": "طابعة الكاشير", "type": "printer", "address": "USB001", "active": True},
                    ],
                },
                "columns": [
                    ("name", "الجهاز", "text", 170),
                    ("type", "النوع", "text", 110),
                    ("address", "العنوان", "text", 150),
                    ("active", "مفعّل", "bool", 70),
                ],
            },
            {
                "key": "dashboard",
                "title": "لوحة التحكم",
                "kind": "form",
                "note": "ما يظهر في النظرة العامة وكم مرة يتحدث.",
                "defaults": {
                    "start_page": "overview", "refresh": 5, "compact": False,
                    "show_kpis": True, "show_floor": True,
                    "show_finance": True, "show_alerts": True,
                },
                "fields": [
                    {"k": "start_page", "t": "الصفحة الافتتاحية", "kind": "choice",
                     "options": [("نظرة عامة", "overview"), ("الأجهزة", "devices"),
                                 ("نقطة البيع", "pos"), ("التقارير", "reports")]},
                    {"k": "refresh", "t": "تحديث كل", "kind": "int",
                     "suffix": "ثانية", "min": 1, "max": 60, "width": 140},
                    {"k": "compact", "t": "عرض مضغوط", "kind": "bool"},
                    {"k": "show_kpis", "t": "بطاقات الأرقام", "kind": "bool"},
                    {"k": "show_floor", "t": "قائمة الأجهزة", "kind": "bool"},
                    {"k": "show_finance", "t": "ملخص الإيراد", "kind": "bool"},
                    {"k": "show_alerts", "t": "التنبيهات", "kind": "bool"},
                ],
            },
        ],
    },
    {
        "key": "operators",
        "title": "المشغلين",
        "icon": "settings",
        "sections": [
            {
                "key": "operators",
                "title": "المشغلين",
                "kind": "table",
                "note": "حسابات الموظفين وصلاحياتهم.",
                "defaults": {
                    "rows": [
                        {"name": "مدير النظام", "role": "admin", "pin": "0000", "active": True},
                        {"name": "أحمد", "role": "cashier", "pin": "1234", "active": True},
                        {"name": "سارة", "role": "supervisor", "pin": "2345", "active": True},
                    ],
                },
                "columns": [
                    ("name", "الاسم", "text", 170),
                    ("role", "الدور", "text", 120),
                    ("pin", "الرمز", "text", 90),
                    ("active", "مفعّل", "bool", 70),
                ],
            }
        ],
    },
]


def sections():
    """Flat list of (group, section) pairs in display order."""
    for group in GROUPS:
        for section in group["sections"]:
            section.setdefault("group_title", group["title"])
            yield group, section


def find(section_key: str):
    for group, section in sections():
        if section["key"] == section_key:
            return group, section
    return None, None
