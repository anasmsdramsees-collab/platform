import type { Locale } from "@/lib/i18n/config";

export interface Landing {
  slug: string;
  /** Search intent this page answers, one locale each. */
  ar: LandingCopy;
  en: LandingCopy;
  /** Product slugs to surface, in order. */
  products: string[];
}

interface LandingCopy {
  title: string;
  h1: string;
  description: string;
  intro: string;
  benefits: { name: string; desc: string }[];
  faq: { q: string; a: string }[];
}

export const landings: Landing[] = [
  {
    slug: "smart-home-riyadh",
    products: ["hub-pro", "panel-11", "t3", "dim", "curtain", "thermostat"],
    ar: {
      title: "منزل ذكي في الرياض | تركيب وبرمجة | سيلترا وان",
      h1: "منزل ذكي في الرياض، من التصميم إلى التشغيل.",
      description:
        "شركة سعودية تصمم وتركّب أنظمة المنزل الذكي في الرياض: إضاءة وستائر وتكييف وأمان، بتحكم عربي بالكامل ومعاينة مجانية قبل أي التزام.",
      intro:
        "سيلترا وان شركة تقنية مقرها الرياض تصمم وتركّب أنظمة المنزل الذكي للشقق والفلل والمجمعات. نعاين الموقع، ونصمم المنظومة على مقاس المكان، ثم نركّب ونبرمج ونسلّم البيت وهو يعمل. كل شيء يُدار من تطبيق واحد أو بصوتك بالعربية عبر مساعدتنا سيلا.",
      benefits: [
        { name: "فريق سعودي في الرياض", desc: "معاينة على الموقع وتركيب وصيانة من فريق محلي، لا وكيل ولا وسيط." },
        { name: "تحكم عربي بالكامل", desc: "التطبيق والشاشات والمساعد الصوتي كلها بالعربية، يستخدمها كل أفراد البيت من أول يوم." },
        { name: "يعمل بدون إنترنت", desc: "الأتمتة الأساسية تعمل محليًا داخل البيت، فتبقى الإضاءة والمشاهد شغالة لو انقطع الإنترنت." },
        { name: "بدون تكسير", desc: "وحدات مخفية خلف المفاتيح الحالية تحوّل الإضاءة الموجودة إلى ذكية دون تغيير التمديدات." },
      ],
      faq: [
        { q: "كم تكلفة تحويل المنزل إلى ذكي في الرياض؟", a: "تعتمد التكلفة على عدد الغرف ونقاط الإضاءة والأنظمة المطلوبة. نبدأ بمعاينة مجانية ثم نرسل عرض سعر مفصّلًا بكل بند: الأجهزة والتركيب والبرمجة والضمان." },
        { q: "هل يمكن تركيب النظام في بيت جاهز ومسكون؟", a: "نعم. وحدات سيلترا المخفية تُركّب خلف المفاتيح الحالية دون تكسير أو إعادة تمديد، ويبقى المفتاح يعمل يدويًا كما هو." },
        { q: "كم يستغرق التركيب؟", a: "الشقة تُنجز غالبًا خلال يوم إلى يومين، والفيلا الكاملة تحتاج عادة من ثلاثة إلى سبعة أيام حسب حجم المشروع." },
        { q: "هل النظام يعمل بالعربية؟", a: "نعم، التطبيق والشاشات والمساعد الصوتي سيلا كلها عربية أولًا مع دعم كامل للإنجليزية." },
      ],
    },
    en: {
      title: "Smart Home in Riyadh | Design and Installation | Syltra One",
      h1: "A smart home in Riyadh, from design to operation.",
      description:
        "A Saudi company designing and installing smart home systems in Riyadh: lighting, curtains, climate and security, fully Arabic, with a free site survey before any commitment.",
      intro:
        "Syltra One is a Riyadh-based technology company that designs and installs smart home systems for apartments, villas and compounds. We survey the site, design the system around the space, then install, program and hand the home over working. Everything runs from one app or by voice in Arabic through our assistant, Syla.",
      benefits: [
        { name: "A local team in Riyadh", desc: "Survey, installation and maintenance from a Saudi team, with no agent and no middleman." },
        { name: "Arabic throughout", desc: "The app, the wall panels and the voice assistant are all Arabic, so the whole household uses them from day one." },
        { name: "Works without internet", desc: "Core automations run locally inside the house, so lights and scenes keep working when the connection drops." },
        { name: "No rewiring", desc: "Hidden modules sit behind your existing switches and make the current lighting smart without changing the wiring." },
      ],
      faq: [
        { q: "What does a smart home cost in Riyadh?", a: "The cost depends on the number of rooms, lighting points and systems involved. We start with a free site survey, then send an itemised quote covering devices, installation, programming and warranty." },
        { q: "Can it be installed in a finished, occupied home?", a: "Yes. Syltra's hidden modules fit behind your existing switches with no demolition and no rewiring, and the switch keeps working manually as before." },
        { q: "How long does installation take?", a: "An apartment is usually finished in one to two days; a full villa typically takes three to seven days depending on the scope." },
        { q: "Does the system work in Arabic?", a: "Yes. The app, the panels and the Syla voice assistant are Arabic-first, with full English support." },
      ],
    },
  },
  {
    slug: "solar-cctv",
    products: ["cctv-solar", "cctv-solar-4g", "cctv-solar-ptz", "cctv-nvr"],
    ar: {
      title: "كاميرات مراقبة بالطاقة الشمسية | بدون كهرباء أو إنترنت | سيلترا وان",
      h1: "كاميرات مراقبة بالطاقة الشمسية، بلا كهرباء ولا تمديدات.",
      description:
        "كاميرات مراقبة تعمل بالطاقة الشمسية للمزارع والاستراحات والمواقع البعيدة، بعضها بشريحة 4G يعمل بدون إنترنت، مع تركيب في الرياض.",
      intro:
        "الكاميرات الشمسية من سيلترا تحل أصعب مشكلة في المراقبة الخارجية: المكان الذي لا تصله كهرباء ولا شبكة. لوح شمسي وبطارية مدمجة يشغّلان الكاميرا طوال العام، وشريحة 4G تنقل البث مباشرة إلى جوالك من المزرعة أو الموقع أو الأرض البعيدة.",
      benefits: [
        { name: "بلا تمديد كهرباء", desc: "لوح شمسي وبطارية مدمجة يكفيان لتشغيل الكاميرا، فلا تحتاج كهربائيًا ولا حفر تمديدات." },
        { name: "تعمل بدون إنترنت", desc: "نسخة الـ 4G تستخدم شريحة اتصال، فتبث من أي مكان تصله شبكة الجوال." },
        { name: "رؤية ليلية ملونة", desc: "دقة 4K مع رؤية ليلية واضحة وكشف حركة يرسل تنبيهًا فوريًا على جوالك." },
        { name: "مقاومة للجو", desc: "هيكل IP66 مصمم لحرارة الصيف والغبار والأمطار الموسمية." },
      ],
      faq: [
        { q: "هل تعمل الكاميرا الشمسية في الشتاء وأيام الغيوم؟", a: "نعم. البطارية المدمجة تخزّن شحن الأيام المشمسة وتكفي لعدة أيام غائمة متتالية، ويظل اللوح يشحن حتى في الضوء غير المباشر." },
        { q: "هل أحتاج إنترنت في المكان؟", a: "لا إذا اخترت نسخة 4G، فهي تعمل بشريحة اتصال. النسخة العادية تحتاج شبكة واي فاي في نطاقها." },
        { q: "أين تُحفظ التسجيلات؟", a: "على بطاقة ذاكرة داخل الكاميرا، أو على جهاز تسجيل محلي، أو على السحابة. الخيار لك ويبقى التسجيل ملكك." },
        { q: "هل يمكن تركيبها في مزرعة بعيدة؟", a: "نعم، هذا استخدامها الأمثل. المزارع والاستراحات والمواقع تحت الإنشاء والأراضي البيضاء كلها تُغطى بكاميرا شمسية 4G." },
      ],
    },
    en: {
      title: "Solar CCTV Cameras | No Power, No Internet | Syltra One",
      h1: "Solar-powered CCTV, with no wiring and no bills.",
      description:
        "Solar surveillance cameras for farms, rest houses and remote sites, including 4G models that work with no internet, installed in Riyadh.",
      intro:
        "Syltra's solar cameras solve the hardest problem in outdoor surveillance: a location with neither power nor a network. A solar panel and built-in battery run the camera all year, and a 4G SIM streams straight to your phone from a farm, a site or a distant plot of land.",
      benefits: [
        { name: "No electrical work", desc: "A solar panel and built-in battery run the camera, so there is no electrician and no trenching." },
        { name: "Works without internet", desc: "The 4G model uses a SIM, so it streams from anywhere with mobile coverage." },
        { name: "Colour night vision", desc: "4K detail with clear night vision and motion detection that alerts your phone instantly." },
        { name: "Built for the weather", desc: "An IP66 body designed for summer heat, dust and seasonal rain." },
      ],
      faq: [
        { q: "Do solar cameras work in winter and on cloudy days?", a: "Yes. The built-in battery stores charge from sunny days and covers several overcast days in a row, and the panel keeps charging in indirect light." },
        { q: "Do I need internet at the location?", a: "Not with the 4G model, which runs on a SIM. The standard model needs Wi-Fi within range." },
        { q: "Where is the footage stored?", a: "On a memory card in the camera, on a local recorder, or in the cloud. You choose, and the recordings stay yours." },
        { q: "Can it be installed on a remote farm?", a: "Yes, that is exactly what it is for. Farms, rest houses, construction sites and empty land are all covered by a 4G solar camera." },
      ],
    },
  },
  {
    slug: "smart-locks",
    products: ["lock-elite", "lock-pro", "lock", "lock-bolt", "doorbell"],
    ar: {
      title: "أقفال ذكية للأبواب | بصمة ورمز وجوال | سيلترا وان",
      h1: "أقفال ذكية تفتح ببصمتك، بلا مفاتيح.",
      description:
        "أقفال أبواب ذكية تعمل بالبصمة والرمز والبطاقة والجوال، مع رموز مؤقتة للضيوف والعمالة وسجل دخول كامل، وتركيب في الرياض.",
      intro:
        "قفل سيلترا الذكي يلغي المفتاح من حياتك اليومية. تفتح الباب ببصمتك أو برمز أو من جوالك، وتمنح الضيوف والسائق والعاملة رموزًا مؤقتة تنتهي وحدها، وتعرف من دخل ومتى من سجل كامل في التطبيق.",
      benefits: [
        { name: "خمس طرق للفتح", desc: "بصمة، رمز رقمي، بطاقة NFC، تطبيق الجوال، ومفتاح احتياطي للطوارئ." },
        { name: "رموز مؤقتة", desc: "امنح الضيف أو العاملة رمزًا يعمل في أوقات محددة وينتهي وحده، دون تسليم مفتاح." },
        { name: "سجل دخول كامل", desc: "تعرف من فتح الباب ومتى، مع تنبيه فوري عند أي محاولة فتح فاشلة." },
        { name: "بطارية تدوم شهورًا", desc: "شحنة تكفي عدة أشهر، مع تنبيه قبل النفاد ومنفذ USB-C للطاقة عند الطوارئ." },
      ],
      faq: [
        { q: "ماذا لو نفدت البطارية والباب مغلق؟", a: "القفل ينبهك في التطبيق قبل النفاد بأسابيع. وعند الطوارئ يمكن تشغيله من بطارية خارجية عبر منفذ USB-C، ويبقى المفتاح الاحتياطي متاحًا دائمًا." },
        { q: "هل يناسب بابي الحالي؟", a: "غالبًا نعم. نعاين الباب وسماكته ونوع القفل قبل الطلب ونحدد الموديل المناسب، والمعاينة مجانية." },
        { q: "هل يمكن فتح الباب وأنا خارج المنزل؟", a: "نعم، من التطبيق عن بُعد. وإذا كان لديك جرس سيلترا بالكاميرا، ترى الزائر وتكلمه ثم تفتح له." },
        { q: "هل بيانات البصمة آمنة؟", a: "البصمة تُخزّن مشفّرة داخل القفل نفسه ولا تُرفع إلى أي خادم." },
      ],
    },
    en: {
      title: "Smart Door Locks | Fingerprint, Code and Phone | Syltra One",
      h1: "Smart locks that open with your fingerprint, no keys.",
      description:
        "Smart door locks with fingerprint, code, card and phone access, temporary guest and staff codes, a full entry log, and installation in Riyadh.",
      intro:
        "A Syltra smart lock takes the key out of your daily life. Open the door with your fingerprint, a code or your phone, hand guests, the driver and the housekeeper temporary codes that expire on their own, and see who came in and when from a full log in the app.",
      benefits: [
        { name: "Five ways in", desc: "Fingerprint, numeric code, NFC card, the mobile app, and a spare key for emergencies." },
        { name: "Temporary codes", desc: "Give a guest or a helper a code that works only at set times and expires by itself, with no key handed over." },
        { name: "A complete entry log", desc: "Know who opened the door and when, with an instant alert on any failed attempt." },
        { name: "Months on a charge", desc: "One charge lasts months, with a low-battery warning ahead of time and a USB-C port for emergency power." },
      ],
      faq: [
        { q: "What if the battery dies while the door is locked?", a: "The lock warns you in the app weeks in advance. In an emergency it can be powered from a power bank through the USB-C port, and the spare key is always available." },
        { q: "Will it fit my existing door?", a: "Usually yes. We check the door, its thickness and the current lock before ordering and pick the right model. The survey is free." },
        { q: "Can I open the door while I'm away?", a: "Yes, remotely from the app. With a Syltra video doorbell you can also see the visitor, speak to them, then let them in." },
        { q: "Is my fingerprint data safe?", a: "The fingerprint is stored encrypted inside the lock itself and is never uploaded to any server." },
      ],
    },
  },
];

export function findLanding(slug: string) {
  return landings.find((l) => l.slug === slug);
}

export function landingCopy(landing: Landing, locale: Locale) {
  return locale === "ar" ? landing.ar : landing.en;
}
