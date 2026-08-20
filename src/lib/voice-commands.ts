export type HomeAction =
  | { kind: "navigate"; path: "products" | "about" | "contact" | "home" }
  | { kind: "lights"; value: boolean }
  | { kind: "climate"; value: boolean }
  | { kind: "curtains"; value: boolean };

interface CommandDef {
  action: HomeAction;
  phrases: string[];
}

// Normalize Arabic so spelling variants match: افتح/إفتح, ستائر/ستاير, ة/ه ...
function normalize(text: string): string {
  return text
    .toLowerCase()
    .replace(/[ً-ْ]/g, "") // diacritics
    .replace(/[أإآ]/g, "ا")
    .replace(/ة/g, "ه")
    .replace(/ى/g, "ي")
    .replace(/ئ/g, "ي")
    .replace(/ؤ/g, "و")
    .replace(/\s+/g, " ")
    .trim();
}

const COMMANDS: CommandDef[] = [
  {
    action: { kind: "navigate", path: "products" },
    phrases: ["open products", "show products", "go to products", "products page", "منتجات", "المنتجات", "افتحي المنتجات", "روحي للمنتجات"],
  },
  {
    action: { kind: "navigate", path: "about" },
    phrases: ["about syntra", "about page", "who are you", "من نحن", "عن سيلترا", "عن الشركة"],
  },
  {
    action: { kind: "navigate", path: "contact" },
    phrases: ["contact us", "contact page", "get in touch", "تواصل معنا", "تواصل", "اتصل بنا"],
  },
  {
    action: { kind: "navigate", path: "home" },
    phrases: ["go home", "homepage", "home page", "الصفحه الرييسيه", "الرييسيه", "الصفحة الرئيسية", "الرئيسية"],
  },
  {
    action: { kind: "lights", value: false },
    phrases: ["turn off the lights", "lights off", "طفي النور", "اطفي النور", "اطفئ النور", "اقفلي النور", "اقفل النور", "طفي الاضاءه", "اطفي الاضاءه", "اقفل الاضاءه", "طفي الانوار", "اطفي الانوار"],
  },
  {
    action: { kind: "lights", value: true },
    phrases: ["turn on the lights", "lights on", "شغلي النور", "شغل النور", "افتحي النور", "افتح النور", "ولعي النور", "ولع النور", "شغل الاضاءه", "شغلي الاضاءه", "افتح الاضاءه", "نوري", "شغل الانوار", "شغلي الانوار"],
  },
  {
    action: { kind: "climate", value: false },
    phrases: ["turn off the ac", "turn off the climate", "ac off", "طفي التكييف", "طفي المكيف", "اطفي التكييف", "اطفي المكيف", "اقفلي التكييف", "اقفل التكييف", "اقفل المكيف"],
  },
  {
    action: { kind: "climate", value: true },
    phrases: ["turn on the ac", "turn on the climate", "ac on", "شغلي التكييف", "شغل التكييف", "شغلي المكيف", "شغل المكيف", "افتح التكييف", "افتح المكيف"],
  },
  {
    action: { kind: "curtains", value: false },
    phrases: ["close the curtains", "curtains closed", "اقفلي الستاير", "اقفل الستاير", "قفل الستاير", "اغلقي الستاير", "اغلق الستاير", "سكري الستاير", "سكر الستاير", "قفلي الستاير"],
  },
  {
    action: { kind: "curtains", value: true },
    phrases: ["open the curtains", "curtains open", "افتحي الستاير", "افتح الستاير", "فتح الستاير", "افتحي الستاره", "افتح الستاره"],
  },
];

// Pre-normalize all phrases once.
const NORMALIZED = COMMANDS.map(({ action, phrases }) => ({
  action,
  phrases: phrases.map(normalize),
}));

export function parseVoiceCommand(transcript: string): HomeAction | null {
  const text = normalize(transcript);
  if (!text) return null;
  for (const { action, phrases } of NORMALIZED) {
    if (phrases.some((phrase) => text.includes(phrase))) return action;
  }
  return null;
}
