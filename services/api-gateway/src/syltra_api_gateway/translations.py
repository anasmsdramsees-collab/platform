"""Reason-code translation at the presentation layer (spec §21, §28).

Reason codes travel through the platform as stable machine identifiers —
`CONFIDENCE_BELOW_THRESHOLD`, `USER_CONTROL_TAKES_PRECEDENCE` — and are turned
into human sentences only here. Keeping translation at the edge means the codes
stay stable for audit and testing while the wording can change freely.

Two rules shape the Arabic:

- **Explain, do not transliterate.** `TARGET_STATE_NOT_FRESH` becomes
  "قراءة الجهاز ليست حديثة بما يكفي" — an actual explanation — rather than an
  Arabic-script rendering of the English words.
- **Technical terms stay recognisable.** Where a household would see the English
  term on the device itself, it is kept alongside the Arabic (spec §28: correct
  alignment for mixed Arabic and technical English terms).
"""

from typing import Final

Locale = str

SUPPORTED_LOCALES: Final[tuple[str, ...]] = ("en", "ar")
DEFAULT_LOCALE: Final[str] = "en"

RTL_LOCALES: Final[frozenset[str]] = frozenset({"ar"})


def is_rtl(locale: str) -> bool:
    return locale in RTL_LOCALES


# ── the catalogue ──
# Every reason code the platform can emit. A contract test extracts codes from
# the source and fails if any is missing here, so a new code cannot ship
# untranslated.

REASON_CODES: Final[dict[str, dict[str, str]]] = {
    # context: occupancy and activity
    "MOTION_DETECTED": {"en": "Motion detected", "ar": "تم رصد حركة"},
    "ROOM_MOTION_DETECTED": {"en": "Motion detected in this room", "ar": "تم رصد حركة في هذه الغرفة"},
    "PRESENCE_TRACKER_HOME": {"en": "A resident's device is at home", "ar": "جهاز أحد السكان موجود في المنزل"},
    "NO_MOTION": {"en": "No motion detected", "ar": "لم يتم رصد أي حركة"},
    "NO_PRESENCE": {"en": "No resident devices detected", "ar": "لم يتم رصد أجهزة السكان"},
    "PRESENCE_ARRIVED": {"en": "A resident has arrived", "ar": "وصل أحد السكان"},
    "PRESENCE_AWAY": {"en": "A resident has left", "ar": "غادر أحد السكان"},
    "ENTRY_OPENED": {"en": "An entry door was opened", "ar": "تم فتح باب الدخول"},
    "HOME_EMPTY": {"en": "The home appears to be empty", "ar": "يبدو أن المنزل خالٍ"},
    "CHILD_TRACKER_HOME": {"en": "A child's tracker is at home", "ar": "جهاز تتبع الطفل موجود في المنزل"},
    "QUIET_HOURS": {"en": "Quiet hours", "ar": "ساعات الهدوء"},
    "WITHIN_QUIET_HOURS": {"en": "Currently within quiet hours", "ar": "الوقت الحالي ضمن ساعات الهدوء"},
    "LIGHTS_OFF": {"en": "Lights are off", "ar": "الإضاءة مطفأة"},
    "KITCHEN_OCCUPIED": {"en": "Someone is in the kitchen", "ar": "يوجد شخص في المطبخ"},
    "APPLIANCE_ACTIVITY": {"en": "An appliance is drawing power", "ar": "يوجد جهاز يستهلك الطاقة"},
    "POWER_ABOVE_THRESHOLD": {"en": "Power use is above the usual level", "ar": "استهلاك الطاقة أعلى من المعتاد"},
    "DEVICES_OFFLINE": {"en": "Some devices are offline", "ar": "بعض الأجهزة غير متصلة"},
    "STALE_READINGS": {"en": "Some readings are out of date", "ar": "بعض القراءات ليست حديثة"},
    "ADVISORY_ONLY": {
        "en": "Advisory only — this does not confirm a hazard",
        "ar": "للعلم فقط — هذا لا يؤكد وجود خطر",
    },
    # adaptive
    "REPEATED_USER_PATTERN": {"en": "You usually do this at this time", "ar": "عادةً ما تفعل ذلك في هذا الوقت"},
    "CONTEXTUAL_PREFERENCE": {"en": "Based on your usual preference", "ar": "بناءً على تفضيلك المعتاد"},
    "NO_ESTABLISHED_PATTERN": {"en": "No established pattern yet", "ar": "لا يوجد نمط ثابت بعد"},
    "CLAMPED_TO_SAFE_RANGE": {"en": "Adjusted to stay within the safe range", "ar": "تم التعديل ليبقى ضمن النطاق الآمن"},
    "WITHIN_BASELINE": {"en": "Within the normal range", "ar": "ضمن النطاق الطبيعي"},
    "ROBUST_STATISTICS": {"en": "Compared against your typical usage", "ar": "بالمقارنة مع استخدامك المعتاد"},
    "ENERGY_ABOVE_BASELINE": {
        "en": "Energy use is unusually high",
        "ar": "استهلاك الطاقة مرتفع بشكل غير معتاد",
    },
    "ENERGY_BELOW_BASELINE": {
        "en": "Energy use is unusually low",
        "ar": "استهلاك الطاقة منخفض بشكل غير معتاد",
    },
    "INSUFFICIENT_SAMPLES": {"en": "Not enough data yet", "ar": "لا توجد بيانات كافية بعد"},
    "INSUFFICIENT_DAY_DIVERSITY": {"en": "Not enough days of data yet", "ar": "لا توجد أيام كافية من البيانات بعد"},
    "INSUFFICIENT_TIME_DIVERSITY": {"en": "Data covers too few times of day", "ar": "البيانات تغطي أوقاتاً قليلة من اليوم"},
    "INSUFFICIENT_POWER_SAMPLES": {"en": "Not enough energy readings yet", "ar": "لا توجد قراءات طاقة كافية بعد"},
    "INSUFFICIENT_SETPOINT_SAMPLES": {"en": "Not enough temperature adjustments yet", "ar": "لا توجد تعديلات حرارة كافية بعد"},
    "NO_CAPABILITY_ACTIVATIONS": {"en": "This device has not been used yet", "ar": "لم يُستخدم هذا الجهاز بعد"},
    "NO_DATA": {"en": "No data available", "ar": "لا توجد بيانات متاحة"},
    # policy
    "WITHIN_POLICY": {"en": "Allowed by your settings", "ar": "مسموح به وفق إعداداتك"},
    "MANUAL_CONTROL": {
        "en": "You did this yourself",
        "ar": "أنت من قام بهذا",
    },
    "NOT_ALLOWED_HERE": {
        "en": "This cannot be operated from here",
        "ar": "لا يمكن تشغيل هذا من هنا",
    },
    "NOT_OPERABLE_BY_HAND": {
        "en": "This is operated by the safety system only",
        "ar": "هذا يشغّله نظام السلامة وحده",
    },
    "CAPABILITY_NOT_AUTOMATABLE": {
        "en": "This can only be operated by the safety system, never by an automation",
        "ar": "هذا لا يُشغَّل إلا من نظام السلامة، ولا يمكن لأي أتمتة تشغيله",
    },
    "AUTHORIZED_BY_SAFETY_GOVERNOR": {
        "en": "Authorized by the safety system, not by a setting",
        "ar": "مصرّح به من نظام السلامة، لا من إعداد",
    },
    "ISOLATION_VERIFIED": {
        "en": "The supply is closed and the device confirmed it",
        "ar": "تم إغلاق الإمداد وأكّد الجهاز ذلك",
    },
    "ISOLATION_UNVERIFIED": {
        "en": "The close command was sent and the device did not confirm it",
        "ar": "أُرسل أمر الإغلاق ولم يؤكّده الجهاز",
    },
    "NO_REACHABLE_ISOLATION_DEVICE": {
        "en": "No reachable valve to close",
        "ar": "لا يوجد محبس يمكن الوصول إليه لإغلاقه",
    },
    "SHADOW_MODE_RECOMMENDATION": {
        "en": "The system is still learning and will not act",
        "ar": "النظام ما زال في مرحلة التعلّم ولن يتخذ أي إجراء",
    },
    "RECOMMENDATION_EXPIRED": {"en": "This suggestion is no longer current", "ar": "لم تعد هذه الاقتراح صالحاً"},
    "HISTORICAL_REPLAY_SUSPECTED": {"en": "Based on out-of-date information", "ar": "مبني على معلومات قديمة"},
    "LIFE_SAFETY_CAPABILITY": {"en": "This device is safety-critical", "ar": "هذا الجهاز حرج للسلامة"},
    "ADAPTIVE_OUTPUT_NOT_PERMITTED": {
        "en": "Safety devices are controlled by fixed rules, never by learning",
        "ar": "أجهزة السلامة تُدار بقواعد ثابتة، وليس عبر التعلّم",
    },
    "ACTIVE_RISK_CASE": {"en": "There is an open safety case", "ar": "توجد حالة سلامة مفتوحة"},
    "COMFORT_AUTOMATION_SUSPENDED": {"en": "Comfort automation is paused", "ar": "تم إيقاف أتمتة الراحة مؤقتاً"},
    "CONSENT_NOT_GRANTED": {"en": "This feature has not been enabled", "ar": "لم يتم تفعيل هذه الميزة"},
    "SUPPRESSED_BY_USER": {"en": "You asked not to be offered this again", "ar": "طلبت عدم عرض هذا مرة أخرى"},
    "RECENT_MANUAL_OVERRIDE": {"en": "You adjusted this device recently", "ar": "قمت بتعديل هذا الجهاز مؤخراً"},
    "USER_CONTROL_TAKES_PRECEDENCE": {"en": "Your control takes precedence", "ar": "تحكّمك له الأولوية"},
    "TARGET_STATE_NOT_FRESH": {"en": "The device reading is not recent enough", "ar": "قراءة الجهاز ليست حديثة بما يكفي"},
    "TWIN_STATUS_STALE": {"en": "The device reading is out of date", "ar": "قراءة الجهاز قديمة"},
    "TWIN_STATUS_UNKNOWN": {"en": "The device state is unknown", "ar": "حالة الجهاز غير معروفة"},
    "CONFIDENCE_BELOW_THRESHOLD": {"en": "Not confident enough to act", "ar": "الثقة غير كافية لاتخاذ إجراء"},
    "CONFIDENCE_BELOW_UNATTENDED_THRESHOLD": {
        "en": "Not confident enough to act without asking",
        "ar": "الثقة غير كافية للتنفيذ دون سؤالك",
    },
    "ALREADY_AT_PROPOSED_VALUE": {"en": "The device is already set this way", "ar": "الجهاز مضبوط على هذه القيمة بالفعل"},
    "COOLDOWN_ACTIVE": {"en": "This device was adjusted very recently", "ar": "تم تعديل هذا الجهاز قبل قليل"},
    "RATE_LIMIT_EXCEEDED": {"en": "Too many changes in a short time", "ar": "عدد كبير من التغييرات خلال وقت قصير"},
    "QUIET_HOURS_ACTIVE": {"en": "Held back during quiet hours", "ar": "تم التأجيل أثناء ساعات الهدوء"},
    "CAPABILITY_REQUIRES_APPROVAL": {"en": "This device always needs your approval", "ar": "هذا الجهاز يتطلب موافقتك دائماً"},
    "AUTOMATION_NOT_YET_TRUSTED": {
        "en": "Automatic action is not enabled yet",
        "ar": "لم يتم تفعيل التنفيذ التلقائي بعد",
    },
    "RECOMMENDATION_REQUESTS_APPROVAL": {"en": "This suggestion asks for your approval", "ar": "هذا الاقتراح يطلب موافقتك"},
    "USER_APPROVED": {"en": "You approved this", "ar": "لقد وافقت على هذا"},
    "USER_REJECTED": {"en": "You declined this", "ar": "لقد رفضت هذا"},
    # actions
    "VERIFIED": {"en": "Confirmed by the device", "ar": "تم التأكيد من الجهاز"},
    # A scene step whose device could not be reached at all. Distinct from a
    # command that was sent and not confirmed: nothing left the hub for this
    # one, and a household deciding whether to walk back and check needs to
    # know which of the two happened.
    "DEVICE_DID_NOT_ANSWER": {
        "en": "The device did not answer",
        "ar": "الجهاز لم يستجب",
    },
    "VERIFICATION_FAILED": {"en": "The device did not confirm the change", "ar": "لم يؤكد الجهاز التغيير"},
    "ALREADY_IN_EXPECTED_STATE": {"en": "The device was already as requested", "ar": "كان الجهاز بالفعل كما هو مطلوب"},
    "ACTION_EXPIRED": {"en": "This action took too long and was abandoned", "ar": "استغرق هذا الإجراء وقتاً طويلاً وتم إلغاؤه"},
    "ACTION_EXPIRED_BEFORE_DISPATCH": {"en": "Expired before it could be sent", "ar": "انتهت صلاحيته قبل الإرسال"},
    "MANUAL_OVERRIDE_DETECTED": {"en": "Cancelled because you took control", "ar": "تم الإلغاء لأنك توليت التحكم"},
    "NO_POLICY_DECISION": {"en": "No approval on record for this action", "ar": "لا توجد موافقة مسجلة لهذا الإجراء"},
    "POLICY_DECISION_NOT_AUTHORIZING": {"en": "This action was not approved", "ar": "لم تتم الموافقة على هذا الإجراء"},
    "DECISION_HOME_MISMATCH": {"en": "The approval belongs to a different home", "ar": "الموافقة تخص منزلاً آخر"},
    "AUDIT_STORE_UNAVAILABLE": {
        "en": "Held back because this action could not be recorded",
        "ar": "تم التأجيل لأنه تعذّر تسجيل هذا الإجراء",
    },
    "DISPATCH_DISABLED_OBSERVE_ONLY": {
        "en": "This hub is observing only and sent nothing to the device",
        "ar": "هذا الموزّع في وضع المراقبة فقط ولم يُرسل شيئاً إلى الجهاز",
    },
    "AUTOMATION_TRIGGERED": {
        "en": "An automation you set up asked for this",
        "ar": "طلبت هذا أتمتة قمت بإعدادها",
    },
    "AUTOMATION_DISABLED": {"en": "This automation is switched off", "ar": "هذه الأتمتة موقوفة"},
    "AUTOMATION_REARMING": {
        "en": "It ran recently and is waiting before it can run again",
        "ar": "عملت مؤخراً وتنتظر قبل أن تعمل مجدداً",
    },
    "AUTOMATION_OWN_ECHO": {
        "en": "Held back because this would react to its own change",
        "ar": "تم التأجيل لأن هذا سيتفاعل مع تغييره الخاص",
    },
    "MANUAL_OVERRIDE_ACTIVE": {
        "en": "You changed this yourself, so the automation left it alone",
        "ar": "غيّرت هذا بنفسك، فتركته الأتمتة كما هو",
    },
    "TRIGGER_NOT_MET": {"en": "Its trigger did not happen", "ar": "لم يقع مُشغّلها"},
    "CONDITION_NOT_MET": {
        "en": "Its trigger happened, but a condition was not met",
        "ar": "وقع مُشغّلها، لكن أحد الشروط لم يتحقق",
    },
    "CRITICAL_ACTUATOR_BLOCKED_IN_DEVELOPMENT": {
        "en": "Safety devices are blocked in this environment",
        "ar": "أجهزة السلامة محظورة في هذه البيئة",
    },
    "INVALID_EVENT_AT_CONSUMER": {"en": "An invalid event was received", "ar": "تم استقبال حدث غير صالح"},
    "DUPLICATE_EVENT": {"en": "Duplicate event ignored", "ar": "تم تجاهل حدث مكرر"},
    "OUT_OF_ORDER_EVENT": {"en": "An out-of-order reading arrived", "ar": "وصلت قراءة خارج الترتيب"},
    "UNMAPPED_ENTITY": {"en": "This device is not yet supported", "ar": "هذا الجهاز غير مدعوم بعد"},
    # risk
    "ADVISORY_PENDING_CONFIRMATION": {
        "en": "Being watched — not yet confirmed",
        "ar": "قيد المراقبة — لم يتم التأكيد بعد",
    },
    "GAS_ALARM_READING": {"en": "The gas detector is reporting", "ar": "كاشف الغاز يُصدر إشارة"},
    "GAS_ALARM_ACTIVE": {"en": "The gas alarm is active", "ar": "إنذار الغاز نشط"},
    "SMOKE_ALARM_READING": {"en": "The smoke detector is reporting", "ar": "كاشف الدخان يُصدر إشارة"},
    "HEAT_ALARM_READING": {"en": "The heat detector is reporting", "ar": "كاشف الحرارة يُصدر إشارة"},
    "CO_ALARM_READING": {"en": "The carbon monoxide detector is reporting", "ar": "كاشف أول أكسيد الكربون يُصدر إشارة"},
    "LEAK_DETECTOR_READING": {"en": "The leak detector is reporting", "ar": "كاشف التسرب يُصدر إشارة"},
    "LEAK_DETECTOR_ACTIVE": {"en": "The leak detector is wet", "ar": "كاشف التسرب مبلل"},
    "COOKING_IN_PROGRESS": {"en": "Cooking appears to be in progress", "ar": "يبدو أن الطهي جارٍ"},
    "CERTIFIED_GAS_ALARM_ACTIVE": {"en": "Certified gas alarm confirmed", "ar": "تم تأكيد إنذار الغاز المعتمد"},
    "CERTIFIED_SMOKE_ALARM_ACTIVE": {"en": "Certified smoke alarm confirmed", "ar": "تم تأكيد إنذار الدخان المعتمد"},
    "CERTIFIED_HEAT_ALARM_ACTIVE": {"en": "Certified heat alarm confirmed", "ar": "تم تأكيد إنذار الحرارة المعتمد"},
    "CERTIFIED_CO_ALARM_ACTIVE": {
        "en": "Certified carbon monoxide alarm confirmed",
        "ar": "تم تأكيد إنذار أول أكسيد الكربون المعتمد",
    },
    "CERTIFIED_WATER_LEAK_ACTIVE": {"en": "Certified leak detector confirmed", "ar": "تم تأكيد كاشف التسرب المعتمد"},
    "DETERMINISTIC_CONFIRMATION": {
        "en": "Confirmed by a fixed safety rule",
        "ar": "تم التأكيد بقاعدة سلامة ثابتة",
    },
    "HIGH_POWER_WHILE_EMPTY": {"en": "High power use while the home is empty", "ar": "استهلاك طاقة مرتفع والمنزل خالٍ"},
    "NO_AUTOMATIC_BREAKER_ACTION": {
        "en": "No automatic electrical action will be taken",
        "ar": "لن يتم اتخاذ أي إجراء كهربائي تلقائي",
    },
    "TEMPERATURE_OUT_OF_RANGE": {"en": "Temperature is outside the safe range", "ar": "درجة الحرارة خارج النطاق الآمن"},
    "SAFETY_SENSOR_NOT_REPORTING": {"en": "A safety sensor has stopped reporting", "ar": "توقف أحد حساسات السلامة عن الإرسال"},
    "PROTECTION_GAP": {"en": "There is a gap in safety coverage", "ar": "توجد ثغرة في تغطية السلامة"},
    "ENTRY_OPENED_WHILE_EMPTY": {"en": "An entry opened while the home was empty", "ar": "تم فتح مدخل والمنزل خالٍ"},
}


def translate_reason(code: str, locale: str = DEFAULT_LOCALE) -> str:
    """Human text for a reason code.

    An unknown code returns the code itself rather than raising: a user seeing a
    raw identifier is a cosmetic problem, while an API failing mid-incident
    because a new code was not yet translated is a real one.
    """
    entry = REASON_CODES.get(code)
    if entry is None:
        return code
    return entry.get(locale) or entry.get(DEFAULT_LOCALE) or code


def translate_reasons(codes: list[str], locale: str = DEFAULT_LOCALE) -> list[str]:
    return [translate_reason(code, locale) for code in codes]


def negotiate_locale(header: str | None, override: str | None = None) -> str:
    """Resolve a locale from an explicit choice or an Accept-Language header."""
    if override and override in SUPPORTED_LOCALES:
        return override
    if not header:
        return DEFAULT_LOCALE
    for part in header.split(","):
        tag = part.split(";")[0].strip().lower()
        base = tag.split("-")[0]
        if base in SUPPORTED_LOCALES:
            return base
    return DEFAULT_LOCALE


def untranslated_codes(codes: set[str]) -> set[str]:
    """Codes with no catalogue entry — used by the contract test."""
    return {code for code in codes if code not in REASON_CODES}
