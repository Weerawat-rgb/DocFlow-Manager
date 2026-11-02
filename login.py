import tkinter as tk
from tkinter import messagebox, ttk
import json
import pyodbc
from Crypto.Cipher import DES
import base64
from PIL import Image, ImageTk
import io
import sys
import os
from database_manager import DatabaseManager 
from utils import set_window_icon



class CryptoHelper:
    """Class สำหรับจัดการการเข้ารหัสและถอดรหัส DES"""
    
    def __init__(self, key="AAAAAAAA"):
        self.key = key
    
    def decrypt_des(self, encrypted_text):
        """
        ถอดรหัส DES แบบเดียวกับโค้ด C#
        
        Args:
            encrypted_text: ข้อความที่เข้ารหัสแล้ว (Base64)
        
        Returns:
            ข้อความที่ถอดรหัสแล้ว หรือ None ถ้าเกิดข้อผิดพลาด
        """
        try:
            key = self.key
            
            # ปรับ key ให้เป็น 16 ตัวอักษร
            if len(key) < 16:
                key += "XXXXXXXXXXXXXXXX"[:16 - len(key)]
            elif len(key) > 16:
                key = key[:16]
            
            # แบ่ง key เป็น 2 ส่วน
            des_key = key[:8].encode('utf-8')
            iv = key[8:16].encode('utf-8')
            
            # แปลง Base64 เป็น bytes
            encrypted_bytes = base64.b64decode(encrypted_text)
            
            # สร้าง DES cipher
            cipher = DES.new(des_key, DES.MODE_CBC, iv)
            
            # ถอดรหัส
            decrypted_bytes = cipher.decrypt(encrypted_bytes)
            
            # ลบ padding (PKCS7)
            padding_length = decrypted_bytes[-1]
            decrypted_text = decrypted_bytes[:-padding_length].decode('utf-8')
            
            return decrypted_text
            
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการถอดรหัส: {e}")
            return None
    
    def encrypt_des(self, plain_text):
        """
        เข้ารหัส DES แบบเดียวกับโค้ด C#
        
        Args:
            plain_text: ข้อความที่ต้องการเข้ารหัส
        
        Returns:
            ข้อความที่เข้ารหัสแล้ว (Base64)
        """
        try:
            key = self.key
            
            # ปรับ key ให้เป็น 16 ตัวอักษร
            if len(key) < 16:
                key += "XXXXXXXXXXXXXXXX"[:16 - len(key)]
            elif len(key) > 16:
                key = key[:16]
            
            # แบ่ง key เป็น 2 ส่วน
            des_key = key[:8].encode('utf-8')
            iv = key[8:16].encode('utf-8')
            
            # เพิ่ม padding (PKCS7)
            plain_bytes = plain_text.encode('utf-8')
            padding_length = 8 - (len(plain_bytes) % 8)
            padded_text = plain_bytes + bytes([padding_length] * padding_length)
            
            # สร้าง DES cipher
            cipher = DES.new(des_key, DES.MODE_CBC, iv)
            
            # เข้ารหัส
            encrypted_bytes = cipher.encrypt(padded_text)
            
            # แปลงเป็น Base64
            encrypted_text = base64.b64encode(encrypted_bytes).decode('utf-8')
            
            return encrypted_text
            
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการเข้ารหัส: {e}")
            return None

class Database:
    """Class สำหรับจัดการการเชื่อมต่อฐานข้อมูล"""
    
    def __init__(self, config_file='config.json'):
        self.config = self.load_config(config_file)
        self.connection = None
    
    def load_config(self, config_file):
        """โหลด config จากไฟล์ JSON"""
        try:
            # รองรับ .exe
            if getattr(sys, 'frozen', False):
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.path.dirname(__file__)
            
            config_path = os.path.join(base_path, config_file)
            
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"ไม่สามารถโหลด config ได้: {e}")
            return None
    
    def connect(self):
        """สร้างการเชื่อมต่อกับฐานข้อมูล SQL Server"""
        try:
            if self.config is None:
                return None
            
            db_config = self.config['database']
            connection_string = (
                f"DRIVER={{{db_config['driver']}}};"
                f"SERVER={db_config['server']},{db_config['port']};"
                f"DATABASE={db_config['database']};"
                f"UID={db_config['username']};"
                f"PWD={db_config['password']};"
            )
            self.connection = pyodbc.connect(connection_string)
            return self.connection
        except Exception as e:
            print(f"ไม่สามารถเชื่อมต่อฐานข้อมูลได้: {e}")
            return None
    
    def close(self):
        """ปิดการเชื่อมต่อฐานข้อมูล"""
        if self.connection:
            self.connection.close()
    
    def execute_query(self, query, params=None):
        """Execute SQL query และส่งผลลัพธ์กลับ"""
        conn = self.connect()
        if conn is None:
            return None
        
        try:
            cursor = conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            results = cursor.fetchall()
            return results
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการ execute query: {e}")
            return None
        finally:
            self.close()
    
    def get_user_by_username(self, username):
        """ดึงข้อมูลผู้ใช้จากฐานข้อมูล"""
        query = "SELECT Username, Password, UserId FROM users WHERE active = 1 AND Username = ?"
        results = self.execute_query(query, (username,))

        if results and len(results) > 0:
            return results[0]
        return None

class AuthService:
    """Class สำหรับจัดการ Authentication"""
    
    def __init__(self):
        self.db = Database()
        self.crypto = CryptoHelper()
    
    def verify_user(self, username, password):
        """
        ตรวจสอบ username และ password
        
        Args:
            username: ชื่อผู้ใช้
            password: รหัสผ่านที่ยังไม่ได้เข้ารหัส
        
        Returns:
            dict ของข้อมูลผู้ใช้ถ้าถูกต้อง, None ถ้าไม่ถูกต้อง
        """
        try:
            # ดึงข้อมูลผู้ใช้จากฐานข้อมูล
            user_data = self.db.get_user_by_username(username)
            
            if user_data is None:
                return None
            
            db_username, encrypted_password, user_id = user_data

            # ถอดรหัสรหัสผ่านจากฐานข้อมูล
            decrypted_password = self.crypto.decrypt_des(encrypted_password)

            if decrypted_password is None:
                print("ไม่สามารถถอดรหัสรหัสผ่านได้")
                return None

            # เปรียบเทียบรหัสผ่าน
            if decrypted_password == password:
                return {
                    "username": db_username,
                    "user_id":  int(user_id) if user_id else 0,
                    "role":     "user"
                }
            else:
                return None
                
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการตรวจสอบข้อมูล: {e}")
            return None

class LoginWindow:
    """Class สำหรับหน้า Login UI"""
    
    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success
        self.auth_service = AuthService()
        self.username_entry = None
        self.password_entry = None
        self.logo_image = None
    #     self.set_window_icon()
        
    # def set_window_icon(self):
    #     try:
    #         # ถ้ารัน .exe ใช้ _MEIPASS
    #         if getattr(sys, 'frozen', False):
    #             base_path = sys._MEIPASS
    #         else:
    #             base_path = os.path.dirname(__file__)
            
    #         icon_path = os.path.join(base_path, 'bill.ico')
    #         self.root.iconbitmap(icon_path)
    #     except Exception as e:
    #         print(f"ไม่สามารถโหลด icon ได้: {e}")

            
    def _load_logos(self):
        """โหลด Logo จาก DB ครั้งเดียว → คืน (photo_small, photo_large)
        พร้อมเก็บ PIL Image ต้นฉบับใน self._logo_pil สำหรับ dynamic resize"""
        self._logo_pil = None
        try:
            db = DatabaseManager()
            company_data = db.get_company_data()
            if not (company_data
                    and 'SitePicture' in company_data
                    and company_data['SitePicture']):
                return None, None

            base64_string = company_data['SitePicture']
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            raw = base64.b64decode(base64_string)

            # เก็บต้นฉบับไว้ resize ทีหลัง
            self._logo_pil = Image.open(io.BytesIO(raw))

            # ขนาดเล็ก 120×120
            img_s = self._logo_pil.copy()
            img_s = img_s.resize((120, 120), Image.Resampling.LANCZOS)
            photo_small = ImageTk.PhotoImage(img_s)

            # ขนาดกลาง (placeholder ก่อน panel render จริง)
            img_l = self._logo_pil.copy()
            img_l.thumbnail((300, 320), Image.Resampling.LANCZOS)
            photo_large = ImageTk.PhotoImage(img_l)

            return photo_small, photo_large

        except Exception as e:
            print(f"ไม่สามารถโหลด Logo ได้: {e}")
            import traceback; traceback.print_exc()
            return None, None

    # ── compat aliases (ใช้ใน session เดิม) ───────────────────────
    def load_logo_from_db(self):
        small, _ = self._load_logos()
        return small

    def load_logo_large(self):
        _, large = self._load_logos()
        return large
                            
    def clear_window(self):
        """ล้างหน้าจอ"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    # ── Design constants ───────────────────────────────────────────
    _BODY_BG    = "#f1f5f9"   # right panel background

    def show(self):
        """แสดงหน้า Login – ซ้ายโลโก้เต็ม / ขวาฟอร์ม"""
        self.clear_window()
        self.root.title("โปรแกรมจัดการเอกสาร")

        # โหลด logo ครั้งเดียว (ทั้งสองขนาด)
        self.logo_image, self.logo_image_large = self._load_logos()

        # ── Body: left logo | right form ──────────────────────────
        body = tk.Frame(self.root, bg=self._BODY_BG)
        body.pack(fill="both", expand=True)

        # ── Left panel: Logo เต็มพื้นที่ ─────────────────────────
        left = tk.Frame(body, bg="white")
        left.pack(side="left", fill="both", expand=True)
        self._build_logo_panel(left)

        # ── Right panel: ฟอร์ม login ──────────────────────────────
        right = tk.Frame(body, bg=self._BODY_BG, width=420)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        # gear ⚙ บนขวาสุด
        gear_btn = tk.Button(
            right, text="⚙", font=("Segoe UI", 12),
            bg=self._BODY_BG, fg="#94a3b8",
            activebackground="#e2e8f0", activeforeground="#334155",
            border=0, padx=8, pady=6, cursor="hand2", relief="flat",
            command=self.show_config)
        gear_btn.pack(anchor="ne", padx=12, pady=(12, 0))
        gear_btn.bind("<Enter>",
                      lambda e: gear_btn.config(fg="#334155"))
        gear_btn.bind("<Leave>",
                      lambda e: gear_btn.config(fg="#94a3b8"))

        # vertical spacers sandwich the card
        tk.Frame(right, bg=self._BODY_BG).pack(fill="both", expand=True)
        self._build_login_card(right)
        tk.Frame(right, bg=self._BODY_BG).pack(fill="both", expand=True)

        # focus ช่อง username อัตโนมัติเมื่อเปิดหน้า login
        self.root.after(100, lambda: self.username_entry.focus_set())

    # ── Left banner panel ──────────────────────────────────────────
    def _build_logo_panel(self, parent):
        """แผงซ้าย – แสดง login_banner.png เต็มพื้นที่ (cover-fit)
        ถ้าไม่พบไฟล์ให้ fallback เป็น logo จาก DB หรือ placeholder"""

        # โหลด PIL image สำหรับแผงซ้าย
        banner_pil = None

        # 1) ลองโหลด login_banner.png ก่อน
        try:
            if getattr(sys, 'frozen', False):
                base_path = os.path.dirname(sys.executable)
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))
            banner_path = os.path.join(base_path, 'login_banner.png')
            if os.path.isfile(banner_path):
                banner_pil = Image.open(banner_path)
        except Exception as e:
            print(f"โหลด login_banner.png ไม่ได้: {e}")

        # 2) fallback → logo จาก DB
        if banner_pil is None:
            banner_pil = getattr(self, '_logo_pil', None)

        if banner_pil is None:
            # 3) fallback → placeholder
            parent.config(bg="#1e3a5f")
            inner = tk.Frame(parent, bg="#1e3a5f")
            inner.place(relx=0.5, rely=0.5, anchor="center")
            tk.Label(inner, text="📄",
                     font=("Segoe UI Emoji", 80),
                     fg="#3b82f6", bg="#1e3a5f").pack()
            tk.Label(inner, text="DocFlow Manager",
                     font=("Segoe UI", 14, "bold"),
                     fg="#93c5fd", bg="#1e3a5f").pack(pady=(8, 0))
            return

        # เก็บ PIL ไว้ใช้ใน resize
        self._banner_pil = banner_pil

        # Label เต็มพื้นที่ (cover-fit: ขยายเต็ม parent ไม่เว้นขอบ)
        lbl = tk.Label(parent, bg="white", bd=0, highlightthickness=0)
        lbl.place(x=0, y=0, relwidth=1.0, relheight=1.0)

        def _on_resize(event):
            pw, ph = event.width, event.height
            if pw < 10 or ph < 10:
                return
            iw, ih = self._banner_pil.size
            # cover-fit: scale ให้เต็มทั้งสองด้าน แล้วตัดส่วนเกิน
            scale = max(pw / iw, ph / ih)
            nw = int(iw * scale)
            nh = int(ih * scale)
            img = self._banner_pil.resize((nw, nh), Image.Resampling.LANCZOS)
            # crop ให้ได้ pw×ph (จากกึ่งกลาง)
            x0 = (nw - pw) // 2
            y0 = (nh - ph) // 2
            img = img.crop((x0, y0, x0 + pw, y0 + ph))
            photo = ImageTk.PhotoImage(img)
            lbl.config(image=photo)
            lbl.image = photo   # prevent GC

        parent.bind("<Configure>", _on_resize)

    # ── Right login form ───────────────────────────────────────────
    def _build_login_card(self, parent):
        """ฟอร์ม Login ฝั่งขวา (ไม่มี card box – วางตรงกลาง)"""
        bg = self._BODY_BG
        wrap = tk.Frame(parent, bg=bg)
        wrap.pack(fill="x", padx=40)

        # Title
        tk.Label(wrap, text="เข้าสู่ระบบ",
                 font=("Segoe UI", 22, "bold"),
                 fg="#111827", bg=bg).pack(anchor="w")
        tk.Label(wrap, text="กรุณากรอกชื่อผู้ใช้และรหัสผ่าน",
                 font=("Segoe UI", 10),
                 fg="#6b7280", bg=bg).pack(anchor="w", pady=(4, 24))

        # Form fields + button (ส่ง bg ไปด้วยเพราะพื้นหลังไม่ขาวแล้ว)
        self._create_username_field(wrap, bg=bg)
        self._create_password_field(wrap, bg=bg)
        self._create_login_button(wrap)

        # Copyright
        tk.Label(wrap,
                 text="© 2025 DocFlow Manager · All rights reserved",
                 font=("Segoe UI", 8),
                 fg="#9ca3af", bg=bg).pack(pady=(20, 0))

    def _create_username_field(self, parent, bg="#f1f5f9"):
        wrap = tk.Frame(parent, bg=bg)
        wrap.pack(fill="x", pady=(0, 16))

        tk.Label(wrap, text="ชื่อผู้ใช้",
                 font=("Segoe UI", 10, "bold"),
                 fg="#334155", bg=bg).pack(anchor="w", pady=(0, 6))

        field_bg = tk.Frame(wrap, bg="white",
                             highlightbackground="#e2e8f0",
                             highlightthickness=1)
        field_bg.pack(fill="x")

        self.username_entry = tk.Entry(
            field_bg, font=("Segoe UI", 11),
            bg="white", fg="#0f172a",
            border=0, insertbackground="#4f46e5")
        self.username_entry.pack(fill="x", padx=14, pady=11)
        self.username_entry.bind("<Return>", lambda e: self.handle_login())
        self.username_entry.bind(
            "<FocusIn>",
            lambda e: (field_bg.config(bg="#eff6ff",
                                        highlightbackground="#93c5fd",
                                        highlightthickness=2),
                       self.username_entry.config(bg="#eff6ff")))
        self.username_entry.bind(
            "<FocusOut>",
            lambda e: (field_bg.config(bg="white",
                                        highlightbackground="#e2e8f0",
                                        highlightthickness=1),
                       self.username_entry.config(bg="white")))

    def _create_password_field(self, parent, bg="#f1f5f9"):
        wrap = tk.Frame(parent, bg=bg)
        wrap.pack(fill="x", pady=(0, 24))

        tk.Label(wrap, text="รหัสผ่าน",
                 font=("Segoe UI", 10, "bold"),
                 fg="#334155", bg=bg).pack(anchor="w", pady=(0, 6))

        field_bg = tk.Frame(wrap, bg="white",
                             highlightbackground="#e2e8f0",
                             highlightthickness=1)
        field_bg.pack(fill="x")

        self.password_entry = tk.Entry(
            field_bg, font=("Segoe UI", 11),
            bg="white", fg="#0f172a",
            border=0, show="•",
            insertbackground="#4f46e5")
        self.password_entry.pack(fill="x", padx=14, pady=11)
        self.password_entry.bind("<Return>", lambda e: self.handle_login())
        self.password_entry.bind(
            "<FocusIn>",
            lambda e: (field_bg.config(bg="#eff6ff",
                                        highlightbackground="#93c5fd",
                                        highlightthickness=2),
                       self.password_entry.config(bg="#eff6ff")))
        self.password_entry.bind(
            "<FocusOut>",
            lambda e: (field_bg.config(bg="white",
                                        highlightbackground="#e2e8f0",
                                        highlightthickness=1),
                       self.password_entry.config(bg="white")))

    def _create_login_button(self, parent):
        btn = tk.Button(
            parent, text="เข้าสู่ระบบ",
            font=("Segoe UI", 12, "bold"),
            bg="#4f46e5", fg="white",
            activebackground="#4338ca", activeforeground="white",
            border=0, pady=14, cursor="hand2", relief="flat",
            command=self.handle_login)
        btn.pack(fill="x")
        btn.bind("<Enter>", lambda e: btn.config(bg="#4338ca"))
        btn.bind("<Leave>", lambda e: btn.config(bg="#4f46e5"))

    def show_config(self):
        """เปิดหน้าตั้งค่า"""
        try:
            from config import ConfigUI
            ConfigUI(self.root)
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด",
                                  f"ไม่สามารถเปิดหน้า Config ได้: {str(e)}",
                                  parent=self.root)

    def handle_login(self):
        """จัดการการ Login"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showwarning("คำเตือน", "กรุณากรอกข้อมูลให้ครบถ้วน",
                                    parent=self.root)
            return

        user_data = self.auth_service.verify_user(username, password)

        if user_data:
            self.on_login_success(user_data)
        else:
            messagebox.showerror("ข้อผิดพลาด",
                                  "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง",
                                  parent=self.root)


# ตัวอย่างการใช้งาน (สำหรับทดสอบ)
if __name__ == "__main__":
    def on_login_success(user_data):
        print(f"Login สำเร็จ: {user_data}")
        # ที่นี่คุณสามารถเรียกหน้า Dashboard หรือทำอย่างอื่นต่อได้
    
    root = tk.Tk()
    root.title("DocFlow Manager - Login")
    root.geometry("800x600")
    
    login_window = LoginWindow(root, on_login_success)
    login_window.show()
    
    root.mainloop()