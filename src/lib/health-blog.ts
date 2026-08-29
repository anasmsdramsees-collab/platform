import type { L } from "@/lib/health-content";

export type HealthPost = {
  slug: string;
  date: string; // ISO date
  category: L;
  title: L;
  excerpt: L;
  image?: string;
  body: { ar: string[]; en: string[] };
};

/** Original SYLTRA HEALTH articles (no em-dashes, AR/EN). */
export const HEALTH_POSTS: HealthPost[] = [
  {
    slug: "your-home-is-the-missing-piece-in-everyday-health",
    date: "2026-08-20",
    category: { ar: "الصحة المتصلة", en: "Connected Health" },
    image: "/brand/health-hero-home-wellness.jpg",
    title: {
      ar: "بيتك هو الجزء الناقص في صحتك اليومية",
      en: "Your home is the missing piece in everyday health",
    },
    excerpt: {
      ar: "معظم تطبيقات الصحة تقرأ جسدك فقط. لكن الهواء والحرارة والرطوبة والحركة من حولك تشكّل جزءًا كبيرًا من راحتك اليومية.",
      en: "Most health apps read only your body. Yet the air, temperature, humidity and movement around you shape much of how you feel each day.",
    },
    body: {
      ar: [
        "حين نفكّر في الصحة، نفكّر عادةً في الخطوات ونبض القلب وساعات النوم. هذه مؤشرات مهمة، لكنها لا تحكي القصة كاملة. أنت لا تعيش داخل ساعتك الذكية، بل داخل بيتك، وبيئة هذا البيت تؤثر في نومك وتركيزك وطاقتك أكثر مما نظن.",
        "جودة الهواء الرديئة قد تفسّر صداعًا متكررًا أو نومًا متقطعًا. الحرارة المرتفعة ليلًا قد تخفض جودة نومك دون أن تدري. والرطوبة غير المتوازنة تؤثر في راحة التنفس. هذه عوامل بيئية لا يلتقطها أي سوار في معصمك.",
        "فكرة سيلترا هيلث أن تجمع الإشارتين معًا: بيانات جسدك من الأجهزة القابلة للارتداء، وبيانات محيطك من حسّاسات المنزل الذكي. عند وضع الاثنتين جنبًا إلى جنب، تبدأ الأنماط بالظهور. مثلًا: تحسّن نومك في الليالي التي كانت فيها جودة الهواء جيدة والحرارة معتدلة.",
        "الهدف ليس إغراقك بالأرقام، بل منحك سياقًا. حين تفهم أن بيئتك جزء من صحتك، تصبح القرارات الصغيرة أوضح: متى تهوّي الغرفة، ومتى تضبط التكييف، ومتى تراجع روتينك المسائي.",
      ],
      en: [
        "When we think about health, we usually think of steps, heart rate and hours of sleep. These matter, but they do not tell the whole story. You do not live inside your smartwatch. You live inside your home, and that environment shapes your sleep, focus and energy more than we tend to assume.",
        "Poor air quality can explain a recurring headache or broken sleep. A room that runs warm at night can quietly lower your sleep quality. Unbalanced humidity affects how easily you breathe. None of these environmental factors are captured by a band on your wrist.",
        "The idea behind SYLTRA HEALTH is to bring both signals together: your body data from wearables, and your surroundings from smart-home sensors. Placed side by side, patterns start to appear. For example, your sleep improves on the nights when air quality was good and the room stayed cool.",
        "The goal is not to drown you in numbers. It is to give you context. Once you understand that your environment is part of your health, small decisions become clearer: when to ventilate a room, when to adjust the air-conditioning, and when to revisit your evening routine.",
      ],
    },
  },
  {
    slug: "air-quality-and-how-it-affects-your-sleep",
    date: "2026-08-18",
    category: { ar: "النوم والبيئة", en: "Sleep & Environment" },
    image: "/brand/health-hero-sleep.jpg",
    title: {
      ar: "جودة الهواء وأثرها على نومك",
      en: "Air quality and how it affects your sleep",
    },
    excerpt: {
      ar: "الليلة السيئة من النوم قد لا تكون بسبب التوتر فقط. أحيانًا يكون السبب في الهواء الذي تتنفسه وأنت نائم.",
      en: "A bad night of sleep is not always about stress. Sometimes it is about the air you breathe while you rest.",
    },
    body: {
      ar: [
        "نقضي نحو ثلث حياتنا نائمين، وغالبًا في غرفة مغلقة لساعات. خلال هذه الساعات، ترتفع نسبة ثاني أكسيد الكربون وتتغيّر الرطوبة، وقد تتراكم ملوّثات دقيقة في الهواء. كل ذلك يحدث بينما أنت غير واعٍ له تمامًا.",
        "الأبحاث العامة حول جودة الهواء الداخلي تشير إلى أن التهوية الجيدة ترتبط بنوم أعمق وشعور أفضل عند الاستيقاظ. المشكلة أن أغلبنا لا يملك طريقة لرؤية هذه العوامل، فنعزو النوم السيئ إلى التوتر أو الكافيين فقط.",
        "حين تربط حسّاسات جودة الهواء والحرارة والرطوبة بتجربة نومك، تصبح الصورة أوضح. يمكنك أن ترى، عبر عدة ليالٍ، متى كان الهواء جيدًا وكيف انعكس ذلك على تعافيك.",
        "الخطوة العملية بسيطة: راقب الاتجاه عبر الأيام لا الليلة الواحدة. الأنماط المتكررة هي التي تستحق التصرف، مثل تحسين التهوية قبل النوم أو ضبط درجة حرارة الغرفة.",
      ],
      en: [
        "We spend about a third of our lives asleep, usually in a closed room for hours at a time. During those hours, carbon dioxide rises, humidity shifts, and fine particles can build up in the air. All of this happens while you are completely unaware of it.",
        "General research on indoor air quality links good ventilation to deeper sleep and feeling better on waking. The problem is that most of us have no way to see these factors, so we blame poor sleep on stress or caffeine alone.",
        "When you connect air-quality, temperature and humidity sensors to your sleep experience, the picture gets clearer. Across several nights, you can see when the air was good and how that reflected on your recovery.",
        "The practical step is simple: watch the trend across days, not a single night. Recurring patterns are the ones worth acting on, such as improving ventilation before bed or adjusting the room temperature.",
      ],
    },
  },
  {
    slug: "what-connected-health-data-can-and-cannot-tell-you",
    date: "2026-08-15",
    category: { ar: "فهم البيانات", en: "Understanding Data" },
    image: "/brand/health-hero-individuals.jpg",
    title: {
      ar: "ما الذي تخبرك به بيانات الصحة المتصلة، وما الذي لا تخبرك به",
      en: "What connected health data can and cannot tell you",
    },
    excerpt: {
      ar: "جمع البيانات خطوة أولى، لكن فهم حدودها لا يقل أهمية. البيانات تدعم القرار ولا تحلّ محل الطبيب.",
      en: "Gathering data is a first step, but understanding its limits matters just as much. Data supports decisions, it does not replace a clinician.",
    },
    body: {
      ar: [
        "من السهل أن نثق بالأرقام لمجرد أنها دقيقة الشكل. لكن قراءة واحدة من أي جهاز هي لحظة واحدة في يوم كامل. القيمة الحقيقية تأتي من الاتجاه عبر الوقت، لا من الرقم المنفرد.",
        "الأجهزة القابلة للارتداء والقراءات المنزلية تعطيك مؤشرات مفيدة عن النشاط والنوم والقراءات اليومية. لكنها لا تشخّص مرضًا، ولا تحدّد جرعة دواء، ولا تستبدل تقييم المختص. هذا فارق جوهري يجب أن يبقى واضحًا.",
        "دور المنصة الجيدة أن تنظّم هذه الإشارات وتعرض مصدر كل معلومة، حتى تعرف من أين جاء كل رقم. الشفافية هنا ليست تفصيلًا تقنيًا، بل شرط للثقة.",
        "استخدم بياناتك لتطرح أسئلة أفضل على فريق الرعاية، لا لتصل إلى نتائج بنفسك. الصورة المتصلة تساعد على حوار أوضح ومتابعة أدق بين الزيارات.",
      ],
      en: [
        "It is easy to trust numbers simply because they look precise. But a single reading from any device is one moment in a whole day. The real value comes from the trend over time, not the isolated number.",
        "Wearables and home readings give useful signals about activity, sleep and daily measurements. They do not diagnose a condition, set a medication dose, or replace a professional assessment. That distinction has to stay clear.",
        "The role of a good platform is to organize these signals and show where each data point came from, so you know the source of every number. Transparency here is not a technical detail. It is a condition for trust.",
        "Use your data to ask better questions of your care team, not to reach conclusions on your own. A connected picture supports clearer conversations and closer follow-up between visits.",
      ],
    },
  },
  {
    slug: "motion-sensors-and-older-adults-support-without-surveillance",
    date: "2026-08-12",
    category: { ar: "كبار السن", en: "Older Adults" },
    image: "/brand/health-hero-older.jpg",
    title: {
      ar: "حسّاسات الحركة وكبار السن: دعم يحترم الخصوصية",
      en: "Motion sensors and older adults: support without surveillance",
    },
    excerpt: {
      ar: "الهدف ليس مراقبة المنزل، بل احترام الاستقلالية مع طمأنينة الأسرة، وبموافقة واضحة من صاحب البيانات.",
      en: "The goal is not to watch the home. It is to respect independence while reassuring family, with clear consent from the person the data belongs to.",
    },
    body: {
      ar: [
        "كثير من كبار السن يقدّرون استقلاليتهم أكثر من أي شيء. أي حل تقني يبدأ من هنا: كيف ندعم دون أن نتطفّل. حسّاسات الحركة يمكن أن تلاحظ أنماط النشاط والخمول غير المعتادة، فتساعد الأسرة على الاطمئنان دون تحويل البيت إلى مساحة مراقبة.",
        "المبدأ الأساسي هو التحكم. صاحب البيانات هو من يقرر من يرى المعلومات، وما الذي يراه، ولمدة كم. لا مشاركة تبدأ دون اختيار واضح، ويمكن إيقافها في أي لحظة.",
        "من المهم أن نكون صريحين بشأن الحدود. هذه الأدوات تدعم الوعي والمتابعة العامة، لكنها ليست خدمة طوارئ ولا تضمن الاستجابة. عند وجود حالة طارئة، يبقى الاتصال بخدمات الطوارئ أو مقدم الرعاية هو الإجراء الصحيح.",
        "حين تُصمَّم التقنية حول كرامة الإنسان أولًا، تتحول من عين تراقب إلى دعم هادئ في الخلفية.",
      ],
      en: [
        "Many older adults value their independence above almost anything. Any technology has to start there: how do we support without intruding. Motion sensors can notice unusual patterns of activity or inactivity, helping family feel reassured without turning the home into a surveillance space.",
        "The core principle is control. The person the data belongs to decides who sees information, what they see, and for how long. No sharing begins without a clear choice, and it can be stopped at any moment.",
        "It is important to be honest about limits. These tools support awareness and general follow-up, but they are not an emergency service and do not guarantee response. In an emergency, contacting emergency services or a care provider remains the right action.",
        "When technology is designed around human dignity first, it shifts from a watching eye into quiet support in the background.",
      ],
    },
  },
  {
    slug: "reading-blood-pressure-trends-not-single-readings",
    date: "2026-08-08",
    category: { ar: "الحالات المزمنة", en: "Chronic Conditions" },
    image: "/brand/health-hero-chronic.jpg",
    title: {
      ar: "اقرأ اتجاه ضغط الدم، لا القراءة الواحدة",
      en: "Read your blood pressure trends, not single readings",
    },
    excerpt: {
      ar: "قراءة مرتفعة في لحظة توتر لا تعني الكثير بمفردها. السياق عبر الأيام هو ما يبني صورة أوضح.",
      en: "A high reading in a stressful moment does not mean much on its own. Context across days is what builds a clearer picture.",
    },
    body: {
      ar: [
        "ضغط الدم يتغيّر خلال اليوم بشكل طبيعي. يرتفع مع المجهود والتوتر والقهوة، وينخفض مع الراحة. لذلك فإن قراءة واحدة قد تربكك أكثر مما تفيدك إن نظرت إليها معزولة.",
        "الأفيد أن تسجّل قراءاتك بانتظام وتراها على خط زمني، بجانب سياقك من نشاط ونوم. هكذا تلاحظ إن كان هناك نمط ثابت يستحق الحديث عنه مع فريق الرعاية.",
        "تنظيم القراءات في تقرير واضح لفترة تختارها يجعل زيارة العيادة أكثر فائدة. بدل محاولة تذكّر أرقام متفرقة، تأتي بصورة مرتبة تدعم القرار.",
        "تذكير مهم: لا تغيّر دواءك أو جرعتك بناءً على التطبيق. اتبع تعليمات مقدم الرعاية، واطلب المساعدة عند ظهور أعراض مقلقة أو قراءات غير معتادة.",
      ],
      en: [
        "Blood pressure changes naturally throughout the day. It rises with effort, stress and coffee, and falls with rest. So a single reading can confuse you more than help if you look at it in isolation.",
        "It is more useful to log your readings regularly and see them on a timeline, alongside your context of activity and sleep. That way you notice whether there is a steady pattern worth discussing with your care team.",
        "Organizing readings into a clear report for a period you choose makes a clinic visit more useful. Instead of trying to recall scattered numbers, you arrive with an ordered picture that supports the decision.",
        "An important reminder: do not change your medication or dose based on the app. Follow your care provider's instructions, and seek help for concerning symptoms or unusual readings.",
      ],
    },
  },
  {
    slug: "building-a-privacy-first-health-routine",
    date: "2026-08-04",
    category: { ar: "الخصوصية", en: "Privacy" },
    image: "/brand/health-hero-privacy.jpg",
    title: {
      ar: "كيف تبني روتينًا صحيًا يبدأ من الخصوصية",
      en: "Building a privacy-first health routine",
    },
    excerpt: {
      ar: "بيانات الصحة من أكثر ما يخصّك. الخصوصية ليست إعدادًا في القائمة، بل أساس تُبنى عليه التجربة.",
      en: "Health data is among the most personal you have. Privacy is not a setting buried in a menu. It is a foundation the whole experience is built on.",
    },
    body: {
      ar: [
        "قبل أن تربط أي جهاز، اسأل نفسك سؤالين: ما الذي أشاركه، ومع من. التجربة الجيدة تجعل الإجابة على هذين السؤالين سهلة وواضحة في أي وقت.",
        "ابدأ بالحد الأدنى. لا تربط إلا المصادر التي تحتاجها فعلًا للغرض الذي تريده. كل ربط إضافي هو بيانات إضافية يجب أن يكون لها سبب.",
        "راجع الصلاحيات بين حين وآخر. من يستطيع رؤية بياناتك اليوم؟ هل ما زلت تريد ذلك؟ القدرة على إيقاف المشاركة بسهولة لا تقل أهمية عن القدرة على بدئها.",
        "أخيرًا، اطلب الشفافية. يجب أن تعرف مصدر كل معلومة والغرض من استخدامها. حين تُبنى التجربة على الموافقة الواضحة وتقليل البيانات، تصبح الثقة نتيجة طبيعية لا وعدًا فقط.",
      ],
      en: [
        "Before connecting any device, ask yourself two questions: what am I sharing, and with whom. A good experience makes answering these two questions easy and clear at any time.",
        "Start with the minimum. Only connect the sources you genuinely need for the purpose you have in mind. Every extra connection is extra data that should have a reason.",
        "Review permissions from time to time. Who can see your data today? Do you still want that? Being able to stop sharing easily matters as much as being able to start it.",
        "Finally, ask for transparency. You should know the source of every data point and the purpose of its use. When an experience is built on clear consent and data minimization, trust becomes a natural result, not just a promise.",
      ],
    },
  },
];

export function postsSorted(): HealthPost[] {
  return [...HEALTH_POSTS].sort((a, b) => (a.date < b.date ? 1 : -1));
}
