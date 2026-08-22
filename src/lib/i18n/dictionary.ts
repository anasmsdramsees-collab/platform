export interface Dictionary {
  meta: {
    titleHome: string;
    titleProducts: string;
    titleAbout: string;
    titleContact: string;
    titleApps: string;
    titleFaq: string;
    titleSyntraTv: string;
    titleHomeAssistant: string;
    description: string;
  };
  common: {
    comingLabel: string;
    platformsLabel: string;
    specsLabel: string;
    appsLabel: string;
    howItWorksLabel: string;
    notifyTitle: string;
    notifySubtitle: string;
    notifyButton: string;
    backToApps: string;
    openAppButton: string;
    livePreviewLabel: string;
    livePreviewNote: string;
  };
  nav: {
    products: string;
    store: string;
    solutions: string;
    services: string;
    apps: string;
    about: string;
    faq: string;
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
  testimonials: {
    eyebrow: string;
    title: string;
    subtitle: string;
    items: { quote: string; name: string; role: string; logo?: string }[];
  };
  homeCta: {
    title: string;
    subtitle: string;
    button: string;
  };
  footer: {
    tagline: string;
    products: string;
    apps: string;
    company: string;
    contact: string;
    rights: string;
  };
  productsPage: {
    eyebrow: string;
    title: string;
    subtitle: string;
  };
  appsPage: {
    eyebrow: string;
    title: string;
    subtitle: string;
    cards: {
      slug: "syntra-tv" | "home-assistant";
      name: string;
      tagline: string;
      desc: string;
      status: string;
    }[];
  };
  syntraTvPage: {
    hero: { eyebrow: string; title: string; subtitle: string };
    platforms: string[];
    specs: string[];
    apps: string[];
    features: { name: string; desc: string }[];
    howItWorks: { step: string; title: string; desc: string }[];
    screen: { eyebrow: string; title: string; items: { name: string; desc: string }[] };
    status: string;
  };
  homeAssistantPage: {
    hero: { eyebrow: string; title: string; subtitle: string };
    platforms: string[];
    features: { name: string; desc: string }[];
    openSection: {
      eyebrow: string;
      title: string;
      paragraphs: string[];
      items: { name: string; desc: string }[];
    };
    howItWorks: { step: string; title: string; desc: string }[];
    status: string;
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
  solutionsPage: {
    eyebrow: string;
    title: string;
    subtitle: string;
    divisions: {
      code: string;
      name: string;
      desc: string;
      points: { name: string; desc: string }[];
    }[];
    healthNote: string;
    sectors: {
      eyebrow: string;
      title: string;
      note: string;
      columns: { sector: string; need: string; units: string };
      rows: { sector: string; need: string; units: string }[];
    };
    trust: {
      eyebrow: string;
      title: string;
      items: { name: string; desc: string }[];
      principles: string[];
      principlesLabel: string;
      note: string;
    };
  };
  servicesPage: {
    eyebrow: string;
    title: string;
    subtitle: string;
    items: { name: string; desc: string }[];
    field: {
      eyebrow: string;
      title: string;
      subtitle: string;
      items: { name: string; desc: string }[];
    };
    delivery: {
      eyebrow: string;
      title: string;
      subtitle: string;
      stages: { code: string; desc: string }[];
      commitments: { name: string; desc: string }[];
    };
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
  faqPage: {
    eyebrow: string;
    title: string;
    subtitle: string;
    items: { q: string; a: string }[];
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
    curtainsOverlayOpen: string;
  };
}
