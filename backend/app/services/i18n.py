"""Internationalization (i18n) service — multi-language support for PANAGAH.

Supported languages: English (en), Urdu (ur), Arabic (ar)
"""

from typing import Optional
from fastapi import APIRouter, Query, Request

router = APIRouter(prefix="/i18n", tags=["Internationalization"])


# ── Translation Database ──────────────────────────────────────────────
TRANSLATIONS = {
    "en": {
        # Navigation
        "nav.home": "Home",
        "nav.build": "Build",
        "nav.materials": "Materials",
        "nav.library": "Library",
        "nav.history": "History",
        "nav.standards": "Standards",
        "nav.review": "Review",

        # Dashboard
        "dashboard.title": "Dashboard",
        "dashboard.total_projects": "Total Projects",
        "dashboard.active_designs": "Active Designs",
        "dashboard.pending_reviews": "Pending Reviews",
        "dashboard.recent_activity": "Recent Activity",

        # Requirements
        "requirements.title": "Requirements",
        "requirements.site_info": "Site Information",
        "requirements.family_details": "Family Details",
        "requirements.climate": "Climate & Environment",
        "requirements.structural": "Structural Properties",
        "requirements.compliance": "Compliance Status",
        "requirements.save": "Save",
        "requirements.mark_ready": "Mark as Ready",

        # Materials
        "materials.title": "Materials",
        "materials.add": "Add Material",
        "materials.name": "Material Name",
        "materials.type": "Material Type",
        "materials.quantity": "Quantity",
        "materials.unit": "Unit",
        "materials.cost": "Unit Cost",
        "materials.available": "Locally Available",

        # Generation
        "generation.title": "Design Generation",
        "generation.generate": "Generate Design",
        "generation.select": "Select",
        "generation.reject": "Reject",
        "generation.pending": "Pending",
        "generation.selected": "Selected",

        # Validation
        "validation.title": "Validation",
        "validation.pass": "Pass",
        "validation.fail": "Fail",
        "validation.warning": "Warning",
        "validation.not_evaluated": "Not Evaluated",

        # Review
        "review.title": "Engineer Review",
        "review.approve": "Approve",
        "review.reject": "Reject",
        "review.request_changes": "Request Changes",
        "review.comments": "Comments",
        "review.decision": "Decision",

        # Common
        "common.save": "Save",
        "common.cancel": "Cancel",
        "common.delete": "Delete",
        "common.edit": "Edit",
        "common.create": "Create",
        "common.loading": "Loading...",
        "common.error": "Error occurred",
        "common.success": "Success",
        "common.back": "Back",
        "common.next": "Next",
        "common.search": "Search...",
        "common.filter": "Filter",
        "common.export": "Export",
        "common.import": "Import",

        # Units
        "unit.meters": "meters",
        "unit.millimeters": "mm",
        "unit.kilograms": "kg",
        "unit.pieces": "pieces",
        "unit.meters_sq": "sq meters",
    },

    "ur": {
        # Navigation
        "nav.home": "ہوم",
        "nav.build": "تعمیر",
        "nav.materials": "مواد",
        "nav.library": "لائبریری",
        "nav.history": "تاریخ",
        "nav.standards": "معیارات",
        "nav.review": "جائزہ",

        # Dashboard
        "dashboard.title": "ڈیش بورڈ",
        "dashboard.total_projects": "کل منصوبے",
        "dashboard.active_designs": "فعال ڈیزائنز",
        "dashboard.pending_reviews": "زیر التوا جائزے",
        "dashboard.recent_activity": "حالیہ سرگرمی",

        # Requirements
        "requirements.title": " تقاضے",
        "requirements.site_info": "سائٹ کی معلومات",
        "requirements.family_details": "خاندان کی تفصیلات",
        "requirements.climate": "موسم اور ماحول",
        "requirements.structural": "ڈھانچے کی خصوصیات",
        "requirements.compliance": " compliance کی حالت",
        "requirements.save": "محفوظ کریں",
        "requirements.mark_ready": "تیار نشان لگائیں",

        # Materials
        "materials.title": "مواد",
        "materials.add": "شامل کریں",
        "materials.name": "مواد کا نام",
        "materials.type": "مواد کی قسم",
        "materials.quantity": "مقدار",
        "materials.unit": "اکائی",
        "materials.cost": "فی اکائی قیمت",
        "materials.available": "مقامی دستیاب",

        # Generation
        "generation.title": "ڈیزائن تخلیق",
        "generation.generate": "ڈیزائن بنائیں",
        "generation.select": "منتخب کریں",
        "generation.reject": "رد کریں",
        "generation.pending": "زیر التوا",
        "generation.selected": "منتخب شدہ",

        # Validation
        "validation.title": "تصدیق",
        "validation.pass": "گزر گیا",
        "validation.fail": "ناکام",
        "validation.warning": "انتباہ",
        "validation.not_evaluated": "جائزہ نہیں لیا گیا",

        # Review
        "review.title": "انجینئر جائزہ",
        "review.approve": "منظوری",
        "review.reject": "رد",
        "review.request_changes": "تبدیلیاں درکار ہیں",
        "review.comments": "تبصرے",
        "review.decision": "فیصلہ",

        # Common
        "common.save": "محفوظ کریں",
        "common.cancel": "منسوخ",
        "common.delete": "حذف کریں",
        "common.edit": "ترمیم",
        "common.create": "بنائیں",
        "common.loading": "لوڈ ہو رہا ہے...",
        "common.error": "خرابی ہوئی",
        "common.success": "کامیابی",
        "common.back": "واپس",
        "common.next": "اگلا",
        "common.search": "تلاش کریں...",
        "common.filter": "فلٹر",
        "common.export": "برآمد",
        "common import": "درآمد",

        # Units
        "unit.meters": "میٹر",
        "unit.millimeters": "ملی میٹر",
        "unit.kilograms": "کلوگرام",
        "unit.pieces": "ٹکڑے",
        "unit.meters_sq": "مربع میٹر",
    },

    "ar": {
        # Navigation
        "nav.home": "الرئيسية",
        "nav.build": "بناء",
        "nav.materials": "المواد",
        "nav.library": "المكتبة",
        "nav.history": "التاريخ",
        "nav.standards": "المعايير",
        "nav.review": "المراجعة",

        # Dashboard
        "dashboard.title": "لوحة التحكم",
        "dashboard.total_projects": "إجمالي المشاريع",
        "dashboard.active_designs": "التصاميم النشطة",
        "dashboard.pending_reviews": "المراجعات المعلقة",
        "dashboard.recent_activity": "النشاط الأخير",

        # Requirements
        "requirements.title": "المتطلبات",
        "requirements.site_info": "معلومات الموقع",
        "requirements.family_details": "تفاصيل العائلة",
        "requirements.climate": "المناخ والبيئة",
        "requirements.structural": "الخصائص الهيكلية",
        "requirements.compliance": "حالة الامتثال",
        "requirements.save": "حفظ",
        "requirements.mark_ready": "تحديد كجاهز",

        # Materials
        "materials.title": "المواد",
        "materials.add": "إضافة",
        "materials.name": "اسم المادة",
        "materials.type": "نوع المادة",
        "materials.quantity": "الكمية",
        "materials.unit": "الوحدة",
        "materials.cost": "سعر الوحدة",
        "materials.available": "متاح محلياً",

        # Generation
        "generation.title": "إنشاء التصميم",
        "generation.generate": "إنشاء",
        "generation.select": "اختيار",
        "generation.reject": "رفض",
        "generation.pending": "قيد الانتظار",
        "generation.selected": "محدد",

        # Validation
        "validation.title": "التحقق",
        "validation.pass": "ناجح",
        "validation.fail": "فاشل",
        "validation.warning": "تحذير",
        "validation.not_evaluated": "لم يتم التقييم",

        # Review
        "review.title": "مراجعة المهندس",
        "review.approve": "موافقة",
        "review.reject": "رفض",
        "review.request_changes": "طلب تغييرات",
        "review.comments": "تعليقات",
        "review.decision": "القرار",

        # Common
        "common.save": "حفظ",
        "common.cancel": "إلغاء",
        "common.delete": "حذف",
        "common.edit": "تعديل",
        "common.create": "إنشاء",
        "common.loading": "جاري التحميل...",
        "common.error": "حدث خطأ",
        "common.success": "نجاح",
        "common.back": "رجوع",
        "common.next": "التالي",
        "common.search": "بحث...",
        "common.filter": "تصفية",
        "common.export": "تصدير",
        "common import": "استيراد",

        # Units
        "unit.meters": "متر",
        "unit.millimeters": "ميليمتر",
        "unit.kilograms": "كيلوجرام",
        "unit.pieces": "قطع",
        "unit.meters_sq": "متر مربع",
    },
}

# Language metadata
LANGUAGES = {
    "en": {"name": "English", "native": "English", "rtl": False, "flag": "🇺🇸"},
    "ur": {"name": "Urdu", "native": "اردو", "rtl": True, "flag": "🇵🇰"},
    "ar": {"name": "Arabic", "native": "العربية", "rtl": True, "flag": "🇸🇦"},
}


class I18nService:
    """Translation service."""

    def __init__(self):
        self._translations = TRANSLATIONS
        self._languages = LANGUAGES

    def translate(self, key: str, lang: str = "en", **kwargs) -> str:
        """Get translation for a key."""
        translations = self._translations.get(lang, self._translations["en"])
        text = translations.get(key, self._translations["en"].get(key, key))

        # Interpolate variables
        if kwargs:
            for k, v in kwargs.items():
                text = text.replace(f"{{{k}}}", str(v))

        return text

    def get_languages(self) -> dict:
        """Get all supported languages."""
        return self._languages

    def get_translations(self, lang: str) -> dict:
        """Get all translations for a language."""
        return self._translations.get(lang, self._translations["en"])

    def get_direction(self, lang: str) -> str:
        """Get text direction for a language."""
        lang_info = self._languages.get(lang, {})
        return "rtl" if lang_info.get("rtl", False) else "ltr"


i18n = I18nService()


# ── API Endpoints ─────────────────────────────────────────────────────

@router.get("/languages", summary="List supported languages")
async def list_languages():
    """Get all supported languages with metadata."""
    return {
        "languages": [
            {
                "code": code,
                "name": info["name"],
                "native": info["native"],
                "rtl": info["rtl"],
                "flag": info["flag"],
            }
            for code, info in LANGUAGES.items()
        ],
        "default": "en",
    }


@router.get("/translate/{lang}", summary="Get all translations for a language")
async def get_translations(lang: str):
    """Get complete translation dictionary for a language."""
    if lang not in TRANSLATIONS:
        return {"error": f"Language '{lang}' not supported", "supported": list(TRANSLATIONS.keys())}

    return {
        "language": lang,
        "direction": i18n.get_direction(lang),
        "translations": i18n.get_translations(lang),
    }


@router.get("/translate/{lang}/{key}", summary="Translate a single key")
async def translate_key(lang: str, key: str):
    """Translate a single key to the specified language."""
    text = i18n.translate(key, lang)
    return {
        "key": key,
        "language": lang,
        "translation": text,
        "direction": i18n.get_direction(lang),
    }
