# SYLTRA Platform UI/UX Guidelines

## Web Platform Design System and Interface Specification

Version: 1.0  
Date: 2026-08-18  
Scope: SYLTRA web platform only  
Excluded: mobile applications, SYLTRA Panel 3.5, SYLTRA Panel 11, TV interfaces, device firmware screens, public marketing website

---

## 0. Instructions to Claude Code

Read this document completely before implementing or changing any SYLTRA web-platform interface.

This file is the source of truth for the current web-platform UI and UX. If a general build specification conflicts with this document on platform-interface behavior, layout, styling, accessibility, interaction, Arabic RTL, or component design, follow this document and record the conflict.

### Mandatory implementation behavior

1. Do not create screens before establishing design tokens and shared components.
2. Do not use a generic admin template as the final design.
3. Do not expose, copy, re-skin, or imitate the Home Assistant frontend.
4. Do not use Home Assistant entities, service names, or internal language directly in customer-facing UI.
5. Build Arabic RTL and English LTR from the same component system.
6. Use semantic HTML and keyboard-accessible components.
7. Meet WCAG 2.2 AA as a minimum.
8. Use color, icon, text, and shape together for status communication.
9. Do not make safety-critical controls one-click actions.
10. Do not present AI recommendations as certain facts.
11. Every recommendation must show reason, confidence, expiry, permission state, and available feedback.
12. Every critical risk must show evidence source, freshness, state, and the system action taken or pending.
13. Never hide device offline, stale, unknown, or failed states.
14. Manual user action must remain visible and must override conflicting adaptive automation.
15. Do not add glassmorphism, decorative gradients, neon effects, oversized cards, or excessive animation.
16. Keep the platform premium, restrained, technical, and readable.
17. Use the approved SYLTRA icon and wordmark assets when provided. Do not redraw or reinterpret them.
18. Use `SYLTRA` exactly for the platform brand and `SILA` exactly for the intelligent interface.
19. Maintain a Storybook or equivalent component catalogue.
20. Add automated accessibility and visual-regression tests for shared components and primary screens.

### First implementation response

After reading this file, Claude Code must return:

1. An audit of the existing platform UI.
2. A list of conflicts with these guidelines.
3. A proposed token and component implementation plan.
4. The exact screens to implement first.
5. Accessibility and RTL test plans.

Do not redesign the entire platform in one uncontrolled change.

---

## 1. Product experience definition

The SYLTRA Platform is the web control and operations environment for smart homes, devices, intelligence, risks, energy, installations, users, and system health.

The interface must communicate five product qualities:

```text
Intelligent
Controlled
Reliable
Private
Premium
```

The platform must feel like an operating system for connected living, not a collection of unrelated dashboards.

### Core experience promise

At any moment, the user must understand:

- what is happening in the property;
- which devices are online, offline, stale, or in error;
- what SILA has learned or recommended;
- why an automation occurred;
- whether an action requires approval;
- whether a risk is possible, confirmed, being handled, or resolved;
- how much energy is being used;
- whether the local hub and cloud connection are healthy.

---

## 2. Current platform scope

This document covers the responsive web platform only.

### Included experiences

- authentication;
- organization and account workspace;
- properties and homes;
- rooms and zones;
- devices and capabilities;
- scenes and automations;
- SILA intelligence and recommendations;
- risk and safety centre;
- energy monitoring;
- installation projects;
- technician diagnostics;
- users, roles, and permissions;
- audit trail;
- system and hub health;
- platform settings;
- Arabic and English interface.

### Excluded experiences

- public website;
- e-commerce;
- consumer mobile application;
- smart-wall panels;
- television interface;
- wearable interface;
- voice hardware;
- packaging and industrial design;
- marketing graphics.

---

## 3. User roles

The UI must be role-aware. Hidden access is not authorization. Backend authorization remains mandatory.

### 3.1 Organization owner

Needs:

- portfolio overview;
- homes and installations;
- subscriptions and system status;
- user and role management;
- high-level risks and energy;
- audit access.

### 3.2 Platform administrator

Needs:

- organization configuration;
- hub and device management;
- policy configuration;
- user permissions;
- integrations;
- diagnostic access.

### 3.3 Operations user

Needs:

- property status;
- alerts and risk cases;
- open incidents;
- device availability;
- work queues;
- action history.

### 3.4 Installer and technician

Needs:

- installation projects;
- commissioning state;
- device discovery and assignment;
- signal, battery, firmware, and connectivity health;
- testing and handover;
- restricted diagnostic logs.

### 3.5 Household administrator

Needs:

- one property overview;
- rooms and devices;
- automations and recommendations;
- risk and energy;
- household users;
- privacy and consent.

### 3.6 Viewer

Needs:

- read-only status;
- no mutation controls;
- no access to sensitive diagnostics or private audit data.

---

## 4. Information architecture

### Primary navigation

```text
Overview
Properties
Rooms
Devices
Automations
SILA Intelligence
Risk Centre
Energy
Installations
Users and Roles
Audit Trail
System Health
Settings
```

Navigation items must be filtered by role and workspace scope.

### Navigation rules

- Use one persistent desktop sidebar.
- Use an expanded and collapsed state.
- Do not use two competing sidebars.
- Keep global workspace and property selection at the top.
- Place user, language, appearance, and sign-out controls in the account area.
- Use breadcrumbs only when hierarchy exceeds two levels.
- Preserve the user’s last valid workspace and property selection.
- Mirror navigation order and directional icons for Arabic RTL.
- Do not mirror universal symbols such as play, pause, power, media, check, warning, or brand marks.

---

## 5. Visual direction

### Design character

```text
Premium minimal
Technical clarity
Calm confidence
High information density with strong hierarchy
Restrained use of color
Real operational state over decorative presentation
```

### Avoid

- generic SaaS template appearance;
- excessive glass panels;
- permanent gradients behind content;
- bright cyan on every component;
- glowing borders;
- oversized dashboard cards;
- fake AI brain graphics;
- playful illustrations in operational views;
- rounded pill shapes for all controls;
- low-contrast grey text;
- charts used as decoration;
- status communicated by color alone;
- hidden table actions that appear only on hover;
- multiple competing primary buttons.

### 5.1 Approved identity assets for the web platform

The following supplied files are the visual identity references for this project:

```text
new logo.PNG              Primary SYLTRA logo lockup reference
instagram pp.PNG          Circular social/profile lockup reference
sila-icon.png             Primary SILA icon reference
sila-identity-sheet.png   SILA identity and interaction-state reference
syltra-app-icon.png       SYLTRA consumer app icon, excluded from the current web-platform scope
```

Asset-use rules:

- Preserve the approved SYLTRA master symbol and wordmark exactly.
- Do not redraw, simplify, stretch, recolor, rotate, crop, animate, or reinterpret the master logo.
- Do not replace the SYLTRA wordmark with ordinary typed text when an approved production asset is available.
- The supplied PNG files are visual references. Request or prepare approved transparent SVG assets before production release.
- Do not trace raster edges into an unapproved vector approximation.
- Do not use the circular `instagram pp.PNG` lockup inside the platform shell. It is a social/profile treatment.
- Do not use `syltra-app-icon.png` as the web-platform sidebar logo or favicon during the current scope. It belongs to the consumer app identity.
- Do not combine the SYLTRA symbol with the SILA icon.
- Do not place the SYLTRA master logo inside a generic app-icon container.
- Do not add Electric Cyan glow to the master SYLTRA logo.

### 5.2 Platform placement

Expanded sidebar:

- use the approved horizontal SYLTRA lockup without the tagline;
- keep a clear zone equal to at least the height of the symbol’s internal wave opening;
- never shrink the wordmark until its letterforms lose separation.

Collapsed sidebar:

- use the approved SYLTRA master symbol only;
- use a prepared transparent monochrome asset;
- do not use the circular social lockup.

Sign-in screen:

- use the primary SYLTRA logo lockup;
- the tagline may appear beneath the logo as `Smart Living. Seamlessly Connected` when approved for that release;
- do not place the tagline in the persistent application shell.

Browser favicon:

- use the master SYLTRA symbol only;
- provide approved 16px, 32px, 48px, SVG, and maskable variants;
- verify legibility at 16px;
- do not use the consumer app icon during the current platform scope.

Loading and system boot:

- use the master symbol without continuous glow or spinning;
- use a short neutral opacity or progress transition;
- do not animate the logo wave as a decorative loop.

### 5.3 SILA identity inside the platform

Use `sila-icon.png` and `sila-identity-sheet.png` as the identity references for SILA.

SILA is a product intelligence identity within SYLTRA, not the master company logo.

Allowed platform locations:

- SILA Intelligence navigation item;
- recommendation cards;
- explanation panels;
- approval requests;
- SILA conversation or intent panel;
- intelligence status and model-mode views.

Do not use the SILA icon for ordinary automation, device status, security, energy, settings, or platform navigation unrelated to intelligence.

Approved SILA interaction states:

```text
IDLE
LISTENING
THINKING
RESPONDING
```

State rules:

- `IDLE`: clean white icon with no active animation.
- `LISTENING`: restrained cyan halo or pulse.
- `THINKING`: controlled blue-cyan radial movement that does not loop indefinitely without active processing.
- `RESPONDING`: brighter cyan edge or response pulse, then return to idle.
- Respect `prefers-reduced-motion` by replacing motion with static state treatment.
- Do not use a generic sparkle icon as a substitute for SILA.
- Do not use the SILA glow treatment elsewhere in the platform.
- Keep the wordmark spelling exactly `SILA`.

### 5.4 Production asset requirement

Before production UI implementation is marked complete, the design-system asset directory must contain approved files similar to:

```text
assets/brand/syltra/syltra-lockup-light.svg
assets/brand/syltra/syltra-lockup-dark.svg
assets/brand/syltra/syltra-symbol-light.svg
assets/brand/syltra/syltra-symbol-dark.svg
assets/brand/syltra/favicon.svg
assets/brand/sila/sila-icon-primary.svg
assets/brand/sila/sila-icon-monochrome-light.svg
assets/brand/sila/sila-icon-monochrome-dark.svg
```

Do not generate these production SVGs automatically from the PNGs without visual review and product-owner approval.

---

## 6. Color system

The SYLTRA brand palette is Graphite Black, Sand White, and Electric Cyan.

Green is not a SYLTRA brand color. Green is permitted only as a semantic success or confirmed-safe status.

### 6.1 Core brand tokens

```css
--syltra-graphite-950: #080B0D;
--syltra-graphite-900: #0A0D10;
--syltra-graphite-850: #0E1317;
--syltra-graphite-800: #11171C;
--syltra-graphite-750: #151D23;
--syltra-graphite-700: #1C252C;
--syltra-graphite-600: #29343B;

--syltra-sand-50: #F7F4EC;
--syltra-sand-100: #EFEADF;
--syltra-sand-200: #DDD6C8;

--syltra-cyan-400: #59D6E6;
--syltra-cyan-500: #2BC4D9;
--syltra-cyan-600: #169DB0;
--syltra-cyan-700: #0E7281;
```

### 6.2 Semantic tokens

```css
--status-success: #22C55E;
--status-warning: #F59E0B;
--status-critical: #EF4444;
--status-info: #3B82F6;
--status-unknown: #7D8A92;
--status-offline: #64727A;
```

### 6.3 Dark theme

Dark theme is the primary platform experience.

```css
--background: #0A0D10;
--surface: #11171C;
--surface-raised: #151D23;
--surface-overlay: #1C252C;
--border: #29343B;
--border-strong: #3B4850;
--text-primary: #F7F4EC;
--text-secondary: #B5BEC3;
--text-tertiary: #89969D;
--text-disabled: #647078;
--accent: #2BC4D9;
--accent-hover: #59D6E6;
--accent-pressed: #169DB0;
--focus-ring: #59D6E6;
```

### 6.4 Light theme

```css
--background: #F5F3ED;
--surface: #FFFFFF;
--surface-raised: #FBFAF7;
--surface-overlay: #FFFFFF;
--border: #D7D3C9;
--border-strong: #B8B3A8;
--text-primary: #11171C;
--text-secondary: #4E5A61;
--text-tertiary: #6E7A80;
--text-disabled: #929DA2;
--accent: #0E7281;
--accent-hover: #169DB0;
--accent-pressed: #0A5661;
--focus-ring: #0E7281;
```

### 6.5 Color-use rules

- Electric Cyan is for selected state, primary action, live connection, and the main data series.
- Do not use cyan for success.
- Do not use red for ordinary destructive settings unless the action is truly destructive.
- Use amber for warning and pre-alert.
- Use red for confirmed critical risk, failed critical action, or destructive action.
- Use green only for confirmed success or safe completion.
- Use neutral grey for unknown, offline, disabled, or unavailable.
- Every semantic color must include text and icon support.
- Validate text contrast at 4.5:1 minimum for normal text.
- Validate essential icons, boundaries, and controls at 3:1 minimum.

---

## 7. Typography

### 7.1 Font families

Arabic:

```text
IBM Plex Sans Arabic
Fallback: Noto Sans Arabic, system sans-serif
```

English and numbers:

```text
Inter
Fallback: system-ui, sans-serif
```

Use tabular numerals for energy, temperature, time, device counts, metrics, and tables.

### 7.2 Type scale

```text
Display       32px / 40px / 600
Page title    28px / 36px / 600
Section title 22px / 30px / 600
Card title    18px / 26px / 600
Body large    16px / 26px / 400
Body          14px / 22px / 400
Label         13px / 20px / 500
Caption       12px / 18px / 400
Metric large  32px / 38px / 600, tabular
Metric        20px / 26px / 600, tabular
```

### 7.3 Typography rules

- Use no more than three weights: 400, 500, 600.
- Do not use all caps for Arabic.
- English utility labels may use sentence case, not all caps.
- Do not use letter spacing on Arabic text.
- Keep Arabic line height slightly larger than equivalent English text.
- Do not place long labels inside narrow pills.
- Do not use images of text.
- Keep technical identifiers such as entity IDs, serial numbers, IP addresses, and model versions LTR inside `<bdi>` or direction-isolated containers.

---

## 8. Spacing, radius, elevation, and density

### 8.1 Spacing scale

Use a 4px base unit.

```css
--space-1: 4px;
--space-2: 8px;
--space-3: 12px;
--space-4: 16px;
--space-5: 20px;
--space-6: 24px;
--space-8: 32px;
--space-10: 40px;
--space-12: 48px;
--space-16: 64px;
```

### 8.2 Radius

```css
--radius-sm: 6px;
--radius-md: 10px;
--radius-lg: 14px;
--radius-xl: 18px;
--radius-round: 999px;
```

Use round pills only for short statuses, filters, and compact segmented controls.

### 8.3 Elevation

- Use borders before shadows.
- Use subtle shadow only for popovers, dialogs, menus, and floating drawers.
- Do not put shadows around every card.
- Avoid inner glow and colored shadow.

### 8.4 Density

Support two density modes:

```text
Comfortable
Compact
```

Comfortable is the default. Compact is for tables and technician workflows.

---

## 9. Responsive layout

### 9.1 Target widths

```text
Desktop large: 1440px and above
Desktop:       1200px to 1439px
Tablet wide:   900px to 1199px
Minimum:       768px
```

The current platform is not required to provide a phone-optimized experience. It must remain readable at 768px without clipped content.

### 9.2 Desktop shell

```text
Sidebar expanded: 264px
Sidebar collapsed: 72px
Top bar: 64px
Content horizontal padding: 24px to 32px
Content vertical padding: 24px
Grid: 12 columns
Grid gap: 20px to 24px
```

### 9.3 Layout rules

- Use fluid content width for operational screens.
- Keep long-form settings and forms within a readable column.
- Avoid more than four metric cards in one row.
- Stack secondary panels below the primary view at narrower widths.
- Keep critical risk banners at the top of the content region.
- Do not hide essential actions behind horizontal scrolling.
- Tables may use controlled horizontal scrolling when columns cannot be reduced safely.
- Preserve sticky table headers for long operational tables.

---

## 10. Arabic RTL and bidirectional behavior

### 10.1 Document direction

For Arabic:

```html
<html lang="ar" dir="rtl">
```

For English:

```html
<html lang="en" dir="ltr">
```

### 10.2 CSS requirements

- Use logical properties: `margin-inline`, `padding-inline`, `inset-inline`, `border-inline`, `text-align: start`.
- Do not encode left and right into reusable layout components.
- Mirror sidebar placement, breadcrumb order, drawers, stepper direction, pagination, and directional arrows.
- Do not mirror power, play, pause, check, warning, device, product, or brand icons.
- Use `dir="auto"` for user-generated text fields where direction is unknown.
- Use `<bdi>` for serial numbers, email, IP, MAC address, entity ID, firmware version, and code.
- Keep chronological charts visually LTR while localizing labels and surrounding layout.
- In Arabic tables, primary text aligns to the right and numeric values remain tabular and direction-isolated.
- Test mixed Arabic, English, numbers, model names, room names, and device IDs.

### 10.3 Translation rules

- Translate meaning, not word order.
- Keep `SYLTRA` and `SILA` in Latin letters unless an approved Arabic lockup exists.
- Do not transliterate technical identifiers.
- Keep Arabic labels short and operational.
- Avoid unexplained English abbreviations in primary UI.

---

## 11. Iconography

### Style

- consistent outline icons;
- 1.5px to 2px stroke;
- rounded joins;
- no multicolor icons except risk illustrations where necessary;
- use 16px, 20px, and 24px sizes;
- use filled variant only for selected or critical state where supported.

### Rules

- Every icon-only button requires an accessible name and tooltip.
- Do not use an icon when text alone is clearer.
- Do not invent different icons for the same capability.
- Device icons must map to canonical SYLTRA capabilities.
- Risk icons must remain consistent across dashboard, list, detail, notifications, and audit.

---

## 12. Core components

Build and document these components before screens.

### 12.1 Buttons

Variants:

```text
Primary
Secondary
Ghost
Destructive
Critical confirmation
Icon button
```

Rules:

- One primary action per local action group.
- Minimum recommended control height: 44px.
- Button label must describe the action.
- Loading state preserves button width.
- Destructive action requires explicit context.
- Critical confirmation uses red only at the final confirmation step.

### 12.2 Inputs

Required:

```text
Text input
Number input
Search
Select
Multi-select
Combobox
Date and time
Checkbox
Radio group
Switch
Range
Textarea
Code or identifier field
```

Rules:

- Every field has a persistent visible label.
- Placeholder is an example, not the label.
- Help text and error text occupy predictable space.
- Validation must not rely on color.
- Switch is for immediate binary settings only.
- Use checkbox for selection and confirmation.

### 12.3 Cards

Use cards only for bounded content:

- metric;
- device;
- room;
- recommendation;
- risk summary;
- action result.

Do not place every section inside a card.

### 12.4 Tables

Required features:

- column headers;
- sorting;
- filtering;
- pagination or virtualization;
- row selection where needed;
- visible status;
- explicit actions;
- empty, loading, and error states;
- column customization only for advanced operational tables.

Rules:

- Keep the primary identifier in the first logical column.
- Align numbers to the end.
- Use tabular numerals.
- Avoid more than two lines in ordinary cells.
- Do not place essential actions only inside hover menus.
- Provide a row detail link.
- Use compact density only when the user selects it or the workflow requires it.

### 12.5 Status badge

Every badge includes:

- label;
- icon or shape;
- semantic color;
- accessible text.

Badges must not be interactive unless implemented as a button with a clear action.

### 12.6 Tabs

- Use for peer views of the same object.
- Do not use tabs as the main global navigation.
- Keep the active tab visible in RTL and LTR.
- Avoid more than six tabs without overflow handling.

### 12.7 Dialogs and drawers

Dialog:

- short decision;
- confirmation;
- small form.

Drawer:

- contextual detail;
- filter panel;
- multi-step side workflow.

Full page:

- complex settings;
- commissioning;
- installation;
- risk investigation.

### 12.8 Toasts

- Use for non-critical completion and transient system messages.
- Do not use a toast as the only record of failure.
- Critical risk uses persistent banner and Risk Centre entry.
- Include direct next action where useful.

### 12.9 Skeleton and progress

- Use skeletons for predictable content shapes.
- Use progress indicator for commissioning, firmware, backup, restore, and model training.
- Show stage and outcome for operations longer than a few seconds.
- Never show endless progress without cancel, timeout, or status information.

---

## 13. Domain components

### 13.1 Property status header

Contains:

- property name;
- local time;
- occupancy state;
- current mode;
- hub status;
- internet or cloud status;
- active risk count;
- last updated time.

### 13.2 Room card

Contains:

- room name;
- occupancy;
- temperature;
- humidity where available;
- lights on count;
- key active devices;
- risk or offline indicator;
- link to room detail.

Do not include every room metric in the card.

### 13.3 Device row or card

Contains:

- device name;
- device type icon;
- room;
- primary state;
- availability;
- battery where relevant;
- last update;
- active fault;
- firmware status;
- primary safe control where appropriate.

### 13.4 SILA recommendation card

Contains:

- proposed action;
- plain-language reason;
- confidence presented as a qualified level plus optional percentage;
- evidence summary;
- created and expiry times;
- permission state;
- affected devices;
- approve;
- reject;
- not now;
- modify;
- never repeat;
- details link.

Do not present confidence as certainty. Do not use phrases such as “SILA knows” when the state is inferred.

### 13.5 Context indicator

Contains:

- inferred context;
- scope;
- confidence;
- evidence count;
- freshness;
- producing rule or model;
- status if suspended or stale.

### 13.6 Risk case card

Contains:

- category;
- state;
- severity;
- location;
- detected time;
- evidence sources;
- evidence freshness;
- fixed alarm confirmation status;
- system action;
- user action required;
- link to timeline.

### 13.7 Action timeline

Shows:

```text
Recommendation
Policy decision
Approval
Dispatch
Device response
Verification
Manual override
Final outcome
```

Each item contains timestamp, actor, reason, and correlation ID access for authorized technicians.

### 13.8 Hub health panel

Contains:

- online state;
- uptime;
- local services health;
- CPU, memory, disk, and temperature;
- Zigbee, Thread, MQTT, and Matter status;
- database and event-stream health;
- cloud connection;
- last backup;
- software version;
- pending update;
- critical fault.

---

## 14. Device states

Use these normalized platform states:

```text
ONLINE
OFFLINE
STALE
UNKNOWN
UPDATING
DEGRADED
ERROR
DISABLED
COMMISSIONING
REMOVED
```

### Display rules

- `ONLINE`: neutral or semantic success, not bright green everywhere.
- `OFFLINE`: grey status plus last seen time.
- `STALE`: amber status plus age of data.
- `UNKNOWN`: neutral grey and explanation.
- `UPDATING`: progress with version.
- `DEGRADED`: amber status and affected capability.
- `ERROR`: red only when operation is materially impaired.
- `DISABLED`: neutral state with who disabled it and when.
- `COMMISSIONING`: blue or cyan progress state.
- `REMOVED`: historical or archived state, never shown as active.

---

## 15. Risk states

Use the same state model everywhere:

```text
NORMAL
WATCH
PRE_ALERT
CONFIRMED
ACTION_IN_PROGRESS
RECOVERY
CLOSED
```

Arabic labels:

```text
NORMAL             طبيعي
WATCH              مراقبة
PRE_ALERT          تأهب
CONFIRMED          خطر مؤكد
ACTION_IN_PROGRESS استجابة جارية
RECOVERY           تعافٍ ومتابعة
CLOSED             مغلق
```

### Risk presentation rules

- `NORMAL` does not require permanent green banners.
- `WATCH` uses neutral information or amber depending on severity.
- `PRE_ALERT` uses amber and explains what the system is preparing.
- `CONFIRMED` uses persistent red treatment and evidence source.
- `ACTION_IN_PROGRESS` shows the exact response and verification state.
- `RECOVERY` shows remaining checks.
- `CLOSED` preserves the final report and timeline.
- AI anomaly and certified alarm must never look identical.
- Display “possible”, “inferred”, or “confirmed” explicitly.

---

## 16. Adaptive-intelligence states

Use:

```text
DISABLED
OBSERVE
SHADOW
RECOMMEND
APPROVAL_REQUIRED
AUTHORIZED_AUTOMATION
SUSPENDED
```

Arabic labels:

```text
DISABLED              متوقف
OBSERVE               يتعلم بالمراقبة
SHADOW                اختبار غير منفذ
RECOMMEND              يقدم اقتراحات
APPROVAL_REQUIRED      يتطلب موافقة
AUTHORIZED_AUTOMATION  أتمتة مصرح بها
SUSPENDED              معلق
```

The UI must always show the active mode and what the mode permits.

---

## 17. Primary platform screens

### 17.1 Sign in

Required:

- SYLTRA identity;
- email or organization login;
- password manager support;
- show password;
- recovery;
- accessible error handling;
- language selection;
- no visual CAPTCHA unless an accessible alternative exists.

### 17.2 Overview

Order:

1. Persistent active-risk area only when needed.
2. Portfolio or property status.
3. Hub and device health.
4. Occupancy and current context.
5. SILA recommendations requiring action.
6. Energy snapshot.
7. Recent actions and incidents.

Do not fill the overview with decorative KPIs.

### 17.3 Properties

List view:

- property name;
- city or location label;
- occupancy;
- hub status;
- device health;
- active risks;
- energy summary;
- last update;
- owner or workspace.

Support search, status filters, and role-aware actions.

### 17.4 Property detail

Header:

- property status;
- home mode;
- active risks;
- hub and connection health.

Sections:

- room overview;
- devices needing attention;
- current contexts;
- recommendations;
- active automations;
- energy;
- recent timeline.

### 17.5 Room detail

Show:

- room state;
- occupancy;
- environment;
- controllable devices;
- contexts;
- active automation;
- room energy if available;
- recent history;
- problems.

### 17.6 Devices

Default to table for operations. Provide cards only when visual device recognition adds value.

Filters:

```text
Property
Room
Device type
Protocol
Availability
Battery
Firmware
Risk
Installation status
```

### 17.7 Device detail

Sections:

- current state;
- controls;
- capabilities;
- room and property;
- connection and signal;
- battery and power;
- firmware;
- event history;
- automations using the device;
- diagnostics;
- permissions;
- maintenance and replacement.

Hide low-level identifiers from ordinary users and expose them to authorized technicians.

### 17.8 Automations

List fields:

- name;
- property;
- trigger summary;
- condition summary;
- action summary;
- enabled state;
- safety class;
- last run;
- success or failure;
- owner;
- source: manual, suggested, adaptive, fixed safety.

Builder requirements:

- clear trigger, condition, and action stages;
- readable summary before save;
- conflict and risk validation;
- test mode;
- dry run where supported;
- version history;
- rollback;
- Arabic RTL support.

### 17.9 SILA Intelligence

Sections:

- current learning mode;
- active recommendations;
- learned routines;
- preference summary;
- suspended models;
- feedback history;
- explanation and evidence;
- privacy and learning controls.

Do not display raw model internals to household users. Provide deeper technical view to authorized administrators.

### 17.10 Risk Centre

Default order:

1. Confirmed active risks.
2. Actions in progress.
3. Pre-alert cases.
4. Watch cases.
5. Recovery.
6. Closed history.

Provide category, property, room, severity, state, evidence, freshness, responsible actor, and timeline filters.

### 17.11 Energy

Show:

- current power;
- daily, weekly, monthly consumption;
- comparison to the user’s own baseline;
- property, room, circuit, and device breakdown where available;
- anomalies;
- cost only when tariff data exists;
- optimization recommendations;
- data completeness and freshness.

Never fabricate cost, savings, carbon, or device-level estimates.

### 17.12 Installations

Stages:

```text
Planned
Site survey
Hub installed
Devices discovered
Devices assigned
Connectivity tested
Automations tested
Safety checks
Customer handover
Completed
```

Show progress, blockers, technician, property, scheduled date, device count, test status, and handover evidence.

### 17.13 Users and roles

Show:

- name;
- organization;
- properties;
- role;
- permission summary;
- last access;
- authentication status;
- invitation status.

Sensitive permission changes require confirmation and audit reason.

### 17.14 Audit Trail

Fields:

- timestamp;
- actor;
- role;
- property;
- event category;
- action;
- target;
- reason;
- result;
- correlation ID for authorized roles.

Audit history is append-only in UI. Do not present edit or delete actions.

### 17.15 System Health

Show:

- hub fleet status;
- services health;
- message backlog;
- database health;
- software versions;
- update status;
- backups;
- integration health;
- model health;
- cloud connection;
- active incidents.

---

## 18. Charts and data visualization

### Rules

- Use charts only when trends, comparison, composition, or distribution matter.
- Directly label important values.
- Use Electric Cyan as the primary series.
- Use semantic colors only for semantic states.
- Do not assign every room or device a decorative color.
- Do not rely on hover for essential values.
- Provide table or summary alternative for critical data.
- Include units on axes and tooltips.
- Show data gaps instead of interpolating silently.
- Show freshness and timezone.
- Use accessible patterns, labels, or shapes with color.
- Avoid 3D charts.
- Avoid gauges unless a bounded real-time measure materially benefits from one.
- Avoid pie charts with many categories.

### Recommended chart types

```text
Energy over time: line or area chart
Device availability: stacked bar
Risk timeline: event timeline
Room comparison: horizontal bar
Automation outcomes: stacked bar
Model acceptance: line or segmented bar
Current home flow: compact Sankey only when source-to-load flow is meaningful
```

---

## 19. Motion and feedback

### Timing tokens

```css
--motion-fast: 120ms;
--motion-standard: 180ms;
--motion-slow: 240ms;
```

### Rules

- Use motion to show state change and spatial relationship.
- Do not loop decorative motion.
- Avoid parallax and floating backgrounds.
- Do not animate critical alerts in a way that impairs reading.
- Respect `prefers-reduced-motion`.
- Keep progress animation calm and bounded.
- Provide immediate pressed, loading, success, and error feedback for actions.

---

## 20. Empty, loading, error, offline, and stale states

Every major screen must implement:

```text
Initial loading
Incremental loading
Empty first-use state
Empty filtered state
Partial-data state
Offline state
Stale-data state
Permission-denied state
Service failure
Recoverable action failure
Permanent action failure
```

### Rules

- Explain what happened.
- State what data is affected.
- Show last successful update when relevant.
- Offer one clear recovery action.
- Preserve unaffected data.
- Never replace a detailed failure with “Something went wrong”.
- Do not show a safe or normal state when data is unavailable.

---

## 21. Safety-critical UX

### Critical action confirmation

For locks, valves, breakers, sirens, security modes, and emergency responses:

1. Show target device and location.
2. Show current state.
3. Show intended new state.
4. Explain expected impact.
5. Show required permission.
6. Show whether reversal is supported.
7. Require explicit confirmation.
8. Record reason where policy requires it.
9. Show dispatch and verification progress.
10. Show final verified state or failure.

### Prohibited patterns

- no swipe-only confirmation;
- no hidden confirmation text;
- no preselected dangerous option;
- no color-only risk state;
- no generic “OK” for critical confirmation;
- no silent retry of non-retryable safety actions;
- no auto-dismissed critical result;
- no AI-generated text as the only safety explanation.

---

## 22. Accessibility requirements

Minimum target: WCAG 2.2 AA.

### Required

- normal text contrast of at least 4.5:1;
- essential non-text component contrast of at least 3:1;
- visible keyboard focus;
- keyboard operation for all functions;
- no keyboard traps;
- logical heading hierarchy;
- landmarks;
- labels and descriptions for forms;
- accessible error association;
- status announcements through appropriate live regions;
- accessible dialogs with focus management;
- reduced motion support;
- zoom to 200% without loss of function;
- 24 by 24 CSS pixel WCAG minimum targets, with 44 by 44 as the SYLTRA recommended control target;
- text and layout that tolerate user text-spacing adjustments;
- no authentication puzzle dependent on memory or transcription alone;
- drag operations must have a non-drag alternative.

### Automated tests

- axe or equivalent accessibility scan;
- keyboard smoke tests;
- contrast checks for token pairs;
- RTL visual regression;
- focus order tests for key workflows.

### Manual tests

- keyboard-only navigation;
- screen reader smoke test;
- 200% browser zoom;
- Windows high contrast or forced colors;
- reduced motion;
- Arabic screen reader reading order;
- mixed bidirectional content.

---

## 23. Content design

### Voice

```text
Direct
Calm
Precise
Explainable
Non-alarming until evidence confirms risk
```

### Rules

- Start with the user outcome.
- Use active voice.
- Use specific device and room names.
- Distinguish inferred from confirmed.
- Explain what the system did and why.
- Do not blame the user.
- Do not overstate AI confidence.
- Avoid technical codes in household-facing text.
- Preserve technical detail in the authorized diagnostic view.

### Example

Avoid:

```text
Automation failed.
```

Use:

```text
لم يستجب مكيف المجلس خلال 10 ثوانٍ. لم نُعد المحاولة لأن الجهاز غير متصل.
```

Avoid:

```text
SILA detected danger.
```

Use:

```text
رصدت SILA ارتفاعاً غير معتاد في قراءة حساس الغاز. لم يتأكد الإنذار بعد، وتم رفع حالة المراقبة.
```

---

## 24. Design tokens and code structure

Create platform tokens as the single source of truth.

Suggested structure:

```text
apps/local-console/
├── src/
│   ├── app/
│   ├── components/
│   │   ├── primitives/
│   │   ├── layout/
│   │   ├── data-display/
│   │   ├── forms/
│   │   ├── feedback/
│   │   └── domain/
│   ├── features/
│   │   ├── overview/
│   │   ├── properties/
│   │   ├── rooms/
│   │   ├── devices/
│   │   ├── automations/
│   │   ├── intelligence/
│   │   ├── risks/
│   │   ├── energy/
│   │   ├── installations/
│   │   ├── users/
│   │   ├── audit/
│   │   └── system-health/
│   ├── design-system/
│   │   ├── tokens/
│   │   ├── themes/
│   │   ├── icons/
│   │   └── typography/
│   ├── i18n/
│   │   ├── ar/
│   │   └── en/
│   └── tests/
```

Required token outputs:

```text
tokens.json
tokens.css
dark-theme.css
light-theme.css
typography.css
motion.css
```

Do not hardcode brand or semantic colors inside feature components.

---

## 25. Component documentation

Every shared component story or documentation page must include:

- purpose;
- variants;
- sizes;
- dark and light themes;
- Arabic RTL and English LTR;
- keyboard behavior;
- accessibility name and role;
- loading state;
- disabled state;
- error state;
- long text;
- mixed-direction text;
- responsive behavior;
- do and do-not examples.

Priority components:

```text
AppShell
Sidebar
TopBar
WorkspaceSelector
PropertySelector
PageHeader
StatusBadge
Metric
DataTable
FilterBar
Search
FormField
Button
Dialog
Drawer
Toast
RiskBanner
DeviceStatus
RoomCard
DeviceRow
RecommendationCard
ContextIndicator
RiskCaseCard
ActionTimeline
HubHealthPanel
EnergyChart
EmptyState
ErrorState
StaleDataNotice
```

---

## 26. Implementation phases

### Phase UI-0: Audit and tokens

Deliver:

- existing UI audit;
- design token files;
- typography;
- dark and light themes;
- RTL foundation;
- accessibility baseline;
- component catalogue setup.

Acceptance:

- no feature component contains hardcoded brand color;
- Arabic and English direction switch works;
- token contrast checks pass;
- themes work without layout changes.

### Phase UI-1: Shell and primitives

Deliver:

- application shell;
- navigation;
- workspace and property selection;
- buttons;
- inputs;
- status;
- dialogs;
- drawers;
- tables;
- loading and error primitives.

Acceptance:

- keyboard navigation passes;
- minimum target size passes;
- Arabic and English visual regression passes;
- 768px layout remains usable.

### Phase UI-2: Core operational screens

Deliver:

- Overview;
- Properties;
- Property detail;
- Rooms;
- Devices;
- Device detail;
- System Health.

Acceptance:

- real API contracts or deterministic fixtures;
- all data states implemented;
- role-based views tested;
- stale and offline states visible.

### Phase UI-3: Intelligence and action screens

Deliver:

- SILA Intelligence;
- recommendations;
- contexts;
- feedback;
- automation list and builder;
- action timeline.

Acceptance:

- inferred and confirmed states are distinguishable;
- recommendation reason and confidence are visible;
- SILA cannot bypass approval or policy UI;
- manual override is visible.

### Phase UI-4: Risk and energy

Deliver:

- Risk Centre;
- risk detail and timeline;
- critical action verification;
- Energy dashboard;
- anomalies;
- data-quality indicators.

Acceptance:

- all risk states tested;
- no critical action is one-click;
- no color-only risk communication;
- charts expose units, gaps, freshness, and accessible summaries.

### Phase UI-5: Installations, users, audit, and settings

Deliver:

- installation projects;
- commissioning workflow;
- users and roles;
- audit trail;
- privacy and platform settings.

Acceptance:

- permission changes require confirmation and audit reason;
- commissioning stages are recoverable;
- audit history is read-only;
- Arabic RTL workflow passes.

### Phase UI-6: Hardening

Deliver:

- full accessibility pass;
- visual regression;
- localization review;
- performance optimization;
- error recovery;
- documentation;
- component adoption audit.

Acceptance:

- WCAG 2.2 AA audit has no unresolved critical issue;
- primary workflows pass keyboard and screen reader smoke tests;
- no duplicated local component replaces a shared component without reason;
- no unresolved RTL layout defect;
- loading, empty, error, offline, stale, and permission states exist for every primary screen.

---

## 27. Definition of done

The SYLTRA Platform web UI is complete only when:

1. Dark and light themes use shared tokens.
2. Arabic RTL and English LTR use the same components.
3. Navigation adapts by role and workspace.
4. Overview shows operational priorities, not decorative KPIs.
5. Device and hub health states are explicit.
6. SILA recommendations show reason, confidence, expiry, and feedback.
7. Risk states distinguish possible, inferred, and confirmed.
8. Critical controls use confirmation and verification flows.
9. Energy charts show units, time, freshness, and data gaps.
10. Every primary screen has loading, empty, partial, offline, stale, permission, and error states.
11. Shared components are documented.
12. Accessibility automation and manual smoke tests pass.
13. Visual regression covers dark, light, Arabic, English, and 768px layouts.
14. No Home Assistant customer-facing UI or terminology is exposed.
15. No unapproved logo redraw or brand icon is created.
16. No green is used as a brand color.
17. No safety-critical operation depends on AI text or a one-click control.
18. The interface reflects the real backend state and does not fabricate success.

---

## 28. Reference standards

- WCAG 2.2 target size minimum: https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html
- WCAG 2.2 enhanced target size: https://www.w3.org/WAI/WCAG22/Understanding/target-size-enhanced.html
- WCAG 2.2 contrast minimum: https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html
- WCAG 2.2 focus appearance: https://www.w3.org/WAI/WCAG22/Understanding/focus-appearance.html
- W3C structural RTL markup: https://www.w3.org/International/questions/qa-html-dir.en.html

---

## 29. Command to Claude Code

Use this command after placing the file in the project root:

```text
Read SYLTRA_Platform_UI_UX_Guidelines.md completely. Audit the current SYLTRA web platform against it. Do not redesign screens yet. First implement Phase UI-0, create the design tokens, themes, RTL foundation, accessibility baseline, and component catalogue. Run all acceptance tests, update IMPLEMENTATION_STATUS.md, then report the results and proposed Phase UI-1 plan.
```
