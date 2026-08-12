<div align="center">

# 📱 WebToApp Studio Pro

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Android SDK](https://img.shields.io/badge/Android%20SDK-API%2030-3DDC84?style=for-the-badge&logo=android&logoColor=white)
![CustomTkinter](https://img.shields.io/badge/GUI-CustomTkinter-00599C?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)

**برنامج سطح مكتب احترافي ومتكامل لتحويل مواقع الويب وملفات HTML المحلية إلى تطبيقات أندرويد (APK & AAB)**
<br>
*A modern, powerful Desktop Suite to convert Web URLs or Local HTML5 projects into native Android Applications (APK & AAB).*

</div>

---

## ✨ المميزات الرئيسية (Key Features)

### ⚙️ 1. إعدادات التطبيق الأساسية (App Settings)
- **اسم التطبيق (App Title)**: تسمية التطبيق واسم حزمة الـ APK التلقائي.
- **اسم الحزمة (Package Name)**: دعم تخصيص المعرف الفريد (مثال: `com.company.myapp`).
- **تخصيص الإصدارات**: إمكانية إدخال `Version Name` و `Version Code`.
- **دعم مصادر المحتوى**:
  - **رابط موقع (Web URL)**: تحويل أي موقع إلكتروني مباشر إلى تطبيق.
  - **مجلد محلي (Local HTML Directory)**: تحويل ملفات HTML/CSS/JS المحلية إلى تطبيق أوفلاين 100%.

### 🎨 2. الهوية والتصميم (Branding & UI Customization)
- **أيقونة التطبيق (App Icon)**: تحويل وتوليد كافة الأحجام الدقيقة (`mdpi`, `hdpi`, `xhdpi`, `xxhdpi`, `xxxhdpi`).
- **شاشة البداية (Splash Screen)**: تخصيص صورة اللوجو، لون الخلفية، ومدة العرض بالثواني.
- **خصائص WebView**:
  - السحب للتحديث (Pull-to-Refresh).
  - شريط تقدم التحميل (Progress Bar) بلون مخصص.
  - التكبير والتصغير بأصابع اليد (Pinch-to-Zoom).

### 🔒 3. الصلاحيات والمميزات المتقدمة (Permissions & Features)
- **إدارة الصلاحيات بـ Checkboxes**: (Internet, Camera, Microphone, GPS Location, Storage).
- **رفع وتنزيل الملفات**: دعم رفع الصور والملفات عبر `WebChromeClient` وتنزيل الملفات عبر `DownloadListener`.
- **تشغيل الوسائط**: دعم كامل لتشغيل فيديوهات HTML5 والصوتيات.
- **وضع الرابط الخارجي (External Links)**: فتح الروابط الخارجية في WebView أو متصفح الجهاز الخارجي.

### 💰 4. تحقيق الدخل والإشعارات (Monetization & Push)
- **Google AdMob**: دمج إعلانات البانر (Banner) والإعلانات البينية (Interstitial).
- **OneSignal**: دمج إشعارات Push Notifications عبر المعرف الخاص.

### 🔑 5. التوقيع والتصدير (Keystore & Output)
- **مولّد مفاتيح (Keystore Generator)**: أداة مدمجة لتوليد مفتاح توقيع مخصص (`.jks`) عبر `keytool`.
- **خيارات التوقيع**: التوقيع بمفتاح للتجربة (Debug) أو مفتاح خاص مخصص (Custom Release Key).
- **تصدير APK & AAB**: بنقرة زر واحدة لبناء ملفات جاهزة للتثبيت المباشر أو الرفع على متجر **Google Play**.

---

## 🛠️ هيكلية المشروع (Project Architecture)

```
Html To APK/
├── main.py                    # النافذة الرئيسية والنقطة المدخلية للبرنامج
├── gui/
│   ├── app_window.py          # واجهة المستخدم الرئيسية المحدثة بـ CustomTkinter
│   ├── theme.py               # نظام التصميم الألوان والخطوط العصرية
│   └── keystore_dialog.py     # نافذة توليد مفتاح التوقيع Keystore
├── backend/
│   ├── config_manager.py      # إدارة حفظ وحفظ إعدادات المشروع (.wtaproj)
│   ├── project_generator.py   # مولّد كود مشروع الأندرويد و AndroidManifest و WebView
│   ├── builder.py             # محرك تشغيل وتتبع Gradle والتصدير الفعلي
│   └── sdk_utils.py           # مكتشف Android SDK و JDK ومحرك Gradle
├── templates/
│   ├── offline.html           # قالب صفحة الانقطاع التفاعلية
│   └── gradle-wrapper.jar     # مكتبة البناء الافتراضية
├── requirements.txt           # مكتبات بايثون المطلوبة
├── .gitignore                 # ملف استبعاد الملفات المؤقتة والـ Build
└── LICENSE                    # ترخيص MIT
```

---

## 🚀 كيفية التشغيل والتطوير (Getting Started)

### 1️⃣ المتطلبات الأساسية (Prerequisites)
- نظام تشغيل **Windows 10 / 11**
- لغة **Python 3.11+**
- أدوات **Android SDK** (تلقائية الاكتشاف)

### 2️⃣ تثبيت المكتبات (Installation)
افتح موجه الأوامر (Terminal / PowerShell) في مجلد المشروع ونفذ:

```bash
pip install -r requirements.txt
```

### 3️⃣ تشغيل البرنامج (Run Application)
```bash
python main.py
```

### 4️⃣ تحويل البرنامج إلى ملف تنفيذي (.exe)
لتوليد نسخة `.exe` مستقلة لا تحتاج تثبيت بايثون:

```bash
python -m PyInstaller --name "WebToApp Studio Pro" --onefile --windowed --add-data "templates;templates" --collect-all customtkinter main.py
```
سيكون الملف التنفيذي جاهزاً داخل مجلد `dist/`.

---

## 📤 خطوات رفع المشروع على GitHub (Git Commands)

افتح موجه الأوامر داخل مجلد المشروع ثم نفذ الأوامر التالية بالترتيب:

```bash
# 1. تهيئة المستودع المحلي
git init

# 2. إضافة جميع الملفات الرئيسية (مع استبعاد الملفات المؤقتة عبر .gitignore)
git add .

# 3. حفظ التغييرات الأولى
git commit -m "Initial release: WebToApp Studio Pro v1.0.0"

# 4. ربط المستودع بموقع GitHub (استبدل YOUR_USERNAME و REPO_NAME برابط مستودعك)
git remote add origin https://github.com/YOUR_USERNAME/REPO_NAME.git

# 5. رفع الملفات إلى الفرع الرئيسي
git branch -M main
git push -u origin main
```

---

## 📜 الترخيص (License)

هذا المشروع مرخص بموجب رخصة **[MIT License](LICENSE)**.

---

<div align="center">
تم التطوير بواسطة <b>Eng Ahmed Abdelaziz</b> ❤️
</div>
