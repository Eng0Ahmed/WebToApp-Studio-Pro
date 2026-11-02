@echo off
chcp 65001 >nul
title WebToApp Studio Pro
echo ========================================================
echo   WebToApp Studio Pro - تشغيل البرنامج بالواجهة العصرية
echo ========================================================
echo.
cd /d "%~dp0"
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo حدث خطأ أثناء تشغيل الواجهة العصرية، جارٍ تجربة الواجهة الكلاسيكية...
    python main.py --classic
)
pause
