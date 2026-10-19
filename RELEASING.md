# 🚀 دورة الإصدارات (Release Workflow) — قاعدة ثابتة

> **قاعدة المشروع:** كل تحديث/ترقية تُرحَّل إلى مجلد `releases/` **و** تُنشر كإصدار
> (GitHub Release) بنفس رقم الإصدار. لا يُعتبر أي تحديث منتهياً قبل تنفيذ الخطوات التالية.

---

## 1) قبل الإصدار

- [ ] تحديث `APP_VERSION` و`APP_CODENAME` و`RELEASE_DATE` في `version.py`
- [ ] إضافة مدخل الإصدار الجديد في أعلى قسم الإصدارات بـ `history.txt`
- [ ] التأكد من أن الشاشات/الميزات الجديدة مربوطة فعلياً (لا أزرار بلا وظيفة ولا Placeholders غير مقصودة)
- [ ] فحص سريع: `python -m compileall Manager Server Client Tools`

## 2) بناء الحزمة

```bat
python Tools/release.py
```

يقوم السكربت تلقائياً بـ:

| الخطوة | التفاصيل |
|---|---|
| قراءة الإصدار | من `version.py` بدون تنفيذ الملف |
| جمع الملفات | كل المشروع مع استثناء `.git` و`__pycache__` و`*.pyc` و`*.log` و`releases/` و`build/`… |
| توليد دليل | `README-<الإصدار>.txt` يحتوي طريقة التشغيل + سجل تحديثات هذا الإصدار من `history.txt` |
| إنشاء الحزمة | `releases/GT.Pos.Manager-<الإصدار>.zip` |
| الفهرس | إعادة بناء جدول الحزم والروابط في `releases/README.md` |
| البصمة | طباعة `SHA256` للحزمة |

خيارات مساعدة:

```bat
python Tools/release.py --force        :: استبدال حزمة موجودة بنفس الرقم
python Tools/release.py --index-only   :: تحديث releases/README.md فقط
python Tools/release.py --out-dir DIR  :: مجلد إخراج مختلف (اختبار)
```

## 3) الترحيل

```bat
git add releases version.py history.txt
git commit -m "chore(release): prepare X.Y.Z package"
git push origin <branch>
gh release create vX.Y.Z --target <branch> --title "GT-POS Gizmo Manager vX.Y.Z — <الاسم الرمزي>" --notes-file notes.md --latest
```

- الوسم دائماً بالشكل `vX.Y.Z` (مثال: `v3.5.0`).
- **Current release** يجب أن يشير إلى أحدث إصدار (أو `--latest`).
- الرابط الثابت للتنزيل:
  `https://github.com/AdooGT-Technology/GT.Pos.Manager/raw/vX.Y.Z/releases/GT.Pos.Manager-X.Y.Z.zip`

> **ملاحظة عن الـ Assets:** في بعض بيئات الرفع يكون `uploads.github.com` محجوباً، فلا
> يمكن إرفاق ZIP كمرفق رسمي. البديل المعتمد في هذا المستودع هو حفظ الحزمة داخل
> `releases/` وربطها من صفحة الإصدار برابط مباشر (الوسم + المسار). لو كان الرفع متاحاً
> أضف الملف كمرفق أيضاً عبر `gh release upload vX.Y.Z releases/...zip`.

## 4) بعد الإصدار

- [ ] التأكد أن صفحة الإصدار تعرض ملاحظات صحيحة ورابط الحزمة يعمل
- [ ] تحديث الـ Pull Request / دمج الفرع إن لزم
- [ ] إبقاء الحزم القديمة في `releases/` (لا تُحذف) ليبقى أرشيف الإصدارات كاملاً

---

## الحالة الحالية

| الإصدار | الحزمة | الإصدار على GitHub |
|---|---|---|
| 3.6.1 | `releases/GT.Pos.Manager-3.6.1.zip` | https://github.com/AdooGT-Technology/GT.Pos.Manager/releases/tag/v3.6.1 |
| 3.6.0 | `releases/GT.Pos.Manager-3.6.0.zip` | https://github.com/AdooGT-Technology/GT.Pos.Manager/releases/tag/v3.6.0 |
| 3.5.0 | `releases/GT.Pos.Manager-3.5.0.zip` | https://github.com/AdooGT-Technology/GT.Pos.Manager/releases/tag/v3.5.0 |
