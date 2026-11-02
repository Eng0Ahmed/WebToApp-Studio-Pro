import json
import os

class ProjectConfig:
    """Manages WebToApp Studio Pro project settings, saving and loading configuration JSON files."""
    
    DEFAULT_CONFIG = {
        # App Settings
        "app_title": "تطبيقي المميز",
        "package_name": "com.example.webapp",
        "version_name": "1.0.0",
        "version_code": 1,
        "content_type": "url",  # "url" or "local"
        "web_url": "https://google.com",
        "local_html_dir": "",
        "orientation": "auto",  # "portrait", "landscape", "auto"
        
        # Branding & Graphics
        "app_icon_path": "",
        "splash_image_path": "",
        "splash_bg_color": "#1e293b",
        "splash_duration": 3,  # seconds
        "pull_to_refresh": True,
        "show_progress_bar": True,
        "progress_bar_color": "#3b82f6",
        "pinch_to_zoom": True,
        
        # Permissions & Features
        "perm_internet": True,
        "perm_camera": False,
        "perm_microphone": False,
        "perm_location": False,
        "perm_storage": True,
        "enable_file_upload": True,
        "enable_file_download": True,
        "enable_media_playback": True,
        "custom_offline_page": True,
        "external_links_mode": "browser",  # "webview" or "browser"
        
        # Monetization & Notifications
        "admob_enabled": False,
        "admob_app_id": "ca-app-pub-3940256099942544~3347511713",
        "admob_banner_id": "ca-app-pub-3940256099942544/6300978111",
        "admob_interstitial_id": "ca-app-pub-3940256099942544/1033173712",
        "onesignal_enabled": False,
        "onesignal_app_id": "",
        
        # Keystore & Signing
        "keystore_type": "debug",  # "debug" or "custom"
        "keystore_path": "",
        "keystore_password": "",
        "key_alias": "",
        "key_password": ""
    }

    @staticmethod
    def get_default():
        return ProjectConfig.DEFAULT_CONFIG.copy()

    @staticmethod
    def save_to_file(config_data, filepath):
        """Saves configuration dict to a JSON file."""
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=4)
        return True

    @staticmethod
    def load_from_file(filepath):
        """Loads configuration dict from a JSON file, merging defaults for any missing keys."""
        if not os.path.exists(filepath):
            return ProjectConfig.get_default()
            
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        config = ProjectConfig.get_default()
        config.update(data)
        return config
