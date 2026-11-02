import os
import sys
import json
import time
import queue
import socket
import threading
import subprocess
import tkinter as tk
from tkinter import filedialog
from bottle import Bottle, request, response, static_file

from backend.config_manager import ProjectConfig
from backend.sdk_utils import SDKUtils
from backend.project_generator import ProjectGenerator
from backend.builder import AndroidBuilder

app = Bottle()

# Global state
log_queue = queue.Queue()
is_building = False
current_step = 1
repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
web_dir = os.path.join(repo_dir, "web")
output_dest_dir = os.path.expanduser(r"~\Desktop\WebToApp_Builds")
os.makedirs(output_dest_dir, exist_ok=True)

def open_tk_dialog(dialog_func, *args, **kwargs):
    """Runs a Tkinter dialog in an isolated thread with a hidden root."""
    result = [""]
    def _run():
        root = tk.Tk()
        root.withdraw()
        root.attributes("-topmost", True)
        try:
            res = dialog_func(*args, **kwargs)
            result[0] = res or ""
        finally:
            root.destroy()
    t = threading.Thread(target=_run)
    t.start()
    t.join()
    return result[0]

# --- Static Routes ---
@app.route('/')
def serve_index():
    return static_file('index.html', root=web_dir)

@app.route('/<filepath:path>')
def serve_static(filepath):
    return static_file(filepath, root=web_dir)

# --- API Endpoints ---
@app.route('/api/initial-data')
def get_initial_data():
    response.content_type = 'application/json'
    return json.dumps({
        "config": ProjectConfig.get_default(),
        "android_sdk": SDKUtils.detect_android_sdk(),
        "java_home": SDKUtils.detect_java_home(),
        "output_dir": output_dest_dir
    })

@app.route('/api/browse-file', method='POST')
def browse_file():
    data = request.json or {}
    file_filter = data.get("filter", "All Files (*.*)")
    types = [("All Files", "*.*")]
    if "Image" in file_filter:
        types = [("Image Files", "*.png;*.jpg;*.jpeg;*.webp"), ("All Files", "*.*")]
    elif "Keystore" in file_filter:
        types = [("Keystore Files", "*.jks;*.keystore"), ("All Files", "*.*")]

    path = open_tk_dialog(
        filedialog.askopenfilename,
        title="اختيار ملف / Select File",
        filetypes=types
    )
    response.content_type = 'application/json'
    return json.dumps({"path": path})

@app.route('/api/browse-dir', method='POST')
def browse_dir():
    path = open_tk_dialog(
        filedialog.askdirectory,
        title="تحديد مجلد / Select Folder"
    )
    response.content_type = 'application/json'
    return json.dumps({"path": path})

@app.route('/api/browse-save', method='POST')
def browse_save():
    data = request.json or {}
    default_name = data.get("default_name", "")
    types = [("Java Keystore", "*.jks"), ("All Files", "*.*")]
    path = open_tk_dialog(
        filedialog.asksaveasfilename,
        title="حفظ باسم / Save As",
        initialfile=default_name,
        filetypes=types
    )
    response.content_type = 'application/json'
    return json.dumps({"path": path})

@app.route('/api/save-project', method='POST')
def save_project():
    data = request.json or {}
    config_dict = data.get("config", {})
    filepath = open_tk_dialog(
        filedialog.asksaveasfilename,
        title="حفظ ملف المشروع",
        defaultextension=".wtaproj",
        filetypes=[("WebToApp Project (*.wtaproj)", "*.wtaproj"), ("JSON File (*.json)", "*.json")]
    )
    response.content_type = 'application/json'
    if filepath:
        ProjectConfig.save_to_file(config_dict, filepath)
        return json.dumps({"success": True, "path": filepath})
    return json.dumps({"success": False})

@app.route('/api/load-project', method='POST')
def load_project():
    filepath = open_tk_dialog(
        filedialog.askopenfilename,
        title="فتح ملف المشروع",
        filetypes=[("WebToApp Project (*.wtaproj;*.json)", "*.wtaproj;*.json"), ("All Files", "*.*")]
    )
    response.content_type = 'application/json'
    if filepath and os.path.exists(filepath):
        config = ProjectConfig.load_from_file(filepath)
        return json.dumps({"success": True, "path": filepath, "config": config})
    return json.dumps({"success": False})

@app.route('/api/generate-keystore', method='POST')
def generate_keystore():
    params = request.json or {}
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
        response.content_type = 'application/json'
        return json.dumps({"success": success, "message": msg})
    except Exception as e:
        response.content_type = 'application/json'
        return json.dumps({"success": False, "error": str(e)})

@app.route('/api/open-output-dir', method='POST')
def open_output_dir_handler():
    if os.path.exists(output_dest_dir):
        os.startfile(output_dest_dir)
        return json.dumps({"success": True})
    return json.dumps({"success": False})

# --- Build Process & Streaming Logs ---
@app.route('/api/start-build', method='POST')
def start_build():
    global is_building
    if is_building:
        return json.dumps({"success": False, "error": "Build already in progress"})

    data = request.json or {}
    config_dict = data.get("config", {})
    is_aab = data.get("is_aab", False)

    def worker():
        global is_building
        is_building = True
        target_type = "AAB (Google Play)" if is_aab else "APK (Direct Install)"

        def push_log(text):
            log_queue.put({"type": "log", "text": text})

        def push_step(step_num):
            log_queue.put({"type": "progress", "step": step_num})

        def push_complete(success, message, artifact_path):
            log_queue.put({"type": "complete", "success": success, "message": message, "artifact": artifact_path or ""})

        try:
            push_step(1)
            push_log(f"🚀 بدء عملية بناء وتجميع: {target_type}\n")
            push_log(f"اسم التطبيق: {config_dict.get('app_title')}\n")
            push_log(f"اسم الحزمة: {config_dict.get('package_name')}\n")
            push_log(f"نوع المحتوى: {config_dict.get('content_type')}\n\n")

            # Step 2: Generate project
            push_step(2)
            push_log("⚙️ [المرحلة 2/5] توليد كود مشروع الأندرويد والـ Gradle و Manifest...\n")

            app_name_clean = "".join(c for c in config_dict.get("app_title", "App") if c.isalnum() or c in (' ', '_', '-')).strip() or "WebApp"
            temp_dir = os.path.join(os.path.expanduser(r"~\AppData\Local\Temp"), f"WebToApp_Build_{app_name_clean}")

            generator = ProjectGenerator(config_dict, temp_dir)
            generator.generate()
            push_log("✓ تم توليد ملفات المشروع بنجاح.\n\n")

            # Step 3: Keystore
            push_step(3)
            push_log("🔒 [المرحلة 3/5] إعداد وتوثيق شهادة التوقيع الرقمي (Keystore)...\n")
            if config_dict.get("keystore_type") == "custom":
                push_log(f"✓ تم ضبط التوقيع بمفتاح مخصص: {config_dict.get('keystore_path')}\n\n")
            else:
                push_log("✓ تم ضبط التوقيع بمفتاح Debug التجريبي التلقائي.\n\n")

            # Step 4: Gradle
            push_step(4)
            push_log(f"🔨 [المرحلة 4/5] تشغيل محرك Gradle لتجميع ملف الـ {target_type}...\n")

            builder = AndroidBuilder(temp_dir, SDKUtils.detect_android_sdk(), SDKUtils.detect_java_home())
            builder.build_apk(
                output_destination_dir=output_dest_dir,
                is_aab=is_aab,
                app_title=config_dict.get("app_title"),
                log_callback=push_log,
                completion_callback=lambda s, m, a: push_complete(s, m, a)
            )

        except Exception as e:
            import traceback
            err_msg = traceback.format_exc()
            push_log(f"\n❌ خطأ غير متوقع أثناء التجميع:\n{err_msg}\n")
            push_complete(False, f"فشلت العملية: {str(e)}", None)
        finally:
            is_building = False

    t = threading.Thread(target=worker, daemon=True)
    t.start()
    return json.dumps({"success": True})

@app.route('/api/stream-logs')
def stream_logs():
    response.content_type = 'text/event-stream'
    response.cache_control = 'no-cache'
    response.headers['Connection'] = 'keep-alive'

    def event_stream():
        while True:
            try:
                item = log_queue.get(timeout=1.0)
                yield f"data: {json.dumps(item)}\n\n"
            except queue.Empty:
                yield ": keepalive\n\n"

    return event_stream()

@app.route('/api/exit', method=['POST', 'GET'])
def exit_app():
    def shutdown():
        time.sleep(0.5)
        os._exit(0)
    threading.Thread(target=shutdown, daemon=True).start()
    return "ok"

def find_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port

def launch_app():
    port = find_free_port()
    url = f"http://127.0.0.1:{port}"

    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        os.path.expanduser(r"~\AppData\Local\Microsoft\Edge\Application\msedge.exe")
    ]
    edge_bin = next((p for p in edge_paths if os.path.exists(p)), None)

    def opener():
        time.sleep(0.6)
        if edge_bin:
            user_data = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "WebToAppStudioPro", "EdgeProfile")
            os.makedirs(user_data, exist_ok=True)
            cmd = [
                edge_bin,
                f"--app={url}",
                "--window-size=1280,860",
                f"--user-data-dir={user_data}"
            ]
            subprocess.Popen(cmd)
        else:
            import webbrowser
            webbrowser.open(url)

    threading.Thread(target=opener, daemon=True).start()

    print(f"WebToApp Studio Pro server running at {url}")
    app.run(host='127.0.0.1', port=port, quiet=True)

if __name__ == '__main__':
    launch_app()
