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
  lead?: Bi; // longer marketing intro for the service detail page
  points?: Bi[]; // key points / what we offer on the detail page
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
      ar: "قسم هندسة التكييف ضمن سيلترا وان، التوريد والتنفيذ الميداني والصيانة الوقائية والتحكّم الذكي، من دراسة الموقع حتى التشغيل والدعم.",
      en: "The HVAC engineering division of Syltra One, supply, field execution, preventive maintenance and smart control, from site study to operation and support.",
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
          ar: "أنظمة التكييف المركزي والشيلر هي الخيار الأمثل للمباني الكبيرة والمجمّعات — تبريد موحّد وموثوق بكفاءة عالية وتحكّم مركزي. نصمّم النظام بعد دراسة حمل حراري دقيقة، ثم نوّرد وننفّذ ونشغّل ونصون.",
          en: "Central and chiller systems are the right fit for large buildings and complexes — unified, reliable cooling with high efficiency and central control. We design the system after an accurate load study, then supply, install, commission and maintain.",
        },
        points: [
          { ar: "دراسة حمل حراري وتحديد السعة الأنسب", en: "Heat-load study and correct capacity sizing" },
          { ar: "شيلر هوائي أو مائي حسب طبيعة المشروع", en: "Air- or water-cooled chillers to suit the project" },
          { ar: "توزيع هواء عبر دكت مصمّم بعناية", en: "Air distribution through carefully engineered ducting" },
          { ar: "تحكّم مركزي ومناطق متعددة", en: "Central control with multiple zones" },
          { ar: "عقود صيانة تحافظ على الكفاءة والعمر", en: "Maintenance contracts that protect efficiency and lifespan" },
        ],
      },
      {
        title: { ar: "أنظمة VRF/VRV", en: "" }, en: "VRF / VRV",
        img: "/divisions/climate-systems/vrf.jpg", slug: "vrf",
        lead: {
          ar: "أنظمة VRF/VRV تمنحك تبريدًا مرنًا لمناطق متعددة بتحكّم مستقل لكل غرفة وكفاءة عالية في الطاقة — مثالية للمكاتب والفلل والمباني ذات الاستخدامات المتنوّعة.",
          en: "VRF/VRV systems give flexible cooling across many zones with independent per-room control and high energy efficiency — ideal for offices, villas and mixed-use buildings.",
        },
        points: [
          { ar: "تحكّم مستقل في درجة حرارة كل منطقة", en: "Independent temperature control per zone" },
          { ar: "كفاءة عالية وتوفير في استهلاك الطاقة", en: "High efficiency and lower energy consumption" },
          { ar: "مرونة في التمديد للمساحات الواسعة", en: "Flexible piping for large layouts" },
          { ar: "تشغيل هادئ وتوزيع متّزن", en: "Quiet operation and balanced distribution" },
          { ar: "ربط بالتطبيق وجداول تشغيل ذكية", en: "App control and smart schedules" },
        ],
      },
      {
        title: { ar: "دكت وتوزيع الهواء", en: "" }, en: "Ducted air",
        img: "/divisions/climate-systems/ducted.jpg", slug: "ducted",
        lead: {
          ar: "أنظمة الدكت المخفية توزّع الهواء بانسيابية وهدوء مع مظهر داخلي نظيف — نصمّم مسارات الدكت والمخارج بعناية لأداء متّزن في كل غرفة.",
          en: "Concealed ducted systems distribute air smoothly and quietly with a clean interior look — we engineer duct runs and grilles for even performance in every room.",
        },
        points: [
          { ar: "تصميم مسارات دكت يقلّل الفاقد والضوضاء", en: "Duct routing that cuts loss and noise" },
          { ar: "مخارج هواء موزّعة بعناية لكل غرفة", en: "Grilles placed carefully per room" },
          { ar: "مظهر داخلي نظيف بلا وحدات ظاهرة", en: "Clean interiors with no visible units" },
          { ar: "عزل حراري وصوتي للدكت", en: "Thermal and acoustic duct insulation" },
          { ar: "اختبار وموازنة (TAB) قبل التسليم", en: "Testing and balancing (TAB) before handover" },
        ],
      },
      {
        title: { ar: "سبليت وملتي سبليت", en: "" }, en: "Split systems",
        img: "/divisions/climate-systems/split.jpg", slug: "split",
        lead: {
          ar: "أنظمة السبليت والملتي سبليت حل عملي واقتصادي للغرف والوحدات الصغيرة — تركيب سريع وكفاءة جيدة وصيانة سهلة.",
          en: "Split and multi-split systems are a practical, economical solution for rooms and smaller units — quick installation, good efficiency and easy maintenance.",
        },
        points: [
          { ar: "اختيار السعة المناسبة لكل غرفة", en: "Right capacity for each room" },
          { ar: "وحدة خارجية واحدة لعدة داخلية (ملتي)", en: "One outdoor unit for several indoor (multi)" },
          { ar: "تركيب نظيف وسريع", en: "Clean, fast installation" },
          { ar: "موديلات موفّرة للطاقة (إنفرتر)", en: "Energy-saving inverter models" },
          { ar: "صيانة دورية وقطع معتمدة", en: "Routine maintenance and certified parts" },
        ],
      },
      {
        title: { ar: "تهوية وتجديد الهواء", en: "" }, en: "Ventilation",
        img: "/divisions/climate-systems/ventilation.jpg", slug: "ventilation",
        lead: {
          ar: "التهوية الجيدة لا تقل أهمية عن التبريد — نصمّم أنظمة تجديد هواء وفلترة تُدخل هواءً نقيًا وتطرد الملوّثات والرطوبة الزائدة لهواء داخلي صحي.",
          en: "Good ventilation matters as much as cooling — we design fresh-air and filtration systems that bring in clean air and remove pollutants and excess humidity for healthy indoor air.",
        },
        points: [
          { ar: "وحدات مناولة هواء (AHU) وتجديد الهواء", en: "Air-handling units (AHU) and fresh air" },
          { ar: "فلترة متعددة المراحل لهواء أنظف", en: "Multi-stage filtration for cleaner air" },
          { ar: "استرجاع حراري لتقليل الاستهلاك (HRV/ERV)", en: "Heat recovery to cut consumption (HRV/ERV)" },
          { ar: "تحكّم بالرطوبة والضغط", en: "Humidity and pressure control" },
          { ar: "مناسبة للمطاعم والعيادات والمساحات المزدحمة", en: "Suited to restaurants, clinics and busy spaces" },
        ],
      },
      {
        title: { ar: "التحكّم والأتمتة", en: "" }, en: "Controls",
        img: "/divisions/climate-systems/controls.jpg", slug: "controls",
        lead: {
          ar: "التحكّم الذكي يحوّل التكييف من جهاز إلى نظام — جداول ومناطق وحساسات وربط بالتطبيق تحافظ على الراحة وتخفّض الفاتورة.",
          en: "Smart control turns AC from a device into a system — schedules, zones, sensors and app control that keep comfort while cutting the bill.",
        },
        points: [
          { ar: "ثيرموستات ذكي وجداول تشغيل", en: "Smart thermostats and schedules" },
          { ar: "مناطق متعددة بتحكّم مستقل", en: "Multiple zones with independent control" },
          { ar: "حساسات إشغال وجودة هواء", en: "Occupancy and air-quality sensors" },
          { ar: "ربط بمنصّة سيلترا لايف والتطبيق", en: "Integration with the Syltra Life platform and app" },
          { ar: "تقارير استهلاك تساعدك على التوفير", en: "Consumption reports that help you save" },
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
      ar: "قسم المصاعد وأنظمة الحركة الرأسية ضمن سيلترا وان، نغطّي دورة حياة المصعد بالكامل، من الدراسة الفنية واختيار النظام إلى التوريد والتركيب والتشغيل والصيانة.",
      en: "The elevators and vertical-mobility division of Syltra One, covering the full lift lifecycle, from technical study and system selection to supply, installation, operation and maintenance.",
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
      { title: { ar: "مصاعد الركاب", en: "" }, en: "Passenger", img: "/divisions/glide-systems/passenger.jpg" },
      { title: { ar: "الفلل والمنازل", en: "" }, en: "Home & villa", img: "/divisions/glide-systems/villa.jpg" },
      { title: { ar: "البانورامية", en: "" }, en: "Panoramic", img: "/divisions/glide-systems/panoramic.jpg" },
      { title: { ar: "ذوي الإعاقة", en: "" }, en: "Accessibility", img: "/divisions/glide-systems/accessibility.jpg" },
      { title: { ar: "المستشفيات", en: "" }, en: "Hospital", img: "/divisions/glide-systems/hospital.jpg" },
      { title: { ar: "البضائع", en: "" }, en: "Freight", img: "/divisions/glide-systems/freight.jpg" },
      { title: { ar: "مصاعد الطعام", en: "" }, en: "Food lifts", img: "/divisions/glide-systems/food.jpg" },
      { title: { ar: "المولات والمباني", en: "" }, en: "Malls & public", img: "/divisions/glide-systems/public.jpg" },
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
      ar: "قسم الأمن والسلامة والأنظمة الكهربائية ضمن سيلترا وان، الحريق والمراقبة والتحكّم بالدخول والتيار المنخفض والبنية الكهربائية، من التصميم حتى التشغيل والصيانة.",
      en: "The security, safety and electrical division of Syltra One, fire, surveillance, access control, low-current and electrical infrastructure, from design to operation and maintenance.",
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
      { title: { ar: "إنذار ومكافحة الحريق", en: "" }, en: "Fire alarm & fighting", img: "/divisions/shield-systems/fire.jpg" },
      { title: { ar: "المراقبة بالكاميرات", en: "" }, en: "CCTV", img: "/divisions/shield-systems/cctv.jpg" },
      { title: { ar: "التحكّم بالدخول", en: "" }, en: "Access control", img: "/divisions/shield-systems/access.jpg" },
      { title: { ar: "الإنذار ضد السرقة", en: "" }, en: "Intrusion alarm", img: "/divisions/shield-systems/intrusion.jpg" },
      { title: { ar: "التيار المنخفض والشبكات", en: "" }, en: "Low current & networks", img: "/divisions/shield-systems/lowcurrent.jpg" },
      { title: { ar: "البنية الكهربائية", en: "" }, en: "Electrical & MEP", img: "/divisions/shield-systems/electrical.jpg" },
      { title: { ar: "النداء الصوتي والإخلاء", en: "" }, en: "PA & evacuation", img: "/divisions/shield-systems/pa.jpg" },
      { title: { ar: "كاميرات المراقبة بالطاقة الشمسية", en: "" }, en: "Solar-powered CCTV" },
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
      ar: "ذراع البرمجيات والذكاء الاصطناعي في سيلترا وان، منتجات جاهزة وأنظمة مخصّصة وحلول ذكاء اصطناعي، من الفكرة حتى التشغيل والدعم المستمر.",
      en: "The software and AI arm of Syltra One, ready products, custom systems and AI solutions, from idea to operation and ongoing support.",
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
      { title: { ar: "سيلترا ERP", en: "" }, en: "ERP, SaaS product", img: "/divisions/os-systems/erp.jpg" },
      { title: { ar: "سيلترا أدابتيف", en: "" }, en: "Adaptive smart-home", img: "/divisions/os-systems/adaptive.jpg" },
      { title: { ar: "مساعدون بالذكاء الاصطناعي", en: "" }, en: "AI assistants", img: "/divisions/os-systems/ai.jpg" },
      { title: { ar: "لوحات التحليلات", en: "" }, en: "Analytics & BI", img: "/divisions/os-systems/analytics.jpg" },
      { title: { ar: "أنظمة مخصّصة", en: "" }, en: "Custom platforms", img: "/divisions/os-systems/custom.jpg" },
      { title: { ar: "التطبيقات", en: "" }, en: "Web & mobile apps", img: "/divisions/os-systems/apps.jpg" },
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
