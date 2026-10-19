#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GT-POS Gizmo Manager - Release Packager
=======================================

يبني حزمة الإصدار الجاهزة للتشغيل ويضعها في مجلد ``releases/``
مع تحديث جدول الحزم في ``releases/README.md`` تلقائياً.

الاستخدام:
    python Tools/release.py                # يبني حزمة الإصدار الحالي من version.py
    python Tools/release.py --force        # يستبدل الحزمة لو موجودة بنفس الرقم
    python Tools/release.py --out-dir DIR  # مجلد إخراج مختلف (للاختبار)
    python Tools/release.py --skip-index   # بدون تحديث releases/README.md
    python Tools/release.py --index-only   # إعادة بناء فهرس الحزم فقط

ثم:
    git add releases && git commit -m "chore(release): add X.Y.Z package"
    git push origin <branch>
    gh release create vX.Y.Z --target <branch> --notes-file <notes> --latest

ملاحظة: الأصول الثنائية (Release Assets) قد لا تكون متاحة من بعض بيئات
الرفع، لذلك الحزمة تُحفظ داخل المستودع في releases/ ويتم ربطها من صفحة
الإصدار برابط raw على الوسم.
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
import zipfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT_DIR = ROOT / "releases"
INDEX_FILE = "README.md"

# مجلدات لا تُضمَّن في الحزمة
EXCLUDED_DIRS = {
    ".git", ".github", ".vscode", ".idea", ".venv", "venv", "env",
    "__pycache__", "releases", "build", "dist", "node_modules", ".pytest_cache",
}
# ملفات لا تُضمَّن أبداً
EXCLUDED_FILES = {".DS_Store", "Thumbs.db", "desktop.ini", ".gitignore"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo", ".log", ".zip", ".tar", ".gz"}

# مجلدات تُنشأ فارغة داخل الحزمة (مثل مجلد السجلات)
EMPTY_DIRS = ["Logs"]

README_TEMPLATE = """==========================================================
 {app_name}  |  الإصدار {version}
 الاسم الرمزي: {codename}
 التاريخ: {release_date}
==========================================================

■ طريقة التشغيل (Windows)
----------------------------------------------------------
1) ثبّت Python 3.10 أو أحدث (مع خيار Add Python to PATH).
2) شغّل:  setup.bat
   - يقوم بتثبيت المكتبات المطلوبة وإنشاء/تهيئة قاعدة البيانات.
3) شغّل السيرفر:  run_server.bat
4) شغّل لوحة التحكم:  run_manager.bat

بيانات الدخول الافتراضية:
   المستخدم: admin
   كلمة المرور: admin123

المتطلبات الخارجية:
   - SQL Server (Express) + ODBC Driver 17 for SQL Server
   - إعدادات الاتصال في: Server/config.py

■ الجديد في هذا الإصدار ({version})
----------------------------------------------------------
{changelog}

■ محتوى الحزمة
----------------------------------------------------------
version.py                  رقم الإصدار الحالي ({version})
history.txt                 سجل التحديثات الكامل
Manager/                    لوحة التحكم وكل الصفحات
Server/                     سيرفر الشبكة وقاعدة البيانات
Client/                     عميل الأجهزة (Agent)
Tools/                      أدوات الفحص والترحيل والنسخ الاحتياطي (ومولّد الحزم release.py)

■ ملاحظات
----------------------------------------------------------
- إذا لم يتوفر اتصال بقاعدة البيانات يعمل البرنامج ببيانات تجريبية.
- راجع history.txt لمعرفة تفاصيل كل إصدار.
"""

INDEX_TEMPLATE = """# حزم الإصدارات الجاهزة

كل تحديث يُرحَّل هنا: حزمة ZIP جاهزة للتشغيل داخل هذا المجلد + إصدار (Release)
على GitHub بنفس رقم الإصدار.

> **قاعدة ثابتة:** كل تحديث يُرحَّل هنا + Release على GitHub بنفس الرقم.
> راجع [`RELEASING.md`](../RELEASING.md) للخطوات الكاملة.

## أحدث إصدار
{latest}

## كل الحزم

| الإصدار | الملف | الحجم | SHA256 |
|---|---|---|---|
{rows}

## تنزيل
{links}

## إضافة إصدار جديد

```bat
python Tools/release.py
git add releases && git commit -m "chore(release): add X.Y.Z package"
git push origin <branch>
gh release create vX.Y.Z --target <branch> --notes-file notes.md --latest
```

> بعد فك الضغط شغّل `setup.bat` ثم `run_server.bat` ثم `run_manager.bat`.
"""


def read_version():
    """يقرأ بيانات الإصدار من version.py بدون تنفيذ الملف."""
    data = {}
    text = (ROOT / "version.py").read_text(encoding="utf-8")
    for key in ("APP_NAME", "APP_VERSION", "APP_CODENAME", "RELEASE_DATE"):
        match = re.search(rf'^{key}\s*=\s*"([^"]*)"', text, re.MULTILINE)
        data[key] = match.group(1).strip() if match else ""
    if not data.get("APP_VERSION"):
        raise SystemExit("[!] لم يتم العثور على APP_VERSION في version.py")
    return data


def changelog_for(version):
    """يجلب أسطر سجل التحديثات الخاصة بالإصدار من history.txt."""
    path = ROOT / "history.txt"
    if not path.exists():
        return "- (لا يوجد سجل تحديثات)"
    lines = path.read_text(encoding="utf-8").splitlines()
    collected, inside = [], False
    for line in lines:
        if re.match(rf"^الإصدار\s+{re.escape(version)}\b", line.strip()):
            inside = True
            continue
        if inside:
            if line.startswith("الإصدار "):
                break
            if line.strip():
                collected.append(line.rstrip())
    return "\n".join(collected) if collected else "- (لا يوجد سجل تحديثات لهذا الإصدار)"


def iter_files():
    """يمر على ملفات المشروع التي يجب ضمّها في الحزمة."""
    for path in sorted(ROOT.rglob("*")):
        rel = path.relative_to(ROOT)
        if any(part in EXCLUDED_DIRS for part in rel.parts):
            continue
        if not path.is_file():
            continue
        if path.name in EXCLUDED_FILES or path.suffix.lower() in EXCLUDED_SUFFIXES:
            continue
        yield path, rel


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_zip(out_dir: Path, version_data: dict, force: bool) -> Path:
    version = version_data["APP_VERSION"]
    out_dir.mkdir(parents=True, exist_ok=True)
    target = out_dir / f"GT.Pos.Manager-{version}.zip"

    if target.exists() and not force:
        raise SystemExit(f"[!] الحزمة موجودة بالفعل: {target}\n    استخدم --force للاستبدال.")

    package_name = f"GT.Pos.Manager {version}"
    readme = README_TEMPLATE.format(
        app_name=version_data["APP_NAME"] or "GT-POS Gizmo Manager",
        version=version,
        codename=version_data["APP_CODENAME"] or "-",
        release_date=version_data["RELEASE_DATE"] or date.today().isoformat(),
        changelog=changelog_for(version),
    )

    added = 0
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path, rel in iter_files():
            archive.write(path, f"{package_name}/{rel.as_posix()}")
            added += 1
        for folder in EMPTY_DIRS:
            if not (ROOT / folder).is_dir() or not any((ROOT / folder).iterdir()):
                archive.writestr(f"{package_name}/{folder}/.gitkeep", "")
        archive.writestr(f"{package_name}/README-{version}.txt", readme)

    print(f"[+] تم إنشاء الحزمة: {target}")
    print(f"    الملفات: {added}  |  الحجم: {target.stat().st_size / 1024:.0f} KB")
    print(f"    SHA256: {sha256_of(target)}")
    return target


def update_index(out_dir: Path):
    """يعيد بناء جدول الحزم في releases/README.md من الملفات الموجودة."""
    index_path = out_dir / INDEX_FILE
    packages = {}
    for path in out_dir.glob("GT.Pos.Manager-*.zip"):
        match = re.search(r"GT\.Pos\.Manager-(\d+\.\d+\.\d+)\.zip$", path.name)
        if match:
            packages[match.group(1)] = path
    if not packages:
        print("[i] لا توجد حزم لتحديث الفهرس.")
        return

    def sort_key(value):
        return tuple(int(part) for part in value.split("."))

    ordered = sorted(packages, key=sort_key, reverse=True)
    rows = []
    links = []
    for version in ordered:
        path = packages[version]
        size_kb = path.stat().st_size / 1024
        rows.append(f"| {version} | `{path.name}` | {size_kb:.0f} KB | `{sha256_of(path)}` |")
        links.append(
            f"- **v{version}**: "
            f"[صفحة الإصدار](https://github.com/AdooGT-Technology/GT.Pos.Manager/releases/tag/v{version}) · "
            f"[تنزيل مباشر](https://github.com/AdooGT-Technology/GT.Pos.Manager/raw/v{version}/releases/{path.name})"
        )

    latest = ordered[0]
    latest_path = packages[latest]
    index_path.write_text(
        INDEX_TEMPLATE.format(
            latest=(
                f"**v{latest}** — [صفحة الإصدار](https://github.com/AdooGT-Technology/GT.Pos.Manager/releases/tag/v{latest}) · "
                f"[تنزيل مباشر](https://github.com/AdooGT-Technology/GT.Pos.Manager/raw/v{latest}/releases/{latest_path.name})"
            ),
            rows="\n".join(rows),
            links="\n".join(links),
        ),
        encoding="utf-8",
    )
    print(f"[+] تم تحديث فهرس الحزم: {index_path}")


def main():
    parser = argparse.ArgumentParser(description="بناء حزمة إصدار GT-POS ووضعها في releases/")
    parser.add_argument("--force", action="store_true", help="استبدال الحزمة لو موجودة")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR), help="مجلد الإخراج")
    parser.add_argument("--skip-index", action="store_true", help="عدم تحديث فهرس الحزم")
    parser.add_argument("--index-only", action="store_true", help="تحديث فهرس الحزم فقط بدون بناء")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    out_dir = Path(args.out_dir).resolve()

    if args.index_only:
        update_index(out_dir)
        return

    version_data = read_version()
    print(f"[i] الإصدار: {version_data['APP_VERSION']} - {version_data['APP_CODENAME']}")
    build_zip(out_dir, version_data, args.force)
    if not args.skip_index:
        update_index(out_dir)
    print("[i] التالي: أضف الحزمة للـ commit ثم أنشئ/حدّث الإصدار على GitHub.")


if __name__ == "__main__":
    main()
