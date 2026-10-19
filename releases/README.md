# حزم الإصدارات الجاهزة

كل تحديث يُرحَّل هنا: حزمة ZIP جاهزة للتشغيل داخل هذا المجلد + إصدار (Release)
على GitHub بنفس رقم الإصدار.

> **قاعدة ثابتة:** كل تحديث يُرحَّل هنا + Release على GitHub بنفس الرقم.
> راجع [`RELEASING.md`](../RELEASING.md) للخطوات الكاملة.

## أحدث إصدار
**v3.6.0** — [صفحة الإصدار](https://github.com/AdooGT-Technology/GT.Pos.Manager/releases/tag/v3.6.0) · [تنزيل مباشر](https://github.com/AdooGT-Technology/GT.Pos.Manager/raw/v3.6.0/releases/GT.Pos.Manager-3.6.0.zip)

## كل الحزم

| الإصدار | الملف | الحجم | SHA256 |
|---|---|---|---|
| 3.6.0 | `GT.Pos.Manager-3.6.0.zip` | 163 KB | `41f5dfe053c9060a51e45c074d82cd3bbdec8a9e0e04d71d5d3a9e1b735636b3` |
| 3.5.0 | `GT.Pos.Manager-3.5.0.zip` | 131 KB | `b1df382bdda7fc8c0cd19b8ff56a50b9c8bd2f1291f6c5fc63863245cae7c0e5` |

## تنزيل
- **v3.6.0**: [صفحة الإصدار](https://github.com/AdooGT-Technology/GT.Pos.Manager/releases/tag/v3.6.0) · [تنزيل مباشر](https://github.com/AdooGT-Technology/GT.Pos.Manager/raw/v3.6.0/releases/GT.Pos.Manager-3.6.0.zip)
- **v3.5.0**: [صفحة الإصدار](https://github.com/AdooGT-Technology/GT.Pos.Manager/releases/tag/v3.5.0) · [تنزيل مباشر](https://github.com/AdooGT-Technology/GT.Pos.Manager/raw/v3.5.0/releases/GT.Pos.Manager-3.5.0.zip)

## إضافة إصدار جديد

```bat
python Tools/release.py
git add releases && git commit -m "chore(release): add X.Y.Z package"
git push origin <branch>
gh release create vX.Y.Z --target <branch> --notes-file notes.md --latest
```

> بعد فك الضغط شغّل `setup.bat` ثم `run_server.bat` ثم `run_manager.bat`.
