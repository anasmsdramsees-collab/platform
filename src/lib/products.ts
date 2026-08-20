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
  image?: string; // populated once real product photography is uploaded
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
        name: "Syltra Hub Mini",
        tags: ["Wi-Fi", "Zigbee", "Z-Wave"],
        en: {
          tagline: "The whole apartment, from one small box.",
          description:
            "Hub Mini brings every room of an apartment or single-floor home onto one system. It's the entry point into the Syltra ecosystem, small enough to sit behind a TV, capable enough to run up to 100 devices without missing a beat.",
          specs: [
            { label: "Processor", value: "Quad-core, 1.2GHz" },
            { label: "Capacity", value: "Up to 100 devices" },
            { label: "Connectivity", value: "Wi-Fi 2.4GHz" },
            { label: "Power", value: "5V / 2A, USB-C" },
          ],
        },
        ar: {
          tagline: "الشقة كاملة، من صندوق صغير واحد.",
          description:
            "مركز Hub Mini يجمع كل غرف الشقة أو المنزل من طابق واحد في نظام واحد. هو نقطة الدخول لمنظومة سيلترا, صغير بما يكفي ليختبئ خلف التلفاز، وقوي بما يكفي لإدارة حتى 100 جهاز دون أي تأخير.",
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
        name: "Syltra Hub Pro",
        tags: ["Wi-Fi", "Zigbee", "Z-Wave", "Thread"],
        en: {
          tagline: "Full-villa coverage, with Home Assistant built in.",
          description:
            "Hub Pro is the default choice for a full villa, wider radio range, faster processing, and an embedded Home Assistant OS so local automations keep running even if the internet doesn't. Built for up to 300 devices across every room.",
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
          tagline: "تغطية للفيلا كاملة، مع Home Assistant مدمج.",
          description:
            "Hub Pro هو الخيار الافتراضي للفيلات الكاملة, مدى لاسلكي أوسع، ومعالجة أسرع، ونظام Home Assistant مدمج يبقي الأتمتة المحلية تعمل حتى لو انقطع الإنترنت. مصمم لإدارة حتى 300 جهاز في كل أرجاء المنزل.",
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
        name: "Syltra Hub Max",
        tags: ["Wi-Fi", "Zigbee", "Z-Wave", "Thread"],
        en: {
          tagline: "One system, an entire property.",
          description:
            "Hub Max is built for estates, hotels and commercial properties, the same design language as Hub Mini and Pro, scaled to coordinate 1,000+ devices across multiple buildings from a single pane of glass.",
          specs: [
            { label: "Processor", value: "Quad-core, 1.8GHz" },
            { label: "Capacity", value: "1,000+ devices" },
            { label: "Connectivity", value: "Wi-Fi 2.4/5GHz" },
            { label: "Network", value: "LAN 10/100/1000" },
          ],
        },
        ar: {
          tagline: "نظام واحد، لمنشأة كاملة.",
          description:
            "Hub Max مصمم للقصور والفنادق والمنشآت التجارية, بنفس لغة تصميم Hub Mini وPro، لكن بقدرة على تنسيق أكثر من 1000 جهاز عبر عدة مبانٍ من شاشة تحكم واحدة.",
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
        name: "Syltra Touch Panel 3″",
        tags: ["Wi-Fi", "Zigbee"],
        en: {
          tagline: "One room, one glance.",
          description:
            "A pocket-sized control point mounted at the door of a single room, lighting, climate and security surfaced on a crisp touch display, with the same glass-and-aluminum language as the rest of the range.",
          specs: [
            { label: "Screen", value: "3″ touch display" },
            { label: "Connectivity", value: "Wi-Fi 2.4GHz, Zigbee 3.0 (optional)" },
            { label: "Input", value: "Multi-touch" },
            { label: "Mounting", value: "Wall-mount, in-wall backbox" },
          ],
        },
        ar: {
          tagline: "غرفة واحدة، بلمحة واحدة.",
          description:
            "نقطة تحكم صغيرة تُركّب عند مدخل الغرفة, تعرض الإضاءة والمناخ والأمان على شاشة لمس واضحة، بنفس لغة الزجاج والألمنيوم المستخدمة في باقي المنظومة.",
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
        name: "Syltra Touch Panel 11″",
        tags: ["Wi-Fi", "Zigbee", "Matter"],
        en: {
          tagline: "The whole home, full resolution.",
          description:
            "An 11-inch dashboard built into the wall, every room, every camera, every scene at full 1920×1200 resolution. This is the panel a household actually gathers around, not a tablet stuck on with tape.",
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
          tagline: "المنزل كله، بدقة كاملة.",
          description:
            "لوحة تحكم بحجم 11 إنش مثبتة على الحائط, كل غرفة، وكل كاميرا، وكل مشهد بدقة 1920×1200. هذه هي اللوحة التي يتجمع حولها أهل البيت فعلًا، لا مجرد تابلت مثبت بشريط لاصق.",
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
        slug: "t1", name: "Syltra T1", tags: ["Zigbee", "Wi-Fi"],
        en: { tagline: "One light, switched cleanly.", description: "A 1-gang toughened-glass touch switch for a single circuit, tap to switch, hold for dimming where supported, control from across the room through the app.", specs: [{ label: "Gangs", value: "1" }, { label: "Surface", value: "Toughened glass" }, { label: "Fire resistance", value: "Up to 850°C" }, { label: "Connectivity", value: "Wi-Fi 2.4GHz, Zigbee 3.0 (optional)" }] },
        ar: { tagline: "مصباح واحد، بتحكم نظيف.", description: "مفتاح لمس بخط واحد وواجهة زجاجية مقساة, لمسة للتشغيل، وضغطة مطولة للتعتيم حيث يتوفر، مع تحكم من أي مكان عبر التطبيق.", specs: [{ label: "عدد الخطوط", value: "1" }, { label: "السطح", value: "زجاج مقسى" }, { label: "مقاومة الحريق", value: "حتى 850°م" }, { label: "الاتصال", value: "Wi-Fi 2.4GHz، Zigbee 3.0 (اختياري)" }] },
      },
      {
        slug: "t2", name: "Syltra T2", tags: ["Zigbee", "Wi-Fi"],
        en: { tagline: "Two circuits, one plate.", description: "A 2-gang touch switch for two independently controlled lights or circuits, one clean glass plate instead of a cluster of mechanical switches.", specs: [{ label: "Gangs", value: "2, independent" }, { label: "Surface", value: "Toughened glass" }, { label: "Fire resistance", value: "Up to 850°C" }, { label: "Connectivity", value: "Wi-Fi 2.4GHz, Zigbee 3.0 (optional)" }] },
        ar: { tagline: "دائرتان، بلوحة واحدة.", description: "مفتاح لمس بخطين للتحكم المستقل في مصباحين أو دائرتين, لوحة زجاجية واحدة أنيقة بدل مجموعة مفاتيح ميكانيكية.", specs: [{ label: "عدد الخطوط", value: "2، مستقلان" }, { label: "السطح", value: "زجاج مقسى" }, { label: "مقاومة الحريق", value: "حتى 850°م" }, { label: "الاتصال", value: "Wi-Fi 2.4GHz، Zigbee 3.0 (اختياري)" }] },
      },
      {
        slug: "t3", name: "Syltra T3", tags: ["Zigbee", "Wi-Fi"],
        en: { tagline: "A full room, one panel.", description: "A 3-gang touch switch that puts an entire room's lighting on a single glass plate, each circuit switched and scheduled independently from the app.", specs: [{ label: "Gangs", value: "3, independent" }, { label: "Surface", value: "Toughened glass" }, { label: "Fire resistance", value: "Up to 850°C" }, { label: "Connectivity", value: "Wi-Fi 2.4GHz, Zigbee 3.0 (optional)" }] },
        ar: { tagline: "غرفة كاملة، بلوحة واحدة.", description: "مفتاح لمس بثلاثة خطوط يجمع إضاءة الغرفة كاملة في لوحة زجاجية واحدة، مع تحكم وجدولة مستقلة لكل دائرة من التطبيق.", specs: [{ label: "عدد الخطوط", value: "3، مستقلة" }, { label: "السطح", value: "زجاج مقسى" }, { label: "مقاومة الحريق", value: "حتى 850°م" }, { label: "الاتصال", value: "Wi-Fi 2.4GHz، Zigbee 3.0 (اختياري)" }] },
      },
      {
        slug: "t4", name: "Syltra T4", tags: ["Zigbee", "Wi-Fi"],
        en: { tagline: "Maximum control, one plate.", description: "A 4-gang touch switch for the busiest walls in the house, four independent circuits on one plate, without four separate mechanical switches interrupting the wall.", specs: [{ label: "Gangs", value: "4, independent" }, { label: "Surface", value: "Toughened glass" }, { label: "Fire resistance", value: "Up to 850°C" }, { label: "Connectivity", value: "Wi-Fi 2.4GHz, Zigbee 3.0 (optional)" }] },
        ar: { tagline: "أقصى تحكم، بلوحة واحدة.", description: "مفتاح لمس بأربعة خطوط لأكثر الحوائط ازدحامًا بالمفاتيح, أربع دوائر مستقلة في لوحة واحدة، بدل أربعة مفاتيح ميكانيكية منفصلة.", specs: [{ label: "عدد الخطوط", value: "4، مستقلة" }, { label: "السطح", value: "زجاج مقسى" }, { label: "مقاومة الحريق", value: "حتى 850°م" }, { label: "الاتصال", value: "Wi-Fi 2.4GHz، Zigbee 3.0 (اختياري)" }] },
      },
      {
        slug: "td", name: "Syltra TD", tags: ["Zigbee", "Wi-Fi"],
        en: { tagline: "A slider for light, not a toggle.", description: "A dimmer touch switch with a true brightness slider under the glass, smooth, flicker-free dimming instead of a blunt on/off toggle.", specs: [{ label: "Function", value: "Dimming, 0–100%" }, { label: "Surface", value: "Toughened glass" }, { label: "Max load", value: "300W" }, { label: "Connectivity", value: "Wi-Fi 2.4GHz, Zigbee 3.0 (optional)" }] },
        ar: { tagline: "شريط تحكم في الضوء، لا مجرد مفتاح.", description: "مفتاح لمس بتعتيم مزود بشريط تحكم حقيقي في السطوع أسفل الزجاج, تعتيم سلس بلا وميض، بدل مفتاح تشغيل وإطفاء تقليدي.", specs: [{ label: "الوظيفة", value: "تعتيم من 0 إلى 100%" }, { label: "السطح", value: "زجاج مقسى" }, { label: "أقصى حمل", value: "300 وات" }, { label: "الاتصال", value: "Wi-Fi 2.4GHz، Zigbee 3.0 (اختياري)" }] },
      },
      {
        slug: "tc", name: "Syltra TC", tags: ["Zigbee", "Wi-Fi"],
        en: { tagline: "Open, stop, close, from the wall.", description: "A dedicated curtain touch switch with three clear controls, open, stop and close, for anyone who'd rather not reach for their phone to adjust the light.", specs: [{ label: "Function", value: "Open / Stop / Close" }, { label: "Surface", value: "Toughened glass" }, { label: "Max load", value: "3A" }, { label: "Connectivity", value: "Wi-Fi 2.4GHz, Zigbee 3.0 (optional)" }] },
        ar: { tagline: "فتح، إيقاف، إغلاق, من الحائط.", description: "مفتاح لمس مخصص للستائر بثلاثة أزرار واضحة, فتح وإيقاف وإغلاق, لمن يفضل عدم فتح الهاتف لمجرد تعديل الإضاءة.", specs: [{ label: "الوظيفة", value: "فتح / إيقاف / إغلاق" }, { label: "السطح", value: "زجاج مقسى" }, { label: "أقصى حمل", value: "3 أمبير" }, { label: "الاتصال", value: "Wi-Fi 2.4GHz، Zigbee 3.0 (اختياري)" }] },
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
        slug: "m1", name: "Syltra M1", tags: ["Zigbee", "Z-Wave", "Wi-Fi"],
        en: { tagline: "Hides behind the switch you already have.", description: "A single-channel module that sits behind any existing 1-gang switch, turning it smart without replacing the plate on the wall. Wire it once, control it from the app forever.", specs: [{ label: "Channels", value: "1" }, { label: "Power", value: "100–240V~, 50/60Hz" }, { label: "Max load", value: "16A" }, { label: "Connectivity", value: "Zigbee 3.0, Wi-Fi 2.4GHz" }] },
        ar: { tagline: "تختبئ خلف مفتاحك الحالي.", description: "وحدة بخط واحد تُركّب خلف أي مفتاح تقليدي بخط واحد، فتجعله ذكيًا دون تغيير اللوحة الظاهرة على الحائط. وصّلها مرة واحدة، وتحكم بها للأبد من التطبيق.", specs: [{ label: "عدد الخطوط", value: "1" }, { label: "الطاقة", value: "100–240V~, 50/60Hz" }, { label: "أقصى حمل", value: "16 أمبير" }, { label: "الاتصال", value: "Zigbee 3.0، Wi-Fi 2.4GHz" }] },
      },
      {
        slug: "m2", name: "Syltra M2", tags: ["Zigbee", "Z-Wave", "Wi-Fi"],
        en: { tagline: "Two loads, one retrofit.", description: "A dual-channel module for two independent circuits behind a single 2-gang switch, ideal for splitting a room's lighting into zones without new wiring.", specs: [{ label: "Channels", value: "2, independent" }, { label: "Power", value: "100–240V~, 50/60Hz" }, { label: "Max load", value: "2 × 10A" }, { label: "Connectivity", value: "Zigbee 3.0, Wi-Fi 2.4GHz" }] },
        ar: { tagline: "حملان، بترقية واحدة.", description: "وحدة بخطين للتحكم المستقل بدائرتين خلف مفتاح واحد بخطين, مثالية لتقسيم إضاءة الغرفة إلى مناطق دون أي أسلاك جديدة.", specs: [{ label: "عدد الخطوط", value: "2، مستقلان" }, { label: "الطاقة", value: "100–240V~, 50/60Hz" }, { label: "أقصى حمل", value: "2 × 10 أمبير" }, { label: "الاتصال", value: "Zigbee 3.0، Wi-Fi 2.4GHz" }] },
      },
      {
        slug: "m3", name: "Syltra M3", tags: ["Zigbee", "Z-Wave", "Wi-Fi"],
        en: { tagline: "A whole circuit, made smart at once.", description: "A triple-channel module behind a 3-gang switch, the fastest way to bring an entire room's lighting circuit onto the Syltra ecosystem in one retrofit.", specs: [{ label: "Channels", value: "3, independent" }, { label: "Power", value: "100–240V~, 50/60Hz" }, { label: "Max load", value: "3 × 10A" }, { label: "Connectivity", value: "Zigbee 3.0, Wi-Fi 2.4GHz" }] },
        ar: { tagline: "دائرة كاملة، ذكية دفعة واحدة.", description: "وحدة بثلاثة خطوط خلف مفتاح بثلاثة خطوط, أسرع طريقة لإدخال دائرة إضاءة غرفة كاملة إلى منظومة سيلترا في عملية ترقية واحدة.", specs: [{ label: "عدد الخطوط", value: "3، مستقلة" }, { label: "الطاقة", value: "100–240V~, 50/60Hz" }, { label: "أقصى حمل", value: "3 × 10 أمبير" }, { label: "الاتصال", value: "Zigbee 3.0، Wi-Fi 2.4GHz" }] },
      },
      {
        slug: "dim", name: "Syltra DIM", tags: ["Zigbee", "Wi-Fi"],
        en: { tagline: "Smooth brightness, behind the wall.", description: "A dimmer module for behind an existing dimmer plate, flicker-free brightness control for dimmable LED and halogen fixtures, tuned from the app or the switch itself.", specs: [{ label: "Function", value: "Dimming, 0–100%" }, { label: "Power", value: "100–240V~, 50/60Hz" }, { label: "Max load", value: "300W" }, { label: "Connectivity", value: "Zigbee 3.0, Wi-Fi 2.4GHz" }] },
        ar: { tagline: "تعتيم سلس، خلف الحائط.", description: "وحدة تعتيم تُركّب خلف مفتاح تعتيم حالي, تحكم سلس بلا وميض في سطوع مصابيح LED والهالوجين القابلة للتعتيم، عبر التطبيق أو المفتاح نفسه.", specs: [{ label: "الوظيفة", value: "تعتيم من 0 إلى 100%" }, { label: "الطاقة", value: "100–240V~, 50/60Hz" }, { label: "أقصى حمل", value: "300 وات" }, { label: "الاتصال", value: "Zigbee 3.0، Wi-Fi 2.4GHz" }] },
      },
      {
        slug: "curtain-module", name: "Syltra CURTAIN", tags: ["Zigbee", "Wi-Fi"],
        en: { tagline: "Motorizes the track you already own.", description: "A curtain motor module that drives an existing curtain track, schedule it with sunrise, tie it to a scene, or just reach for the app instead of the cord.", specs: [{ label: "Function", value: "Open / Stop / Close" }, { label: "Power", value: "100–240V~, 50/60Hz" }, { label: "Max load", value: "3A" }, { label: "Connectivity", value: "Zigbee 3.0, Wi-Fi 2.4GHz" }] },
        ar: { tagline: "تُحرّك السكة التي تملكها بالفعل.", description: "وحدة محرك ستائر تُشغّل سكة الستائر الحالية, اجعلها تعمل مع شروق الشمس، أو اربطها بمشهد كامل، أو ببساطة استخدم التطبيق بدل الحبل.", specs: [{ label: "الوظيفة", value: "فتح / إيقاف / إغلاق" }, { label: "الطاقة", value: "100–240V~, 50/60Hz" }, { label: "أقصى حمل", value: "3 أمبير" }, { label: "الاتصال", value: "Zigbee 3.0، Wi-Fi 2.4GHz" }] },
      },
      {
        slug: "fan", name: "Syltra FAN", tags: ["Zigbee", "Wi-Fi"],
        en: { tagline: "Speed control for the fan on your ceiling.", description: "A fan control module for ceiling and exhaust fans, on/off and speed from the app or a paired touch switch, no new wiring beyond the existing circuit.", specs: [{ label: "Function", value: "On/off, speed control" }, { label: "Power", value: "100–240V~, 50/60Hz" }, { label: "Max load", value: "2A" }, { label: "Connectivity", value: "Zigbee 3.0, Wi-Fi 2.4GHz" }] },
        ar: { tagline: "تحكم في سرعة المروحة فوق رأسك.", description: "وحدة تحكم بمراوح السقف والشفط, تشغيل وإطفاء وتحكم في السرعة من التطبيق أو مفتاح لمس مقترن، دون أي أسلاك إضافية بخلاف الدائرة الحالية.", specs: [{ label: "الوظيفة", value: "تشغيل/إطفاء وتحكم بالسرعة" }, { label: "الطاقة", value: "100–240V~, 50/60Hz" }, { label: "أقصى حمل", value: "2 أمبير" }, { label: "الاتصال", value: "Zigbee 3.0، Wi-Fi 2.4GHz" }] },
      },
      {
        slug: "garage", name: "Syltra GARAGE", tags: ["Zigbee", "Wi-Fi"],
        en: { tagline: "Know the door is closed, from anywhere.", description: "A garage door module that opens, closes and confirms status straight from the app, the peace of mind of checking the garage without walking back to it.", specs: [{ label: "Function", value: "Open / close / status" }, { label: "Power", value: "100–240V~, 50/60Hz" }, { label: "Max load", value: "5A" }, { label: "Connectivity", value: "Zigbee 3.0, Wi-Fi 2.4GHz" }] },
        ar: { tagline: "اطمئن أن الباب مغلق، من أي مكان.", description: "وحدة تحكم بباب الكراج تفتح وتغلق وتؤكد الحالة مباشرة من التطبيق, راحة بال التأكد من الكراج دون الرجوع إليه.", specs: [{ label: "الوظيفة", value: "فتح / إغلاق / تأكيد الحالة" }, { label: "الطاقة", value: "100–240V~, 50/60Hz" }, { label: "أقصى حمل", value: "5 أمبير" }, { label: "الاتصال", value: "Zigbee 3.0، Wi-Fi 2.4GHz" }] },
      },
      {
        slug: "air", name: "Syltra AIR", tags: ["Wi-Fi", "BLE"],
        en: { tagline: "Any air conditioner, one app.", description: "A universal infrared module that brings app and voice control to virtually any air conditioner already installed, no need to replace the unit to make it smart.", specs: [{ label: "Function", value: "Universal IR control" }, { label: "Power", value: "100–240V~, 50/60Hz" }, { label: "IR frequency", value: "38KHz" }, { label: "Connectivity", value: "Wi-Fi 2.4GHz, Bluetooth LE" }] },
        ar: { tagline: "أي مكيف، بتطبيق واحد.", description: "وحدة تحكم شاملة بالأشعة تحت الحمراء تمنح أي مكيف مُركّب بالفعل تحكمًا بالتطبيق والصوت, دون الحاجة لاستبدال الجهاز نفسه.", specs: [{ label: "الوظيفة", value: "تحكم شامل بالأشعة تحت الحمراء" }, { label: "الطاقة", value: "100–240V~, 50/60Hz" }, { label: "تردد الأشعة", value: "38 كيلوهرتز" }, { label: "الاتصال", value: "Wi-Fi 2.4GHz، بلوتوث LE" }] },
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
        slug: "lock", name: "Syltra Lock", tags: ["BLE", "App"],
        en: { tagline: "The everyday smart lock.", description: "Fingerprint and PIN entry with full app control, the lock most households reach for first, built to feel as fast as a key and as secure as a vault.", specs: [{ label: "Entry methods", value: "Fingerprint, PIN" }, { label: "App control", value: "Unlock, lock, access log" }, { label: "Connectivity", value: "Bluetooth LE" }, { label: "Alerts", value: "Real-time, on every entry" }] },
        ar: { tagline: "القفل الذكي اليومي.", description: "دخول بالبصمة والرقم السري مع تحكم كامل عبر التطبيق, القفل الذي تلجأ إليه أغلب المنازل أولًا، سريع كالمفتاح وآمن كالخزنة.", specs: [{ label: "طرق الدخول", value: "بصمة، رقم سري" }, { label: "تحكم التطبيق", value: "فتح، إغلاق، سجل الدخول" }, { label: "الاتصال", value: "بلوتوث LE" }, { label: "التنبيهات", value: "فورية مع كل عملية دخول" }] },
      },
      {
        slug: "lock-pro", name: "Syltra Pro", tags: ["BLE", "App"],
        en: { tagline: "Keyless, and always in your pocket.", description: "App-first lock control built for households ready to leave the key behind entirely, keyless entry, remote access, and a shared log for family and guests.", specs: [{ label: "Entry methods", value: "App, keyless" }, { label: "App control", value: "Remote unlock, guest access" }, { label: "Connectivity", value: "Bluetooth LE" }, { label: "Best for", value: "Everyday households" }] },
        ar: { tagline: "بلا مفتاح، ودائمًا في جيبك.", description: "تحكم كامل بالتطبيق للمنازل المستعدة للاستغناء عن المفتاح تمامًا, دخول بدون مفتاح، وتحكم عن بُعد، وسجل مشترك للعائلة والضيوف.", specs: [{ label: "طرق الدخول", value: "تطبيق، بدون مفتاح" }, { label: "تحكم التطبيق", value: "فتح عن بُعد، دخول للضيوف" }, { label: "الاتصال", value: "بلوتوث LE" }, { label: "الأنسب لـ", value: "الاستخدام المنزلي اليومي" }] },
      },
      {
        slug: "lock-elite", name: "Syltra Elite", tags: ["NFC", "BLE", "App"],
        en: { tagline: "Every entry method, one lock.", description: "Fingerprint, face, PIN and NFC card in a single premium lock, for a household that wants every option covered and never wants to be locked out.", specs: [{ label: "Entry methods", value: "Fingerprint, face, PIN, NFC card" }, { label: "App control", value: "Full remote management" }, { label: "Connectivity", value: "NFC, Bluetooth LE" }, { label: "Finish", value: "Premium metal" }] },
        ar: { tagline: "كل طرق الدخول، في قفل واحد.", description: "بصمة ووجه ورقم سري وبطاقة NFC في قفل فاخر واحد, لمن يريد كل الخيارات مغطاة ولا يريد أن يُحرم من الدخول أبدًا.", specs: [{ label: "طرق الدخول", value: "بصمة، وجه، رقم سري، بطاقة NFC" }, { label: "تحكم التطبيق", value: "إدارة كاملة عن بُعد" }, { label: "الاتصال", value: "NFC، بلوتوث LE" }, { label: "الخامة", value: "معدن فاخر" }] },
      },
      {
        slug: "lock-bolt", name: "Syltra Bolt", tags: ["BLE", "App"],
        en: { tagline: "Built for offices and rentals.", description: "A retrofit deadbolt lock designed for offices and rental units, install over the existing bolt, manage access by tenant or shift, no locksmith required.", specs: [{ label: "Type", value: "Retrofit deadbolt" }, { label: "Best for", value: "Offices, rental units" }, { label: "App control", value: "Per-tenant access codes" }, { label: "Connectivity", value: "Bluetooth LE" }] },
        ar: { tagline: "مصمم للمكاتب والوحدات المؤجرة.", description: "قفل ترقية يُركّب فوق القفل الحالي, مناسب للمكاتب والوحدات المؤجرة، مع إدارة صلاحيات الدخول لكل مستأجر أو وردية دون الحاجة لفني أقفال.", specs: [{ label: "النوع", value: "قفل ترقية للباب الحالي" }, { label: "الأنسب لـ", value: "المكاتب والوحدات المؤجرة" }, { label: "تحكم التطبيق", value: "رموز دخول لكل مستأجر" }, { label: "الاتصال", value: "بلوتوث LE" }] },
      },
      {
        slug: "cam", name: "Syltra Cam", tags: ["Wi-Fi"],
        en: { tagline: "AI on the device, not in someone else's cloud.", description: "A 4K camera with on-device AI detection, people, vehicles and packages recognized locally, so footage only leaves the house if you choose to share it.", specs: [{ label: "Resolution", value: "4K" }, { label: "Detection", value: "On-device AI, person, vehicle, package" }, { label: "Connectivity", value: "Wi-Fi 2.4GHz" }, { label: "Storage", value: "Local and optional cloud" }] },
        ar: { tagline: "ذكاء اصطناعي على الجهاز، لا في سحابة أحد آخر.", description: "كاميرا بدقة 4K مع كشف ذكاء اصطناعي محلي, تتعرف على الأشخاص والمركبات والطرود محليًا، فلا تغادر اللقطات المنزل إلا إذا اخترت مشاركتها.", specs: [{ label: "الدقة", value: "4K" }, { label: "الكشف", value: "ذكاء اصطناعي محلي, أشخاص، مركبات، طرود" }, { label: "الاتصال", value: "Wi-Fi 2.4GHz" }, { label: "التخزين", value: "محلي، مع خيار سحابي" }] },
      },
      {
        slug: "doorbell", name: "Syltra Doorbell", tags: ["Wi-Fi"],
        en: { tagline: "See who's there, before you open the door.", description: "An HD video doorbell with instant alerts and two-way talk, answer the door from across the world, or just from the couch.", specs: [{ label: "Video", value: "HD, night vision" }, { label: "Audio", value: "Two-way talk" }, { label: "Alerts", value: "Instant, on motion or press" }, { label: "Connectivity", value: "Wi-Fi 2.4GHz" }] },
        ar: { tagline: "اعرف من بالباب، قبل أن تفتحه.", description: "جرس باب بفيديو عالي الدقة مع تنبيهات فورية ومحادثة مباشرة, رد على الباب من أي مكان في العالم، أو ببساطة من الأريكة.", specs: [{ label: "الفيديو", value: "دقة عالية، رؤية ليلية" }, { label: "الصوت", value: "محادثة ثنائية الاتجاه" }, { label: "التنبيهات", value: "فورية عند الحركة أو الضغط" }, { label: "الاتصال", value: "Wi-Fi 2.4GHz" }] },
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
        en: { tagline: "Knows a room is occupied before you flip a switch.", description: "A PIR motion sensor that triggers lighting and security scenes the instant someone enters a room, no more walking into the dark, no more lights left on empty rooms.", specs: [{ label: "Detection", value: "PIR, wide-angle" }, { label: "Battery life", value: "Up to 2 years" }, { label: "Connectivity", value: "Zigbee 3.0" }] },
        ar: { tagline: "تعرف أن الغرفة مشغولة قبل أن تلمس المفتاح.", description: "حساس حركة PIR يشغّل الإضاءة ومشاهد الأمان لحظة دخول أي شخص للغرفة, لا مزيد من الدخول إلى الظلام، ولا مزيد من الأنوار المتروكة في غرف فارغة.", specs: [{ label: "الكشف", value: "PIR، زاوية واسعة" }, { label: "عمر البطارية", value: "حتى سنتين" }, { label: "الاتصال", value: "Zigbee 3.0" }] },
      },
      {
        slug: "door-window", name: "Syltra Door / Window Sensor", tags: ["Zigbee"],
        en: { tagline: "Knows the instant it opens.", description: "A slim magnetic contact sensor for doors and windows, instant alerts on opening, and the automation trigger behind countless Syltra scenes.", specs: [{ label: "Detection", value: "Magnetic reed contact" }, { label: "Battery life", value: "Up to 2 years" }, { label: "Connectivity", value: "Zigbee 3.0" }] },
        ar: { tagline: "تعرف اللحظة التي يُفتح فيها.", description: "حساس مغناطيسي رفيع للأبواب والنوافذ, تنبيه فوري عند الفتح، وهو المحفّز وراء عدد كبير من مشاهد سيلترا.", specs: [{ label: "الكشف", value: "تلامس مغناطيسي" }, { label: "عمر البطارية", value: "حتى سنتين" }, { label: "الاتصال", value: "Zigbee 3.0" }] },
      },
      {
        slug: "climate", name: "Syltra Temperature & Humidity Sensor", tags: ["Zigbee"],
        en: { tagline: "Room-by-room, not house-wide.", description: "A precise temperature and humidity sensor for automations that actually adapt to each room, not a single reading averaged across the whole house.", specs: [{ label: "Temperature accuracy", value: "±0.5°C" }, { label: "Humidity", value: "0–100% RH" }, { label: "Battery life", value: "Up to 2 years" }, { label: "Connectivity", value: "Zigbee 3.0" }] },
        ar: { tagline: "لكل غرفة على حدة، لا للمنزل كله.", description: "حساس دقيق لدرجة الحرارة والرطوبة يجعل الأتمتة تتكيف فعليًا مع كل غرفة، بدل قراءة واحدة متوسطة للمنزل بأكمله.", specs: [{ label: "دقة الحرارة", value: "±0.5°م" }, { label: "الرطوبة", value: "0–100%" }, { label: "عمر البطارية", value: "حتى سنتين" }, { label: "الاتصال", value: "Zigbee 3.0" }] },
      },
      {
        slug: "light-sensor", name: "Syltra Light Sensor", tags: ["Zigbee"],
        en: { tagline: "Reads the light, so scenes react to it.", description: "An ambient light sensor that triggers shades and lighting at the right moment, closing curtains at noon glare, or bringing lights up as the sun sets.", specs: [{ label: "Detection", value: "Ambient lux level" }, { label: "Battery life", value: "Up to 2 years" }, { label: "Connectivity", value: "Zigbee 3.0" }] },
        ar: { tagline: "تقيس الضوء، فتتفاعل المشاهد معه.", description: "حساس إضاءة محيطة يشغّل الستائر والأنوار في التوقيت المناسب, إغلاق الستائر عند وهج الظهيرة، أو رفع إضاءة الغرفة مع غروب الشمس.", specs: [{ label: "الكشف", value: "مستوى الإضاءة المحيطة" }, { label: "عمر البطارية", value: "حتى سنتين" }, { label: "الاتصال", value: "Zigbee 3.0" }] },
      },
      {
        slug: "smoke", name: "Syltra Smoke Sensor", tags: ["Zigbee"],
        en: { tagline: "Early warning, straight to your phone.", description: "A photoelectric smoke sensor with an instant phone alert, the kind of early warning that matters most when no one's home to hear the alarm.", specs: [{ label: "Detection", value: "Photoelectric" }, { label: "Alert", value: "Local siren + instant push alert" }, { label: "Connectivity", value: "Zigbee 3.0" }] },
        ar: { tagline: "إنذار مبكر، مباشرة على هاتفك.", description: "حساس دخان ضوئي مع تنبيه فوري على الهاتف, الإنذار المبكر الذي يهم أكثر عندما لا يكون أحد في المنزل ليسمع الجرس.", specs: [{ label: "الكشف", value: "ضوئي" }, { label: "التنبيه", value: "صفارة محلية + إشعار فوري" }, { label: "الاتصال", value: "Zigbee 3.0" }] },
      },
      {
        slug: "gas", name: "Syltra Gas Sensor", tags: ["Zigbee"],
        en: { tagline: "Catches a leak before it becomes a hazard.", description: "A combustible gas sensor for the kitchen or utility room, detects a leak early and can trigger a scene that shuts the gas valve and alerts everyone in the house.", specs: [{ label: "Detection", value: "Combustible gas" }, { label: "Alert", value: "Local siren + instant push alert" }, { label: "Connectivity", value: "Zigbee 3.0" }] },
        ar: { tagline: "يكتشف التسرب قبل أن يتحول إلى خطر.", description: "حساس غاز قابل للاشتعال للمطبخ أو غرفة المرافق, يكتشف التسرب مبكرًا، ويمكن ربطه بمشهد يغلق صمام الغاز وينبّه كل من في المنزل.", specs: [{ label: "الكشف", value: "غاز قابل للاشتعال" }, { label: "التنبيه", value: "صفارة محلية + إشعار فوري" }, { label: "الاتصال", value: "Zigbee 3.0" }] },
      },
      {
        slug: "water-leak", name: "Syltra Water Leak Sensor", tags: ["Zigbee"],
        en: { tagline: "Catches the drip before it's a flood.", description: "A compact leak sensor placed under a sink or beside a water heater, catches the first drop, not the flood that follows a night unnoticed.", specs: [{ label: "Detection", value: "Water contact probes" }, { label: "Battery life", value: "Up to 2 years" }, { label: "Connectivity", value: "Zigbee 3.0" }] },
        ar: { tagline: "يكتشف القطرة الأولى، قبل أن تصبح فيضانًا.", description: "حساس تسرب مياه مدمج يُوضع أسفل الحوض أو بجانب السخان, يكتشف أول قطرة، لا الفيضان الذي يتبعها بعد ليلة لم يلاحظها أحد.", specs: [{ label: "الكشف", value: "أطراف تلامس مائية" }, { label: "عمر البطارية", value: "حتى سنتين" }, { label: "الاتصال", value: "Zigbee 3.0" }] },
      },
      {
        slug: "air-quality", name: "Syltra Air Quality Sensor", tags: ["Zigbee", "Wi-Fi"],
        en: { tagline: "A live number for the air you're breathing.", description: "A live AQI reading that ties directly into ventilation and AC scenes, when the air quality drops, the house can respond before anyone feels it.", specs: [{ label: "Reading", value: "Live AQI" }, { label: "Automation", value: "Triggers ventilation & AC scenes" }, { label: "Connectivity", value: "Zigbee 3.0, Wi-Fi 2.4GHz" }] },
        ar: { tagline: "رقم حي للهواء الذي تتنفسه.", description: "قراءة حية لمؤشر جودة الهواء ترتبط مباشرة بمشاهد التهوية والتكييف, عندما تنخفض جودة الهواء، يستجيب المنزل قبل أن يشعر أحد بذلك.", specs: [{ label: "القراءة", value: "مؤشر جودة الهواء الحي" }, { label: "الأتمتة", value: "يفعّل مشاهد التهوية والتكييف" }, { label: "الاتصال", value: "Zigbee 3.0، Wi-Fi 2.4GHz" }] },
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
        en: { tagline: "Learns the household's rhythm.", description: "An adaptive thermostat that studies the household's daily rhythm and adjusts ahead of it, comfortable when you're home, efficient when you're not.", specs: [{ label: "Control", value: "Adaptive scheduling" }, { label: "Display", value: "Live temperature readout" }, { label: "Connectivity", value: "Zigbee 3.0, Wi-Fi 2.4GHz" }] },
        ar: { tagline: "يتعلم إيقاع المنزل اليومي.", description: "منظم حرارة تكيّفي يدرس الروتين اليومي للمنزل ويستبق التعديل قبل الحاجة إليه, مريح عندما تكون في المنزل، وموفّر عندما تكون خارجه.", specs: [{ label: "التحكم", value: "جدولة تكيّفية" }, { label: "الشاشة", value: "عرض حي لدرجة الحرارة" }, { label: "الاتصال", value: "Zigbee 3.0، Wi-Fi 2.4GHz" }] },
      },
      {
        slug: "ac-control", name: "Syltra AC Control", tags: ["Wi-Fi", "BLE"],
        en: { tagline: "One panel, any air conditioner.", description: "Universal control for any split or central AC unit, from the app or a dedicated wall panel, schedules, energy reports and remote control in one place.", specs: [{ label: "Compatibility", value: "Any split or central AC" }, { label: "Control", value: "App + wall panel" }, { label: "Reporting", value: "Energy consumption reports" }, { label: "Connectivity", value: "Wi-Fi 2.4GHz, Bluetooth LE" }] },
        ar: { tagline: "لوحة واحدة، لأي مكيف.", description: "تحكم شامل لأي مكيف سبليت أو مركزي، من التطبيق أو لوحة حائط مخصصة, جداول تشغيل وتقارير استهلاك وتحكم عن بُعد في مكان واحد.", specs: [{ label: "التوافق", value: "أي مكيف سبليت أو مركزي" }, { label: "التحكم", value: "تطبيق + لوحة حائط" }, { label: "التقارير", value: "تقارير استهلاك الطاقة" }, { label: "الاتصال", value: "Wi-Fi 2.4GHz، بلوتوث LE" }] },
      },
      {
        slug: "plug", name: "Syltra Plug", tags: ["Wi-Fi"],
        en: { tagline: "Turns any appliance into a scheduled one.", description: "A smart plug that turns any appliance into a scheduled, remote-controlled device, with live energy monitoring for the ones worth watching.", specs: [{ label: "Max load", value: "16A" }, { label: "Monitoring", value: "Live energy usage" }, { label: "Connectivity", value: "Wi-Fi 2.4GHz" }] },
        ar: { tagline: "يحوّل أي جهاز إلى جهاز مجدول.", description: "مقبس ذكي يحوّل أي جهاز كهربائي إلى جهاز مجدول ويُتحكم فيه عن بُعد, مع مراقبة حية لاستهلاك الطاقة للأجهزة التي تستحق المتابعة.", specs: [{ label: "أقصى حمل", value: "16 أمبير" }, { label: "المراقبة", value: "استهلاك طاقة حي" }, { label: "الاتصال", value: "Wi-Fi 2.4GHz" }] },
      },
      {
        slug: "light", name: "Syltra Light", tags: ["Zigbee"],
        en: { tagline: "Every fixture, scene-ready.", description: "A tunable smart bulb for every fixture in the house, warm to cool white, dimmable, and ready to join any scene without an extra hub.", specs: [{ label: "Tuning", value: "Warm to cool white, dimmable" }, { label: "Fitting", value: "Standard screw / bayonet" }, { label: "Connectivity", value: "Zigbee 3.0" }] },
        ar: { tagline: "كل تجهيزة، جاهزة للمشاهد.", description: "مصباح ذكي قابل للتعديل لكل تجهيزة في المنزل, من الأبيض الدافئ إلى البارد، قابل للتعتيم، وجاهز للانضمام لأي مشهد دون مركز إضافي.", specs: [{ label: "التعديل", value: "أبيض دافئ إلى بارد، قابل للتعتيم" }, { label: "التركيب", value: "قاعدة قياسية" }, { label: "الاتصال", value: "Zigbee 3.0" }] },
      },
      {
        slug: "curtain", name: "Syltra Curtain", tags: ["Zigbee", "Wi-Fi"],
        en: { tagline: "Silent, scheduled, and quiet about it.", description: "A silent motorized curtain track for light and privacy on schedule, quiet enough not to wake anyone at sunrise.", specs: [{ label: "Noise level", value: "Under 45dB" }, { label: "Function", value: "Open / Stop / Close, scheduled" }, { label: "Connectivity", value: "Zigbee 3.0, Wi-Fi 2.4GHz" }] },
        ar: { tagline: "صامتة، مجدولة، وهادئة في عملها.", description: "سكة ستائر كهربائية صامتة للتحكم في الضوء والخصوصية حسب الجدول, هادئة بما يكفي ألا توقظ أحدًا عند شروق الشمس.", specs: [{ label: "مستوى الضجيج", value: "أقل من 45 ديسيبل" }, { label: "الوظيفة", value: "فتح / إيقاف / إغلاق مجدول" }, { label: "الاتصال", value: "Zigbee 3.0، Wi-Fi 2.4GHz" }] },
      },
      {
        slug: "robot", name: "Syltra Robot", tags: ["Wi-Fi"],
        en: { tagline: "Maps the home, then cleans it on schedule.", description: "A robot vacuum that maps the home room by room and runs on a schedule, from the same app that runs the lights and the locks.", specs: [{ label: "Mapping", value: "Room-by-room, saved maps" }, { label: "Scheduling", value: "Per-room or whole-home" }, { label: "Connectivity", value: "Wi-Fi 2.4GHz" }] },
        ar: { tagline: "تُخطط المنزل، ثم تنظفه حسب الجدول.", description: "مكنسة روبوت تُخطط المنزل غرفة تلو الأخرى وتعمل حسب جدول محدد, من نفس التطبيق الذي يدير الأنوار والأقفال.", specs: [{ label: "التخطيط", value: "غرفة بغرفة، خرائط محفوظة" }, { label: "الجدولة", value: "لكل غرفة أو للمنزل كله" }, { label: "الاتصال", value: "Wi-Fi 2.4GHz" }] },
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
