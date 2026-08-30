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
    slug: "growing-older-at-home-technology-that-respects-the-person",
    date: "2026-08-30",
    category: { ar: "كبار السن", en: "Older Adults" },
    image: "/brand/health-hero-older.jpg",
    title: {
      ar: "أن تكبر في بيتك: تقنية تحترم الإنسان قبل الرقم",
      en: "Growing older at home: technology that respects the person",
    },
    excerpt: {
      ar: "أغلب كبار السن يريدون شيئًا واحدًا بسيطًا: أن يبقوا في بيوتهم بكرامة. دور التقنية أن تسند هذه الرغبة، لا أن تصادرها.",
      en: "Most older adults want one simple thing: to stay in their own home with dignity. Technology should support that wish, not take it over.",
    },
    body: {
      ar: [
        "حين يكبر أحد والدينا، يتغيّر شكل القلق في البيت. مكالمة لا تُرد، صوت لم نسمعه منذ الصباح، درجة تأخذ وقتًا أطول من المعتاد. لا نريد أن نراقب، ونخاف في الوقت نفسه أن نغفل. هذه المسافة بين الاطمئنان والتطفّل هي ما يجب أن تفهمه التقنية أولًا.",
        "الفكرة ليست كاميرا في كل زاوية. الفكرة أن يتعلّم البيت نمط اليوم المعتاد: متى يستيقظ، متى يتحرك في المطبخ، متى يهدأ في المساء. حين يغيب نشاط اعتاد أن يحدث، يلاحظ النظام الفرق بهدوء، ويبدأ بالسؤال عن الشخص نفسه قبل أن يزعج أحدًا.",
        "الكرامة تعني أن يبقى صاحب البيت هو صاحب القرار. هو من يحدّد من يرى ماذا، ومتى يصل التنبيه، وما المعلومة التي تُشارك. الابن الذي يسكن بعيدًا قد يرى أن الأمور على ما يرام، دون أن يطّلع على تفاصيل يومه الصغيرة.",
        "ومن الأمانة أن نكون واضحين في الحدود. هذه أدوات تدعم الطمأنينة والمتابعة، وليست خدمة طوارئ ولا بديلًا عن رعاية. عند الحاجة الحقيقية يبقى الاتصال بالطوارئ أو مقدم الرعاية هو الخطوة الصحيحة. أفضل تقنية لكبار السن هي التي لا تُشعرهم بأنهم مراقَبون، بل بأنهم غير وحيدين.",
      ],
      en: [
        "When a parent grows older, worry changes shape at home. A call that goes unanswered, a voice we have not heard since morning, a step that takes longer than it used to. We do not want to watch over them, and at the same time we fear missing something. That distance between reassurance and intrusion is what technology has to understand first.",
        "The idea is not a camera in every corner. It is a home that learns the shape of an ordinary day: when someone wakes, when they move in the kitchen, when they settle in the evening. When an activity that usually happens is missing, the system notices the difference quietly and starts by checking in with the person themselves before disturbing anyone else.",
        "Dignity means the person stays the one who decides. They set who sees what, when an alert travels, and which information is shared. A son living far away can see that things are fine without being handed the small details of a day.",
        "And it is only honest to be clear about limits. These are tools that support reassurance and follow-up. They are not an emergency service and not a substitute for care. When help is genuinely needed, calling emergency services or a care provider remains the right step. The best technology for older adults is the kind that does not make them feel watched, but makes them feel less alone.",
      ],
    },
  },
  {
    slug: "when-movement-is-hard-a-home-that-meets-you-halfway",
    date: "2026-08-29",
    category: { ar: "أصحاب الهمم: الإعاقة الحركية", en: "People of Determination: Motor" },
    image: "/brand/health-hero-accessibility.jpg",
    title: {
      ar: "حين تكون الحركة صعبة: بيت يقطع نصف الطريق إليك",
      en: "When movement is hard: a home that meets you halfway",
    },
    excerpt: {
      ar: "بالنسبة لمن تكون الحركة عنده جهدًا محسوبًا، كل خطوة غير ضرورية مكسب. البيت الذكي هنا ليس رفاهية، بل استقلالية.",
      en: "For someone whose movement is measured effort, every unnecessary step saved is a gain. A smart home here is not luxury, it is independence.",
    },
    body: {
      ar: [
        "من يعيش مع إعاقة حركية يعرف أن اليوم سلسلة من الحسابات الصغيرة: هل أقوم الآن أم أجمع مهامي معًا، هل الطريق إلى المفتاح يستحق العناء، كم تبقّى لي من طاقة. حين يفهم البيت هذه المعادلة، يتغيّر معنى المكان نفسه.",
        "أشياء بسيطة تصنع فرقًا كبيرًا: إضاءة وحرارة وستائر وأبواب يتحكم بها الصوت أو لمسة واحدة، دون الحاجة للوصول الجسدي إلى كل جهاز. الهدف أن يبقى المجهود لما تختاره أنت، لا لما يفرضه ترتيب الغرفة.",
        "الجانب الصحي لا يقل أهمية. الجلوس الطويل أو نمط حركة ثابت قد يحتاج إلى تذكير لطيف بتغيير الوضعية، أو إلى بيئة تُضبط مسبقًا لتقليل الإجهاد. هذه تفاصيل يوافق عليها المستخدم مسبقًا، وتعمل في الخلفية لصالحه.",
        "وحين تأتي لحظة يحتاج فيها إلى مساعدة، لا ينبغي أن تكون الاستجابة مرهقة. طلب واحد واضح، ووصول إلى الشخص الأنسب من دائرته الموثوقة، بأقل قدر ضروري من المعلومات. التقنية الجيدة هنا لا تلفت الانتباه إلى الإعاقة، بل تزيح العقبات بهدوء وتترك القرار كاملًا لصاحبه.",
      ],
      en: [
        "Anyone living with a motor disability knows the day is a string of small calculations: do I get up now or gather my tasks together, is the trip to the switch worth the effort, how much energy is left. When a home understands this arithmetic, the meaning of the space itself changes.",
        "Simple things make a large difference: light, temperature, curtains and doors controlled by voice or a single touch, without needing to physically reach every device. The aim is to keep effort for what you choose, not for what the layout of a room imposes.",
        "The health side matters just as much. Long sitting or a fixed movement pattern may call for a gentle reminder to shift position, or an environment set in advance to reduce strain. These are details the user approves beforehand, working in the background in their favor.",
        "And when a moment of needing help arrives, the response should not be exhausting. One clear request, reaching the most suitable person in a trusted circle, with the minimum necessary information. Good technology here does not draw attention to the disability. It quietly removes obstacles and leaves the decision fully with the person.",
      ],
    },
  },
  {
    slug: "a-home-you-can-see-when-you-cannot-hear-it",
    date: "2026-08-28",
    category: { ar: "أصحاب الهمم: الإعاقة السمعية", en: "People of Determination: Hearing" },
    image: "/brand/health-hero-accessibility.jpg",
    title: {
      ar: "بيت تراه حين لا تستطيع سماعه",
      en: "A home you can see when you cannot hear it",
    },
    excerpt: {
      ar: "معظم التنبيهات في بيوتنا صوتية. لمن لا يسمع، الحل ليس رفع الصوت، بل تحويل المعلومة إلى شكل يُرى ويُحسّ.",
      en: "Most alerts in our homes are sound. For someone who does not hear, the answer is not a louder tone, it is turning information into something seen and felt.",
    },
    body: {
      ar: [
        "جرّس الباب، صفير الجهاز، إنذار الدخان، رنين الهاتف. البيت مليء بالأصوات التي نعتمد عليها دون أن ننتبه. من يعيش مع إعاقة سمعية يفقد هذه الطبقة كاملة، ومعها قدر من الأمان والاستقلال.",
        "الحل أن تُترجم كل إشارة صوتية إلى قناة أخرى: وميض ضوئي بلون متفق عليه، اهتزاز في الساعة أو الهاتف، إشعار واضح على الشاشة يقول ما الذي حدث وأين. المعلومة نفسها تصل، لكن بلغة يفهمها الجسد.",
        "الأهم أن تبقى هذه الترجمة متسقة ومفهومة. لون معيّن لجرس الباب، نمط اهتزاز مختلف للتنبيه المهم، بحيث يتعلّمها المستخدم بسهولة ويثق بها. الوضوح هنا شرط للطمأنينة.",
        "وفي لحظة الحاجة، لا يجب أن يعتمد طلب المساعدة على مكالمة صوتية. التواصل النصي والمرئي مع الدائرة الموثوقة، مع تأكيد بصري بأن الرسالة وصلت وأن أحدًا في الطريق، يمنح ثقة لا تقل عن أي صوت. البيت الذي يُرى بوضوح يمكن أن يكون آمنًا تمامًا كالبيت الذي يُسمع.",
      ],
      en: [
        "The doorbell, an appliance beep, a smoke alarm, a ringing phone. A home is full of sounds we rely on without noticing. Someone living with a hearing disability loses this entire layer, and with it a measure of safety and independence.",
        "The answer is to translate every sound into another channel: a light flash in an agreed color, a vibration in a watch or phone, a clear on-screen notice that says what happened and where. The same information arrives, but in a language the body understands.",
        "What matters most is that this translation stays consistent and legible. A specific color for the doorbell, a distinct vibration pattern for an important alert, so the user learns them easily and trusts them. Clarity here is a condition for reassurance.",
        "And in a moment of need, asking for help should not depend on a voice call. Text and visual contact with the trusted circle, with a visual confirmation that the message arrived and someone is on the way, gives confidence no less than any sound. A home that is clearly seen can be every bit as safe as a home that is heard.",
      ],
    },
  },
  {
    slug: "being-understood-without-speaking-a-word",
    date: "2026-08-27",
    category: { ar: "أصحاب الهمم: الإعاقة الصوتية والنطقية", en: "People of Determination: Speech" },
    image: "/brand/health-hero-accessibility.jpg",
    title: {
      ar: "أن تُفهَم دون أن تنطق كلمة",
      en: "Being understood without speaking a word",
    },
    excerpt: {
      ar: "كثير من الأنظمة اليوم تنتظر أمرًا صوتيًا. لمن لا يستطيع الكلام أو يجد فيه صعوبة، يجب أن يكون هناك طريق آخر بنفس الكرامة.",
      en: "Many systems today wait for a spoken command. For someone who cannot speak, or finds it hard, there must be another path with the same dignity.",
    },
    body: {
      ar: [
        "صار الصوت واجهة أساسية للتقنية: قل هذا، اطلب ذاك. لكن حين تكون القدرة على الكلام محدودة، تتحول هذه الراحة إلى حاجز. المشكلة ليست في المستخدم، بل في نظام لا يفترض إلا طريقة واحدة للتعبير.",
        "البيت الذي يحترم الجميع يقدّم أكثر من مدخل: لمسة، إيماءة، اختيار من شاشة، أزرار مخصصة لمهام متكررة، أو رسائل جاهزة يُكوّنها المستخدم مسبقًا ليعبّر بها بسرعة. الفكرة أن يكون لكل نية طريق واضح لا يمر بالصوت بالضرورة.",
        "في التواصل مع الآخرين، يصنع هذا فرقًا كبيرًا. القدرة على إرسال رسالة محددة بلمسة واحدة، أو تشغيل تسلسل متفق عليه، تعني أن يعبّر الإنسان عن حاجته دون أن يُرهق نفسه أو ينتظر من يترجم عنه.",
        "وفي لحظة الطوارئ خصوصًا، لا يصح أن تكون الاستجابة معلّقة على جملة منطوقة. طلب صامت وواضح، يصل إلى الدائرة الموثوقة بمعلومة كافية، قد يكون أسرع وأأمن. أن تُفهَم دون أن تتكلم ليس ترفًا، بل شكل من أشكال الاحترام.",
      ],
      en: [
        "Voice has become a primary interface for technology: say this, ask for that. But when the ability to speak is limited, this convenience turns into a barrier. The problem is not the user, it is a system that assumes only one way to express intent.",
        "A home that respects everyone offers more than one input: a touch, a gesture, a choice on a screen, buttons dedicated to frequent tasks, or ready phrases the user composes in advance to express something quickly. The idea is that every intention has a clear path that does not necessarily pass through the voice.",
        "In communicating with others, this makes a real difference. Being able to send a specific message with a single touch, or trigger an agreed sequence, means a person expresses a need without exhausting themselves or waiting for someone to translate.",
        "And in an emergency especially, response should never hang on a spoken sentence. A silent, clear request that reaches the trusted circle with enough information can be faster and safer. To be understood without speaking is not a luxury, it is a form of respect.",
      ],
    },
  },
  {
    slug: "a-home-that-speaks-when-the-eyes-cannot-read-it",
    date: "2026-08-26",
    category: { ar: "أصحاب الهمم: الإعاقة البصرية", en: "People of Determination: Vision" },
    image: "/brand/health-hero-accessibility.jpg",
    title: {
      ar: "بيت ينطق حين لا تقرؤه العين",
      en: "A home that speaks when the eyes cannot read it",
    },
    excerpt: {
      ar: "الواجهات المرئية تفترض أنك تنظر. لمن لا يرى، يجب أن تصل المعلومة نفسها عبر الصوت واللمس بترتيب واضح يمكن الاعتماد عليه.",
      en: "Visual interfaces assume you are looking. For someone who does not see, the same information must arrive through sound and touch, in a clear order you can rely on.",
    },
    body: {
      ar: [
        "معظم الأجهزة الذكية تتحدث بلغة الشاشة: أيقونات، ألوان، قوائم. من يعيش مع إعاقة بصرية لا يحتاج إلى شاشة أوضح، بل إلى طريق مختلف للمعلومة نفسها، طريق مسموع ومحسوس ومنظّم.",
        "هذا يعني تصميمًا يعمل بالكامل مع قارئ الشاشة، وأوامر صوتية موثوقة، وردودًا منطوقة تصف الحالة بدقة: الباب مغلق، الحرارة مضبوطة، جودة الهواء جيدة. الوصف الجيد ليس زخرفة، بل هو الواجهة كلها.",
        "الترتيب والثبات مهمان بقدر الصوت. حين يكون لكل شيء مكان متوقع وتسمية واضحة لا تتغيّر، يبني المستخدم خريطة ذهنية للبيت يثق بها. المفاجآت في التصميم عبء إضافي على من يعتمد على الذاكرة والسمع.",
        "وفي الحالات المهمة، يجب أن يُعلَن التنبيه بوضوح صوتيًا، وأن تكون الاستجابة قابلة للتنفيذ دون نظر: تأكيد منطوق بأن الرسالة وصلت، ومن سيصل، ومتى. حين يتكلم البيت بلغة واضحة، يصبح مكانًا يُدار بثقة لا بتخمين.",
      ],
      en: [
        "Most smart devices speak the language of the screen: icons, colors, menus. Someone living with a visual disability does not need a clearer screen, they need a different path to the same information, a path that is heard, felt and ordered.",
        "This means a design that works fully with a screen reader, reliable voice commands, and spoken responses that describe state precisely: the door is locked, the temperature is set, the air quality is good. Good description is not decoration, it is the whole interface.",
        "Order and consistency matter as much as sound. When everything has a predictable place and a clear, unchanging name, the user builds a mental map of the home they can trust. Surprises in design are an extra burden on someone relying on memory and hearing.",
        "And in important situations, an alert must be announced clearly in sound, and the response must be actionable without sight: a spoken confirmation that the message arrived, who is coming, and when. When a home speaks a clear language, it becomes a place managed with confidence, not guesswork.",
      ],
    },
  },
  {
    slug: "a-calmer-home-for-a-sensitive-nervous-system",
    date: "2026-08-25",
    category: { ar: "أصحاب الهمم: الحساسية الحسية", en: "People of Determination: Sensory" },
    image: "/brand/health-hero-accessibility.jpg",
    title: {
      ar: "بيت أهدأ لجهاز عصبي أكثر حساسية",
      en: "A calmer home for a sensitive nervous system",
    },
    excerpt: {
      ar: "لبعض الناس، الضوء القوي والصوت المفاجئ ليسا إزعاجًا عابرًا، بل إجهاد حقيقي. البيت يمكن أن يكون مصدر هدوء لا مصدر تحفيز زائد.",
      en: "For some people, harsh light and sudden sound are not a passing annoyance, they are real strain. A home can be a source of calm rather than overload.",
    },
    body: {
      ar: [
        "الحساسية الحسية تجربة يعيشها كثيرون بصمت: إضاءة قوية تؤلم، صوت مفاجئ يربك، تغيّر حاد في المحيط يستهلك طاقة كبيرة لاستعادة التوازن. ما يبدو عاديًا للبعض قد يكون مرهقًا لآخرين، وهذا فرق يستحق الاحترام لا التقليل.",
        "البيت يمكن أن يخفّف هذا العبء. انتقالات هادئة في الإضاءة بدل التغيّر المفاجئ، تنبيهات ألطف وأقل حدة، بيئة صوتية وحرارية مستقرة يمكن ضبطها مسبقًا لتناسب حدود المستخدم لا معدّلات عامة.",
        "الثبات هو الراحة هنا. حين يعرف الإنسان أن محيطه لن يفاجئه، ينخفض التوتر الكامن الذي يستهلكه طوال اليوم. الأنماط المتوقعة والانتقالات المتدرجة تمنح شعورًا بالأمان أكثر مما تمنحه أي ميزة لامعة.",
        "وكل هذا يبقى في يد صاحبه. هو من يحدّد ما المريح وما المزعج، ويضبط بيئته على مقاسه. حين يُصمَّم البيت حول حدود الإنسان الحسية، يتحول من مساحة تتطلب تحمّلًا مستمرًا إلى مكان يمكن أن يرتاح فيه فعلًا.",
      ],
      en: [
        "Sensory sensitivity is an experience many live with quietly: strong light that hurts, a sudden sound that unsettles, a sharp change in surroundings that costs real energy to recover from. What seems ordinary to some can be exhausting to others, and that difference deserves respect, not dismissal.",
        "A home can ease this load. Gentle transitions in lighting instead of abrupt change, softer and less jarring alerts, a stable sound and temperature environment that can be set in advance to fit the user's limits rather than general averages.",
        "Consistency is comfort here. When a person knows their surroundings will not startle them, the underlying tension that drains them all day drops. Predictable patterns and gradual transitions give a sense of safety more than any flashy feature.",
        "And all of this stays in the person's hands. They decide what is soothing and what is disturbing, and tune their environment to their own measure. When a home is designed around a person's sensory limits, it turns from a space that demands constant endurance into a place they can genuinely rest in.",
      ],
    },
  },
  {
    slug: "gentle-structure-for-memory-and-focus",
    date: "2026-08-24",
    category: { ar: "أصحاب الهمم: الإعاقة الذهنية والإدراكية", en: "People of Determination: Cognitive" },
    image: "/brand/health-hero-accessibility.jpg",
    title: {
      ar: "بنية لطيفة تسند الذاكرة والتركيز",
      en: "Gentle structure for memory and focus",
    },
    excerpt: {
      ar: "الدعم الإدراكي الجيد لا يقرّر عن الإنسان، بل يبسّط عليه القرار. تذكير في وقته وخطوة واحدة واضحة أثمن من قائمة طويلة.",
      en: "Good cognitive support does not decide for a person, it makes deciding simpler. A timely reminder and one clear step are worth more than a long list.",
    },
    body: {
      ar: [
        "من يعيش مع صعوبات في الذاكرة أو التركيز لا ينقصه الذكاء، بل يثقله الحمل: خطوات كثيرة، مواعيد متشابكة، قرارات صغيرة متتالية تستنزف الطاقة. الدعم الحقيقي يبدأ بتقليل هذا الحمل، لا بإضافة نظام معقّد آخر.",
        "البيت يمكن أن يسند بهدوء: تذكير لطيف بالدواء أو الماء في وقته، تسلسل مسائي يهيّئ الغرفة للنوم بخطوة واحدة، تنبيه بسيط إن بقي الموقد مشتعلًا أو الباب مفتوحًا. الهدف روتين متوقع يخفّف الحاجة إلى تذكّر كل شيء.",
        "التصميم نفسه جزء من الدعم. لغة واضحة، خطوة واحدة في كل مرة، خيارات قليلة بدل قوائم مزدحمة. حين تكون الواجهة بسيطة ومتسقة، تتحول من عبء إضافي إلى يد ممدودة.",
        "وتبقى الكرامة والاختيار في القلب. الدعم يقترح ويذكّر ويسهّل، لكنه لا يسلب القرار ولا يعامل الإنسان كطفل. حين تُبنى التقنية حول احترام الاستقلالية، تصبح البنية اللطيفة سندًا يمنح ثقة، لا قيدًا يذكّر بالعجز.",
      ],
      en: [
        "Someone living with difficulties in memory or focus does not lack intelligence, they are weighed down by load: too many steps, tangled schedules, a run of small decisions that drains energy. Real support begins by reducing that load, not by adding another complicated system.",
        "A home can quietly assist: a gentle reminder for medication or water at the right time, an evening sequence that prepares the room for sleep in a single step, a simple alert if the stove is still on or a door is left open. The aim is a predictable routine that eases the need to remember everything.",
        "The design itself is part of the support. Clear language, one step at a time, few options instead of crowded menus. When an interface is simple and consistent, it turns from an extra burden into an extended hand.",
        "And dignity and choice stay at the heart of it. Support suggests, reminds and simplifies, but it does not take the decision away or treat a person like a child. When technology is built around respect for independence, gentle structure becomes a support that gives confidence, not a constraint that reminds someone of limitation.",
      ],
    },
  },
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
    slug: "what-a-personal-baseline-is-and-why-one-reading-is-not-enough",
    date: "2026-08-26",
    category: { ar: "النمط الشخصي", en: "Personal Baseline" },
    image: "/brand/health-hero-chronic.jpg",
    title: {
      ar: "ما هو النمط الشخصي، ولماذا لا تكفي قراءة واحدة",
      en: "What a personal baseline is, and why one reading is not enough",
    },
    excerpt: {
      ar: "القراءة المنفردة لحظة واحدة في يوم كامل. النمط الشخصي هو ما يجعل التغيّر مفهومًا.",
      en: "A single reading is one moment in a whole day. A personal baseline is what makes a change meaningful.",
    },
    body: {
      ar: [
        "الرقم وحده لا يعني الكثير. نبض 95 قد يكون طبيعيًا بعد صعود الدرج، وقد يكون لافتًا أثناء الجلوس الهادئ. الفرق ليس في الرقم، بل في مقارنته بما هو معتاد لك في هذا الوقت وهذا السياق.",
        "النمط الشخصي هو خطك الأساسي: أوقات نومك واستيقاظك، حركتك المعتادة خلال اليوم، فترات هدوئك الطبيعية، والبيئة المنزلية المرتبطة براحتك. تُبنى هذه الصورة مع الوقت، لا من يوم واحد.",
        "عندما يعرف النظام نمطك، يصبح قادرًا على ملاحظة الانحراف عنه: حركة غائبة في وقت اعتدت فيه النشاط، أو قراءة تختلف عن معدّلك المعتاد. هذا الانحراف، لا الرقم المطلق، هو ما يستحق الانتباه.",
        "لهذا لا تعتمد سيلترا هيلث على قراءة منفردة. تجمع الإشارات المتزامنة وتقارنها بنمطك قبل أي خطوة، فتقلّل الإنذارات غير الضرورية وتجعل التنبيه، حين يأتي، ذا معنى.",
      ],
      en: [
        "A number on its own does not mean much. A pulse of 95 can be normal after climbing stairs, and notable during quiet sitting. The difference is not the number, but how it compares to what is usual for you at this time and context.",
        "A personal baseline is your normal: your sleep and wake times, your usual daytime movement, your natural quiet periods, and the home environment tied to your comfort. This picture is built over time, not from a single day.",
        "Once the system knows your pattern, it can notice deviation from it: movement missing at a time you are usually active, or a reading unlike your typical range. That deviation, not the absolute number, is what deserves attention.",
        "This is why SYLTRA HEALTH never relies on a single reading. It gathers coinciding signals and compares them to your baseline before any step, reducing needless alerts and making an alert, when it comes, meaningful.",
      ],
    },
  },
  {
    slug: "building-a-trusted-circle-who-your-home-reaches",
    date: "2026-08-25",
    category: { ar: "الدائرة الموثوقة", en: "Trusted Circle" },
    image: "/brand/health-hero-older.jpg",
    title: {
      ar: "الدائرة الموثوقة: من يصل إليه بيتك، وكيف",
      en: "Building a trusted circle: who your home reaches, and how",
    },
    excerpt: {
      ar: "الهدف ليس إشعار الجميع، بل الوصول إلى الشخص الأنسب بأقل قدر ضروري من المعلومات.",
      en: "The goal is not to notify everyone. It is to reach the most suitable person with the minimum necessary information.",
    },
    body: {
      ar: [
        "عند الحاجة إلى مساعدة، الإنذار العام لكل الأسرة ليس الحل الأفضل. قد يزعج من لا يستطيع الوصول، ويؤخّر من يستطيع. الأفضل أن يصل التنبيه إلى الشخص الأنسب في تلك اللحظة.",
        "في سيلترا هيلث تنشئ دائرة من أشخاص تثق بهم، وتحدّد لكل واحد علاقته وأولويته، وما البيانات التي يراها، وأوقات توفّره، وهل يستطيع دخول المنزل. أنت من يرسم هذه الحدود.",
        "عند الحاجة، يختار النظام وفق عوامل عملية: زمن الوصول المتوقع، القرب، حالة الاتصال، الأولوية، والقبول. وإن لم يقبل الأول، ينتقل إلى التالي وفق خطتك.",
        "وتُشارك أقل كمية لازمة فقط: ما يكفي ليعرف الشخص أن هناك حاجة وأين، دون كشف تفاصيل لا لزوم لها. الخصوصية والوصول السريع ليسا على طرفي نقيض هنا.",
      ],
      en: [
        "When help is needed, a general alarm to the whole family is not the best answer. It can disturb those who cannot reach you and delay those who can. It is better for the alert to reach the most suitable person at that moment.",
        "In SYLTRA HEALTH you build a circle of people you trust and set each one's relationship and priority, what data they see, when they are available, and whether they can enter the home. You draw these boundaries.",
        "When needed, the system chooses by practical factors: expected arrival time, proximity, connection status, priority and acceptance. If the first does not accept, it moves to the next under your plan.",
        "And only the minimum necessary is shared: enough for the person to know there is a need and where, without revealing details that are not required. Privacy and fast access are not opposites here.",
      ],
    },
  },
  {
    slug: "test-mode-trying-a-response-plan-before-it-is-needed",
    date: "2026-08-24",
    category: { ar: "الأمان أولًا", en: "Safety First" },
    image: "/brand/health-hero-privacy.jpg",
    title: {
      ar: "وضع الاختبار: جرّب خطة الاستجابة قبل أن تحتاجها",
      en: "Test mode: trying a response plan before it is needed",
    },
    excerpt: {
      ar: "أفضل وقت لتفهم كيف تعمل الاستجابة هو قبل الحاجة إليها، وبدون إرسال أي تنبيه حقيقي.",
      en: "The best time to understand how response works is before you need it, without sending any real alert.",
    },
    body: {
      ar: [
        "الثقة في أي نظام استجابة تأتي من رؤيته يعمل. لكن لا أحد يريد أن يجرّب ذلك في لحظة حقيقية. لهذا يبدأ الإعداد بوضع اختبار يحاكي الحالة دون تنبيه فعلي لأحد.",
        "في وضع الاختبار ترى كيف يتحقق النظام منك، كم ينتظر، ومن سيُنبَّه في كل مستوى لو لم تستجب. تفهم الرحلة كاملة وأنت مطمئن أن لا شيء يُرسل خارج شاشتك.",
        "هذا يمنحك فرصة لضبط خطتك: ربما تريد مدة انتظار أطول، أو ترتيبًا مختلفًا لأشخاص دائرتك، أو معلومات أقل تُشارك. تعدّل قبل أن تعتمد الخطة.",
        "الأمان أولًا يعني أيضًا أن النسخة الأولى تبدأ بقواعد واضحة قابلة للاختبار، لا بقرارات تلقائية عن الطوارئ. تفهم ما يفعله النظام ولماذا، خطوة بخطوة.",
      ],
      en: [
        "Trust in any response system comes from seeing it work. But no one wants to try that in a real moment. So setup begins with a test mode that simulates the situation without actually alerting anyone.",
        "In test mode you see how the system checks in with you, how long it waits, and who would be alerted at each level if you did not respond. You understand the full journey, reassured that nothing leaves your screen.",
        "This is a chance to tune your plan: perhaps a longer wait, a different order for your circle, or less information shared. You adjust before you commit the plan.",
        "Safety first also means the first version starts with clear, testable rules, not automated emergency decisions. You understand what the system does and why, step by step.",
      ],
    },
  },
  {
    slug: "when-the-home-adapts-to-you",
    date: "2026-08-23",
    category: { ar: "البيئة المتكيّفة", en: "Adaptive Environment" },
    image: "/brand/health-hero-home-wellness.jpg",
    title: {
      ar: "عندما يتكيّف البيت معك، لا العكس",
      en: "When the home adapts to you, not the other way round",
    },
    excerpt: {
      ar: "المنزل الذكي الحقيقي لا ينتظر أوامرك فقط. يهيّئ بيئته وفق حالتك وروتينك بموافقتك.",
      en: "A truly smart home does not just wait for your commands. It adapts to your state and routine, with your consent.",
    },
    body: {
      ar: [
        "معظم أنظمة المنزل الذكي تنفّذ ما تطلبه: أطفئ الضوء، اضبط الحرارة. مفيد، لكنه يبقى رد فعل لأوامرك. الخطوة التالية أن يراعي البيت حالتك دون أن تطلب.",
        "عند ربط بيانات صحتك ببيئة المنزل، تصبح إعدادات وافقت عليها مسبقًا ممكنة: تعديل الحرارة إلى نطاق راحتك قبل النوم، تحسين التهوية عند انخفاض جودة الهواء، إضاءة خافتة عند الحركة الليلية، وتذكير لطيف بالحركة أو الماء.",
        "المفتاح هنا الموافقة المسبقة. البيت لا يقرّر عنك، بل ينفّذ ما اخترته مسبقًا في السياق المناسب. تبقى السيطرة لك، ويبقى الإجراء داعمًا للراحة لا بديلًا عن قرار طبي.",
        "النتيجة بيئة تعمل بهدوء في الخلفية لصالحك، فتقلّل التعب الصغير المتكرر الذي لا نلاحظه، وتترك لك طاقة أكثر لما يهم.",
      ],
      en: [
        "Most smart-home systems do what you ask: turn off the light, set the temperature. Useful, but still a reaction to your commands. The next step is a home that considers your state without being asked.",
        "When your health data connects with the home environment, settings you approved in advance become possible: bringing the temperature to your comfort range before sleep, improving ventilation when air quality drops, dim lighting on night movement, and a gentle reminder to move or hydrate.",
        "The key here is prior consent. The home does not decide for you. It runs what you chose earlier, in the right context. Control stays with you, and the action supports comfort rather than replacing a medical decision.",
        "The result is an environment that quietly works in your favor, reducing the small recurring friction we rarely notice, and leaving you more energy for what matters.",
      ],
    },
  },
  {
    slug: "consent-first-connecting-only-what-you-choose",
    date: "2026-08-22",
    category: { ar: "الخصوصية", en: "Privacy" },
    image: "/brand/health-hero-individuals.jpg",
    title: {
      ar: "الموافقة أولًا: تربط فقط ما تختاره",
      en: "Consent first: connecting only what you choose",
    },
    excerpt: {
      ar: "لا تُجمع البيانات لمجرد توفّرها. كل مصدر يبدأ باختيار واضح، ويمكن إيقافه في أي لحظة.",
      en: "Data is not collected just because it is available. Every source starts with a clear choice, and can be stopped at any moment.",
    },
    body: {
      ar: [
        "في الصحة تحديدًا، ليست القاعدة أن نجمع كل ما نستطيع. القاعدة أن نجمع ما تحتاجه التجربة فعلًا، وبموافقتك على كل نوع على حدة.",
        "قبل ربط أي جهاز، تعرف ما البيانات التي ستُستخدم ولماذا. تربط ما تريد فقط، وتترك الباقي. وكل ربط إضافي هو بيانات إضافية يجب أن يكون لها سبب واضح.",
        "التحكم مستمر لا لحظي: تستطيع مراجعة الصلاحيات، تعديل من يرى ماذا، إيقاف مشاركة الموقع، سحب الموافقة، وحذف بياناتك، ومراجعة سجل التنبيهات والمشاركة.",
        "هذه ليست فقرة قانونية في نهاية الصفحة، بل جزء من تصميم التجربة نفسها. حين تُبنى الثقة على الموافقة الواضحة وتقليل البيانات، تصبح نتيجة طبيعية لا وعدًا.",
      ],
      en: [
        "In health especially, the rule is not to collect everything we can. The rule is to collect what the experience genuinely needs, with your consent for each type separately.",
        "Before connecting any device, you know what data will be used and why. You connect only what you want and leave the rest. Every extra connection is extra data that should have a clear reason.",
        "Control is ongoing, not a one-time step: you can review permissions, change who sees what, stop location sharing, withdraw consent, delete your data, and review the alert and sharing log.",
        "This is not a legal paragraph at the bottom of the page. It is part of the design of the experience itself. When trust is built on clear consent and data minimization, it becomes a natural result, not a promise.",
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
