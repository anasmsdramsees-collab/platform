import type { Locale } from "@/lib/i18n/config";

/** Bilingual string. */
export type L = { ar: string; en: string };
export function pickH(v: L, locale: Locale): string {
  return locale === "ar" ? v.ar : v.en;
}

/** SYLTRA HEALTH accent (division green) + supporting tokens. */
export const HEALTH = {
  accent: "#22e06b",
  accentDim: "#1aa653",
  rgb: "34, 224, 107",
};

export const HEALTH_BRAND = {
  tagline: { ar: "ذكاء متصل لصحة أفضل", en: "Connected Intelligence for Better Health" } as L,
  coreSentence: { ar: "منزل يفهم صحتك، ويعرف متى تحتاج أحداً.", en: "A home that understands your health and knows when you need someone." } as L,
  endorsement: { ar: "إحدى شركات سيلترا وان", en: "A SYLTRA ONE Company" } as L,
  category: {
    ar: "تقنيات الصحة والرفاه المتصل",
    en: "Connected Health and Wellness Technology",
  } as L,
  trustLine: {
    ar: "تقنية مصممة لدعم الفهم والمتابعة، وليست بديلاً عن التقييم أو الرعاية الطبية.",
    en: "Technology designed to support understanding and follow-up. It does not replace medical evaluation or care.",
  } as L,
};

/**
 * SYLTRA HEALTH social channels. Replace the `#` placeholders with the real
 * profile URLs once available (single source of truth for nav/footer).
 */
export const HEALTH_SOCIAL: { name: string; href: string }[] = [
  { name: "LinkedIn", href: "https://www.linkedin.com/company/syltra-health" },
  { name: "X", href: "#" },
  { name: "Instagram", href: "https://www.instagram.com/syltrahealth" },
];

/** Primary navigation for the HEALTH section (locale-less paths under /health). */
export const HEALTH_NAV: { href: string; label: L }[] = [
  { href: "", label: { ar: "الرئيسية", en: "Home" } },
  { href: "/how-it-works", label: { ar: "كيف تعمل", en: "How It Works" } },
  { href: "/individuals", label: { ar: "للأفراد", en: "For Individuals" } },
  { href: "/older-adults", label: { ar: "كبار السن", en: "Older Adults" } },
  { href: "/chronic-conditions", label: { ar: "الحالات المزمنة", en: "Chronic Conditions" } },
  { href: "/medication", label: { ar: "الالتزام الدوائي", en: "Medication" } },
  { href: "/sleep-recovery", label: { ar: "النوم والتعافي", en: "Sleep & Recovery" } },
  { href: "/home-wellness", label: { ar: "صحة المنزل", en: "Home Wellness" } },
  { href: "/care-providers", label: { ar: "لمقدمي الرعاية", en: "For Care Providers" } },
  { href: "/accessibility", label: { ar: "أصحاب الهمم", en: "People of Determination" } },
  { href: "/app", label: { ar: "التطبيق", en: "The App" } },
  { href: "/integrations", label: { ar: "التكاملات", en: "Integrations" } },
  { href: "/blog", label: { ar: "المدونة", en: "Journal" } },
  { href: "/privacy", label: { ar: "الخصوصية", en: "Privacy" } },
  { href: "/about", label: { ar: "عن سيلترا هيلث", en: "About" } },
];

/**
 * "Works with" logo strip shown under the hero copy. Drop official brand files
 * at these same paths to replace the stylized placeholders automatically.
 */
export const WORKS_WITH: { name: string; icon: string }[] = [
  { name: "Apple Health", icon: "/brand/logos/apple-health.svg" },
  { name: "Google Health Connect", icon: "/brand/logos/google-health-connect.png" },
  { name: "Samsung Health", icon: "/brand/logos/samsung-health.jpg" },
  { name: "Fitbit", icon: "/brand/logos/fitbit.png" },
  { name: "WHOOP", icon: "/brand/logos/whoop.webp" },
  { name: "HUAWEI Health", icon: "/brand/logos/huawei-health.webp" },
  { name: "Nike Run Club", icon: "/brand/logos/nike-run-club.jpg" },
  { name: "Apple Home", icon: "/brand/logos/apple-home.png" },
  { name: "Google Home", icon: "/brand/logos/google-home.png" },
  { name: "Home Assistant", icon: "/brand/logos/home-assistant.svg" },
];

/** The four target ecosystems used across hero graphics and the integrations page. */
export type Ecosystem = {
  key: string;
  name: string;
  logo?: string;
  tint: string;
  ar: string;
  en: string;
  status: L;
};

export const ECOSYSTEMS: Ecosystem[] = [
  {
    key: "apple",
    name: "Apple Health",
    tint: "#ffffff",
    ar: "تكامل مستهدف لقراءة أنواع البيانات التي يوافق عليها المستخدم من Apple Health عبر HealthKit، بما يشمل البيانات المدعومة من iPhone وApple Watch. يُطلب الوصول لكل نوع من البيانات بصورة منفصلة وفق نظام صلاحيات Apple.",
    en: "A target integration for reading user-approved data types from Apple Health through HealthKit, including supported data from iPhone and Apple Watch. Access is requested separately for each data type through Apple's permission system.",
    status: { ar: "قيد التطوير والتحقق", en: "Under development and verification" },
  },
  {
    key: "google",
    name: "Google Health Connect",
    tint: "#4285f4",
    ar: "تكامل مستهدف مع Health Connect لجمع بيانات الصحة واللياقة المدعومة على Android من التطبيقات والأجهزة التي يوافق المستخدم على ربطها.",
    en: "A target integration with Health Connect to bring together supported health and fitness data on Android from apps and devices approved by the user.",
    status: { ar: "قيد التطوير والتحقق", en: "Under development and verification" },
  },
  {
    key: "samsung",
    name: "Samsung Health",
    tint: "#1428a0",
    ar: "تكامل مستهدف عبر Samsung Health Data SDK للوصول إلى البيانات التي يختارها المستخدم داخل Samsung Health، بما في ذلك البيانات المدعومة من الهواتف وأجهزة Galaxy Watch وGalaxy Ring المتوافقة.",
    en: "A target integration through the Samsung Health Data SDK for user-selected data in Samsung Health, including supported data from phones and compatible Galaxy Watch and Galaxy Ring devices.",
    status: { ar: "قيد التطوير والتحقق", en: "Under development and verification" },
  },
  {
    key: "whoop",
    name: "WHOOP",
    tint: "#f5f5f5",
    ar: "تكامل مستهدف مع WHOOP Developer Platform لعرض البيانات التي يسمح بها المستخدم، مثل النوم والتعافي والنشاط والتمارين، وفق النطاقات المتاحة في واجهة WHOOP.",
    en: "A target integration with the WHOOP Developer Platform for user-authorized data such as sleep, recovery, activity and workouts, subject to the scopes available through WHOOP.",
    status: { ar: "قيد التطوير والتحقق", en: "Under development and verification" },
  },
];

/**
 * Six-node orbit shown in the hero graphic. The smart home is the foundation:
 * SYLTRA LIFE and Home Sensors sit at the top and are emphasised, with
 * wearables and health apps orbiting around the connected home.
 */
export const HERO_NODES: { label: string; icon: string; emphasis?: boolean }[] = [
  { label: "SYLTRA LIFE", icon: "/brand/health-icons/syltra-life.svg", emphasis: true },
  { label: "Apple Health", icon: "/brand/health-icons/apple-health.svg" },
  { label: "Samsung Health", icon: "/brand/health-icons/samsung-health.svg" },
  { label: "Home Sensors", icon: "/brand/health-icons/home-sensors.svg", emphasis: true },
  { label: "WHOOP", icon: "/brand/health-icons/whoop.svg" },
  { label: "Health Connect", icon: "/brand/health-icons/health-connect.svg" },
];
