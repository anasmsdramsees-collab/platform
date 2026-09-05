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

const ALL_POSTS: Post[] = [
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
  {
    slug: 'central-ac-cost-saudi', division: 'climate', date: '2026-08-26',
    title: { ar: 'تكلفة تركيب التكييف المركزي في السعودية: ما الذي يحدّد السعر؟', en: 'The cost of installing central AC in Saudi Arabia: what drives the price' },
    excerpt: { ar: 'لماذا تختلف أسعار التكييف المركزي، وما العوامل التي تحدّد التكلفة، وكيف توازن بين السعر والجودة على المدى الطويل.', en: 'Why central AC prices vary, what factors set the cost, and how to balance price against long-term value.' },
    keywords: ['تكلفة التكييف المركزي', 'سعر تركيب تكييف', 'تكييف السعودية', 'central AC cost'],
    body: [
      { p: [{ ar: 'سؤال «كم يكلّف؟» من أول ما يسأله كل صاحب مشروع، والإجابة الصادقة: يعتمد. سعر التكييف المركزي ليس رقمًا ثابتًا بل نتيجة عدة عوامل، وفهمها يحميك من العروض المضلّلة الرخيصة التي تكلّفك أكثر لاحقًا.', en: "'How much does it cost?' is the first question every project owner asks, and the honest answer is: it depends. Central AC pricing isn't a fixed number but the result of several factors, and understanding them protects you from misleadingly cheap offers that cost more later." }] },
      { h: { ar: 'العوامل التي تحدّد السعر', en: 'Factors that set the price' }, p: [{ ar: 'المساحة والحمل الحراري، نوع النظام (شيلر هوائي أو مائي)، جودة المعدات وكفاءتها، تعقيد شبكة الدكت والتوزيع، ومستوى التحكّم المطلوب. كل عامل يرفع أو يخفّض التكلفة، والدراسة الهندسية الدقيقة هي ما يحوّل هذه العوامل إلى رقم عادل.', en: 'Area and heat load, system type (air- or water-cooled chiller), equipment quality and efficiency, ducting and distribution complexity, and the control level required. Each factor raises or lowers the cost, and an accurate engineering study is what turns them into a fair number.' }] },
      { h: { ar: 'الرخيص قد يكون الأغلى', en: 'Cheap can be the most expensive' }, p: [{ ar: 'عرض أقل بمعدات مجهولة أو تصميم غير دقيق يعني استهلاك طاقة أعلى وأعطال متكرّرة وعمرًا أقصر. الفرق في الفاتورة الشهرية وحدها قد يتجاوز ما «وفّرته» عند الشراء خلال سنة أو سنتين.', en: "A lower offer with unknown equipment or imprecise design means higher energy use, frequent faults and a shorter lifespan. The difference in the monthly bill alone can exceed what you 'saved' at purchase within a year or two." }] },
      { h: { ar: 'كيف تحصل على سعر عادل', en: 'How to get a fair price' }, p: [{ ar: 'اطلب دراسة حمل حراري مكتوبة، واسأل عن ماركة المعدات وكفاءتها والضمان وعقد الصيانة. في سيلترا كلايمت نقدّم عرضًا شفافًا يوضّح ما تدفع مقابله بالضبط. ابدأ بمعاينة موقع مجانية.', en: 'Ask for a written heat-load study, and inquire about equipment brand, efficiency, warranty and the maintenance contract. At Syltra Climate we give a transparent proposal that shows exactly what you pay for. Start with a free site survey.' }] },
    ],
  },
  {
    slug: 'ac-maintenance-signs-schedule', division: 'climate', date: '2026-08-25',
    title: { ar: 'متى تحتاج صيانة التكييف؟ العلامات والجدول المثالي', en: 'When does your AC need maintenance? Signs and the ideal schedule' },
    excerpt: { ar: 'علامات تدلّ على أن تكييفك يحتاج صيانة، وجدول الصيانة الموصى به، ولماذا الصيانة الوقائية أوفر من الإصلاح.', en: 'Signs your AC needs service, the recommended maintenance schedule, and why preventive care beats repair.' },
    keywords: ['صيانة التكييف', 'جدول صيانة المكيف', 'عقد صيانة تكييف', 'AC maintenance'],
    body: [
      { p: [{ ar: 'التكييف مثل السيارة: يحتاج صيانة دورية ليعمل بكفاءة ويعيش طويلًا. تجاهل الصيانة يعني فاتورة أعلى وهواء أقل نقاءً وعطلًا مفاجئًا في أشدّ أيام الصيف حرارة.', en: 'AC is like a car: it needs regular maintenance to run efficiently and last. Ignoring service means a higher bill, less clean air and a sudden breakdown on the hottest summer days.' }] },
      { h: { ar: 'علامات تحتاج انتباهك', en: 'Signs to watch' }, p: [{ ar: 'ضعف التبريد، ارتفاع الفاتورة دون سبب، أصوات أو روائح غير معتادة، تسرّب ماء، أو تشغيل متواصل دون الوصول لدرجة الحرارة المطلوبة. أي من هذه يستدعي فحصًا سريعًا قبل أن تتفاقم المشكلة.', en: 'Weak cooling, an unexplained bill rise, unusual noises or smells, water leakage, or continuous running without reaching the set temperature. Any of these calls for a quick inspection before the problem grows.' }] },
      { h: { ar: 'الجدول الموصى به', en: 'The recommended schedule' }, p: [{ ar: 'تنظيف الفلاتر شهريًا في ذروة الصيف، وفحص شامل كل 3 إلى 6 أشهر حسب الاستخدام يشمل الغاز والضغط والكهرباء والمكوّنات. الأنظمة المركزية والتجارية تحتاج جدولًا أدقّ وتقارير أداء.', en: 'Clean filters monthly at peak summer, and a full inspection every 3–6 months depending on usage — covering refrigerant, pressure, electrics and components. Central and commercial systems need a tighter schedule and performance reports.' }] },
      { h: { ar: 'لماذا العقد السنوي؟', en: 'Why an annual contract?' }, p: [{ ar: 'عقد الصيانة يحوّل الصيانة من ردّ فعل على العطل إلى وقاية مجدولة، مع أولوية في الاستجابة وتقارير وأسعار أفضل. في سيلترا كلايمت نقدّم عقودًا تحافظ على كفاءة نظامك وتطيل عمره.', en: "A maintenance contract turns service from reacting to failure into scheduled prevention, with response priority, reports and better rates. At Syltra Climate we offer contracts that preserve your system's efficiency and extend its life." }] },
    ],
  },
  {
    slug: 'cut-ac-bill-summer', division: 'climate', date: '2026-08-24',
    title: { ar: 'كيف تخفّض فاتورة التكييف في الصيف؟ 7 خطوات عملية', en: 'How to cut your AC bill in summer: 7 practical steps' },
    excerpt: { ar: 'خطوات عملية تخفّض استهلاك التكييف دون التضحية بالراحة، من الإعدادات الذكية إلى الصيانة والعزل.', en: 'Practical steps that cut AC consumption without sacrificing comfort — from smart settings to maintenance and insulation.' },
    keywords: ['توفير فاتورة التكييف', 'كفاءة الطاقة', 'تكييف موفّر', 'energy saving AC'],
    body: [
      { p: [{ ar: 'التكييف هو أكبر بند في فاتورة الكهرباء صيفًا في المملكة. الخبر الجيد أن خفض الاستهلاك ممكن بخطوات بسيطة دون أن تشعر بفرق في الراحة.', en: "AC is the largest item on the summer electricity bill in the Kingdom. The good news: cutting consumption is possible with simple steps you won't feel as a loss in comfort." }] },
      { h: { ar: 'الإعدادات والعادات', en: 'Settings and habits' }, p: [{ ar: 'اضبط الحرارة على 24 درجة بدل 20، فكل درجة أقل تزيد الاستهلاك تقريبًا 6٪. استخدم جداول التشغيل والمشاهد لإطفاء التكييف في الغرف الفارغة، والمراوح لتوزيع الهواء البارد.', en: 'Set the temperature to 24°C instead of 20 — each degree lower raises consumption by roughly 6%. Use schedules and scenes to switch off AC in empty rooms, and fans to circulate cool air.' }] },
      { h: { ar: 'الصيانة والعزل', en: 'Maintenance and insulation' }, p: [{ ar: 'فلتر متّسخ أو غاز ناقص يرفع الاستهلاك كثيرًا. العزل الجيد للنوافذ والأبواب والستائر العاكسة يقلّل الحمل الحراري. الصيانة الدورية وحدها قد توفّر جزءًا ملموسًا من الفاتورة.', en: 'A dirty filter or low refrigerant sharply raises consumption. Good insulation of windows and doors and reflective curtains reduce the heat load. Regular maintenance alone can save a tangible part of the bill.' }] },
      { h: { ar: 'التحكّم الذكي', en: 'Smart control' }, p: [{ ar: 'ربط التكييف بمنصّة ذكية يمنحك جداول ومناطق وحساسات إشغال وتقارير استهلاك تكشف أين يذهب الهدر. في سيلترا كلايمت نساعدك على تحويل تكييفك إلى نظام موفّر فعلًا.', en: 'Connecting AC to a smart platform gives you schedules, zones, occupancy sensors and consumption reports that reveal where the waste goes. At Syltra Climate we help turn your AC into a genuinely efficient system.' }] },
    ],
  },
  {
    slug: 'home-lift-cost-saudi', division: 'glide', date: '2026-08-26',
    title: { ar: 'كم تكلفة تركيب مصعد منزلي في السعودية؟', en: 'How much does a home elevator cost in Saudi Arabia?' },
    excerpt: { ar: 'ما الذي يحدّد سعر المصعد المنزلي، والفرق بين الأنواع، وكيف تخطّط لتركيبه في فيلتك دون مفاجآت.', en: 'What sets the price of a home elevator, the differences between types, and how to plan its installation in your villa without surprises.' },
    keywords: ['مصعد منزلي', 'سعر مصعد فيلا', 'تكلفة مصعد', 'home elevator cost'],
    body: [
      { p: [{ ar: 'مع انتشار الفلل متعددة الأدوار، صار المصعد المنزلي استثمارًا يضيف راحة وقيمة. لكن السعر يختلف كثيرًا حسب النوع والمواصفات، وفهم ذلك يساعدك على التخطيط الصحيح.', en: 'As multi-storey villas spread, a home elevator has become an investment that adds comfort and value. But the price varies widely by type and specs, and understanding that helps you plan right.' }] },
      { h: { ar: 'ما الذي يحدّد السعر', en: 'What sets the price' }, p: [{ ar: 'عدد الوقفات، نوع النظام (هيدروليك أو بمحرّك)، أبعاد الكابينة والتشطيب، ووجود بئر جاهز من عدمه. المصعد المنزلي المدمج غالبًا أوفر من المصاعد التجارية لأنه مصمّم للأحمال الأخفّ.', en: "Number of stops, system type (hydraulic or traction), cabin size and finish, and whether a shaft already exists. A compact home lift is usually cheaper than commercial lifts because it's designed for lighter loads." }] },
      { h: { ar: 'التركيب في منزل قائم', en: 'Installing in an existing home' }, p: [{ ar: 'يمكن تركيب مصاعد منزلية في الفلل القائمة بحلول مدمجة تحتاج مساحة محدودة، لكن ذلك يتطلّب دراسة للموقع والبئر. التخطيط المبكر أثناء البناء أوفر وأسهل دائمًا.', en: 'Home lifts can be installed in existing villas with compact solutions needing limited space, but this requires a site and shaft study. Planning early during construction is always cheaper and easier.' }] },
      { h: { ar: 'احصل على تقدير دقيق', en: 'Get an accurate estimate' }, p: [{ ar: 'تجنّب الأرقام العامة على الإنترنت؛ السعر الدقيق يأتي من معاينة موقعك. في سيلترا جلايد نعاين ونرشّح النظام الأنسب لميزانيتك ومنزلك ونجهّز عرضًا واضحًا.', en: 'Avoid generic online numbers; an accurate price comes from surveying your site. At Syltra Glide we survey and recommend the system that fits your budget and home, and prepare a clear proposal.' }] },
    ],
  },
  {
    slug: 'elevator-modernization-when-why', division: 'glide', date: '2026-08-25',
    title: { ar: 'تحديث المصاعد القديمة: متى ولماذا وكيف؟', en: 'Elevator modernization: when, why and how' },
    excerpt: { ar: 'علامات تدلّ على حاجة مصعدك للتحديث، وفوائد التحديث مقابل الاستبدال الكامل، وكيف يتم على مراحل.', en: "Signs your elevator needs modernizing, the benefits of upgrading versus full replacement, and how it's done in stages." },
    keywords: ['تحديث المصاعد', 'تطوير مصعد قديم', 'صيانة مصاعد', 'elevator modernization'],
    body: [
      { p: [{ ar: 'المصعد الذي يعمل منذ سنوات قد يبدو بخير، لكن الأعطال المتكرّرة والاستهلاك العالي والقطع النادرة تكلّفك أكثر مما تتخيّل. التحديث يمنحه عمرًا جديدًا بجزء من تكلفة الاستبدال.', en: "An elevator running for years may look fine, but frequent faults, high consumption and scarce parts cost more than you'd think. Modernization gives it new life at a fraction of the cost of replacement." }] },
      { h: { ar: 'علامات الحاجة للتحديث', en: 'Signs it needs upgrading' }, p: [{ ar: 'توقّفات متكرّرة، بطء أو اهتزاز، صعوبة إيجاد قطع الغيار، استهلاك كهرباء عالٍ، أو عدم مطابقة لمعايير السلامة الحديثة. أي من هذه يشير إلى أن التحديث أصبح قرارًا اقتصاديًا.', en: 'Frequent stoppages, slowness or vibration, difficulty finding spare parts, high electricity use, or non-compliance with modern safety standards. Any of these signals that modernization has become an economic decision.' }] },
      { h: { ar: 'التحديث مقابل الاستبدال', en: 'Upgrade vs replacement' }, p: [{ ar: 'غالبًا لا تحتاج لاستبدال المصعد بالكامل. تحديث اللوحات والمحرّك والأبواب وأنظمة الأمان يرفع الكفاءة والأمان بتكلفة أقل وتوقّف أقصر للمبنى.', en: "Often you don't need to replace the whole elevator. Upgrading controllers, motor, doors and safety systems raises efficiency and safety at lower cost and with less building downtime." }] },
      { h: { ar: 'كيف يتم على مراحل', en: "How it's done in stages" }, p: [{ ar: 'نقيّم حالة المصعد، ونحدّد ما يحتاج تحديثًا، وننفّذ على مراحل تقلّل التعطيل. في سيلترا جلايد نرفع كفاءة مصاعدك القائمة مع الحفاظ على تشغيلها قدر الإمكان.', en: "We assess the elevator's condition, define what needs upgrading, and execute in stages that minimize disruption. At Syltra Glide we raise the efficiency of your existing lifts while keeping them running where possible." }] },
    ],
  },
  {
    slug: 'elevator-maintenance-contract', division: 'glide', date: '2026-08-24',
    title: { ar: 'صيانة المصاعد: لماذا العقد السنوي ضرورة لا رفاهية؟', en: 'Elevator maintenance: why an annual contract is a necessity, not a luxury' },
    excerpt: { ar: 'لماذا تحتاج المصاعد صيانة دورية إلزامية، ما الذي يشمله العقد الجيد، وكيف يحميك من التوقّف والمساءلة.', en: 'Why elevators require mandatory regular maintenance, what a good contract covers, and how it protects you from downtime and liability.' },
    keywords: ['صيانة مصاعد', 'عقد صيانة مصعد', 'سلامة المصاعد', 'elevator maintenance contract'],
    body: [
      { p: [{ ar: 'المصعد وسيلة نقل يستخدمها الناس يوميًا، وسلامته مسؤولية قانونية وأخلاقية. عقد الصيانة ليس تكلفة إضافية بل حماية لك ولمستخدمي المبنى.', en: "An elevator is transport people use daily, and its safety is a legal and ethical responsibility. A maintenance contract isn't an extra cost but protection for you and the building's users." }] },
      { h: { ar: 'لماذا الصيانة الدورية إلزامية', en: 'Why regular service is mandatory' }, p: [{ ar: 'الأجزاء الميكانيكية تتآكل، وأنظمة الأمان تحتاج فحصًا دوريًا لتعمل وقت الطوارئ. الإهمال قد يؤدّي إلى أعطال خطيرة ومساءلة قانونية، فضلًا عن إزعاج السكّان.', en: 'Mechanical parts wear, and safety systems need periodic checks to work in emergencies. Neglect can lead to serious faults and legal liability, besides inconveniencing residents.' }] },
      { h: { ar: 'ما يشمله العقد الجيد', en: 'What a good contract covers' }, p: [{ ar: 'زيارات مجدولة، فحص أنظمة الأمان، تشحيم وضبط، قطع غيار أصلية، تقارير حالة، واستجابة سريعة للطوارئ على مدار الساعة. احذر العقود التي تستثني قطع الغيار أو تبطئ الاستجابة.', en: 'Scheduled visits, safety-system checks, lubrication and adjustment, genuine parts, condition reports, and fast 24/7 emergency response. Beware contracts that exclude parts or slow the response.' }] },
      { h: { ar: 'راحة بال دائمة', en: 'Lasting peace of mind' }, p: [{ ar: 'مع عقد صيانة موثوق، مصعدك جاهز دائمًا وتوقّفه نادر. في سيلترا جلايد نقدّم عقودًا تشمل قطعًا معتمدة واستجابة طوارئ تحافظ على جاهزية مصعدك.', en: 'With a reliable maintenance contract, your elevator is always ready and rarely down. At Syltra Glide we offer contracts including certified parts and emergency response that keep your lift ready.' }] },
    ],
  },
  {
    slug: 'choose-cctv-system', division: 'shield', date: '2026-08-26',
    title: { ar: 'كيف تختار نظام كاميرات المراقبة المناسب لمنشأتك؟', en: 'How to choose the right CCTV system for your facility' },
    excerpt: { ar: 'دليل عملي لاختيار كاميرات المراقبة: الدقة، التغطية، التخزين، الرؤية الليلية، والمطابقة لاشتراطات وزارة الداخلية.', en: 'A practical guide to choosing CCTV: resolution, coverage, storage, night vision, and Ministry of Interior compliance.' },
    keywords: ['كاميرات مراقبة', 'اختيار كاميرا مراقبة', 'مراقبة السعودية', 'CCTV Saudi Arabia'],
    body: [
      { p: [{ ar: 'كاميرا المراقبة الجيدة ليست الأغلى ثمنًا بل الأنسب لاحتياجك. اختيار خاطئ يترك نقاطًا عمياء أو تسجيلًا لا يُقرأ وقت الحاجة، فيتحوّل الاستثمار إلى مجرد ديكور.', en: "A good surveillance camera isn't the priciest but the one that fits your need. A wrong choice leaves blind spots or unreadable footage when it matters, turning the investment into mere decoration." }] },
      { h: { ar: 'الدقة والتغطية', en: 'Resolution and coverage' }, p: [{ ar: 'الدقة العالية تسمح بتمييز الوجوه ولوحات السيارات، لكن الأهم هو تصميم تغطية بلا نقاط عمياء. عدد الكاميرات وزواياها ومواضعها أهم أحيانًا من الدقة وحدها.', en: 'High resolution lets you distinguish faces and plates, but more important is designing coverage with no blind spots. The number of cameras, their angles and placement often matter more than resolution alone.' }] },
      { h: { ar: 'التخزين والرؤية الليلية', en: 'Storage and night vision' }, p: [{ ar: 'حدّد مدة التخزين المطلوبة (وقد تفرضها اللوائح)، واختر كاميرات برؤية ليلية جيدة للمواقع الخارجية. للمواقع البعيدة، الكاميرات بالطاقة الشمسية حل عملي دون بنية كهربائية.', en: 'Define the storage duration you need (regulations may set it), and choose cameras with good night vision for outdoor sites. For remote locations, solar-powered cameras are a practical option without electrical infrastructure.' }] },
      { h: { ar: 'المطابقة والمتابعة عبر الجوال', en: 'Compliance and mobile access' }, p: [{ ar: 'تأكّد من مطابقة النظام لاشتراطات وزارة الداخلية، والمشاهدة المباشرة عبر الجوال 24/7. في سيلترا شيلد نصمّم مخطّط تغطية مطابقًا ونربطه بجوالك.', en: 'Ensure the system complies with Ministry of Interior requirements, with 24/7 live mobile viewing. At Syltra Shield we design a compliant coverage plan and connect it to your phone.' }] },
    ],
  },
  {
    slug: 'fire-suppression-fm200-vs-sprinklers', division: 'shield', date: '2026-08-25',
    title: { ar: 'أنظمة إطفاء الحريق: FM200 أم الرشّاشات؟ كيف تختار؟', en: 'Fire suppression: FM200 or sprinklers? How to choose' },
    excerpt: { ar: 'الفرق بين أنظمة الإطفاء بالغاز والرشّاشات المائية، وأيّها يناسب كل نوع من المباني والمخاطر.', en: 'The difference between gas and water-sprinkler suppression, and which suits each building type and risk.' },
    keywords: ['أنظمة إطفاء الحريق', 'FM200', 'رشاشات حريق', 'fire suppression'],
    body: [
      { p: [{ ar: 'ليست كل الحرائق متشابهة، ولا كل أنظمة الإطفاء تناسب كل مكان. اختيار النظام الصحيح يحمي الأرواح والممتلكات ويحقّق متطلبات الدفاع المدني في آن واحد.', en: 'Not all fires are alike, and not every suppression system suits every place. Choosing the right system protects lives and property and meets Civil Defense requirements at once.' }] },
      { h: { ar: 'الرشّاشات المائية', en: 'Water sprinklers' }, p: [{ ar: 'الحل الأكثر شيوعًا واقتصادية لمعظم المباني السكنية والتجارية. فعّالة وموثوقة، لكنها غير مناسبة للمناطق التي تتضرّر بالماء كغرف الخوادم والأرشيف والمعدات الكهربائية.', en: 'The most common and economical solution for most residential and commercial buildings. Effective and reliable, but unsuitable for water-sensitive areas like server rooms, archives and electrical equipment.' }] },
      { h: { ar: 'أنظمة الغاز مثل FM200', en: 'Gas systems like FM200' }, p: [{ ar: 'تطفئ الحريق دون ماء أو بقايا، ما يجعلها مثالية للمناطق الحسّاسة والمعدات القيمة. أغلى من الرشّاشات لكنها الخيار الوحيد المناسب حيث يكون الماء مدمّرًا.', en: 'They extinguish fire without water or residue, making them ideal for sensitive areas and valuable equipment. Pricier than sprinklers but the only suitable option where water would be destructive.' }] },
      { h: { ar: 'القرار يعتمد على المخاطر', en: 'The decision depends on risk' }, p: [{ ar: 'غالبًا يجمع المبنى بين النظامين: رشّاشات للمساحات العامة وغاز للغرف الحسّاسة. في سيلترا شيلد نصمّم المنظومة وفق طبيعة مبناك ومخاطره ومتطلبات الدفاع المدني.', en: "Often a building combines both: sprinklers for general areas and gas for sensitive rooms. At Syltra Shield we design the system to your building's nature, risks and Civil Defense requirements." }] },
    ],
  },
  {
    slug: 'access-control-methods', division: 'shield', date: '2026-08-24',
    title: { ar: 'ما أفضل نظام تحكّم بالدخول لمنشأتك؟ (بطاقة، بصمة، وجه)', en: 'What is the best access-control system for your facility?' },
    excerpt: { ar: 'مقارنة بين وسائل التحكّم بالدخول المختلفة، مزايا كل منها، وكيف تختار الأنسب لأمان منشأتك.', en: "A comparison of access-control methods, the pros of each, and how to choose the right one for your facility's security." },
    keywords: ['التحكم بالدخول', 'بصمة', 'access control', 'أنظمة أمنية'],
    body: [
      { p: [{ ar: 'المفتاح التقليدي يمكن نسخه وفقده، ولا يترك سجلًا لمن دخل ومتى. أنظمة التحكّم بالدخول الحديثة تحلّ ذلك وتمنحك تحكّمًا دقيقًا في كل باب.', en: 'A traditional key can be copied and lost, and leaves no record of who entered and when. Modern access-control systems solve this and give you precise control over every door.' }] },
      { h: { ar: 'البطاقة والرمز', en: 'Card and PIN' }, p: [{ ar: 'الحل الأبسط والأوفر، مناسب للمكاتب والمنشآت متوسطة الأمان. سهل الإدارة، لكن البطاقة قابلة للإعارة أو الفقد، والرمز قابل للمشاركة.', en: 'The simplest, most economical solution, suited to offices and medium-security facilities. Easy to manage, but a card can be lent or lost, and a PIN can be shared.' }] },
      { h: { ar: 'البصمة والوجه', en: 'Fingerprint and face' }, p: [{ ar: 'تربط الدخول بالشخص نفسه لا بشيء يحمله، فترفع الأمان وتمنع الإعارة. مثالية للمناطق الحسّاسة، مع سرعة وسهولة في الاستخدام اليومي.', en: 'They tie access to the person, not something they carry, raising security and preventing sharing. Ideal for sensitive areas, with speed and ease in daily use.' }] },
      { h: { ar: 'التكامل هو الأهم', en: 'Integration matters most' }, p: [{ ar: 'أفضل نظام هو الذي يتكامل مع المراقبة والحريق ويعطيك سجلًا وتقارير وإدارة مركزية. في سيلترا شيلد نصمّم نظام دخول متكامل يناسب مستويات الصلاحية في منشأتك.', en: "The best system integrates with surveillance and fire and gives you logs, reports and central management. At Syltra Shield we design an integrated access system matched to your facility's permission levels." }] },
    ],
  },
  {
    slug: 'what-is-erp-why-need', division: 'os', date: '2026-08-26',
    title: { ar: 'ما هو نظام ERP ولماذا تحتاجه مؤسستك؟', en: 'What is ERP and why does your organization need it?' },
    excerpt: { ar: 'شرح مبسّط لنظام تخطيط موارد المؤسسات، ما الذي يحلّه، وعلامات تدلّ على أن عملك أصبح يحتاجه.', en: 'A simple explanation of ERP, what it solves, and signs your business now needs one.' },
    keywords: ['ما هو ERP', 'نظام تخطيط موارد', 'برمجيات إدارة', 'what is ERP'],
    body: [
      { p: [{ ar: 'كلمة ERP تتردّد كثيرًا لكن كثيرين لا يعرفون ما تعنيه فعلًا. ببساطة: هو نظام واحد يربط كل أقسام مؤسستك في مكان واحد بدل الجداول والأنظمة المتفرّقة.', en: "The term ERP comes up a lot, but many don't know what it really means. Simply: it's one system that links all your organization's departments in one place instead of scattered spreadsheets and systems." }] },
      { h: { ar: 'ما الذي يحلّه', en: 'What it solves' }, p: [{ ar: 'بدل إدخال البيانات مرات متعدّدة في أنظمة لا تتحدّث، يجمع ERP المحاسبة والمخزون والمبيعات والموارد البشرية في تدفّق واحد، فتصبح لديك صورة واحدة دقيقة ولحظية عن عملك.', en: "Instead of entering data multiple times into systems that don't talk, ERP unifies accounting, inventory, sales and HR into one flow, giving you a single, accurate, real-time picture of your business." }] },
      { h: { ar: 'علامات أنك تحتاجه', en: 'Signs you need it' }, p: [{ ar: 'اعتماد كبير على جداول Excel، أخطاء متكرّرة في البيانات، صعوبة في معرفة أرقامك الحقيقية، أو بطء في اتخاذ القرار لغياب تقارير موحّدة. إذا نمَت مؤسستك فوق أدواتها، فقد حان الوقت.', en: "Heavy reliance on Excel, frequent data errors, difficulty knowing your real numbers, or slow decisions from a lack of unified reports. If your organization has outgrown its tools, it's time." }] },
      { h: { ar: 'جاهز أم مخصّص؟', en: 'Ready or custom?' }, p: [{ ar: 'سيلترا ERP منتج جاهز بالاشتراك يبدأ سريعًا ويناسب الاحتياجات القياسية، ويمكن تخصيصه. نساعدك على معرفة ما يناسبك بعد جلسة اكتشاف قصيرة.', en: 'Syltra ERP is a ready subscription product that starts fast, fits standard needs and can be customized. We help you find what suits you after a short discovery session.' }] },
    ],
  },
  {
    slug: 'ai-for-business-saudi', division: 'os', date: '2026-08-25',
    title: { ar: 'كيف يستفيد عملك من الذكاء الاصطناعي في السعودية؟', en: 'How can your business benefit from AI in Saudi Arabia?' },
    excerpt: { ar: 'كيف تستفيد المؤسسات السعودية من الذكاء الاصطناعي فعليًا، بعيدًا عن الضجيج، بتطبيقات تخدم القرار وتوفّر الوقت.', en: 'How Saudi organizations actually benefit from AI, beyond the hype, with applications that serve decisions and save time.' },
    keywords: ['الذكاء الاصطناعي للأعمال', 'تطبيقات ذكاء اصطناعي', 'AI السعودية', 'AI for business'],
    body: [
      { p: [{ ar: 'الذكاء الاصطناعي ليس شعارًا للمستقبل بل أداة تعمل اليوم. لكن النجاح لا يأتي من تبنّي التقنية لذاتها، بل من توظيفها في مشكلة حقيقية تخدم عملك.', en: "AI isn't a slogan for the future but a tool that works today. Yet success doesn't come from adopting the technology for its own sake, but from applying it to a real problem that serves your business." }] },
      { h: { ar: 'خدمة العملاء والدعم', en: 'Customer service and support' }, p: [{ ar: 'مساعد ذكي يجيب أسئلة العملاء المتكرّرة بالعربية على مدار الساعة، ويحوّل الحالات المعقّدة للموظف. يوفّر وقت الفريق ويرفع رضا العملاء دون زيادة التكلفة.', en: "A smart assistant answers customers' repetitive questions in Arabic around the clock and routes complex cases to a human. It saves the team's time and raises satisfaction without added cost." }] },
      { h: { ar: 'التحليلات والتنبّؤ', en: 'Analytics and forecasting' }, p: [{ ar: 'نماذج تحلّل بياناتك وتتنبّأ بالطلب والمخزون والاتجاهات، فتتّخذ قرارات مبنية على أرقام لا حدس. هذا مفيد بشكل خاص للتجارة والتشغيل واللوجستيات.', en: 'Models analyze your data and forecast demand, inventory and trends, so you decide from numbers not hunches. This is especially useful for retail, operations and logistics.' }] },
      { h: { ar: 'ابدأ صغيرًا واثبت القيمة', en: 'Start small and prove value' }, p: [{ ar: 'أفضل طريقة هي البدء بتطبيق واحد واضح العائد ثم التوسّع. في سيلترا او-إس نبني حلول ذكاء اصطناعي تدعم العربية ومربوطة ببياناتك بأمان، مع احترام خصوصيتك وملكيتك لبياناتك.', en: 'The best approach is starting with one application with clear returns, then expanding. At Syltra OS we build AI solutions that support Arabic and connect securely to your data, respecting your privacy and data ownership.' }] },
    ],
  },
  {
    slug: 'successful-software-project', division: 'os', date: '2026-08-24',
    title: { ar: 'كيف تنجح في مشروع تطوير برمجي وتتجنّب الأخطاء الشائعة؟', en: 'How to succeed in a software project and avoid common mistakes' },
    excerpt: { ar: 'الأسباب الحقيقية لفشل المشاريع البرمجية، وكيف تتجنّبها من البداية لتحصل على نظام يخدم عملك فعلًا.', en: 'The real reasons software projects fail, and how to avoid them from the start to get a system that truly serves your business.' },
    keywords: ['تطوير برمجي', 'مشروع برمجي', 'أنظمة مخصّصة', 'software project'],
    body: [
      { p: [{ ar: 'كثير من المشاريع البرمجية تتأخّر أو تتجاوز الميزانية أو تنتهي بنظام لا يُستخدم. المفاجأة أن السبب نادرًا ما يكون تقنيًا بحتًا، بل في التخطيط والتواصل.', en: "Many software projects run late, over budget, or end with a system nobody uses. Surprisingly, the cause is rarely purely technical — it's in planning and communication." }] },
      { h: { ar: 'ابدأ بالاحتياج لا بالحل', en: 'Start with the need, not the solution' }, p: [{ ar: 'الخطأ الأكبر هو القفز إلى «نريد تطبيقًا» قبل فهم المشكلة. جلسة اكتشاف جيدة تحدّد الاحتياج الحقيقي وتوفّر عليك بناء ميزات لا أحد يستخدمها.', en: "The biggest mistake is jumping to 'we want an app' before understanding the problem. A good discovery session defines the real need and saves you from building features nobody uses." }] },
      { h: { ar: 'أطلق مبكرًا وطوّر تدريجيًا', en: 'Ship early and iterate' }, p: [{ ar: 'محاولة بناء كل شيء دفعة واحدة وصفة للفشل. المنهجية الرشيقة تطلق نسخة أولى قابلة للاستخدام سريعًا، ثم تطوّر بناءً على ملاحظات حقيقية.', en: 'Trying to build everything at once is a recipe for failure. An agile approach ships a usable first version quickly, then iterates on real feedback.' }] },
      { h: { ar: 'اختر شريكًا لا مجرّد مورّد', en: 'Choose a partner, not just a vendor' }, p: [{ ar: 'النظام يحتاج تطويرًا ودعمًا بعد الإطلاق. اختر من يبقى معك ويفهم عملك. في سيلترا او-إس نعمل كشريك من الفكرة حتى التشغيل والتطوير المستمر، وبياناتك ملكك.', en: 'A system needs iteration and support after launch. Choose someone who stays with you and understands your business. At Syltra OS we work as a partner from idea to operation and ongoing iteration — and your data is yours.' }] },
    ],
  },
  {
    slug: 'best-smart-locks-guide', division: 'life', date: '2026-08-26',
    title: { ar: 'أفضل أقفال الأبواب الذكية: كيف تختار القفل المناسب؟', en: 'The best smart door locks: how to choose the right one' },
    excerpt: { ar: 'دليل اختيار القفل الذكي: طرق الفتح، الأمان، البطارية، التوافق، وما يجب أن تنتبه له قبل الشراء.', en: 'A guide to choosing a smart lock: unlock methods, security, battery, compatibility, and what to watch before buying.' },
    keywords: ['أقفال ذكية', 'أفضل قفل ذكي', 'قفل باب ذكي', 'smart lock', 'best smart lock'],
    body: [
      { p: [{ ar: 'القفل الذكي من أكثر ما يبدأ به الناس رحلة المنزل الذكي، لأنه يجمع بين الراحة والأمان. لكن السوق مليء بالخيارات، وليست كلها بنفس الجودة.', en: 'A smart lock is one of the most common starting points on the smart-home journey, combining comfort and security. But the market is full of options, and not all are equal.' }] },
      { h: { ar: 'طرق الفتح', en: 'Unlock methods' }, p: [{ ar: 'أفضل الأقفال تدعم عدة طرق: البصمة، الرمز، البطاقة، التطبيق، والمفتاح التقليدي كخيار طوارئ. المهم أن يعمل القفل حتى بدون واي فاي أو بلوتوث، وأن يبقى مفتاح احتياطي.', en: 'The best locks support several methods: fingerprint, PIN, card, app, and a traditional key for emergencies. The key is that it works even without Wi-Fi or Bluetooth, with a backup key.' }] },
      { h: { ar: 'الأمان والبطارية', en: 'Security and battery' }, p: [{ ar: 'ابحث عن التشفير، تنبيهات فورية عند كل فتح، صلاحيات مؤقتة للضيوف، وسجل دخول. البطارية الجيدة تدوم عدة أشهر مع تنبيه قبل نفادها، والقفل يعمل أثناء انقطاع الكهرباء.', en: 'Look for encryption, instant alerts on every unlock, temporary guest access and an entry log. A good battery lasts several months with a low-battery alert, and the lock works during outages.' }] },
      { h: { ar: 'جزء من منظومة أكبر', en: 'Part of a bigger system' }, p: [{ ar: 'القفل الأذكى هو الذي يتكامل مع منزلك الذكي: يشغّل مشهد «الوصول» عند الفتح، ويربط مع الكاميرا والإنذار. في سيلترا لايف نختار لك القفل ضمن منظومة متكاملة لا كجهاز منفصل.', en: "The smartest lock integrates with your smart home: triggering an 'arrival' scene on unlock and linking to the camera and alarm. At Syltra Life we select your lock within an integrated system, not as a standalone device." }] },
    ],
  },
  {
    slug: 'smart-home-energy-savings', division: 'life', date: '2026-08-25',
    title: { ar: 'المنزل الذكي وتوفير الطاقة: كم توفّر فعلًا؟', en: 'Smart homes and energy savings: how much do you really save?' },
    excerpt: { ar: 'كيف يخفّض المنزل الذكي فاتورة الكهرباء عمليًا، وأين يأتي التوفير الحقيقي، وما التوقّعات الواقعية.', en: 'How a smart home practically cuts the electricity bill, where the real savings come from, and realistic expectations.' },
    keywords: ['توفير الطاقة', 'منزل ذكي', 'خفض فاتورة الكهرباء', 'smart home energy saving'],
    body: [
      { p: [{ ar: 'يُقال إن المنزل الذكي يوفّر الطاقة، لكن كم بالضبط؟ التوفير حقيقي لكنه يأتي من أماكن محدّدة، وفهمها يساعدك على استثمار ذكي بدل توقّعات مبالغ فيها.', en: "It's said that a smart home saves energy, but how much exactly? The savings are real but come from specific places, and understanding them helps you invest wisely rather than overexpect." }] },
      { h: { ar: 'التكييف والإضاءة', en: 'Cooling and lighting' }, p: [{ ar: 'التكييف هو أكبر مستهلك، والتحكّم الذكي (جداول، مناطق، حساسات إشغال) يمنع تبريد الغرف الفارغة ويضبط الحرارة تلقائيًا. الإضاءة الذكية تطفئ ما لا يُستخدم وتخفّت حسب الحاجة.', en: "Cooling is the biggest consumer, and smart control (schedules, zones, occupancy sensors) prevents cooling empty rooms and adjusts temperature automatically. Smart lighting turns off what's unused and dims as needed." }] },
      { h: { ar: 'المراقبة تكشف الهدر', en: 'Monitoring reveals waste' }, p: [{ ar: 'أهم ما يقدّمه المنزل الذكي هو الرؤية: تقارير استهلاك تُظهر أين تذهب الكهرباء، فتتّخذ قرارات مبنية على أرقام. ما لا يُقاس لا يُدار.', en: "The most valuable thing a smart home offers is visibility: consumption reports showing where electricity goes, so you decide from numbers. What isn't measured isn't managed." }] },
      { h: { ar: 'توقّعات واقعية', en: 'Realistic expectations' }, p: [{ ar: 'التوفير يعتمد على عاداتك وحجم منزلك ومدى الأتمتة، لكن الأثر التراكمي ملموس على مدى العام. في سيلترا لايف نصمّم نظامك ليوفّر فعلًا لا ليبدو ذكيًا فقط.', en: 'Savings depend on your habits, home size and degree of automation, but the cumulative effect over a year is tangible. At Syltra Life we design your system to genuinely save, not just look smart.' }] },
    ],
  },
  {
    slug: 'smart-home-security-systems', division: 'life', date: '2026-08-24',
    title: { ar: 'كيف تحمي منزلك بنظام أمن ذكي متكامل؟', en: 'How do you protect your home with an integrated smart-security system?' },
    excerpt: { ar: 'كيف تحمي منزلك بمنظومة أمن ذكية متكاملة، ما مكوّناتها الأساسية، وكيف تمنحك راحة البال أينما كنت.', en: 'How to protect your home with an integrated smart-security system, its essential components, and how it gives peace of mind anywhere.' },
    keywords: ['أمن منزلي', 'كاميرات منزلية', 'إنذار سرقة', 'smart home security'],
    body: [
      { p: [{ ar: 'أمان منزلك وعائلتك لا يحتمل الحلول الجزئية. المنظومة الأمنية الذكية تجمع الكاميرات والحساسات والإنذار في نظام واحد تتحكّم فيه من جوالك وأنت في أي مكان.', en: "Your home and family's safety can't rely on partial solutions. A smart security system unites cameras, sensors and alarms in one system you control from your phone anywhere." }] },
      { h: { ar: 'الكاميرات والمراقبة', en: 'Cameras and monitoring' }, p: [{ ar: 'كاميرات داخلية وخارجية برؤية ليلية وتنبيهات ذكية عند الحركة، تشاهدها مباشرة عبر الجوال 24/7. تسجيل آمن يمنحك دليلًا عند الحاجة وردعًا للمتسلّلين.', en: 'Indoor and outdoor cameras with night vision and smart motion alerts, viewed live on your phone 24/7. Secure recording gives you evidence when needed and deters intruders.' }] },
      { h: { ar: 'الحساسات والإنذار', en: 'Sensors and alarms' }, p: [{ ar: 'حساسات أبواب ونوافذ وحركة تكشف أي اقتحام وترسل تنبيهًا فوريًا. يمكن ربطها بالإضاءة لمحاكاة وجودك، وبالأقفال الذكية لإغلاق تلقائي.', en: 'Door, window and motion sensors detect any break-in and send an instant alert. They can link to lighting to simulate presence, and to smart locks for automatic locking.' }] },
      { h: { ar: 'التكامل يصنع الفرق', en: 'Integration makes the difference' }, p: [{ ar: 'قوة النظام في تكامله: عند اكتشاف حركة، تضيء الأنوار وتسجّل الكاميرا ويصلك تنبيه معًا. في سيلترا لايف نبني منظومة أمن متكاملة تمنحك راحة بال حقيقية.', en: "The system's power is in integration: on detecting motion, lights turn on, the camera records and you get an alert together. At Syltra Life we build an integrated security system that gives real peace of mind." }] },
    ],
  },
  {
    slug: 'saudi-building-code-hvac', division: 'climate', date: '2026-08-23',
    title: { ar: 'ما اشتراطات التكييف في كود البناء السعودي (SBC)؟', en: 'What are the HVAC requirements in the Saudi Building Code (SBC)?' },
    excerpt: { ar: 'نظرة على متطلبات أنظمة التكييف والتهوية في كود البناء السعودي، وكفاءة الطاقة، وكيف تضمن مطابقة مشروعك.', en: 'An overview of HVAC and ventilation requirements in the Saudi Building Code, energy efficiency, and how to keep your project compliant.' },
    keywords: ['كود البناء السعودي', 'اشتراطات التكييف', 'SBC', 'كفاءة الطاقة', 'Saudi Building Code HVAC'],
    body: [
      { p: [{ ar: 'كود البناء السعودي (SBC) يضع معايير إلزامية لأنظمة التكييف والتهوية تهدف إلى السلامة وكفاءة الطاقة وجودة الهواء الداخلي. تجاهلها قد يؤخّر اعتماد مشروعك أو يرفع تكاليف التشغيل.', en: "The Saudi Building Code (SBC) sets mandatory standards for HVAC and ventilation aimed at safety, energy efficiency and indoor air quality. Ignoring them can delay your project's approval or raise operating costs." }] },
      { h: { ar: 'كفاءة الطاقة', en: 'Energy efficiency' }, p: [{ ar: 'يشدّد الكود ودعم كفاءة الطاقة على اختيار معدات ذات كفاءة عالية وعزل مناسب وتصميم يقلّل الأحمال. هذا لا يخدم المطابقة فقط بل يخفّض فاتورتك على المدى الطويل.', en: 'The code and energy-efficiency initiatives stress high-efficiency equipment, proper insulation and load-reducing design. This serves not only compliance but also lowers your long-term bill.' }] },
      { h: { ar: 'التهوية وجودة الهواء', en: 'Ventilation and air quality' }, p: [{ ar: 'تحدّد المتطلبات معدلات تجديد الهواء اللازمة حسب نوع المبنى واستخدامه، خاصة في المطاعم والعيادات والمساحات المزدحمة، لضمان هواء داخلي صحّي.', en: 'Requirements define the fresh-air rates needed by building type and use, especially in restaurants, clinics and busy spaces, to ensure healthy indoor air.' }] },
      { h: { ar: 'كيف تضمن المطابقة', en: 'How to ensure compliance' }, p: [{ ar: 'المطابقة تبدأ من التصميم بمخطّطات ودراسة صحيحة ومعدات معتمدة. في سيلترا كلايمت نصمّم وننفّذ وفق الكود لنجنّبك التأخير والتعديلات المكلفة لاحقًا.', en: 'Compliance starts at design with correct drawings, study and certified equipment. At Syltra Climate we design and execute to code to spare you delays and costly rework.' }] },
    ],
  },
  {
    slug: 'elevator-licenses-requirements-saudi', division: 'glide', date: '2026-08-23',
    title: { ar: 'تراخيص واشتراطات المصاعد في السعودية: ما تحتاج معرفته؟', en: 'Elevator licenses and requirements in Saudi Arabia: what you need to know' },
    excerpt: { ar: 'الجهات المنظّمة للمصاعد، شهادات المطابقة (SASO)، متطلبات الأمانة، وشهادة تشغيل المصعد وصيانته الدورية.', en: 'The bodies regulating elevators, conformity certificates (SASO), municipality requirements, and the operating certificate and periodic maintenance.' },
    keywords: ['تراخيص المصاعد', 'اشتراطات المصاعد', 'SASO', 'سلامة المصاعد', 'elevator license Saudi Arabia'],
    body: [
      { p: [{ ar: 'تركيب مصعد لا ينتهي عند التشغيل؛ فهناك اشتراطات وتراخيص تضمن سلامته وقانونية تشغيله. تجاهلها قد يعرّضك للمساءلة أو إيقاف المصعد.', en: "Installing an elevator doesn't end at operation; there are requirements and licenses ensuring its safety and legal operation. Ignoring them can expose you to liability or a shutdown." }] },
      { h: { ar: 'المطابقة والمواصفات', en: 'Conformity and standards' }, p: [{ ar: 'يجب أن تتوافق المصاعد مع المواصفات المعتمدة من الهيئة السعودية للمواصفات (SASO) ومعايير السلامة المعتمدة، مع شهادات مطابقة للمعدات المستوردة.', en: 'Elevators must conform to standards approved by the Saudi Standards Organization (SASO) and adopted safety standards, with conformity certificates for imported equipment.' }] },
      { h: { ar: 'متطلبات الأمانة والتشغيل', en: 'Municipality and operation' }, p: [{ ar: 'تشترط الأمانات والجهات المختصة فحصًا وشهادة قبل التشغيل، وصيانة دورية موثّقة تضمن استمرار السلامة. الصيانة ليست اختيارية بل شرط لاستمرار التشغيل الآمن.', en: "Municipalities and authorities require inspection and a certificate before operation, plus documented periodic maintenance ensuring ongoing safety. Maintenance isn't optional but a condition for continued safe operation." }] },
      { h: { ar: 'نتولّى ذلك عنك', en: 'We handle it for you' }, p: [{ ar: 'في سيلترا جلايد ننفّذ وفق المواصفات المعتمدة ونوثّق ونساعدك في متطلبات التشغيل والصيانة، لتطمئن أن مصعدك آمن وقانوني.', en: "At Syltra Glide we execute to approved standards, document, and help with operating and maintenance requirements, so you're assured your elevator is safe and compliant." }] },
    ],
  },
  {
    slug: 'civil-defense-safety-certificate', division: 'shield', date: '2026-08-23',
    title: { ar: 'كيف تحصل على شهادة السلامة من الدفاع المدني؟', en: 'How do you obtain a Civil Defense safety certificate?' },
    excerpt: { ar: 'خطوات الحصول على شهادة السلامة، المتطلبات الأساسية، والأخطاء التي تؤخّر الاعتماد، وكيف تجهّز منشأتك.', en: 'The steps to obtain a safety certificate, the core requirements, mistakes that delay approval, and how to prepare your facility.' },
    keywords: ['شهادة السلامة', 'الدفاع المدني', 'ترخيص سلامة', 'اشتراطات الدفاع المدني', 'civil defense certificate'],
    body: [
      { p: [{ ar: 'شهادة السلامة من الدفاع المدني شرط لتشغيل معظم المنشآت التجارية والصناعية. الحصول عليها يبدو معقّدًا، لكن التجهيز الصحيح من البداية يجعله سلسًا.', en: 'A Civil Defense safety certificate is a condition for operating most commercial and industrial facilities. Getting it seems complex, but preparing correctly from the start makes it smooth.' }] },
      { h: { ar: 'المتطلبات الأساسية', en: 'Core requirements' }, p: [{ ar: 'منظومة حريق متكاملة (كشف وإنذار ومكافحة) مطابقة لطبيعة المبنى، مخارج ومسارات إخلاء واضحة، لوحات إرشادية، ومخطّطات سلامة معتمدة. المعدات يجب أن تكون معتمدة والتنفيذ موثّقًا.', en: 'An integrated fire system (detection, alarm, suppression) matched to the building, clear exits and evacuation routes, signage, and approved safety drawings. Equipment must be certified and execution documented.' }] },
      { h: { ar: 'أخطاء تؤخّر الاعتماد', en: 'Mistakes that delay approval' }, p: [{ ar: 'أكبر خطأ هو معالجة السلامة كخطوة أخيرة بعد اكتمال البناء. تعديل الأنظمة لاحقًا مكلف وبطيء. الأخطاء الشائعة تشمل معدات غير معتمدة أو مخطّطات غير مطابقة أو تنفيذ بلا إشراف هندسي.', en: 'The biggest mistake is treating safety as a last step after construction. Retrofitting systems is costly and slow. Common errors include uncertified equipment, non-compliant drawings, or execution without engineering supervision.' }] },
      { h: { ar: 'جهّز منشأتك بثقة', en: 'Prepare your facility with confidence' }, p: [{ ar: 'في سيلترا شيلد نصمّم وننفّذ منظومة السلامة وفق اشتراطات الدفاع المدني ونوثّقها، ونرافقك حتى الحصول على الاعتماد.', en: 'At Syltra Shield we design and execute the safety system to Civil Defense requirements and document it, accompanying you through approval.' }] },
    ],
  },
  {
    slug: 'pdpl-data-protection-compliance', division: 'os', date: '2026-08-23',
    title: { ar: 'حماية البيانات والامتثال (PDPL) للأنظمة في السعودية', en: 'Data protection and PDPL compliance for systems in Saudi Arabia' },
    excerpt: { ar: 'ما يتطلّبه نظام حماية البيانات الشخصية السعودي من الأنظمة والتطبيقات، وكيف تبني برمجياتك ممتثلة من البداية.', en: "What Saudi Arabia's Personal Data Protection Law requires of systems and apps, and how to build your software compliant from day one." },
    keywords: ['حماية البيانات', 'PDPL', 'نظام حماية البيانات الشخصية', 'الامتثال', 'data protection Saudi Arabia'],
    body: [
      { p: [{ ar: 'مع نظام حماية البيانات الشخصية (PDPL) في السعودية، لم تعد حماية بيانات العملاء خيارًا بل التزامًا قانونيًا. أي نظام أو تطبيق يجمع بيانات يجب أن يبنى مع مراعاة الامتثال.', en: "With Saudi Arabia's Personal Data Protection Law (PDPL), protecting customer data is no longer optional but a legal obligation. Any system or app collecting data must be built with compliance in mind." }] },
      { h: { ar: 'ماذا يتطلّب النظام؟', en: 'What does the law require?' }, p: [{ ar: 'موافقة واضحة على جمع البيانات، غرض محدّد لاستخدامها، حماية مناسبة لها، وحقوق للمستخدم في الوصول والتصحيح والحذف. تخزين البيانات ونقلها يخضع لضوابط.', en: 'Clear consent to collect data, a defined purpose for its use, appropriate protection, and user rights to access, correct and delete. Data storage and transfer are subject to controls.' }] },
      { h: { ar: 'الامتثال من التصميم', en: 'Compliance by design' }, p: [{ ar: 'أرخص وأأمن طريقة هي بناء الامتثال داخل النظام من البداية: تشفير، صلاحيات، سجلّات، وإدارة موافقات. إضافته لاحقًا مكلف ومحفوف بالمخاطر.', en: 'The cheapest, safest way is building compliance into the system from the start: encryption, permissions, logs and consent management. Adding it later is costly and risky.' }] },
      { h: { ar: 'نبني أنظمة ممتثلة', en: 'We build compliant systems' }, p: [{ ar: 'في سيلترا او-إس نبني برمجياتك مع مراعاة حماية البيانات وملكيتك لها، لتكون مطمئنًا قانونيًا ومحترمًا لخصوصية عملائك.', en: "At Syltra OS we build your software with data protection and your ownership in mind, so you're legally assured and respectful of your customers' privacy." }] },
    ],
  },
  {
    slug: 'smart-home-permits-requirements', division: 'life', date: '2026-08-23',
    title: { ar: 'هل تحتاج تصريحًا لتركيب نظام منزل ذكي؟ الاشتراطات', en: 'Do you need a permit to install a smart-home system? The requirements' },
    excerpt: { ar: 'ما الذي يتطلّبه تركيب أنظمة المنزل الذكي والتيار المنخفض من اشتراطات فنية، ومتى تحتاج تنسيقًا مع الجهات.', en: 'What smart-home and low-current installations require technically, and when you need to coordinate with authorities.' },
    keywords: ['اشتراطات المنزل الذكي', 'التيار المنخفض', 'تصريح منزل ذكي', 'smart home requirements'],
    body: [
      { p: [{ ar: 'كثيرون يتساءلون: هل يحتاج المنزل الذكي إلى تصاريح خاصة؟ الإجابة تعتمد على نطاق العمل، لكن الأهم هو تنفيذه وفق اشتراطات فنية سليمة تضمن الأمان والموثوقية.', en: 'Many ask: does a smart home need special permits? The answer depends on scope, but what matters most is executing it to sound technical requirements ensuring safety and reliability.' }] },
      { h: { ar: 'التيار المنخفض والكهرباء', en: 'Low-current and electrical' }, p: [{ ar: 'أنظمة المنزل الذكي تعتمد على بنية تيار منخفض وكهرباء سليمة. التنفيذ الرديء للكابلات والشبكات يسبّب أعطالًا وأحيانًا مخاطر. الالتزام بالمعايير الكهربائية أساس لأي نظام ذكي موثوق.', en: 'Smart-home systems rely on a sound low-current and electrical base. Poor cabling and networking cause faults and sometimes hazards. Adhering to electrical standards is the foundation of any reliable smart system.' }] },
      { h: { ar: 'المشاريع الكبيرة والمباني', en: 'Large projects and buildings' }, p: [{ ar: 'في الفلل الكبيرة والمباني والمجمّعات، قد يتطلّب العمل تنسيقًا مع المقاول والاستشاري ومطابقة لكود البناء، خاصة عند التكامل مع الحريق والأمن والكهرباء.', en: 'In large villas, buildings and compounds, the work may require coordination with the contractor and consultant and compliance with the building code, especially when integrating with fire, security and electrical systems.' }] },
      { h: { ar: 'ننفّذ باحترافية', en: 'We execute professionally' }, p: [{ ar: 'في سيلترا لايف ننفّذ أنظمة المنزل الذكي والتيار المنخفض وفق المعايير الفنية بتصميم نظيف وقابل للتوسّع، لتحصل على منزل ذكي آمن وموثوق.', en: 'At Syltra Life we execute smart-home and low-current systems to technical standards with a clean, scalable design, so you get a safe, reliable smart home.' }] },
    ],
  },
];

/**
 * Only the currently active brands publish on the parent-site journal. The
 * hidden engineering divisions (climate, glide, shield, os) still have their
 * division pages, but their articles are removed from the blog, its routes and
 * the sitemap. Update this set to re-expose a division's posts.
 */
const BLOG_DIVISIONS = new Set(["life", "one", "health"]);
export const POSTS: Post[] = ALL_POSTS.filter((p) => BLOG_DIVISIONS.has(p.division));

export function postsForDivision(key: string) {
  return POSTS.filter((p) => p.division === key);
}
