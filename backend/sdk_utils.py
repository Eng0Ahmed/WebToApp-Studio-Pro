import os
import subprocess
import shutil
import urllib.request
import zipfile

class SDKUtils:
    """Utility class for detecting Android SDK, JDK, Gradle, keytool, and generating Keystore files."""
    
    @staticmethod
    def detect_android_sdk():
        """Returns the Android SDK path if found, or None."""
        possible_paths = [
            os.environ.get("ANDROID_HOME"),
            os.environ.get("ANDROID_SDK_ROOT"),
            os.path.expanduser(r"~\AppData\Local\Android\Sdk"),
            r"C:\Android\Sdk",
            r"C:\Program Files (x86)\Android\android-sdk"
        ]
        
        for path in possible_paths:
            if path and os.path.isdir(path):
                if os.path.exists(os.path.join(path, "platforms")) or os.path.exists(os.path.join(path, "build-tools")):
                    return os.path.abspath(path)
        return None

    @staticmethod
    def detect_java_home():
        """Returns JAVA_HOME path (preferring a full JDK with tools.jar)."""
        java_home = os.environ.get("JAVA_HOME")
        if java_home and os.path.exists(os.path.join(java_home, "bin", "javac.exe")):
            return java_home
            
        # Check custom downloaded OpenJDK 8
        custom_jdk = os.path.expanduser(r"~\.jdk\jdk8u392-b08")
        if os.path.exists(os.path.join(custom_jdk, "bin", "javac.exe")):
            return custom_jdk

        search_dirs = [
            os.path.expanduser(r"~\.jdk"),
            r"C:\Program Files\Java",
            r"C:\Program Files\Android\Android Studio\jbr"
        ]
        
        for s_dir in search_dirs:
            if os.path.exists(s_dir):
                for root, dirs, files in os.walk(s_dir):
                    if "javac.exe" in files:
                        jdk_path = os.path.dirname(os.path.dirname(os.path.join(root, "javac.exe")))
                        return jdk_path

        return r"C:\Program Files\Java\jre1.8.0_251"

    @staticmethod
    def detect_gradle():
        """Detects or auto-configures a Java-8 compatible Gradle binary executable (Gradle 6.8.3)."""
        gradle_dists = os.path.expanduser(r"~\.gradle\wrapper\dists")
        
        preferred = ["gradle-6.8.3", "gradle-6.9", "gradle-7.0", "gradle-7.2"]
        if os.path.exists(gradle_dists):
            for pref in preferred:
                for root, dirs, files in os.walk(gradle_dists):
                    if pref in root and ("gradle.bat" in files or "gradle" in files):
                        bin_path = os.path.join(root, "gradle.bat" if os.name == 'nt' else "gradle")
                        if os.path.basename(os.path.dirname(bin_path)).lower() == "bin":
                            return bin_path

        standalone_dir = os.path.expanduser(r"~\.gradle\wrapper\dists\gradle-6.8.3-bin")
        bat = os.path.join(standalone_dir, "gradle-6.8.3", "bin", "gradle.bat" if os.name == 'nt' else "gradle")
        if os.path.exists(bat):
            return bat

        return shutil.which("gradle")

    @staticmethod
    def get_keytool_path():
        """Finds keytool executable path."""
        keytool_in_path = shutil.which("keytool")
        if keytool_in_path:
            return keytool_in_path
            
        java_home = SDKUtils.detect_java_home()
        if java_home:
            kt = os.path.join(java_home, "bin", "keytool.exe" if os.name == 'nt' else "keytool")
            if os.path.exists(kt):
                return kt
                
        if os.path.exists(r"C:\Program Files\Java"):
            for root, dirs, files in os.walk(r"C:\Program Files\Java"):
                if "keytool.exe" in files:
                    return os.path.join(root, "keytool.exe")
                    
        return "keytool"

    @staticmethod
    def generate_keystore(output_path, alias, password, key_password, first_last_name, org_unit, org_name, city, state, country_code, validity_years=25):
        """Generates a JKS keystore file using keytool CLI."""
        keytool = SDKUtils.get_keytool_path()
        dname = f"CN={first_last_name}, OU={org_unit}, O={org_name}, L={city}, ST={state}, C={country_code}"
        
        cmd = [
            keytool,
            "-genkeypair",
            "-v",
            "-keystore", output_path,
            "-alias", alias,
            "-keyalg", "RSA",
            "-keysize", "2048",
            "-validity", str(validity_years * 365),
            "-storepass", password,
            "-keypass", key_password or password,
            "-dname", dname,
            "-storetype", "JKS"
        ]
        
        try:
            res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
            return True, res.stdout
        except subprocess.CalledProcessError as e:
            return False, f"Keytool Failed: {e.stderr}"
        except Exception as ex:
            return False, f"Exception: {str(ex)}"
