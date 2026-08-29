# نشر SYLTRA HEALTH على health.syltraone.com (مشروع Cloudflare Pages منفصل)

الموقع كله (بما فيه HEALTH) يُبنى من نفس الريبو. لعرض HEALTH على الـsubdomain
ننشئ **مشروع Pages ثاني** من نفس الريبو، ونجعل أمر البناء يضيف ملف `_redirects`
يحوّل جذر الـsubdomain إلى صفحة HEALTH. لا حاجة لتعديل أي كود.

## 1) إنشاء مشروع Pages الجديد
Cloudflare Dashboard → Workers & Pages → Create → Pages → Connect to Git → اختر
نفس الريبو (`platform`) والفرع `main`.

## 2) إعدادات البناء (Build settings) للمشروع الجديد فقط
- **Framework preset:** None
- **Build command:**
  ```
  STATIC_EXPORT=1 npx next build && printf '/  /en/health  302\n/en  /en/health  302\n/ar  /ar/health  302\n' > out/_redirects
  ```
- **Build output directory:** `out`
- **Root directory:** `syltra smart` (نفس ما في المشروع الأساسي إن كان الريبو يحوي مجلدات)

> السطر الأخير ينشئ `out/_redirects` في هذا المشروع فقط (لأنه جزء من أمر بنائه)،
> فلا يؤثّر على المشروع الأساسي syltraone.com.

## 3) ربط الدومين
- في المشروع الجديد → Custom domains → Set up a domain → `health.syltraone.com`.
- Cloudflare يضيف سجل CNAME تلقائيًا إن كان النطاق مُدارًا لديه.
  (يدويًا: CNAME `health` → `<اسم-مشروع-Pages>.pages.dev`، Proxied.)

## 4) بعد النشر
- `https://health.syltraone.com/` → يفتح صفحة HEALTH (تحويل 302 إلى `/en/health`).
- الصفحات الفعلية تظل على `health.syltraone.com/en/health` و `/ar/health`.
- الـcanonical في كل صفحة يشير إلى `syltraone.com/.../health` (تم ضبطه في الكود)،
  فلا يوجد محتوى مكرّر ضار للسيو.

## 5) جعل HEALTH حصريًا على الـsubdomain (اختياري لكن موصى به)
لمنع ظهور `/health` على الموقع الأم `syltraone.com`، عدّل **أمر بناء المشروع الأساسي**
ليحوّل مسار `/health` إلى الـsubdomain:

```
STATIC_EXPORT=1 npx next build && printf '/health/*  https://health.syltraone.com/:splat  301\n' >> out/_redirects
```

بهذا:
- `syltraone.com/en/health` → يحوّل إلى `health.syltraone.com/en/health`.
- HEALTH يظهر ويُؤرشَف **فقط** على الـsubdomain.

> canonical / hreflang / OG / JSON-LD لصفحات HEALTH مضبوطة أصلًا على
> `https://health.syltraone.com` (في الكود)، وصفحات HEALTH **غير مدرجة** في
> sitemap الموقع الأم — فلا يوجد محتوى مكرر.

## ملاحظات
- إن لم تُضِف تحويل المشروع الأساسي، ستبقى `/health` مفتوحة على النطاقين تقنيًا،
  لكن الـcanonical يوجّه محركات البحث للـsubdomain على أي حال.
