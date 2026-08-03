import type { Locale } from "./config";
import type { Dictionary } from "./dictionary";
import en from "./en";
import ar from "./ar";

const dictionaries: Record<Locale, Dictionary> = { en, ar };

export function getDictionary(locale: Locale): Dictionary {
  return dictionaries[locale];
}
