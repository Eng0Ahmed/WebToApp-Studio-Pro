import os
import sys
import customtkinter as ctk
from tkinter import filedialog, messagebox, colorchooser
from PIL import Image, ImageTk

from gui.theme import Theme
from gui.keystore_dialog import KeystoreDialog
from backend.config_manager import ProjectConfig
from backend.sdk_utils import SDKUtils
from backend.project_generator import ProjectGenerator
from backend.builder import AndroidBuilder

class AppWindow(ctk.CTk):
    """Main Desktop GUI Window for WebToApp Studio Pro."""

    def __init__(self):
        super().__init__()

        # Window Config
        self.title("WebToApp Studio Pro - تحويل المواقع لـ APK & AAB")
        self.geometry("1180x820")
        self.minsize(1040, 700)
        ctk.set_appearance_mode("Dark")

        # Initial Config Data
        self.config_data = ProjectConfig.get_default()

        # System SDK Detection
        self.android_sdk = SDKUtils.detect_android_sdk()
        self.java_home = SDKUtils.detect_java_home()

        # Builder Instance
        self.builder = None
        self.output_dest_dir = os.path.expanduser(r"~\Desktop\WebToApp_Builds")

        # Build UI Components
        self._build_ui()
        self._load_config_to_ui(self.config_data)

    def _build_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # ----------------------------------------------------
        # 1. Top Header Bar
        # ----------------------------------------------------
        header = ctk.CTkFrame(self, fg_color=Theme.SURFACE_CARD, corner_radius=0, height=70)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")

        lbl_logo = ctk.CTkLabel(
            header,
            text="📱 WebToApp Studio Pro",
            font=Theme.FONT_HEADER,
            text_color=Theme.PRIMARY
        )
        lbl_logo.pack(side="left", padx=24, pady=14)

        lbl_sub = ctk.CTkLabel(
            header,
            text="أداة تحويل موقع الويب أو ملفات HTML إلى تطبيقات أندرويد (APK & AAB)",
            font=Theme.FONT_BODY,
            text_color=Theme.TEXT_SECONDARY
        )
        lbl_sub.pack(side="left", padx=10, pady=14)

        # Header Action Buttons
        btn_save_proj = ctk.CTkButton(
            header, text="💾 حفظ المشروع", font=Theme.FONT_TITLE,
            fg_color=Theme.SURFACE_CARD_HOVER, width=130, height=40, command=self._save_project_file
        )
        btn_save_proj.pack(side="right", padx=16, pady=14)

        btn_load_proj = ctk.CTkButton(
            header, text="📂 فتح مشروع", font=Theme.FONT_TITLE,
            fg_color=Theme.SURFACE_CARD_HOVER, width=130, height=40, command=self._load_project_file
        )
        btn_load_proj.pack(side="right", padx=(0, 4), pady=14)

        btn_about_dev = ctk.CTkButton(
            header, text="👨‍💻 بيانات المطور", font=Theme.FONT_TITLE,
            fg_color=Theme.SURFACE_CARD_HOVER, width=130, height=40, command=self._show_about_dialog
        )
        btn_about_dev.pack(side="right", padx=(0, 4), pady=14)

        # ----------------------------------------------------
        # 2. Left Sidebar (Live Preview & Environment Info)
        # ----------------------------------------------------
        sidebar = ctk.CTkFrame(self, fg_color=Theme.SURFACE_CARD, corner_radius=14, width=310)
        sidebar.grid(row=1, column=0, sticky="nsew", padx=(16, 8), pady=16)
        sidebar.grid_propagate(False)

        # Developer Credit Card (Sidebar Footer)
        dev_card = ctk.CTkFrame(sidebar, fg_color=Theme.BG_DARK, corner_radius=12, border_width=1, border_color=Theme.BORDER)
        dev_card.pack(fill="x", padx=16, pady=(12, 16), side="bottom")

        ctk.CTkLabel(dev_card, text="👨‍💻 تطوير المهندس / Developer", font=Theme.FONT_TITLE, text_color=Theme.PRIMARY).pack(anchor="w", padx=12, pady=(10, 2))
        ctk.CTkLabel(dev_card, text="Eng_Ahmed Abdelaziz Mohamed", font=Theme.FONT_BODY, text_color=Theme.TEXT_PRIMARY).pack(anchor="w", padx=12, pady=1)
        ctk.CTkLabel(dev_card, text="📧 eng.ahmed.abdelaziz.2022@gmail.com", font=Theme.FONT_BODY, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=12, pady=1)
        ctk.CTkLabel(dev_card, text="📞 +201024735044", font=Theme.FONT_BODY, text_color=Theme.TEXT_MUTED).pack(anchor="w", padx=12, pady=(1, 10))

        # Preview Card Header
        ctk.CTkLabel(sidebar, text="معاينة التطبيق الحية", font=Theme.FONT_SUBHEADER, text_color=Theme.TEXT_PRIMARY).pack(pady=(18, 10))

        # Icon Container Frame
        self.preview_card = ctk.CTkFrame(sidebar, fg_color=Theme.BG_DARK, corner_radius=16, border_width=1, border_color=Theme.BORDER)
        self.preview_card.pack(fill="x", padx=16, pady=8, ipady=16)

        self.lbl_preview_icon = ctk.CTkLabel(self.preview_card, text="[أيقونة]", width=84, height=84, fg_color=Theme.SURFACE_CARD, corner_radius=18)
        self.lbl_preview_icon.pack(pady=(16, 10))

        self.lbl_preview_title = ctk.CTkLabel(self.preview_card, text="تطبيقي المميز", font=Theme.FONT_SUBHEADER, text_color=Theme.TEXT_PRIMARY)
        self.lbl_preview_title.pack(pady=2)

        self.lbl_preview_pkg = ctk.CTkLabel(self.preview_card, text="com.example.webapp", font=Theme.FONT_BODY, text_color=Theme.TEXT_MUTED)
        self.lbl_preview_pkg.pack(pady=(0, 10))

        # System Status
        status_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        status_frame.pack(fill="x", padx=16, pady=16)

        sdk_status_text = "🟢 Android SDK متوفر" if self.android_sdk else "🔴 لم يتم العثور على SDK"
        ctk.CTkLabel(status_frame, text=sdk_status_text, font=Theme.FONT_BODY, text_color=Theme.SUCCESS if self.android_sdk else Theme.DANGER).pack(anchor="w", pady=3)

        java_status_text = "🟢 Java JDK متوفر" if self.java_home else "🔴 لم يتم العثور على JDK"
        ctk.CTkLabel(status_frame, text=java_status_text, font=Theme.FONT_BODY, text_color=Theme.SUCCESS if self.java_home else Theme.DANGER).pack(anchor="w", pady=3)

        # Fast Build Buttons in Sidebar
        ctk.CTkLabel(sidebar, text="التصدير السريع", font=Theme.FONT_SUBHEADER, text_color=Theme.TEXT_PRIMARY).pack(pady=(18, 10))

        self.btn_fast_apk = ctk.CTkButton(
            sidebar, text="⚡ بناء APK الآن", font=Theme.FONT_TITLE,
            fg_color=Theme.PRIMARY, hover_color=Theme.PRIMARY_HOVER, height=48, corner_radius=10,
            command=lambda: self._start_build(is_aab=False)
        )
        self.btn_fast_apk.pack(fill="x", padx=16, pady=8)

        self.btn_fast_aab = ctk.CTkButton(
            sidebar, text="📦 بناء AAB (لجوجل بلاي)", font=Theme.FONT_TITLE,
            fg_color=Theme.SUCCESS, hover_color=Theme.SUCCESS_HOVER, height=48, corner_radius=10,
            command=lambda: self._start_build(is_aab=True)
        )
        self.btn_fast_aab.pack(fill="x", padx=16, pady=8)

        # ----------------------------------------------------
        # 3. Main Center Content Container (Tabs + Log Console)
        # ----------------------------------------------------
        main_content = ctk.CTkFrame(self, fg_color="transparent")
        main_content.grid(row=1, column=1, sticky="nsew", padx=(8, 16), pady=16)
        main_content.grid_rowconfigure(0, weight=3)
        main_content.grid_rowconfigure(1, weight=1)
        main_content.grid_columnconfigure(0, weight=1)

        # Tabview
        self.tabview = ctk.CTkTabview(main_content, fg_color=Theme.SURFACE_CARD, corner_radius=14)
        self.tabview.grid(row=0, column=0, sticky="nsew")

        # Custom Tab font
        try:
            self.tabview._segmented_button.configure(font=Theme.FONT_TITLE, height=40)
        except Exception:
            pass

        tab_basic = self.tabview.add("1. البيانات الأساسية")
        tab_branding = self.tabview.add("2. الهوية والتصميم")
        tab_features = self.tabview.add("3. الصلاحيات والمميزات")
        tab_monetization = self.tabview.add("4. الإعلانات والإشعارات")
        tab_build = self.tabview.add("5. التوقيع والتصدير")

        self._setup_tab_basic(tab_basic)
        self._setup_tab_branding(tab_branding)
        self._setup_tab_features(tab_features)
        self._setup_tab_monetization(tab_monetization)
        self._setup_tab_build(tab_build)

        # Log Terminal Console (Bottom)
        console_frame = ctk.CTkFrame(main_content, fg_color=Theme.SURFACE_CARD, corner_radius=14)
        console_frame.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        console_frame.grid_columnconfigure(0, weight=1)
        console_frame.grid_rowconfigure(1, weight=1)

        console_header = ctk.CTkFrame(console_frame, fg_color="transparent")
        console_header.grid(row=0, column=0, sticky="ew", padx=16, pady=8)

        ctk.CTkLabel(console_header, text="💻 سجل بناء التطبيق (Build Console Logs)", font=Theme.FONT_SUBHEADER, text_color=Theme.TEXT_PRIMARY).pack(side="left")

        self.btn_open_output = ctk.CTkButton(
            console_header, text="📁 فتح مجلد المخرجات", font=Theme.FONT_TITLE,
            fg_color=Theme.SURFACE_CARD_HOVER, width=140, height=34, command=self._open_output_dir
        )
        self.btn_open_output.pack(side="right")

        self.txt_console = ctk.CTkTextbox(console_frame, font=Theme.FONT_MONO, fg_color=Theme.BG_DARK, text_color="#38bdf8", corner_radius=10)
        self.txt_console.grid(row=1, column=0, sticky="nsew", padx=14, pady=(0, 14))

    # ----------------------------------------------------
    # TAB 1: Basic App Settings
    # ----------------------------------------------------
    def _setup_tab_basic(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=12)

        # App Title
        ctk.CTkLabel(scroll, text="اسم التطبيق (App Title):", font=Theme.FONT_TITLE, text_color=Theme.TEXT_PRIMARY).pack(anchor="w", pady=(10, 4))
        self.entry_app_title = ctk.CTkEntry(scroll, font=Theme.FONT_BODY, height=42)
        self.entry_app_title.pack(fill="x", pady=2)
        self.entry_app_title.bind("<KeyRelease>", lambda e: self._update_preview())

        # Package Name
        ctk.CTkLabel(scroll, text="اسم الحزمة (Package Name):", font=Theme.FONT_TITLE, text_color=Theme.TEXT_PRIMARY).pack(anchor="w", pady=(16, 4))
        self.entry_package_name = ctk.CTkEntry(scroll, font=Theme.FONT_BODY, placeholder_text="com.domain.app", height=42)
        self.entry_package_name.pack(fill="x", pady=2)
        self.entry_package_name.bind("<KeyRelease>", lambda e: self._update_preview())

        # Version Name & Version Code
        ver_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        ver_frame.pack(fill="x", pady=(16, 4))

        f1 = ctk.CTkFrame(ver_frame, fg_color="transparent")
        f1.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkLabel(f1, text="إصدار التطبيق (Version Name):", font=Theme.FONT_TITLE).pack(anchor="w", pady=(0, 4))
        self.entry_version_name = ctk.CTkEntry(f1, font=Theme.FONT_BODY, height=42)
        self.entry_version_name.pack(fill="x")

        f2 = ctk.CTkFrame(ver_frame, fg_color="transparent")
        f2.pack(side="right", fill="x", expand=True)
        ctk.CTkLabel(f2, text="رقم الإصدار (Version Code):", font=Theme.FONT_TITLE).pack(anchor="w", pady=(0, 4))
        self.entry_version_code = ctk.CTkEntry(f2, font=Theme.FONT_BODY, height=42)
        self.entry_version_code.pack(fill="x")

        # Content Type Selection
        ctk.CTkLabel(scroll, text="مصدر محتوى التطبيق (Content Source):", font=Theme.FONT_TITLE, text_color=Theme.TEXT_PRIMARY).pack(anchor="w", pady=(20, 6))

        self.seg_content_type = ctk.CTkSegmentedButton(
            scroll, values=["رابط ويب (Web URL)", "مجلد محلي (Local HTML Directory)"],
            font=Theme.FONT_TITLE, height=40,
            command=self._on_content_type_changed
        )
        self.seg_content_type.pack(fill="x", pady=4)

        self.frame_url = ctk.CTkFrame(scroll, fg_color="transparent")
        self.frame_url.pack(fill="x", pady=8)
        ctk.CTkLabel(self.frame_url, text="رابط الموقع (Web URL):", font=Theme.FONT_TITLE).pack(anchor="w")
        self.entry_web_url = ctk.CTkEntry(self.frame_url, font=Theme.FONT_BODY, placeholder_text="https://example.com", height=42)
        self.entry_web_url.pack(fill="x", pady=2)

        self.frame_local = ctk.CTkFrame(scroll, fg_color="transparent")
        ctk.CTkLabel(self.frame_local, text="مسار مجلد ملفات HTML المحلية:", font=Theme.FONT_TITLE).pack(anchor="w")
        f_loc = ctk.CTkFrame(self.frame_local, fg_color="transparent")
        f_loc.pack(fill="x", pady=2)
        self.entry_local_dir = ctk.CTkEntry(f_loc, font=Theme.FONT_BODY, placeholder_text="اختر مجلد يحتوي على index.html", height=42)
        self.entry_local_dir.pack(side="left", fill="x", expand=True, padx=(0, 10))
        btn_browse_local = ctk.CTkButton(f_loc, text="استعراض...", width=110, height=42, font=Theme.FONT_TITLE, command=self._browse_local_dir)
        btn_browse_local.pack(side="right")

        # Orientation
        ctk.CTkLabel(scroll, text="اتجاه الشاشة (Screen Orientation):", font=Theme.FONT_TITLE, text_color=Theme.TEXT_PRIMARY).pack(anchor="w", pady=(20, 6))
        self.seg_orientation = ctk.CTkSegmentedButton(
            scroll, values=["عمودي (Portrait)", "أفقي (Landscape)", "تلقائي (Auto)"],
            font=Theme.FONT_TITLE, height=40
        )
        self.seg_orientation.pack(fill="x", pady=4)

    def _on_content_type_changed(self, value):
        if "رابط" in value:
            self.frame_url.pack(fill="x", pady=8)
            self.frame_local.pack_forget()
        else:
            self.frame_url.pack_forget()
            self.frame_local.pack(fill="x", pady=8)

    def _browse_local_dir(self):
        directory = filedialog.askdirectory()
        if directory:
            self.entry_local_dir.delete(0, "end")
            self.entry_local_dir.insert(0, directory)

    # ----------------------------------------------------
    # TAB 2: Branding & Graphics
    # ----------------------------------------------------
    def _setup_tab_branding(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=12)

        # App Icon
        ctk.CTkLabel(scroll, text="أيقونة التطبيق (App Icon PNG):", font=Theme.FONT_TITLE, text_color=Theme.TEXT_PRIMARY).pack(anchor="w", pady=(10, 4))
        f_icon = ctk.CTkFrame(scroll, fg_color="transparent")
        f_icon.pack(fill="x", pady=2)
        self.entry_app_icon = ctk.CTkEntry(f_icon, font=Theme.FONT_BODY, placeholder_text="اختر صورة PNG عالي الجودة...", height=42)
        self.entry_app_icon.pack(side="left", fill="x", expand=True, padx=(0, 10))
        btn_browse_icon = ctk.CTkButton(f_icon, text="رفع أيقونة...", width=120, height=42, font=Theme.FONT_TITLE, command=self._browse_icon_file)
        btn_browse_icon.pack(side="right")

        # Splash Screen
        ctk.CTkLabel(scroll, text="إعدادات شاشة البداية (Splash Screen):", font=Theme.FONT_SUBHEADER, text_color=Theme.PRIMARY).pack(anchor="w", pady=(22, 8))

        f_splash = ctk.CTkFrame(scroll, fg_color="transparent")
        f_splash.pack(fill="x", pady=2)
        self.entry_splash_img = ctk.CTkEntry(f_splash, font=Theme.FONT_BODY, placeholder_text="صورة Splash (اختياري)...", height=42)
        self.entry_splash_img.pack(side="left", fill="x", expand=True, padx=(0, 10))
        btn_browse_splash = ctk.CTkButton(f_splash, text="رفع صورة...", width=120, height=42, font=Theme.FONT_TITLE, command=self._browse_splash_file)
        btn_browse_splash.pack(side="right")

        f_splash_opts = ctk.CTkFrame(scroll, fg_color="transparent")
        f_splash_opts.pack(fill="x", pady=10)

        f_bg = ctk.CTkFrame(f_splash_opts, fg_color="transparent")
        f_bg.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkLabel(f_bg, text="لون خلفية Splash (Hex):", font=Theme.FONT_TITLE).pack(anchor="w")
        
        f_bg_picker = ctk.CTkFrame(f_bg, fg_color="transparent")
        f_bg_picker.pack(fill="x", pady=2)
        self.entry_splash_bg = ctk.CTkEntry(f_bg_picker, font=Theme.FONT_BODY, height=42)
        self.entry_splash_bg.pack(side="left", fill="x", expand=True, padx=(0, 6))
        btn_pick_bg = ctk.CTkButton(f_bg_picker, text="🎨 لون", width=60, height=42, font=Theme.FONT_TITLE, command=lambda: self._pick_color(self.entry_splash_bg))
        btn_pick_bg.pack(side="right")

        f_dur = ctk.CTkFrame(f_splash_opts, fg_color="transparent")
        f_dur.pack(side="right", fill="x", expand=True)
        ctk.CTkLabel(f_dur, text="مدة عرض شاشة البداية (ثواني):", font=Theme.FONT_TITLE).pack(anchor="w")
        self.entry_splash_dur = ctk.CTkEntry(f_dur, font=Theme.FONT_BODY, height=42)
        self.entry_splash_dur.pack(fill="x", pady=2)

        # UI Behavior & Controls
        ctk.CTkLabel(scroll, text="خيارات العرض والتفاعل (UI Controls):", font=Theme.FONT_SUBHEADER, text_color=Theme.PRIMARY).pack(anchor="w", pady=(22, 10))

        self.switch_pull_refresh = ctk.CTkSwitch(scroll, text="تفعيل التمرير للتحديث (Pull to Refresh)", font=Theme.FONT_TITLE)
        self.switch_pull_refresh.pack(anchor="w", pady=8)

        self.switch_progress_bar = ctk.CTkSwitch(scroll, text="إظهار شريط التحميل العلوي (Progress Bar)", font=Theme.FONT_TITLE)
        self.switch_progress_bar.pack(anchor="w", pady=8)

        f_prog_col = ctk.CTkFrame(scroll, fg_color="transparent")
        f_prog_col.pack(fill="x", pady=6)
        ctk.CTkLabel(f_prog_col, text="لون شريط التحميل (Progress Color):", font=Theme.FONT_TITLE).pack(side="left", padx=(0, 10))
        self.entry_progress_color = ctk.CTkEntry(f_prog_col, width=140, font=Theme.FONT_BODY, height=40)
        self.entry_progress_color.pack(side="left", padx=(0, 6))
        btn_pick_prog = ctk.CTkButton(f_prog_col, text="🎨 لون", width=60, height=40, font=Theme.FONT_TITLE, command=lambda: self._pick_color(self.entry_progress_color))
        btn_pick_prog.pack(side="left")

        self.switch_pinch_zoom = ctk.CTkSwitch(scroll, text="تفعيل التكبير/التصغير بأصبعين (Pinch to Zoom)", font=Theme.FONT_TITLE)
        self.switch_pinch_zoom.pack(anchor="w", pady=8)

    def _browse_icon_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("PNG Images", "*.png"), ("All Images", "*.*")])
        if filepath:
            self.entry_app_icon.delete(0, "end")
            self.entry_app_icon.insert(0, filepath)
            self._update_preview()

    def _browse_splash_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg"), ("All Files", "*.*")])
        if filepath:
            self.entry_splash_img.delete(0, "end")
            self.entry_splash_img.insert(0, filepath)

    def _pick_color(self, entry_widget):
        color = colorchooser.askcolor(title="اختر اللون")[1]
        if color:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, color)

    # ----------------------------------------------------
    # TAB 3: Permissions & Advanced Features
    # ----------------------------------------------------
    def _setup_tab_features(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=12)

        # Android Permissions
        ctk.CTkLabel(scroll, text="صلاحيات الأجهزة المطلوبة (Android Permissions):", font=Theme.FONT_SUBHEADER, text_color=Theme.PRIMARY).pack(anchor="w", pady=(10, 10))

        perm_frame = ctk.CTkFrame(scroll, fg_color=Theme.SURFACE_CARD, corner_radius=12)
        perm_frame.pack(fill="x", pady=4, ipadx=12, ipady=12)

        self.chk_internet = ctk.CTkCheckBox(perm_frame, text="صلاحية الإنترنت (Internet Access)", font=Theme.FONT_TITLE)
        self.chk_internet.grid(row=0, column=0, sticky="w", padx=14, pady=8)

        self.chk_camera = ctk.CTkCheckBox(perm_frame, text="صلاحية الكاميرا (Camera Access)", font=Theme.FONT_TITLE)
        self.chk_camera.grid(row=0, column=1, sticky="w", padx=14, pady=8)

        self.chk_microphone = ctk.CTkCheckBox(perm_frame, text="صلاحية الميكروفون (Microphone Access)", font=Theme.FONT_TITLE)
        self.chk_microphone.grid(row=1, column=0, sticky="w", padx=14, pady=8)

        self.chk_location = ctk.CTkCheckBox(perm_frame, text="صلاحية الموقع الجغرافي (GPS Location)", font=Theme.FONT_TITLE)
        self.chk_location.grid(row=1, column=1, sticky="w", padx=14, pady=8)

        self.chk_storage = ctk.CTkCheckBox(perm_frame, text="صلاحية مساحة التخزين (Storage Read/Write)", font=Theme.FONT_TITLE)
        self.chk_storage.grid(row=2, column=0, sticky="w", padx=14, pady=8)

        # Media & File Features
        ctk.CTkLabel(scroll, text="المميزات المتقدمة للتطبيق:", font=Theme.FONT_SUBHEADER, text_color=Theme.PRIMARY).pack(anchor="w", pady=(22, 10))

        self.chk_file_upload = ctk.CTkCheckBox(scroll, text="دعم رفع الصور والملفات من داخل التطبيق (File Upload)", font=Theme.FONT_TITLE)
        self.chk_file_upload.pack(anchor="w", pady=8)

        self.chk_file_download = ctk.CTkCheckBox(scroll, text="دعم تنزيل الملفات (File Download Support)", font=Theme.FONT_TITLE)
        self.chk_file_download.pack(anchor="w", pady=8)

        self.chk_media_play = ctk.CTkCheckBox(scroll, text="دعم تشغيل الفيديو والصوت HTML5 بملء الشاشة", font=Theme.FONT_TITLE)
        self.chk_media_play.pack(anchor="w", pady=8)

        self.chk_offline_page = ctk.CTkCheckBox(scroll, text="إظهار صفحة خطأ مخصصة عند انقطاع الاتصال (Custom Offline Page)", font=Theme.FONT_TITLE)
        self.chk_offline_page.pack(anchor="w", pady=8)

        # External Links Handling
        ctk.CTkLabel(scroll, text="معالجة الروابط الخارجية (External Links Handling):", font=Theme.FONT_TITLE, text_color=Theme.TEXT_PRIMARY).pack(anchor="w", pady=(22, 6))
        self.seg_ext_links = ctk.CTkSegmentedButton(
            scroll, values=["فتح الروابط الخارجية في المتصفح الافتراضي", "فتح كافة الروابط داخل التطبيق"],
            font=Theme.FONT_TITLE, height=40
        )
        self.seg_ext_links.pack(fill="x", pady=4)

    # ----------------------------------------------------
    # TAB 4: Monetization & Push Notifications
    # ----------------------------------------------------
    def _setup_tab_monetization(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=12)

        # AdMob
        ctk.CTkLabel(scroll, text="دمج إعلانات جوجل (Google AdMob):", font=Theme.FONT_SUBHEADER, text_color=Theme.PRIMARY).pack(anchor="w", pady=(10, 10))

        self.switch_admob = ctk.CTkSwitch(scroll, text="تفعيل إعلانات AdMob", font=Theme.FONT_TITLE, command=self._toggle_admob_fields)
        self.switch_admob.pack(anchor="w", pady=6)

        self.frame_admob = ctk.CTkFrame(scroll, fg_color=Theme.SURFACE_CARD, corner_radius=12)
        self.frame_admob.pack(fill="x", pady=8, ipadx=12, ipady=12)

        ctk.CTkLabel(self.frame_admob, text="معرف تطبيق AdMob (App ID):", font=Theme.FONT_TITLE).pack(anchor="w", padx=10, pady=(6, 2))
        self.entry_admob_app_id = ctk.CTkEntry(self.frame_admob, font=Theme.FONT_BODY, height=40)
        self.entry_admob_app_id.pack(fill="x", padx=10, pady=2)

        ctk.CTkLabel(self.frame_admob, text="معرف إعلان البانر (Banner Ad Unit ID):", font=Theme.FONT_TITLE).pack(anchor="w", padx=10, pady=(10, 2))
        self.entry_admob_banner = ctk.CTkEntry(self.frame_admob, font=Theme.FONT_BODY, height=40)
        self.entry_admob_banner.pack(fill="x", padx=10, pady=2)

        ctk.CTkLabel(self.frame_admob, text="معرف الإعلان البيني (Interstitial Ad Unit ID):", font=Theme.FONT_TITLE).pack(anchor="w", padx=10, pady=(10, 2))
        self.entry_admob_inter = ctk.CTkEntry(self.frame_admob, font=Theme.FONT_BODY, height=40)
        self.entry_admob_inter.pack(fill="x", padx=10, pady=2)

        # OneSignal Push Notifications
        ctk.CTkLabel(scroll, text="إشعارات الفلاش (OneSignal Push Notifications):", font=Theme.FONT_SUBHEADER, text_color=Theme.PRIMARY).pack(anchor="w", pady=(22, 10))

        self.switch_onesignal = ctk.CTkSwitch(scroll, text="تفعيل إشعارات OneSignal", font=Theme.FONT_TITLE, command=self._toggle_onesignal_fields)
        self.switch_onesignal.pack(anchor="w", pady=6)

        self.frame_onesignal = ctk.CTkFrame(scroll, fg_color=Theme.SURFACE_CARD, corner_radius=12)
        self.frame_onesignal.pack(fill="x", pady=8, ipadx=12, ipady=12)

        ctk.CTkLabel(self.frame_onesignal, text="معرف تطبيق OneSignal (OneSignal App ID):", font=Theme.FONT_TITLE).pack(anchor="w", padx=10, pady=(6, 2))
        self.entry_onesignal_id = ctk.CTkEntry(self.frame_onesignal, font=Theme.FONT_BODY, placeholder_text="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", height=40)
        self.entry_onesignal_id.pack(fill="x", padx=10, pady=2)

    def _toggle_admob_fields(self):
        enabled = self.switch_admob.get() == 1
        state = "normal" if enabled else "disabled"
        self.entry_admob_app_id.configure(state=state)
        self.entry_admob_banner.configure(state=state)
        self.entry_admob_inter.configure(state=state)

    def _toggle_onesignal_fields(self):
        enabled = self.switch_onesignal.get() == 1
        state = "normal" if enabled else "disabled"
        self.entry_onesignal_id.configure(state=state)

    # ----------------------------------------------------
    # TAB 5: Keystore & Build
    # ----------------------------------------------------
    def _setup_tab_build(self, parent):
        scroll = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=12, pady=12)

        # Keystore Configuration
        ctk.CTkLabel(scroll, text="توقيع التطبيق (Keystore & Signing):", font=Theme.FONT_SUBHEADER, text_color=Theme.PRIMARY).pack(anchor="w", pady=(10, 10))

        self.seg_keystore_type = ctk.CTkSegmentedButton(
            scroll, values=["مفتاح للتجربة (Debug Key)", "مفتاح خاص مخصص (Custom Keystore)"],
            font=Theme.FONT_TITLE, height=40,
            command=self._on_keystore_type_changed
        )
        self.seg_keystore_type.pack(fill="x", pady=4)

        self.frame_custom_ks = ctk.CTkFrame(scroll, fg_color=Theme.SURFACE_CARD, corner_radius=12)
        self.frame_custom_ks.pack(fill="x", pady=8, ipadx=12, ipady=12)

        ctk.CTkLabel(self.frame_custom_ks, text="مسار ملف Keystore (.jks / .keystore):", font=Theme.FONT_TITLE).pack(anchor="w", padx=10, pady=(6, 2))
        f_ks = ctk.CTkFrame(self.frame_custom_ks, fg_color="transparent")
        f_ks.pack(fill="x", padx=10, pady=2)
        self.entry_ks_path = ctk.CTkEntry(f_ks, font=Theme.FONT_BODY, height=42)
        self.entry_ks_path.pack(side="left", fill="x", expand=True, padx=(0, 10))
        btn_browse_ks = ctk.CTkButton(f_ks, text="استعراض...", width=110, height=42, font=Theme.FONT_TITLE, command=self._browse_keystore_file)
        btn_browse_ks.pack(side="right", padx=(0, 8))
        btn_gen_ks = ctk.CTkButton(f_ks, text="✨ مفتاح جديد", width=120, height=42, font=Theme.FONT_TITLE, fg_color=Theme.SUCCESS, command=self._open_keystore_dialog)
        btn_gen_ks.pack(side="right")

        f_ks_creds = ctk.CTkFrame(self.frame_custom_ks, fg_color="transparent")
        f_ks_creds.pack(fill="x", padx=10, pady=8)

        c1 = ctk.CTkFrame(f_ks_creds, fg_color="transparent")
        c1.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkLabel(c1, text="الاسم المستعار (Alias):", font=Theme.FONT_TITLE).pack(anchor="w")
        self.entry_ks_alias = ctk.CTkEntry(c1, font=Theme.FONT_BODY, height=40)
        self.entry_ks_alias.pack(fill="x", pady=2)

        c2 = ctk.CTkFrame(f_ks_creds, fg_color="transparent")
        c2.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkLabel(c2, text="كلمة مرور Keystore:", font=Theme.FONT_TITLE).pack(anchor="w")
        self.entry_ks_pass = ctk.CTkEntry(c2, show="*", font=Theme.FONT_BODY, height=40)
        self.entry_ks_pass.pack(fill="x", pady=2)

        c3 = ctk.CTkFrame(f_ks_creds, fg_color="transparent")
        c3.pack(side="right", fill="x", expand=True)
        ctk.CTkLabel(c3, text="كلمة مرور المفتاح (Key Pass):", font=Theme.FONT_TITLE).pack(anchor="w")
        self.entry_key_pass = ctk.CTkEntry(c3, show="*", font=Theme.FONT_BODY, height=40)
        self.entry_key_pass.pack(fill="x", pady=2)

        # Output Folder Settings
        ctk.CTkLabel(scroll, text="مجلد حفظ الملفات الناتجة (Build Output Directory):", font=Theme.FONT_TITLE, text_color=Theme.TEXT_PRIMARY).pack(anchor="w", pady=(22, 6))
        f_out = ctk.CTkFrame(scroll, fg_color="transparent")
        f_out.pack(fill="x", pady=2)
        self.entry_out_dir = ctk.CTkEntry(f_out, font=Theme.FONT_BODY, height=42)
        self.entry_out_dir.insert(0, self.output_dest_dir)
        self.entry_out_dir.pack(side="left", fill="x", expand=True, padx=(0, 10))
        btn_browse_out = ctk.CTkButton(f_out, text="تغيير المجلد...", width=130, height=42, font=Theme.FONT_TITLE, command=self._browse_output_dir)
        btn_browse_out.pack(side="right")

    def _on_keystore_type_changed(self, value):
        if "مخصص" in value:
            self.frame_custom_ks.pack(fill="x", pady=8, ipadx=12, ipady=12)
        else:
            self.frame_custom_ks.pack_forget()

    def _browse_keystore_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("Keystore Files", "*.jks;*.keystore"), ("All Files", "*.*")])
        if filepath:
            self.entry_ks_path.delete(0, "end")
            self.entry_ks_path.insert(0, filepath)

    def _open_keystore_dialog(self):
        def on_created(path, alias, storepass, keypass):
            self.seg_keystore_type.set("مفتاح خاص مخصص (Custom Keystore)")
            self._on_keystore_type_changed("مخصص")
            self.entry_ks_path.delete(0, "end")
            self.entry_ks_path.insert(0, path)
            self.entry_ks_alias.delete(0, "end")
            self.entry_ks_alias.insert(0, alias)
            self.entry_ks_pass.delete(0, "end")
            self.entry_ks_pass.insert(0, storepass)
            self.entry_key_pass.delete(0, "end")
            self.entry_key_pass.insert(0, keypass)

        KeystoreDialog(self, on_keystore_created=on_created)

    def _browse_output_dir(self):
        directory = filedialog.askdirectory()
        if directory:
            self.entry_out_dir.delete(0, "end")
            self.entry_out_dir.insert(0, directory)
            self.output_dest_dir = directory

    # ----------------------------------------------------
    # Load / Save Config Logic
    # ----------------------------------------------------
    def _collect_config_from_ui(self):
        is_url = "رابط" in self.seg_content_type.get()
        is_custom_ks = "مخصص" in self.seg_keystore_type.get()
        ext_mode = "browser" if "المتصفح" in self.seg_ext_links.get() else "webview"
        
        orient_val = self.seg_orientation.get()
        orient_map = {"عمودي (Portrait)": "portrait", "أفقي (Landscape)": "landscape", "تلقائي (Auto)": "auto"}

        config = {
            "app_title": self.entry_app_title.get().strip() or "تطبيقي المميز",
            "package_name": self.entry_package_name.get().strip() or "com.example.webapp",
            "version_name": self.entry_version_name.get().strip() or "1.0.0",
            "version_code": int(self.entry_version_code.get().strip() or 1),
            "content_type": "url" if is_url else "local",
            "web_url": self.entry_web_url.get().strip() or "https://google.com",
            "local_html_dir": self.entry_local_dir.get().strip(),
            "orientation": orient_map.get(orient_val, "auto"),
            
            "app_icon_path": self.entry_app_icon.get().strip(),
            "splash_image_path": self.entry_splash_img.get().strip(),
            "splash_bg_color": self.entry_splash_bg.get().strip() or "#1e293b",
            "splash_duration": int(self.entry_splash_dur.get().strip() or 3),
            "pull_to_refresh": self.switch_pull_refresh.get() == 1,
            "show_progress_bar": self.switch_progress_bar.get() == 1,
            "progress_bar_color": self.entry_progress_color.get().strip() or "#3b82f6",
            "pinch_to_zoom": self.switch_pinch_zoom.get() == 1,
            
            "perm_internet": self.chk_internet.get() == 1,
            "perm_camera": self.chk_camera.get() == 1,
            "perm_microphone": self.chk_microphone.get() == 1,
            "perm_location": self.chk_location.get() == 1,
            "perm_storage": self.chk_storage.get() == 1,
            "enable_file_upload": self.chk_file_upload.get() == 1,
            "enable_file_download": self.chk_file_download.get() == 1,
            "enable_media_playback": self.chk_media_play.get() == 1,
            "custom_offline_page": self.chk_offline_page.get() == 1,
            "external_links_mode": ext_mode,
            
            "admob_enabled": self.switch_admob.get() == 1,
            "admob_app_id": self.entry_admob_app_id.get().strip(),
            "admob_banner_id": self.entry_admob_banner.get().strip(),
            "admob_interstitial_id": self.entry_admob_inter.get().strip(),
            "onesignal_enabled": self.switch_onesignal.get() == 1,
            "onesignal_app_id": self.entry_onesignal_id.get().strip(),
            
            "keystore_type": "custom" if is_custom_ks else "debug",
            "keystore_path": self.entry_ks_path.get().strip(),
            "keystore_password": self.entry_ks_pass.get().strip(),
            "key_alias": self.entry_ks_alias.get().strip(),
            "key_password": self.entry_key_pass.get().strip()
        }
        return config

    def _load_config_to_ui(self, cfg):
        # Basic
        self.entry_app_title.delete(0, "end")
        self.entry_app_title.insert(0, cfg.get("app_title", ""))

        self.entry_package_name.delete(0, "end")
        self.entry_package_name.insert(0, cfg.get("package_name", ""))

        self.entry_version_name.delete(0, "end")
        self.entry_version_name.insert(0, cfg.get("version_name", "1.0.0"))

        self.entry_version_code.delete(0, "end")
        self.entry_version_code.insert(0, str(cfg.get("version_code", 1)))

        if cfg.get("content_type") == "local":
            self.seg_content_type.set("مجلد محلي (Local HTML Directory)")
            self._on_content_type_changed("مجلد")
        else:
            self.seg_content_type.set("رابط ويب (Web URL)")
            self._on_content_type_changed("رابط")

        self.entry_web_url.delete(0, "end")
        self.entry_web_url.insert(0, cfg.get("web_url", ""))

        self.entry_local_dir.delete(0, "end")
        self.entry_local_dir.insert(0, cfg.get("local_html_dir", ""))

        orient_rev = {"portrait": "عمودي (Portrait)", "landscape": "أفقي (Landscape)", "auto": "تلقائي (Auto)"}
        self.seg_orientation.set(orient_rev.get(cfg.get("orientation"), "تلقائي (Auto)"))

        # Branding
        self.entry_app_icon.delete(0, "end")
        self.entry_app_icon.insert(0, cfg.get("app_icon_path", ""))

        self.entry_splash_img.delete(0, "end")
        self.entry_splash_img.insert(0, cfg.get("splash_image_path", ""))

        self.entry_splash_bg.delete(0, "end")
        self.entry_splash_bg.insert(0, cfg.get("splash_bg_color", "#1e293b"))

        self.entry_splash_dur.delete(0, "end")
        self.entry_splash_dur.insert(0, str(cfg.get("splash_duration", 3)))

        if cfg.get("pull_to_refresh", True): self.switch_pull_refresh.select()
        else: self.switch_pull_refresh.deselect()

        if cfg.get("show_progress_bar", True): self.switch_progress_bar.select()
        else: self.switch_progress_bar.deselect()

        self.entry_progress_color.delete(0, "end")
        self.entry_progress_color.insert(0, cfg.get("progress_bar_color", "#3b82f6"))

        if cfg.get("pinch_to_zoom", True): self.switch_pinch_zoom.select()
        else: self.switch_pinch_zoom.deselect()

        # Features
        if cfg.get("perm_internet", True): self.chk_internet.select()
        else: self.chk_internet.deselect()

        if cfg.get("perm_camera"): self.chk_camera.select()
        else: self.chk_camera.deselect()

        if cfg.get("perm_microphone"): self.chk_microphone.select()
        else: self.chk_microphone.deselect()

        if cfg.get("perm_location"): self.chk_location.select()
        else: self.chk_location.deselect()

        if cfg.get("perm_storage", True): self.chk_storage.select()
        else: self.chk_storage.deselect()

        if cfg.get("enable_file_upload", True): self.chk_file_upload.select()
        else: self.chk_file_upload.deselect()

        if cfg.get("enable_file_download", True): self.chk_file_download.select()
        else: self.chk_file_download.deselect()

        if cfg.get("enable_media_playback", True): self.chk_media_play.select()
        else: self.chk_media_play.deselect()

        if cfg.get("custom_offline_page", True): self.chk_offline_page.select()
        else: self.chk_offline_page.deselect()

        ext_val = "فتح كافة الروابط داخل التطبيق" if cfg.get("external_links_mode") == "webview" else "فتح الروابط الخارجية في المتصفح الافتراضي"
        self.seg_ext_links.set(ext_val)

        # Monetization
        if cfg.get("admob_enabled"): self.switch_admob.select()
        else: self.switch_admob.deselect()
        self._toggle_admob_fields()

        self.entry_admob_app_id.delete(0, "end")
        self.entry_admob_app_id.insert(0, cfg.get("admob_app_id", ""))

        self.entry_admob_banner.delete(0, "end")
        self.entry_admob_banner.insert(0, cfg.get("admob_banner_id", ""))

        self.entry_admob_inter.delete(0, "end")
        self.entry_admob_inter.insert(0, cfg.get("admob_interstitial_id", ""))

        if cfg.get("onesignal_enabled"): self.switch_onesignal.select()
        else: self.switch_onesignal.deselect()
        self._toggle_onesignal_fields()

        self.entry_onesignal_id.delete(0, "end")
        self.entry_onesignal_id.insert(0, cfg.get("onesignal_app_id", ""))

        # Keystore & Build
        if cfg.get("keystore_type") == "custom":
            self.seg_keystore_type.set("مفتاح خاص مخصص (Custom Keystore)")
            self._on_keystore_type_changed("مخصص")
        else:
            self.seg_keystore_type.set("مفتاح للتجربة (Debug Key)")
            self._on_keystore_type_changed("تجربة")

        self.entry_ks_path.delete(0, "end")
        self.entry_ks_path.insert(0, cfg.get("keystore_path", ""))

        self.entry_ks_alias.delete(0, "end")
        self.entry_ks_alias.insert(0, cfg.get("key_alias", ""))

        self.entry_ks_pass.delete(0, "end")
        self.entry_ks_pass.insert(0, cfg.get("keystore_password", ""))

        self.entry_key_pass.delete(0, "end")
        self.entry_key_pass.insert(0, cfg.get("key_password", ""))

        self._update_preview()

    def _update_preview(self):
        title = self.entry_app_title.get().strip() or "تطبيقي المميز"
        pkg = self.entry_package_name.get().strip() or "com.example.webapp"
        self.lbl_preview_title.configure(text=title)
        self.lbl_preview_pkg.configure(text=pkg)

        icon_path = self.entry_app_icon.get().strip()
        if icon_path and os.path.exists(icon_path):
            try:
                img = Image.open(icon_path).resize((72, 72), Image.Resampling.LANCZOS)
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(72, 72))
                self.lbl_preview_icon.configure(image=ctk_img, text="")
            except Exception:
                self.lbl_preview_icon.configure(image=None, text="[أيقونة]")

    def _save_project_file(self):
        filepath = filedialog.asksaveasfilename(
            defaultextension=".wtaproj",
            filetypes=[("WebToApp Project", "*.wtaproj"), ("JSON Files", "*.json")]
        )
        if filepath:
            cfg = self._collect_config_from_ui()
            ProjectConfig.save_to_file(cfg, filepath)
            messagebox.showinfo("تم الحفظ", "تم حفظ إعدادات المشروع بنجاح!")

    def _load_project_file(self):
        filepath = filedialog.askopenfilename(
            filetypes=[("WebToApp Project", "*.wtaproj;*.json"), ("All Files", "*.*")]
        )
        if filepath:
            cfg = ProjectConfig.load_from_file(filepath)
            self._load_config_to_ui(cfg)
            messagebox.showinfo("تم التحميل", "تم فتح إعدادات المشروع بنجاح!")

    # ----------------------------------------------------
    # Build Execution Engine
    # ----------------------------------------------------
    def _start_build(self, is_aab=False):
        cfg = self._collect_config_from_ui()
        out_dir = self.entry_out_dir.get().strip() or self.output_dest_dir

        target_type = "AAB" if is_aab else "APK"

        if not cfg["package_name"] or len(cfg["package_name"].split(".")) < 2:
            messagebox.showerror("خطأ في البيانات", "يرجى كتابة اسم حزمة صحيح (مثال: com.myapp.service).")
            return

        self.txt_console.delete("1.0", "end")
        self._append_log(f"=========================================\n")
        self._append_log(f"🚀 بدء عملية إنشاء مشروع أندرويد وبناء {target_type}...\n")
        self._append_log(f"=========================================\n")

        self.btn_fast_apk.configure(state="disabled")
        self.btn_fast_aab.configure(state="disabled")

        # 1. Generate Project Structure
        temp_project_dir = os.path.join(os.environ.get("TEMP", "C:\\Temp"), "WebToApp_GeneratedProject")
        try:
            self._append_log("🔨 جاري توليد ملفات وسورس كود مشروع أندرويد...\n")
            generator = ProjectGenerator(cfg, temp_project_dir)
            generated_dir = generator.generate()
            self._append_log(f"✅ تم توليد المشروع بنجاح في: {generated_dir}\n")
        except Exception as ex:
            self._append_log(f"❌ خطأ أثناء توليد المشروع: {str(ex)}\n")
            self._on_build_completed(False, str(ex), None)
            return

        # 2. Run Gradle Builder
        self.builder = AndroidBuilder(generated_dir, android_sdk=self.android_sdk, java_home=self.java_home)
        self.builder.build_apk(
            output_destination_dir=out_dir,
            is_aab=is_aab,
            app_title=cfg.get("app_title"),
            log_callback=self._append_log,
            completion_callback=self._on_build_completed
        )

    def _append_log(self, text):
        self.txt_console.insert("end", text)
        self.txt_console.see("end")

    def _on_build_completed(self, success, message, artifact_path):
        self.btn_fast_apk.configure(state="normal")
        self.btn_fast_aab.configure(state="normal")

        if success:
            messagebox.showinfo("نجاح التجميع 🎉", f"{message}\n\nمسار الملف الناتج:\n{artifact_path}")
        else:
            messagebox.showerror("فشل التجميع ❌", f"{message}\nيرجى التحقق من السجلات في نافذة Console.")

    def _open_output_dir(self):
        out_dir = self.entry_out_dir.get().strip() or self.output_dest_dir
        os.makedirs(out_dir, exist_ok=True)
        os.startfile(out_dir)

    def _show_about_dialog(self):
        messagebox.showinfo(
            "بيانات المطور والاتصال 👨‍💻",
            "✨ WebToApp Studio Pro\n"
            "------------------------------------------\n"
            "👨‍💻 المهندس المطور: Eng_Ahmed Abdelaziz Mohamed\n"
            "📧 البريد الإلكتروني: eng.ahmed.abdelaziz.2022@gmail.com\n"
            "📞 الهاتف / واتساب: +201024735044\n"
            "------------------------------------------\n"
            "تطوير احترافي لتطبيقات سطح المكتب والأندرويد."
        )
