import type { Locale } from "@/lib/i18n/config";

export type PropertyKind = "villa" | "office" | "apartment";
export type SystemKey = "lighting" | "curtains" | "climate" | "security" | "cameras" | "audio";

export interface RoomDef {
  id: string;
  /** Footprint in metres: [x, z] centre and [w, d] size on the floor grid. */
  centre: [number, number];
  size: [number, number];
  /** Which floor level the room sits on. */
  level: number;
  ar: string;
  en: string;
  /** Systems that make sense in this room, used to price and to place markers. */
  systems: SystemKey[];
}

export interface PropertyDef {
  kind: PropertyKind;
  levels: number;
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
    key: "audio",
    color: "#7ee08a",
    ar: { name: "أنظمة الصوت", desc: "سماعات سقف ومناطق صوت ومسرح منزلي." },
    en: { name: "Audio", desc: "Ceiling speakers, zones and home theatre." },
  },
];

const VILLA: PropertyDef = {
  kind: "villa",
  levels: 2,
  ar: { name: "فيلا", blurb: "دوران، مجلس وصالة، أربع غرف، حوش ومدخل." },
  en: { name: "Villa", blurb: "Two levels, a majlis and living room, four bedrooms, yard and entrance." },
  rooms: [
    { id: "majlis", centre: [-2.6, -2.2], size: [4.4, 3.6], level: 0, ar: "المجلس", en: "Majlis", systems: ["lighting", "curtains", "climate", "audio"] },
    { id: "living", centre: [2.2, -2.2], size: [4.6, 3.6], level: 0, ar: "الصالة", en: "Living room", systems: ["lighting", "curtains", "climate", "audio", "cameras"] },
    { id: "kitchen", centre: [-2.6, 1.8], size: [4.4, 3.2], level: 0, ar: "المطبخ", en: "Kitchen", systems: ["lighting", "climate", "security"] },
    { id: "dining", centre: [2.2, 1.8], size: [4.6, 3.2], level: 0, ar: "غرفة الطعام", en: "Dining", systems: ["lighting", "curtains", "climate"] },
    { id: "entrance", centre: [0, 4.6], size: [3.2, 2.2], level: 0, ar: "المدخل", en: "Entrance", systems: ["security", "cameras", "lighting"] },
    { id: "master", centre: [-2.6, -2.2], size: [4.4, 3.6], level: 1, ar: "غرفة النوم الرئيسية", en: "Master bedroom", systems: ["lighting", "curtains", "climate", "audio"] },
    { id: "bed2", centre: [2.2, -2.2], size: [4.6, 3.6], level: 1, ar: "غرفة نوم", en: "Bedroom", systems: ["lighting", "curtains", "climate"] },
    { id: "bed3", centre: [-2.6, 1.8], size: [4.4, 3.2], level: 1, ar: "غرفة نوم", en: "Bedroom", systems: ["lighting", "curtains", "climate"] },
    { id: "family", centre: [2.2, 1.8], size: [4.6, 3.2], level: 1, ar: "صالة عائلية", en: "Family lounge", systems: ["lighting", "curtains", "climate", "audio"] },
  ],
};

const APARTMENT: PropertyDef = {
  kind: "apartment",
  levels: 1,
  ar: { name: "شقة", blurb: "دور واحد، صالة ومطبخ وغرفتان." },
  en: { name: "Apartment", blurb: "One level, a living room, kitchen and two bedrooms." },
  rooms: [
    { id: "living", centre: [-2.0, -1.6], size: [4.6, 3.4], level: 0, ar: "الصالة", en: "Living room", systems: ["lighting", "curtains", "climate", "audio", "cameras"] },
    { id: "kitchen", centre: [2.4, -1.6], size: [3.6, 3.4], level: 0, ar: "المطبخ", en: "Kitchen", systems: ["lighting", "climate", "security"] },
    { id: "master", centre: [-2.0, 2.2], size: [4.6, 3.4], level: 0, ar: "غرفة النوم", en: "Bedroom", systems: ["lighting", "curtains", "climate"] },
    { id: "bed2", centre: [2.4, 2.2], size: [3.6, 3.4], level: 0, ar: "غرفة ثانية", en: "Second bedroom", systems: ["lighting", "curtains", "climate"] },
    { id: "entrance", centre: [0.2, 5.0], size: [2.6, 1.8], level: 0, ar: "المدخل", en: "Entrance", systems: ["security", "cameras"] },
  ],
};

const OFFICE: PropertyDef = {
  kind: "office",
  levels: 1,
  ar: { name: "مكتب", blurb: "استقبال، مساحة عمل، غرفة اجتماعات ومكتب المدير." },
  en: { name: "Office", blurb: "Reception, open workspace, a meeting room and the director's office." },
  rooms: [
    { id: "reception", centre: [0, 4.4], size: [4.2, 2.6], level: 0, ar: "الاستقبال", en: "Reception", systems: ["security", "cameras", "lighting", "climate"] },
    { id: "open", centre: [-2.2, -0.4], size: [4.8, 5.2], level: 0, ar: "مساحة العمل", en: "Workspace", systems: ["lighting", "climate", "curtains", "cameras"] },
    { id: "meeting", centre: [2.6, 1.2], size: [3.8, 3.0], level: 0, ar: "غرفة الاجتماعات", en: "Meeting room", systems: ["lighting", "climate", "audio", "curtains"] },
    { id: "director", centre: [2.6, -2.6], size: [3.8, 3.0], level: 0, ar: "مكتب المدير", en: "Director's office", systems: ["lighting", "climate", "curtains", "security"] },
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
