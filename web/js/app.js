/**
 * WebToApp Studio Pro - Application Controller
 * Handles UI interactions, live preview synchronization, i18n, themes, and Python bridge.
 */

class WebToApp {
  constructor() {
    this.currentLang = 'ar';
    this.currentTheme = 'dark';
    this.currentTab = 0;
    this.isBuilding = false;
    this.config = {};

    this.initClock();
    this.initDragAndDrop();
    this.initEventListeners();
  }

  initClock() {
    setInterval(() => {
      const now = new Date();
      const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false });
      const clockEl = document.getElementById('phoneClock');
      if (clockEl) clockEl.textContent = timeStr;
    }, 1000);
  }

  initEventListeners() {
    window.addEventListener('DOMContentLoaded', () => {
      this.applyTranslations();
      this.updatePreview();
      
      // Wait for pywebview bridge
      window.addEventListener('pywebviewready', () => {
        this.fetchInitialData();
      });

      // Also try direct fetch in case pywebview is already ready
      setTimeout(() => {
        this.fetchInitialData();
      }, 300);
    });
  }

  initDragAndDrop() {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      document.body.addEventListener(eventName, (e) => {
        e.preventDefault();
        e.stopPropagation();
      }, false);
    });

    document.body.addEventListener('drop', (e) => {
      const dt = e.dataTransfer;
      const files = dt.files;
      if (files && files.length > 0) {
        const file = files[0];
        const path = file.path || file.name;
        const ext = path.split('.').pop().toLowerCase();

        if (['png', 'jpg', 'jpeg', 'webp'].includes(ext)) {
          // If on tab 2 or icon is empty, set as icon
          const iconInput = document.getElementById('cfg_app_icon_path');
          iconInput.value = path;
          this.previewIcon(path);
          this.appendLog(`[إفلات ملف] تم تعيين الأيقونة: ${path}\n`, 'log-info');
        } else if (file.type === '' || !ext || ext === 'html' || ext === 'htm') {
          // Likely a directory or html file
          const dirInput = document.getElementById('cfg_local_html_dir');
          dirInput.value = path;
          this.switchContentType('local');
          this.appendLog(`[إفلات مجلد] تم تعيين مسار المحتوى المحلي: ${path}\n`, 'log-info');
        }
      }
    });
  }

  // ==========================================
  // PYTHON BRIDGE & DATA
  // ==========================================
  async fetchInitialData() {
    if (window.pywebview && window.pywebview.api) {
      try {
        const data = await window.pywebview.api.get_initial_data();
        if (data) {
          this.populateData(data);
        }
      } catch (err) {
        console.warn("Bridge fetch error:", err);
      }
    }
  }

  populateData(data) {
    if (data.android_sdk) {
      const pill = document.getElementById('sdkPill');
      pill.className = 'status-pill ready';
      document.getElementById('sdkPillText').textContent = translations[this.currentLang].sdkReady;
    } else {
      const pill = document.getElementById('sdkPill');
      pill.className = 'status-pill missing';
      document.getElementById('sdkPillText').textContent = translations[this.currentLang].sdkMissing;
    }

    if (data.java_home) {
      const pill = document.getElementById('jdkPill');
      pill.className = 'status-pill ready';
      document.getElementById('jdkPillText').textContent = translations[this.currentLang].jdkReady;
    } else {
      const pill = document.getElementById('jdkPill');
      pill.className = 'status-pill missing';
      document.getElementById('jdkPillText').textContent = translations[this.currentLang].jdkMissing;
    }

    if (data.config) {
      this.loadConfigIntoUI(data.config);
    }
  }

  loadConfigIntoUI(cfg) {
    this.config = cfg;
    
    // Tab 1
    this.setVal('cfg_app_title', cfg.app_title || '');
    this.setVal('cfg_package_name', cfg.package_name || '');
    this.setVal('cfg_version_name', cfg.version_name || '1.0.0');
    this.setVal('cfg_version_code', cfg.version_code || 1);
    this.setVal('cfg_web_url', cfg.web_url || 'https://google.com');
    this.setVal('cfg_local_html_dir', cfg.local_html_dir || '');
    this.setVal('cfg_orientation', cfg.orientation || 'auto');
    this.switchContentType(cfg.content_type || 'url');

    // Tab 2
    this.setVal('cfg_app_icon_path', cfg.app_icon_path || '');
    this.setVal('cfg_splash_image_path', cfg.splash_image_path || '');
    this.setVal('cfg_splash_bg_color', cfg.splash_bg_color || '#1e293b');
    this.setVal('cfg_splash_bg_color_hex', cfg.splash_bg_color || '#1e293b');
    this.setVal('cfg_splash_duration', cfg.splash_duration !== undefined ? cfg.splash_duration : 3);
    this.setChecked('cfg_pull_to_refresh', cfg.pull_to_refresh !== false);
    this.setChecked('cfg_show_progress_bar', cfg.show_progress_bar !== false);
    this.setVal('cfg_progress_bar_color', cfg.progress_bar_color || '#3b82f6');
    this.setVal('cfg_progress_bar_color_hex', cfg.progress_bar_color || '#3b82f6');
    this.setChecked('cfg_pinch_to_zoom', cfg.pinch_to_zoom !== false);

    // Tab 3
    this.setChecked('cfg_perm_internet', cfg.perm_internet !== false);
    this.setChecked('cfg_perm_camera', !!cfg.perm_camera);
    this.setChecked('cfg_perm_microphone', !!cfg.perm_microphone);
    this.setChecked('cfg_perm_location', !!cfg.perm_location);
    this.setChecked('cfg_perm_storage', cfg.perm_storage !== false);
    this.setChecked('cfg_enable_file_upload', cfg.enable_file_upload !== false);
    this.setChecked('cfg_enable_file_download', cfg.enable_file_download !== false);
    this.setChecked('cfg_enable_media_playback', cfg.enable_media_playback !== false);
    this.setChecked('cfg_custom_offline_page', cfg.custom_offline_page !== false);
    this.setVal('cfg_external_links_mode', cfg.external_links_mode || 'browser');

    // Tab 4
    this.setChecked('cfg_admob_enabled', !!cfg.admob_enabled);
    this.toggleAdMobFields(!!cfg.admob_enabled);
    this.setVal('cfg_admob_app_id', cfg.admob_app_id || '');
    this.setVal('cfg_admob_banner_id', cfg.admob_banner_id || '');
    this.setVal('cfg_admob_interstitial_id', cfg.admob_interstitial_id || '');

    this.setChecked('cfg_onesignal_enabled', !!cfg.onesignal_enabled);
    this.toggleOneSignalFields(!!cfg.onesignal_enabled);
    this.setVal('cfg_onesignal_app_id', cfg.onesignal_app_id || '');

    // Tab 5
    this.switchKeyType(cfg.keystore_type || 'debug');
    this.setVal('cfg_keystore_path', cfg.keystore_path || '');
    this.setVal('cfg_keystore_password', cfg.keystore_password || '');
    this.setVal('cfg_key_alias', cfg.key_alias || '');
    this.setVal('cfg_key_password', cfg.key_password || '');

    this.updatePreview();
  }

  collectConfigFromUI() {
    return {
      app_title: this.getVal('cfg_app_title') || 'تطبيقي المميز',
      package_name: this.getVal('cfg_package_name') || 'com.example.webapp',
      version_name: this.getVal('cfg_version_name') || '1.0.0',
      version_code: parseInt(this.getVal('cfg_version_code')) || 1,
      content_type: document.querySelector('input[name="content_type"]:checked').value,
      web_url: this.getVal('cfg_web_url') || 'https://google.com',
      local_html_dir: this.getVal('cfg_local_html_dir') || '',
      orientation: this.getVal('cfg_orientation') || 'auto',

      app_icon_path: this.getVal('cfg_app_icon_path') || '',
      splash_image_path: this.getVal('cfg_splash_image_path') || '',
      splash_bg_color: this.getVal('cfg_splash_bg_color') || '#1e293b',
      splash_duration: parseInt(this.getVal('cfg_splash_duration')) || 3,
      pull_to_refresh: this.isChecked('cfg_pull_to_refresh'),
      show_progress_bar: this.isChecked('cfg_show_progress_bar'),
      progress_bar_color: this.getVal('cfg_progress_bar_color') || '#3b82f6',
      pinch_to_zoom: this.isChecked('cfg_pinch_to_zoom'),

      perm_internet: this.isChecked('cfg_perm_internet'),
      perm_camera: this.isChecked('cfg_perm_camera'),
      perm_microphone: this.isChecked('cfg_perm_microphone'),
      perm_location: this.isChecked('cfg_perm_location'),
      perm_storage: this.isChecked('cfg_perm_storage'),
      enable_file_upload: this.isChecked('cfg_enable_file_upload'),
      enable_file_download: this.isChecked('cfg_enable_file_download'),
      enable_media_playback: this.isChecked('cfg_enable_media_playback'),
      custom_offline_page: this.isChecked('cfg_custom_offline_page'),
      external_links_mode: this.getVal('cfg_external_links_mode') || 'browser',

      admob_enabled: this.isChecked('cfg_admob_enabled'),
      admob_app_id: this.getVal('cfg_admob_app_id'),
      admob_banner_id: this.getVal('cfg_admob_banner_id'),
      admob_interstitial_id: this.getVal('cfg_admob_interstitial_id'),
      onesignal_enabled: this.isChecked('cfg_onesignal_enabled'),
      onesignal_app_id: this.getVal('cfg_onesignal_app_id'),

      keystore_type: document.querySelector('input[name="keystore_type"]:checked').value,
      keystore_path: this.getVal('cfg_keystore_path'),
      keystore_password: this.getVal('cfg_keystore_password'),
      key_alias: this.getVal('cfg_key_alias'),
      key_password: this.getVal('cfg_key_password')
    };
  }

  // ==========================================
  // TAB NAVIGATION
  // ==========================================
  switchTab(index) {
    this.currentTab = index;
    const buttons = document.querySelectorAll('.tab-btn');
    const panels = document.querySelectorAll('.tab-content-panel');

    buttons.forEach((btn, i) => {
      btn.classList.toggle('active', i === index);
    });

    panels.forEach((pnl, i) => {
      pnl.classList.toggle('active', i === index);
    });
  }

  switchContentType(type) {
    const radioUrl = document.getElementById('radioCardUrl');
    const radioLocal = document.getElementById('radioCardLocal');
    const secUrl = document.getElementById('sectionWebUrl');
    const secLocal = document.getElementById('sectionLocalDir');

    if (type === 'url') {
      radioUrl.classList.add('active');
      radioLocal.classList.remove('active');
      secUrl.style.display = 'block';
      secLocal.style.display = 'none';
      document.querySelector('input[name="content_type"][value="url"]').checked = true;
    } else {
      radioUrl.classList.remove('active');
      radioLocal.classList.add('active');
      secUrl.style.display = 'none';
      secLocal.style.display = 'block';
      document.querySelector('input[name="content_type"][value="local"]').checked = true;
    }
  }

  switchKeyType(type) {
    const rDebug = document.getElementById('radioKeyDebug');
    const rCustom = document.getElementById('radioKeyCustom');
    const customFields = document.getElementById('customKeystoreFields');

    if (type === 'debug') {
      rDebug.classList.add('active');
      rCustom.classList.remove('active');
      customFields.style.display = 'none';
      document.querySelector('input[name="keystore_type"][value="debug"]').checked = true;
    } else {
      rDebug.classList.remove('active');
      rCustom.classList.add('active');
      customFields.style.display = 'block';
      document.querySelector('input[name="keystore_type"][value="custom"]').checked = true;
    }
  }

  toggleAdMobFields(checked) {
    document.getElementById('admobFieldsGroup').style.display = checked ? 'block' : 'none';
  }

  toggleOneSignalFields(checked) {
    document.getElementById('onesignalFieldsGroup').style.display = checked ? 'block' : 'none';
  }

  syncColor(hexVal, targetId) {
    if (/^#[0-9A-F]{6}$/i.test(hexVal)) {
      document.getElementById(targetId).value = hexVal;
      this.updatePreview();
    }
  }

  // ==========================================
  // LIVE PREVIEW UPDATE
  // ==========================================
  updatePreview() {
    const title = this.getVal('cfg_app_title') || 'تطبيقي المميز';
    const pkg = this.getVal('cfg_package_name') || 'com.example.webapp';
    const splashBg = this.getVal('cfg_splash_bg_color') || '#1e293b';

    document.getElementById('previewAppTitle').textContent = title;
    document.getElementById('previewAppTitleSub').textContent = title;
    document.getElementById('previewAppPkg').textContent = pkg;

    const splashOverlay = document.getElementById('phoneSplashOverlay');
    if (splashOverlay) splashOverlay.style.backgroundColor = splashBg;
  }

  previewIcon(path) {
    const iconImg = document.getElementById('previewAppIcon');
    if (path) {
      iconImg.src = path;
    }
  }

  triggerSplashTest() {
    const overlay = document.getElementById('phoneSplashOverlay');
    const duration = parseInt(this.getVal('cfg_splash_duration')) || 3;
    const splashLogoPath = this.getVal('cfg_splash_image_path');
    const logoEl = document.getElementById('previewSplashLogo');

    if (splashLogoPath) {
      logoEl.src = splashLogoPath;
      logoEl.style.display = 'block';
    } else {
      logoEl.style.display = 'none';
    }

    overlay.style.display = 'flex';
    setTimeout(() => {
      overlay.style.display = 'none';
    }, duration * 1000);
  }

  // ==========================================
  // FILE DIALOGS VIA PYTHON
  // ==========================================
  async browseIcon() {
    if (window.pywebview && window.pywebview.api) {
      const path = await window.pywebview.api.select_file("Image Files (*.png;*.jpg;*.jpeg)|*.png;*.jpg;*.jpeg");
      if (path) {
        document.getElementById('cfg_app_icon_path').value = path;
        this.previewIcon(path);
      }
    }
  }

  async browseSplash() {
    if (window.pywebview && window.pywebview.api) {
      const path = await window.pywebview.api.select_file("Image Files (*.png;*.jpg;*.jpeg)|*.png;*.jpg;*.jpeg");
      if (path) {
        document.getElementById('cfg_splash_image_path').value = path;
      }
    }
  }

  async browseLocalDir() {
    if (window.pywebview && window.pywebview.api) {
      const path = await window.pywebview.api.select_directory();
      if (path) {
        document.getElementById('cfg_local_html_dir').value = path;
      }
    }
  }

  async browseKeystore() {
    if (window.pywebview && window.pywebview.api) {
      const path = await window.pywebview.api.select_file("Keystore Files (*.jks;*.keystore)|*.jks;*.keystore");
      if (path) {
        document.getElementById('cfg_keystore_path').value = path;
      }
    }
  }

  async saveProject() {
    if (window.pywebview && window.pywebview.api) {
      const cfg = this.collectConfigFromUI();
      const res = await window.pywebview.api.save_project_file(cfg);
      if (res && res.success) {
        this.appendLog(`[مشروع] تم حفظ المشروع بنجاح: ${res.path}\n`, 'log-success');
      }
    }
  }

  async loadProject() {
    if (window.pywebview && window.pywebview.api) {
      const data = await window.pywebview.api.load_project_file();
      if (data && data.config) {
        this.loadConfigIntoUI(data.config);
        this.appendLog(`[مشروع] تم تحميل المشروع بنجاح: ${data.path}\n`, 'log-success');
      }
    }
  }

  // ==========================================
  // KEYSTORE GENERATOR
  // ==========================================
  async chooseKeystoreSavePath() {
    if (window.pywebview && window.pywebview.api) {
      const path = await window.pywebview.api.select_save_file("Java Keystore (*.jks)|*.jks", "release_key.jks");
      if (path) {
        document.getElementById('gen_output_path').value = path;
      }
    }
  }

  async confirmGenerateKeystore() {
    const outPath = document.getElementById('gen_output_path').value;
    const alias = document.getElementById('gen_alias').value;
    const pass = document.getElementById('gen_password').value;

    if (!outPath || !alias || !pass) {
      alert(this.currentLang === 'ar' ? 'يرجى ملء مكان الحفظ والاسم المستعار وكلمة المرور!' : 'Please fill output path, alias, and password!');
      return;
    }

    if (pass.length < 6) {
      alert(this.currentLang === 'ar' ? 'كلمة المرور يجب أن تكون 6 أحرف على الأقل!' : 'Password must be at least 6 characters!');
      return;
    }

    const params = {
      output_path: outPath,
      alias: alias,
      password: pass,
      key_password: pass,
      first_last_name: document.getElementById('gen_name').value || 'Developer',
      org_unit: document.getElementById('gen_org_unit').value || 'Dev',
      org_name: document.getElementById('gen_org_name').value || 'Studio',
      city: document.getElementById('gen_city').value || 'City',
      state: document.getElementById('gen_state').value || 'State',
      country_code: document.getElementById('gen_country').value || 'EG',
      validity_years: parseInt(document.getElementById('gen_validity').value) || 25
    };

    if (window.pywebview && window.pywebview.api) {
      const res = await window.pywebview.api.generate_keystore(params);
      if (res && res.success) {
        // Auto-fill into Tab 5 fields
        document.getElementById('cfg_keystore_path').value = outPath;
        document.getElementById('cfg_keystore_password').value = pass;
        document.getElementById('cfg_key_alias').value = alias;
        document.getElementById('cfg_key_password').value = pass;
        this.switchKeyType('custom');
        this.closeModal('modalKey');
        this.appendLog(`[Keystore] تم إنشاء شهادة التوقيع الرقمي بنجاح: ${outPath}\n`, 'log-success');
      } else {
        alert("خطأ: " + (res.error || 'Failed to generate keystore'));
      }
    }
  }

  // ==========================================
  // BUILD & COMPILE TRIGGER
  // ==========================================
  async startBuild(isAab) {
    if (this.isBuilding) return;

    const cfg = this.collectConfigFromUI();

    // Basic Validation
    if (!cfg.app_title.trim()) {
      alert(this.currentLang === 'ar' ? 'يرجى إدخال اسم التطبيق!' : 'Please enter application title!');
      this.switchTab(0);
      return;
    }

    if (!cfg.package_name.trim() || !cfg.package_name.includes('.')) {
      alert(this.currentLang === 'ar' ? 'يرجى إدخال اسم حزمة صالح (مثل com.example.app)!' : 'Please enter a valid package name (e.g. com.example.app)!');
      this.switchTab(0);
      return;
    }

    if (cfg.content_type === 'url' && !cfg.web_url.startsWith('http')) {
      alert(this.currentLang === 'ar' ? 'يرجى إدخال رابط موقع صالح يبدأ بـ http أو https!' : 'Please enter a valid URL starting with http or https!');
      this.switchTab(0);
      return;
    }

    if (cfg.content_type === 'local' && !cfg.local_html_dir) {
      alert(this.currentLang === 'ar' ? 'يرجى تحديد مسار مجلد الـ HTML المحلي!' : 'Please select local HTML directory path!');
      this.switchTab(0);
      return;
    }

    this.isBuilding = true;
    this.updateBuildButtons(true);
    this.setStep(1);
    this.clearLog();

    if (window.pywebview && window.pywebview.api) {
      await window.pywebview.api.start_build(cfg, isAab);
    }
  }

  updateBuildButtons(building) {
    document.getElementById('btnFastApk').disabled = building;
    document.getElementById('btnFastAab').disabled = building;
  }

  setStep(stepIndex) {
    for (let i = 1; i <= 5; i++) {
      const el = document.getElementById(`step${i}`);
      if (i < stepIndex) {
        el.className = 'step-item done';
      } else if (i === stepIndex) {
        el.className = 'step-item active';
      } else {
        el.className = 'step-item';
      }
    }
  }

  appendLog(text, className = '') {
    const consoleBox = document.getElementById('terminalConsole');
    if (!consoleBox) return;

    const span = document.createElement('span');
    span.textContent = text;
    if (className) span.className = className;

    // Auto coloring for common keywords
    if (!className) {
      if (text.includes('BUILD SUCCESSFUL') || text.includes('تم التجميع بنجاح')) {
        span.className = 'log-success';
        this.setStep(5);
      } else if (text.includes('BUILD FAILED') || text.includes('خطأ') || text.includes('ERROR:')) {
        span.className = 'log-error';
      } else if (text.includes('WARNING:')) {
        span.className = 'log-warning';
      } else if (text.includes('Task :') || text.includes('بدء عملية')) {
        span.className = 'log-info';
      }
    }

    consoleBox.appendChild(span);
    consoleBox.scrollTop = consoleBox.scrollHeight;
  }

  clearLog() {
    const consoleBox = document.getElementById('terminalConsole');
    if (consoleBox) consoleBox.innerHTML = '';
  }

  copyLog() {
    const consoleBox = document.getElementById('terminalConsole');
    if (consoleBox) {
      navigator.clipboard.writeText(consoleBox.textContent);
      this.appendLog(`\n[${translations[this.currentLang].copied}]\n`, 'log-success');
    }
  }

  async openOutputFolder() {
    if (window.pywebview && window.pywebview.api) {
      await window.pywebview.api.open_output_dir();
    }
  }

  // ==========================================
  // I18N & THEMES
  // ==========================================
  toggleLanguage() {
    this.currentLang = this.currentLang === 'ar' ? 'en' : 'ar';
    document.documentElement.lang = this.currentLang;
    document.documentElement.dir = this.currentLang === 'ar' ? 'rtl' : 'ltr';
    document.getElementById('langText').textContent = translations[this.currentLang].langToggle;
    this.applyTranslations();
  }

  applyTranslations() {
    const dict = translations[this.currentLang];
    document.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      if (dict[key]) {
        el.textContent = dict[key];
      }
    });
  }

  toggleTheme() {
    this.currentTheme = this.currentTheme === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', this.currentTheme);
    document.getElementById('themeIcon').textContent = this.currentTheme === 'dark' ? '☀️' : '🌙';
  }

  // Modals
  openModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.add('active');
  }

  closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) modal.classList.remove('active');
  }

  // Helpers
  getVal(id) {
    const el = document.getElementById(id);
    return el ? el.value : '';
  }

  setVal(id, val) {
    const el = document.getElementById(id);
    if (el) el.value = val;
  }

  isChecked(id) {
    const el = document.getElementById(id);
    return el ? el.checked : false;
  }

  setChecked(id, val) {
    const el = document.getElementById(id);
    if (el) el.checked = !!val;
  }
}

// Global Instance
const app = new WebToApp();

// Bridge Callbacks from Python
window.onBuildLog = function(line) {
  app.appendLog(line);
};

window.onBuildProgress = function(stepIndex) {
  app.setStep(stepIndex);
};

window.onBuildComplete = function(success, message, artifactPath) {
  app.isBuilding = false;
  app.updateBuildButtons(false);
  if (success) {
    app.setStep(5);
    app.appendLog(`\n🎉 ${message}\n📁 ${artifactPath}\n`, 'log-success');
  } else {
    app.appendLog(`\n❌ ${message}\n`, 'log-error');
  }
};
