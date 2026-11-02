import os
import customtkinter as ctk
from tkinter import filedialog, messagebox
from gui.theme import Theme
from backend.sdk_utils import SDKUtils

class KeystoreDialog(ctk.CTkToplevel):
    """Popup dialog for generating custom Android JKS Keystores using keytool CLI."""

    def __init__(self, parent, completion_callback=None):
        super().__init__(parent)

        self.title("🔑 مولّد مفاتيح التوقيع (Keystore Generator)")
        self.geometry("540 x 680")
        self.resizable(False, False)
        self.configure(fg_color=Theme.BG_DARK)

        self.completion_callback = completion_callback

        # Make modal window
        self.transient(parent)
        self.grab_set()

        self._build_ui()

    def _build_ui(self):
        header = ctk.CTkFrame(self, fg_color=Theme.SURFACE_CARD, corner_radius=0, height=60)
        header.pack(fill="x")

        ctk.CTkLabel(
            header,
            text="🔐 إنشاء مفتاح توقيع جديد (Generate Keystore)",
            font=Theme.FONT_HEADER,
            text_color=Theme.TEXT_PRIMARY
        ).pack(side="left", padx=20, pady=12)

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=20, pady=12)

        form = scroll

        # 1. Output Path
        ctk.CTkLabel(form, text="مسار حفظ ملف Keystore:", font=Theme.FONT_TITLE, text_color=Theme.TEXT_PRIMARY).pack(anchor="w", pady=(8, 4))
        path_frame = ctk.CTkFrame(form, fg_color="transparent")
        path_frame.pack(fill="x", pady=4)
        
        self.entry_path = ctk.CTkEntry(path_frame, placeholder_text="اختر مسار حفظ الملف...", font=Theme.FONT_BODY, height=38)
        self.entry_path.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        btn_browse = ctk.CTkButton(path_frame, text="استعراض...", width=100, height=38, command=self._browse_save_path, fg_color=Theme.PRIMARY, font=Theme.FONT_TITLE)
        btn_browse.pack(side="right")

        # 2. Key Alias & Password
        ctk.CTkLabel(form, text="الاسم المستعار (Key Alias):", font=Theme.FONT_TITLE, text_color=Theme.TEXT_PRIMARY).pack(anchor="w", pady=(14, 4))
        self.entry_alias = ctk.CTkEntry(form, font=Theme.FONT_BODY, height=38)
        self.entry_alias.insert(0, "key0")
        self.entry_alias.pack(fill="x", pady=2)

        ctk.CTkLabel(form, text="كلمة مرور Keystore (Keystore Password):", font=Theme.FONT_TITLE, text_color=Theme.TEXT_PRIMARY).pack(anchor="w", pady=(14, 4))
        self.entry_storepass = ctk.CTkEntry(form, show="*", font=Theme.FONT_BODY, height=38)
        self.entry_storepass.pack(fill="x", pady=2)

        ctk.CTkLabel(form, text="كلمة مرور المفتاح (Key Password):", font=Theme.FONT_TITLE, text_color=Theme.TEXT_PRIMARY).pack(anchor="w", pady=(14, 4))
        self.entry_keypass = ctk.CTkEntry(form, show="*", placeholder_text="اتركه فارغاً لاستخدام نفس كلمة مرور Keystore", font=Theme.FONT_BODY, height=38)
        self.entry_keypass.pack(fill="x", pady=2)

        # 3. Certificate Details (Pre-filled with Developer Info)
        ctk.CTkLabel(form, text="بيانات المطور والشهادة (Certificate Details):", font=Theme.FONT_SUBHEADER, text_color=Theme.PRIMARY).pack(anchor="w", pady=(20, 8))

        grid = ctk.CTkFrame(form, fg_color=Theme.SURFACE_CARD, corner_radius=12)
        grid.pack(fill="x", pady=4, ipadx=10, ipady=10)

        # Name
        ctk.CTkLabel(grid, text="الاسم الكامل (First & Last Name):", font=Theme.FONT_BODY).grid(row=0, column=0, sticky="w", padx=10, pady=6)
        self.entry_cn = ctk.CTkEntry(grid, width=260, font=Theme.FONT_BODY, height=36)
        self.entry_cn.insert(0, "Eng_Ahmed Abdelaziz Mohamed")
        self.entry_cn.grid(row=0, column=1, padx=10, pady=6)

        # Organizational Unit
        ctk.CTkLabel(grid, text="القسم (Org Unit):", font=Theme.FONT_BODY).grid(row=1, column=0, sticky="w", padx=10, pady=6)
        self.entry_ou = ctk.CTkEntry(grid, width=260, font=Theme.FONT_BODY, height=36)
        self.entry_ou.insert(0, "Software Engineering")
        self.entry_ou.grid(row=1, column=1, padx=10, pady=6)

        # Organization Name
        ctk.CTkLabel(grid, text="اسم الشركة (Org Name):", font=Theme.FONT_BODY).grid(row=2, column=0, sticky="w", padx=10, pady=6)
        self.entry_o = ctk.CTkEntry(grid, width=260, font=Theme.FONT_BODY, height=36)
        self.entry_o.insert(0, "Eng. Ahmed Abdelaziz")
        self.entry_o.grid(row=2, column=1, padx=10, pady=6)

        # City / Locality
        ctk.CTkLabel(grid, text="المدينة (City/Locality):", font=Theme.FONT_BODY).grid(row=3, column=0, sticky="w", padx=10, pady=6)
        self.entry_l = ctk.CTkEntry(grid, width=260, font=Theme.FONT_BODY, height=36)
        self.entry_l.insert(0, "Cairo")
        self.entry_l.grid(row=3, column=1, padx=10, pady=6)

        # Country Code
        ctk.CTkLabel(grid, text="رمز الدولة (Country Code 2 Letters):", font=Theme.FONT_BODY).grid(row=4, column=0, sticky="w", padx=10, pady=6)
        self.entry_c = ctk.CTkEntry(grid, width=260, font=Theme.FONT_BODY, height=36)
        self.entry_c.insert(0, "EG")
        self.entry_c.grid(row=4, column=1, padx=10, pady=6)

        # Validity
        ctk.CTkLabel(grid, text="مدة الصلاحية بالسنوات (Years):", font=Theme.FONT_BODY).grid(row=5, column=0, sticky="w", padx=10, pady=6)
        self.entry_validity = ctk.CTkEntry(grid, width=260, font=Theme.FONT_BODY, height=36)
        self.entry_validity.insert(0, "25")
        self.entry_validity.grid(row=5, column=1, padx=10, pady=6)

        # Generate Button
        btn_generate = ctk.CTkButton(
            form, text="⚡ إنشاء ملف المفتاح الآن",
            font=Theme.FONT_HEADER,
            fg_color=Theme.SUCCESS,
            hover_color=Theme.SUCCESS_HOVER,
            height=46,
            command=self._generate_keystore
        )
        btn_generate.pack(fill="x", pady=20)

    def _browse_save_path(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".jks",
            filetypes=[("Java KeyStore File", "*.jks"), ("KeyStore File", "*.keystore"), ("All Files", "*.*")]
        )
        if path:
            self.entry_path.delete(0, "end")
            self.entry_path.insert(0, path)

    def _generate_keystore(self):
        output_path = self.entry_path.get().strip()
        alias = self.entry_alias.get().strip()
        storepass = self.entry_storepass.get().strip()
        keypass = self.entry_keypass.get().strip() or storepass
        
        cn = self.entry_cn.get().strip() or "Eng_Ahmed Abdelaziz Mohamed"
        ou = self.entry_ou.get().strip() or "Development"
        o = self.entry_o.get().strip() or "Eng. Ahmed Abdelaziz"
        l = self.entry_l.get().strip() or "Cairo"
        c = self.entry_c.get().strip() or "EG"
        
        try:
            validity = int(self.entry_validity.get().strip() or 25)
        except ValueError:
            validity = 25

        if not output_path:
            messagebox.showerror("خطأ", "يرجى تحديد مسار حفظ ملف Keystore.")
            return

        if not alias:
            messagebox.showerror("خطأ", "يرجى كتابة الاسم المستعار (Key Alias).")
            return

        if len(storepass) < 6:
            messagebox.showerror("خطأ", "كلمة المرور يجب أن لا تقل عن 6 أحرف.")
            return

        success, output = SDKUtils.generate_keystore(
            output_path, alias, storepass, keypass,
            first_last_name=cn, org_unit=ou, org_name=o,
            city=l, state=l, country_code=c, validity_years=validity
        )

        if success:
            messagebox.showinfo("تم بنجاح! 🎉", f"تم إنشاء ملف Keystore بنجاح في المسار:\n{output_path}")
            if self.completion_callback:
                self.completion_callback(output_path, storepass, alias, keypass)
            self.destroy()
        else:
            messagebox.showerror("فشل الإنشاء ❌", f"لم نتمكن من إنشاء ملف المفتاح:\n\n{output}")
