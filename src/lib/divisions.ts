import type { Locale } from "@/lib/i18n/config";

export type DivisionKey = "life" | "climate" | "glide" | "shield" | "os" | "health";

export interface DivisionMeta {
  key: DivisionKey;
  /** Brand accent color for this division. */
  color: string;
  /** RGB triplet (for canvas / rgba usage). */
  rgb: string;
  href: string;
  /** Hero background image under /public. */
  image: string;
  /** Division wordmark logo under /public. */
  logo: string;
  name: { ar: string; en: string };
  /** Short label shown in the umbrella grid. */
  label: { ar: string; en: string };
  tagline: { ar: string; en: string };
}

/**
 * The five SYLTRA ONE divisions, in the brand's canonical order:
 * Life → Climate → Glide → Shield → OS.
 */
export const DIVISIONS: DivisionMeta[] = [
  {
    key: "life",
    color: "#4d73ff",
    rgb: "77, 115, 255",
    href: "/life",
    image: "/divisions/life.jpg",
    logo: "/brand/divisions/life.png",
    name: { ar: "سيلترا لايف", en: "Syltra Life" },
    label: { ar: "البيوت والمباني الذكية", en: "Smart homes & buildings" },
    tagline: {
      ar: "الإضاءة والمناخ والأمن والترفيه في منظومة واحدة تتكيّف مع أسلوب حياتك.",
      en: "Lighting, climate, security and entertainment in one system that adapts to how you live.",
    },
  },
  {
    key: "climate",
    color: "#55c9f5",
    rgb: "85, 201, 245",
    href: "/climate",
    image: "/divisions/climate.jpg",
    logo: "/brand/divisions/climate.png",
    name: { ar: "سيلترا كلايمت", en: "Syltra Climate" },
    label: { ar: "التكييف وجودة الهواء", en: "HVAC & air quality" },
    tagline: {
      ar: "من حساب الحمل الحراري والتوريد والتركيب إلى الصيانة الدورية والتحكّم الذكي.",
      en: "From load calculation and installation to preventive maintenance and smart control.",
    },
  },
  {
    key: "glide",
    color: "#7c5cff",
    rgb: "124, 92, 255",
    href: "/glide",
    image: "/divisions/glide.jpg",
    logo: "/brand/divisions/glide.png",
    name: { ar: "سيلترا جلايد", en: "Syltra Glide" },
    label: { ar: "المصاعد والحركة الرأسية", en: "Elevators & vertical mobility" },
    tagline: {
      ar: "توريد وتركيب وتشغيل وصيانة، وتحديث للمصاعد القائمة بمعايير أمان عالية.",
      en: "Supply, installation, operation and maintenance, plus modernization of existing lifts.",
    },
  },
  {
    key: "shield",
    color: "#ffb21c",
    rgb: "255, 178, 28",
    href: "/shield",
    image: "/divisions/shield.jpg",
    logo: "/brand/divisions/shield.png",
    name: { ar: "سيلترا شيلد", en: "Syltra Shield" },
    label: { ar: "الأمن والسلامة والأعمال الهندسية", en: "Security, safety & engineering" },
    tagline: {
      ar: "الحريق والمراقبة والتحكّم بالدخول والتيار المنخفض والبنية الكهربائية.",
      en: "Fire, surveillance, access control, low-current and electrical infrastructure.",
    },
  },
  {
    key: "os",
    color: "#ff5148",
    rgb: "255, 81, 72",
    href: "/os",
    image: "/divisions/os.jpg",
    logo: "/brand/divisions/os.png",
    name: { ar: "سيلترا او إس", en: "Syltra OS" },
    label: { ar: "البرمجيات والذكاء الاصطناعي", en: "Software & AI" },
    tagline: {
      ar: "منتجات جاهزة وأنظمة مخصّصة وحلول ذكاء اصطناعي، من الفكرة حتى التشغيل.",
      en: "Ready products, custom systems and AI solutions, from idea to operation.",
    },
  },
];

/**
 * SYLTRA HEALTH is a separate branded property (health.syltraone.com / the
 * /health section), not one of the engineering divisions above, but it is
 * surfaced on the parent site alongside LIFE.
 */
export const HEALTH_DIVISION: DivisionMeta = {
  key: "health",
  color: "#1aa653",
  rgb: "26, 166, 83",
  href: "/health",
  image: "/brand/health-og.jpg",
  logo: "/brand/health-lockup.png",
  name: { ar: "سيلترا هيلث", en: "Syltra Health" },
  label: { ar: "الصحة والعافية المتصلة", en: "Connected health & wellness" },
  tagline: {
    ar: "منزل يفهم صحتك ويعرف متى تحتاج أحداً، مع سوار وتطبيق ومتابعة هادئة على مدار اليوم.",
    en: "A home that understands your health and knows when you need someone, with a band, an app and calm all-day follow-up.",
  },
};

/**
 * The offerings shown on the parent SYLTRA ONE site. The engineering divisions
 * other than LIFE are currently hidden from all navigation; their routes still
 * exist but are unlinked. LIFE stays reachable from the parent site, and HEALTH
 * is presented beside it.
 */
export const VISIBLE_DIVISIONS: DivisionMeta[] = [
  DIVISIONS.find((d) => d.key === "life")!,
  HEALTH_DIVISION,
];

export function divisionName(d: DivisionMeta, locale: Locale) {
  return locale === "ar" ? d.name.ar : d.name.en;
}
