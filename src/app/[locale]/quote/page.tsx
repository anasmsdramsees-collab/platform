import type { Metadata } from "next";
import { locales, isLocale, type Locale } from "@/lib/i18n/config";
import { pageMetadata } from "@/lib/seo";
import { QuoteForm, type QuoteCopy } from "@/components/ui/quote-form";
import { InfoCard } from "@/components/ui/info-card";

const COPY: Record<Locale, QuoteCopy & { eyebrow: string; title: string; subtitle: string; promises: { name: string; desc: string }[] }> = {
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
    budget: "الميزانية التقريبية",
    budgetOptions: ["أقل من 20,000 ريال", "20,000 إلى 50,000 ريال", "50,000 إلى 150,000 ريال", "أكثر من 150,000 ريال", "غير محددة بعد"],
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
    budget: "Approximate budget",
    budgetOptions: ["Under SAR 20,000", "SAR 20,000 to 50,000", "SAR 50,000 to 150,000", "Over SAR 150,000", "Not decided yet"],
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

export function generateStaticParams() {
  return locales.map((locale) => ({ locale }));
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>;
}): Promise<Metadata> {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const c = COPY[locale];
  return pageMetadata({ locale, path: "/quote", title: `${c.title} | Syltra One`, description: c.subtitle });
}

export default async function QuotePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale: raw } = await params;
  const locale: Locale = isLocale(raw) ? raw : "en";
  const c = COPY[locale];

  return (
    <section>
      <div className="mx-auto max-w-3xl px-5 py-20 sm:px-8 sm:py-24">
        <div className="text-center">
          <p className="font-mono text-[12px] uppercase tracking-[0.14em] text-slate">{c.eyebrow}</p>
          <h1 className="font-display mt-3 text-balance text-4xl font-bold text-platinum sm:text-5xl">
            {c.title}
          </h1>
          <p className="mx-auto mt-5 max-w-xl text-chrome-dim">{c.subtitle}</p>
        </div>

        <div className="mt-10 grid gap-4 sm:grid-cols-3">
          {c.promises.map((p) => (
            <InfoCard key={p.name} className="p-5">
              <p className="text-sm font-semibold leading-snug text-platinum">{p.name}</p>
              <p className="mt-2 text-[13px] leading-relaxed text-chrome-dim">{p.desc}</p>
            </InfoCard>
          ))}
        </div>

        <div className="mt-8">
          <QuoteForm copy={c} source="quote-page" />
        </div>
      </div>
    </section>
  );
}
