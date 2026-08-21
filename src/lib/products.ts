export type ProductTag =
  | "Matter"
  | "Zigbee"
  | "Z-Wave"
  | "Wi-Fi"
  | "BLE"
  | "Thread"
  | "NFC"
  | "App";

export interface Spec {
  label: string;
  value: string;
}

export interface ProductCopy {
  tagline: string;
  description: string;
  specs: Spec[];
}

export interface Product {
  slug: string;
  name: string; // kept in Latin across both locales, matching real hardware silkscreen/packaging
  en: ProductCopy;
  ar: ProductCopy;
  tags: ProductTag[];
  images?: string[]; // slide gallery, first image is the cover
}

export interface ProductCategory {
  key: string;
  en: { name: string; desc: string };
  ar: { name: string; desc: string };
  items: Product[];
}

export const productCatalog: ProductCategory[] = [
  {
    key: "hubs",
    en: {
      name: "Hubs & Panels",
      desc: "The brain of the system, and the glass you touch to run it.",
    },
    ar: {
      name: "المراكز وشاشات التحكم",
      desc: "العقل الذي يدير المنزل، والزجاج الذي تلمسه للتحكم فيه.",
    },
    items: [
      {
        slug: "hub-mini",
        images: ["/store/hub-mini.jpg", "/store/hub-mini-2.jpg", "/store/hub-mini-poster.jpg"],
        name: "Syltra Hub Mini",
        tags: ["Wi-Fi", "Zigbee", "Z-Wave"],
        en: {
          tagline: "The whole apartment, from one small box.",
          description: "Hub Mini runs an apartment or single-floor home from one quiet box behind the TV. Plug it in, add your devices, and every light, curtain and sensor answers to one app. It handles up to 100 devices without slowing down.",
          specs: [
            { label: "Processor", value: "Quad-core, 1.2GHz" },
            { label: "Capacity", value: "Up to 100 devices" },
            { label: "Connectivity", value: "Wi-Fi 2.4GHz" },
            { label: "Power", value: "5V / 2A, USB-C" },
          ],
        },
        ar: {
          tagline: "الشقة كلها من صندوق صغير واحد.",
          description: "يدير Hub Mini شقة كاملة أو منزلًا من طابق واحد من صندوق هادئ خلف التلفاز. وصّله وأضف أجهزتك، وستجد كل إضاءة وستارة وحساس يستجيب من تطبيق واحد. يستوعب حتى 100 جهاز دون أن يتباطأ.",
          specs: [
            { label: "المعالج", value: "رباعي النواة، 1.2GHz" },
            { label: "السعة", value: "حتى 100 جهاز" },
            { label: "الاتصال", value: "Wi-Fi 2.4GHz" },
            { label: "الطاقة", value: "5V / 2A، USB-C" },
          ],
        },
      },
      {
        slug: "hub-pro",
        images: ["/store/hub-pro.jpg", "/store/hub-pro-2.jpg", "/store/hub-pro-poster.jpg"],
        name: "Syltra Hub Pro",
        tags: ["Wi-Fi", "Zigbee", "Z-Wave", "Thread"],
        en: {
          tagline: "Full-villa coverage with a local brain.",
          description: "Hub Pro is built for the full villa. Longer radio range, faster processing, and automations that run locally, so the house keeps working even when the internet does not. Up to 300 devices across every floor.",
          specs: [
            { label: "Processor", value: "Quad-core, 1.5GHz" },
            { label: "Memory", value: "1GB RAM / 8GB eMMC" },
            { label: "Capacity", value: "Up to 300 devices" },
            { label: "Connectivity", value: "Wi-Fi 2.4/5GHz, Bluetooth 5.0" },
            { label: "Z-Wave range", value: "Up to 150m, line of sight" },
            { label: "Ethernet", value: "10/100/1000 Mbps" },
            { label: "Dimensions", value: "110 × 110 × 28 mm" },
          ],
        },
        ar: {
          tagline: "تغطية كاملة للفيلا بعقل محلي.",
          description: "صُمم Hub Pro للفلل الكبيرة. مدى لاسلكي أطول ومعالجة أسرع وأتمتة تعمل محليًا، فيبقى المنزل شغالًا حتى لو انقطع الإنترنت. يدير حتى 300 جهاز في كل الطوابق.",
          specs: [
            { label: "المعالج", value: "رباعي النواة، 1.5GHz" },
            { label: "الذاكرة", value: "1GB RAM / 8GB eMMC" },
            { label: "السعة", value: "حتى 300 جهاز" },
            { label: "الاتصال", value: "Wi-Fi 2.4/5GHz، بلوتوث 5.0" },
            { label: "مدى Z-Wave", value: "حتى 150 مترًا، خط رؤية مباشر" },
            { label: "منفذ الشبكة", value: "10/100/1000 ميجابت" },
            { label: "الأبعاد", value: "110 × 110 × 28 مم" },
          ],
        },
      },
      {
        slug: "hub-max",
        images: ["/store/hub-max.jpg", "/store/hub-max-2.jpg", "/store/hub-max-poster.jpg"],
        name: "Syltra Hub Max",
        tags: ["Wi-Fi", "Zigbee", "Z-Wave", "Thread"],
        en: {
          tagline: "One system for an entire property.",
          description: "Hub Max coordinates estates, hotels and commercial buildings from a single screen. More than a thousand devices across several buildings, managed as one system with the same simplicity as a single room.",
          specs: [
            { label: "Processor", value: "Quad-core, 1.8GHz" },
            { label: "Capacity", value: "1,000+ devices" },
            { label: "Connectivity", value: "Wi-Fi 2.4/5GHz" },
            { label: "Network", value: "LAN 10/100/1000" },
          ],
        },
        ar: {
          tagline: "نظام واحد لمنشأة كاملة.",
          description: "ينسق Hub Max القصور والفنادق والمباني التجارية من شاشة واحدة. أكثر من ألف جهاز موزعة على عدة مبانٍ تُدار كنظام واحد بنفس بساطة إدارة غرفة واحدة.",
          specs: [
            { label: "المعالج", value: "رباعي النواة، 1.8GHz" },
            { label: "السعة", value: "أكثر من 1000 جهاز" },
            { label: "الاتصال", value: "Wi-Fi 2.4/5GHz" },
            { label: "الشبكة", value: "LAN 10/100/1000" },
          ],
        },
      },
      {
        slug: "panel-3",
        images: ["/store/panel-3.jpg", "/store/panel-3-2.jpg", "/store/panel-3-poster.jpg"],
        name: "Syltra Touch Panel 3″",
        tags: ["Wi-Fi", "Zigbee"],
        en: {
          tagline: "One room at your fingertips.",
          description: "A compact wall panel at the room door. Lights, temperature and curtains on a bright touch screen, in the same glass and aluminum finish as the rest of the line.",
          specs: [
            { label: "Screen", value: "3″ touch display" },
            { label: "Connectivity", value: "Wi-Fi 2.4GHz, Zigbee 3.0 (optional)" },
            { label: "Input", value: "Multi-touch" },
            { label: "Mounting", value: "Wall-mount, in-wall backbox" },
          ],
        },
        ar: {
          tagline: "الغرفة كلها بلمسة عند الباب.",
          description: "شاشة حائط صغيرة عند مدخل الغرفة. الإضاءة والحرارة والستائر على شاشة لمس واضحة، بنفس تشطيب الزجاج والألمنيوم لبقية المنظومة.",
          specs: [
            { label: "الشاشة", value: "شاشة لمس 3 إنش" },
            { label: "الاتصال", value: "Wi-Fi 2.4GHz، Zigbee 3.0 (اختياري)" },
            { label: "الإدخال", value: "لمس متعدد النقاط" },
            { label: "التركيب", value: "تثبيت على الحائط" },
          ],
        },
      },
      {
        slug: "panel-11",
        images: ["/store/panel-11.jpg", "/store/panel-11-2.jpg", "/store/panel-11-poster.jpg"],
        name: "Syltra Touch Panel 11″",
        tags: ["Wi-Fi", "Zigbee", "Matter"],
        en: {
          tagline: "The whole home on one bright screen.",
          description: "An 11-inch dashboard built into the wall. Every room, camera and scene in sharp 1920x1200 resolution. A real control center the household gathers around, not a tablet taped to the wall.",
          specs: [
            { label: "Screen", value: "11″ IPS touch, 1920 × 1200 (FHD+)" },
            { label: "Processor", value: "Quad-core, 1.8GHz" },
            { label: "Memory", value: "2GB RAM / 16GB storage" },
            { label: "Connectivity", value: "Wi-Fi 2.4/5GHz, Bluetooth 5.0" },
            { label: "Power", value: "12V / 2A, USB-C" },
            { label: "Dimensions", value: "264 × 166 × 11 mm" },
          ],
        },
        ar: {
          tagline: "المنزل كله على شاشة واحدة.",
          description: "لوحة تحكم 11 إنش مدمجة في الحائط. كل غرفة وكاميرا ومشهد بدقة 1920×1200. مركز تحكم حقيقي يلتف حوله أهل البيت، لا جهاز لوحي مثبت بشريط لاصق.",
          specs: [
            { label: "الشاشة", value: "11 إنش IPS لمس، دقة 1920×1200" },
            { label: "المعالج", value: "رباعي النواة، 1.8GHz" },
            { label: "الذاكرة", value: "2GB RAM / 16GB تخزين" },
            { label: "الاتصال", value: "Wi-Fi 2.4/5GHz، بلوتوث 5.0" },
            { label: "الطاقة", value: "12V / 2A، USB-C" },
            { label: "الأبعاد", value: "264 × 166 × 11 مم" },
          ],
        },
      },
    ],
  },
  {
    key: "switches",
    en: {
      name: "Touch Switches",
      desc: "Glass-front switches built to replace the wall switch entirely.",
    },
    ar: {
      name: "مفاتيح اللمس الذكية",
      desc: "مفاتيح بواجهة زجاجية تحل محل مفتاح الحائط التقليدي، لا تكتفي بأتمتته.",
    },
    items: [
      {
        slug: "t1", images: ["/store/t1.jpg", "/store/t1-2.jpg"], name: "Syltra T1", tags: ["Zigbee", "Wi-Fi"],
        en: { tagline: "One touch, one light, done right.", description: "A single-gang glass switch with a backlit icon you can find in the dark. Works from the wall, the app, or a word to Syla. Fits standard boxes and replaces your old switch in minutes.", specs: [{ label: "Gangs", value: "1" }, { label: "Surface", value: "Toughened glass" }, { label: "Fire resistance", value: "Up to 850°C" }, { label: "Connectivity", value: "Wi-Fi 2.4GHz, Zigbee 3.0 (optional)" }] },
        ar: { tagline: "لمسة واحدة تكفي.", description: "مفتاح زجاجي بزر واحد بأيقونة مضيئة تجدها في العتمة. يعمل من الحائط أو التطبيق أو بكلمة لسيلا. يركب مكان مفتاحك القديم في دقائق.", specs: [{ label: "عدد الخطوط", value: "1" }, { label: "السطح", value: "زجاج مقسى" }, { label: "مقاومة الحريق", value: "حتى 850°م" }, { label: "الاتصال", value: "Wi-Fi 2.4GHz، Zigbee 3.0 (اختياري)" }] },
      },
      {
        slug: "t2", images: ["/store/t2.jpg", "/store/t2-2.jpg"], name: "Syltra T2", tags: ["Zigbee", "Wi-Fi"],
        en: { tagline: "Two circuits, one clean panel.", description: "Two independent touch circuits on one glass panel. Control each light alone or both together, from the wall or the app. The blue indicators tell you what is on at a glance.", specs: [{ label: "Gangs", value: "2, independent" }, { label: "Surface", value: "Toughened glass" }, { label: "Fire resistance", value: "Up to 850°C" }, { label: "Connectivity", value: "Wi-Fi 2.4GHz, Zigbee 3.0 (optional)" }] },
        ar: { tagline: "زران على لوحة واحدة أنيقة.", description: "دائرتان مستقلتان على لوحة زجاجية واحدة. تحكم في كل إضاءة وحدها أو الاثنتين معًا من الحائط أو التطبيق، والمؤشر الأزرق يخبرك بما يعمل من نظرة.", specs: [{ label: "عدد الخطوط", value: "2، مستقلان" }, { label: "السطح", value: "زجاج مقسى" }, { label: "مقاومة الحريق", value: "حتى 850°م" }, { label: "الاتصال", value: "Wi-Fi 2.4GHz، Zigbee 3.0 (اختياري)" }] },
      },
      {
        slug: "t3", images: ["/store/t3.jpg", "/store/t3-2.jpg"], name: "Syltra T3", tags: ["Zigbee", "Wi-Fi"],
        en: { tagline: "Three lights, zero clutter.", description: "Three touch circuits in the space of one switch. Perfect for majlis and living rooms where three lighting zones used to mean three ugly switches.", specs: [{ label: "Gangs", value: "3, independent" }, { label: "Surface", value: "Toughened glass" }, { label: "Fire resistance", value: "Up to 850°C" }, { label: "Connectivity", value: "Wi-Fi 2.4GHz, Zigbee 3.0 (optional)" }] },
        ar: { tagline: "ثلاث إضاءات دون زحمة مفاتيح.", description: "ثلاث دوائر لمسية في مساحة مفتاح واحد. مثالي للمجالس والصالات التي كانت تحتاج ثلاثة مفاتيح متجاورة لثلاث مناطق إضاءة.", specs: [{ label: "عدد الخطوط", value: "3، مستقلة" }, { label: "السطح", value: "زجاج مقسى" }, { label: "مقاومة الحريق", value: "حتى 850°م" }, { label: "الاتصال", value: "Wi-Fi 2.4GHz، Zigbee 3.0 (اختياري)" }] },
      },
      {
        slug: "t4", images: ["/store/t4.jpg", "/store/t4-2.jpg"], name: "Syltra T4", tags: ["Zigbee", "Wi-Fi"],
        en: { tagline: "Four zones from one point.", description: "Four independent circuits on a single glass panel. One point on the wall controls the chandelier, the spots, the cove and the lamp, each with its own glowing key.", specs: [{ label: "Gangs", value: "4, independent" }, { label: "Surface", value: "Toughened glass" }, { label: "Fire resistance", value: "Up to 850°C" }, { label: "Connectivity", value: "Wi-Fi 2.4GHz, Zigbee 3.0 (optional)" }] },
        ar: { tagline: "أربع مناطق من نقطة واحدة.", description: "أربع دوائر مستقلة على لوحة زجاجية واحدة. نقطة واحدة على الحائط تتحكم في الثريا والسبوتات والإضاءة المخفية والأباجورة، ولكل منها زر مضيء خاص.", specs: [{ label: "عدد الخطوط", value: "4، مستقلة" }, { label: "السطح", value: "زجاج مقسى" }, { label: "مقاومة الحريق", value: "حتى 850°م" }, { label: "الاتصال", value: "Wi-Fi 2.4GHz، Zigbee 3.0 (اختياري)" }] },
      },
      {
        slug: "td", images: ["/store/td.jpg", "/store/td-2.jpg"], name: "Syltra TD", tags: ["Zigbee", "Wi-Fi"],
        en: { tagline: "Set the light to match the moment.", description: "A touch dimmer with a glowing slide bar. Sweep your finger for full brightness at dinner or a faint glow for a movie. Remembers your favorite level and returns to it.", specs: [{ label: "Function", value: "Dimming, 0–100%" }, { label: "Surface", value: "Toughened glass" }, { label: "Max load", value: "300W" }, { label: "Connectivity", value: "Wi-Fi 2.4GHz, Zigbee 3.0 (optional)" }] },
        ar: { tagline: "إضاءة على مزاج اللحظة.", description: "معتّم لمسي بشريط انزلاقي مضيء. مرر إصبعك لإضاءة كاملة على العشاء أو توهج خافت لفيلم الليلة. يحفظ مستواك المفضل ويعود إليه.", specs: [{ label: "الوظيفة", value: "تعتيم من 0 إلى 100%" }, { label: "السطح", value: "زجاج مقسى" }, { label: "أقصى حمل", value: "300 وات" }, { label: "الاتصال", value: "Wi-Fi 2.4GHz، Zigbee 3.0 (اختياري)" }] },
      },
      {
        slug: "tc", images: ["/store/tc.jpg", "/store/tc-2.jpg"], name: "Syltra TC", tags: ["Zigbee", "Wi-Fi"],
        en: { tagline: "Curtains at a touch.", description: "Open, stop and close from three glowing keys on the wall. Pairs with Syltra curtain motors and joins your morning scene so the house wakes with the sun.", specs: [{ label: "Function", value: "Open / Stop / Close" }, { label: "Surface", value: "Toughened glass" }, { label: "Max load", value: "3A" }, { label: "Connectivity", value: "Wi-Fi 2.4GHz, Zigbee 3.0 (optional)" }] },
        ar: { tagline: "الستائر بلمسة من الحائط.", description: "فتح وإيقاف وإغلاق من ثلاثة أزرار مضيئة. يقترن بمحركات ستائر سيلترا وينضم لمشهد الصباح فيصحو البيت مع الشمس.", specs: [{ label: "الوظيفة", value: "فتح / إيقاف / إغلاق" }, { label: "السطح", value: "زجاج مقسى" }, { label: "أقصى حمل", value: "3 أمبير" }, { label: "الاتصال", value: "Wi-Fi 2.4GHz، Zigbee 3.0 (اختياري)" }] },
      },
    ],
  },
  {
    key: "modules",
    en: {
      name: "Smart Modules",
      desc: "Retrofit intelligence for the switch and circuit already in your wall.",
    },
    ar: {
      name: "وحدات التحكم الذكية",
      desc: "أضف الذكاء إلى مفاتيحك ودوائرك الكهربائية الحالية دون تغييرها.",
    },
    items: [
      {
        slug: "m1", images: ["/store/m1.jpg", "/store/m1-2.jpg"], name: "Syltra M1", tags: ["Zigbee", "Z-Wave", "Wi-Fi"],
        en: { tagline: "Any switch becomes smart, invisibly.", description: "M1 hides behind your existing switch and makes it smart without changing how it looks. The wall works as before, and the app, scenes and Syla all join in.", specs: [{ label: "Channels", value: "1" }, { label: "Power", value: "100–240V~, 50/60Hz" }, { label: "Max load", value: "16A" }, { label: "Connectivity", value: "Zigbee 3.0, Wi-Fi 2.4GHz" }] },
        ar: { tagline: "أي مفتاح يصبح ذكيًا دون أن يتغير شكله.", description: "يختبئ M1 خلف مفتاحك الحالي ويجعله ذكيًا كما هو. يبقى الحائط يعمل كعادته، وينضم التطبيق والمشاهد وسيلا إلى التحكم.", specs: [{ label: "عدد الخطوط", value: "1" }, { label: "الطاقة", value: "100–240V~, 50/60Hz" }, { label: "أقصى حمل", value: "16 أمبير" }, { label: "الاتصال", value: "Zigbee 3.0، Wi-Fi 2.4GHz" }] },
      },
      {
        slug: "m2", images: ["/store/m2.jpg", "/store/m2-2.jpg"], name: "Syltra M2", tags: ["Zigbee", "Z-Wave", "Wi-Fi"],
        en: { tagline: "Two circuits in one hidden module.", description: "Two independently controlled channels from one module behind the switch. Half the wiring, half the cost, and both lights in the app with schedules and scenes.", specs: [{ label: "Channels", value: "2, independent" }, { label: "Power", value: "100–240V~, 50/60Hz" }, { label: "Max load", value: "2 × 10A" }, { label: "Connectivity", value: "Zigbee 3.0, Wi-Fi 2.4GHz" }] },
        ar: { tagline: "قناتان في وحدة واحدة مخفية.", description: "قناتان مستقلتان من وحدة واحدة خلف المفتاح. نصف التمديدات ونصف التكلفة، وكلتا الإضاءتين في التطبيق بجداول ومشاهد.", specs: [{ label: "عدد الخطوط", value: "2، مستقلان" }, { label: "الطاقة", value: "100–240V~, 50/60Hz" }, { label: "أقصى حمل", value: "2 × 10 أمبير" }, { label: "الاتصال", value: "Zigbee 3.0، Wi-Fi 2.4GHz" }] },
      },
      {
        slug: "m3", images: ["/store/m3.jpg", "/store/m3-2.jpg"], name: "Syltra M3", tags: ["Zigbee", "Z-Wave", "Wi-Fi"],
        en: { tagline: "Three channels, one deep box.", description: "Three circuits from a single module. The economical choice for rooms with many lighting zones, with every channel scheduled and scened on its own.", specs: [{ label: "Channels", value: "3, independent" }, { label: "Power", value: "100–240V~, 50/60Hz" }, { label: "Max load", value: "3 × 10A" }, { label: "Connectivity", value: "Zigbee 3.0, Wi-Fi 2.4GHz" }] },
        ar: { tagline: "ثلاث قنوات من وحدة واحدة.", description: "ثلاث دوائر من وحدة واحدة. الخيار الاقتصادي للغرف كثيرة المناطق، مع جدولة ومشاهد مستقلة لكل قناة.", specs: [{ label: "عدد الخطوط", value: "3، مستقلة" }, { label: "الطاقة", value: "100–240V~, 50/60Hz" }, { label: "أقصى حمل", value: "3 × 10 أمبير" }, { label: "الاتصال", value: "Zigbee 3.0، Wi-Fi 2.4GHz" }] },
      },
      {
        slug: "dim", images: ["/store/dim.jpg", "/store/dim-2.jpg"], name: "Syltra DIM", tags: ["Zigbee", "Wi-Fi"],
        en: { tagline: "Smooth dimming behind any switch.", description: "A hidden dimmer that brings smooth, flicker-free dimming to your existing lights. From one percent to one hundred, on the wall, in the app, or by voice.", specs: [{ label: "Function", value: "Dimming, 0–100%" }, { label: "Power", value: "100–240V~, 50/60Hz" }, { label: "Max load", value: "300W" }, { label: "Connectivity", value: "Zigbee 3.0, Wi-Fi 2.4GHz" }] },
        ar: { tagline: "تعتيم ناعم خلف أي مفتاح.", description: "معتّم مخفي يمنح إضاءتك الحالية تعتيمًا ناعمًا بلا وميض. من واحد بالمئة إلى مئة، من الحائط أو التطبيق أو بالصوت.", specs: [{ label: "الوظيفة", value: "تعتيم من 0 إلى 100%" }, { label: "الطاقة", value: "100–240V~, 50/60Hz" }, { label: "أقصى حمل", value: "300 وات" }, { label: "الاتصال", value: "Zigbee 3.0، Wi-Fi 2.4GHz" }] },
      },
      {
        slug: "curtain-module", images: ["/store/curtain-module.jpg", "/store/curtain-module-2.jpg"], name: "Syltra CURTAIN", tags: ["Zigbee", "Wi-Fi"],
        en: { tagline: "Your curtain motor, on the network.", description: "Wires into the curtain or shutter motor and gives you open, close and exact position from the app. Set it to fifty percent at noon, closed at sunset, open with the alarm.", specs: [{ label: "Function", value: "Open / Stop / Close" }, { label: "Power", value: "100–240V~, 50/60Hz" }, { label: "Max load", value: "3A" }, { label: "Connectivity", value: "Zigbee 3.0, Wi-Fi 2.4GHz" }] },
        ar: { tagline: "محرك ستارتك على الشبكة.", description: "توصَّل بمحرك الستارة أو الرول وتمنحك الفتح والإغلاق والموضع الدقيق من التطبيق. اضبطها على النصف ظهرًا، مغلقة عند الغروب، مفتوحة مع المنبه.", specs: [{ label: "الوظيفة", value: "فتح / إيقاف / إغلاق" }, { label: "الطاقة", value: "100–240V~, 50/60Hz" }, { label: "أقصى حمل", value: "3 أمبير" }, { label: "الاتصال", value: "Zigbee 3.0، Wi-Fi 2.4GHz" }] },
      },
      {
        slug: "fan", images: ["/store/fan.jpg", "/store/fan-2.jpg"], name: "Syltra FAN", tags: ["Zigbee", "Wi-Fi"],
        en: { tagline: "Three speeds, quietly smart.", description: "Controls a ceiling or exhaust fan at three speeds from the wall and the app. Ties into climate scenes so the room stirs the air before it gets warm.", specs: [{ label: "Function", value: "On/off, speed control" }, { label: "Power", value: "100–240V~, 50/60Hz" }, { label: "Max load", value: "2A" }, { label: "Connectivity", value: "Zigbee 3.0, Wi-Fi 2.4GHz" }] },
        ar: { tagline: "ثلاث سرعات بذكاء هادئ.", description: "تتحكم بمروحة السقف أو الشفاط على ثلاث سرعات من الحائط والتطبيق. ترتبط بمشاهد المناخ فتحرك الهواء قبل أن تشتد الحرارة.", specs: [{ label: "الوظيفة", value: "تشغيل/إطفاء وتحكم بالسرعة" }, { label: "الطاقة", value: "100–240V~, 50/60Hz" }, { label: "أقصى حمل", value: "2 أمبير" }, { label: "الاتصال", value: "Zigbee 3.0، Wi-Fi 2.4GHz" }] },
      },
      {
        slug: "garage", images: ["/store/garage.jpg", "/store/garage-2.jpg"], name: "Syltra GARAGE", tags: ["Zigbee", "Wi-Fi"],
        en: { tagline: "The garage answers your phone.", description: "Connects to the garage motor, opens and closes from the app, and tells you the door state wherever you are. No more turning back to check.", specs: [{ label: "Function", value: "Open / close / status" }, { label: "Power", value: "100–240V~, 50/60Hz" }, { label: "Max load", value: "5A" }, { label: "Connectivity", value: "Zigbee 3.0, Wi-Fi 2.4GHz" }] },
        ar: { tagline: "الجراج يرد على جوالك.", description: "تتصل بمحرك الجراج وتفتح وتغلق من التطبيق وتخبرك بحالة الباب أينما كنت. لا رجوع للبيت للتأكد بعد اليوم.", specs: [{ label: "الوظيفة", value: "فتح / إغلاق / تأكيد الحالة" }, { label: "الطاقة", value: "100–240V~, 50/60Hz" }, { label: "أقصى حمل", value: "5 أمبير" }, { label: "الاتصال", value: "Zigbee 3.0، Wi-Fi 2.4GHz" }] },
      },
      {
        slug: "air", images: ["/store/air.jpg", "/store/air-2.jpg"], name: "Syltra AIR", tags: ["Wi-Fi", "BLE"],
        en: { tagline: "Old AC, new brain.", description: "Turns any remote-controlled AC into a smart one. Temperature, mode and fan from the app, with schedules that cool the room before you arrive and save power when you leave.", specs: [{ label: "Function", value: "Universal IR control" }, { label: "Power", value: "100–240V~, 50/60Hz" }, { label: "IR frequency", value: "38KHz" }, { label: "Connectivity", value: "Wi-Fi 2.4GHz, Bluetooth LE" }] },
        ar: { tagline: "مكيف قديم بعقل جديد.", description: "تحوّل أي مكيف يعمل بريموت إلى مكيف ذكي. الحرارة والوضع والمروحة من التطبيق، مع جداول تبرد الغرفة قبل وصولك وتوفر الكهرباء بعد خروجك.", specs: [{ label: "الوظيفة", value: "تحكم شامل بالأشعة تحت الحمراء" }, { label: "الطاقة", value: "100–240V~, 50/60Hz" }, { label: "تردد الأشعة", value: "38 كيلوهرتز" }, { label: "الاتصال", value: "Wi-Fi 2.4GHz، بلوتوث LE" }] },
      },
    ],
  },
  {
    key: "security",
    en: {
      name: "Security",
      desc: "Locks, cameras and doorbells built for the front door, not the demo table.",
    },
    ar: {
      name: "الأمان",
      desc: "أقفال وكاميرات وأجراس أبواب مصممة للاستخدام الفعلي، لا للعرض فقط.",
    },
    items: [
      {
        slug: "lock", images: ["/store/lock.jpg"], name: "Syltra Lock", tags: ["BLE", "App"],
        en: { tagline: "Your door, without keys.", description: "A smart handle lock that opens by fingerprint, code or phone. Guests get temporary codes, you get a log of every entry, and the key stays for emergencies only.", specs: [{ label: "Entry methods", value: "Fingerprint, PIN" }, { label: "App control", value: "Unlock, lock, access log" }, { label: "Connectivity", value: "Bluetooth LE" }, { label: "Alerts", value: "Real-time, on every entry" }] },
        ar: { tagline: "بابك بلا مفاتيح.", description: "قفل ذكي بمقبض يفتح بالبصمة أو الرمز أو الجوال. للضيوف رموز مؤقتة، ولك سجل بكل دخول، ويبقى المفتاح للطوارئ فقط.", specs: [{ label: "طرق الدخول", value: "بصمة، رقم سري" }, { label: "تحكم التطبيق", value: "فتح، إغلاق، سجل الدخول" }, { label: "الاتصال", value: "بلوتوث LE" }, { label: "التنبيهات", value: "فورية مع كل عملية دخول" }] },
      },
      {
        slug: "lock-pro", images: ["/store/lock-pro.jpg"], name: "Syltra Pro", tags: ["BLE", "App"],
        en: { tagline: "A fingerprint in the handle itself.", description: "The sensor sits inside the handle, so the door opens in one natural motion. Grip, read, open. Solid metal body and a battery that lasts months per charge.", specs: [{ label: "Entry methods", value: "App, keyless" }, { label: "App control", value: "Remote unlock, guest access" }, { label: "Connectivity", value: "Bluetooth LE" }, { label: "Best for", value: "Everyday households" }] },
        ar: { tagline: "البصمة في المقبض نفسه.", description: "الحساس داخل المقبض، فيُفتح الباب بحركة واحدة طبيعية: أمسك، اقرأ، ادخل. جسم معدني صلب وبطارية تدوم شهورًا بالشحنة.", specs: [{ label: "طرق الدخول", value: "تطبيق، بدون مفتاح" }, { label: "تحكم التطبيق", value: "فتح عن بُعد، دخول للضيوف" }, { label: "الاتصال", value: "بلوتوث LE" }, { label: "الأنسب لـ", value: "الاستخدام المنزلي اليومي" }] },
      },
      {
        slug: "lock-elite", name: "Syltra Elite", tags: ["NFC", "BLE", "App"],
        en: { tagline: "The flagship of the door.", description: "Fingerprint, NFC card, code and phone in one flagship lock. A full-metal body, a camera in the peephole, and alerts for every attempt at the door.", specs: [{ label: "Entry methods", value: "Fingerprint, face, PIN, NFC card" }, { label: "App control", value: "Full remote management" }, { label: "Connectivity", value: "NFC, Bluetooth LE" }, { label: "Finish", value: "Premium metal" }] },
        ar: { tagline: "قمة أقفال سيلترا.", description: "بصمة وبطاقة NFC ورمز وجوال في قفل واحد رائد. جسم معدني كامل وكاميرا في العين السحرية وتنبيه عند أي محاولة على الباب.", specs: [{ label: "طرق الدخول", value: "بصمة، وجه، رقم سري، بطاقة NFC" }, { label: "تحكم التطبيق", value: "إدارة كاملة عن بُعد" }, { label: "الاتصال", value: "NFC، بلوتوث LE" }, { label: "الخامة", value: "معدن فاخر" }] },
      },
      {
        slug: "lock-bolt", images: ["/store/lock-bolt.jpg"], name: "Syltra Bolt", tags: ["BLE", "App"],
        en: { tagline: "A deadbolt with a keypad face.", description: "Replaces the deadbolt cylinder with a glass keypad. Codes for the family, temporary codes for the driver and the housekeeper, and a USB-C port for emergency power.", specs: [{ label: "Type", value: "Retrofit deadbolt" }, { label: "Best for", value: "Offices, rental units" }, { label: "App control", value: "Per-tenant access codes" }, { label: "Connectivity", value: "Bluetooth LE" }] },
        ar: { tagline: "سلندر ذكي بلوحة أرقام.", description: "يستبدل سلندر القفل بلوحة أرقام زجاجية. رموز للعائلة ورموز مؤقتة للسائق والعاملة ومنفذ USB-C للطاقة عند الطوارئ.", specs: [{ label: "النوع", value: "قفل ترقية للباب الحالي" }, { label: "الأنسب لـ", value: "المكاتب والوحدات المؤجرة" }, { label: "تحكم التطبيق", value: "رموز دخول لكل مستأجر" }, { label: "الاتصال", value: "بلوتوث LE" }] },
      },
      {
        slug: "cam", images: ["/store/cam.jpg"], name: "Syltra Cam", tags: ["Wi-Fi"],
        en: { tagline: "An eye that follows the motion.", description: "An indoor camera that pans and tilts to follow movement. Sharp night vision, two-way talk, and recordings that stay yours, on the card or your private cloud.", specs: [{ label: "Resolution", value: "4K" }, { label: "Detection", value: "On-device AI, person, vehicle, package" }, { label: "Connectivity", value: "Wi-Fi 2.4GHz" }, { label: "Storage", value: "Local and optional cloud" }] },
        ar: { tagline: "عين تتابع الحركة.", description: "كاميرا داخلية تدور وتميل لتتابع الحركة. رؤية ليلية حادة ومحادثة بالاتجاهين وتسجيلات تبقى ملكك على البطاقة أو سحابتك الخاصة.", specs: [{ label: "الدقة", value: "4K" }, { label: "الكشف", value: "ذكاء اصطناعي محلي, أشخاص، مركبات، طرود" }, { label: "الاتصال", value: "Wi-Fi 2.4GHz" }, { label: "التخزين", value: "محلي، مع خيار سحابي" }] },
      },
      {
        slug: "doorbell", images: ["/store/doorbell.jpg"], name: "Syltra Doorbell", tags: ["Wi-Fi"],
        en: { tagline: "See who is there, from anywhere.", description: "A video doorbell that rings your phone. See the visitor, talk to them, and open the smart lock, from the majlis or from another city.", specs: [{ label: "Video", value: "HD, night vision" }, { label: "Audio", value: "Two-way talk" }, { label: "Alerts", value: "Instant, on motion or press" }, { label: "Connectivity", value: "Wi-Fi 2.4GHz" }] },
        ar: { tagline: "شاهد من بالباب من أي مكان.", description: "جرس بكاميرا يرن على جوالك. شاهد الزائر وكلمه وافتح القفل الذكي، من المجلس أو من مدينة أخرى.", specs: [{ label: "الفيديو", value: "دقة عالية، رؤية ليلية" }, { label: "الصوت", value: "محادثة ثنائية الاتجاه" }, { label: "التنبيهات", value: "فورية عند الحركة أو الضغط" }, { label: "الاتصال", value: "Wi-Fi 2.4GHz" }] },
      },
    ],
  },
  {
    key: "sensors",
    en: {
      name: "Sensors",
      desc: "Quiet awareness for every room, presence, air, water and smoke.",
    },
    ar: {
      name: "الحساسات",
      desc: "وعي صامت بكل ما يحدث في المنزل, الحركة والهواء والماء والدخان.",
    },
    items: [
      {
        slug: "motion", name: "Syltra Motion Sensor", tags: ["Zigbee"],
        en: { tagline: "The house feels you coming.", description: "A small sensor that turns hallways and bathrooms into rooms that light themselves. Enter, light on. Leave, light off. Two years on one battery.", specs: [{ label: "Detection", value: "PIR, wide-angle" }, { label: "Battery life", value: "Up to 2 years" }, { label: "Connectivity", value: "Zigbee 3.0" }] },
        ar: { tagline: "البيت يشعر بقدومك.", description: "حساس صغير يجعل الممرات ودورات المياه تضيء نفسها. تدخل فيضيء، تخرج فينطفئ. سنتان على بطارية واحدة.", specs: [{ label: "الكشف", value: "PIR، زاوية واسعة" }, { label: "عمر البطارية", value: "حتى سنتين" }, { label: "الاتصال", value: "Zigbee 3.0" }] },
      },
      {
        slug: "door-window", name: "Syltra Door / Window Sensor", tags: ["Zigbee"],
        en: { tagline: "Knows every open and close.", description: "Two small pieces on the door or window frame. The house knows the moment it opens, arms the scene at night, and tells you if something opened while you were away.", specs: [{ label: "Detection", value: "Magnetic reed contact" }, { label: "Battery life", value: "Up to 2 years" }, { label: "Connectivity", value: "Zigbee 3.0" }] },
        ar: { tagline: "يعرف كل فتح وإغلاق.", description: "قطعتان صغيرتان على إطار الباب أو النافذة. يعرف البيت لحظة الفتح، ويسلّح مشهد الليل، ويخبرك إن انفتح شيء في غيابك.", specs: [{ label: "الكشف", value: "تلامس مغناطيسي" }, { label: "عمر البطارية", value: "حتى سنتين" }, { label: "الاتصال", value: "Zigbee 3.0" }] },
      },
      {
        slug: "climate", name: "Syltra Temperature & Humidity Sensor", tags: ["Zigbee"],
        en: { tagline: "The number behind comfort.", description: "Reads temperature and humidity in each room and feeds the AC scenes, so cooling follows the actual room, not a guess from the hallway.", specs: [{ label: "Temperature accuracy", value: "±0.5°C" }, { label: "Humidity", value: "0–100% RH" }, { label: "Battery life", value: "Up to 2 years" }, { label: "Connectivity", value: "Zigbee 3.0" }] },
        ar: { tagline: "الرقم الذي خلف الراحة.", description: "يقرأ الحرارة والرطوبة في كل غرفة ويغذي مشاهد التكييف، فيتبع التبريد حال الغرفة فعلًا لا تخمينًا من الممر.", specs: [{ label: "دقة الحرارة", value: "±0.5°م" }, { label: "الرطوبة", value: "0–100%" }, { label: "عمر البطارية", value: "حتى سنتين" }, { label: "الاتصال", value: "Zigbee 3.0" }] },
      },
      {
        slug: "light-sensor", name: "Syltra Light Sensor", tags: ["Zigbee"],
        en: { tagline: "Curtains that follow the sun.", description: "Measures daylight and drives the scenes. Curtains soften the noon glare, lights come on at real dusk, not at a fixed hour.", specs: [{ label: "Detection", value: "Ambient lux level" }, { label: "Battery life", value: "Up to 2 years" }, { label: "Connectivity", value: "Zigbee 3.0" }] },
        ar: { tagline: "ستائر تتبع الشمس.", description: "يقيس ضوء النهار ويقود المشاهد. تلطف الستائر وهج الظهيرة وتضيء الأنوار عند الغسق الحقيقي لا عند ساعة ثابتة.", specs: [{ label: "الكشف", value: "مستوى الإضاءة المحيطة" }, { label: "عمر البطارية", value: "حتى سنتين" }, { label: "الاتصال", value: "Zigbee 3.0" }] },
      },
      {
        slug: "smoke", name: "Syltra Smoke Sensor", tags: ["Zigbee"],
        en: { tagline: "The alarm that reaches your phone.", description: "A smoke sensor that sounds locally and alerts every phone in the family, at home or away. Ties into scenes that flash the lights and open the curtains for exit.", specs: [{ label: "Detection", value: "Photoelectric" }, { label: "Alert", value: "Local siren + instant push alert" }, { label: "Connectivity", value: "Zigbee 3.0" }] },
        ar: { tagline: "إنذار يصل إلى جوالك.", description: "حساس دخان يصفّر محليًا وينبه جوالات العائلة كلها في البيت وخارجه. يرتبط بمشاهد تومض الأنوار وتفتح الستائر لتسهيل الخروج.", specs: [{ label: "الكشف", value: "ضوئي" }, { label: "التنبيه", value: "صفارة محلية + إشعار فوري" }, { label: "الاتصال", value: "Zigbee 3.0" }] },
      },
      {
        slug: "gas", name: "Syltra Gas Sensor", tags: ["Zigbee"],
        en: { tagline: "Catches the leak early.", description: "Watches for combustible gas in the kitchen and utility room. An early local alarm, an instant notification, and a scene that can shut the gas valve.", specs: [{ label: "Detection", value: "Combustible gas" }, { label: "Alert", value: "Local siren + instant push alert" }, { label: "Connectivity", value: "Zigbee 3.0" }] },
        ar: { tagline: "يلتقط التسرب مبكرًا.", description: "يراقب الغاز القابل للاشتعال في المطبخ وغرفة المرافق. إنذار محلي مبكر وإشعار فوري ومشهد يمكنه إغلاق صمام الغاز.", specs: [{ label: "الكشف", value: "غاز قابل للاشتعال" }, { label: "التنبيه", value: "صفارة محلية + إشعار فوري" }, { label: "الاتصال", value: "Zigbee 3.0" }] },
      },
      {
        slug: "water-leak", name: "Syltra Water Leak Sensor", tags: ["Zigbee"],
        en: { tagline: "The first drop, not the flood.", description: "Sits under the sink or beside the heater and catches the first drop. A late-night leak becomes a notification, not a ruined floor.", specs: [{ label: "Detection", value: "Water contact probes" }, { label: "Battery life", value: "Up to 2 years" }, { label: "Connectivity", value: "Zigbee 3.0" }] },
        ar: { tagline: "القطرة الأولى لا الفيضان.", description: "يوضع تحت الحوض أو بجانب السخان ويلتقط القطرة الأولى. تسرب منتصف الليل يصبح إشعارًا على الجوال لا أرضية متضررة.", specs: [{ label: "الكشف", value: "أطراف تلامس مائية" }, { label: "عمر البطارية", value: "حتى سنتين" }, { label: "الاتصال", value: "Zigbee 3.0" }] },
      },
      {
        slug: "air-quality", name: "Syltra Air Quality Sensor", tags: ["Zigbee", "Wi-Fi"],
        en: { tagline: "A live number for the air you breathe.", description: "Reads air quality around the clock and drives ventilation and AC scenes, so the house responds to poor air before anyone feels it.", specs: [{ label: "Reading", value: "Live AQI" }, { label: "Automation", value: "Triggers ventilation & AC scenes" }, { label: "Connectivity", value: "Zigbee 3.0, Wi-Fi 2.4GHz" }] },
        ar: { tagline: "رقم حي للهواء الذي تتنفسه.", description: "يقرأ جودة الهواء على مدار الساعة ويقود مشاهد التهوية والتكييف، فيستجيب البيت لرداءة الهواء قبل أن يشعر بها أحد.", specs: [{ label: "القراءة", value: "مؤشر جودة الهواء الحي" }, { label: "الأتمتة", value: "يفعّل مشاهد التهوية والتكييف" }, { label: "الاتصال", value: "Zigbee 3.0، Wi-Fi 2.4GHz" }] },
      },
    ],
  },
  {
    key: "cctv",
    en: {
      name: "CCTV & Surveillance",
      desc: "Professional-grade cameras and recording, for homes and businesses.",
    },
    ar: {
      name: "كاميرات المراقبة CCTV",
      desc: "كاميرات وتسجيل بمستوى احترافي, للمنازل والمنشآت التجارية.",
    },
    items: [
      {
        slug: "cctv-bullet", name: "Syltra CCTV Bullet", tags: ["Wi-Fi", "App"],
        en: { tagline: "Around-the-clock perimeter watch.", description: "A weatherproof outdoor camera for entrances, driveways and fences. Sharp 4MP by day, clear night vision after dark, and footage on your recorder or cloud.", specs: [{ label: "Resolution", value: "4MP, night vision" }, { label: "Build", value: "IP67 weatherproof" }, { label: "Storage", value: "NVR / cloud / microSD" }] },
        ar: { tagline: "مراقبة محيط المنزل على مدار الساعة.", description: "كاميرا خارجية مقاومة للعوامل الجوية للمداخل والممرات والأسوار. دقة 4MP نهارًا ورؤية ليلية واضحة، والتسجيل على جهازك أو سحابتك.", specs: [{ label: "الدقة", value: "4MP مع رؤية ليلية" }, { label: "التصنيع", value: "مقاومة IP67" }, { label: "التخزين", value: "جهاز تسجيل / سحابي / بطاقة ذاكرة" }] },
      },
      {
        slug: "cctv-dome", name: "Syltra CCTV Dome", tags: ["Wi-Fi", "App"],
        en: { tagline: "Wide coverage, quiet presence.", description: "A ceiling dome for lobbies, shops and halls. A wide angle covers the space from one point, in a tamper-resistant housing that blends into the ceiling.", specs: [{ label: "Resolution", value: "4MP wide angle" }, { label: "Mount", value: "Ceiling, tamper-resistant" }, { label: "Storage", value: "NVR / cloud / microSD" }] },
        ar: { tagline: "تغطية واسعة بحضور هادئ.", description: "قبة سقفية للاستقبال والمحلات والصالات. زاوية واسعة تغطي المكان من نقطة واحدة، في هيكل مقاوم للعبث يذوب في السقف.", specs: [{ label: "الدقة", value: "4MP بزاوية واسعة" }, { label: "التركيب", value: "سقفي مقاوم للعبث" }, { label: "التخزين", value: "جهاز تسجيل / سحابي / بطاقة ذاكرة" }] },
      },
      {
        slug: "cctv-ptz", name: "Syltra CCTV PTZ", tags: ["Wi-Fi", "App"],
        en: { tagline: "One camera does the work of three.", description: "A motorized camera that pans, tilts and zooms, and follows motion on its own. One unit sweeps a yard that would need three fixed cameras.", specs: [{ label: "Motion", value: "355° pan, 90° tilt, zoom" }, { label: "Tracking", value: "Auto motion tracking" }, { label: "Storage", value: "NVR / cloud / microSD" }] },
        ar: { tagline: "كاميرا واحدة بعمل ثلاث.", description: "كاميرا متحركة تدور وتميل وتقرب وتتعقب الحركة بنفسها. وحدة واحدة تمسح ساحة كانت تحتاج ثلاث كاميرات ثابتة.", specs: [{ label: "الحركة", value: "دوران 355° وإمالة 90° وتقريب" }, { label: "التعقب", value: "تعقب تلقائي للحركة" }, { label: "التخزين", value: "جهاز تسجيل / سحابي / بطاقة ذاكرة" }] },
      },
      {
        slug: "cctv-solar", name: "Syltra CCTV Solar", tags: ["Wi-Fi", "App"],
        en: { tagline: "Power from the sun, watching nonstop.", description: "A fully wireless camera with its own solar panel and battery. Mount it where the sun reaches and it simply works, no cabling, no electrician, no bills.", specs: [{ label: "Power", value: "Solar panel + built-in battery" }, { label: "Resolution", value: "4MP, color night vision" }, { label: "Build", value: "IP66, fully wireless" }] },
        ar: { tagline: "طاقتها من الشمس ومراقبتها لا تتوقف.", description: "كاميرا لاسلكية بالكامل بلوحها الشمسي وبطاريتها. ثبتها حيث تصل الشمس وستعمل ببساطة، بلا تمديدات ولا كهربائي ولا فواتير.", specs: [{ label: "الطاقة", value: "لوح شمسي + بطارية مدمجة" }, { label: "الدقة", value: "4MP برؤية ليلية ملونة" }, { label: "التصنيع", value: "IP66 لاسلكية بالكامل" }] },
      },
      {
        slug: "cctv-solar-4g", name: "Syltra CCTV Solar 4G", tags: ["App"],
        en: { tagline: "For land beyond the internet.", description: "A solar camera with a 4G SIM for farms, sites and remote plots. No power, no Wi-Fi, and it still streams straight to your phone.", specs: [{ label: "Power", value: "Solar panel + built-in battery" }, { label: "Connectivity", value: "4G SIM, no Wi-Fi needed" }, { label: "Use", value: "Farms, sites, remote land" }] },
        ar: { tagline: "للأراضي التي لا يصلها الإنترنت.", description: "كاميرا شمسية بشريحة 4G للمزارع والمواقع والأراضي البعيدة. لا كهرباء ولا واي فاي، وتبث مع ذلك مباشرة إلى جوالك.", specs: [{ label: "الطاقة", value: "لوح شمسي + بطارية مدمجة" }, { label: "الاتصال", value: "شريحة 4G بدون واي فاي" }, { label: "الاستخدام", value: "مزارع ومواقع وأراضٍ بعيدة" }] },
      },
      {
        slug: "cctv-solar-ptz", name: "Syltra CCTV Solar PTZ", tags: ["Wi-Fi", "App"],
        en: { tagline: "Sun-powered, motion-tracking.", description: "A motorized solar camera that sweeps gates and yards and follows movement automatically. Wide coverage with zero wiring.", specs: [{ label: "Motion", value: "355° pan with auto tracking" }, { label: "Power", value: "Solar panel + built-in battery" }, { label: "Build", value: "IP66 outdoor" }] },
        ar: { tagline: "بطاقة الشمس وتتعقب الحركة.", description: "كاميرا شمسية متحركة تمسح البوابات والأحواش وتتابع الحركة تلقائيًا. تغطية واسعة بلا سلك واحد.", specs: [{ label: "الحركة", value: "دوران 355° وتعقب تلقائي" }, { label: "الطاقة", value: "لوح شمسي + بطارية مدمجة" }, { label: "التصنيع", value: "IP66 خارجية" }] },
      },
      {
        slug: "cctv-nvr", name: "Syltra NVR 8", tags: ["App"],
        en: { tagline: "Weeks of footage, seconds to find.", description: "An 8-channel recorder that keeps weeks of footage locally. Review any camera from the app, jump by motion events, export a clip in seconds.", specs: [{ label: "Channels", value: "8 cameras" }, { label: "Storage", value: "Up to 8TB HDD" }, { label: "Access", value: "Live + playback from the app" }] },
        ar: { tagline: "أسابيع من التسجيل وثوانٍ للوصول.", description: "جهاز تسجيل بثماني قنوات يحفظ أسابيع من اللقطات محليًا. راجع أي كاميرا من التطبيق وتنقل بين أحداث الحركة وصدّر المقطع في ثوانٍ.", specs: [{ label: "القنوات", value: "8 كاميرات" }, { label: "التخزين", value: "حتى 8 تيرابايت" }, { label: "الوصول", value: "بث حي ومراجعة من التطبيق" }] },
      },
    ],
  },
  {
    key: "comfort",
    en: {
      name: "Comfort & Living",
      desc: "The everyday layer, climate, plugs, curtains, light and sound.",
    },
    ar: {
      name: "الراحة والمعيشة",
      desc: "الطبقة اليومية للمنزل, المناخ والمقابس والستائر والإضاءة والصوت.",
    },
    items: [
      {
        slug: "thermostat", name: "Syltra Thermostat", tags: ["Zigbee", "Wi-Fi"],
        en: { tagline: "Comfort that learns your rhythm.", description: "A thermostat that studies the household routine and adjusts ahead of it. Cool when you arrive, economical when you leave, without touching a button.", specs: [{ label: "Control", value: "Adaptive scheduling" }, { label: "Display", value: "Live temperature readout" }, { label: "Connectivity", value: "Zigbee 3.0, Wi-Fi 2.4GHz" }] },
        ar: { tagline: "راحة تتعلم إيقاعك.", description: "منظم حرارة يدرس روتين البيت ويسبقه بالتعديل. بارد عند وصولك واقتصادي بعد خروجك، دون أن تلمس زرًا.", specs: [{ label: "التحكم", value: "جدولة تكيّفية" }, { label: "الشاشة", value: "عرض حي لدرجة الحرارة" }, { label: "الاتصال", value: "Zigbee 3.0، Wi-Fi 2.4GHz" }] },
      },
      {
        slug: "ac-control", name: "Syltra AC Control", tags: ["Wi-Fi", "BLE"],
        en: { tagline: "Every remote AC, one app.", description: "Controls any remote-based air conditioner from the phone. Schedules, room targets and a place in the whole-home scenes, for the AC you already own.", specs: [{ label: "Compatibility", value: "Any split or central AC" }, { label: "Control", value: "App + wall panel" }, { label: "Reporting", value: "Energy consumption reports" }, { label: "Connectivity", value: "Wi-Fi 2.4GHz, Bluetooth LE" }] },
        ar: { tagline: "كل المكيفات في تطبيق واحد.", description: "يتحكم بأي مكيف يعمل بالريموت من الجوال. جداول ودرجات مستهدفة ومكان في مشاهد البيت الكاملة، لمكيفك الذي تملكه اليوم.", specs: [{ label: "التوافق", value: "أي مكيف سبليت أو مركزي" }, { label: "التحكم", value: "تطبيق + لوحة حائط" }, { label: "التقارير", value: "تقارير استهلاك الطاقة" }, { label: "الاتصال", value: "Wi-Fi 2.4GHz، بلوتوث LE" }] },
      },
      {
        slug: "plug", name: "Syltra Plug", tags: ["Wi-Fi"],
        en: { tagline: "The socket that reports back.", description: "A smart plug that switches anything and measures its power. See what the heater really costs, schedule the coffee machine, and cut standby waste.", specs: [{ label: "Max load", value: "16A" }, { label: "Monitoring", value: "Live energy usage" }, { label: "Connectivity", value: "Wi-Fi 2.4GHz" }] },
        ar: { tagline: "القابس الذي يرد عليك.", description: "قابس ذكي يشغّل أي جهاز ويقيس استهلاكه. اعرف كم يكلف السخان فعلًا، وجدول آلة القهوة، واقطع هدر الاستعداد.", specs: [{ label: "أقصى حمل", value: "16 أمبير" }, { label: "المراقبة", value: "استهلاك طاقة حي" }, { label: "الاتصال", value: "Wi-Fi 2.4GHz" }] },
      },
      {
        slug: "light", name: "Syltra Light", tags: ["Zigbee"],
        en: { tagline: "Sixteen million moods.", description: "A smart bulb with full color and warmth control. White for work, warm for the evening, any color for the occasion, all from the app or a word.", specs: [{ label: "Tuning", value: "Warm to cool white, dimmable" }, { label: "Fitting", value: "Standard screw / bayonet" }, { label: "Connectivity", value: "Zigbee 3.0" }] },
        ar: { tagline: "ستة عشر مليون مزاج.", description: "لمبة ذكية بتحكم كامل في اللون والدفء. أبيض للعمل ودافئ للمساء وأي لون للمناسبة، من التطبيق أو بكلمة واحدة.", specs: [{ label: "التعديل", value: "أبيض دافئ إلى بارد، قابل للتعتيم" }, { label: "التركيب", value: "قاعدة قياسية" }, { label: "الاتصال", value: "Zigbee 3.0" }] },
      },
      {
        slug: "curtain", name: "Syltra Curtain", tags: ["Zigbee", "Wi-Fi"],
        en: { tagline: "The house wakes with the sun.", description: "A quiet curtain motor with app, voice and schedule control. Opens gently with the morning alarm and closes itself at sunset.", specs: [{ label: "Noise level", value: "Under 45dB" }, { label: "Function", value: "Open / Stop / Close, scheduled" }, { label: "Connectivity", value: "Zigbee 3.0, Wi-Fi 2.4GHz" }] },
        ar: { tagline: "يصحو البيت مع الشمس.", description: "محرك ستائر هادئ يعمل بالتطبيق والصوت والجدولة. يفتح بهدوء مع منبه الصباح ويغلق نفسه عند الغروب.", specs: [{ label: "مستوى الضجيج", value: "أقل من 45 ديسيبل" }, { label: "الوظيفة", value: "فتح / إيقاف / إغلاق مجدول" }, { label: "الاتصال", value: "Zigbee 3.0، Wi-Fi 2.4GHz" }] },
      },
      {
        slug: "robot", name: "Syltra Robot", tags: ["Wi-Fi"],
        en: { tagline: "The floor cleans itself.", description: "A robot vacuum that maps the house, mops and vacuums on schedule, and returns to charge itself. The floor is done before you notice it needed doing.", specs: [{ label: "Mapping", value: "Room-by-room, saved maps" }, { label: "Scheduling", value: "Per-room or whole-home" }, { label: "Connectivity", value: "Wi-Fi 2.4GHz" }] },
        ar: { tagline: "الأرضية تنظف نفسها.", description: "روبوت يمسح خريطة البيت ويكنس ويمسح بجدول ويعود ليشحن نفسه. تجد الأرضية نظيفة قبل أن تنتبه أنها كانت تحتاج تنظيفًا.", specs: [{ label: "التخطيط", value: "غرفة بغرفة، خرائط محفوظة" }, { label: "الجدولة", value: "لكل غرفة أو للمنزل كله" }, { label: "الاتصال", value: "Wi-Fi 2.4GHz" }] },
      },
    ],
  },
];

export function findProductBySlug(slug: string): { product: Product; category: ProductCategory } | null {
  for (const category of productCatalog) {
    const product = category.items.find((item) => item.slug === slug);
    if (product) return { product, category };
  }
  return null;
}

export function allProductSlugs(): string[] {
  return productCatalog.flatMap((category) => category.items.map((item) => item.slug));
}
