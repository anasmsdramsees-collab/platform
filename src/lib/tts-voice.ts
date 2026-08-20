// Pick a female-sounding voice for Syla's spoken replies.
// Browsers expose different voice sets per OS, so we match against known
// female voice names first, then fall back to any voice for the language.

const FEMALE_HINTS = [
  "female",
  "أنثى",
  // Arabic voices
  "hoda", // Microsoft ar-EG
  "salma",
  "zariyah", // Microsoft Edge ar-SA neural
  "amina",
  "laila",
  "layla",
  "mariam",
  "fatima",
  // English voices
  "samantha",
  "victoria",
  "karen",
  "moira",
  "tessa",
  "fiona",
  "susan",
  "zira", // Microsoft
  "jenny",
  "aria",
  "ava",
  "allison",
  "serena",
  "kate",
];

const MALE_HINTS = ["male", "majed", "naayf", "hamed", "daniel", "alex", "fred", "david", "mark", "guy", "tarik"];

export function pickFemaleVoice(lang: string): SpeechSynthesisVoice | null {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return null;
  const voices = window.speechSynthesis.getVoices();
  if (!voices.length) return null;

  const base = lang.split("-")[0].toLowerCase();
  const forLang = voices.filter((v) => v.lang.toLowerCase().startsWith(base));
  const pool = forLang.length ? forLang : voices;

  const isFemale = (v: SpeechSynthesisVoice) =>
    FEMALE_HINTS.some((h) => v.name.toLowerCase().includes(h));
  const isMale = (v: SpeechSynthesisVoice) =>
    MALE_HINTS.some((h) => v.name.toLowerCase().includes(h));

  return (
    pool.find(isFemale) ??
    pool.find((v) => !isMale(v)) ??
    pool[0] ??
    null
  );
}

// Configure an utterance to sound like Syla: female voice when available,
// otherwise nudge pitch up so a default male voice reads softer.
export function applySylaVoice(u: SpeechSynthesisUtterance, lang: string) {
  u.lang = lang;
  const voice = pickFemaleVoice(lang);
  if (voice) {
    u.voice = voice;
    u.pitch = 1;
  } else {
    u.pitch = 1.15;
  }
}
