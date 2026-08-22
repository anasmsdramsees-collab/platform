import type { Locale } from "@/lib/i18n/config";

export type PropertyKind = "villa" | "office" | "apartment";
export type SystemKey =
  | "lighting"
  | "curtains"
  | "climate"
  | "security"
  | "cameras"
  | "audio"
  | "motion"
  | "gas"
  | "health";

/** Villas get ducted central air; apartments and offices get wall splits. */
export type ClimateKind = "central" | "split";

export interface RoomDef {
  id: string;
  /** Footprint in metres: [x, z] centre and [w, d] size on the floor grid. */
  centre: [number, number];
  size: [number, number];
  /** Which floor level the room sits on. */
  level: number;
  ar: string;
  en: string;
  /** Systems that make sense in this room, used to price and to place fixtures. */
  systems: SystemKey[];
  /** Which side of the room carries the window, so curtains hang correctly. */
  window?: "north" | "south" | "east" | "west";
}

export interface PropertyDef {
  kind: PropertyKind;
  levels: number;
  climate: ClimateKind;
  ar: { name: string; blurb: string };
  en: { name: string; blurb: string };
  rooms: RoomDef[];
}

export const SYSTEMS: {
  key: SystemKey;
  color: string;
  ar: { name: string; desc: string };
  en: { name: string; desc: string };
}[] = [
  {
    key: "lighting",
    color: "#f5c451",
    ar: { name: "الإضاءة الذكية", desc: "مفاتيح ومعتّمات ومشاهد جاهزة لكل غرفة." },
    en: { name: "Smart lighting", desc: "Switches, dimmers and ready-made scenes in every room." },
  },
  {
    key: "curtains",
    color: "#8ab4ff",
    ar: { name: "الستائر", desc: "محركات تفتح مع المنبه وتغلق عند الغروب." },
    en: { name: "Curtains", desc: "Motors that open with your alarm and close at sunset." },
  },
  {
    key: "climate",
    color: "#5ed4d0",
    ar: { name: "التكييف", desc: "تحكم بالحرارة لكل منطقة وجدولة توفّر الكهرباء." },
    en: { name: "Climate", desc: "Per-zone temperature control and schedules that save power." },
  },
  {
    key: "security",
    color: "#ff6b6b",
    ar: { name: "الأقفال والأمان", desc: "أقفال بالبصمة وحساسات أبواب ونوافذ." },
    en: { name: "Locks and safety", desc: "Fingerprint locks with door and window sensors." },
  },
  {
    key: "cameras",
    color: "#c78bff",
    ar: { name: "الكاميرات", desc: "مراقبة داخلية وخارجية بتسجيل يبقى ملكك." },
    en: { name: "Cameras", desc: "Indoor and outdoor surveillance, with recordings that stay yours." },
  },
  {
    key: "motion",
    color: "#ffa94d",
    ar: { name: "حساسات الحركة", desc: "الممرات تضيء عند المرور وتطفئ وحدها." },
    en: { name: "Motion sensors", desc: "Hallways light as you pass and switch themselves off." },
  },
  {
    key: "gas",
    color: "#ff8787",
    ar: { name: "حساس تسرب الغاز", desc: "كشف مبكر في المطبخ مع إنذار وإشعار فوري." },
    en: { name: "Gas leak sensor", desc: "Early detection in the kitchen with an alarm and instant alert." },
  },
  {
    key: "health",
    color: "#63d3a6",
    ar: { name: "سيلترا هيلث", desc: "يقيس النوم وجودة الهواء والضوضاء من الغرفة نفسها." },
    en: { name: "Syltra Health", desc: "Measures sleep, air quality and noise from the room itself." },
  },
  {
    key: "audio",
    color: "#7ee08a",
    ar: { name: "أنظمة الصوت", desc: "سماعات سقف ومناطق صوت ومسرح منزلي." },
    en: { name: "Audio", desc: "Ceiling speakers, zones and home theatre." },
  },
];

const VILLA: PropertyDef = {
  kind: "villa",
  levels: 2,
  climate: "central",
  ar: { name: "فيلا", blurb: "دوران، مجلس وصالة، أربع غرف، حوش ومدخل." },
  en: { name: "Villa", blurb: "Two levels, a majlis and living room, four bedrooms, yard and entrance." },
  rooms: [
    { id: "majlis", centre: [-2.6, -2.2], size: [4.4, 3.6], level: 0, ar: "المجلس", en: "Majlis", window: "north", systems: ["lighting", "curtains", "climate", "audio", "motion"] },
    { id: "living", centre: [2.2, -2.2], size: [4.6, 3.6], level: 0, ar: "الصالة", en: "Living room", window: "north", systems: ["lighting", "curtains", "climate", "audio", "cameras", "motion"] },
    { id: "kitchen", centre: [-2.6, 1.8], size: [4.4, 3.2], level: 0, ar: "المطبخ", en: "Kitchen", systems: ["lighting", "climate", "gas", "motion"] },
    { id: "dining", centre: [2.2, 1.8], size: [4.6, 3.2], level: 0, ar: "غرفة الطعام", en: "Dining", window: "south", systems: ["lighting", "curtains", "climate"] },
    { id: "entrance", centre: [0, 4.6], size: [3.2, 2.2], level: 0, ar: "المدخل", en: "Entrance", systems: ["security", "cameras", "lighting", "motion"] },
    { id: "master", centre: [-2.6, -2.2], size: [4.4, 3.6], level: 1, ar: "غرفة النوم الرئيسية", en: "Master bedroom", window: "north", systems: ["lighting", "curtains", "climate", "audio", "health"] },
    { id: "bed2", centre: [2.2, -2.2], size: [4.6, 3.6], level: 1, ar: "غرفة نوم", en: "Bedroom", window: "north", systems: ["lighting", "curtains", "climate", "health"] },
    { id: "bed3", centre: [-2.6, 1.8], size: [4.4, 3.2], level: 1, ar: "غرفة نوم", en: "Bedroom", window: "south", systems: ["lighting", "curtains", "climate", "health"] },
    { id: "family", centre: [2.2, 1.8], size: [4.6, 3.2], level: 1, ar: "صالة عائلية", en: "Family lounge", window: "south", systems: ["lighting", "curtains", "climate", "audio", "motion"] },
  ],
};

const APARTMENT: PropertyDef = {
  kind: "apartment",
  levels: 1,
  climate: "split",
  ar: { name: "شقة", blurb: "دور واحد، صالة ومطبخ وغرفتان." },
  en: { name: "Apartment", blurb: "One level, a living room, kitchen and two bedrooms." },
  rooms: [
    { id: "living", centre: [-2.0, -1.6], size: [4.6, 3.4], level: 0, ar: "الصالة", en: "Living room", window: "north", systems: ["lighting", "curtains", "climate", "audio", "cameras", "motion"] },
    { id: "kitchen", centre: [2.4, -1.6], size: [3.6, 3.4], level: 0, ar: "المطبخ", en: "Kitchen", systems: ["lighting", "climate", "gas"] },
    { id: "master", centre: [-2.0, 2.2], size: [4.6, 3.4], level: 0, ar: "غرفة النوم", en: "Bedroom", window: "south", systems: ["lighting", "curtains", "climate", "health"] },
    { id: "bed2", centre: [2.4, 2.2], size: [3.6, 3.4], level: 0, ar: "غرفة ثانية", en: "Second bedroom", window: "south", systems: ["lighting", "curtains", "climate"] },
    { id: "entrance", centre: [0.2, 5.0], size: [2.6, 1.8], level: 0, ar: "المدخل", en: "Entrance", systems: ["security", "cameras", "motion"] },
  ],
};

const OFFICE: PropertyDef = {
  kind: "office",
  levels: 1,
  climate: "split",
  ar: { name: "مكتب", blurb: "استقبال، مساحة عمل، غرفة اجتماعات ومكتب المدير." },
  en: { name: "Office", blurb: "Reception, open workspace, a meeting room and the director's office." },
  rooms: [
    { id: "reception", centre: [0, 4.4], size: [4.2, 2.6], level: 0, ar: "الاستقبال", en: "Reception", systems: ["security", "cameras", "lighting", "climate", "motion"] },
    { id: "open", centre: [-2.2, -0.4], size: [4.8, 5.2], level: 0, ar: "مساحة العمل", en: "Workspace", window: "north", systems: ["lighting", "climate", "curtains", "cameras", "motion"] },
    { id: "meeting", centre: [2.6, 1.2], size: [3.8, 3.0], level: 0, ar: "غرفة الاجتماعات", en: "Meeting room", window: "south", systems: ["lighting", "climate", "audio", "curtains", "motion"] },
    { id: "director", centre: [2.6, -2.6], size: [3.8, 3.0], level: 0, ar: "مكتب المدير", en: "Director's office", window: "north", systems: ["lighting", "climate", "curtains", "security"] },
  ],
};

export const PROPERTIES: Record<PropertyKind, PropertyDef> = {
  villa: VILLA,
  apartment: APARTMENT,
  office: OFFICE,
};

export function propertyCopy(def: PropertyDef, locale: Locale) {
  return locale === "ar" ? def.ar : def.en;
}

export function roomName(room: RoomDef, locale: Locale) {
  return locale === "ar" ? room.ar : room.en;
}

export function systemCopy(key: SystemKey, locale: Locale) {
  const s = SYSTEMS.find((x) => x.key === key)!;
  return locale === "ar" ? s.ar : s.en;
}
