@echo off
chcp 65001 >nul
echo ========================================
echo   تثبيت متطلبات السيرفر - GT-POS
echo ========================================
echo.

python -m pip install --upgrade pip
if %errorlevel% neq 0 (
    echo [!] Python غير موجود أو pip لا يعمل. تأكد من تثبيت Python 3.10+
    pause
    exit /b 1
)

echo [1/2] تثبيت المتطلبات الأساسية...
pip install -r requirements-server.txt
if %errorlevel% neq 0 (
    echo [!] فشل تثبيت requirements-server.txt
    pause
    exit /b 1
)

echo [2/2] تثبيت مشغل الوسائط المدمج...
pip install PyQt6-WebEngine
if %errorlevel% neq 0 (
    echo [!] فشل تثبيت PyQt6-WebEngine
    pause
    exit /b 1
)

echo.
echo ========================================
echo   [✓] تم تثبيت جميع متطلبات السيرفر بنجاح
echo ========================================
pause