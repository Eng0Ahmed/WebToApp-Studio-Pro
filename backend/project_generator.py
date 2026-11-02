import os
import shutil
import re
from PIL import Image
from backend.sdk_utils import SDKUtils

class ProjectGenerator:
    """Generates complete runnable Android Gradle project structure based on configuration."""

    ICON_SIZES = {
        "mipmap-mdpi": 48,
        "mipmap-hdpi": 72,
        "mipmap-xhdpi": 96,
        "mipmap-xxhdpi": 144,
        "mipmap-xxxhdpi": 192
    }

    def __init__(self, config, output_dir):
        self.config = config
        self.output_dir = os.path.abspath(output_dir)
        self.app_dir = os.path.join(self.output_dir, "app")
        self.src_main = os.path.join(self.app_dir, "src", "main")
        self.java_dir = os.path.join(self.src_main, "java")
        self.res_dir = os.path.join(self.src_main, "res")
        self.assets_dir = os.path.join(self.src_main, "assets")
        
        # Package directory path
        package_parts = config["package_name"].split(".")
        self.package_java_dir = os.path.join(self.java_dir, *package_parts)

    def generate(self):
        """Generates the full project structure."""
        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir)
            
        os.makedirs(self.package_java_dir, exist_ok=True)
        os.makedirs(self.res_dir, exist_ok=True)
        os.makedirs(self.assets_dir, exist_ok=True)
        
        # 1. Generate Icons & Splash
        self._generate_icons()
        self._copy_splash()
        
        # 2. Process Content (URL vs Local HTML)
        self._process_content()
        
        # 3. Create Gradle Files & local.properties
        self._create_root_build_gradle()
        self._create_settings_gradle()
        self._create_gradle_properties()
        self._create_local_properties()
        self._create_app_build_gradle()
        
        # 4. Create Resources
        self._create_resources()
        
        # 5. Create AndroidManifest
        self._create_manifest()
        
        # 6. Create Java Classes
        self._create_main_activity()
        self._create_application_class()
        
        # 7. Create Gradle Wrapper & copy jar
        self._create_gradle_wrapper()
        
        return self.output_dir

    def _generate_icons(self):
        """Resizes the provided PNG icon into all mipmap densities."""
        icon_path = self.config.get("app_icon_path")
        
        if icon_path and os.path.exists(icon_path):
            try:
                base_img = Image.open(icon_path).convert("RGBA")
            except Exception:
                base_img = self._create_default_icon_img()
        else:
            base_img = self._create_default_icon_img()

        for folder_name, size in self.ICON_SIZES.items():
            folder_path = os.path.join(self.res_dir, folder_name)
            os.makedirs(folder_path, exist_ok=True)
            resized = base_img.resize((size, size), Image.Resampling.LANCZOS)
            resized.save(os.path.join(folder_path, "ic_launcher.png"))
            resized.save(os.path.join(folder_path, "ic_launcher_round.png"))

    def _create_default_icon_img(self):
        """Creates a default 512x512 gradient app icon."""
        img = Image.new("RGBA", (512, 512), (59, 130, 246, 255))
        return img

    def _copy_splash(self):
        """Copies splash image to drawable directory."""
        drawable_dir = os.path.join(self.res_dir, "drawable")
        os.makedirs(drawable_dir, exist_ok=True)
        
        splash_path = self.config.get("splash_image_path")
        if splash_path and os.path.exists(splash_path):
            try:
                img = Image.open(splash_path).convert("RGBA")
                img.save(os.path.join(drawable_dir, "splash_img.png"))
            except Exception:
                self._create_default_splash_img(drawable_dir)
        else:
            self._create_default_splash_img(drawable_dir)

    def _create_default_splash_img(self, drawable_dir):
        img = Image.new("RGBA", (512, 512), (0, 0, 0, 0))
        img.save(os.path.join(drawable_dir, "splash_img.png"))

    def _process_content(self):
        """Copies local HTML files or sets up offline template."""
        template_offline = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "offline.html")
        if os.path.exists(template_offline):
            shutil.copy(template_offline, os.path.join(self.assets_dir, "offline.html"))
            
        if self.config.get("content_type") == "local":
            local_dir = self.config.get("local_html_dir")
            www_dir = os.path.join(self.assets_dir, "www")
            os.makedirs(www_dir, exist_ok=True)
            if local_dir and os.path.exists(local_dir):
                for item in os.listdir(local_dir):
                    s = os.path.join(local_dir, item)
                    d = os.path.join(www_dir, item)
                    if os.path.isdir(s):
                        shutil.copytree(s, d, dirs_exist_ok=True)
                    else:
                        shutil.copy2(s, d)

    def _create_root_build_gradle(self):
        content = """buildscript {
    repositories {
        google()
        mavenCentral()
    }
    dependencies {
        classpath 'com.android.tools.build:gradle:4.1.3'
    }
}

allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

task clean(type: Delete) {
    delete rootProject.buildDir
}
"""
        with open(os.path.join(self.output_dir, "build.gradle"), 'w', encoding='utf-8') as f:
            f.write(content)

    def _create_settings_gradle(self):
        content = f"rootProject.name = \"{self.config['app_title']}\"\ninclude ':app'\n"
        with open(os.path.join(self.output_dir, "settings.gradle"), 'w', encoding='utf-8') as f:
            f.write(content)

    def _create_gradle_properties(self):
        content = """org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
android.useAndroidX=true
android.enableJetifier=true
"""
        with open(os.path.join(self.output_dir, "gradle.properties"), 'w', encoding='utf-8') as f:
            f.write(content)

    def _create_local_properties(self):
        sdk_path = SDKUtils.detect_android_sdk()
        if sdk_path:
            clean_sdk_path = sdk_path.replace("\\", "/")
            content = f"sdk.dir={clean_sdk_path}\n"
            with open(os.path.join(self.output_dir, "local.properties"), 'w', encoding='utf-8') as f:
                f.write(content)

    def _create_app_build_gradle(self):
        pkg = self.config["package_name"]
        vcode = self.config["version_code"]
        vname = self.config["version_name"]
        
        dependencies = [
            "implementation 'androidx.appcompat:appcompat:1.3.1'",
            "implementation 'com.google.android.material:material:1.4.0'",
            "implementation 'androidx.constraintlayout:constraintlayout:2.1.0'",
            "implementation 'androidx.swiperefreshlayout:swiperefreshlayout:1.1.0'"
        ]
        
        if self.config.get("admob_enabled"):
            dependencies.append("implementation 'com.google.android.gms:play-services-ads:20.6.0'")
            
        if self.config.get("onesignal_enabled"):
            dependencies.append("implementation 'com.onesignal:OneSignal:[4.0.0, 4.99.99]'")

        deps_str = "\n    ".join(dependencies)
        
        signing_block = ""
        if self.config.get("keystore_type") == "custom" and self.config.get("keystore_path"):
            ks_path = self.config["keystore_path"].replace("\\", "/")
            signing_block = f"""
    signingConfigs {{
        release {{
            storeFile file('{ks_path}')
            storePassword '{self.config.get("keystore_password")}'
            keyAlias '{self.config.get("key_alias")}'
            keyPassword '{self.config.get("key_password")}'
        }}
    }}"""
            release_signing = "signingConfig signingConfigs.release"
        else:
            release_signing = "signingConfig signingConfigs.debug"

        content = f"""plugins {{
    id 'com.android.application'
}}

android {{
    compileSdkVersion 30
    buildToolsVersion "33.0.1"

    defaultConfig {{
        applicationId "{pkg}"
        minSdkVersion 21
        targetSdkVersion 30
        versionCode {vcode}
        versionName "{vname}"
    }}
    {signing_block}

    buildTypes {{
        release {{
            minifyEnabled false
            proguardFiles getDefaultProguardFile('proguard-android-optimize.txt'), 'proguard-rules.pro'
            {release_signing}
        }}
    }}
    compileOptions {{
        sourceCompatibility JavaVersion.VERSION_1_8
        targetCompatibility JavaVersion.VERSION_1_8
    }}
}}

dependencies {{
    {deps_str}
}}
"""
        with open(os.path.join(self.app_dir, "build.gradle"), 'w', encoding='utf-8') as f:
            f.write(content)

    def _create_resources(self):
        layout_dir = os.path.join(self.res_dir, "layout")
        values_dir = os.path.join(self.res_dir, "values")
        os.makedirs(layout_dir, exist_ok=True)
        os.makedirs(values_dir, exist_ok=True)
        
        splash_bg = self.config.get("splash_bg_color", "#1e293b")
        prog_color = self.config.get("progress_bar_color", "#3b82f6")
        
        colors_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="purple_500">#6200EE</color>
    <color name="purple_700">#3700B3</color>
    <color name="teal_200">#03DAC5</color>
    <color name="teal_700">#018786</color>
    <color name="black">#FF000000</color>
    <color name="white">#FFFFFFFF</color>
    <color name="splash_bg">{splash_bg}</color>
    <color name="progress_bar_color">{prog_color}</color>
</resources>
"""
        with open(os.path.join(values_dir, "colors.xml"), 'w', encoding='utf-8') as f:
            f.write(colors_xml)
            
        strings_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">{self.config['app_title']}</string>
</resources>
"""
        with open(os.path.join(values_dir, "strings.xml"), 'w', encoding='utf-8') as f:
            f.write(strings_xml)
            
        styles_xml = """<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="Theme.WebToApp" parent="Theme.MaterialComponents.DayNight.NoActionBar">
        <item name="colorPrimary">@color/purple_500</item>
        <item name="colorPrimaryVariant">@color/purple_700</item>
        <item name="colorOnPrimary">@color/white</item>
        <item name="android:statusBarColor">@color/splash_bg</item>
    </style>
</resources>
"""
        with open(os.path.join(values_dir, "styles.xml"), 'w', encoding='utf-8') as f:
            f.write(styles_xml)

        layout_xml = """<?xml version="1.0" encoding="utf-8"?>
<RelativeLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:background="@color/splash_bg">

    <RelativeLayout
        android:id="@+id/splash_layout"
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:background="@color/splash_bg"
        android:gravity="center"
        android:elevation="10dp">

        <ImageView
            android:id="@+id/splash_image"
            android:layout_width="160dp"
            android:layout_height="160dp"
            android:layout_centerInParent="true"
            android:src="@drawable/splash_img"
            android:contentDescription="Splash" />

        <ProgressBar
            android:layout_width="wrap_content"
            android:layout_height="wrap_content"
            android:layout_below="@id/splash_image"
            android:layout_centerHorizontal="true"
            android:layout_marginTop="24dp" />
    </RelativeLayout>

    <LinearLayout
        android:layout_width="match_parent"
        android:layout_height="match_parent"
        android:orientation="vertical">

        <ProgressBar
            android:id="@+id/progress_bar"
            style="?android:attr/progressBarStyleHorizontal"
            android:layout_width="match_parent"
            android:layout_height="4dp"
            android:visibility="gone"
            android:indeterminate="true" />

        <androidx.swiperefreshlayout.widget.SwipeRefreshLayout
            android:id="@+id/swipe_refresh"
            android:layout_width="match_parent"
            android:layout_height="0dp"
            android:layout_weight="1">

            <WebView
                android:id="@+id/web_view"
                android:layout_width="match_parent"
                android:layout_height="match_parent" />
        </androidx.swiperefreshlayout.widget.SwipeRefreshLayout>

        <FrameLayout
            android:id="@+id/ad_container"
            android:layout_width="match_parent"
            android:layout_height="wrap_content"
            android:visibility="gone" />
    </LinearLayout>

</RelativeLayout>
"""
        with open(os.path.join(layout_dir, "activity_main.xml"), 'w', encoding='utf-8') as f:
            f.write(layout_xml)

    def _create_manifest(self):
        pkg = self.config["package_name"]
        
        perms = []
        if self.config.get("perm_internet", True):
            perms.append('<uses-permission android:name="android.permission.INTERNET" />')
            perms.append('<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />')
        if self.config.get("perm_camera"):
            perms.append('<uses-permission android:name="android.permission.CAMERA" />')
        if self.config.get("perm_microphone"):
            perms.append('<uses-permission android:name="android.permission.RECORD_AUDIO" />')
        if self.config.get("perm_location"):
            perms.append('<uses-permission android:name="android.permission.ACCESS_FINE_LOCATION" />')
            perms.append('<uses-permission android:name="android.permission.ACCESS_COARSE_LOCATION" />')
        if self.config.get("perm_storage"):
            perms.append('<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />')
            perms.append('<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />')

        perms_str = "\n    ".join(perms)

        orient_map = {
            "portrait": "portrait",
            "landscape": "landscape",
            "auto": "unspecified"
        }
        screen_orientation = orient_map.get(self.config.get("orientation"), "unspecified")

        admob_meta = ""
        if self.config.get("admob_enabled") and self.config.get("admob_app_id"):
            admob_meta = f"""
        <meta-data
            android:name="com.google.android.gms.ads.APPLICATION_ID"
            android:value="{self.config['admob_app_id']}"/>"""

        app_name_class = f".MyApplication" if self.config.get("onesignal_enabled") else "android.app.Application"

        manifest_xml = f"""<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="{pkg}">

    {perms_str}

    <application
        android:name="{app_name_class}"
        android:allowBackup="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="true"
        android:theme="@style/Theme.WebToApp"
        android:usesCleartextTraffic="true">
        {admob_meta}

        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:configChanges="orientation|screenSize|keyboardHidden"
            android:screenOrientation="{screen_orientation}">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>

</manifest>
"""
        with open(os.path.join(self.src_main, "AndroidManifest.xml"), 'w', encoding='utf-8') as f:
            f.write(manifest_xml)

    def _create_application_class(self):
        if not self.config.get("onesignal_enabled"):
            return
            
        pkg = self.config["package_name"]
        onesignal_id = self.config.get("onesignal_app_id", "")

        app_class = f"""package {pkg};

import android.app.Application;
import com.onesignal.OneSignal;

public class MyApplication extends Application {{
    private static final String ONESIGNAL_APP_ID = "{onesignal_id}";

    @Override
    public void onCreate() {{
        super.onCreate();
        
        OneSignal.setLogLevel(OneSignal.LOG_LEVEL.VERBOSE, OneSignal.LOG_LEVEL.NONE);
        OneSignal.initWithContext(this);
        OneSignal.setAppId(ONESIGNAL_APP_ID);
        OneSignal.promptForPushNotifications();
    }}
}}
"""
        with open(os.path.join(self.package_java_dir, "MyApplication.java"), 'w', encoding='utf-8') as f:
            f.write(app_class)

    def _create_main_activity(self):
        pkg = self.config["package_name"]
        content_type = self.config.get("content_type", "url")
        url = self.config.get("web_url", "https://google.com") if content_type == "url" else "file:///android_asset/www/index.html"
        
        pull_to_refresh = "true" if self.config.get("pull_to_refresh") else "false"
        pinch_zoom = "true" if self.config.get("pinch_to_zoom") else "false"
        ext_mode = self.config.get("external_links_mode", "browser")
        splash_dur = self.config.get("splash_duration", 3) * 1000

        java_code = f"""package {pkg};

import android.annotation.SuppressLint;
import android.content.Context;
import android.content.Intent;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.view.View;
import android.webkit.DownloadListener;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.ProgressBar;
import android.widget.RelativeLayout;

import androidx.annotation.Nullable;
import androidx.appcompat.app.AppCompatActivity;
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout;

public class MainActivity extends AppCompatActivity {{

    private static final String INITIAL_URL = "{url}";
    private static final int FILE_CHOOSER_RESULT_CODE = 1001;

    private WebView webView;
    private SwipeRefreshLayout swipeRefresh;
    private ProgressBar progressBar;
    private RelativeLayout splashLayout;
    private ValueCallback<Uri[]> uploadMessage;

    @Override
    @SuppressLint({{"SetJavaScriptEnabled", "RequiresFeature"}})
    protected void onCreate(Bundle savedInstanceState) {{
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        webView = findViewById(R.id.web_view);
        swipeRefresh = findViewById(R.id.swipe_refresh);
        progressBar = findViewById(R.id.progress_bar);
        splashLayout = findViewById(R.id.splash_layout);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(true);
        settings.setAllowContentAccess(true);
        
        try {{
            settings.setAllowFileAccessFromFileURLs(true);
            settings.setAllowUniversalAccessFromFileURLs(true);
        }} catch (Exception ignored) {{}}

        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {{
            settings.setMixedContentMode(WebSettings.MIXED_CONTENT_ALWAYS_ALLOW);
        }}

        boolean enableZoom = {pinch_zoom};
        settings.setBuiltInZoomControls(enableZoom);
        settings.setDisplayZoomControls(false);
        settings.setSupportZoom(enableZoom);

        webView.setDownloadListener(new DownloadListener() {{
            @Override
            public void onDownloadStart(String url, String userAgent, String contentDisposition, String mimetype, long contentLength) {{
                Intent i = new Intent(Intent.ACTION_VIEW);
                i.setData(Uri.parse(url));
                startActivity(i);
            }}
        }});

        swipeRefresh.setEnabled({pull_to_refresh});
        swipeRefresh.setOnRefreshListener(() -> {{
            if (INITIAL_URL.startsWith("file://") || isNetworkAvailable()) {{
                webView.reload();
            }} else {{
                swipeRefresh.setRefreshing(false);
                loadOfflinePage();
            }}
        }});

        webView.setWebChromeClient(new WebChromeClient() {{
            @Override
            public void onProgressChanged(WebView view, int newProgress) {{
                if (newProgress < 100 && {str(self.config.get("show_progress_bar")).lower()}) {{
                    progressBar.setVisibility(View.VISIBLE);
                    progressBar.setProgress(newProgress);
                }} else {{
                    progressBar.setVisibility(View.GONE);
                }}
            }}

            @Override
            public boolean onShowFileChooser(WebView webView, ValueCallback<Uri[]> filePathCallback, FileChooserParams fileChooserParams) {{
                if (uploadMessage != null) {{
                    uploadMessage.onReceiveValue(null);
                    uploadMessage = null;
                }}
                uploadMessage = filePathCallback;
                Intent intent = fileChooserParams.createIntent();
                try {{
                    startActivityForResult(intent, FILE_CHOOSER_RESULT_CODE);
                }} catch (Exception e) {{
                    uploadMessage = null;
                    return false;
                }}
                return true;
            }}
        }});

        webView.setWebViewClient(new WebViewClient() {{
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {{
                String targetUrl = request.getUrl().toString();
                String extMode = "{ext_mode}";

                if (targetUrl.startsWith("http://") || targetUrl.startsWith("https://")) {{
                    if ("browser".equals(extMode) && !targetUrl.contains(getHostDomain(INITIAL_URL))) {{
                        Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(targetUrl));
                        startActivity(intent);
                        return true;
                    }}
                    return false;
                }} else {{
                    try {{
                        Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(targetUrl));
                        startActivity(intent);
                        return true;
                    }} catch (Exception e) {{
                        return true;
                    }}
                }}
            }}

            @Override
            public void onPageFinished(WebView view, String url) {{
                swipeRefresh.setRefreshing(false);
            }}

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {{
                if (request.isForMainFrame() && !INITIAL_URL.startsWith("file://")) {{
                    loadOfflinePage();
                }}
            }}
        }});

        if (INITIAL_URL.startsWith("file://") || isNetworkAvailable()) {{
            webView.loadUrl(INITIAL_URL);
        }} else {{
            loadOfflinePage();
        }}

        new Handler(Looper.getMainLooper()).postDelayed(() -> {{
            if (splashLayout != null) {{
                splashLayout.animate()
                        .alpha(0f)
                        .setDuration(400)
                        .withEndAction(() -> splashLayout.setVisibility(View.GONE));
            }}
        }}, {splash_dur});
    }}

    private boolean isNetworkAvailable() {{
        ConnectivityManager cm = (ConnectivityManager) getSystemService(Context.CONNECTIVITY_SERVICE);
        if (cm != null) {{
            NetworkInfo activeNetwork = cm.getActiveNetworkInfo();
            return activeNetwork != null && activeNetwork.isConnected();
        }}
        return false;
    }}

    private void loadOfflinePage() {{
        webView.loadUrl("file:///android_asset/offline.html");
    }}

    private String getHostDomain(String urlStr) {{
        try {{
            Uri uri = Uri.parse(urlStr);
            return uri.getHost() != null ? uri.getHost() : "";
        }} catch (Exception e) {{
            return "";
        }}
    }}

    @Override
    protected void onActivityResult(int requestCode, int resultCode, @Nullable Intent data) {{
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == FILE_CHOOSER_RESULT_CODE) {{
            if (uploadMessage == null) return;
            uploadMessage.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(resultCode, data));
            uploadMessage = null;
        }}
    }}

    @Override
    public void onBackPressed() {{
        if (webView.canGoBack()) {{
            webView.goBack();
        }} else {{
            super.onBackPressed();
        }}
    }}
}}
"""
        with open(os.path.join(self.package_java_dir, "MainActivity.java"), 'w', encoding='utf-8') as f:
            f.write(java_code)

    def _create_gradle_wrapper(self):
        wrapper_dir = os.path.join(self.output_dir, "gradle", "wrapper")
        os.makedirs(wrapper_dir, exist_ok=True)

        src_jar = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "gradle-wrapper.jar")
        if os.path.exists(src_jar):
            shutil.copy2(src_jar, os.path.join(wrapper_dir, "gradle-wrapper.jar"))

        gradlew_bat = r"""@rem
@if "%DEBUG%" == "" @echo off
@if "%OS%"=="Windows_NT" setlocal

set DIRNAME=%~dp0
if "%DIRNAME%" == "" set DIRNAME=.
set APP_BASE_NAME=%~n0
set APP_HOME=%DIRNAME%

set DEFAULT_JVM_OPTS="-Xmx1024m"

if defined JAVA_HOME goto findJavaFromJavaHome
set JAVA_EXE=java.exe
goto execute

:findJavaFromJavaHome
set JAVA_HOME=%JAVA_HOME:"=%
set JAVA_EXE="%JAVA_HOME%\bin\java.exe"

:execute
set CLASSPATH="%APP_HOME%gradle\wrapper\gradle-wrapper.jar"

%JAVA_EXE% %DEFAULT_JVM_OPTS% %JAVA_OPTS% %GRADLE_OPTS% "-Dorg.gradle.appname=%APP_BASE_NAME%" -classpath %CLASSPATH% org.gradle.wrapper.GradleWrapperMain %*

if "%OS%"=="Windows_NT" endlocal
"""
        with open(os.path.join(self.output_dir, "gradlew.bat"), 'w', encoding='utf-8') as f:
            f.write(gradlew_bat)

        props = """distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\\://services.gradle.org/distributions/gradle-6.8.3-bin.zip
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
"""
        with open(os.path.join(wrapper_dir, "gradle-wrapper.properties"), 'w', encoding='utf-8') as f:
            f.write(props)
