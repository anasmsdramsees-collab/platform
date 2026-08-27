import type { Locale } from "@/lib/i18n/config";
import type { DivisionKey, DivisionMeta } from "@/lib/divisions";

interface Bi {
  ar: string;
  en: string;
}
interface Item {
  title: Bi;
  desc: Bi;
}
interface SysItem {
  title: Bi;
  en: string; // small latin sublabel (same in both locales)
  img?: string; // optional illustrative image under /public
  slug?: string; // when set, the tile links to /[locale]/[division]/[slug]
  lead?: Bi; // short intro shown in the detail hero
  body?: Bi[]; // longer overview paragraphs on the detail page
  points?: Bi[]; // key points / what we offer on the detail page
  useCases?: Bi[]; // where it fits / applications
}
interface HeroSlide {
  title: Bi;
  caption: Bi;
  image?: string; // optional per-slide hero image; falls back to division.image
}

export interface DivisionContent {
  h1: Bi;
  intro: Bi;
  heroSlides: HeroSlide[];
  servicesEyebrow: Bi;
  servicesTitle: Bi;
  services: Item[];
  systemsEyebrow: Bi;
  systemsTitle: Bi;
  systems: SysItem[];
  systemsNote: Bi;
  statementTitle: Bi;
  statementBody: Bi;
  flowEyebrow: Bi;
  flowTitle: Bi;
  flow: Item[];
  ctaTitle: Bi;
  ctaBody: Bi;
}

export function pick(b: Bi, locale: Locale) {
  return locale === "ar" ? b.ar : b.en;
}

export const DIVISION_CONTENT: Record<Exclude<DivisionKey, "life">, DivisionContent> = {
  climate: {
    h1: { ar: "مناخ ذكي. راحة محسوبة.", en: "Smart climate. Measured comfort." },
    intro: {
      ar: "في سيلترا كلايمت نتولّى تكييف مشروعك من أوّله لآخره: ندرس المكان، نختار النظام الأنسب، ننفّذه بأيدٍ هندسية، ونبقى معك بالصيانة، راحة تدوم وفاتورة أخفّ.",
      en: "At Syltra Climate we handle your cooling end to end: we study the space, pick the right system, install it with real engineering, and stay with you for maintenance, comfort that lasts and a lighter bill.",
    },
    heroSlides: [
      { title: { ar: "أنظمة مركزية وVRF", en: "Central & VRF systems" }, caption: { ar: "توزيع متّزن للهواء عبر دكت مصمّم بعناية أو حلول VRF متعددة المناطق.", en: "Balanced air distribution through engineered ducting or multi-zone VRF." }, image: "/divisions/climate-2.jpg" },
      { title: { ar: "جودة هواء وتهوية", en: "Air quality & ventilation" }, caption: { ar: "فلترة وتهوية وتحكّم بالرطوبة لهواء أنظف داخل كل غرفة.", en: "Filtration, ventilation and humidity control for cleaner air in every room." }, image: "/divisions/climate.jpg" },
      { title: { ar: "صيانة وتحكّم ذكي", en: "Maintenance & smart control" }, caption: { ar: "عقود صيانة وربط بالتطبيق يحافظ على الأداء ويخفّض الاستهلاك.", en: "Service contracts and app control that sustain performance and cut consumption." }, image: "/divisions/climate-2.jpg" },
    ],
    servicesEyebrow: { ar: "الخدمات", en: "Services" },
    servicesTitle: { ar: "من التصميم إلى التشغيل، منظومة واحدة منسّقة.", en: "From design to operation, one coordinated system." },
    services: [
      { title: { ar: "دراسة الحمل الحراري", en: "Heat-load study" }, desc: { ar: "حساب دقيق للأحمال يحدّد النظام والسعة الأنسب لكل مساحة.", en: "Accurate load calculation that sizes the right system for each space." } },
      { title: { ar: "التوريد والتركيب", en: "Supply & installation" }, desc: { ar: "معدات معتمدة وتنفيذ ميداني منضبط من المصدر حتى التشغيل.", en: "Certified equipment and disciplined field execution end to end." } },
      { title: { ar: "مركزي ودكت وVRF", en: "Central, duct & VRF" }, desc: { ar: "من الدكت المخطّط إلى حلول VRF متعددة المناطق والأنظمة المركزية.", en: "From engineered ducting to multi-zone VRF and central systems." } },
      { title: { ar: "الاختبار والموازنة", en: "Testing & balancing" }, desc: { ar: "ضبط التدفّق والموازنة (TAB) لأداء متّزن قبل التسليم.", en: "Airflow balancing (TAB) for even performance before handover." } },
      { title: { ar: "عقود الصيانة", en: "Maintenance contracts" }, desc: { ar: "زيارات مجدولة وفحص وتنظيف وتقارير أداء ودعم بالأولوية.", en: "Scheduled visits, inspection, cleaning, performance reports and priority support." } },
      { title: { ar: "تحكّم ذكي وجودة هواء", en: "Smart control & air quality" }, desc: { ar: "ربط التكييف بالتطبيق والمناطق والحساسات مع اهتمام بالتهوية.", en: "App, zone and sensor control with attention to ventilation." } },
    ],
    systemsEyebrow: { ar: "الأنظمة", en: "Systems" },
    systemsTitle: { ar: "حلول التكييف التي نغطّيها.", en: "The HVAC solutions we cover." },
    systems: [
      {
        title: { ar: "التكييف المركزي", en: "" }, en: "Central AC",
        img: "/divisions/climate-systems/central.jpg", slug: "central",
        lead: {
          ar: "للمباني الكبيرة والمجمّعات، التكييف المركزي والشيلر هو الحل الأهدأ والأكفأ: تبريد موحّد يُدار من مكان واحد. نبدأ بدراسة دقيقة لمبناك، ونمشي معك خطوة بخطوة حتى يعمل النظام كما ينبغي، ونبقى معك بعدها.",
          en: "For large buildings and complexes, central and chiller cooling is the quietest, most efficient answer: unified cooling managed from one place. We start with a careful study of your building, walk you through every step until it runs as it should, and stay with you afterward.",
        },
        body: [
          { ar: 'التكييف المركزي هو العمود الفقري لتبريد المباني الكبيرة كالأبراج والمجمّعات التجارية والمرافق الحكومية والفنادق. يعتمد على وحدة تبريد مركزية (شيلر) توزّع التبريد عبر المبنى بكفاءة أعلى واستهلاك أقل مقارنة بالوحدات المنفصلة، مع تحكّم مركزي يسهّل الإدارة والصيانة.', en: 'Central air conditioning is the backbone of cooling large buildings, towers, commercial complexes, government facilities and hotels. A central chiller distributes cooling across the building with higher efficiency and lower consumption than standalone units, with central control that simplifies management and maintenance.' },
          { ar: 'في سيلترا كلايمت نبدأ بدراسة حمل حراري دقيقة تحدّد نوع الشيلر (هوائي أو مائي) وسعته، ثم نصمّم شبكة التوزيع والتحكّم، ونوّرد معدات معتمدة، وننفّذ التركيب بإشراف هندسي، وننتهي باختبار وموازنة قبل التسليم، يليها عقود صيانة تحافظ على الأداء والعمر الافتراضي.', en: 'At Syltra Climate we begin with an accurate heat-load study that defines the chiller type (air- or water-cooled) and capacity, then design the distribution and control network, supply certified equipment, execute installation under engineering supervision, and finish with testing and balancing before handover, followed by maintenance contracts that protect performance and lifespan.' },
        ],
        points: [
          { ar: "دراسة حمل حراري وتحديد السعة الأنسب", en: "Heat-load study and correct capacity sizing" },
          { ar: "شيلر هوائي أو مائي حسب طبيعة المشروع", en: "Air- or water-cooled chillers to suit the project" },
          { ar: "توزيع هواء عبر دكت مصمّم بعناية", en: "Air distribution through carefully engineered ducting" },
          { ar: "تحكّم مركزي ومناطق متعددة", en: "Central control with multiple zones" },
          { ar: "عقود صيانة تحافظ على الكفاءة والعمر", en: "Maintenance contracts that protect efficiency and lifespan" },
        ],
        useCases: [
          { ar: 'الأبراج والمباني السكنية الكبيرة', en: 'Towers and large residential buildings' },
          { ar: 'المجمّعات التجارية والمولات', en: 'Commercial complexes and malls' },
          { ar: 'الفنادق والمنشآت الضيافية', en: 'Hotels and hospitality facilities' },
          { ar: 'المرافق الحكومية والمستشفيات', en: 'Government facilities and hospitals' },
        ],
      },
      {
        title: { ar: "أنظمة VRF/VRV", en: "" }, en: "VRF / VRV",
        img: "/divisions/climate-systems/vrf.jpg", slug: "vrf",
        lead: {
          ar: "أنظمة VRF/VRV تمنحك تبريدًا مرنًا لمناطق متعددة بتحكّم مستقل لكل غرفة وكفاءة عالية في الطاقة، مثالية للمكاتب والفلل والمباني ذات الاستخدامات المتنوّعة.",
          en: "VRF/VRV systems give flexible cooling across many zones with independent per-room control and high energy efficiency, ideal for offices, villas and mixed-use buildings.",
        },
        body: [
          { ar: 'تقنية VRF/VRV (التدفّق المتغيّر لغاز التبريد) من أذكى حلول التكييف الحديثة: وحدة خارجية واحدة تخدم عدة وحدات داخلية، وكل منطقة تُضبط بدرجة حرارتها المستقلة. النظام يعدّل استهلاكه تلقائيًا حسب الحمل الفعلي، ما يحقّق توفيرًا كبيرًا في الطاقة مع راحة دقيقة.', en: 'VRF/VRV (variable refrigerant flow) is one of the smartest modern cooling solutions: a single outdoor unit serves several indoor units, and each zone holds its own independent temperature. The system modulates its consumption automatically to the actual load, delivering major energy savings with precise comfort.' },
          { ar: 'نصمّم نظام VRF ليناسب توزيع المساحات وأنماط الاستخدام، مثالي للمكاتب والفلل والمباني متعددة الاستخدامات حيث تختلف احتياجات كل جناح. نراعي أطوال المواسير والفروق المسموحة، ونربط النظام بالتطبيق وجداول تشغيل ذكية.', en: 'We design the VRF system around the layout and usage patterns, ideal for offices, villas and mixed-use buildings where each wing has different needs. We respect pipe lengths and allowed differentials, and connect the system to an app and smart schedules.' },
        ],
        points: [
          { ar: "تحكّم مستقل في درجة حرارة كل منطقة", en: "Independent temperature control per zone" },
          { ar: "كفاءة عالية وتوفير في استهلاك الطاقة", en: "High efficiency and lower energy consumption" },
          { ar: "مرونة في التمديد للمساحات الواسعة", en: "Flexible piping for large layouts" },
          { ar: "تشغيل هادئ وتوزيع متّزن", en: "Quiet operation and balanced distribution" },
          { ar: "ربط بالتطبيق وجداول تشغيل ذكية", en: "App control and smart schedules" },
        ],
        useCases: [
          { ar: 'المكاتب والمساحات الإدارية', en: 'Offices and administrative spaces' },
          { ar: 'الفلل والمنازل الكبيرة', en: 'Villas and large homes' },
          { ar: 'المباني متعددة الاستخدامات', en: 'Mixed-use buildings' },
          { ar: 'العيادات والمراكز التجارية الصغيرة', en: 'Clinics and small commercial centers' },
        ],
      },
      {
        title: { ar: "دكت وتوزيع الهواء", en: "" }, en: "Ducted air",
        img: "/divisions/climate-systems/ducted.jpg", slug: "ducted",
        lead: {
          ar: "أنظمة الدكت المخفية توزّع الهواء بانسيابية وهدوء مع مظهر داخلي نظيف، نصمّم مسارات الدكت والمخارج بعناية لأداء متّزن في كل غرفة.",
          en: "Concealed ducted systems distribute air smoothly and quietly with a clean interior look, we engineer duct runs and grilles for even performance in every room.",
        },
        body: [
          { ar: 'أنظمة الدكت المخفية تمنحك تبريدًا موزّعًا بهدوء ومظهرًا داخليًا نظيفًا بلا وحدات ظاهرة، الوحدة مخفية في السقف الساقط والهواء يصل عبر شبكة دكت ومخارج مدروسة. الخيار المفضّل حين تكون الأناقة الداخلية والتوزيع المتّزن أولوية.', en: 'Concealed ducted systems give you quietly distributed cooling and a clean interior with no visible units, the unit hides in the false ceiling and air reaches through an engineered duct network and grilles. The preferred choice when interior elegance and even distribution are a priority.' },
          { ar: 'نصمّم مسارات الدكت لتقليل الفاقد والضوضاء، ونحسب أقطارها ومخارجها بدقة، ونعزلها حراريًا وصوتيًا، ثم نجري اختبار وموازنة (TAB) لضمان تدفّق متساوٍ في كل غرفة قبل التسليم.', en: 'We design duct runs to reduce loss and noise, size ducts and grilles precisely, insulate them thermally and acoustically, then perform testing and balancing (TAB) to ensure even flow in every room before handover.' },
        ],
        points: [
          { ar: "تصميم مسارات دكت يقلّل الفاقد والضوضاء", en: "Duct routing that cuts loss and noise" },
          { ar: "مخارج هواء موزّعة بعناية لكل غرفة", en: "Grilles placed carefully per room" },
          { ar: "مظهر داخلي نظيف بلا وحدات ظاهرة", en: "Clean interiors with no visible units" },
          { ar: "عزل حراري وصوتي للدكت", en: "Thermal and acoustic duct insulation" },
          { ar: "اختبار وموازنة (TAB) قبل التسليم", en: "Testing and balancing (TAB) before handover" },
        ],
        useCases: [
          { ar: 'الفلل والمنازل الراقية', en: 'Upscale villas and homes' },
          { ar: 'المكاتب والمساحات المفتوحة', en: 'Offices and open spaces' },
          { ar: 'المطاعم والمقاهي', en: 'Restaurants and cafés' },
          { ar: 'المشاريع ذات التصميم الداخلي المميّز', en: 'Projects with distinctive interior design' },
        ],
      },
      {
        title: { ar: "سبليت وملتي سبليت", en: "" }, en: "Split systems",
        img: "/divisions/climate-systems/split.jpg", slug: "split",
        lead: {
          ar: "أنظمة السبليت والملتي سبليت حل عملي واقتصادي للغرف والوحدات الصغيرة، تركيب سريع وكفاءة جيدة وصيانة سهلة.",
          en: "Split and multi-split systems are a practical, economical solution for rooms and smaller units, quick installation, good efficiency and easy maintenance.",
        },
        body: [
          { ar: 'أنظمة السبليت والملتي سبليت هي الحل الأسرع والأوفر للغرف والوحدات الصغيرة والإضافات، تركيب نظيف وسريع وكفاءة جيدة وصيانة سهلة. في الملتي سبليت تخدم وحدة خارجية واحدة عدة وحدات داخلية لتوفير المساحة والمظهر.', en: 'Split and multi-split systems are the fastest, most economical solution for rooms, small units and additions, clean, quick installation, good efficiency and easy maintenance. In multi-split, one outdoor unit serves several indoor units to save space and improve the look.' },
          { ar: 'نساعدك على اختيار السعة المناسبة لكل غرفة والموديل الأنسب (خاصة موديلات الإنفرتر الموفّرة للطاقة)، وننفّذ تركيبًا نظيفًا، ونوفّر صيانة دورية بقطع معتمدة تطيل عمر الجهاز.', en: "We help you choose the right capacity per room and the best model (especially energy-saving inverter models), install cleanly, and provide routine maintenance with certified parts that extend the unit's life." },
        ],
        points: [
          { ar: "اختيار السعة المناسبة لكل غرفة", en: "Right capacity for each room" },
          { ar: "وحدة خارجية واحدة لعدة داخلية (ملتي)", en: "One outdoor unit for several indoor (multi)" },
          { ar: "تركيب نظيف وسريع", en: "Clean, fast installation" },
          { ar: "موديلات موفّرة للطاقة (إنفرتر)", en: "Energy-saving inverter models" },
          { ar: "صيانة دورية وقطع معتمدة", en: "Routine maintenance and certified parts" },
        ],
        useCases: [
          { ar: 'الشقق والوحدات السكنية الصغيرة', en: 'Apartments and small residential units' },
          { ar: 'الغرف والمكاتب المنفردة', en: 'Single rooms and offices' },
          { ar: 'الإضافات والملاحق', en: 'Extensions and annexes' },
          { ar: 'المحلات الصغيرة', en: 'Small shops' },
        ],
      },
      {
        title: { ar: "تهوية وتجديد الهواء", en: "" }, en: "Ventilation",
        img: "/divisions/climate-systems/ventilation.jpg", slug: "ventilation",
        lead: {
          ar: "التهوية الجيدة لا تقل أهمية عن التبريد، نصمّم أنظمة تجديد هواء وفلترة تُدخل هواءً نقيًا وتطرد الملوّثات والرطوبة الزائدة لهواء داخلي صحي.",
          en: "Good ventilation matters as much as cooling, we design fresh-air and filtration systems that bring in clean air and remove pollutants and excess humidity for healthy indoor air.",
        },
        body: [
          { ar: 'جودة الهواء الداخلي لا تقل أهمية عن التبريد، فالتهوية السيّئة تعني رطوبة وروائح وملوّثات وتراكم ثاني أكسيد الكربون. نصمّم أنظمة تجديد هواء وفلترة تُدخل هواءً نقيًا وتطرد الملوّثات، لهواء داخلي صحّي ومريح.', en: 'Indoor air quality matters as much as cooling, poor ventilation means humidity, odors, pollutants and CO₂ build-up. We design fresh-air and filtration systems that bring in clean air and remove pollutants, for healthy, comfortable indoor air.' },
          { ar: 'نستخدم وحدات مناولة الهواء (AHU) وأنظمة الاسترجاع الحراري (HRV/ERV) التي تقلّل استهلاك الطاقة أثناء تجديد الهواء، مع فلترة متعددة المراحل وتحكّم بالرطوبة والضغط، حل أساسي للمطاعم والعيادات والمساحات المزدحمة.', en: 'We use air-handling units (AHU) and heat-recovery systems (HRV/ERV) that cut energy use while renewing air, with multi-stage filtration and humidity/pressure control, essential for restaurants, clinics and busy spaces.' },
        ],
        points: [
          { ar: "وحدات مناولة هواء (AHU) وتجديد الهواء", en: "Air-handling units (AHU) and fresh air" },
          { ar: "فلترة متعددة المراحل لهواء أنظف", en: "Multi-stage filtration for cleaner air" },
          { ar: "استرجاع حراري لتقليل الاستهلاك (HRV/ERV)", en: "Heat recovery to cut consumption (HRV/ERV)" },
          { ar: "تحكّم بالرطوبة والضغط", en: "Humidity and pressure control" },
          { ar: "مناسبة للمطاعم والعيادات والمساحات المزدحمة", en: "Suited to restaurants, clinics and busy spaces" },
        ],
        useCases: [
          { ar: 'المطاعم والمطابخ التجارية', en: 'Restaurants and commercial kitchens' },
          { ar: 'العيادات والمرافق الصحية', en: 'Clinics and health facilities' },
          { ar: 'القاعات والمساحات المزدحمة', en: 'Halls and crowded spaces' },
          { ar: 'المصانع والورش', en: 'Factories and workshops' },
        ],
      },
      {
        title: { ar: "التحكّم والأتمتة", en: "" }, en: "Controls",
        img: "/divisions/climate-systems/controls.jpg", slug: "controls",
        lead: {
          ar: "التحكّم الذكي يحوّل التكييف من جهاز إلى نظام، جداول ومناطق وحساسات وربط بالتطبيق تحافظ على الراحة وتخفّض الفاتورة.",
          en: "Smart control turns AC from a device into a system, schedules, zones, sensors and app control that keep comfort while cutting the bill.",
        },
        body: [
          { ar: 'التحكّم الذكي يحوّل التكييف من مجرد جهاز إلى نظام يفهم احتياجك: جداول تشغيل، مناطق مستقلة، حساسات إشغال وجودة هواء، وربط بالتطبيق، تحافظ على الراحة تلقائيًا وتخفّض الفاتورة دون أن تنتبه.', en: 'Smart control turns AC from a mere device into a system that understands your needs: schedules, independent zones, occupancy and air-quality sensors, and app connectivity, keeping comfort automatically and cutting the bill without you noticing.' },
          { ar: 'نربط أنظمة التكييف بمنصّة سيلترا لايف لتعمل ضمن منظومة المنزل أو المبنى الذكي كاملة، مع تقارير استهلاك واضحة تساعدك على اتخاذ قرارات توفير حقيقية.', en: 'We connect the AC to the Syltra Life platform so it works within the full smart-home or building ecosystem, with clear consumption reports that help you make real energy-saving decisions.' },
        ],
        points: [
          { ar: "ثيرموستات ذكي وجداول تشغيل", en: "Smart thermostats and schedules" },
          { ar: "مناطق متعددة بتحكّم مستقل", en: "Multiple zones with independent control" },
          { ar: "حساسات إشغال وجودة هواء", en: "Occupancy and air-quality sensors" },
          { ar: "ربط بمنصّة سيلترا لايف والتطبيق", en: "Integration with the Syltra Life platform and app" },
          { ar: "تقارير استهلاك تساعدك على التوفير", en: "Consumption reports that help you save" },
        ],
        useCases: [
          { ar: 'المنازل والفلل الذكية', en: 'Smart homes and villas' },
          { ar: 'المكاتب والمباني الإدارية', en: 'Offices and administrative buildings' },
          { ar: 'الفنادق والمنشآت متعددة الغرف', en: 'Hotels and multi-room facilities' },
          { ar: 'أي مشروع يسعى لتوفير الطاقة', en: 'Any project aiming to save energy' },
        ],
      },
    ],
    systemsNote: { ar: "الاختيار يعتمد على المساحة والاستخدام والحمل الحراري وعدد المناطق ومستوى التحكّم المطلوب.", en: "Selection depends on space, usage, heat load, number of zones and the control level required." },
    statementTitle: { ar: "الراحة أكثر من درجة حرارة.", en: "Comfort is more than a temperature." },
    statementBody: { ar: "نوازن الحرارة والرطوبة وتجديد الهواء والصوت، لتشعر بالفرق دون أن تراه.", en: "We balance heat, humidity, fresh air and sound, so you feel the difference without seeing it." },
    flowEyebrow: { ar: "مسار العمل", en: "How we work" },
    flowTitle: { ar: "مسار واحد من المعاينة حتى الصيانة.", en: "One path from survey to maintenance." },
    flow: [
      { title: { ar: "المعاينة والدراسة", en: "Survey & study" }, desc: { ar: "حساب الأحمال.", en: "Load calculation." } },
      { title: { ar: "التصميم والعرض", en: "Design & proposal" }, desc: { ar: "اختيار النظام.", en: "System selection." } },
      { title: { ar: "التوريد والتركيب", en: "Supply & install" }, desc: { ar: "تنفيذ ميداني.", en: "Field execution." } },
      { title: { ar: "الاختبار والتشغيل", en: "Test & commission" }, desc: { ar: "موازنة وتسليم.", en: "Balance & handover." } },
      { title: { ar: "الصيانة والدعم", en: "Maintenance" }, desc: { ar: "عقود دورية.", en: "Recurring contracts." } },
    ],
    ctaTitle: { ar: "ابدأ بمعاينة الموقع.", en: "Start with a site survey." },
    ctaBody: { ar: "نحدّد النظام المناسب لمساحتك، ونجهّز عرضًا واضحًا للتوريد والتنفيذ والصيانة والتحكّم الذكي.", en: "We size the right system for your space and prepare a clear proposal for supply, execution, maintenance and smart control." },
  },

  glide: {
    h1: { ar: "حركة آمنة ترفع قيمة المبنى.", en: "Safe movement that lifts a building's value." },
    intro: {
      ar: "المصعد يرفع قيمة مبناك كل يوم. في سيلترا جلايد نرافقك من أول فكرة حتى آخر زيارة صيانة: دراسة، اختيار، تركيب، وتشغيل آمن يدوم.",
      en: "An elevator adds value to your building every day. At Syltra Glide we walk with you from the first idea to the last service visit: study, selection, installation, and safe operation that lasts.",
    },
    heroSlides: [
      { title: { ar: "مصاعد الركاب والفلل", en: "Passenger & villa lifts" }, caption: { ar: "حلول رأسية سلسة للسكني والتجاري بمعايير أمان عالية.", en: "Smooth vertical solutions for residential and commercial with high safety standards." }, image: "/divisions/glide.jpg" },
      { title: { ar: "التركيب والتنفيذ الميداني", en: "Installation & field execution" }, caption: { ar: "تركيب دقيق في بئر المصعد يراعي المعدات وواجهات المبنى.", en: "Precise in-shaft installation that respects equipment and building facades." }, image: "/divisions/glide-2.jpg" },
      { title: { ar: "تحديث وصيانة", en: "Modernization & service" }, caption: { ar: "رفع كفاءة المصاعد القائمة وعقود صيانة تضمن الجاهزية.", en: "Upgrading existing lifts and service contracts that keep them ready." }, image: "/divisions/glide-1.jpg" },
    ],
    servicesEyebrow: { ar: "النطاق", en: "Scope" },
    servicesTitle: { ar: "نغطّي دورة حياة المصعد بالكامل.", en: "We cover the full lift lifecycle." },
    services: [
      { title: { ar: "الدراسة والاستشارات الفنية", en: "Study & consulting" }, desc: { ar: "دراسة الاحتياج واختيار النظام الأنسب لطبيعة المبنى.", en: "Needs study and selecting the best system for the building." } },
      { title: { ar: "التوريد والتركيب", en: "Supply & installation" }, desc: { ar: "تنفيذ دقيق يراعي البئر والمعدات وواجهات المبنى.", en: "Precise execution respecting the shaft, equipment and facades." } },
      { title: { ar: "الاختبار والتشغيل والتسليم", en: "Testing & commissioning" }, desc: { ar: "اختبار وضبط وتسليم موثّق قبل التشغيل.", en: "Documented testing, tuning and handover before operation." } },
      { title: { ar: "الصيانة الوقائية والطوارئ", en: "Preventive & emergency service" }, desc: { ar: "زيارات مجدولة واستجابة للحالات الطارئة.", en: "Scheduled visits and response to emergencies." } },
      { title: { ar: "التحديث والتطوير", en: "Modernization" }, desc: { ar: "رفع كفاءة المصاعد القائمة على مراحل.", en: "Upgrading existing lifts in stages." } },
      { title: { ar: "العقود السنوية والفحص", en: "Annual contracts & inspection" }, desc: { ar: "عقود سنوية وفحص وتقارير حالة دورية.", en: "Annual contracts, inspection and periodic condition reports." } },
    ],
    systemsEyebrow: { ar: "الحلول", en: "Solutions" },
    systemsTitle: { ar: "مصاعد لكل استخدام، سكني وتجاري وضيافة.", en: "Lifts for every use, residential, commercial and hospitality." },
    systems: [
      {
        title: { ar: 'مصاعد الركاب', en: "" }, en: "Passenger",
        img: "/divisions/glide-systems/passenger.jpg", slug: "passenger",
        lead: { ar: 'مصاعد الركاب هي القلب النابض للمباني السكنية والتجارية، حركة رأسية سلسة وآمنة وموثوقة تنقل الناس بين الطوابق بسرعة وراحة. نوفّر حلولًا بغرفة ماكينة (MR) وبدونها (MRL) تناسب مختلف الارتفاعات والأحمال.', en: 'Passenger elevators are the beating heart of residential and commercial buildings, smooth, safe, reliable vertical movement that carries people between floors quickly and comfortably. We offer machine-room (MR) and machine-room-less (MRL) solutions for various rises and loads.' },
        body: [
          { ar: 'مصاعد الركاب اختيار أساسي لأي مبنى متعدد الطوابق، من العمارات السكنية إلى المكاتب والمراكز التجارية. المعيار الأهم هو التوازن بين السرعة والحمولة وعدد الرحلات وراحة الركوب، وكلها تُحدّد بدراسة فنية دقيقة لحركة المبنى.', en: 'Passenger elevators are essential for any multi-storey building, from residential blocks to offices and commercial centers. The key is balancing speed, load, trip frequency and ride comfort, all defined by a careful traffic study of the building.' },
          { ar: 'في سيلترا جلايد نختار النظام الأنسب (MRL للمباني الحديثة الموفّرة للمساحة، أو MR للأحمال والسرعات العالية)، وننفّذ التركيب بإشراف هندسي واختبار وتسليم موثّق، مع عقود صيانة تضمن جاهزية دائمة واستجابة سريعة.', en: 'At Syltra Glide we pick the right system (MRL for space-saving modern buildings, or MR for higher loads and speeds), install under engineering supervision with documented testing and handover, and back it with maintenance contracts for constant readiness and fast response.' },
        ],
        points: [
          { ar: 'حلول MRL وMR حسب المبنى', en: 'MRL and MR solutions to suit the building' },
          { ar: 'سرعات وحمولات متعددة', en: 'Multiple speeds and capacities' },
          { ar: 'كابينة بتشطيبات تناسب هوية المكان', en: 'Cabin finishes that match the space' },
          { ar: 'أنظمة أمان ومعايير معتمدة', en: 'Certified safety systems and standards' },
          { ar: 'عقود صيانة واستجابة طوارئ', en: 'Maintenance contracts and emergency response' },
        ],
        useCases: [
          { ar: 'العمارات السكنية', en: 'Residential buildings' },
          { ar: 'المكاتب والمباني الإدارية', en: 'Offices and administrative buildings' },
          { ar: 'المراكز التجارية', en: 'Commercial centers' },
          { ar: 'الفنادق والمنشآت العامة', en: 'Hotels and public facilities' },
        ],
      },
      {
        title: { ar: 'الفلل والمنازل', en: "" }, en: "Home & villa",
        img: "/divisions/glide-systems/villa.jpg", slug: "villa",
        lead: { ar: 'مصاعد الفلل والمنازل حلّ أنيق وعملي يضيف راحة وقيمة لمنزلك، تصميم مدمج يناسب المساحات المحدودة دون الحاجة إلى بئر كبير أو غرفة ماكينة، مع خيارات تشطيب راقية.', en: 'Home and villa lifts are an elegant, practical solution that adds comfort and value to your home, a compact design for limited spaces without a large shaft or machine room, with premium finish options.' },
        body: [
          { ar: 'مع تزايد الفلل متعددة الأدوار، أصبح المصعد المنزلي ضرورة لكبار السن وذوي الاحتياجات ولراحة العائلة اليومية. الحلول الحديثة مدمجة وهادئة وآمنة وتُركّب في المنازل القائمة أو أثناء البناء.', en: 'As multi-storey villas grow more common, a home lift has become essential for the elderly, people with limited mobility and everyday family comfort. Modern solutions are compact, quiet, safe, and fit existing homes or new builds.' },
          { ar: 'ندرس المساحة المتاحة ونرشّح النظام الأنسب (هيدروليك أو بمحرّك) والتشطيب الذي يناسب ديكور منزلك، وننفّذ بتركيب نظيف واختبار وتسليم، مع صيانة تحافظ على الأمان والأداء.', en: 'We study the available space and recommend the best system (hydraulic or traction) and a finish that matches your interior, then install cleanly with testing and handover, plus maintenance that preserves safety and performance.' },
        ],
        points: [
          { ar: 'تصميم مدمج للمساحات المحدودة', en: 'Compact design for limited spaces' },
          { ar: 'تركيب في منزل قائم أو أثناء البناء', en: 'Fits existing homes or new builds' },
          { ar: 'تشطيبات فاخرة تناسب الديكور', en: 'Luxury finishes that match your interior' },
          { ar: 'تشغيل هادئ وآمن', en: 'Quiet, safe operation' },
          { ar: 'صيانة دورية وقطع معتمدة', en: 'Routine maintenance and certified parts' },
        ],
        useCases: [
          { ar: 'الفلل متعددة الأدوار', en: 'Multi-storey villas' },
          { ar: 'المنازل الخاصة', en: 'Private homes' },
          { ar: 'كبار السن وذوو الاحتياجات', en: 'Elderly and limited-mobility users' },
          { ar: 'الاستراحات والمزارع', en: 'Resthouses and farms' },
        ],
      },
      {
        title: { ar: 'المصاعد البانورامية', en: "" }, en: "Panoramic",
        img: "/divisions/glide-systems/panoramic.jpg", slug: "panoramic",
        lead: { ar: 'المصاعد البانورامية والزجاجية تحوّل الحركة الرأسية إلى تجربة بصرية، كابينة شفّافة تطلّ على المكان وتصبح جزءًا من هوية المبنى وواجهته المعمارية، مثالية للفنادق والمولات والمشاريع المميّزة.', en: "Panoramic and glass elevators turn vertical movement into a visual experience, a transparent cabin that overlooks the space and becomes part of the building's identity and architectural facade, ideal for hotels, malls and landmark projects." },
        body: [
          { ar: 'المصعد البانورامي ليس وسيلة نقل فقط، بل عنصر تصميم يضيف فخامة وإحساسًا بالاتساع، ويمنح الركاب إطلالة أثناء الحركة. يُنفّذ عادة في الأتريوم والواجهات الزجاجية والمساحات المفتوحة.', en: "A panoramic elevator is not just transport but a design element that adds luxury and a sense of openness, giving riders a view as they move. It's typically executed in atriums, glass facades and open spaces." },
          { ar: 'ننسّق التصميم مع المعماري لاختيار شكل الكابينة والزجاج والإضاءة والمواد بما يناسب هوية المشروع، وننفّذ بمعايير أمان صارمة واختبار وتسليم موثّق وصيانة مستمرة.', en: "We coordinate the design with the architect to choose the cabin shape, glass, lighting and materials to fit the project's identity, and execute to strict safety standards with documented testing, handover and ongoing maintenance." },
        ],
        points: [
          { ar: 'كابينة زجاجية بتصاميم متعددة', en: 'Glass cabins in multiple designs' },
          { ar: 'تنسيق مع التصميم المعماري', en: 'Coordinated with the architecture' },
          { ar: 'إضاءة ومواد فاخرة', en: 'Premium lighting and materials' },
          { ar: 'معايير أمان عالية', en: 'High safety standards' },
          { ar: 'صيانة تحافظ على المظهر والأداء', en: 'Maintenance that preserves look and performance' },
        ],
        useCases: [
          { ar: 'الفنادق والمنتجعات', en: 'Hotels and resorts' },
          { ar: 'المولات والمراكز التجارية', en: 'Malls and commercial centers' },
          { ar: 'المباني ذات الأتريوم', en: 'Buildings with atriums' },
          { ar: 'المشاريع المعمارية المميّزة', en: 'Landmark architectural projects' },
        ],
      },
      {
        title: { ar: 'مصاعد ذوي الإعاقة', en: "" }, en: "Accessibility",
        img: "/divisions/glide-systems/accessibility.jpg", slug: "accessibility",
        lead: { ar: 'حلول الحركة الرأسية لذوي الإعاقة وكبار السن، منصّات رفع ومصاعد مصمّمة لتوفير وصول آمن وكريم للجميع، وفق معايير إتاحة الوصول (accessibility) المعتمدة.', en: 'Vertical-mobility solutions for people with disabilities and the elderly, platform lifts and elevators designed to provide safe, dignified access for everyone, per approved accessibility standards.' },
        body: [
          { ar: 'إتاحة الوصول للجميع مسؤولية والتزام في المباني الحديثة والمرافق العامة. توفّر منصّات الرفع ومصاعد ذوي الإعاقة حلاً عمليًا للفروقات في المستويات والسلالم، بأمان وسهولة استخدام.', en: 'Accessibility for all is a responsibility and a requirement in modern buildings and public facilities. Platform lifts and accessibility elevators offer a practical solution for level changes and stairs, safely and simply.' },
          { ar: 'نصمّم الحل المناسب للموقع (منصّة رفع عمودية أو مائلة على الدرج أو مصعد) مع أزرار وارتفاعات ومواصفات تراعي الاستخدام، وننفّذ ونختبر ونصون وفق المعايير.', en: 'We design the right solution for the site (vertical or inclined stair platform, or an elevator) with buttons, heights and specs that consider real use, then install, test and maintain to standard.' },
        ],
        points: [
          { ar: 'منصّات رفع عمودية ومائلة', en: 'Vertical and inclined platform lifts' },
          { ar: 'مصاعد متوافقة مع معايير الإتاحة', en: 'Accessibility-compliant elevators' },
          { ar: 'أزرار وارتفاعات سهلة الاستخدام', en: 'Easy-to-use buttons and heights' },
          { ar: 'أمان وموثوقية عالية', en: 'High safety and reliability' },
          { ar: 'صيانة ودعم مستمر', en: 'Maintenance and ongoing support' },
        ],
        useCases: [
          { ar: 'المرافق الحكومية والعامة', en: 'Government and public facilities' },
          { ar: 'المساجد والمراكز', en: 'Mosques and centers' },
          { ar: 'المدارس والجامعات', en: 'Schools and universities' },
          { ar: 'المنازل لكبار السن', en: 'Homes for the elderly' },
        ],
      },
      {
        title: { ar: 'مصاعد المستشفيات', en: "" }, en: "Hospital",
        img: "/divisions/glide-systems/hospital.jpg", slug: "hospital",
        lead: { ar: 'مصاعد المستشفيات والأسرّة مصمّمة لنقل المرضى والأسرّة والمعدات الطبية بثبات وسلاسة، كابينة واسعة وعميقة وحركة ناعمة تراعي حالة المريض، بمعايير صحية وأمان صارمة.', en: "Hospital and bed elevators are built to move patients, beds and medical equipment steadily and smoothly, a wide, deep cabin and gentle motion that respect the patient's condition, to strict health and safety standards." },
        body: [
          { ar: 'في المنشآت الصحية، المصعد جزء من سلسلة الرعاية، أي تأخير أو اهتزاز قد يؤثّر على المريض. لذلك تتطلّب مصاعد المستشفيات أبعادًا خاصة وحركة دقيقة وموثوقية عالية وأنظمة أولوية للطوارئ.', en: 'In healthcare facilities the elevator is part of the care chain, any delay or jolt can affect the patient. Hospital elevators therefore need special dimensions, precise motion, high reliability and emergency-priority systems.' },
          { ar: 'نوفّر مصاعد أسرّة بكابينة واسعة وحركة ناعمة وأنظمة تحكّم بالأولوية والطوارئ، مع مواد سهلة التعقيم، وننفّذها بمعايير معتمدة ونصونها بعقود تضمن جاهزية دائمة.', en: 'We provide bed elevators with a wide cabin, gentle motion and priority/emergency control systems, with easy-to-sanitize materials, executed to approved standards and maintained under contracts ensuring constant readiness.' },
        ],
        points: [
          { ar: 'كابينة واسعة وعميقة للأسرّة', en: 'Wide, deep cabins for beds' },
          { ar: 'حركة ناعمة وتوقّف دقيق', en: 'Gentle motion and accurate leveling' },
          { ar: 'أنظمة أولوية وطوارئ', en: 'Priority and emergency systems' },
          { ar: 'مواد سهلة التعقيم', en: 'Easy-to-sanitize materials' },
          { ar: 'صيانة تضمن جاهزية دائمة', en: 'Maintenance ensuring constant readiness' },
        ],
        useCases: [
          { ar: 'المستشفيات والمراكز الطبية', en: 'Hospitals and medical centers' },
          { ar: 'المستوصفات والعيادات الكبيرة', en: 'Polyclinics and large clinics' },
          { ar: 'دور الرعاية', en: 'Care homes' },
          { ar: 'مراكز التأهيل', en: 'Rehabilitation centers' },
        ],
      },
      {
        title: { ar: 'مصاعد البضائع', en: "" }, en: "Freight",
        img: "/divisions/glide-systems/freight.jpg", slug: "freight",
        lead: { ar: 'مصاعد البضائع مصمّمة لنقل الأحمال الثقيلة بأمان وكفاءة بين الطوابق، هيكل متين وأرضية تتحمّل وأبواب واسعة، تناسب المستودعات والمصانع والمراكز التجارية.', en: 'Freight elevators are built to move heavy loads safely and efficiently between floors, a sturdy structure, load-bearing floor and wide doors, suited to warehouses, factories and commercial centers.' },
        body: [
          { ar: 'نقل البضائع بين الطوابق يدويًا مكلف وبطيء وخطر. يوفّر مصعد البضائع حلاً موثوقًا يرفع الإنتاجية ويحمي العاملين، بحمولات تبدأ من مئات الكيلوغرامات وتصل إلى عدة أطنان حسب الحاجة.', en: 'Moving goods between floors manually is costly, slow and risky. A freight elevator provides a reliable solution that raises productivity and protects workers, with capacities from hundreds of kilograms up to several tonnes as needed.' },
          { ar: 'نحدّد الحمولة والأبعاد ونوع الاستخدام، ونختار النظام المناسب (هيدروليك أو بمحرّك) بأرضية وأبواب تتحمّل، وننفّذ بمعايير سلامة ونصون بعقود دورية.', en: 'We define the load, dimensions and usage, choose the right system (hydraulic or traction) with a load-bearing floor and doors, execute to safety standards and maintain under periodic contracts.' },
        ],
        points: [
          { ar: 'حمولات من مئات الكيلوغرامات إلى أطنان', en: 'Capacities from hundreds of kg to tonnes' },
          { ar: 'هيكل متين وأرضية تتحمّل', en: 'Sturdy structure and load-bearing floor' },
          { ar: 'أبواب واسعة لسهولة التحميل', en: 'Wide doors for easy loading' },
          { ar: 'أنظمة سلامة للحمل الثقيل', en: 'Safety systems for heavy loads' },
          { ar: 'صيانة دورية تقلّل التوقّف', en: 'Periodic maintenance that reduces downtime' },
        ],
        useCases: [
          { ar: 'المستودعات ومراكز التوزيع', en: 'Warehouses and distribution centers' },
          { ar: 'المصانع وخطوط الإنتاج', en: 'Factories and production lines' },
          { ar: 'المولات والمطاعم الكبيرة', en: 'Malls and large restaurants' },
          { ar: 'المرائب متعددة الأدوار', en: 'Multi-storey garages' },
        ],
      },
      {
        title: { ar: 'مصاعد الطعام', en: "" }, en: "Food lifts",
        img: "/divisions/glide-systems/food.jpg", slug: "food",
        lead: { ar: 'مصاعد الطعام (الدمبوايتر) حلّ عملي لنقل الأطباق والمستلزمات بين طوابق المطاعم والفنادق والمنازل، سريع ونظيف وصامت، يوفّر الجهد ويرفع كفاءة الخدمة.', en: 'Food lifts (dumbwaiters) are a practical solution for moving dishes and supplies between floors in restaurants, hotels and homes, fast, clean and quiet, saving effort and improving service efficiency.' },
        body: [
          { ar: 'في المطاعم والفنادق متعددة الأدوار، نقل الطعام يدويًا يبطئ الخدمة ويرهق العاملين. يوفّر مصعد الطعام مسارًا مخصّصًا وسريعًا وصحّيًا بين المطبخ وصالات الخدمة.', en: 'In multi-storey restaurants and hotels, carrying food by hand slows service and tires staff. A food lift provides a dedicated, fast and hygienic path between the kitchen and service areas.' },
          { ar: 'نصمّم المصعد بالحجم والحمولة المناسبة، بمواد سهلة التنظيف ومطابقة لمعايير الصحة، وننفّذه بتركيب نظيف ونصونه ليعمل بموثوقية يومية.', en: 'We size the lift and load appropriately, with easy-to-clean, health-compliant materials, install it cleanly and maintain it to run reliably every day.' },
        ],
        points: [
          { ar: 'أحجام وحمولات متعددة', en: 'Multiple sizes and capacities' },
          { ar: 'مواد سهلة التنظيف ومطابقة للصحة', en: 'Easy-clean, health-compliant materials' },
          { ar: 'تشغيل سريع وصامت', en: 'Fast, quiet operation' },
          { ar: 'تركيب نظيف يوفّر المساحة', en: 'Clean, space-saving installation' },
          { ar: 'صيانة تضمن التشغيل اليومي', en: 'Maintenance ensuring daily operation' },
        ],
        useCases: [
          { ar: 'المطاعم متعددة الأدوار', en: 'Multi-storey restaurants' },
          { ar: 'الفنادق وقاعات المناسبات', en: 'Hotels and event halls' },
          { ar: 'المنازل والفلل', en: 'Homes and villas' },
          { ar: 'المستشفيات والمختبرات', en: 'Hospitals and labs' },
        ],
      },
      {
        title: { ar: 'مصاعد المولات والمباني العامة', en: "" }, en: "Malls & public",
        img: "/divisions/glide-systems/public.jpg", slug: "public",
        lead: { ar: 'مصاعد المولات والمباني العامة مصمّمة للتعامل مع كثافة الحركة وأعداد الركاب الكبيرة، سرعة وحمولة وموثوقية عالية مع تجربة ركوب مريحة وآمنة تناسب المنشآت الحيوية.', en: 'Mall and public-building elevators are designed to handle high traffic and large passenger numbers, high speed, capacity and reliability with a comfortable, safe ride suited to busy facilities.' },
        body: [
          { ar: 'في المولات والمطارات والمرافق العامة، حركة الركاب مكثّفة ومستمرة، ما يتطلّب مصاعد بحمولة وسرعة عالية ونظام إدارة حركة ذكي يقلّل الانتظار ويوزّع الأحمال.', en: 'In malls, airports and public facilities, passenger traffic is intense and continuous, requiring high-capacity, high-speed elevators and a smart traffic-management system that reduces waiting and distributes loads.' },
          { ar: 'ندرس حركة المبنى ونحدّد عدد المصاعد وسعتها وسرعتها ونظام التوزيع الأمثل، وننفّذ بمعايير أمان صارمة، ونوفّر عقود صيانة تضمن جاهزية دائمة في المنشآت التي لا تتوقّف.', en: "We study the building's traffic and define the number, capacity, speed and optimal dispatch system, execute to strict safety standards, and provide maintenance contracts ensuring constant readiness in facilities that never stop." },
        ],
        points: [
          { ar: 'حمولات وسرعات عالية', en: 'High capacities and speeds' },
          { ar: 'نظام إدارة حركة ذكي', en: 'Smart traffic-management system' },
          { ar: 'موثوقية عالية للحركة المكثّفة', en: 'High reliability for intense traffic' },
          { ar: 'معايير أمان صارمة', en: 'Strict safety standards' },
          { ar: 'صيانة تضمن جاهزية دائمة', en: 'Maintenance ensuring constant readiness' },
        ],
        useCases: [
          { ar: 'المولات والمراكز التجارية', en: 'Malls and shopping centers' },
          { ar: 'المطارات ومحطات النقل', en: 'Airports and transport stations' },
          { ar: 'المباني الحكومية الكبيرة', en: 'Large government buildings' },
          { ar: 'المستشفيات والجامعات', en: 'Hospitals and universities' },
        ],
      },
    ],
    systemsNote: { ar: "خيارات هندسية بغرفة ماكينة (MR) أو بدونها (MRL), يعتمد الاختيار على الارتفاع والحمولة والسرعة والبئر وعدد الرحلات.", en: "Machine-room (MR) or machine-room-less (MRL) options, selection depends on rise, load, speed, shaft and traffic." },
    statementTitle: { ar: "الكابينة جزء من هوية المكان.", en: "The cabin is part of the space's identity." },
    statementBody: { ar: "ننسّق المواد والإضاءة والأرضيات والمرايا والدرابزين لتناسب هوية المشروع، ستانلس ستيل، جرافيت ومرايا، نحاسي وذهبي.", en: "We coordinate materials, lighting, floors, mirrors and handrails to fit the project, stainless, graphite and mirror, brass and gold." },
    flowEyebrow: { ar: "مسار العمل", en: "How we work" },
    flowTitle: { ar: "مسار واحد من الدراسة حتى التشغيل.", en: "One path from study to operation." },
    flow: [
      { title: { ar: "معاينة الموقع", en: "Site survey" }, desc: { ar: "فهم الاحتياج.", en: "Understand needs." } },
      { title: { ar: "التصميم والمواصفات", en: "Design & specs" }, desc: { ar: "تحديد النظام.", en: "Define the system." } },
      { title: { ar: "التوريد والتحضير", en: "Supply & prep" }, desc: { ar: "تجهيز المعدات.", en: "Prepare equipment." } },
      { title: { ar: "التركيب والاختبار", en: "Install & test" }, desc: { ar: "تنفيذ وضبط.", en: "Execute & tune." } },
      { title: { ar: "التسليم والصيانة", en: "Handover & service" }, desc: { ar: "تشغيل ورعاية.", en: "Operate & care." } },
    ],
    ctaTitle: { ar: "ارفع تجربة المبنى مع سيلترا جلايد.", en: "Elevate the building experience with Syltra Glide." },
    ctaBody: { ar: "ابدأ بدراسة مشروعك، نحدّد النظام المناسب ونجهّز عرضًا واضحًا للتوريد والتنفيذ والصيانة.", en: "Start with a project study, we select the right system and prepare a clear proposal for supply, execution and maintenance." },
  },

  shield: {
    h1: { ar: "حماية متكاملة. أنظمة تعمل وقت الحاجة.", en: "Integrated protection. Systems that work when it matters." },
    intro: {
      ar: "الأمان لا يحتمل التأجيل. في سيلترا شيلد نحمي مبناك وناسه بأنظمة حريق ومراقبة وتحكّم دخول وكهرباء، مصمّمة لتعمل في اللحظة التي تحتاجها فيها.",
      en: "Safety can't wait. At Syltra Shield we protect your building and its people with fire, surveillance, access-control and electrical systems, built to work the moment you need them.",
    },
    heroSlides: [
      { title: { ar: "الحريق والإنذار", en: "Fire & alarm" }, caption: { ar: "كشف وإنذار ومكافحة وفق كود البناء واشتراطات الدفاع المدني.", en: "Detection, alarm and suppression per building code and civil-defense requirements." }, image: "/divisions/shield-1.jpg" },
      { title: { ar: "المراقبة والتحكّم بالدخول", en: "Surveillance & access" }, caption: { ar: "كاميرات وتحكّم دخول في منصّة مراقبة واحدة.", en: "Cameras and access control in one monitoring platform." }, image: "/divisions/shield-2.jpg" },
      { title: { ar: "الكهرباء والتيار المنخفض", en: "Electrical & low-current" }, caption: { ar: "بنية كهربائية وشبكات منظّمة وموثوقة.", en: "Organized, reliable electrical and network infrastructure." }, image: "/divisions/shield.jpg" },
    ],
    servicesEyebrow: { ar: "الخدمات", en: "Services" },
    servicesTitle: { ar: "تصميم وتوريد وتنفيذ وصيانة، تحت مظلة واحدة.", en: "Design, supply, execution and maintenance, under one roof." },
    services: [
      { title: { ar: "التصميم والدراسة الفنية", en: "Design & study" }, desc: { ar: "مخططات تلبّي الكود والاشتراطات الدفاعية.", en: "Drawings that meet code and civil-defense requirements." } },
      { title: { ar: "التوريد والتركيب", en: "Supply & installation" }, desc: { ar: "معدات معتمدة وتنفيذ ميداني منضبط.", en: "Certified equipment and disciplined field execution." } },
      { title: { ar: "الاختبار والتشغيل", en: "Testing & commissioning" }, desc: { ar: "اختبار وتشغيل وتسليم موثّق.", en: "Documented testing, commissioning and handover." } },
      { title: { ar: "الصيانة والعقود السنوية", en: "Maintenance & contracts" }, desc: { ar: "فحص دوري يحافظ على جاهزية الأنظمة.", en: "Periodic inspection that keeps systems ready." } },
      { title: { ar: "التكامل والتحكّم المركزي", en: "Integration & central control" }, desc: { ar: "ربط الأنظمة في منصّة مراقبة واحدة.", en: "Linking systems into one monitoring platform." } },
      { title: { ar: "المطابقة والاعتماد", en: "Compliance & approval" }, desc: { ar: "توثيق يلبّي متطلبات الجهات المختصة.", en: "Documentation that meets authority requirements." } },
    ],
    systemsEyebrow: { ar: "الأنظمة", en: "Systems" },
    systemsTitle: { ar: "أنظمة الأمن والسلامة والكهرباء التي نغطّيها.", en: "The security, safety and electrical systems we cover." },
    systems: [
      {
        title: { ar: 'إنذار ومكافحة الحريق', en: "" }, en: "Fire alarm & fighting",
        img: "/divisions/shield-systems/fire.jpg", slug: "fire",
        lead: { ar: 'أنظمة كشف وإنذار ومكافحة الحريق هي خط الدفاع الأول لحماية الأرواح والممتلكات، نصمّم وننفّذ وفق كود البناء السعودي واشتراطات الدفاع المدني، من الكواشف والإنذار إلى الإطفاء بالغاز والرشاشات.', en: 'Fire detection, alarm and suppression are the first line of defense for lives and property, we design and execute to the Saudi building code and Civil Defense requirements, from detectors and alarms to gas suppression and sprinklers.' },
        body: [
          { ar: 'الحريق لا يعطي إنذارًا مسبقًا، ولحظة الاستجابة تصنع الفرق. نظام الحريق المتكامل يكشف الدخان والحرارة مبكرًا، ينبّه المبنى، ويبدأ الإطفاء تلقائيًا، بما يحمي الأرواح ويقلّل الخسائر ويحقّق متطلبات الجهات المختصة.', en: 'Fire gives no warning, and the moment of response makes the difference. An integrated fire system detects smoke and heat early, alerts the building, and starts suppression automatically, protecting lives, reducing losses and meeting authority requirements.' },
          { ar: 'نصمّم النظام وفق طبيعة المبنى ومخاطره، ونوّرد معدات معتمدة، وننفّذ بإشراف هندسي، ونحصل على مطابقة الدفاع المدني، ونصون بعقود دورية تُبقي النظام جاهزًا وقت الحاجة.', en: "We design the system to the building's nature and risks, supply certified equipment, execute under engineering supervision, obtain Civil Defense compliance, and maintain under periodic contracts that keep the system ready when needed." },
        ],
        points: [
          { ar: 'كواشف دخان وحرارة وإنذار', en: 'Smoke/heat detectors and alarm' },
          { ar: 'إطفاء بالغاز (FM200) والرشاشات', en: 'Gas suppression (FM200) and sprinklers' },
          { ar: 'لوحات تحكّم وإنذار مركزية', en: 'Central control and alarm panels' },
          { ar: 'مطابقة الدفاع المدني والتوثيق', en: 'Civil Defense compliance and documentation' },
          { ar: 'صيانة دورية وفحص معتمد', en: 'Periodic maintenance and certified inspection' },
        ],
        useCases: [
          { ar: 'المباني السكنية والتجارية', en: 'Residential and commercial buildings' },
          { ar: 'المصانع والمستودعات', en: 'Factories and warehouses' },
          { ar: 'الفنادق والمستشفيات', en: 'Hotels and hospitals' },
          { ar: 'المرافق الحكومية', en: 'Government facilities' },
        ],
      },
      {
        title: { ar: 'المراقبة بالكاميرات', en: "" }, en: "CCTV",
        img: "/divisions/shield-systems/cctv.jpg", slug: "cctv",
        lead: { ar: 'أنظمة المراقبة بالكاميرات توفّر عيونًا لا تنام على منشأتك، مراقبة مباشرة وتسجيل عالي الدقة وتنبيهات فورية عبر الجوال على مدار 24 ساعة، بكاميرات وشبكات مطابقة لاشتراطات وزارة الداخلية.', en: 'CCTV systems give your facility eyes that never sleep, live monitoring, high-resolution recording and instant mobile alerts around the clock, with cameras and networks compliant with Ministry of Interior requirements.' },
        body: [
          { ar: 'المراقبة الفعّالة ليست مجرد كاميرات، بل نظام متكامل: تغطية مدروسة بلا نقاط عمياء، تخزين آمن، ووصول سريع للّقطات عند الحاجة. الكاميرات الحديثة تدعم التعرّف والتنبيه الذكي عند الحركة أو التسلّل.', en: 'Effective surveillance is not just cameras but an integrated system: engineered coverage with no blind spots, secure storage, and quick footage access when needed. Modern cameras support recognition and smart alerts on motion or intrusion.' },
          { ar: 'نصمّم مخطّط التغطية ونختار الكاميرات المناسبة (داخلية/خارجية/ليلية) ونظام التخزين، ونربطها بالجوال، ونطابقها مع اشتراطات وزارة الداخلية، ونصونها لضمان تشغيل دائم.', en: 'We design the coverage plan, select the right cameras (indoor/outdoor/night) and storage, connect them to mobile, ensure Ministry of Interior compliance, and maintain them for continuous operation.' },
        ],
        points: [
          { ar: 'كاميرات عالية الدقة داخلية وخارجية', en: 'High-resolution indoor/outdoor cameras' },
          { ar: 'تسجيل وتخزين آمن', en: 'Secure recording and storage' },
          { ar: 'مراقبة ومشاهدة عبر الجوال 24/7', en: '24/7 mobile monitoring' },
          { ar: 'مطابقة اشتراطات وزارة الداخلية', en: 'Ministry of Interior compliance' },
          { ar: 'تنبيهات ذكية عند الحركة', en: 'Smart motion alerts' },
        ],
        useCases: [
          { ar: 'المنشآت التجارية والمحلات', en: 'Commercial facilities and shops' },
          { ar: 'المستودعات والمصانع', en: 'Warehouses and factories' },
          { ar: 'المجمّعات السكنية', en: 'Residential compounds' },
          { ar: 'المكاتب والمرافق الحكومية', en: 'Offices and government facilities' },
        ],
      },
      {
        title: { ar: 'التحكّم بالدخول', en: "" }, en: "Access control",
        img: "/divisions/shield-systems/access.jpg", slug: "access",
        lead: { ar: 'أنظمة التحكّم بالدخول تنظّم من يدخل وأين ومتى، أبواب إلكترونية وبطاقات وبصمة وتطبيق، مع سجل دخول كامل وصلاحيات دقيقة تحمي المناطق الحسّاسة.', en: 'Access control systems govern who enters, where and when, electronic doors, cards, fingerprint and app, with a full entry log and precise permissions that protect sensitive areas.' },
        body: [
          { ar: 'في المنشآت الحديثة، لم يعد المفتاح كافيًا. نظام التحكّم بالدخول يمنح كل شخص صلاحية محدّدة، يسجّل كل حركة، ويُلغى فورًا عند الحاجة، ما يرفع الأمان ويسهّل الإدارة ويوفّر تقارير دقيقة.', en: 'In modern facilities a key is no longer enough. Access control gives each person a defined permission, logs every movement, and can be revoked instantly, raising security, easing management and providing accurate reports.' },
          { ar: 'نصمّم النظام حسب المناطق ومستويات الصلاحية، ونختار وسائل التعريف (بطاقة/بصمة/وجه/تطبيق)، وندمجه مع المراقبة والحريق، وننفّذ ونصون بمعايير معتمدة.', en: 'We design the system by zones and permission levels, choose identification methods (card/fingerprint/face/app), integrate it with surveillance and fire, then execute and maintain to certified standards.' },
        ],
        points: [
          { ar: 'أبواب إلكترونية وبوابات', en: 'Electronic doors and gates' },
          { ar: 'بطاقة وبصمة ووجه وتطبيق', en: 'Card, fingerprint, face and app' },
          { ar: 'صلاحيات دقيقة وسجل دخول', en: 'Precise permissions and entry log' },
          { ar: 'تكامل مع المراقبة والحريق', en: 'Integration with surveillance and fire' },
          { ar: 'إدارة مركزية وتقارير', en: 'Central management and reports' },
        ],
        useCases: [
          { ar: 'المكاتب والشركات', en: 'Offices and companies' },
          { ar: 'المصانع والمناطق الحسّاسة', en: 'Factories and sensitive areas' },
          { ar: 'المجمّعات السكنية', en: 'Residential compounds' },
          { ar: 'المرافق الحكومية والبنوك', en: 'Government facilities and banks' },
        ],
      },
      {
        title: { ar: 'الإنذار ضد السرقة', en: "" }, en: "Intrusion alarm",
        img: "/divisions/shield-systems/intrusion.jpg", slug: "intrusion",
        lead: { ar: 'أنظمة الإنذار ضد السرقة تكشف أي تسلّل أو اقتحام وتنبّهك فورًا، حساسات حركة وأبواب ونوافذ وصفّارات، مع ربط بالجوال ومركز مراقبة لحماية منشأتك على مدار الساعة.', en: 'Intrusion alarm systems detect any break-in and alert you instantly, motion, door and window sensors and sirens, with mobile and monitoring-center connectivity to protect your facility around the clock.' },
        body: [
          { ar: 'الوقاية خير من الخسارة. نظام الإنذار ضد السرقة يشكّل طبقة حماية استباقية: يكشف محاولات الاقتحام مبكرًا، يطلق الإنذار، ويرسل تنبيهًا فوريًا، ما يردع المتسلّل ويقلّل المخاطر.', en: 'Prevention beats loss. An intrusion alarm forms a proactive protection layer: it detects break-in attempts early, sounds the alarm, and sends an instant alert, deterring intruders and reducing risk.' },
          { ar: 'نحدّد نقاط الضعف والمداخل، ونوزّع الحساسات المناسبة، ونربط النظام بالجوال ومركز المراقبة، وندمجه مع المراقبة والدخول، ونصونه لضمان جاهزية دائمة.', en: 'We identify weak points and entries, place the right sensors, connect the system to mobile and a monitoring center, integrate it with surveillance and access, and maintain it for constant readiness.' },
        ],
        points: [
          { ar: 'حساسات حركة وأبواب ونوافذ', en: 'Motion, door and window sensors' },
          { ar: 'صفّارات وإنذار صوتي', en: 'Sirens and audible alarm' },
          { ar: 'تنبيه فوري عبر الجوال', en: 'Instant mobile alerts' },
          { ar: 'ربط بمركز مراقبة', en: 'Monitoring-center connectivity' },
          { ar: 'تكامل مع المراقبة والدخول', en: 'Integration with surveillance and access' },
        ],
        useCases: [
          { ar: 'المنازل والفلل', en: 'Homes and villas' },
          { ar: 'المحلات والمستودعات', en: 'Shops and warehouses' },
          { ar: 'المكاتب والشركات', en: 'Offices and companies' },
          { ar: 'المواقع والمشاريع تحت الإنشاء', en: 'Sites and projects under construction' },
        ],
      },
      {
        title: { ar: 'التيار المنخفض والشبكات', en: "" }, en: "Low current & networks",
        img: "/divisions/shield-systems/lowcurrent.jpg", slug: "lowcurrent",
        lead: { ar: 'أنظمة التيار المنخفض والشبكات هي العمود الفقري الرقمي للمبنى، كابلات منظّمة وشبكات موثوقة تربط المراقبة والدخول والصوت والبيانات والإنترنت في بنية تحتية واحدة نظيفة.', en: "Low-current and network systems are the building's digital backbone, organized cabling and reliable networks linking surveillance, access, audio, data and internet in one clean infrastructure." },
        body: [
          { ar: 'خلف كل نظام ذكي بنية تحتية من التيار المنخفض. التنظيم الجيد للكابلات والشبكات يعني موثوقية أعلى وصيانة أسهل وقابلية للتوسّع، بينما الفوضى تعني أعطالًا وتكاليف مستقبلية.', en: 'Behind every smart system is a low-current infrastructure. Well-organized cabling and networks mean higher reliability, easier maintenance and scalability, while a mess means faults and future costs.' },
          { ar: 'نصمّم البنية وفق المعايير (هيكلة الكابلات، غرف الاتصالات، الشبكات)، وننفّذها بترتيب واحترافية، ونوثّقها، ونصونها، لتكون أساسًا موثوقًا لكل الأنظمة.', en: 'We design the infrastructure to standard (structured cabling, comms rooms, networks), execute it neatly and professionally, document it, and maintain it, a reliable foundation for every system.' },
        ],
        points: [
          { ar: 'هيكلة كابلات منظّمة', en: 'Structured, organized cabling' },
          { ar: 'شبكات سلكية ولاسلكية موثوقة', en: 'Reliable wired and wireless networks' },
          { ar: 'غرف اتصالات وخزائن منظّمة', en: 'Comms rooms and tidy racks' },
          { ar: 'توثيق كامل للبنية', en: 'Full infrastructure documentation' },
          { ar: 'قابلية للتوسّع مستقبلًا', en: 'Scalable for the future' },
        ],
        useCases: [
          { ar: 'المباني التجارية والإدارية', en: 'Commercial and administrative buildings' },
          { ar: 'المصانع والمستودعات', en: 'Factories and warehouses' },
          { ar: 'الفنادق والمجمّعات', en: 'Hotels and compounds' },
          { ar: 'المرافق الحكومية', en: 'Government facilities' },
        ],
      },
      {
        title: { ar: 'البنية الكهربائية', en: "" }, en: "Electrical & MEP",
        img: "/divisions/shield-systems/electrical.jpg", slug: "electrical",
        lead: { ar: 'البنية الكهربائية الموثوقة أساس تشغيل أي منشأة، لوحات وتمديدات وأنظمة توزيع منفّذة بمعايير سلامة، تضمن طاقة مستقرّة وآمنة لكل الأنظمة.', en: 'Reliable electrical infrastructure is the foundation for running any facility, panels, wiring and distribution systems executed to safety standards, ensuring stable, safe power for every system.' },
        body: [
          { ar: 'الكهرباء ليست مجرد تمديدات، بل نظام سلامة. البنية المصمّمة جيدًا توزّع الأحمال بأمان، تحمي من الأعطال والحرائق، وتوفّر استقرارًا يحمي أجهزتك وأنظمتك الحسّاسة.', en: 'Electrical work is not just wiring but a safety system. A well-designed infrastructure distributes loads safely, protects against faults and fires, and provides stability that safeguards your equipment and sensitive systems.' },
          { ar: 'نصمّم ونحسب الأحمال، ونوّرد لوحات ومكوّنات معتمدة، وننفّذ التمديدات وأنظمة التوزيع والحماية بمعايير السلامة، ونختبر ونسلّم ونصون.', en: 'We design and calculate loads, supply certified panels and components, execute wiring, distribution and protection to safety standards, then test, hand over and maintain.' },
        ],
        points: [
          { ar: 'لوحات كهربائية وتوزيع', en: 'Electrical panels and distribution' },
          { ar: 'حساب أحمال وحماية', en: 'Load calculation and protection' },
          { ar: 'تمديدات بمعايير سلامة', en: 'Wiring to safety standards' },
          { ar: 'أنظمة أرضي وحماية من الصواعق', en: 'Earthing and lightning protection' },
          { ar: 'اختبار وتسليم وصيانة', en: 'Testing, handover and maintenance' },
        ],
        useCases: [
          { ar: 'المباني التجارية والصناعية', en: 'Commercial and industrial buildings' },
          { ar: 'المشاريع السكنية', en: 'Residential projects' },
          { ar: 'المصانع والورش', en: 'Factories and workshops' },
          { ar: 'المرافق الحكومية', en: 'Government facilities' },
        ],
      },
      {
        title: { ar: 'النداء الصوتي والإخلاء', en: "" }, en: "PA & evacuation",
        img: "/divisions/shield-systems/pa.jpg", slug: "pa",
        lead: { ar: 'أنظمة النداء الصوتي والإخلاء توصّل الصوت والتعليمات بوضوح في كل أنحاء المبنى، بثّ عام وإعلانات وتوجيه إخلاء آمن وقت الطوارئ، بجودة صوت عالية وتغطية شاملة.', en: 'Public-address and evacuation systems deliver clear sound and instructions throughout the building, general broadcast, announcements and safe evacuation guidance in emergencies, with high audio quality and full coverage.' },
        body: [
          { ar: 'وقت الطوارئ، التواصل الواضح ينقذ الأرواح. نظام النداء والإخلاء يبثّ تعليمات مسموعة ومفهومة في كل منطقة، ويوجّه الإخلاء بهدوء ونظام، وهو متطلّب أساسي في المنشآت الكبيرة والعامة.', en: 'In an emergency, clear communication saves lives. A PA/evacuation system broadcasts audible, understandable instructions in every area and guides evacuation calmly and orderly, an essential requirement in large and public facilities.' },
          { ar: 'نصمّم مناطق الصوت والتغطية، ونختار السمّاعات والمكبّرات المناسبة، وندمج النظام مع الحريق للإخلاء التلقائي، وننفّذ ونختبر ونصون.', en: 'We design sound zones and coverage, select the right speakers and amplifiers, integrate the system with fire for automatic evacuation, then execute, test and maintain.' },
        ],
        points: [
          { ar: 'بثّ عام وإعلانات', en: 'General broadcast and announcements' },
          { ar: 'توجيه إخلاء وقت الطوارئ', en: 'Evacuation guidance in emergencies' },
          { ar: 'تكامل مع نظام الحريق', en: 'Integration with the fire system' },
          { ar: 'تغطية صوتية شاملة', en: 'Full audio coverage' },
          { ar: 'جودة صوت عالية وموثوقية', en: 'High audio quality and reliability' },
        ],
        useCases: [
          { ar: 'المولات والمراكز التجارية', en: 'Malls and commercial centers' },
          { ar: 'المطارات ومحطات النقل', en: 'Airports and transport stations' },
          { ar: 'المستشفيات والجامعات', en: 'Hospitals and universities' },
          { ar: 'المصانع والمنشآت الكبيرة', en: 'Factories and large facilities' },
        ],
      },
      {
        title: { ar: 'كاميرات المراقبة بالطاقة الشمسية', en: "" }, en: "Solar-powered CCTV",
        slug: "solar",
        lead: { ar: 'كاميرات المراقبة بالطاقة الشمسية حلّ مثالي للمواقع البعيدة أو بدون بنية كهربائية، تعمل باستقلالية تام بالطاقة الشمسية مع بطارية تخزين واتصال لاسلكي، ومراقبة عبر الجوال على مدار الساعة.', en: 'Solar-powered surveillance cameras are ideal for remote sites or locations without electrical infrastructure, fully autonomous on solar power with battery storage and wireless connectivity, plus 24/7 mobile monitoring.' },
        body: [
          { ar: 'ليست كل المواقع مزوّدة بالكهرباء والكابلات، المزارع والمشاريع تحت الإنشاء والمواقع النائية تحتاج حماية أيضًا. الكاميرا الشمسية تعمل باستقلالية دون بنية تحتية، ما يوفّر التمديدات ويسرّع التركيب.', en: 'Not every site has power and cabling, farms, projects under construction and remote sites need protection too. A solar camera runs autonomously without infrastructure, saving wiring and speeding installation.' },
          { ar: 'نختار الكاميرا واللوح الشمسي والبطارية بما يناسب ساعات التشغيل، ونؤمّن الاتصال اللاسلكي والتخزين، ونربطها بالجوال، ونصونها لضمان تشغيل دائم في أصعب المواقع.', en: 'We size the camera, solar panel and battery to the required operating hours, secure wireless connectivity and storage, connect to mobile, and maintain them for continuous operation in the toughest sites.' },
        ],
        points: [
          { ar: 'تشغيل مستقل بالطاقة الشمسية', en: 'Autonomous solar operation' },
          { ar: 'بطارية تخزين لتشغيل ليلي', en: 'Battery storage for night operation' },
          { ar: 'اتصال لاسلكي (4G) ومراقبة بالجوال', en: 'Wireless (4G) connectivity and mobile monitoring' },
          { ar: 'تركيب سريع بلا تمديدات', en: 'Fast installation without wiring' },
          { ar: 'مناسبة للمواقع النائية', en: 'Suited to remote sites' },
        ],
        useCases: [
          { ar: 'المزارع والاستراحات', en: 'Farms and resthouses' },
          { ar: 'المشاريع تحت الإنشاء', en: 'Projects under construction' },
          { ar: 'المواقع النائية والطرق', en: 'Remote sites and roads' },
          { ar: 'مواقف ومساحات خارجية', en: 'Parking and outdoor areas' },
        ],
      },
    ],
    systemsNote: { ar: "تصميم وتنفيذ وفق كود البناء السعودي واشتراطات الدفاع المدني، مع توثيق ومطابقة لكل نظام.", en: "Designed and executed per the Saudi building code and civil-defense requirements, with documentation and compliance for every system." },
    statementTitle: { ar: "السلامة لا تُختبر وقت الحريق.", en: "Safety isn't tested during the fire." },
    statementBody: { ar: "نبني الأنظمة لتعمل في اللحظة الحرجة، اختبار دوري وصيانة موثّقة تُبقيها جاهزة قبل الحاجة إليها.", en: "We build systems to work at the critical moment, periodic testing and documented maintenance keep them ready before they're needed." },
    flowEyebrow: { ar: "مسار العمل", en: "How we work" },
    flowTitle: { ar: "من التصميم حتى الجاهزية الدائمة.", en: "From design to permanent readiness." },
    flow: [
      { title: { ar: "المعاينة والدراسة", en: "Survey & study" }, desc: { ar: "تقييم المخاطر.", en: "Risk assessment." } },
      { title: { ar: "التصميم والمطابقة", en: "Design & compliance" }, desc: { ar: "مخططات معتمدة.", en: "Approved drawings." } },
      { title: { ar: "التوريد والتركيب", en: "Supply & install" }, desc: { ar: "تنفيذ ميداني.", en: "Field execution." } },
      { title: { ar: "الاختبار والتشغيل", en: "Test & commission" }, desc: { ar: "تسليم موثّق.", en: "Documented handover." } },
      { title: { ar: "الصيانة والجاهزية", en: "Maintenance" }, desc: { ar: "فحص دوري.", en: "Periodic inspection." } },
    ],
    ctaTitle: { ar: "ابدأ بتقييم موقعك.", en: "Start with a site assessment." },
    ctaBody: { ar: "نعاين المبنى ونحدّد الأنظمة المطلوبة، ونجهّز عرضًا واضحًا للتصميم والتوريد والتنفيذ والصيانة.", en: "We survey the building, define the required systems and prepare a clear proposal for design, supply, execution and maintenance." },
  },

  os: {
    h1: { ar: "برمجيات تُبنى للتشغيل الحقيقي.", en: "Software built for real operation." },
    intro: {
      ar: "البرمجيات الجيدة تختفي خلف عمل يسير بسلاسة. في سيلترا او-إس نبني لك ما تحتاجه فعلًا، منتج جاهز أو نظام على مقاسك أو ذكاء اصطناعي، ونبقى معك بعد الإطلاق.",
      en: "Good software disappears behind a business that just runs. At Syltra OS we build what you actually need, a ready product, a tailored system, or AI, and stay with you after launch.",
    },
    heroSlides: [
      { title: { ar: "منتجات SaaS جاهزة", en: "Ready SaaS products" }, caption: { ar: "أنظمة تشغيل تبدأ بها سريعًا باشتراك، مثل سيلترا ERP.", en: "Operating systems you start with fast on a subscription, like Syltra ERP." }, image: "/divisions/os.jpg" },
      { title: { ar: "أنظمة وتطبيقات مخصّصة", en: "Custom systems & apps" }, caption: { ar: "برمجيات وتطبيقات تُبنى حول إجراءات عملك.", en: "Software and apps built around your business processes." }, image: "/divisions/os-1.jpg" },
      { title: { ar: "ذكاء اصطناعي وتحليلات", en: "AI & analytics" }, caption: { ar: "مساعدون ونماذج ولوحات تخدم قرارك اليومي.", en: "Assistants, models and dashboards that serve your daily decisions." }, image: "/divisions/os-2.jpg" },
    ],
    servicesEyebrow: { ar: "ما نقدّمه", en: "What we offer" },
    servicesTitle: { ar: "من منتج جاهز إلى نظام مبني على مقاسك.", en: "From a ready product to a system built to fit." },
    services: [
      { title: { ar: "منتجات SaaS جاهزة", en: "Ready SaaS products" }, desc: { ar: "أنظمة تشغيل تبدأ العمل بها سريعًا باشتراك.", en: "Operating systems you start using quickly on a subscription." } },
      { title: { ar: "أنظمة مخصّصة", en: "Custom systems" }, desc: { ar: "برمجيات تُبنى حول إجراءات عملك.", en: "Software built around your business processes." } },
      { title: { ar: "حلول الذكاء الاصطناعي", en: "AI solutions" }, desc: { ar: "مساعدون وتحليلات ونماذج تخدم قرارك.", en: "Assistants, analytics and models that serve your decisions." } },
      { title: { ar: "التكامل والربط", en: "Integration" }, desc: { ar: "ربط أنظمتك القائمة في تدفّق واحد.", en: "Connecting your existing systems into one flow." } },
      { title: { ar: "التطبيقات والمنصّات", en: "Apps & platforms" }, desc: { ar: "واجهات ويب وموبايل بتجربة نظيفة.", en: "Web and mobile interfaces with a clean experience." } },
      { title: { ar: "الدعم والتطوير المستمر", en: "Support & iteration" }, desc: { ar: "تحديث ورعاية بعد الإطلاق.", en: "Updates and care after launch." } },
    ],
    systemsEyebrow: { ar: "منتجاتنا", en: "Our products" },
    systemsTitle: { ar: "أنظمة نبنيها ونشغّلها.", en: "Systems we build and run." },
    systems: [
      {
        title: { ar: 'سيلترا ERP', en: "" }, en: "ERP, SaaS product",
        img: "/divisions/os-systems/erp.jpg", slug: "erp",
        lead: { ar: 'سيلترا ERP نظام تخطيط موارد مؤسسات جاهز بالاشتراك (SaaS), يجمع المحاسبة والمخزون والمبيعات والموارد البشرية في منصّة واحدة تبدأ العمل بها سريعًا دون بناء من الصفر.', en: 'Syltra ERP is a ready subscription (SaaS) enterprise resource planning system, uniting accounting, inventory, sales and HR in one platform you start using quickly without building from scratch.' },
        body: [
          { ar: 'إدارة الأعمال بجداول متفرّقة وأنظمة لا تتحدّث مع بعضها تكلّف الوقت والدقّة. نظام ERP موحّد يمنحك صورة واحدة لكل أقسامك، ويؤتمت الإجراءات، ويوفّر تقارير لحظية تساعدك على اتخاذ قرار أسرع وأدقّ.', en: "Running a business on scattered spreadsheets and systems that don't talk costs time and accuracy. A unified ERP gives you one view across departments, automates procedures, and provides real-time reports for faster, sharper decisions." },
          { ar: 'سيلترا ERP منتج جاهز يبدأ سريعًا باشتراك، ويناسب الاحتياجات القياسية مع إمكانية التخصيص. نساعدك في الإعداد والترحيل والتدريب والتكامل مع أنظمتك، مع دعم مستمر بعد الإطلاق.', en: 'Syltra ERP is a ready product that starts fast on a subscription, fitting standard needs with room to customize. We help with setup, migration, training and integration with your systems, plus ongoing post-launch support.' },
        ],
        points: [
          { ar: 'محاسبة ومخزون ومبيعات وموارد بشرية', en: 'Accounting, inventory, sales and HR' },
          { ar: 'منصّة واحدة بتقارير لحظية', en: 'One platform with real-time reports' },
          { ar: 'اشتراك يبدأ سريعًا', en: 'Subscription that starts fast' },
          { ar: 'تخصيص وتكامل مع أنظمتك', en: 'Customization and integration with your systems' },
          { ar: 'إعداد وتدريب ودعم مستمر', en: 'Setup, training and ongoing support' },
        ],
        useCases: [
          { ar: 'المؤسسات الصغيرة والمتوسطة', en: 'Small and medium enterprises' },
          { ar: 'المقاولات والمصانع', en: 'Contracting and factories' },
          { ar: 'التجارة والتجزئة', en: 'Trade and retail' },
          { ar: 'الشركات الخدمية', en: 'Service companies' },
        ],
      },
      {
        title: { ar: 'سيلترا أدابتيف', en: "" }, en: "Adaptive smart-home",
        img: "/divisions/os-systems/adaptive.jpg", slug: "adaptive",
        lead: { ar: 'سيلترا أدابتيف هو مشروعنا الداخلي ومنصّة الذكاء التي تشغّل منظومة المنزل الذكي التكيّفية، طبقة ذكاء محلية تتعلّم عادات السكّان وتتصرّف تلقائيًا مع أولوية للأمان والتحكّم اليدوي.', en: "Syltra Adaptive is our in-house project and the intelligence platform powering the adaptive smart-home ecosystem, a local intelligence layer that learns residents' habits and acts automatically, with safety and manual override first." },
        body: [
          { ar: 'أغلب أنظمة المنزل الذكي تنفّذ أوامر فقط. أدابتيف يذهب أبعد: يفهم السياق والعادات ويقترح ويؤتمت بذكاء، مع بقاء التحكّم اليدوي أولوية والسلامة قرارًا حتميًا لا يتجاوزه الذكاء الاصطناعي.', en: 'Most smart-home systems only execute commands. Adaptive goes further: it understands context and habits, recommends and automates intelligently, while manual control stays a priority and safety remains a deterministic decision the AI never overrides.' },
          { ar: 'أدابتيف مشروع بحث وتطوير خاص بسيلترا، الدماغ الذي يقوّي منظومة سيلترا لايف. يعمل محليًا دون اعتماد كامل على السحابة، ويتكامل مع الأجهزة عبر معايير مفتوحة.', en: "Adaptive is Syltra's own R&D project, the brain that strengthens the Syltra Life ecosystem. It runs locally without full cloud dependency and integrates with devices through open standards." },
        ],
        points: [
          { ar: 'طبقة ذكاء محلية تتعلّم العادات', en: 'A local intelligence layer that learns habits' },
          { ar: 'أتمتة تكيّفية مع تحكّم يدوي دائم', en: 'Adaptive automation with always-on manual control' },
          { ar: 'السلامة قرار حتمي مستقل', en: 'Safety as an independent deterministic decision' },
          { ar: 'تشغيل محلي لا يعتمد على السحابة', en: 'Local operation, not cloud-dependent' },
          { ar: 'تكامل عبر معايير مفتوحة', en: 'Integration through open standards' },
        ],
        useCases: [
          { ar: 'منظومة سيلترا لايف', en: 'The Syltra Life ecosystem' },
          { ar: 'المنازل والفلل الذكية', en: 'Smart homes and villas' },
          { ar: 'المباني التكيّفية', en: 'Adaptive buildings' },
          { ar: 'مشاريع البحث والتطوير', en: 'R&D projects' },
        ],
      },
      {
        title: { ar: 'مساعدون بالذكاء الاصطناعي', en: "" }, en: "AI assistants",
        img: "/divisions/os-systems/ai.jpg", slug: "ai",
        lead: { ar: 'مساعدو الذكاء الاصطناعي يحوّلون بياناتك إلى قرارات، مساعدون ونماذج تفهم العربية، تجيب وتلخّص وتتنبّأ وتؤتمت المهام المتكرّرة، مبنية حول احتياج عملك.', en: 'AI assistants turn your data into decisions, assistants and models that understand Arabic, answer, summarize, predict and automate repetitive tasks, built around your business needs.' },
        body: [
          { ar: 'الذكاء الاصطناعي لم يعد رفاهية. المساعد الذكي المدمج في عملك يجيب العملاء، يلخّص المستندات، يحلّل الأنماط ويتنبّأ بالطلب، ما يوفّر وقتًا ويرفع جودة القرار.', en: 'AI is no longer a luxury. A smart assistant embedded in your business answers customers, summarizes documents, analyzes patterns and forecasts demand, saving time and raising decision quality.' },
          { ar: 'نبني مساعدين ونماذج تدعم اللغة العربية ونربطها ببياناتك وأنظمتك بأمان، مع مراعاة الخصوصية وملكيتك لبياناتك، ودعم وتطوير مستمر.', en: 'We build assistants and models that support Arabic and connect them to your data and systems securely, respecting privacy and your data ownership, with ongoing support and iteration.' },
        ],
        points: [
          { ar: 'مساعدون يفهمون العربية', en: 'Assistants that understand Arabic' },
          { ar: 'تلخيص وإجابة ومعالجة مستندات', en: 'Summarizing, answering and document processing' },
          { ar: 'تحليل وتنبّؤ بالطلب', en: 'Analysis and demand forecasting' },
          { ar: 'ربط آمن ببياناتك وأنظمتك', en: 'Secure connection to your data and systems' },
          { ar: 'خصوصية وملكية بياناتك', en: 'Privacy and your data ownership' },
        ],
        useCases: [
          { ar: 'خدمة العملاء والدعم', en: 'Customer service and support' },
          { ar: 'التحليلات واتخاذ القرار', en: 'Analytics and decision-making' },
          { ar: 'أتمتة المهام المكتبية', en: 'Office task automation' },
          { ar: 'القطاعات كثيفة البيانات', en: 'Data-heavy sectors' },
        ],
      },
      {
        title: { ar: 'لوحات التحليلات', en: "" }, en: "Analytics & BI",
        img: "/divisions/os-systems/analytics.jpg", slug: "analytics",
        lead: { ar: 'لوحات التحليلات وذكاء الأعمال تحوّل أرقامك المتناثرة إلى صورة واضحة، لوحات حيّة ومؤشّرات أداء وتقارير تفاعلية تساعدك على متابعة عملك واتخاذ قرار مبني على بيانات.', en: 'Analytics and business-intelligence dashboards turn scattered numbers into a clear picture, live dashboards, KPIs and interactive reports that help you track your business and decide from data.' },
        body: [
          { ar: 'البيانات بلا تحليل مجرّد أرقام. لوحة تحليلات جيدة تجمع مصادرك في مكان واحد، تُظهر المؤشّرات المهمّة لحظيًا، وتكشف الأنماط والفرص والمخاطر قبل أن تكبر.', en: 'Data without analysis is just numbers. A good analytics dashboard unifies your sources in one place, shows key metrics in real time, and reveals patterns, opportunities and risks before they grow.' },
          { ar: 'نربط مصادر بياناتك (ERP، مبيعات، تشغيل)، ونصمّم لوحات ومؤشّرات تناسب قراراتك، ونؤتمت التحديث والتقارير، مع تصميم واضح يسهل قراءته.', en: 'We connect your data sources (ERP, sales, operations), design dashboards and KPIs that fit your decisions, automate refresh and reporting, with a clear, readable design.' },
        ],
        points: [
          { ar: 'لوحات حيّة ومؤشّرات أداء', en: 'Live dashboards and KPIs' },
          { ar: 'ربط مصادر بيانات متعددة', en: 'Connecting multiple data sources' },
          { ar: 'تقارير تفاعلية وتلقائية', en: 'Interactive and automated reports' },
          { ar: 'كشف الأنماط والفرص', en: 'Pattern and opportunity discovery' },
          { ar: 'تصميم واضح سهل القراءة', en: 'Clear, readable design' },
        ],
        useCases: [
          { ar: 'الإدارة التنفيذية', en: 'Executive management' },
          { ar: 'المبيعات والتشغيل', en: 'Sales and operations' },
          { ar: 'المالية والمخزون', en: 'Finance and inventory' },
          { ar: 'أي مؤسسة تعتمد على البيانات', en: 'Any data-driven organization' },
        ],
      },
      {
        title: { ar: 'أنظمة مخصّصة', en: "" }, en: "Custom platforms",
        img: "/divisions/os-systems/custom.jpg", slug: "custom",
        lead: { ar: 'الأنظمة المخصّصة تُبنى حول إجراءات عملك بالضبط، حين لا يكفي المنتج الجاهز، نصمّم ونطوّر نظامًا يناسب طريقة عملك ويتكامل مع أدواتك الحالية.', en: "Custom systems are built exactly around your processes, when a ready product isn't enough, we design and develop a system that fits how you work and integrates with your existing tools." },
        body: [
          { ar: 'كل عمل له طريقته. أحيانًا يفرض المنتج الجاهز عليك إجراءاته بدل أن يخدم إجراءاتك. النظام المخصّص يعكس سير عملك الحقيقي، يزيل الخطوات اليدوية، ويمنحك ميزة تنافسية يصعب نسخها.', en: "Every business has its own way. Sometimes a ready product imposes its process instead of serving yours. A custom system reflects your real workflow, removes manual steps, and gives you a competitive edge that's hard to copy." },
          { ar: 'نبدأ بجلسة اكتشاف نفهم فيها احتياجك، ثم نصمّم ونطوّر بمنهجية رشيقة نطلق فيها نسخة أولى سريعًا، ونتكامل مع أنظمتك، ونطوّر ونصون باستمرار، وبياناتك ملكك.', en: 'We start with a discovery session to understand your needs, then design and develop in an agile way that ships a first version quickly, integrate with your systems, and iterate and maintain, and your data is yours.' },
        ],
        points: [
          { ar: 'مبني حول إجراءات عملك', en: 'Built around your processes' },
          { ar: 'منهجية رشيقة بإطلاق سريع', en: 'Agile approach with a quick first release' },
          { ar: 'تكامل مع أنظمتك الحالية', en: 'Integration with your existing systems' },
          { ar: 'ملكية واضحة للكود والبيانات', en: 'Clear code and data ownership' },
          { ar: 'تطوير ودعم مستمر', en: 'Ongoing development and support' },
        ],
        useCases: [
          { ar: 'الإجراءات الفريدة غير القياسية', en: 'Unique, non-standard processes' },
          { ar: 'المؤسسات ذات المتطلّبات الخاصة', en: 'Organizations with special requirements' },
          { ar: 'ربط أنظمة متعددة', en: 'Connecting multiple systems' },
          { ar: 'المشاريع التي تحتاج ميزة تنافسية', en: 'Projects needing a competitive edge' },
        ],
      },
      {
        title: { ar: 'التطبيقات', en: "" }, en: "Web & mobile apps",
        img: "/divisions/os-systems/apps.jpg", slug: "apps",
        lead: { ar: 'تطبيقات الويب والموبايل تصل بك إلى عملائك وفريقك في أي مكان، واجهات نظيفة وسريعة وسهلة الاستخدام، مبنية بأحدث التقنيات ومصمّمة لتجربة استخدام ممتازة.', en: 'Web and mobile apps reach your customers and team anywhere, clean, fast, easy-to-use interfaces, built with the latest technologies and designed for an excellent user experience.' },
        body: [
          { ar: 'التطبيق الجيد ليس مجرد شاشات، بل تجربة. الواجهة النظيفة السريعة تبني ثقة المستخدم وتزيد التفاعل، بينما التطبيق البطيء المعقّد يطرد العملاء مهما كانت الفكرة جيدة.', en: 'A good app is not just screens but an experience. A clean, fast interface builds user trust and boosts engagement, while a slow, complex app drives customers away no matter how good the idea.' },
          { ar: 'نصمّم تجربة الاستخدام والمعمار، ونطوّر تطبيقات ويب وموبايل بأداء عالٍ، ونربطها بأنظمتك، ونطلقها ونطوّرها بعد الإطلاق مع دعم مستمر.', en: 'We design the UX and architecture, develop high-performance web and mobile apps, connect them to your systems, and launch and iterate after go-live with ongoing support.' },
        ],
        points: [
          { ar: 'واجهات ويب وموبايل نظيفة', en: 'Clean web and mobile interfaces' },
          { ar: 'أداء عالٍ وسرعة', en: 'High performance and speed' },
          { ar: 'تجربة استخدام مدروسة', en: 'Considered user experience' },
          { ar: 'ربط بأنظمتك وواجهات التكامل', en: 'Integration with your systems and APIs' },
          { ar: 'إطلاق وتطوير ودعم', en: 'Launch, iteration and support' },
        ],
        useCases: [
          { ar: 'المتاجر والخدمات الرقمية', en: 'Stores and digital services' },
          { ar: 'الشركات الناشئة', en: 'Startups' },
          { ar: 'المؤسسات التي تخدم عملاء', en: 'Customer-facing organizations' },
          { ar: 'أي فكرة تحتاج منصّة', en: 'Any idea that needs a platform' },
        ],
      },
    ],
    systemsNote: { ar: "ERP منتج جاهز بالاشتراك، وأدابتيف مشروعنا الداخلي للمنزل الذكي التكيّفي؛ وما بينهما نبني أنظمة على مقاس كل عميل.", en: "ERP is a ready subscription product, Adaptive is our in-house adaptive smart-home project; between them we build systems tailored to each client." },
    statementTitle: { ar: "البرمجيات تُقاس بالتشغيل، لا بالعرض.", en: "Software is measured by operation, not by the demo." },
    statementBody: { ar: "نبني أنظمة تصمد في الاستخدام اليومي، واضحة، موثوقة، ومبنية لتتطوّر مع عملك.", en: "We build systems that hold up in daily use, clear, reliable and built to evolve with your business." },
    flowEyebrow: { ar: "مسار العمل", en: "How we work" },
    flowTitle: { ar: "من الفكرة حتى التشغيل.", en: "From idea to operation." },
    flow: [
      { title: { ar: "الاكتشاف", en: "Discovery" }, desc: { ar: "فهم الاحتياج.", en: "Understand needs." } },
      { title: { ar: "التصميم", en: "Design" }, desc: { ar: "تجربة ومعمار.", en: "UX & architecture." } },
      { title: { ar: "البناء", en: "Build" }, desc: { ar: "تطوير رشيق.", en: "Agile development." } },
      { title: { ar: "الإطلاق", en: "Launch" }, desc: { ar: "تشغيل واعتماد.", en: "Operate & adopt." } },
      { title: { ar: "التطوير", en: "Iterate" }, desc: { ar: "دعم مستمر.", en: "Ongoing support." } },
    ],
    ctaTitle: { ar: "عندك فكرة أو نظام تريد بناءه؟", en: "Have an idea or a system to build?" },
    ctaBody: { ar: "نبدأ بجلسة اكتشاف نفهم فيها احتياجك، ونجهّز خطة واضحة للبناء والتشغيل.", en: "We start with a discovery session to understand your needs and prepare a clear plan to build and operate." },
  },
};

export function divisionMetaColor(_d: DivisionMeta) {
  return _d.color;
}
