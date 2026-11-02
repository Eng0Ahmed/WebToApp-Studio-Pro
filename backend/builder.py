import os
import subprocess
import shutil
import threading
import re
from backend.sdk_utils import SDKUtils

class AndroidBuilder:
    """Build manager that executes Gradle commands, streams logs, and collects build artifacts."""

    def __init__(self, project_dir, android_sdk=None, java_home=None):
        self.project_dir = os.path.abspath(project_dir)
        self.android_sdk = android_sdk or SDKUtils.detect_android_sdk()
        self.java_home = java_home or SDKUtils.detect_java_home()
        self.system_gradle = SDKUtils.detect_gradle()
        self.is_building = False
        self._proc = None

    def _safe_log(self, callback, message):
        if not callback:
            return
        try:
            callback(message)
        except Exception:
            try:
                cleaned = message.encode('ascii', errors='ignore').decode('ascii')
                callback(cleaned)
            except Exception:
                pass

    def build_apk(self, output_destination_dir, is_aab=False, app_title=None, log_callback=None, completion_callback=None):
        """Runs gradle build task in a separate background thread."""
        def run_thread():
            self.is_building = True
            target_type = "AAB" if is_aab else "APK"
            
            self._safe_log(log_callback, f"=== بدء عملية بناء تطبيق {target_type} ===\n")
            self._safe_log(log_callback, f"مسار المشروع: {self.project_dir}\n")

            env = os.environ.copy()
            if self.android_sdk:
                env["ANDROID_HOME"] = self.android_sdk
                env["ANDROID_SDK_ROOT"] = self.android_sdk
                self._safe_log(log_callback, f"Android SDK: {self.android_sdk}\n")

            if self.java_home:
                env["JAVA_HOME"] = self.java_home
                env["PATH"] = os.path.join(self.java_home, "bin") + os.pathsep + env.get("PATH", "")
                self._safe_log(log_callback, f"Java JDK: {self.java_home}\n")

            gradle_bin = self.system_gradle
            if not gradle_bin or not os.path.exists(gradle_bin):
                gradle_bin = os.path.join(self.project_dir, "gradlew.bat")

            if not os.path.exists(gradle_bin):
                self._safe_log(log_callback, "خطأ: لم يتم العثور على أداة Gradle للتجميع.\n")
                self.is_building = False
                if completion_callback:
                    completion_callback(False, "أداة Gradle غير متوفرة", None)
                return

            task = "bundleRelease" if is_aab else "assembleRelease"
            cmd = [gradle_bin, task, "--stacktrace"]

            self._safe_log(log_callback, f"أداة البناء: {gradle_bin}\n")
            self._safe_log(log_callback, f"الأمر: {task}\n\n")

            try:
                self._proc = subprocess.Popen(
                    cmd,
                    cwd=self.project_dir,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    bufsize=1,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
                )

                for line in iter(self._proc.stdout.readline, ''):
                    self._safe_log(log_callback, line)

                self._proc.stdout.close()
                return_code = self._proc.wait()

                if return_code == 0:
                    artifact_path = self._find_and_copy_artifact(output_destination_dir, is_aab, app_title)
                    if artifact_path and os.path.exists(artifact_path):
                        self._safe_log(log_callback, f"\nتم التجميع بنجاح!\nالملف الناتج: {artifact_path}\n")
                        if completion_callback:
                            completion_callback(True, "تم البناء بنجاح!", artifact_path)
                    else:
                        self._safe_log(log_callback, "\nتم الانتهاء ولكن لم يتم العثور على الملف الناتج.\n")
                        if completion_callback:
                            completion_callback(False, "لم يتم العثور على ملف الناتج النهائي", None)
                else:
                    self._safe_log(log_callback, f"\nفشلت عملية البناء. كود الخطأ: {return_code}\n")
                    if completion_callback:
                        completion_callback(False, f"فشلت عملية البناء (Code {return_code})", None)

            except Exception as ex:
                self._safe_log(log_callback, f"\nحدث استثناء أثناء البناء: {str(ex)}\n")
                if completion_callback:
                    completion_callback(False, str(ex), None)
            finally:
                self.is_building = False

        thread = threading.Thread(target=run_thread, daemon=True)
        thread.start()

    def cancel_build(self):
        """Cancels running build process if active."""
        if self._proc and self._proc.poll() is None:
            self._proc.terminate()
            self.is_building = False

    def _find_and_copy_artifact(self, dest_dir, is_aab, app_title=None):
        """Finds generated APK or AAB in app/build/outputs and copies to destination using app title."""
        os.makedirs(dest_dir, exist_ok=True)
        ext = ".aab" if is_aab else ".apk"
        search_root = os.path.join(self.project_dir, "app", "build", "outputs")
        
        found_file = None
        for root, dirs, files in os.walk(search_root):
            for file in files:
                if file.endswith(ext) and ("release" in file.lower() or "debug" in file.lower()):
                    found_file = os.path.join(root, file)
                    break
            if found_file:
                break
                
        if found_file:
            if app_title and app_title.strip():
                clean_title = re.sub(r'[\\/*?:"<>|]', '_', app_title.strip()).replace(" ", "_")
                dest_name = f"{clean_title}{ext}"
            else:
                dest_name = f"WebToApp_Build{ext}"
                
            dest_path = os.path.join(dest_dir, dest_name)
            shutil.copy2(found_file, dest_path)
            return dest_path
        return None
