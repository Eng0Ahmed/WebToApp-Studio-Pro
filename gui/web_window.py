import os
import sys
import json
import threading
import tkinter as tk
from tkinter import filedialog
import webview

from backend.config_manager import ProjectConfig
from backend.sdk_utils import SDKUtils
from backend.project_generator import ProjectGenerator
from backend.builder import AndroidBuilder

class BridgeApi:
    """Two-way bridge between pywebview frontend and Python backend."""

    def __init__(self):
        self._window = None
        self.output_dest_dir = os.path.expanduser(r"~\Desktop\WebToApp_Builds")
        os.makedirs(self.output_dest_dir, exist_ok=True)
        self.android_sdk = SDKUtils.detect_android_sdk()
        self.java_home = SDKUtils.detect_java_home()
        self.builder = None

    def set_window(self, window):
        self._window = window

    def _open_tk_dialog(self, dialog_func, *args, **kwargs):
        """Runs Tkinter file dialog with a hidden temporary root window."""
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        try:
            result = dialog_func(*args, **kwargs)
        finally:
            root.destroy()
        return result or ""

    def get_initial_data(self):
        """Returns initial system and default configuration data to JavaScript."""
        return {
            "config": ProjectConfig.get_default(),
            "android_sdk": self.android_sdk,
            "java_home": self.java_home,
            "output_dir": self.output_dest_dir
        }

    def select_file(self, file_filter="All Files (*.*)|*.*"):
        """Opens native file picker dialog."""
        types = [("Compatible Files", "*.*")]
        if "Image" in file_filter:
            types = [("Image Files", "*.png;*.jpg;*.jpeg;*.webp"), ("All Files", "*.*")]
        elif "Keystore" in file_filter:
            types = [("Keystore Files", "*.jks;*.keystore"), ("All Files", "*.*")]

        return self._open_tk_dialog(
            filedialog.askopenfilename,
            title="اختيار ملف / Select File",
            filetypes=types
        )

    def select_directory(self):
        """Opens native folder picker dialog."""
        return self._open_tk_dialog(
            filedialog.askdirectory,
            title="تحديد مجلد / Select Folder"
        )

    def select_save_file(self, file_filter="All Files (*.*)", default_name=""):
        """Opens native save file dialog."""
        types = [("Save Files", "*.*")]
        if ".jks" in file_filter:
            types = [("Java Keystore", "*.jks"), ("All Files", "*.*")]
        elif ".wtaproj" in file_filter:
            types = [("WebToApp Project", "*.wtaproj"), ("All Files", "*.*")]

        return self._open_tk_dialog(
            filedialog.asksaveasfilename,
            title="حفظ باسم / Save As",
            initialfile=default_name,
            filetypes=types
        )

    def save_project_file(self, config_dict):
        """Saves current configuration as a .wtaproj JSON file."""
        filepath = self._open_tk_dialog(
            filedialog.asksaveasfilename,
            title="حفظ ملف المشروع",
            defaultextension=".wtaproj",
            filetypes=[("WebToApp Project (*.wtaproj)", "*.wtaproj"), ("JSON File (*.json)", "*.json")]
        )
        if filepath:
            ProjectConfig.save_to_file(config_dict, filepath)
            return {"success": True, "path": filepath}
        return {"success": False}

    def load_project_file(self):
        """Loads configuration from a .wtaproj JSON file."""
        filepath = self._open_tk_dialog(
            filedialog.askopenfilename,
            title="فتح ملف المشروع",
            filetypes=[("WebToApp Project (*.wtaproj;*.json)", "*.wtaproj;*.json"), ("All Files", "*.*")]
        )
        if filepath and os.path.exists(filepath):
            config = ProjectConfig.load_from_file(filepath)
            return {"success": True, "path": filepath, "config": config}
        return {"success": False}

    def generate_keystore(self, params):
        """Generates digital JKS signing keystore file."""
        try:
            success, msg = SDKUtils.generate_keystore(
                output_path=params.get("output_path"),
                alias=params.get("alias"),
                password=params.get("password"),
                key_password=params.get("key_password"),
                first_last_name=params.get("first_last_name", "Developer"),
                org_unit=params.get("org_unit", "Dev"),
                org_name=params.get("org_name", "Studio"),
                city=params.get("city", "City"),
                state=params.get("state", "State"),
                country_code=params.get("country_code", "EG"),
                validity_years=params.get("validity_years", 25)
            )
            return {"success": success, "message": msg}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def open_output_dir(self):
        """Opens the output builds folder in Windows Explorer."""
        if os.path.exists(self.output_dest_dir):
            os.startfile(self.output_dest_dir)
            return True
        return False

    def start_build(self, config_dict, is_aab=False):
        """Executes full Android project generation and Gradle compilation in a background worker."""
        def worker():
            target_type = "AAB (Google Play)" if is_aab else "APK (Direct Install)"
            
            def log_callback(line):
                if self._window:
                    clean_line = json.dumps(str(line))
                    self._window.evaluate_js(f"window.onBuildLog({clean_line});")

            def progress_callback(step_idx):
                if self._window:
                    self._window.evaluate_js(f"window.onBuildProgress({step_idx});")

            def completion_callback(success, message, artifact_path):
                if self._window:
                    s_js = "true" if success else "false"
                    m_js = json.dumps(str(message))
                    a_js = json.dumps(str(artifact_path or ""))
                    self._window.evaluate_js(f"window.onBuildComplete({s_js}, {m_js}, {a_js});")

            try:
                progress_callback(1)
                log_callback(f"🚀 بدء عملية بناء وتجميع: {target_type}\n")
                log_callback(f"اسم التطبيق: {config_dict.get('app_title')}\n")
                log_callback(f"اسم الحزمة: {config_dict.get('package_name')}\n")
                log_callback(f"نوع المحتوى: {config_dict.get('content_type')}\n\n")

                # Step 2: Project Generation
                progress_callback(2)
                log_callback("⚙️ [المرحلة 2/5] توليد كود مشروع الأندرويد والـ Gradle و Manifest...\n")

                app_name_clean = "".join(c for c in config_dict.get("app_title", "App") if c.isalnum() or c in (' ', '_', '-')).strip() or "WebApp"
                temp_dir = os.path.join(os.path.expanduser(r"~\AppData\Local\Temp"), f"WebToApp_Build_{app_name_clean}")

                generator = ProjectGenerator(config_dict, temp_dir)
                generator.generate()
                log_callback("✓ تم توليد ملفات المشروع بنجاح.\n\n")

                # Step 3: Keystore check
                progress_callback(3)
                log_callback("🔒 [المرحلة 3/5] إعداد وتوثيق شهادة التوقيع الرقمي (Keystore)...\n")
                if config_dict.get("keystore_type") == "custom":
                    log_callback(f"✓ تم ضبط التوقيع بمفتاح مخصص: {config_dict.get('keystore_path')}\n\n")
                else:
                    log_callback("✓ تم ضبط التوقيع بمفتاح Debug التجريبي التلقائي.\n\n")

                # Step 4: Gradle compilation
                progress_callback(4)
                log_callback(f"🔨 [المرحلة 4/5] تشغيل محرك Gradle لتجميع ملف الـ {target_type}...\n")
                
                self.builder = AndroidBuilder(temp_dir, self.android_sdk, self.java_home)
                self.builder.build_apk(
                    output_destination_dir=self.output_dest_dir,
                    is_aab=is_aab,
                    app_title=config_dict.get("app_title"),
                    log_callback=log_callback,
                    completion_callback=completion_callback
                )

            except Exception as e:
                import traceback
                err_msg = traceback.format_exc()
                log_callback(f"\n❌ خطأ غير متوقع أثناء التجميع:\n{err_msg}\n")
                completion_callback(False, f"فشلت العملية: {str(e)}", None)

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        return True


class WebWindow:
    """Main Web-based Application Window using pywebview."""

    @staticmethod
    def run():
        import tempfile
        user_data = os.path.join(os.environ.get('LOCALAPPDATA', tempfile.gettempdir()), 'WebToAppStudioPro', 'WebView2')
        os.makedirs(user_data, exist_ok=True)
        os.environ['WEBVIEW2_USER_DATA_FOLDER'] = user_data

        repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        html_file = os.path.join(repo_dir, "web", "index.html")

        if not os.path.exists(html_file):
            raise FileNotFoundError(f"HTML entrypoint not found: {html_file}")

        api = BridgeApi()
        window = webview.create_window(
            title="WebToApp Studio Pro - تحويل المواقع لـ APK & AAB",
            url=html_file,
            js_api=api,
            width=1280,
            height=860,
            min_size=(1060, 700),
            background_color='#090d16'
        )
        api.set_window(window)
        webview.start(debug=False)
