export interface Dictionary {
  meta: {
    titleHome: string;
    titleProducts: string;
    titleAbout: string;
    titleContact: string;
    description: string;
  };
  nav: {
    products: string;
    about: string;
    contact: string;
  };
  hero: {
    eyebrow: string;
    title: string;
    subtitle: string;
    ctaProducts: string;
    ctaAbout: string;
  };
  stats: { value: string; label: string }[];
  ecosystem: {
    eyebrow: string;
    title: string;
    subtitle: string;
    pillars: { name: string; desc: string }[];
  };
  why: {
    eyebrow: string;
    title: string;
    items: { name: string; desc: string }[];
  };
  categories: {
    eyebrow: string;
    title: string;
    subtitle: string;
    cta: string;
  };
  protocols: {
    eyebrow: string;
    title: string;
    subtitle: string;
    items: { name: string; desc: string }[];
  };
  homeCta: {
    title: string;
    subtitle: string;
    button: string;
  };
  footer: {
    tagline: string;
    products: string;
    company: string;
    contact: string;
    rights: string;
  };
  productsPage: {
    eyebrow: string;
    title: string;
    subtitle: string;
  };
  aboutPage: {
    hero: { eyebrow: string; title: string; subtitle: string };
    story: { eyebrow: string; title: string; paragraphs: string[] };
    mission: { label: string; text: string };
    vision: { label: string; text: string };
    values: { eyebrow: string; title: string; items: { name: string; desc: string }[] };
    chairman: { eyebrow: string; quote: string; name: string; role: string };
    facts: { value: string; label: string }[];
    roadmap: { eyebrow: string; title: string; items: { year: string; text: string }[] };
  };
  contactPage: {
    eyebrow: string;
    title: string;
    subtitle: string;
    hqLabel: string;
    hqValue: string;
    emailLabel: string;
    webLabel: string;
    corporateLabel: string;
    corporateValue: string;
  };
  sina: {
    launcherLabel: string;
    title: string;
    subtitle: string;
    greeting: string;
    placeholder: string;
    send: string;
    thinking: string;
    disclaimer: string;
    unavailable: string;
    error: string;
    close: string;
    mic: string;
    listening: string;
    voiceReplies: string;
  };
  energyReminder: {
    message: string;
    dismiss: string;
  };
  lightsPanel: {
    label: string;
    room: string;
    on: string;
    off: string;
    hint: string;
    voiceHint: string;
    offMessage: string;
    tapToTurnOn: string;
    tileLighting: string;
    tileClimate: string;
    tileCurtains: string;
    curtainsOpen: string;
    curtainsClosed: string;
    curtainsOverlayMessage: string;
    curtainsOverlayHint: string;
  };
}
