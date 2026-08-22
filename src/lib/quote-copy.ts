import type { Locale } from "@/lib/i18n/config";
import type { QuoteCopy } from "@/components/ui/quote-form";

/** Shared between the booking page and every landing page. */
export const quoteCopy: Record<Locale, QuoteCopy & {
  eyebrow: string;
  title: string;
  subtitle: string;
  promises: { name: string; desc: string }[];
}> = {
  ar: {
    eyebrow: "احجز معاينة",
    title: "معاينة مجانية، وعرض سعر واضح.",
    subtitle:
      "املأ النموذج وسيتواصل معك فريق سيلترا خلال يوم عمل واحد لتحديد موعد المعاينة. المعاينة والتقدير المبدئي بدون أي رسوم.",
    promises: [
      { name: "رد خلال يوم عمل", desc: "نتواصل معك على الجوال أو الواتساب لتحديد الموعد المناسب." },
      { name: "معاينة بدون رسوم", desc: "نزور الموقع، نقيس الاحتياج، ونشرح الخيارات قبل أي التزام." },
      { name: "عرض سعر مفصّل", desc: "أجهزة وتركيب وبرمجة وضمان، كل بند بسعره وبدون مفاجآت." },
    ],
    name: "الاسم الكامل *",
    phone: "رقم الجوال *",
    email: "البريد الإلكتروني",
    city: "المدينة",
    propertyType: "نوع العقار",
    propertyOptions: ["شقة", "فيلا", "قصر", "مكتب أو مقر", "فندق أو شقق فندقية", "مجمع سكني", "محل تجاري", "مزرعة أو استراحة"],
    interests: "ما الذي يهمك؟",
    interestOptions: ["الإضاءة الذكية", "الستائر", "التكييف", "الأقفال الذكية", "كاميرات المراقبة", "الحساسات والسلامة", "أنظمة الصوت", "سيلترا تي في", "شاشات التحكم", "نظام كامل للمنزل"],
    notes: "تفاصيل إضافية عن المشروع (اختياري)",
    submit: "أرسل الطلب",
    sending: "جارٍ الإرسال...",
    error: "تعذر إرسال الطلب، حاول مرة أخرى أو راسلنا على الواتساب.",
    successTitle: "استلمنا طلبك",
    successBody: "شكرًا لك. سيتواصل معك فريق سيلترا خلال يوم عمل واحد لتحديد موعد المعاينة.",
    again: "إرسال طلب آخر",
    privacy: "نستخدم بياناتك للتواصل معك بخصوص هذا الطلب فقط.",
  },
  en: {
    eyebrow: "Book a survey",
    title: "A free site survey and a clear quote.",
    subtitle:
      "Fill in the form and the Syltra team will contact you within one working day to arrange the survey. The visit and the initial estimate carry no fee.",
    promises: [
      { name: "A reply within one working day", desc: "We call or message you on WhatsApp to agree a time that suits you." },
      { name: "No-fee site survey", desc: "We visit, measure the need, and walk you through the options before any commitment." },
      { name: "An itemised quote", desc: "Devices, installation, programming and warranty, each line priced, with no surprises." },
    ],
    name: "Full name *",
    phone: "Phone number *",
    email: "Email address",
    city: "City",
    propertyType: "Property type",
    propertyOptions: ["Apartment", "Villa", "Palace", "Office or headquarters", "Hotel or serviced apartments", "Residential compound", "Retail unit", "Farm or rest house"],
    interests: "What are you interested in?",
    interestOptions: ["Smart lighting", "Curtains", "Air conditioning", "Smart locks", "CCTV cameras", "Sensors and safety", "Audio systems", "Syltra TV", "Control panels", "A complete home system"],
    notes: "Anything else about the project (optional)",
    submit: "Send request",
    sending: "Sending...",
    error: "The request could not be sent. Please try again or message us on WhatsApp.",
    successTitle: "We have your request",
    successBody: "Thank you. The Syltra team will contact you within one working day to arrange the survey.",
    again: "Send another request",
    privacy: "We use your details only to contact you about this request.",
  },
};
