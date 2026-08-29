import type { L } from "@/lib/health-content";

/** A CTA button. `primary` fills with the accent; otherwise it's a text link. */
export type HButton = { label: L; href: string; primary?: boolean };

/** Content blocks a HEALTH page is composed of. Rendered by <HealthBlocks />. */
export type Block =
  | { kind: "hero"; eyebrow?: L; headline: L; body: L; buttons?: HButton[]; graphic?: "connect" | "ring" | "scene"; image?: string }
  | { kind: "section"; eyebrow?: L; headline?: L; body?: L }
  | { kind: "cards"; headline?: L; body?: L; items: { title: L; body: L }[] }
  | { kind: "list"; headline?: L; body?: L; items: L[] }
  | { kind: "journey"; headline?: L; body?: L; steps: { label: L; body: L }[] }
  | { kind: "steps"; headline?: L; steps: { title: L; body: L }[] }
  | { kind: "safety"; text: L }
  | { kind: "links"; headline?: L; items: HButton[] }
  | { kind: "integrations" }
  | { kind: "cta"; headline: L; body?: L; buttons: HButton[] };

export type HealthPage = {
  slug: string; // locale-less path under /health, e.g. "" or "/how-it-works"
  seoTitle: L;
  seoDescription: L;
  blocks: Block[];
};

const CTA_EARLY: HButton = { label: { ar: "انضم للتجربة المبكرة", en: "Join Early Access" }, href: "/health/contact", primary: true };
const CTA_HOW: HButton = { label: { ar: "اكتشف كيف تعمل", en: "See How It Works" }, href: "/health/how-it-works" };
const CTA_PILOT: HButton = { label: { ar: "ناقش شراكة تجريبية", en: "Discuss a Pilot Partnership" }, href: "/health/contact" };

export const HEALTH_PAGES: Record<string, HealthPage> = {
  // ---------------------------------------------------------------- HOME
  "": {
    slug: "",
    seoTitle: { ar: "سيلترا هيلث | تقنيات الصحة والرفاه المتصل", en: "SYLTRA HEALTH | Connected Health and Wellness Technology" },
    seoDescription: {
      ar: "منصة صحية تبني على المنزل الذكي وحسّاساته (سيلترا لايف), الهواء والحرارة والرطوبة والحركة، ثم تربط الساعات والقراءات في رؤية يومية واحدة للأفراد والأسر وفرق الرعاية.",
      en: "A health platform built on the smart home and its sensors (SYLTRA LIFE), air, temperature, humidity and movement, then connecting wearables and readings in one daily view for people, families and care teams.",
    },
    blocks: [
      {
        kind: "hero",
        graphic: "scene",
        eyebrow: { ar: "طبقة الذكاء الصحي في بيتك", en: "The health intelligence layer for your home" },
        headline: { ar: "بيتك يعرف لما يتغيّر شيء.", en: "Your home knows when something changes." },
        body: {
          ar: "بيتك يعرفك: متى تنام، كيف تتحرّك، وكيف يبدو يومك الجيد. سيلترا هيلث تجمع إحساس بيتك ببياناتك الصحية، فتهيّئ لك مساحة أهدأ، وتبقى قريبة حين تحتاج من يطمئن عليك.",
          en: "Your home gets to know you: when you sleep, how you move, what a good day feels like. SYLTRA HEALTH brings that sense of home together with your health data, shapes a calmer space around you, and stays close for the moment you need someone to check in.",
        },
        buttons: [CTA_EARLY, CTA_HOW],
      },
      {
        kind: "cards",
        headline: { ar: "يبدأ من البيت.", en: "It starts at home." },
        body: {
          ar: "صحتك لا تعيش داخل جهاز على معصمك. تتأثر بالهواء الذي تتنفّسه، بحرارة غرفتك ليلًا، وبإيقاع حركتك في البيت. لهذا نبدأ من حيث تقضي معظم وقتك: بيتك، الذي يبقى معك طوال اليوم.",
          en: "Your health does not live inside a device on your wrist. It is shaped by the air you breathe, how warm your room feels at night, and the rhythm of how you move at home. So we start where you spend most of your time: your home, which is with you all day.",
        },
        items: [
          { title: { ar: "حسّاسات البيئة", en: "Environmental sensors" }, body: { ar: "جودة الهواء والحرارة والرطوبة داخل مساحتك، لحظة بلحظة.", en: "Air quality, temperature and humidity in your space, moment to moment." } },
          { title: { ar: "حسّاسات الحركة", en: "Motion sensors" }, body: { ar: "تساعد على ملاحظة أنماط النشاط والخمول غير المعتادة، لتنبيه الأسرة أسرع ودعم المتابعة، وليست بديلاً عن خدمات الطوارئ.", en: "Help surface unusual activity or inactivity patterns, so family is reached faster and follow-up is supported, not a replacement for emergency services." } },
          { title: { ar: "تكامل سيلترا لايف", en: "SYLTRA LIFE integration" }, body: { ar: "بيانات المنزل الذكي تظهر داخل تجربتك الصحية بعد موافقتك.", en: "Smart-home data appears inside your health experience, with your consent." } },
          { title: { ar: "إجراءات منزلية", en: "Home actions" }, body: { ar: "إعدادات يوافق عليها المستخدم مثل ضبط التكييف والتهوية بعد اعتماد الأجهزة.", en: "User-approved settings such as air-conditioning and ventilation once devices are verified." } },
        ],
      },
      {
        kind: "safety",
        text: {
          ar: "حسّاسات الحركة تدعم الوعي والمتابعة فقط. سيلترا هيلث ليست خدمة طوارئ ولا تضمن الاستجابة، ولا تستبدل الاتصال بخدمات الطوارئ أو مقدم الرعاية عند الحاجة.",
          en: "Motion sensors support awareness and follow-up only. SYLTRA HEALTH is not an emergency service, does not guarantee response, and does not replace contacting emergency services or a care provider when needed.",
        },
      },
      {
        kind: "cards",
        headline: { ar: "إشارات متعددة. رؤية واحدة.", en: "Many signals. One clear view." },
        body: {
          ar: "صحتك اليومية لا تعيش داخل جهاز واحد. تتأثر بنومك، حركتك، قراءاتك، وروتينك والبيئة المحيطة بك. تجمع سيلترا هيلث هذه الإشارات في تجربة منظمة وسهلة الفهم.",
          en: "Everyday health does not live inside one device. It is shaped by sleep, movement, readings, routines and the surrounding environment. SYLTRA HEALTH organizes these signals into one experience that is easier to understand.",
        },
        items: [
          { title: { ar: "الهاتف", en: "Phone" }, body: { ar: "بيانات الحركة، الموقع والإدخالات التي يختارها المستخدم.", en: "Movement, location and user-selected entries." } },
          { title: { ar: "الأجهزة القابلة للارتداء", en: "Wearables" }, body: { ar: "النوم، النشاط والمؤشرات التي تدعمها الأجهزة المتوافقة.", en: "Sleep, activity and supported signals from compatible devices." } },
          { title: { ar: "الأجهزة الصحية المنزلية", en: "Home health devices" }, body: { ar: "قراءات الضغط والسكر وغيرها من الأجهزة المتوافقة.", en: "Blood pressure, glucose and other readings from compatible devices." } },
          { title: { ar: "حساسات المنزل", en: "Home sensors" }, body: { ar: "جودة الهواء، الحرارة والرطوبة والبيانات البيئية المتاحة.", en: "Available air quality, temperature, humidity and environmental data." } },
        ],
      },
      {
        kind: "journey",
        headline: { ar: "التقنية الصحية الأقرب إلى يومك.", en: "Health technology built around your day." },
        body: {
          ar: "من لحظة الاستيقاظ إلى نهاية اليوم، تساعدك سيلترا هيلث على رؤية ما يحدث عبر الوقت، بدلاً من التعامل مع كل قراءة بصورة منفصلة.",
          en: "From the moment you wake up to the end of the day, SYLTRA HEALTH helps you see what happens over time instead of treating every reading as a separate event.",
        },
        steps: [
          { label: { ar: "الصباح", en: "Morning" }, body: { ar: "ملخص النوم والتعافي وبيئة الغرفة.", en: "A summary of sleep, recovery and room conditions." } },
          { label: { ar: "خلال اليوم", en: "During the day" }, body: { ar: "النشاط والحركة والقراءات التي يضيفها المستخدم.", en: "Activity, movement and readings added by the user." } },
          { label: { ar: "المساء", en: "Evening" }, body: { ar: "صورة مبسطة لليوم والأنماط المتكررة.", en: "A simplified view of the day and recurring patterns." } },
          { label: { ar: "عند المتابعة", en: "During follow-up" }, body: { ar: "تقرير مختار يشاركه المستخدم مع الأسرة أو فريق الرعاية.", en: "A selected report shared with family or a care team." } },
        ],
      },
      {
        kind: "cards",
        headline: { ar: "تجربة واحدة لمراحل واحتياجات مختلفة.", en: "One experience for different needs and life stages." },
        items: [
          { title: { ar: "للأفراد", en: "For individuals" }, body: { ar: "فهم أوضح للنوم والنشاط والروتين اليومي.", en: "A clearer view of sleep, activity and daily routines." } },
          { title: { ar: "لكبار السن", en: "For older adults" }, body: { ar: "متابعة يومية تحترم الاستقلالية وتمنح الأسرة الاطمئنان بموافقة المستخدم.", en: "Daily visibility that respects independence and reassures families with the user's permission." } },
          { title: { ar: "للحالات المزمنة", en: "For chronic conditions" }, body: { ar: "جمع القراءات والعادات في صورة متصلة تدعم المتابعة.", en: "Readings and routines brought together to support follow-up." } },
          { title: { ar: "لمقدمي الرعاية", en: "For care providers" }, body: { ar: "ملخصات منظمة يختار المستخدم مشاركتها بين الزيارات.", en: "Organized summaries that users choose to share between visits." } },
        ],
      },
      {
        kind: "section",
        eyebrow: { ar: "من البيانات إلى الفهم", en: "From data to understanding" },
        headline: { ar: "يتعلّم إيقاعك.", en: "It learns your rhythm." },
        body: {
          ar: "الأرقام وحدها باردة. سيلترا هيلث تتعرّف على إيقاعك: متى تنام، كيف تمرّ ساعاتك، والجو الذي يريحك في بيتك. ومع الوقت تعرف الفرق بين يومٍ عادي ويومٍ يختلف عنك، فتنتبه فقط حين يستحق الأمر الانتباه.",
          en: "Numbers on their own feel cold. SYLTRA HEALTH gets to know your rhythm: when you sleep, how your hours pass, and the setting that puts you at ease at home. Over time it learns the difference between an ordinary day and one that is unlike you, so it pays attention only when it truly matters.",
        },
      },
      {
        kind: "section",
        eyebrow: { ar: "من الفهم إلى الاستجابة", en: "From understanding to response" },
        headline: { ar: "لا يكتفي بأن يعرف. يهتمّ.", en: "It does more than know. It cares." },
        body: {
          ar: "أن يعرف بيتك أنك لست على ما يُرام شيء، وأن يتصرّف بلطف شيء آخر. يهيّئ لك جوًا أنسب، ويسألك باطمئنان حين يلاحظ اختلافًا، وإن لم تردّ، يصل بهدوء إلى أقرب شخص تثق به وفق خطة رسمتها أنت. لا يتسرّع بقراءة واحدة، بل يتمهّل ويتأكّد أولًا.",
          en: "There is a difference between your home knowing you are unwell and it doing something kind about it. It shapes a calmer setting for you, checks in gently when it notices something is off, and if you do not answer, it quietly reaches the closest person you trust, under a plan you set. It does not rush on a single reading. It takes a breath and makes sure first.",
        },
      },
      {
        kind: "cards",
        headline: { ar: "مستويات الاستجابة.", en: "Levels of response." },
        body: {
          ar: "تبدأ الاستجابة من الأخف، ولا تتصاعد إلا عند اجتماع مؤشرات تستحق ذلك، وبموافقتك المسبقة في كل مستوى.",
          en: "Response starts at the lightest level and only escalates when signals genuinely warrant it, under your prior consent at each level.",
        },
        items: [
          { title: { ar: "دعم يومي", en: "Everyday support" }, body: { ar: "تذكير بالحركة أو القياس أو الماء، وتهيئة إعدادات الراحة.", en: "Reminders to move, measure or hydrate, and comfort-setting adjustments." } },
          { title: { ar: "تحقّق", en: "Check-in" }, body: { ar: "سؤال مباشر لك عند وجود تغيّر ملحوظ في النمط أو القراءة.", en: "A direct check-in when there is a noticeable change in pattern or reading." } },
          { title: { ar: "تنبيه شخص موثوق", en: "Alert a trusted person" }, body: { ar: "تنبيه الشخص الأنسب عند طلبك المساعدة أو عدم استجابتك مع مؤشرات متزامنة.", en: "Alerting the most suitable person when you ask for help, or do not respond while signals coincide." } },
          { title: { ar: "تصعيد معتمد", en: "Approved escalation" }, body: { ar: "إجراء إضافي ضمن خطة موثّقة، بعد توفر التكاملات والاعتمادات الرسمية.", en: "A further step within a documented plan, once official integrations and approvals are in place." } },
        ],
      },
      {
        kind: "section",
        eyebrow: { ar: "الدائرة الموثوقة", en: "Trusted circle" },
        headline: { ar: "لو ما رديت، يعرف من الأقرب.", en: "If you do not answer, it knows who is closest." },
        body: {
          ar: "الأشخاص الذين نحبّهم لا نريد إزعاجهم بلا داعٍ، لكن نريدهم قريبين وقت الحاجة. تختار دائرتك الموثوقة، وتحدّد من الأقرب ومن يرى ماذا. وحين يلزم الأمر، يصل التنبيه إلى الشخص الأنسب فقط، بأقل ما يلزم من المعلومات، لا رسالة قلق تصل الجميع.",
          en: "The people we love, we do not want to worry for no reason, yet we want them near when it counts. You choose your trusted circle and set who is closest and who sees what. When it matters, the alert reaches only the most suitable person, with the least information needed, not a wave of worry sent to everyone.",
        },
      },
      {
        kind: "safety",
        text: {
          ar: "سيلترا هيلث لا تقدّم تشخيصًا طبيًا مستقلاً، وليست خدمة طوارئ، ولا تضمن وصول المساعدة، ولا تتصل بالإسعاف تلقائيًا. تكتشف تغيّرات غير معتادة في البيانات المتاحة، وتساعد في التحقق وتنبيه الأشخاص الموثوقين وفق خطتك.",
          en: "SYLTRA HEALTH does not provide an independent medical diagnosis, is not an emergency service, does not guarantee help arrives, and does not auto-dial emergency services. It detects unusual changes in the available data and helps with verification and alerting trusted people under your plan.",
        },
      },
      {
        kind: "section",
        eyebrow: { ar: "الخصوصية", en: "Privacy" },
        headline: { ar: "أنت تحدّد من يعرف ماذا.", en: "You decide who knows what." },
        body: {
          ar: "تختار الأجهزة المتصلة، والبيانات المسموح باستخدامها، والأشخاص الموثوقين، والمعلومات التي يرونها، ووقت إيقاف المشاركة. لا تُجمع البيانات لمجرد توفّرها، وتُشارك أقل كمية لازمة فقط.",
          en: "You choose the connected devices, the data allowed to be used, the trusted people, what they see and when sharing stops. Data is not collected just because it is available, and only the minimum necessary is shared.",
        },
      },
      { kind: "integrations" },
      {
        kind: "cta",
        headline: { ar: "ابدأ بصورة أوضح لصحتك اليومية.", en: "Start with a clearer view of everyday health." },
        body: {
          ar: "انضم إلى قائمة التجربة المبكرة أو ناقش معنا برنامجاً تجريبياً لمؤسستك.",
          en: "Join the early-access list or discuss a pilot program for your organization.",
        },
        buttons: [CTA_EARLY, CTA_PILOT],
      },
    ],
  },

  // -------------------------------------------------------- HOW IT WORKS
  "how-it-works": {
    slug: "/how-it-works",
    seoTitle: { ar: "كيف تعمل سيلترا هيلث | SYLTRA HEALTH", en: "How It Works | SYLTRA HEALTH" },
    seoDescription: {
      ar: "من بيانات متفرقة إلى صورة مترابطة: اربط، اجمع، افهم، وشارك، بموافقتك وتحت سيطرتك.",
      en: "From scattered data to one connected picture: connect, bring together, understand and share, with your consent and under your control.",
    },
    blocks: [
      {
        kind: "hero",
        graphic: "scene",
        image: "/brand/health-hero-how.jpg",
        headline: { ar: "من الإشارات إلى الاستجابة.", en: "From signals to response." },
        body: {
          ar: "تربط سيلترا هيلث بيانات جسمك بمحيطك بعد موافقتك، تتعلّم نمطك، تهيّئ بيئتك، ثم تحوّل التغيّرات المهمة إلى تحقّق واستجابة وفق خطتك.",
          en: "With your consent, SYLTRA HEALTH connects your body's data with your surroundings, learns your pattern, adapts your environment, then turns meaningful changes into verification and response under your plan.",
        },
        buttons: [CTA_EARLY],
      },
      {
        kind: "steps",
        steps: [
          { title: { ar: "اربط", en: "Connect" }, body: { ar: "اختر الأجهزة والتطبيقات والحساسات المتوافقة. لا يبدأ الربط من دون موافقتك، ولكل نوع بيانات موافقة محددة.", en: "Choose the compatible devices, apps and sensors. Connection does not begin without your permission, with specific consent for each data type." } },
          { title: { ar: "تعلّم نمطك", en: "Learn your pattern" }, body: { ar: "تبني المنصة خطك الأساسي: أوقات نومك، حركتك المعتادة، والبيئة المنزلية المرتبطة براحتك.", en: "The platform builds your baseline: sleep times, usual movement, and the home environment tied to your comfort." } },
          { title: { ar: "هيّئ بيئتك", en: "Adapt your space" }, body: { ar: "ينفّذ المنزل إعدادات وافقت عليها مسبقًا: ضبط الحرارة، تحسين التهوية، إضاءة مناسبة، وتذكير بالحركة أو القياس.", en: "The home runs settings you approved in advance: temperature, better ventilation, suitable lighting, and reminders to move or measure." } },
          { title: { ar: "تحقّق واستجب", en: "Verify and respond" }, body: { ar: "عند تغيّر مهم، يتحقق منك أولًا، ثم يصل إلى الشخص الموثوق الأنسب وفق خطة الاستجابة التي اخترتها.", en: "On a meaningful change, it checks in with you first, then reaches the most suitable trusted person under the response plan you chose." } },
        ],
      },
      {
        kind: "cards",
        headline: { ar: "مسار الاستجابة الذكية.", en: "How intelligent response works." },
        body: {
          ar: "عند ظهور تغيّر غير معتاد، لا يعتمد النظام على قراءة منفردة، بل يمرّ بخطوات واضحة وقابلة للتفسير.",
          en: "When an unusual change appears, the system never relies on a single reading. It follows clear, explainable steps.",
        },
        items: [
          { title: { ar: "جمع الإشارات", en: "Collect signals" }, body: { ar: "المؤشرات الصحية والحركة ووجود الأشخاص وبيئة المنزل في اللحظة نفسها.", en: "Health signals, movement, presence and home environment at the same moment." } },
          { title: { ar: "المقارنة بالنمط", en: "Compare to baseline" }, body: { ar: "مقارنة الإشارات بنمطك الشخصي وسجلك السابق لتقدير مستوى التنبيه.", en: "Comparing signals to your personal baseline and history to gauge the alert level." } },
          { title: { ar: "التحقّق منك", en: "Check in with you" }, body: { ar: "سؤال مباشر على الهاتف أو الساعة أو شاشة المنزل: هل أنت بخير؟", en: "A direct check-in on your phone, watch or home screen: are you okay?" } },
          { title: { ar: "انتظار الاستجابة", en: "Wait for a response" }, body: { ar: "الانتظار خلال المدة التي حدّدتها قبل أي خطوة تالية.", en: "Waiting for the period you defined before any next step." } },
          { title: { ar: "اختيار الأنسب", en: "Choose the right person" }, body: { ar: "اختيار الشخص الموثوق الأنسب وفق القرب وزمن الوصول والقبول.", en: "Selecting the most suitable trusted person by proximity, arrival time and acceptance." } },
          { title: { ar: "تصعيد معتمد", en: "Approved escalation" }, body: { ar: "تصعيد وفق الخطة التي اعتمدتها مسبقًا، مع الحد الأدنى من المعلومات.", en: "Escalating under the plan you approved in advance, with minimal information." } },
        ],
      },
      {
        kind: "cards",
        headline: { ar: "المكوّنات الأساسية.", en: "The core components." },
        body: {
          ar: "خمس طبقات تعمل معًا. الاستجابة الذكية ليست ميزة منفصلة، بل النتيجة التي تعمل لأجلها كل الطبقات.",
          en: "Five layers working together. Intelligent response is not a separate feature, it is the outcome all the layers work toward.",
        },
        items: [
          { title: { ar: "الصحة المتصلة", en: "Connected Health" }, body: { ar: "ربط بيانات الصحة واللياقة من المصادر المعتمدة والمصرّح بها.", en: "Connecting health and fitness data from approved, authorized sources." } },
          { title: { ar: "وعي المنزل", en: "Home Awareness" }, body: { ar: "فهم الحركة والوجود والبيئة المنزلية.", en: "Understanding movement, presence and the home environment." } },
          { title: { ar: "النمط الشخصي", en: "Personal Baseline" }, body: { ar: "تعلّم النمط الطبيعي لكل مستخدم مع مرور الوقت.", en: "Learning each user's normal pattern over time." } },
          { title: { ar: "البيئة المتكيّفة", en: "Adaptive Environment" }, body: { ar: "تكييف بيئة المنزل وفق الإعدادات الصحية والروتين.", en: "Adapting the home environment to health settings and routine." } },
          { title: { ar: "الاستجابة الذكية", en: "Intelligent Response" }, body: { ar: "تحويل التغيّرات المهمة إلى تحقّق وتنبيه وتصعيد شخصي.", en: "Turning meaningful changes into verification, alerting and personal escalation." } },
        ],
      },
      {
        kind: "journey",
        headline: { ar: "كيف تبدأ.", en: "How you get started." },
        body: {
          ar: "أنت تضبط التجربة من البداية، وتجرّبها بأمان قبل تفعيل أي تنبيه حقيقي.",
          en: "You set the experience up from the start, and try it safely before any real alert is active.",
        },
        steps: [
          { label: { ar: "اضبط موافقاتك", en: "Set your consents" }, body: { ar: "اربط المصادر التي تريدها فقط، ولكل نوع بيانات موافقة محددة يمكن سحبها.", en: "Connect only the sources you want, with specific, revocable consent per data type." } },
          { label: { ar: "ابنِ دائرتك الموثوقة", en: "Build your trusted circle" }, body: { ar: "أضف الأشخاص الذين تثق بهم وحدّد لكل واحد علاقته وأولويته وما يراه.", en: "Add the people you trust and set each one's relationship, priority and what they see." } },
          { label: { ar: "اختر خطة الاستجابة", en: "Choose your response plan" }, body: { ar: "حدّد متى يتحقق النظام، ومدة الانتظار، ومن يُنبَّه في كل مستوى.", en: "Decide when the system checks in, how long it waits, and who is alerted at each level." } },
          { label: { ar: "جرّب في وضع الاختبار", en: "Try it in test mode" }, body: { ar: "شغّل محاكاة تريك كيف تعمل الاستجابة دون إرسال أي تنبيه حقيقي.", en: "Run a simulation that shows how the response works without sending any real alert." } },
        ],
      },
      {
        kind: "safety",
        text: {
          ar: "سيلترا هيلث لا تقدّم تشخيصًا مستقلاً وليست خدمة طوارئ، ولا تضمن وصول المساعدة ولا تتصل بالإسعاف تلقائيًا. تبدأ النسخة الأولى بقواعد واضحة قابلة للاختبار، ثم يُضاف التعلّم الشخصي لاكتشاف الانحراف عن النمط.",
          en: "SYLTRA HEALTH does not provide an independent diagnosis and is not an emergency service. It does not guarantee help arrives or auto-dial emergency services. The first version starts with clear, testable rules, then adds personal learning to detect deviation from the pattern.",
        },
      },
    ],
  },

  // ----------------------------------------------------------- INDIVIDUALS
  individuals: {
    slug: "/individuals",
    seoTitle: { ar: "للأفراد | سيلترا هيلث", en: "For Individuals | SYLTRA HEALTH" },
    seoDescription: {
      ar: "اجمع نومك ونشاطك وقراءاتك وبيئة منزلك في مكان واحد، وركز على الصورة بدلاً من التنقل بين التطبيقات.",
      en: "Bring sleep, activity, readings and your home environment into one place and focus on the bigger picture instead of moving between apps.",
    },
    blocks: [
      {
        kind: "hero",
        graphic: "scene",
        image: "/brand/health-hero-individuals.jpg",
        eyebrow: { ar: "للأفراد", en: "For Individuals" },
        headline: { ar: "تجربة صحية أقرب إلى حياتك.", en: "A health experience closer to real life." },
        body: {
          ar: "اجمع نومك ونشاطك وقراءاتك وبيئة منزلك في مكان واحد، وركز على الصورة بدلاً من التنقل بين التطبيقات.",
          en: "Bring sleep, activity, readings and your home environment into one place and focus on the bigger picture instead of moving between apps.",
        },
        buttons: [CTA_EARLY],
      },
      {
        kind: "list",
        headline: { ar: "ما الذي تحصل عليه.", en: "What you get." },
        items: [
          { ar: "ملخص يومي واضح.", en: "A clear daily summary." },
          { ar: "اتجاهات عبر الأيام والأسابيع.", en: "Trends across days and weeks." },
          { ar: "ربط القراءات بالسياق اليومي.", en: "Readings connected to daily context." },
          { ar: "تقارير يختار المستخدم مشاركتها.", en: "Reports shared only when the user chooses." },
          { ar: "إعدادات خصوصية قابلة للتحكم.", en: "Controllable privacy settings." },
        ],
      },
    ],
  },

  // ---------------------------------------------------------- OLDER ADULTS
  "older-adults": {
    slug: "/older-adults",
    seoTitle: { ar: "تقنيات صحية لكبار السن | SYLTRA HEALTH", en: "Connected Health for Older Adults | SYLTRA HEALTH" },
    seoDescription: {
      ar: "رؤية مبسطة ليوم كبار السن، مع مشاركة المعلومات المختارة مع الأسرة أو مقدم الرعاية بموافقة واضحة.",
      en: "A simpler view of an older adult's day, with selected information shared with family or a care provider through clear consent.",
    },
    blocks: [
      {
        kind: "hero",
        graphic: "scene",
        image: "/brand/health-hero-older.jpg",
        eyebrow: { ar: "كبار السن", en: "Older Adults" },
        headline: { ar: "استقلالية أكبر. اطمئنان أقرب.", en: "Greater independence. Closer reassurance." },
        body: {
          ar: "تمنح سيلترا هيلث كبار السن رؤية مبسطة ليومهم، وتتيح مشاركة المعلومات المختارة مع الأسرة أو مقدم الرعاية بموافقة واضحة.",
          en: "SYLTRA HEALTH gives older adults a simpler view of their day and allows selected information to be shared with family or a care provider through clear consent.",
        },
        buttons: [{ label: { ar: "سجّل اهتمامك بحلول كبار السن", en: "Register Interest in Older Adult Solutions" }, href: "/health/contact", primary: true }],
      },
      {
        kind: "section",
        eyebrow: { ar: "سيناريو", en: "Scenario" },
        headline: { ar: "عندما يختلف صباحٌ معتاد.", en: "When a usual morning is different." },
        body: {
          ar: "مستخدم كبير في السن لديه نمط حركة صباحي ثابت داخل المنزل. في أحد الأيام لم تسجّل الحساسات حركته في الوقت المعتاد، وسجّلت الساعة تغيّرًا في النبض، ولم يستجب للتنبيه. تراجع المنصة: هل هو داخل المنزل؟ هل عدم الحركة طبيعي في هذا التوقيت؟ هل توجد قراءة مختلفة عن نمطه؟ هل يوجد أحد من الأسرة؟ من أقرب شخص موثوق يستطيع الوصول؟ وبعد التحقق، تشغّل مستوى الاستجابة المناسب بدلًا من إرسال إنذار عام لكل الأسرة.",
          en: "An older user has a steady morning movement pattern at home. One day the sensors do not record movement at the usual time, the watch notes a change in pulse, and there is no response to the check-in. The platform reviews: is the user home? Is this stillness normal for this hour? Is there a reading unlike their pattern? Is any family member present? Who is the nearest trusted person who can reach them? After verifying, it triggers the appropriate level of response instead of a general alarm to the whole family.",
        },
      },
      {
        kind: "section",
        headline: { ar: "دعم يحترم الإنسان وخصوصيته.", en: "Support without surveillance." },
        body: {
          ar: "صُممت التجربة لتدعم الاستقلالية، لا لتحويل المنزل إلى مساحة مراقبة. يحدد المستخدم من يرى المعلومات، وما الذي يراه، ومدة الوصول.",
          en: "The experience is designed to support independence, not turn the home into a surveillance space. The user decides who sees information, what they see and for how long.",
        },
      },
      {
        kind: "list",
        headline: { ar: "حالات الاستخدام.", en: "Use cases." },
        items: [
          { ar: "متابعة النشاط والنوم على مدى الوقت.", en: "View activity and sleep over time." },
          { ar: "عرض قراءات الأجهزة الصحية المتوافقة.", en: "Display readings from compatible home health devices." },
          { ar: "فهم أثر الحرارة والرطوبة وجودة الهواء داخل المنزل.", en: "Understand indoor temperature, humidity and air-quality context." },
          { ar: "مشاركة ملخص يومي أو أسبوعي مع شخص موثوق.", en: "Share a daily or weekly summary with a trusted person." },
          { ar: "دعم المتابعة بين الزيارات الطبية.", en: "Support follow-up between clinical visits." },
        ],
      },
      {
        kind: "safety",
        text: {
          ar: "سيلترا هيلث ليست خدمة طوارئ ولا تستبدل الاتصال بخدمات الطوارئ أو مقدم الرعاية عند الحاجة.",
          en: "SYLTRA HEALTH is not an emergency service and does not replace contacting emergency services or a care provider when needed.",
        },
      },
    ],
  },

  // ------------------------------------------------------ CHRONIC CONDITIONS
  "chronic-conditions": {
    slug: "/chronic-conditions",
    seoTitle: { ar: "الحالات المزمنة | سيلترا هيلث", en: "Chronic Conditions | SYLTRA HEALTH" },
    seoDescription: {
      ar: "اجمع القراءات اليومية والنشاط والنوم والسياق المنزلي في رؤية متصلة تدعم المتابعة مع فريق الرعاية.",
      en: "Bring daily readings, activity, sleep and home context into one connected view that supports follow-up with a care team.",
    },
    blocks: [
      {
        kind: "hero",
        graphic: "scene",
        image: "/brand/health-hero-chronic.jpg",
        eyebrow: { ar: "الحالات المزمنة", en: "Chronic Conditions" },
        headline: { ar: "متابعة يومية. صورة أوضح.", en: "Daily tracking. A clearer picture." },
        body: {
          ar: "تساعد سيلترا هيلث على جمع القراءات اليومية والنشاط والنوم والسياق المنزلي في رؤية متصلة تدعم الحوار والمتابعة مع فريق الرعاية.",
          en: "SYLTRA HEALTH brings daily readings, activity, sleep and home context into one connected view that supports follow-up and conversations with a care team.",
        },
        buttons: [CTA_EARLY],
      },
      {
        kind: "section",
        headline: { ar: "السياق يصنع الفرق.", en: "Context matters." },
        body: {
          ar: "القراءة الواحدة مهمة، لكن سياق الأيام والأسابيع يساعد على بناء صورة أكثر اكتمالاً. ترتب سيلترا هيلث المعلومات التي يختارها المستخدم دون تقديم تشخيص أو تغيير خطة العلاج.",
          en: "One reading matters, but context across days and weeks helps create a more complete picture. SYLTRA HEALTH organizes user-selected information without diagnosing or changing a treatment plan.",
        },
      },
      {
        kind: "links",
        headline: { ar: "حسب الحالة", en: "By condition" },
        items: [
          { label: { ar: "ضغط الدم", en: "Blood Pressure" }, href: "/health/chronic-conditions/blood-pressure" },
          { label: { ar: "السكري", en: "Diabetes" }, href: "/health/chronic-conditions/diabetes" },
        ],
      },
    ],
  },

  // --------------------------------------------------------- BLOOD PRESSURE
  "chronic-conditions/blood-pressure": {
    slug: "/chronic-conditions/blood-pressure",
    seoTitle: { ar: "متابعة ضغط الدم | سيلترا هيلث", en: "Blood Pressure Tracking | SYLTRA HEALTH" },
    seoDescription: {
      ar: "اجمع قراءات ضغط الدم من الأجهزة المتوافقة مع النشاط والنوم في سجل منظم يدعم المتابعة مع فريق الرعاية.",
      en: "Bring blood-pressure readings from compatible devices together with activity and sleep in an organized view that supports follow-up with your care team.",
    },
    blocks: [
      {
        kind: "hero",
        eyebrow: { ar: "الحالات المزمنة · ضغط الدم", en: "Chronic Conditions · Blood Pressure" },
        headline: { ar: "ضغطك. بصورة يومية أوضح.", en: "Your blood pressure. A clearer daily picture." },
        body: {
          ar: "اجمع قراءات ضغط الدم من الأجهزة المتوافقة مع بيانات النشاط والنوم في سجل منظم يدعم المتابعة مع فريق الرعاية.",
          en: "Bring blood-pressure readings from compatible devices together with activity and sleep data in an organized view that supports follow-up with your care team.",
        },
        buttons: [{ label: { ar: "سجّل اهتمامك بمتابعة ضغط الدم", en: "Register Interest in Blood-Pressure Tracking" }, href: "/health/contact", primary: true }],
      },
      {
        kind: "list",
        headline: { ar: "ماذا تستطيع.", en: "What you can do." },
        items: [
          { ar: "إضافة القراءات يدوياً أو عبر الأجهزة المتوافقة.", en: "Add readings manually or through compatible devices." },
          { ar: "عرض القراءات على خط زمني واضح.", en: "View readings on a clear timeline." },
          { ar: "مقارنة القراءات بسياق النشاط والنوم.", en: "See readings alongside activity and sleep context." },
          { ar: "إنشاء ملخص لفترة يحددها المستخدم.", en: "Create a summary for a user-selected period." },
          { ar: "مشاركة الملخص مع فريق الرعاية بموافقة المستخدم.", en: "Share the summary with a care team with user consent." },
        ],
      },
      {
        kind: "safety",
        text: {
          ar: "لا تغيّر دواءك أو جرعتك بناءً على التطبيق. اتبع تعليمات مقدم الرعاية، واطلب المساعدة الطبية عند ظهور أعراض مقلقة أو قراءات غير معتادة.",
          en: "Do not change medication or dosage based on the app. Follow your care provider's instructions and seek medical help for concerning symptoms or unusual readings.",
        },
      },
    ],
  },

  // --------------------------------------------------------------- DIABETES
  "chronic-conditions/diabetes": {
    slug: "/chronic-conditions/diabetes",
    seoTitle: { ar: "متابعة السكري | سيلترا هيلث", en: "Diabetes Tracking | SYLTRA HEALTH" },
    seoDescription: {
      ar: "اجمع قراءات السكر من الأجهزة المتوافقة مع النشاط والنوم والسياق اليومي في رؤية منظمة تدعم المتابعة.",
      en: "Bring glucose readings from compatible devices together with activity, sleep and daily context in an organized view that supports follow-up.",
    },
    blocks: [
      {
        kind: "hero",
        eyebrow: { ar: "الحالات المزمنة · السكري", en: "Chronic Conditions · Diabetes" },
        headline: { ar: "قراءات السكر. بصورة يومية أوضح.", en: "Glucose readings. A clearer daily picture." },
        body: {
          ar: "اجمع قراءات السكر من الأجهزة المتوافقة مع النشاط والنوم والسياق اليومي في رؤية منظمة تدعم المتابعة مع فريق الرعاية.",
          en: "Bring glucose readings from compatible devices together with activity, sleep and daily context in an organized view that supports follow-up with your care team.",
        },
        buttons: [{ label: { ar: "سجّل اهتمامك بمتابعة السكري", en: "Register Interest in Diabetes Tracking" }, href: "/health/contact", primary: true }],
      },
      {
        kind: "section",
        eyebrow: { ar: "سيناريو", en: "Scenario" },
        headline: { ar: "عند انخفاض القراءة وأنت وحدك.", en: "When a reading drops and you are alone." },
        body: {
          ar: "يسجّل جهاز السكر المتصل قراءة منخفضة، وفي الوقت نفسه تلاحظ حساسات المنزل توقفًا غير معتاد عن الحركة. تقارن سيلترا هيلث هذه الإشارات بنمطك السابق وتتحقق من وجودك، ثم ترسل تنبيهًا على الساعة والهاتف وشاشة المنزل: رصدنا تغيّرًا غير معتاد، هل أنت بخير؟ مع خيارات واضحة. وإذا لم تستجب خلال المدة المحددة، تصل إلى الشخص الموثوق الأنسب بأقل قدر ضروري من المعلومات والموقع. لا يصف النظام الحالة تشخيصًا مؤكدًا، بل يستخدم صياغة دقيقة مثل: رصدنا قراءة منخفضة مع توقف غير معتاد عن الحركة وعدم استجابة.",
          en: "A connected glucose device logs a low reading while home sensors notice unusual stillness. SYLTRA HEALTH compares these signals to your baseline, confirms your presence, then sends a check-in to your watch, phone and home screen: we noticed an unusual change, are you okay? With clear options. If you do not respond within the set time, it reaches the most suitable trusted person with the minimum necessary information and location. The system never calls it a confirmed diagnosis. It uses precise wording such as: a low reading with unusual stillness and no response.",
        },
      },
      {
        kind: "list",
        headline: { ar: "ماذا تستطيع.", en: "What you can do." },
        items: [
          { ar: "ربط الأجهزة المتوافقة أو إضافة القراءات يدوياً.", en: "Connect compatible devices or add readings manually." },
          { ar: "عرض القراءات والاتجاهات عبر الوقت.", en: "View readings and trends over time." },
          { ar: "مشاهدة النشاط والنوم بجانب القراءات.", en: "See activity and sleep alongside readings." },
          { ar: "إنشاء تقارير للفترة التي يختارها المستخدم.", en: "Create reports for a user-selected period." },
          { ar: "مشاركة المعلومات مع فريق الرعاية بموافقة واضحة.", en: "Share information with a care team through clear consent." },
        ],
      },
      {
        kind: "safety",
        text: {
          ar: "سيلترا هيلث لا يحسب جرعات الأنسولين ولا يغيّر خطة العلاج. اتبع تعليمات فريق الرعاية واطلب المساعدة عند وجود أعراض أو قراءات مقلقة.",
          en: "SYLTRA HEALTH does not calculate insulin doses or change treatment plans. Follow your care team's instructions and seek help for concerning symptoms or readings.",
        },
      },
    ],
  },

  // ---------------------------------------------------------- SLEEP RECOVERY
  "sleep-recovery": {
    slug: "/sleep-recovery",
    seoTitle: { ar: "النوم والتعافي | سيلترا هيلث", en: "Sleep & Recovery | SYLTRA HEALTH" },
    seoDescription: {
      ar: "اربط بيانات النوم من الأجهزة المتوافقة بظروف الغرفة وروتينك اليومي لرؤية العوامل المحيطة براحتك.",
      en: "Connect sleep data from compatible devices with room conditions and daily routines for a fuller view of the context around your rest.",
    },
    blocks: [
      {
        kind: "hero",
        graphic: "scene",
        image: "/brand/health-hero-sleep.jpg",
        eyebrow: { ar: "النوم والتعافي", en: "Sleep & Recovery" },
        headline: { ar: "نوم أهدأ. يوم أوضح.", en: "Better sleep. Clearer days." },
        body: {
          ar: "اربط بيانات النوم من الأجهزة المتوافقة بظروف الغرفة وروتينك اليومي لرؤية العوامل المحيطة براحتك بصورة أكثر اكتمالاً.",
          en: "Connect sleep data from compatible devices with room conditions and daily routines for a more complete view of the context around your rest.",
        },
        buttons: [CTA_EARLY],
      },
      {
        kind: "list",
        headline: { ar: "ما الذي يجتمع معاً.", en: "What comes together." },
        items: [
          { ar: "مدة النوم وأوقاته من الأجهزة المتوافقة.", en: "Sleep duration and timing from compatible devices." },
          { ar: "مؤشرات النشاط والتعافي المتاحة.", en: "Available activity and recovery signals." },
          { ar: "حرارة الغرفة ورطوبتها وجودة الهواء.", en: "Room temperature, humidity and air quality." },
          { ar: "الروتين الذي يضيفه المستخدم.", en: "Routines added by the user." },
          { ar: "اتجاهات عبر عدة أيام بدلاً من ليلة واحدة.", en: "Trends across multiple days instead of one night." },
        ],
      },
      {
        kind: "safety",
        text: {
          ar: "معلومات النوم المعروضة لدعم الرفاه والمتابعة العامة، ولا تمثل تشخيصاً لاضطرابات النوم.",
          en: "Sleep information is presented to support wellness and general follow-up. It does not diagnose sleep disorders.",
        },
      },
    ],
  },

  // ----------------------------------------------------------- HOME WELLNESS
  "home-wellness": {
    slug: "/home-wellness",
    seoTitle: { ar: "صحة المنزل | سيلترا هيلث", en: "Home Wellness | SYLTRA HEALTH" },
    seoDescription: {
      ar: "تربط سيلترا هيلث بيانات البيئة المنزلية بتجربة الصحة والرفاه لتظهر الصورة في سياقها.",
      en: "SYLTRA HEALTH brings home-environment data into the health and wellness experience so information appears in context.",
    },
    blocks: [
      {
        kind: "hero",
        graphic: "scene",
        image: "/brand/health-hero-home-wellness.jpg",
        eyebrow: { ar: "صحة المنزل", en: "Home Wellness" },
        headline: { ar: "بيتك جزء من صحتك.", en: "Your home is part of your health." },
        body: {
          ar: "جودة الهواء والحرارة والرطوبة تؤثر في الراحة اليومية. تربط سيلترا هيلث بيانات البيئة المنزلية بتجربة الصحة والرفاه لتظهر الصورة في سياقها.",
          en: "Air quality, temperature and humidity shape everyday comfort. SYLTRA HEALTH brings home-environment data into the health and wellness experience so information appears in context.",
        },
        buttons: [{ label: { ar: "اكتشف تكامل الصحة والمنزل", en: "Explore Connected Home Wellness" }, href: "/health/integrations", primary: true }],
      },
      {
        kind: "section",
        headline: { ar: "التكامل مع سيلترا لايف.", en: "Integration with SYLTRA LIVE." },
        body: {
          ar: "عند الربط مع أجهزة سيلترا لايف المتوافقة، تظهر بيانات المنزل داخل تجربة سيلترا هيلث. ويمكن تنفيذ إعدادات منزلية يوافق عليها المستخدم، مثل ضبط التكييف أو التهوية، بعد اعتماد الأجهزة والوظائف المتاحة.",
          en: "When connected to compatible SYLTRA LIVE devices, home data appears inside the SYLTRA HEALTH experience. User-approved home settings, such as air-conditioning or ventilation adjustments, can be enabled once supported devices and functions are verified.",
        },
      },
    ],
  },

  // ---------------------------------------------------------- CARE PROVIDERS
  "care-providers": {
    slug: "/care-providers",
    seoTitle: { ar: "لمقدمي الرعاية | سيلترا هيلث", en: "For Care Providers | SYLTRA HEALTH" },
    seoDescription: {
      ar: "ملخصات منظمة يختار المستخدم مشاركتها، لتدعم المتابعة والحوار المبني على سياق أوسع بين الزيارات.",
      en: "Organized summaries that users choose to share, supporting follow-up and conversations informed by broader daily context between visits.",
    },
    blocks: [
      {
        kind: "hero",
        graphic: "scene",
        image: "/brand/health-hero-care-providers.jpg",
        eyebrow: { ar: "لمقدمي الرعاية", en: "For Care Providers" },
        headline: { ar: "صورة يومية أوضح بين الزيارات.", en: "A clearer daily picture between visits." },
        body: {
          ar: "تساعد سيلترا هيلث مقدمي الرعاية على استقبال ملخصات منظمة يختار المستخدم مشاركتها، لتدعم المتابعة والحوار المبني على سياق أوسع.",
          en: "SYLTRA HEALTH helps care providers receive organized summaries that users choose to share, supporting follow-up and conversations informed by broader daily context.",
        },
        buttons: [{ label: { ar: "ناقش برنامجاً تجريبياً", en: "Discuss a Pilot Program" }, href: "/health/contact", primary: true }],
      },
      {
        kind: "list",
        headline: { ar: "القدرات.", en: "Capabilities." },
        items: [
          { ar: "ملخصات لفترات يحددها المستخدم.", en: "Summaries for user-selected periods." },
          { ar: "عرض القراءات بجانب النشاط والنوم والسياق المنزلي.", en: "Readings displayed alongside activity, sleep and home context." },
          { ar: "صلاحيات وصول مبنية على الأدوار.", en: "Role-based access." },
          { ar: "سجل للموافقة والمشاركة.", en: "Consent and sharing records." },
          { ar: "تكاملات مؤسسية عبر واجهات آمنة بعد اعتمادها.", en: "Institutional integrations through verified secure interfaces." },
          { ar: "برامج تجريبية قابلة للتخصيص للعيادات ومقدمي الرعاية.", en: "Configurable pilot programs for clinics and care providers." },
        ],
      },
    ],
  },

  // ------------------------------------------------------------ INTEGRATIONS
  integrations: {
    slug: "/integrations",
    seoTitle: { ar: "التكاملات | سيلترا هيلث", en: "Integrations | SYLTRA HEALTH" },
    seoDescription: {
      ar: "مصممة للتكامل مع أبرز منظومات الصحة والأجهزة القابلة للارتداء، مع إظهار مصدر كل معلومة وتحكم المستخدم في الصلاحيات.",
      en: "Designed to connect with leading health and wearable ecosystems, showing where each data point came from and giving users control over permissions.",
    },
    blocks: [
      {
        kind: "hero",
        graphic: "scene",
        image: "/brand/health-hero-integrations.jpg",
        eyebrow: { ar: "التكاملات", en: "Integrations" },
        headline: { ar: "منظومة صحية واحدة. متصلة.", en: "One health ecosystem. Connected." },
        body: {
          ar: "تُبنى سيلترا هيلث كطبقة تربط مصادر متعددة، مع إظهار مصدر كل معلومة ومنح المستخدم التحكم في الصلاحيات.",
          en: "SYLTRA HEALTH is built as a layer that connects multiple sources while showing where information came from and giving users control over permissions.",
        },
        buttons: [{ label: { ar: "استعرض التكاملات", en: "View integrations" }, href: "#ecosystems", primary: true }],
      },
      { kind: "integrations" },
      {
        kind: "list",
        headline: { ar: "فئات التكامل.", en: "Integration categories." },
        items: [
          { ar: "Apple Health عبر HealthKit.", en: "Apple Health through HealthKit." },
          { ar: "Google Health Connect على Android.", en: "Google Health Connect on Android." },
          { ar: "Samsung Health عبر Samsung Health Data SDK.", en: "Samsung Health through the Samsung Health Data SDK." },
          { ar: "WHOOP عبر WHOOP Developer Platform.", en: "WHOOP through the WHOOP Developer Platform." },
          { ar: "الساعات والأساور الرياضية المتوافقة.", en: "Compatible watches and fitness bands." },
          { ar: "أجهزة قياس الضغط والسكر والأجهزة المنزلية المتوافقة.", en: "Compatible blood-pressure, glucose and home health devices." },
          { ar: "حساسات جودة الهواء والحرارة والرطوبة.", en: "Air-quality, temperature and humidity sensors." },
          { ar: "أجهزة ومنصات سيلترا لايف المتوافقة.", en: "Compatible SYLTRA LIVE devices and platforms." },
          { ar: "أنظمة مقدمي الرعاية عبر واجهات تكامل معتمدة.", en: "Care-provider systems through approved integration interfaces." },
        ],
      },
      {
        kind: "section",
        headline: { ar: "التوفر.", en: "Availability." },
        body: {
          ar: "تختلف الوظائف حسب الجهاز والمنطقة ومرحلة الإطلاق. تعرض صفحة كل تكامل حالة الدعم قبل الربط.",
          en: "Functions vary by device, region and launch stage. Each integration page shows support status before connection.",
        },
      },
    ],
  },

  // ---------------------------------------------------------------- PRIVACY
  privacy: {
    slug: "/privacy",
    seoTitle: { ar: "الخصوصية وأمن البيانات | سيلترا هيلث", en: "Privacy & Data Security | SYLTRA HEALTH" },
    seoDescription: {
      ar: "تبدأ سيلترا هيلث بالموافقة الواضحة، جمع الحد الأدنى، وإظهار ما يُجمع ولماذا ومع من يُشارك.",
      en: "SYLTRA HEALTH starts with clear consent, minimum necessary collection and transparency about what is collected, why and who it is shared with.",
    },
    blocks: [
      {
        kind: "hero",
        graphic: "scene",
        image: "/brand/health-hero-privacy.jpg",
        eyebrow: { ar: "الخصوصية وأمن البيانات", en: "Privacy & Data Security" },
        headline: { ar: "بياناتك. قرارك.", en: "Your data. Your decision." },
        body: {
          ar: "الصحة من أكثر البيانات خصوصية. لذلك تبدأ سيلترا هيلث بالموافقة الواضحة، جمع الحد الأدنى، وإظهار ما يُجمع ولماذا ومع من يُشارك.",
          en: "Health information is deeply personal. SYLTRA HEALTH starts with clear consent, minimum necessary collection and transparency about what is collected, why and who it is shared with.",
        },
      },
      {
        kind: "cards",
        headline: { ar: "مبادئنا.", en: "Our principles." },
        items: [
          { title: { ar: "الموافقة", en: "Consent" }, body: { ar: "لا يتم ربط مصدر أو مشاركة بيانات دون اختيار واضح.", en: "No source is connected and no information is shared without a clear choice." } },
          { title: { ar: "الحد الأدنى", en: "Minimum necessary" }, body: { ar: "نجمع البيانات اللازمة للغرض المحدد فقط.", en: "Only information needed for the stated purpose is collected." } },
          { title: { ar: "التحكم", en: "Control" }, body: { ar: "يستطيع المستخدم مراجعة الصلاحيات وإيقاف المشاركة.", en: "Users can review permissions and stop sharing." } },
          { title: { ar: "الشفافية", en: "Transparency" }, body: { ar: "نوضح مصدر البيانات والغرض من استخدامها.", en: "The source and purpose of data use are explained." } },
          { title: { ar: "المساءلة", en: "Accountability" }, body: { ar: "تُسجل إجراءات الوصول والمشاركة وفق التصميم المعتمد.", en: "Access and sharing actions are logged within the approved design." } },
          { title: { ar: "الاحتفاظ", en: "Retention" }, body: { ar: "لا يُحتفظ بالبيانات أكثر من المدة اللازمة للغرض المعلن.", en: "Data is not kept longer than necessary for the stated purpose." } },
        ],
      },
      {
        kind: "safety",
        text: {
          ar: "الموقع التعريفي لا يطلب تقارير طبية أو قراءات صحية. لا تكتب معلومات صحية داخل نموذج التواصل أو التسجيل المبكر.",
          en: "The informational website does not request medical reports or health readings. Do not enter health information in contact or early-access forms.",
        },
      },
      {
        kind: "links",
        headline: { ar: "روابط", en: "Links" },
        items: [
          { label: { ar: "سياسة الخصوصية", en: "Privacy Policy" }, href: "/health/privacy" },
          { label: { ar: "شروط الاستخدام", en: "Terms of Use" }, href: "/health/privacy" },
          { label: { ar: "إدارة الموافقات", en: "Manage Consent" }, href: "/health/contact" },
          { label: { ar: "طلب الوصول أو التصحيح أو الحذف", en: "Request Access, Correction or Deletion" }, href: "/health/contact" },
          { label: { ar: "الإبلاغ عن مشكلة خصوصية", en: "Report a Privacy Concern" }, href: "/health/contact" },
        ],
      },
    ],
  },

  // ------------------------------------------------------------------ ABOUT
  about: {
    slug: "/about",
    seoTitle: { ar: "عن سيلترا هيلث", en: "About SYLTRA HEALTH" },
    seoDescription: {
      ar: "شركة تقنيات صحية ضمن سيلترا وان، تربط بيانات المستخدم بالأجهزة القابلة للارتداء والقراءات المنزلية وحساسات البيئة.",
      en: "A health technology company within SYLTRA ONE, connecting personal data with wearables, home health readings and environmental sensors.",
    },
    blocks: [
      {
        kind: "hero",
        graphic: "scene",
        image: "/brand/health-hero-about.jpg",
        eyebrow: { ar: "عن سيلترا هيلث", en: "About" },
        headline: { ar: "التقنية الصحية التي تربط الإنسان ببيئته.", en: "Health technology connecting people with their environment." },
        body: {
          ar: "سيلترا هيلث هي شركة تقنيات صحية ضمن سيلترا وان. نبني تجربة تربط بيانات المستخدم الشخصية بالأجهزة القابلة للارتداء والقراءات الصحية المنزلية وحساسات البيئة، حتى تصبح المعلومات اليومية أكثر وضوحاً وفائدة.",
          en: "SYLTRA HEALTH is a health technology company within SYLTRA ONE. We build an experience that connects personal data with wearables, home health readings and environmental sensors so everyday information becomes clearer and more useful.",
        },
      },
      {
        kind: "section",
        body: {
          ar: "نعمل عند نقطة التقاء الصحة الرقمية، الذكاء الاصطناعي، إنترنت الأشياء والبيوت الذكية. هدفنا ليس إضافة تطبيق جديد إلى هاتف المستخدم، بل تقليل التشتت وبناء صورة مترابطة يحكم المستخدم الوصول إليها.",
          en: "We work at the intersection of digital health, artificial intelligence, the Internet of Things and smart living. Our goal is not to add another disconnected app to a user's phone. It is to reduce fragmentation and build one connected picture controlled by the user.",
        },
      },
      {
        kind: "cta",
        headline: { ar: "ابنِ معنا تجربة صحية أكثر اتصالاً.", en: "Help build a more connected health experience." },
        buttons: [CTA_EARLY, CTA_PILOT],
      },
    ],
  },
};

export const HEALTH_PAGE_ORDER = [
  "",
  "how-it-works",
  "individuals",
  "older-adults",
  "chronic-conditions",
  "chronic-conditions/blood-pressure",
  "chronic-conditions/diabetes",
  "sleep-recovery",
  "home-wellness",
  "care-providers",
  "integrations",
  "privacy",
  "about",
];
