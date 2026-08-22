# SYLTRA Cloud Code Max Master Build Prompt
## Home Assistant → SYLTRA Cloud → SYLTRA Adaptive → Hub → Physical Devices

Version: 1.0
Project: SYLTRA | سيلترا
Platform: SYLTRA Adaptive
AI Assistant: SILA
Tagline: Smart Living, Seamlessly Connected.

---

# 01. مهمة المشروع

أنت تعمل كمهندس برمجيات رئيسي، مهندس Cloud، مهندس IoT، مهندس Edge، مهندس أمن، ومهندس DevOps لبناء Prototype إنتاجي قابل للتوسع لمنصة SYLTRA.

الهدف:

بناء بنية برمجية كاملة تبدأ من SYLTRA Cloud وتنتهي بربط SYLTRA Hub مع Home Assistant والأجهزة الذكية.

لا تبنِ نظامًا تجريبيًا منفصلًا عن المعمارية النهائية.

ابنِ MVP مرتبًا بحيث يمكن تطويره لاحقًا إلى منتج تجاري.

---

# 02. القرار المعماري الأساسي

Home Assistant هو طبقة Edge وDevice Integration.

SYLTRA هي طبقة المنصة والذكاء.

لا تجعل SYLTRA تعتمد مباشرة على Home Assistant داخل Cloud.

استخدم:

```text
SYLTRA Cloud
      |
SYLTRA Edge Agent
      |
Home Assistant
      |
Matter / Zigbee / Z-Wave / MQTT / Wi-Fi / BLE
      |
Physical Devices
```

الهدف هو إمكانية استبدال Home Assistant مستقبلًا دون إعادة بناء SYLTRA Cloud أو SYLTRA Adaptive Core.

---

# 03. القاعدة الذهبية

لا تسمح لـ SILA أو أي LLM بإرسال أوامر مباشرة إلى الأجهزة.

التدفق الإلزامي:

```text
User
  ↓
SILA
  ↓
Intent
  ↓
Policy Engine
  ↓
SYLTRA Adaptive Core
  ↓
Plan
  ↓
Validation
  ↓
Execution Engine
  ↓
SYLTRA Edge Agent
  ↓
Home Assistant
  ↓
Device
```

---

# 04. نطاق MVP

يجب أن يدعم الإصدار الأول:

- إنشاء حساب.
- تسجيل الدخول.
- Multi-tenancy.
- إنشاء Property.
- إنشاء Building.
- إنشاء Rooms.
- تسجيل Hub.
- ربط Home Assistant.
- اكتشاف الأجهزة.
- مزامنة الأجهزة.
- توحيد Capabilities.
- قراءة State.
- إرسال Commands.
- استقبال Events.
- Local control.
- Cloud control.
- Basic Automation.
- State Engine.
- Basic Adaptive Core.
- Energy telemetry.
- App/API readiness.
- Admin dashboard.
- Device health.
- Audit logs.

---

# 05. الأجهزة الأولية

لا تبدأ بعدد كبير من الأجهزة.

استخدم ثلاثة إلى أربعة أنواع:

```text
Temperature Sensor
Motion Sensor
Smart Switch
AC Controller
```

يجب دعم Virtual Devices للاختبار قبل توصيل Hardware حقيقي.

---

# 06. Architecture

```text
                         SYLTRA CLOUD
                              |
                    +---------+---------+
                    |                   |
                API Gateway        WebSocket
                    |
          +---------+----------+
          |                    |
      Identity             Core APIs
          |                    |
          +---------+----------+
                    |
          +---------+----------------------+
          |         |          |           |
       Devices   Buildings   State     Adaptive
          |         |          |           |
          +---------+----------+-----------+
                    |
              Event / Command
                    |
             SYLTRA EDGE AGENT
                    |
             HOME ASSISTANT
                    |
       +------------+-------------+
       |            |             |
     Matter      Zigbee        Z-Wave
       |            |             |
       +------------+-------------+
                    |
               DEVICES
```

---

# 07. Repository

أنشئ Monorepo:

```text
syltra-platform/
├── apps/
│   ├── admin/
│   ├── web/
│   └── installer/
│
├── services/
│   ├── api/
│   ├── identity/
│   ├── tenants/
│   ├── buildings/
│   ├── devices/
│   ├── state/
│   ├── automation/
│   ├── adaptive/
│   ├── energy/
│   ├── notifications/
│   ├── audit/
│   └── firmware/
│
├── edge/
│   └── syltra-edge-agent/
│
├── integrations/
│   └── home-assistant/
│
├── packages/
│   ├── capability-model/
│   ├── device-model/
│   ├── event-schema/
│   ├── command-schema/
│   ├── auth/
│   └── shared/
│
├── infrastructure/
│   ├── docker/
│   ├── terraform/
│   ├── monitoring/
│   └── environments/
│
├── docs/
└── tests/
```

إذا كانت بيئة Cloud Code Max تفرض هيكلًا مختلفًا، حافظ على نفس الحدود المنطقية.

---

# 08. Technology Baseline

استخدم Stack بسيط وقابل للتوسع:

```text
Backend:
TypeScript + NestJS

Database:
PostgreSQL

Cache:
Redis

Device Messaging:
MQTT

Realtime:
WebSocket

Frontend:
Next.js

Mobile readiness:
REST/WebSocket API first

Containers:
Docker

Testing:
Unit + Integration + E2E

Infrastructure:
Terraform

Local development:
Docker Compose
```

لا تستخدم Kubernetes في أول MVP إلا إذا كانت البيئة تفرضه.

---

# 09. Environment

أنشئ:

```text
development
staging
production
```

لا تضع secrets داخل Git.

استخدم:

```text
.env.example
```

مع Secret Manager في بيئة الإنتاج.

---

# 10. Database

أنشئ PostgreSQL Schema.

الجداول الأساسية:

```text
users
organizations
memberships
roles
permissions
properties
buildings
floors
zones
rooms
hubs
devices
device_capabilities
device_states
device_events
device_commands
automations
automation_runs
adaptive_goals
adaptive_plans
adaptive_actions
energy_readings
notifications
audit_logs
firmware_versions
device_credentials
```

كل Entity تجاري يجب أن يرتبط بـ tenant أو organization حسب الحاجة.

---

# 11. Multi-Tenancy

كل طلب API يجب أن يحمل Context للمؤسسة.

يجب منع:

```text
Tenant A → Tenant B data
```

اختبارات العزل مطلوبة.

مثال:

```text
Organization
  |
Property
  |
Building
  |
Room
  |
Device
```

---

# 12. Identity

نفذ:

- Email/password.
- Session management.
- Refresh tokens.
- Role-based access.
- MFA readiness.
- API tokens.
- Service identity.

Roles:

```text
Owner
Admin
Installer
Resident
Guest
Developer
Service
```

---

# 13. Device Capability Model

لا تعتمد على أسماء الأجهزة.

أنشئ Capability Model.

مثال HVAC:

```json
{
  "type": "hvac",
  "capabilities": [
    "power",
    "temperature",
    "mode",
    "fan_speed"
  ]
}
```

مثال Light:

```json
{
  "type": "light",
  "capabilities": [
    "power",
    "brightness"
  ]
}
```

مثال Sensor:

```json
{
  "type": "temperature_sensor",
  "capabilities": [
    "temperature"
  ]
}
```

---

# 14. Device Abstraction

أنشئ طبقة:

```text
Manufacturer Device
        ↓
Home Assistant Entity
        ↓
SYLTRA Adapter
        ↓
SYLTRA Device Model
        ↓
SYLTRA Capability Model
```

لا تسمح لـ Adaptive Core بمعرفة Home Assistant entity IDs.

مثال ممنوع داخل Core:

```text
climate.living_room
```

مثال صحيح:

```text
device_id = AC-LIVING-01
capability = temperature
```

---

# 15. SYLTRA Edge Agent

أنشئ خدمة مستقلة:

```text
syltra-edge-agent
```

مسؤولياتها:

- تسجيل Hub.
- Authentication.
- الاتصال بالـ Cloud.
- الاتصال بـ Home Assistant.
- Device discovery.
- State sync.
- Event sync.
- Command execution.
- Offline queue.
- Retry.
- Health reporting.
- Secure configuration.
- OTA readiness.

---

# 16. Edge Agent Configuration

مثال:

```yaml
cloud:
  api_url: ${SYLTRA_API_URL}
  tenant_id: ${SYLTRA_TENANT_ID}
  hub_id: ${SYLTRA_HUB_ID}

home_assistant:
  url: ${HA_URL}
  token: ${HA_TOKEN}

mqtt:
  broker: ${MQTT_BROKER}
```

لا تحفظ tokens داخل source code.

---

# 17. Home Assistant Integration

أنشئ SYLTRA Integration منفصلة.

الوظائف:

```text
Home Assistant
       |
SYLTRA Integration
       |
SYLTRA Edge Agent
```

يجب أن تستطيع Integration:

- قراءة entities.
- قراءة states.
- استقبال state changes.
- تنفيذ service calls.
- اكتشاف capabilities.
- إرسال device metadata.
- الإبلاغ عن unavailable devices.

---

# 18. Home Assistant API Boundary

لا تجعل Cloud يتصل بـ Home Assistant مباشرة.

ممنوع:

```text
Cloud → HA
```

المعتمد:

```text
Cloud
 ↓
Edge Agent
 ↓
HA
```

---

# 19. Device Discovery

عند تسجيل Hub:

```text
Hub Registration
 ↓
Connect Home Assistant
 ↓
Discover Entities
 ↓
Normalize
 ↓
Map Capabilities
 ↓
Create SYLTRA Devices
 ↓
Assign Rooms
 ↓
Sync State
```

يجب أن تكون العملية idempotent.

لا تنشئ جهازًا مكررًا عند إعادة المزامنة.

---

# 20. Device State

لكل جهاز:

```text
device_id
capability
value
unit
source
timestamp
quality
```

مثال:

```json
{
  "device_id": "AC-LIVING-01",
  "capability": "temperature",
  "value": 27,
  "unit": "celsius",
  "source": "home_assistant",
  "quality": "valid"
}
```

---

# 21. Event Model

أنشئ Events:

```text
DeviceDiscovered
DeviceUpdated
DeviceConnected
DeviceDisconnected
StateChanged
TemperatureChanged
MotionDetected
EnergyUpdated
CommandRequested
CommandExecuted
CommandFailed
AutomationTriggered
PlanCreated
PlanExecuted
PlanFailed
```

كل Event:

```json
{
  "event_id": "uuid",
  "tenant_id": "uuid",
  "source_id": "uuid",
  "type": "StateChanged",
  "timestamp": "ISO-8601",
  "correlation_id": "uuid",
  "payload": {}
}
```

---

# 22. Command Model

```json
{
  "command_id": "uuid",
  "device_id": "AC-LIVING-01",
  "capability": "temperature",
  "action": "set",
  "value": 24,
  "requested_by": "adaptive-core",
  "correlation_id": "uuid"
}
```

حالات الأمر:

```text
PENDING
SENT
ACKNOWLEDGED
SUCCEEDED
FAILED
TIMEOUT
CANCELLED
```

---

# 23. State Engine

أنشئ:

```text
Observed State
Current State
Desired State
Expected State
```

لا تخلط بينها.

مثال:

```text
Observed = 27°C
Desired = 24°C
Expected = 24°C
```

---

# 24. Context Engine

أنشئ Context Object:

```json
{
  "time": {},
  "weather": {},
  "occupancy": {},
  "location": {},
  "energy": {},
  "devices": {},
  "user_preferences": {},
  "security": {}
}
```

ابدأ بالبيانات المتاحة محليًا.

---

# 25. Adaptive Core

أنشئ Service:

```text
adaptive-core
```

وظائفه:

```text
createGoal()
buildDesiredState()
generatePlans()
validatePlan()
executePlan()
observeResult()
reconcile()
replan()
```

---

# 26. Adaptive Loop

نفذ:

```text
Sense
 ↓
Context
 ↓
Goal
 ↓
Desired State
 ↓
Plan
 ↓
Validate
 ↓
Execute
 ↓
Observe
 ↓
Compare
 ↓
Reconcile
 ↓
Adapt
```

---

# 27. Constraints

أضف Constraint Engine.

القيود الأولية:

```text
comfort
energy
security
device_availability
user_preferences
time
```

مثال:

```json
{
  "objective": "comfort",
  "constraints": [
    {
      "type": "temperature_min",
      "value": 23
    },
    {
      "type": "temperature_max",
      "value": 25
    }
  ]
}
```

---

# 28. Basic Adaptive Scenario

ابنِ أول سيناريو:

## Comfort + Energy

البيئة:

```text
Living Room
Temperature Sensor
Motion Sensor
AC Controller
Energy Meter
```

الهدف:

الحفاظ على راحة الغرفة مع تقليل تشغيل AC غير الضروري.

---

# 29. Reconciliation

بعد تنفيذ الأمر:

```text
Expected State
      vs
Observed State
```

إذا لم يتحقق الهدف:

```text
Device unavailable
OR
User intervention
OR
Environmental change
OR
Command failure
OR
Capability mismatch
```

ثم أعد التخطيط.

---

# 30. Automation

ابدأ بـ Rules بسيطة.

مثال:

```text
IF occupancy = false
AND duration > 20 minutes
THEN reduce HVAC
```

لكن اجعل Automation وAdaptive Core طبقتين منفصلتين.

---

# 31. Energy

أنشئ:

```text
energy_readings
energy_aggregation
energy_baseline
energy_events
```

ابدأ بالقياس فقط.

ثم أضف optimization.

---

# 32. SILA Integration

في هذه المرحلة لا تحتاج إلى تدريب نموذج خاص.

أنشئ API:

```text
POST /v1/sila/intents
```

مثال:

```json
{
  "text": "جهز البيت للنوم"
}
```

المخرجات:

```json
{
  "intent": "PREPARE_HOME_FOR_SLEEP",
  "confidence": 0.94
}
```

ثم:

```text
Intent
 ↓
Policy
 ↓
Adaptive Core
```

لا تسمح للنموذج بإرسال Device Commands.

---

# 33. API

أنشئ API versioning:

```text
/v1/auth
/v1/organizations
/v1/properties
/v1/buildings
/v1/rooms
/v1/hubs
/v1/devices
/v1/states
/v1/commands
/v1/automations
/v1/adaptive
/v1/energy
/v1/sila
/v1/health
```

---

# 34. WebSocket

استخدم WebSocket للأحداث الحية:

```text
device.state_changed
device.availability_changed
energy.updated
adaptive.plan_created
adaptive.plan_completed
notification.created
```

---

# 35. Admin Dashboard

أنشئ Dashboard بسيطًا أولًا:

```text
Organizations
Properties
Hubs
Devices
Online/Offline
Commands
Events
Adaptive Plans
Errors
Energy
```

---

# 36. Installer Flow

أنشئ Flow:

```text
Create Project
 ↓
Register Hub
 ↓
Connect Home Assistant
 ↓
Discover Devices
 ↓
Map Rooms
 ↓
Test Devices
 ↓
Save Configuration
 ↓
Handover
```

---

# 37. Hub Provisioning

يجب أن يكون السيناريو:

```text
Factory Reset
 ↓
Boot
 ↓
Generate Device Identity
 ↓
Pairing Mode
 ↓
Installer scans QR
 ↓
Cloud registers Hub
 ↓
Edge Agent receives credentials
 ↓
Home Assistant starts
 ↓
Device discovery
 ↓
Ready
```

في MVP، استخدم QR pairing.

---

# 38. Offline Mode

عند انقطاع الإنترنت:

يجب أن يستمر:

- Home Assistant.
- Local device control.
- Critical automations.
- Local state.
- Local event queue.

عند عودة الاتصال:

```text
Offline Queue
 ↓
Sync
 ↓
Conflict Resolution
 ↓
Cloud State
```

---

# 39. Security

يجب تنفيذ:

- TLS.
- Token rotation readiness.
- Device identity.
- Secrets management.
- RBAC.
- Audit logs.
- API rate limiting.
- Input validation.
- Secure WebSocket.
- Encrypted database backups.

لا تسجل secrets أو tokens في logs.

---

# 40. Audit Log

سجل:

```text
User Login
Device Added
Device Removed
Command Sent
Automation Changed
Adaptive Plan Executed
Permission Changed
Hub Registered
Firmware Changed
```

---

# 41. Testing

أنشئ:

## Unit Tests

لكل:

- Capability Mapping.
- State Engine.
- Policy Engine.
- Adaptive Planner.
- Reconciliation.

## Integration Tests

اختبر:

```text
API
 ↓
Database
 ↓
MQTT
 ↓
Edge Agent
 ↓
Home Assistant Mock
```

## E2E

اختبر:

```text
Create Tenant
 ↓
Create Property
 ↓
Register Hub
 ↓
Discover Virtual Device
 ↓
Read State
 ↓
Send Command
 ↓
Receive Event
 ↓
Adaptive Plan
 ↓
Execute
```

---

# 42. Home Assistant Test Environment

لا تبدأ بالأجهزة الحقيقية.

أنشئ:

```text
Docker
 ↓
Home Assistant
 ↓
Mock / Virtual Devices
```

استخدم أجهزة افتراضية:

```text
virtual_temperature_sensor
virtual_motion_sensor
virtual_light
virtual_ac
virtual_energy_meter
```

ثم اختبر المنظومة.

---

# 43. MQTT Topics

صمم namespace:

```text
syltra/{tenant_id}/hubs/{hub_id}/events
syltra/{tenant_id}/hubs/{hub_id}/commands
syltra/{tenant_id}/hubs/{hub_id}/state
syltra/{tenant_id}/hubs/{hub_id}/health
```

لا تضع بيانات حساسة في topic names.

---

# 44. Health Model

لكل Hub:

```text
online
last_seen
cpu
memory
storage
ha_status
edge_status
mqtt_status
cloud_status
```

لكل Device:

```text
online
last_seen
availability
battery
signal
error
```

---

# 45. Observability

أضف:

```text
structured logs
metrics
health endpoints
error tracking
request IDs
correlation IDs
```

Endpoints:

```text
/health
/ready
/live
```

---

# 46. Docker Compose

أنشئ بيئة محلية:

```text
postgres
redis
mqtt
api
edge-agent
home-assistant
admin
```

يجب أن يعمل النظام محليًا بأمر واحد.

مثال:

```bash
docker compose up -d
```

---

# 47. Seed Data

أنشئ Demo Tenant:

```text
SYLTRA Demo
 |
Villa 01
 |
Living Room
 |
Temperature Sensor
Motion Sensor
AC
Light
Energy Meter
```

---

# 48. Demo Scenario

عند تشغيل Demo:

```text
Temperature = 28°C
Occupancy = true
Energy = high
AC = 28°C
```

يطلب المستخدم:

"خل الغرفة مريحة."

Adaptive Core:

```text
Goal:
Comfort

Target:
24°C

Constraint:
Energy efficiency
```

ثم ينفذ:

```text
Set AC = 24°C
```

ثم يراقب.

إذا أصبحت:

```text
Temperature = 24°C
```

يسجل:

```text
Plan = SUCCESS
```

---

# 49. Production Readiness Checklist

قبل ربط Hardware حقيقي، يجب أن ينجح:

```text
[ ] Authentication
[ ] Multi-tenancy
[ ] Device Registry
[ ] Capability Model
[ ] Home Assistant Integration
[ ] Edge Agent
[ ] MQTT
[ ] State Sync
[ ] Commands
[ ] Events
[ ] Offline Queue
[ ] Adaptive Core
[ ] Reconciliation
[ ] Audit Logs
[ ] Security
[ ] Backups
[ ] Monitoring
[ ] Tests
[ ] Docker deployment
```

---

# 50. Hardware Readiness

بعد نجاح Software MVP، يجب أن يكون النظام جاهزًا لاستقبال:

```text
SYLTRA Hub
SYLTRA Switch
SYLTRA Sense
SYLTRA Relay
SYLTRA Air
SYLTRA Panel
```

لكن لا تبدأ تصنيع Hardware قبل نجاح Virtual Device E2E.

---

# 51. Hardware Integration Contract

أي جهاز SYLTRA مستقبلي يجب أن يوفر:

```text
Device Identity
Capabilities
State
Commands
Events
Firmware Version
Health
Security Identity
```

---

# 52. SYLTRA Hub Requirements

الـ Hub المستقبلي يحتاج:

```text
CPU
RAM
Storage
Wi-Fi
Ethernet
Bluetooth
Matter readiness
Thread readiness
Zigbee readiness
Z-Wave readiness
Secure identity
OTA
Local database
```

المواصفات النهائية للـ PCB لا تثبت في هذا المشروع قبل اختبار الـ software stack.

---

# 53. OTA

صمم النظام منذ البداية ليستقبل:

```text
Hub Firmware
Edge Agent Update
Home Assistant Integration Update
Configuration Update
```

ولا تنفذ Firmware flashing تلقائيًا في MVP إلا بعد إضافة signing وrollback.

---

# 54. Data Privacy

افصل:

```text
Operational Data
Analytics Data
AI Context
Audit Data
```

لا ترسل كل بيانات المنزل إلى نموذج AI بشكل افتراضي.

أرسل أقل قدر لازم لتنفيذ Intent أو تحليل محدد.

---

# 55. Intellectual Property Boundary

اعتبر هذه المكونات ملكية SYLTRA:

```text
SYLTRA Capability Model
SYLTRA Environment Model
SYLTRA State Engine
SYLTRA Adaptive Core
SYLTRA Planning
SYLTRA Policy Engine
SYLTRA Reconciliation
SYLTRA Energy Intelligence
SYLTRA Edge Agent
SYLTRA Cloud
```

Home Assistant يبقى مكونًا خارجيًا وفق شروط رخصته.

لا تنسب مكونات Home Assistant إلى SYLTRA.

---

# 56. ممنوعات المشروع

لا:

- تعدل Home Assistant Core بدون سبب.
- تربط Cloud مباشرة بـ Home Assistant.
- تجعل SILA تتحكم بالأجهزة مباشرة.
- تخزن secrets في Git.
- تربط Adaptive Core بـ entity IDs.
- تبدأ بتصنيع عشرات الأجهزة.
- تبدأ بـ Kubernetes بلا حاجة.
- تبني Microservices منفصلة بلا حاجة.
- تعتمد على جهاز حقيقي قبل Virtual E2E.
- تجعل Home Assistant قاعدة بيانات SYLTRA التجارية.
- تعتمد على Home Assistant كواجهة المستخدم النهائية.

---

# 57. طريقة التنفيذ داخل Cloud Code Max

لا تحاول إنشاء المشروع كله في Prompt واحد إذا أدى ذلك إلى ملفات ناقصة.

نفذ على مراحل.

## Stage 1

أنشئ repository والـ Docker environment.

## Stage 2

أنشئ PostgreSQL schema وmigrations.

## Stage 3

أنشئ Identity وMulti-tenancy.

## Stage 4

أنشئ Device Model وCapability Model.

## Stage 5

أنشئ API.

## Stage 6

أنشئ MQTT infrastructure.

## Stage 7

أنشئ Edge Agent.

## Stage 8

اربط Home Assistant.

## Stage 9

نفذ Virtual Device Discovery.

## Stage 10

نفذ State Sync.

## Stage 11

نفذ Command Execution.

## Stage 12

نفذ Adaptive Core.

## Stage 13

نفذ Reconciliation.

## Stage 14

نفذ Admin Dashboard.

## Stage 15

نفذ Installer Flow.

## Stage 16

نفذ SILA Intent API.

## Stage 17

نفذ Security Hardening.

## Stage 18

نفذ E2E Tests.

## Stage 19

جهز Hardware Integration Contract.

---

# 58. شرط كل Stage

بعد كل Stage:

1. شغل الاختبارات.
2. أصلح الأخطاء.
3. حدّث documentation.
4. لا تكسر الوظائف السابقة.
5. اعرض الملفات التي تغيرت.
6. اعرض أوامر التشغيل.
7. اعرض المتطلبات الجديدة.
8. لا تنتقل للمرحلة التالية قبل نجاح المرحلة الحالية.

---

# 59. Definition of Done

يعتبر المشروع جاهزًا للـ Hardware Integration عندما:

```text
Cloud works
AND
Edge works
AND
Home Assistant works
AND
Device discovery works
AND
State sync works
AND
Commands work
AND
Events work
AND
Offline operation works
AND
Adaptive Core works
AND
Reconciliation works
AND
Security baseline passes
AND
E2E tests pass
```

---

# 60. Final Target

النتيجة النهائية:

```text
                SYLTRA APP
                     |
                    API
                     |
              SYLTRA CLOUD
                     |
             SYLTRA ADAPTIVE
                     |
            SYLTRA EDGE AGENT
                     |
             SYLTRA HUB
                     |
          HOME ASSISTANT CORE
                     |
        +------------+------------+
        |            |            |
      Matter       Zigbee       Z-Wave
        |            |            |
        +------------+------------+
                     |
              SYLTRA DEVICES
```

المستخدم النهائي لا يرى Home Assistant.

المستخدم يرى:

SYLTRA.

---

# 61. أول أمر للمطور AI

ابدأ الآن بالمرحلة الأولى فقط.

لا تبنِ باقي المراحل قبل إنهاء المرحلة الأولى.

المطلوب:

1. إنشاء Monorepo.
2. إنشاء Docker Compose.
3. تشغيل PostgreSQL.
4. تشغيل Redis.
5. تشغيل MQTT Broker.
6. إنشاء NestJS API.
7. إنشاء Health Endpoints.
8. إنشاء configuration system.
9. إنشاء `.env.example`.
10. إنشاء README.
11. إنشاء CI baseline.
12. إنشاء test baseline.
13. التأكد من أن كل الخدمات تعمل محليًا.

بعد نجاح Stage 1، توقف وانتظر الأمر التالي:

`BUILD STAGE 2`

لا تنتقل تلقائيًا.
