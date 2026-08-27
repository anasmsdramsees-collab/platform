import type { Locale } from "@/lib/i18n/config";

interface Bi {
  ar: string;
  en: string;
}
interface Section {
  h?: Bi; // optional heading
  p: Bi[]; // paragraphs
}
export interface Post {
  slug: string;
  division: string; // division key or "one"
  date: string; // ISO
  title: Bi;
  excerpt: Bi;
  keywords: string[];
  body: Section[];
}

export function bt(v: Bi, locale: Locale) {
  return locale === "ar" ? v.ar : v.en;
}

export const POSTS: Post[] = [
  {
    slug: "how-to-choose-ac-system-saudi",
    division: "climate",
    date: "2026-08-27",
    title: {
      ar: "كيف تختار نظام التكييف المناسب لمبناك في السعودية؟",
      en: "How to choose the right AC system for your building in Saudi Arabia",
    },
    excerpt: {
      ar: "مركزي أم VRF أم سبليت؟ دليل عملي يساعدك على اختيار نظام التكييف الأنسب لمساحتك وميزانيتك ومناخ المملكة.",
      en: "Central, VRF or split? A practical guide to choosing the AC system that fits your space, budget and the Kingdom's climate.",
    },
    keywords: ["تكييف مركزي", "VRF", "اختيار نظام التكييف", "تكييف السعودية", "central AC", "VRF Saudi Arabia"],
    body: [
      {
        p: [
          {
            ar: "في مناخ تتجاوز فيه الحرارة الأربعين درجة أشهرًا طويلة، لا يكون التكييف رفاهية بل ضرورة تشغيلية. لكن اختيار النظام الخطأ يعني فاتورة أعلى وراحة أقل وصيانة أكثر. في هذا الدليل نبسّط الفروق بين الأنظمة الثلاثة الأكثر شيوعًا حتى تقرّر بثقة.",
            en: "In a climate that stays above 40°C for long months, air conditioning is not a luxury but an operational necessity. Choosing the wrong system means a higher bill, less comfort and more maintenance. This guide simplifies the differences between the three most common systems so you can decide with confidence.",
          },
        ],
      },
      {
        h: { ar: "التكييف المركزي (الشيلر)", en: "Central (chiller) systems" },
        p: [
          {
            ar: "الأنسب للمباني الكبيرة كالأبراج والمولات والفنادق. يوفّر تبريدًا موحّدًا يُدار من مكان واحد بكفاءة عالية عند التشغيل الكامل. يحتاج مساحة للمعدات ودراسة هندسية دقيقة، لكنه الأوفر على المدى الطويل للمساحات الشاسعة.",
            en: "Best for large buildings such as towers, malls and hotels. It delivers unified cooling managed from one place, highly efficient at full load. It needs equipment space and careful engineering, but it's the most economical long-term choice for vast areas.",
          },
        ],
      },
      {
        h: { ar: "أنظمة VRF/VRV", en: "VRF/VRV systems" },
        p: [
          {
            ar: "الخيار المرن للمكاتب والفلل والمباني متعددة الاستخدامات. تخدم وحدة خارجية واحدة عدة وحدات داخلية، وكل منطقة تُضبط بدرجة حرارتها المستقلة. يعدّل النظام استهلاكه حسب الحمل الفعلي، ما يحقّق توفيرًا ملحوظًا في الطاقة.",
            en: "The flexible choice for offices, villas and mixed-use buildings. One outdoor unit serves several indoor units, and each zone holds its own temperature. The system adjusts consumption to the actual load, delivering noticeable energy savings.",
          },
        ],
      },
      {
        h: { ar: "أنظمة السبليت", en: "Split systems" },
        p: [
          {
            ar: "الحل العملي والاقتصادي للغرف والوحدات الصغيرة والإضافات. تركيب سريع وصيانة سهلة، مع موديلات إنفرتر موفّرة للطاقة. أقل كفاءة من الأنظمة الكبيرة عند التغطية الواسعة، لكنه مثالي للمساحات المحدودة.",
            en: "The practical, economical solution for rooms, small units and additions. Quick installation and easy maintenance, with energy-saving inverter models. Less efficient than larger systems across wide coverage, but ideal for limited spaces.",
          },
        ],
      },
      {
        h: { ar: "القاعدة الذهبية: ابدأ بدراسة الحمل الحراري", en: "The golden rule: start with a heat-load study" },
        p: [
          {
            ar: "أيًّا كان النظام، القرار الصحيح يبدأ بحساب دقيق للأحمال الحرارية لمساحتك. نظام أكبر من اللازم يهدر الطاقة، وأصغر من اللازم لا يبرّد جيدًا ويتعطّل أسرع. لهذا نبدأ في سيلترا كلايمت دائمًا بالدراسة قبل التوصية.",
            en: "Whatever the system, the right decision starts with an accurate heat-load calculation for your space. An oversized system wastes energy; an undersized one won't cool well and fails sooner. That's why at Syltra Climate we always start with the study before recommending.",
          },
          {
            ar: "هل تريد مساعدة في اختيار النظام الأنسب لمشروعك؟ ابدأ بمعاينة موقع مجانية ودعنا نجهّز لك عرضًا واضحًا.",
            en: "Want help choosing the right system for your project? Start with a site survey and let us prepare a clear proposal.",
          },
        ],
      },
    ],
  },

  {
    slug: "mrl-vs-mr-elevator-guide",
    division: "glide",
    date: "2026-08-27",
    title: {
      ar: "دليل اختيار المصعد: MRL أم MR، وما الذي يناسب مبناك؟",
      en: "Choosing an elevator: MRL or MR, and what fits your building",
    },
    excerpt: {
      ar: "الفرق بين المصاعد بغرفة ماكينة وبدونها، ومتى تختار كلًّا منهما، وما يجب معرفته قبل شراء مصعد في السعودية.",
      en: "The difference between machine-room and machine-room-less lifts, when to choose each, and what to know before buying an elevator in Saudi Arabia.",
    },
    keywords: ["مصاعد", "MRL", "غرفة ماكينة", "مصعد فيلا", "اختيار مصعد", "elevator Saudi Arabia", "home lift"],
    body: [
      {
        p: [
          {
            ar: "المصعد استثمار طويل الأمد يرفع قيمة المبنى ويخدم ساكنيه لعقود. لكن السوق مليء بالخيارات والمصطلحات التي قد تربك المشتري. نوضّح هنا أهم قرار تقني: هل تحتاج مصعدًا بغرفة ماكينة أم بدونها؟",
            en: "An elevator is a long-term investment that raises a building's value and serves its occupants for decades. But the market is full of options and jargon that can confuse buyers. Here we clarify the key technical decision: do you need a machine-room or a machine-room-less lift?",
          },
        ],
      },
      {
        h: { ar: "المصعد بدون غرفة ماكينة (MRL)", en: "Machine-room-less (MRL)" },
        p: [
          {
            ar: "يضع المحرّك داخل بئر المصعد نفسه، فيوفّر مساحة غرفة الماكينة على السطح. الأنسب للمباني الحديثة التي تريد استغلال كل متر، ويستهلك طاقة أقل عادة. مثالي للعمارات السكنية والمكاتب متوسطة الارتفاع.",
            en: "Places the motor inside the shaft itself, saving the rooftop machine-room space. Best for modern buildings that want to use every meter, and it usually consumes less energy. Ideal for residential blocks and mid-rise offices.",
          },
        ],
      },
      {
        h: { ar: "المصعد بغرفة ماكينة (MR)", en: "Machine-room (MR)" },
        p: [
          {
            ar: "يضع المعدات في غرفة مستقلة، ويتحمّل عادة أحمالًا وسرعات أعلى، وصيانته قد تكون أسهل في بعض الحالات. الأنسب للمباني العالية والمستشفيات والاستخدامات الثقيلة التي تتطلّب أداءً عاليًا مستمرًا.",
            en: "Places the equipment in a separate room, usually handles higher loads and speeds, and can be easier to service in some cases. Best for high-rise buildings, hospitals and heavy-duty uses that demand continuous high performance.",
          },
        ],
      },
      {
        h: { ar: "قبل أن تشتري: أسئلة أساسية", en: "Before you buy: essential questions" },
        p: [
          {
            ar: "كم عدد الطوابق والوقفات؟ ما الحمولة وعدد الركاب المتوقّع في الساعة؟ ما أبعاد البئر المتاحة؟ هل النظام مطابق لمواصفات السلامة المعتمدة (SASO)؟ وهل تشمل الصفقة قطع غيار أصلية وعقد صيانة واستجابة طوارئ؟ الإجابات تحدّد النظام الأنسب.",
            en: "How many floors and stops? What load and how many passengers per hour? What are the available shaft dimensions? Is the system compliant with approved safety standards (SASO)? And does the deal include genuine parts, a maintenance contract and emergency response? The answers define the right system.",
          },
          {
            ar: "في سيلترا جلايد نبدأ بمعاينة ودراسة فنية تحدّد لك الخيار الأمثل بلا مبالغة في المواصفات ولا نقص فيها. تواصل معنا لدراسة مشروعك.",
            en: "At Syltra Glide we start with a survey and technical study that identifies the optimal option — neither over- nor under-specified. Contact us to study your project.",
          },
        ],
      },
    ],
  },

  {
    slug: "civil-defense-fire-security-requirements",
    division: "shield",
    date: "2026-08-27",
    title: {
      ar: "متطلبات الدفاع المدني لأنظمة الحريق والمراقبة في السعودية",
      en: "Civil Defense requirements for fire and surveillance systems in Saudi Arabia",
    },
    excerpt: {
      ar: "ما الذي يطلبه الدفاع المدني ووزارة الداخلية لاعتماد أنظمة الحريق والكاميرات، وكيف تضمن مطابقة منشأتك.",
      en: "What Civil Defense and the Ministry of Interior require to approve fire and camera systems, and how to ensure your facility complies.",
    },
    keywords: ["الدفاع المدني", "أنظمة الحريق", "كاميرات مراقبة", "FM200", "اشتراطات السلامة", "civil defense Saudi Arabia", "fire alarm"],
    body: [
      {
        p: [
          {
            ar: "الحصول على شهادة السلامة من الدفاع المدني شرط أساسي لتشغيل أي منشأة تجارية أو صناعية في المملكة. تأخير أو رفض الاعتماد قد يوقف المشروع بالكامل. نستعرض هنا أهم المتطلبات وكيف تتجنّب الأخطاء الشائعة.",
            en: "Obtaining a Civil Defense safety certificate is a prerequisite for operating any commercial or industrial facility in the Kingdom. A delay or rejection can halt the whole project. Here we review the key requirements and how to avoid common mistakes.",
          },
        ],
      },
      {
        h: { ar: "أنظمة الحريق: الكشف والإنذار والمكافحة", en: "Fire systems: detection, alarm and suppression" },
        p: [
          {
            ar: "يشترط الدفاع المدني منظومة متكاملة تناسب طبيعة المبنى ومخاطره: كواشف دخان وحرارة، لوحة إنذار مركزية، وسائل مكافحة (رشّاشات أو أنظمة غاز مثل FM200 للمناطق الحسّاسة)، ومخارج ومسارات إخلاء واضحة. يجب أن تكون المعدات معتمدة والمخطّطات مصدّقة.",
            en: "Civil Defense requires an integrated system matched to the building's nature and risks: smoke and heat detectors, a central alarm panel, suppression means (sprinklers or gas systems such as FM200 for sensitive areas), and clear exits and evacuation routes. Equipment must be certified and drawings approved.",
          },
        ],
      },
      {
        h: { ar: "أنظمة المراقبة: مطابقة اشتراطات وزارة الداخلية", en: "Surveillance: Ministry of Interior compliance" },
        p: [
          {
            ar: "كاميرات المراقبة في المنشآت تخضع لاشتراطات وزارة الداخلية من حيث الدقة ومدة التخزين وتغطية النقاط الحسّاسة. التركيب غير المطابق قد يعرّضك للمخالفة، لذا يجب اختيار كاميرات معتمدة وتصميم تغطية بلا نقاط عمياء.",
            en: "Facility surveillance cameras are subject to Ministry of Interior requirements for resolution, storage duration and coverage of sensitive points. Non-compliant installation can expose you to penalties, so choose approved cameras and design coverage with no blind spots.",
          },
        ],
      },
      {
        h: { ar: "الخلاصة: صمّم للمطابقة من البداية", en: "Bottom line: design for compliance from the start" },
        p: [
          {
            ar: "أكبر خطأ هو معالجة السلامة كخطوة أخيرة. المطابقة تبدأ من التصميم: مخطّطات صحيحة، معدات معتمدة، تنفيذ بإشراف هندسي، وتوثيق كامل. في سيلترا شيلد نتولّى ذلك من التصميم حتى الحصول على الاعتماد والصيانة.",
            en: "The biggest mistake is treating safety as a last step. Compliance starts at design: correct drawings, certified equipment, supervised execution and full documentation. At Syltra Shield we handle this from design through approval and maintenance.",
          },
        ],
      },
    ],
  },

  {
    slug: "erp-ready-vs-custom",
    division: "os",
    date: "2026-08-27",
    title: {
      ar: "ERP جاهز أم نظام مخصّص؟ كيف تتّخذ القرار الصحيح",
      en: "Ready ERP or a custom system? How to make the right decision",
    },
    excerpt: {
      ar: "متى يكفيك نظام ERP جاهز بالاشتراك، ومتى تحتاج نظامًا مبنيًا على مقاسك، وكيف توازن بين السرعة والتخصيص.",
      en: "When a ready subscription ERP is enough, when you need a system built to fit, and how to balance speed against customization.",
    },
    keywords: ["ERP", "نظام مخصّص", "برمجيات إدارة", "SaaS", "تحول رقمي", "ERP Saudi Arabia", "custom software"],
    body: [
      {
        p: [
          {
            ar: "مع تسارع التحوّل الرقمي في المملكة، صار سؤال «نظام جاهز أم مخصّص؟» يواجه كل مؤسسة تريد تنظيم أعمالها. لا توجد إجابة واحدة، بل قرار يعتمد على طبيعة عملك ومدى تفرّد إجراءاتك.",
            en: "As digital transformation accelerates in the Kingdom, the question 'ready or custom?' faces every organization looking to organize its operations. There's no single answer — it's a decision that depends on your business and how unique your processes are.",
          },
        ],
      },
      {
        h: { ar: "متى يكفيك نظام جاهز؟", en: "When is a ready system enough?" },
        p: [
          {
            ar: "إذا كانت إجراءاتك قياسية إلى حد كبير (محاسبة، مخزون، مبيعات، موارد بشرية)، فنظام ERP جاهز بالاشتراك مثل سيلترا ERP يوفّر عليك الوقت والتكلفة، ويبدأ العمل خلال أيام لا أشهر، مع إمكانية تخصيص محدود.",
            en: "If your processes are largely standard (accounting, inventory, sales, HR), a ready subscription ERP like Syltra ERP saves time and cost, goes live in days not months, and allows limited customization.",
          },
        ],
      },
      {
        h: { ar: "متى تحتاج نظامًا مخصّصًا؟", en: "When do you need a custom system?" },
        p: [
          {
            ar: "حين تكون لديك إجراءات فريدة تمنحك ميزة تنافسية، أو تحتاج تكاملًا خاصًا مع أنظمة قائمة، أو حين يفرض عليك النظام الجاهز طريقة عمل لا تناسبك. النظام المخصّص يعكس سير عملك الحقيقي، لكنه يتطلّب وقتًا واستثمارًا أكبر.",
            en: "When you have unique processes that give you an edge, need special integration with existing systems, or when a ready product forces a way of working that doesn't suit you. A custom system reflects your real workflow but takes more time and investment.",
          },
        ],
      },
      {
        h: { ar: "الطريق الوسط", en: "The middle path" },
        p: [
          {
            ar: "غالبًا يكون الحل الأمثل هو البدء بمنتج جاهز مع تخصيص الأجزاء الحرجة، أو بناء نظام مخصّص يتكامل مع أدوات جاهزة. في سيلترا او-إس نبدأ بجلسة اكتشاف نفهم فيها احتياجك الحقيقي قبل أن نوصي — لأن القرار الصحيح يوفّر عليك سنوات من الإحباط.",
            en: "Often the best solution is starting with a ready product and customizing the critical parts, or building a custom system that integrates with ready tools. At Syltra OS we start with a discovery session to understand your real need before recommending — because the right decision saves you years of frustration.",
          },
        ],
      },
    ],
  },

  {
    slug: "smart-home-saudi-where-to-start",
    division: "life",
    date: "2026-08-27",
    title: {
      ar: "المنزل الذكي في السعودية: من أين تبدأ وكيف تختار؟",
      en: "Smart homes in Saudi Arabia: where to start and how to choose",
    },
    excerpt: {
      ar: "دليل مبسّط للبدء بمنزلك الذكي: ما الذي يمكن أتمتته، هل يناسب منزلك القائم، وكيف تختار نظامًا يتوسّع معك.",
      en: "A simple guide to starting your smart home: what you can automate, whether it fits your existing home, and how to choose a system that grows with you.",
    },
    keywords: ["المنزل الذكي", "سمارت هوم", "أتمتة منزلية", "أقفال ذكية", "smart home Saudi Arabia", "home automation"],
    body: [
      {
        p: [
          {
            ar: "أصبح المنزل الذكي في متناول الجميع، لكن كثرة الأجهزة والأنظمة قد تربك من يريد البدء. المفتاح ليس شراء أكبر عدد من الأجهزة، بل بناء منظومة متكاملة تتكيّف مع أسلوب حياتك وتتوسّع مع احتياجك.",
            en: "Smart homes are now within everyone's reach, but the abundance of devices and systems can overwhelm anyone starting out. The key isn't buying the most gadgets, but building an integrated system that adapts to your lifestyle and grows with your needs.",
          },
        ],
      },
      {
        h: { ar: "ما الذي يمكن أتمتته؟", en: "What can you automate?" },
        p: [
          {
            ar: "الإضاءة والمشاهد، التكييف حسب الغرفة والوقت، الأمن والكاميرات والأقفال الذكية، الستائر، الصوت والترفيه، وحتى مراقبة استهلاك الطاقة. الأفضل أن تبدأ بما يهمّك أكثر (غالبًا الإضاءة والأمن) ثم تتوسّع.",
            en: "Lighting and scenes, climate by room and time, security with cameras and smart locks, curtains, audio and entertainment, and even energy monitoring. It's best to start with what matters most to you (often lighting and security), then expand.",
          },
        ],
      },
      {
        h: { ar: "هل يناسب منزلي القائم؟", en: "Does it fit my existing home?" },
        p: [
          {
            ar: "نعم. الحلول اللاسلكية الحديثة تُركّب في المنازل القائمة دون تكسير أو تعديلات هيكلية كبيرة، ويمكنك البدء بجزء والتوسّع لاحقًا. المهم اختيار منصّة مبنية على الانفتاح تتكامل مع المعايير الحديثة مثل Matter وThread.",
            en: "Yes. Modern wireless solutions retrofit into existing homes without major structural work, and you can start with part of it and expand later. The key is choosing an open platform that works with modern standards like Matter and Thread.",
          },
        ],
      },
      {
        h: { ar: "الأقفال الذكية: راحة وأمان", en: "Smart locks: comfort and security" },
        p: [
          {
            ar: "من أكثر ما يبدأ به الناس. القفل الذكي يفتح بالبصمة أو الرمز أو البطاقة أو التطبيق، ويعمل حتى بدون واي فاي، ويمنحك سجل دخول وصلاحيات مؤقتة للضيوف وتنبيهات فورية عند كل فتح.",
            en: "One of the most common starting points. A smart lock opens by fingerprint, code, card or app, works even without Wi-Fi, and gives you an entry log, temporary guest access and instant alerts on every unlock.",
          },
        ],
      },
      {
        h: { ar: "ابدأ بخطوة واحدة", en: "Start with one step" },
        p: [
          {
            ar: "لا تحتاج إلى أتمتة كل شيء دفعة واحدة. ابدأ بمنطقة واحدة، جرّب، ثم وسّع ضمن منظومة واحدة تنمو معك. في سيلترا لايف نساعدك على التخطيط من البداية حتى لا تندم على اختيارات مبكرة يصعب تغييرها.",
            en: "You don't need to automate everything at once. Start with one area, try it, then expand within one system that grows with you. At Syltra Life we help you plan from the start so you don't regret early choices that are hard to change.",
          },
        ],
      },
    ],
  },
];

export function postsForDivision(key: string) {
  return POSTS.filter((p) => p.division === key);
}
