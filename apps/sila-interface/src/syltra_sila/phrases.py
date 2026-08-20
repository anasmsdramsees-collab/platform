"""SILA phrasing in Arabic and English (spec §14.10, §28).

Templates, not generation. SILA composes sentences from a fixed catalogue with
typed substitutions — there is no language model in this path, so what SILA says
is always something a person wrote and reviewed.

The Arabic is written as Arabic, not translated word-for-word from the English:
"لا توجد مخاطر نشطة" reads naturally, where a literal rendering of "no active
risks" would not.
"""

from typing import Any, Final

PHRASES: Final[dict[str, dict[str, str]]] = {
    "home_status": {
        "en": "{devices} devices, {online} online, with {contexts} active contexts.",
        "ar": "{devices} جهازاً، منها {online} متصل، مع {contexts} سياقات نشطة.",
    },
    "risk_clear": {
        "en": "Everything looks normal. No active risks.",
        "ar": "كل شيء يبدو طبيعياً. لا توجد مخاطر نشطة.",
    },
    "risk_watching": {
        "en": "I am watching {count} situation(s). Nothing is confirmed.",
        "ar": "أراقب {count} حالة. لم يتم تأكيد أي منها.",
    },
    "risk_confirmed": {
        "en": "A {category} alarm is confirmed. Please check immediately.",
        "ar": "تم تأكيد إنذار {category}. يرجى التحقق فوراً.",
    },
    "recommendation_count": {
        "en": "You have {count} suggestion(s) waiting.",
        "ar": "لديك {count} اقتراح في الانتظار.",
    },
    "explain_recommendation": {
        "en": "I suggest {value}, because {reason}.",
        "ar": "أقترح {value}، لأن {reason}.",
    },
    "explain_decision": {
        "en": "The decision was {outcome}, because {reason}.",
        "ar": "كان القرار {outcome}، لأن {reason}.",
    },
    "approved": {"en": "Approved. I will carry it out.", "ar": "تمت الموافقة. سأقوم بالتنفيذ."},
    "rejected": {"en": "Understood. I will not do it.", "ar": "مفهوم. لن أقوم بذلك."},
    "feedback_recorded": {
        "en": "Thank you — recorded as {kind}.",
        "ar": "شكراً لك — تم التسجيل باعتباره {kind}.",
    },
    "request_allowed": {
        "en": "That is allowed. Sending it for execution.",
        "ar": "هذا مسموح به. سيتم إرساله للتنفيذ.",
    },
    "request_denied": {
        "en": "I cannot do that, because {reason}.",
        "ar": "لا أستطيع فعل ذلك، لأن {reason}.",
    },
    "request_needs_approval": {
        "en": "That needs approval first, because {reason}.",
        "ar": "هذا يحتاج موافقة أولاً، لأن {reason}.",
    },
    "request_deferred": {
        "en": "I have prepared it but held it back, because {reason}.",
        "ar": "قمت بتجهيزه لكن أجّلته، لأن {reason}.",
    },
    "request_escalated": {
        "en": "That device is controlled by fixed safety rules, not by me.",
        "ar": "هذا الجهاز تتحكم به قواعد سلامة ثابتة، ولست أنا.",
    },
}


def phrase(key: str, locale: str = "en", **values: Any) -> str:
    """Render a phrase. Unknown keys return the key rather than raising."""
    entry = PHRASES.get(key)
    if entry is None:
        return key
    template = entry.get(locale) or entry.get("en") or key
    try:
        return template.format(**values)
    except (KeyError, IndexError):
        # A missing substitution should degrade to the template, not crash a
        # response the user is waiting for.
        return template
