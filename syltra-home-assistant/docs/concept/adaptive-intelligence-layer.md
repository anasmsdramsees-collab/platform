# SYLTRA — Adaptive Intelligence Layer

طبقة الذكاء التكيفي والتأهب للمخاطر

**LOCAL-FIRST · PRIVACY-PRESERVING · SAFETY-GOVERNED**

The target architecture as authored by the product owner. This file is the
source of truth for the design; it is reproduced here verbatim and is **not** a
description of what is currently implemented. See "Where the build actually
stands" at the bottom for that.

```mermaid
flowchart TB
    subgraph INPUT["مدخلات طبقة الذكاء"]
        A["بيانات الحساسات والأجهزة"]
        B["تفاعل المستخدم والأوامر"]
        C["الوقت، الموقع، الطقس، الإشغال"]
    end

    subgraph PIPE["معالجة البيانات على SYLTRA Edge"]
        D["ناقل الأحداث اللحظي"]
        E["تنظيف وتوحيد البيانات"]
        F["دمج بيانات الحساسات"]
        G["التوأم الرقمي للمنزل"]
    end

    subgraph CONTEXT["فهم الحالة والسياق"]
        H["محرك حالة المنزل"]
        I["محرك السياق"]
        J["تقدير الإشغال والنشاط"]
    end

    subgraph LEARNING["التعلم التكيفي"]
        K["اكتشاف الروتين المتكرر"]
        L["نموذج سلوك المستخدم"]
        M["نموذج التفضيلات"]
        N["خط الأساس الطبيعي للمنزل"]
        O["التعلم المحلي المستمر"]
    end

    subgraph DECISION["التنبؤ واتخاذ القرار"]
        P["محرك التنبؤ"]
        Q["كشف السلوك غير الطبيعي"]
        R["تقييم المخاطر"]
        S["محرك السياسات التكيفية"]
        T["مخطط السيناريوهات"]
    end

    subgraph SAFETY["طبقة الأمان الحاكمة"]
        U["قواعد سلامة ثابتة"]
        V["درجة الثقة"]
        W{"مستوى الخطر"}
    end

    subgraph RESPONSE["التأهب والاستجابة"]
        X["مراقبة مكثفة"]
        Y["تجهيز الأجهزة والسيناريو"]
        Z["تنبيه المستخدم وطلب التأكيد"]
        AA["استجابة طارئة آلية"]
    end

    subgraph ACTIONS["مخرجات التحكم"]
        AB["تشغيل السيناريوهات"]
        AC["إغلاق الغاز أو المياه"]
        AD["فصل الدوائر الخطرة"]
        AE["تشغيل الإنذار والكاميرات"]
        AF["فتح مخارج الطوارئ وإرسال التنبيه"]
    end

    subgraph FEEDBACK["الذاكرة والتغذية الراجعة"]
        AG["تقييم نتيجة القرار"]
        AH["ذاكرة قصيرة المدى"]
        AI["سجل الأنماط طويل المدى"]
        AJ["سجل الحوادث"]
    end

    A --> D
    B --> D
    C --> D
    D --> E --> F --> G

    G --> H
    G --> I
    H --> J
    I --> J

    J --> K
    K --> L
    L --> M
    G --> N
    M --> O
    N --> O

    O --> P
    G --> P
    P --> Q
    Q --> R
    M --> S
    R --> S
    S --> T

    T --> V
    R --> V
    U --> V
    V --> W

    W -->|"منخفض"| X
    W -->|"متوسط"| Y
    W -->|"يحتاج قراراً"| Z
    W -->|"حرج ومؤكد"| AA

    X --> AB
    Y --> AB
    Z --> AB
    AA --> AC
    AA --> AD
    AA --> AE
    AA --> AF

    AB --> AG
    AC --> AG
    AD --> AG
    AE --> AG
    AF --> AG

    AG --> AH
    AG --> AI
    AG --> AJ
    AH --> O
    AI --> O
    AJ --> U
```

## Properties the graph asserts

Reading the edges rather than the boxes:

1. **Safety is a gate, not a monitor.** Every path from decision to actuation
   runs `T/R → V → W`. There is no edge from the decision layer straight to the
   control outputs. Nothing actuates without passing the trust score and the
   risk classifier.

2. **Emergency actuation is exclusive to the top tier.** `X`, `Y` and `Z` all
   converge on `AB` (run scenarios) only. Gas/water cut-off, circuit isolation,
   alarm, and exits (`AC`–`AF`) hang off `AA` alone. A medium-risk or
   awaiting-confirmation path can never reach a valve or a breaker.

3. **Two feedback loops with different destinations.** Short-term memory and the
   long-term pattern log feed `O` (continuous local learning). The incident log
   feeds `U` (fixed safety rules). Experience tunes the learner; incidents harden
   the rules. They are deliberately not the same loop.

4. **The digital twin fans out three ways.** `G` feeds context (`H`, `I`), the
   normal baseline (`N`), and the prediction engine (`P`) directly. It is the
   single shared representation the whole core reads from.

5. **Preferences reach policy without passing through prediction.** `M → S` is a
   direct edge, parallel to `R → S`. Policy is shaped by what the resident
   prefers and by measured risk, independently.

## Where the build actually stands

Mapping the graph's ~30 nodes onto the current codebase.

| Node | Status | Notes |
|---|---|---|
| A sensor/device data | partial | Edge Agent discovers HA entities; `device_states` table |
| B user interaction | partial | SILA intent classification, commands API |
| C time/location/weather/occupancy | **absent** | no weather, location, or occupancy source |
| D real-time event bus | partial | MQTT is transport only, not an event bus in this role |
| E clean/normalise | partial | `state-translator.ts` maps HA states to capability/value |
| F sensor fusion | **absent** | |
| G digital twin | **absent** | state is per-device rows; no home model |
| H, I, J context layer | **absent** | |
| K, L, M, N, O learning layer | **absent** | nothing learns today |
| P prediction | **absent** | |
| Q anomaly detection | **absent** | |
| R risk assessment | **absent** | |
| S adaptive policy engine | partial | `AdaptiveService` compiles objectives → constraints → commands, rule-based, no learned input |
| T scenario planner | partial | `AdaptivePlan`/`PlanStep` is a plan *structure*; scenes in the UI are hardcoded |
| U, V, W safety layer | **absent** | commands go straight from planner to device |
| X, Y, Z, AA response tiers | **absent** | no tiering |
| AB run scenarios | partial | commands execute; UI scenes are mock |
| AC–AF emergency outputs | **absent** | see blocker below |
| AG outcome evaluation | **absent** | reconciliation compares desired vs observed but does not judge decision quality |
| AH, AI memory | **absent** | |
| AJ incident log | partial | `device_events` logs plan lifecycle, not incidents |

### Three things to resolve before building

**The AI Core is specified as local, and is currently in the cloud.** The graph
places the pipeline and the core on SYLTRA Edge, and the footer claims
LOCAL-FIRST and PRIVACY-PRESERVING. `AdaptiveService` runs in `backend/api` —
the cloud. The Edge Agent is a thin translator with no decision logic. Building
this as drawn means moving the core to the edge, or the local-first property is
not true.

**The emergency actuators do not exist in the device model.** The Edge Agent's
capability mapper covers `climate`, `light`, `switch`, `cover`, `lock`, `sensor`,
`binary_sensor`. There is no gas valve, water valve, circuit breaker, siren, or
exit release. Layer 8's emergency branch (`AC`–`AF`) has nothing to command until
those device types and their Home Assistant domains are modelled. This is the
hard blocker on the most safety-critical part of the design.

**Safety-critical actuation needs a failure story the graph does not yet cover.**
Cutting gas, isolating circuits and releasing exits are irreversible and
life-safety relevant. What happens when the edge is offline, when a sensor is
faulty, or when `V` is uncertain, is not specified — and defaults matter more
here than anywhere else in the system.
