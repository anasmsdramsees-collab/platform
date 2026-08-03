export type HomeAction =
  | { kind: "navigate"; path: "products" | "about" | "contact" | "home" }
  | { kind: "lights"; value: boolean }
  | { kind: "climate"; value: boolean }
  | { kind: "curtains"; value: boolean };

interface CommandDef {
  action: HomeAction;
  phrases: string[];
}

const COMMANDS: CommandDef[] = [
  {
    action: { kind: "navigate", path: "products" },
    phrases: ["open products", "show products", "go to products", "products page", "منتجات", "المنتجات", "افتحي المنتجات", "روحي للمنتجات"],
  },
  {
    action: { kind: "navigate", path: "about" },
    phrases: ["about syntra", "about page", "who are you", "من نحن", "عن سنترا", "عن الشركة"],
  },
  {
    action: { kind: "navigate", path: "contact" },
    phrases: ["contact us", "contact page", "get in touch", "تواصل معنا", "تواصل", "اتصل بنا"],
  },
  {
    action: { kind: "navigate", path: "home" },
    phrases: ["go home", "homepage", "home page", "الصفحة الرئيسية", "الرئيسية"],
  },
  {
    action: { kind: "lights", value: false },
    phrases: ["turn off the lights", "lights off", "طفي النور", "اطفي النور", "اقفلي النور"],
  },
  {
    action: { kind: "lights", value: true },
    phrases: ["turn on the lights", "lights on", "شغلي النور", "شغل النور", "افتحي النور"],
  },
  {
    action: { kind: "climate", value: false },
    phrases: ["turn off the ac", "turn off the climate", "ac off", "طفي التكييف", "طفي المكيف", "اقفلي التكييف"],
  },
  {
    action: { kind: "climate", value: true },
    phrases: ["turn on the ac", "turn on the climate", "ac on", "شغلي التكييف", "شغل التكييف", "شغلي المكيف"],
  },
  {
    action: { kind: "curtains", value: false },
    phrases: ["close the curtains", "curtains closed", "اقفلي الستائر", "قفل الستائر", "اغلقي الستائر"],
  },
  {
    action: { kind: "curtains", value: true },
    phrases: ["open the curtains", "curtains open", "افتحي الستائر", "فتح الستائر"],
  },
];

export function parseVoiceCommand(transcript: string): HomeAction | null {
  const text = transcript.trim().toLowerCase();
  if (!text) return null;
  for (const { action, phrases } of COMMANDS) {
    if (phrases.some((phrase) => text.includes(phrase))) return action;
  }
  return null;
}
