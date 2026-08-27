import type { Locale } from "@/lib/i18n/config";

export interface QA {
  q: { ar: string; en: string };
  a: { ar: string; en: string };
}

export function faqText(v: { ar: string; en: string }, locale: Locale) {
  return locale === "ar" ? v.ar : v.en;
}

/** Per-division FAQ, informed by the questions Saudi buyers actually ask. */
export const DIVISION_FAQ: Record<string, QA[]> = {
  life: [
    {
      q: { ar: "ما هو نظام المنزل الذكي وماذا يشمل؟", en: "What is a smart-home system and what does it include?" },
      a: {
        ar: "منظومة تجمع الإضاءة والتكييف والأمن والترفيه والستائر في تحكّم واحد عبر التطبيق أو شاشة أو الأوامر الصوتية، مع مشاهد جاهزة تعمل بلمسة واحدة.",
        en: "One system that brings lighting, climate, security, entertainment and curtains into a single control — app, screen or voice — with ready scenes that run at a tap.",
      },
    },
    {
      q: { ar: "هل يمكن تركيب النظام في منزل قائم دون تكسير؟", en: "Can it be installed in an existing home without major work?" },
      a: {
        ar: "نعم، نوفّر حلولًا لاسلكية مرنة تُركّب في المنازل القائمة دون تعديلات هيكلية كبيرة، ويمكن البدء بجزء والتوسّع لاحقًا.",
        en: "Yes, flexible wireless solutions retrofit into existing homes without major structural changes — start with part of it and expand later.",
      },
    },
    {
      q: { ar: "هل أتحكّم في بيتي وأنا خارجه؟", en: "Can I control my home while I'm away?" },
      a: {
        ar: "نعم، تحكّم كامل من أي مكان عبر التطبيق مع اطمئنان على البيت وتنبيهات فورية.",
        en: "Yes, full control from anywhere through the app, with peace of mind and instant alerts.",
      },
    },
    {
      q: { ar: "ما طرق فتح القفل الذكي؟", en: "How does a smart lock open?" },
      a: {
        ar: "عدة طرق: البصمة، الرمز السري، البطاقة، التطبيق، والمفتاح التقليدي — وتعمل حتى بدون واي فاي أو بلوتوث.",
        en: "Several ways: fingerprint, PIN, card, app and a traditional key — and it works even without Wi-Fi or Bluetooth.",
      },
    },
    {
      q: { ar: "هل الأقفال الذكية آمنة؟", en: "Are smart locks secure?" },
      a: {
        ar: "نعم، تشفير وتنبيهات فورية عند كل فتح وإغلاق، وصلاحيات مؤقتة للضيوف، وسجل دخول كامل.",
        en: "Yes, encryption, instant open/close alerts, temporary guest access and a full entry log.",
      },
    },
    {
      q: { ar: "هل النظام قابل للتوسّع والتكامل مع أجهزة أخرى؟", en: "Is the system expandable and compatible with other devices?" },
      a: {
        ar: "نعم، منصّة سيلترا لايف مبنية على الانفتاح وتتكامل مع المعايير الحديثة (Matter وThread وZigbee) وتنمو مع احتياجك.",
        en: "Yes, the Syltra Life platform is built open and works with modern standards (Matter, Thread, Zigbee), growing with your needs.",
      },
    },
    {
      q: { ar: "هل يوفّر النظام في استهلاك الطاقة؟", en: "Does the system save energy?" },
      a: {
        ar: "نعم، جداول ومشاهد وحساسات تقلّل استهلاك الإضاءة والتكييف وتُظهر لك استهلاكك بوضوح.",
        en: "Yes, schedules, scenes and sensors cut lighting and cooling use and show your consumption clearly.",
      },
    },
    {
      q: { ar: "ما الأجهزة والأنظمة التي يمكن أتمتتها؟", en: "What devices and systems can be automated?" },
      a: {
        ar: "الإضاءة والستائر والتكييف والصوت والكاميرات والإنتركم والأقفال وحتى شحن السيارات الكهربائية — في منظومة واحدة قابلة للتوسّع.",
        en: "Lighting, curtains, climate, audio, cameras, intercom, locks and even EV charging — in one expandable ecosystem.",
      },
    },
    {
      q: { ar: "كم تدوم بطارية القفل الذكي وماذا لو انقطعت الكهرباء؟", en: "How long does the smart-lock battery last, and what if the power goes out?" },
      a: {
        ar: "تدوم البطارية عادة عدة أشهر مع تنبيه قبل نفادها، والقفل يعمل أثناء انقطاع الكهرباء مع مفتاح أو منفذ طوارئ احتياطي.",
        en: "The battery typically lasts several months with a low-battery alert, and the lock keeps working during outages with a backup key or emergency port.",
      },
    },
    {
      q: { ar: "هل تقدّمون التركيب والدعم والضمان؟", en: "Do you provide installation, support and warranty?" },
      a: {
        ar: "نعم، معاينة وتصميم وتركيب وإعداد كامل، مع دعم وضمان بعد التشغيل.",
        en: "Yes, survey, design, installation and full setup, with support and warranty after go-live.",
      },
    },
  ],

  climate: [
    {
      q: { ar: "كيف أختار بين التكييف المركزي وأنظمة VRF والسبليت؟", en: "How do I choose between central, VRF and split AC?" },
      a: {
        ar: "يعتمد على المساحة وعدد الغرف والحمل الحراري والميزانية. نبدأ بدراسة حمل حراري ونرشّح الأنسب: المركزي/الشيلر للمباني الكبيرة، وVRF للمرونة ومتعدد المناطق، والسبليت للوحدات الصغيرة.",
        en: "It depends on area, number of rooms, heat load and budget. We start with a load study and recommend the best fit: central/chiller for large buildings, VRF for multi-zone flexibility, and split for smaller units.",
      },
    },
    {
      q: { ar: "هل تعمل الأنظمة بكفاءة في مناخ السعودية الحار؟", en: "Do the systems work efficiently in Saudi Arabia's hot climate?" },
      a: {
        ar: "نعم؛ نختار معدات مصمّمة لدرجات الحرارة العالية، ونحسب الأحمال بدقة، ونضبط النظام بالموازنة (TAB) لأداء متّزن وكفاءة في الصيف.",
        en: "Yes. We select equipment rated for high ambient temperatures, size the loads accurately and balance the system (TAB) for even, efficient performance in summer.",
      },
    },
    {
      q: { ar: "كم مرة يحتاج التكييف للصيانة؟", en: "How often does AC need maintenance?" },
      a: {
        ar: "ننصح بصيانة دورية كل 3–6 أشهر حسب الاستخدام. عقود الصيانة السنوية تشمل الفحص والتنظيف وتقارير الأداء والدعم بالأولوية.",
        en: "We recommend service every 3–6 months depending on usage. Annual contracts cover inspection, cleaning, performance reports and priority support.",
      },
    },
    {
      q: { ar: "هل تقدّمون توريد وتركيب أم صيانة فقط؟", en: "Do you handle supply and installation, or maintenance only?" },
      a: {
        ar: "دورة كاملة: دراسة، توريد معدات معتمدة، تركيب، اختبار وتشغيل، ثم صيانة وعقود سنوية.",
        en: "The full cycle: study, certified-equipment supply, installation, testing and commissioning, then maintenance and annual contracts.",
      },
    },
    {
      q: { ar: "هل يمكن التحكّم في التكييف عبر الجوال؟", en: "Can the AC be controlled from a phone?" },
      a: {
        ar: "نعم، نربط الأنظمة بالتطبيق والمناطق والحساسات مع جداول تشغيل تقلّل الاستهلاك.",
        en: "Yes, we connect the systems to an app, zones and sensors with schedules that cut consumption.",
      },
    },
    {
      q: { ar: "هل تلتزمون بماركة واحدة أم تختارون الأنسب؟", en: "Are you tied to one brand, or do you pick the best fit?" },
      a: {
        ar: "لسنا وكلاء لماركة واحدة؛ نرشّح المعدات المعتمدة الأنسب لمشروعك حسب الأداء والحمل والميزانية — قرار هندسي محايد لمصلحتك.",
        en: "We're not a single-brand agency; we recommend the certified equipment that best fits your project by performance, load and budget — a neutral engineering decision in your interest.",
      },
    },
    {
      q: { ar: "كيف أحصل على عرض سعر؟", en: "How do I get a quote?" },
      a: {
        ar: "نبدأ بمعاينة الموقع ودراسة الحمل، ثم نجهّز عرضًا واضحًا للتوريد والتنفيذ والصيانة.",
        en: "We start with a site survey and load study, then prepare a clear proposal for supply, execution and maintenance.",
      },
    },
  ],

  glide: [
    {
      q: { ar: "ما الفرق بين المصاعد بغرفة ماكينة (MR) وبدونها (MRL)؟", en: "What's the difference between machine-room (MR) and machine-room-less (MRL) lifts?" },
      a: {
        ar: "MRL يوفّر مساحة غرفة الماكينة وأنسب للمباني الحديثة، وMR يناسب الأحمال والسرعات العالية. الاختيار يعتمد على الارتفاع والحمولة والسرعة والبئر.",
        en: "MRL saves the machine-room space and suits modern buildings; MR fits higher loads and speeds. The choice depends on rise, load, speed and shaft.",
      },
    },
    {
      q: { ar: "هل يمكن تركيب مصعد في فيلا أو منزل قائم؟", en: "Can a lift be installed in an existing villa or home?" },
      a: {
        ar: "نعم، لدينا حلول مصاعد منزلية مدمجة تناسب الفلل، مع دراسة للمساحة والبئر واختيار النظام الأنسب.",
        en: "Yes, we have compact home-lift solutions for villas, with a study of the space and shaft to pick the right system.",
      },
    },
    {
      q: { ar: "هل تقدّمون تحديثًا للمصاعد القديمة؟", en: "Do you modernize old elevators?" },
      a: {
        ar: "نعم، نرفع كفاءة المصاعد القائمة (تحديث اللوحات والمعدات) على مراحل، دون استبدال كامل حيثما أمكن.",
        en: "Yes, we upgrade existing lifts (controllers and equipment) in stages, without a full replacement where possible.",
      },
    },
    {
      q: { ar: "ما معايير الأمان والاعتماد؟", en: "What safety standards and approvals apply?" },
      a: {
        ar: "ننفّذ وفق مواصفات السلامة المعتمدة (الكود ومتطلبات SASO) مع اختبار وتسليم موثّق وعقود صيانة تضمن الجاهزية.",
        en: "We execute to approved safety specifications (code and SASO requirements) with documented testing, handover and maintenance contracts that keep lifts ready.",
      },
    },
    {
      q: { ar: "كم تستغرق فترة التركيب؟", en: "How long does installation take?" },
      a: {
        ar: "تختلف حسب نوع المصعد وعدد الوقفات وجاهزية الموقع؛ نحدّد جدولًا واضحًا بعد المعاينة.",
        en: "It varies by lift type, number of stops and site readiness; we set a clear schedule after the survey.",
      },
    },
    {
      q: { ar: "هل تشمل الصيانة قطع غيار أصلية واستجابة طوارئ؟", en: "Does maintenance include genuine parts and emergency response?" },
      a: {
        ar: "نعم، عقودنا تشمل زيارات مجدولة وقطعًا معتمدة واستجابة للحالات الطارئة.",
        en: "Yes, our contracts include scheduled visits, certified parts and emergency response.",
      },
    },
  ],

  shield: [
    {
      q: { ar: "هل أنظمتكم معتمدة من الدفاع المدني؟", en: "Are your systems approved by Civil Defense?" },
      a: {
        ar: "نعم، نصمّم وننفّذ وفق كود البناء السعودي واشتراطات الدفاع المدني، مع توثيق ومطابقة لكل نظام.",
        en: "Yes, we design and execute to the Saudi building code and Civil Defense requirements, with documentation and compliance for every system.",
      },
    },
    {
      q: { ar: "هل يمكن ربط كاميرات المراقبة بالجوال؟", en: "Can surveillance cameras be viewed on a phone?" },
      a: {
        ar: "نعم، نوفّر مراقبة مباشرة عبر الجوال على مدار 24 ساعة مع تسجيل وتنبيهات.",
        en: "Yes, we provide 24/7 live viewing on mobile with recording and alerts.",
      },
    },
    {
      q: { ar: "ما أنظمة إطفاء الحريق التي تقدّمونها؟", en: "Which fire-suppression systems do you offer?" },
      a: {
        ar: "كشف وإنذار ومكافحة — بما فيها أنظمة الغاز (مثل FM200) والرشاشات — حسب طبيعة المبنى ومتطلبات الدفاع المدني.",
        en: "Detection, alarm and suppression — including gas systems (e.g. FM200) and sprinklers — based on the building and Civil Defense requirements.",
      },
    },
    {
      q: { ar: "هل تجمعون الأنظمة في منصّة واحدة؟", en: "Do you integrate everything into one platform?" },
      a: {
        ar: "نعم، ندمج الحريق والمراقبة والتحكّم بالدخول والتيار المنخفض في منصّة مراقبة موحّدة.",
        en: "Yes, we integrate fire, surveillance, access control and low-current into one monitoring platform.",
      },
    },
    {
      q: { ar: "هل توفّرون كاميرات مراقبة بالطاقة الشمسية؟", en: "Do you offer solar-powered surveillance cameras?" },
      a: {
        ar: "نعم، كاميرات تعمل بالطاقة الشمسية للمواقع البعيدة أو بدون بنية كهربائية.",
        en: "Yes, solar-powered cameras for remote sites or locations without electrical infrastructure.",
      },
    },
    {
      q: { ar: "هل تقدّمون عقود صيانة؟", en: "Do you provide maintenance contracts?" },
      a: {
        ar: "نعم، فحص دوري وصيانة موثّقة تُبقي الأنظمة جاهزة قبل الحاجة إليها.",
        en: "Yes, periodic inspection and documented maintenance that keep systems ready before they're needed.",
      },
    },
  ],

  os: [
    {
      q: { ar: "أختار نظام ERP جاهز أم نظام مخصّص؟", en: "Should I pick a ready ERP or a custom system?" },
      a: {
        ar: "الجاهز (سيلترا ERP) يبدأ سريعًا باشتراك ويناسب الاحتياجات القياسية؛ المخصّص يُبنى حول إجراءاتك حين تحتاج تكاملًا خاصًا. نرشّح الأنسب بعد جلسة اكتشاف.",
        en: "The ready product (Syltra ERP) starts fast on a subscription and suits standard needs; a custom system is built around your processes when you need special integration. We recommend the fit after a discovery session.",
      },
    },
    {
      q: { ar: "هل تدعمون التكامل مع أنظمتنا الحالية؟", en: "Do you integrate with our existing systems?" },
      a: {
        ar: "نعم، نربط أنظمتك القائمة (محاسبة، مخزون، موارد) في تدفّق واحد عبر واجهات تكامل.",
        en: "Yes, we connect your existing systems (accounting, inventory, HR) into one flow through integration interfaces.",
      },
    },
    {
      q: { ar: "هل حلول الذكاء الاصطناعي تدعم العربية؟", en: "Do your AI solutions support Arabic?" },
      a: {
        ar: "نعم، نبني مساعدين ونماذج تحليل تدعم اللغة العربية وتخدم قرارك اليومي.",
        en: "Yes, we build assistants and analytics models that support Arabic and serve your daily decisions.",
      },
    },
    {
      q: { ar: "من يملك الكود والبيانات؟", en: "Who owns the code and the data?" },
      a: {
        ar: "أنت تملك بياناتك؛ ونتفق على ملكية الكود بوضوح حسب نوع المشروع (مخصّص مقابل منتج باشتراك).",
        en: "You own your data; code ownership is agreed clearly up front based on the engagement (custom vs subscription product).",
      },
    },
    {
      q: { ar: "كم يستغرق بناء نظام؟", en: "How long does it take to build a system?" },
      a: {
        ar: "يعتمد على النطاق؛ نعمل بمنهجية رشيقة نطلق فيها نسخة أولى سريعًا ثم نطوّر.",
        en: "It depends on scope; we work in an agile way, shipping a first version quickly then iterating.",
      },
    },
    {
      q: { ar: "هل تقدّمون دعمًا بعد الإطلاق؟", en: "Do you provide post-launch support?" },
      a: {
        ar: "نعم، تحديث ورعاية ودعم مستمر بعد التشغيل.",
        en: "Yes, updates, care and ongoing support after go-live.",
      },
    },
  ],
};

/** General Syltra One FAQ (the group). */
export const GENERAL_FAQ: QA[] = [
  {
    q: { ar: "ما هي سيلترا وان؟", en: "What is Syltra One?" },
    a: {
      ar: "مجموعة تقنية سعودية تضم خمسة أقسام: الحياة الذكية (لايف)، والبرمجيات والذكاء الاصطناعي (او-إس)، والتكييف (كلايمت)، والأمن والسلامة (شيلد)، والمصاعد (جلايد) — تحت هوية ومعايير واحدة.",
      en: "A Saudi technology group of five divisions: smart living (Life), software & AI (OS), HVAC (Climate), security & safety (Shield) and elevators (Glide) — under one identity and standards.",
    },
  },
  {
    q: { ar: "لماذا أتعامل مع مجموعة واحدة بدل موردين متفرّقين؟", en: "Why work with one group instead of scattered vendors?" },
    a: {
      ar: "مسؤولية واحدة تدير التصميم والتنفيذ والصيانة عبر كل الأنظمة، بمعايير موحّدة وتكامل حقيقي بينها.",
      en: "One accountability owning design, execution and maintenance across every system, with unified standards and real integration.",
    },
  },
  {
    q: { ar: "أين تعملون؟", en: "Where do you operate?" },
    a: {
      ar: "مقرّنا الرياض ونخدم المملكة العربية السعودية، مع خطة توسّع في دول الخليج.",
      en: "We're based in Riyadh and serve Saudi Arabia, with a plan to expand across the Gulf.",
    },
  },
  {
    q: { ar: "هل تنفّذون مشاريع تشمل أكثر من قسم؟", en: "Do you deliver projects spanning more than one division?" },
    a: {
      ar: "نعم، نجمع أقسام سيلترا وان في خطة واحدة من الدراسة حتى التشغيل والصيانة.",
      en: "Yes, we bring Syltra One's divisions into one plan from study to operation and maintenance.",
    },
  },
  {
    q: { ar: "كيف أطلب عرض سعر أو استشارة؟", en: "How do I request a quote or consultation?" },
    a: {
      ar: "تواصل معنا أو احجز معاينة، ونحدّد احتياجك ونجهّز عرضًا واضحًا.",
      en: "Contact us or book a survey; we scope your need and prepare a clear proposal.",
    },
  },
  {
    q: { ar: "هل أنتم داعمون لرؤية 2030؟", en: "Are you aligned with Saudi Vision 2030?" },
    a: {
      ar: "نعم، نبني تقنية وطنية تخدم أهداف التحوّل الرقمي وجودة الحياة والاقتصاد المتنوّع.",
      en: "Yes, we build national technology that serves digital-transformation, quality-of-life and diversified-economy goals.",
    },
  },
];
