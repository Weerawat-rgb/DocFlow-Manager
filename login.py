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
        query = "SELECT Username, Password FROM users WHERE active = 1 AND Username = ?"
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
            
            db_username, encrypted_password = user_data
            
            # ถอดรหัสรหัสผ่านจากฐานข้อมูล
            decrypted_password = self.crypto.decrypt_des(encrypted_password)
            
            if decrypted_password is None:
                print("ไม่สามารถถอดรหัสรหัสผ่านได้")
                return None
            
            # เปรียบเทียบรหัสผ่าน
            if decrypted_password == password:
                return {
                    "username": db_username,
                    "role": "user"
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

            
    def load_logo_from_db(self):
        """โหลด Logo จากฐานข้อมูล"""
        try:
            db = DatabaseManager()
            company_data = db.get_company_data()
            
            if company_data and 'SitePicture' in company_data and company_data['SitePicture']:
                # SitePicture เป็น base64 string แบบ "data:image/jpeg;base64,..."
                base64_string = company_data['SitePicture']
                
                # ตัด prefix "data:image/jpeg;base64," ออก
                if ',' in base64_string:
                    base64_string = base64_string.split(',')[1]
                
                # แปลง base64 เป็น bytes
                image_data = base64.b64decode(base64_string)
                
                # แปลง bytes เป็น Image
                image = Image.open(io.BytesIO(image_data))
                
                # ปรับขนาด logo
                image = image.resize((120, 120), Image.Resampling.LANCZOS)
                
                # แปลงเป็น PhotoImage
                photo = ImageTk.PhotoImage(image)
                return photo
            
            return None
            
        except Exception as e:
            print(f"ไม่สามารถโหลด Logo ได้: {e}")
            import traceback
            traceback.print_exc()
            return None
                            
    def clear_window(self):
        """ล้างหน้าจอ"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def show(self):
        """แสดงหน้า Login"""
        self.clear_window()
        
        self.logo_image = self.load_logo_from_db()
        
        # Soft gradient background
        main_container = tk.Frame(self.root, bg='#f8fafc')
        main_container.pack(fill='both', expand=True)
        
        # Subtle gradient layers
        gradient_layers = [
            {'bg': '#18181b', 'height': 0.5, 'y': 0},
            {'bg': '#27272a', 'height': 0.3, 'y': 0.3},
            {'bg': '#3f3f46', 'height': 0.2, 'y': 0.5},
        ]
        
        for layer in gradient_layers:
            grad_frame = tk.Frame(main_container, bg=layer['bg'])
            grad_frame.place(x=0, y=0, relwidth=1, relheight=layer['height'], rely=layer['y'])
        
        # Clean login card - เพิ่มความสูง
        login_card = tk.Frame(main_container, bg='white', padx=50, pady=40)
        login_card.place(relx=0.5, rely=0.5, anchor='center', width=420, height=650)
        
        # Soft shadow effect
        shadow = tk.Frame(main_container, bg='#e2e8f0', padx=50, pady=40)
        shadow.place(relx=0.5, rely=0.5, anchor='center', width=420, height=650, x=3, y=3)
        login_card.lift()
        
        # === HEADER SECTION ===
        self._create_header(login_card)
        
        # === FORM SECTION ===
        self._create_form(login_card)
        
        # === FOOTER SECTION ===
        self._create_footer(login_card)
        
        # Settings button at top right corner - ปรับให้เข้ากับ theme
        settings_btn = tk.Button(main_container, text="⚙️",
                            font=('Segoe UI', 16),
                            bg='#27272a', fg='#9ca3af',
                            activebackground='#3f3f46',
                            activeforeground='#d1d5db',
                            border=0, padx=15, pady=10,
                            cursor='hand2',
                            relief='flat',
                            command=self.show_config)
        settings_btn.place(relx=1.0, rely=0.0, anchor='ne', x=-20, y=20)
        
        # Settings hover effects
        settings_btn.bind("<Enter>", lambda e: settings_btn.config(bg='#3f3f46', fg='#d1d5db'))
        settings_btn.bind("<Leave>", lambda e: settings_btn.config(bg='#27272a', fg='#9ca3af'))
    
    def _create_header(self, parent):
        """สร้าง Header Section"""
        header_section = tk.Frame(parent, bg='white', height=220)  
        header_section.pack(fill='x', pady=(10, 20)) 
        header_section.pack_propagate(False)
        
        # Logo
        logo_container = tk.Frame(header_section, bg='white')
        logo_container.pack(pady=(20, 15))
        
        # โหลด logo จากฐานข้อมูล
        if self.logo_image:
            # แสดง logo จากฐานข้อมูล
            logo_label = tk.Label(logo_container, image=self.logo_image, bg='white')
            logo_label.pack()
            logo_label.image = self.logo_image  # เก็บ reference
        else:
            # แสดง logo เริ่มต้น
            logo_bg = tk.Frame(logo_container, bg='#6366f1', width=70, height=70)
            logo_bg.pack()
            logo_bg.pack_propagate(False)
            
            tk.Label(logo_bg, text="📊", font=('Segoe UI Emoji', 24), 
                    fg='white', bg='#6366f1').pack(expand=True)
        
        # Title
        tk.Label(header_section, text="ระบบวางบิล", 
                font=('Segoe UI', 20, 'bold'), 
                fg='#374151', bg='white').pack(pady=(5, 5))
        
        # Subtitle
        tk.Label(header_section, text="ระบบจัดการเอกสารวางบิล", 
            font=('Segoe UI', 11), 
            fg='#6b7280', bg='white').pack()    
        
    def _create_form(self, parent):
        """สร้าง Form Section"""
        form_section = tk.Frame(parent, bg='white')
        form_section.pack(fill='x', pady=(0, 30))
        
        # Username field
        self._create_username_field(form_section)
        
        # Password field
        self._create_password_field(form_section)
        
        # Login button
        self._create_login_button(form_section)
    
    def _create_username_field(self, parent):
        """สร้างช่องกรอก Username"""
        username_container = tk.Frame(parent, bg='white')
        username_container.pack(fill='x', pady=(0, 20))
        
        tk.Label(username_container, text="ชื่อผู้ใช้",
                font=('Segoe UI', 10, 'bold'),
                fg='#374151', bg='white').pack(anchor='w', pady=(0, 6))
        
        username_bg = tk.Frame(username_container, bg='#f9fafb', relief='solid', bd=1)
        username_bg.pack(fill='x')
        
        self.username_entry = tk.Entry(username_bg, font=('Segoe UI', 11),
                        bg='#f9fafb', fg='#374151',
                        border=0, insertbackground='#6366f1')
        self.username_entry.pack(fill='x', padx=14, pady=12)
        self.username_entry.bind("<Return>", lambda event: self.handle_login())
        
        # Focus effects
        def on_focus_in(event):
            username_bg.config(bg='#f0f9ff', relief='solid', bd=2)
            self.username_entry.config(bg='#f0f9ff')
            
        def on_focus_out(event):
            username_bg.config(bg='#f9fafb', relief='solid', bd=1)
            self.username_entry.config(bg='#f9fafb')
        
        self.username_entry.bind("<FocusIn>", on_focus_in)
        self.username_entry.bind("<FocusOut>", on_focus_out)
    
    def _create_password_field(self, parent):
        """สร้างช่องกรอก Password"""
        password_container = tk.Frame(parent, bg='white')
        password_container.pack(fill='x', pady=(0, 20))
        
        tk.Label(password_container, text="รหัสผ่าน",
                font=('Segoe UI', 10, 'bold'),
                fg='#374151', bg='white').pack(anchor='w', pady=(0, 6))
        
        password_bg = tk.Frame(password_container, bg='#f9fafb', relief='solid', bd=1)
        password_bg.pack(fill='x')
        
        self.password_entry = tk.Entry(password_bg, font=('Segoe UI', 11),
                        bg='#f9fafb', fg='#374151',
                        border=0, show='•',
                        insertbackground='#6366f1')
        self.password_entry.pack(fill='x', padx=14, pady=12)
        self.password_entry.bind("<Return>", lambda event: self.handle_login())
        
        # Focus effects
        def on_focus_in(event):
            password_bg.config(bg='#f0f9ff', relief='solid', bd=2)
            self.password_entry.config(bg='#f0f9ff')
            
        def on_focus_out(event):
            password_bg.config(bg='#f9fafb', relief='solid', bd=1)
            self.password_entry.config(bg='#f9fafb')
        
        self.password_entry.bind("<FocusIn>", on_focus_in)
        self.password_entry.bind("<FocusOut>", on_focus_out)
    
    def _create_login_button(self, parent):
        """สร้างปุ่ม Login"""
        # สร้าง frame สำหรับจัดตำแหน่งปุ่ม
        btn_frame = tk.Frame(parent, bg='white')
        btn_frame.pack(fill='x', pady=(25, 0))
        
        login_btn = tk.Button(btn_frame, text="เข้าสู่ระบบ",  # เปลี่ยนเป็น btn_frame
                            font=('Segoe UI', 13, 'bold'),
                            bg='#0284c7', fg='white',
                            activebackground='#0369a1',
                            activeforeground='white',
                            border=0, 
                            pady=16,
                            cursor='hand2',
                            relief='flat',
                            command=self.handle_login)
        login_btn.pack(fill='x', padx=40)  
        
        # Hover effects
        login_btn.bind("<Enter>", lambda e: login_btn.config(bg='#0369a1'))
        login_btn.bind("<Leave>", lambda e: login_btn.config(bg='#0284c7'))    
        
    def _create_footer(self, parent):
        """สร้าง Footer Section"""
        footer_section = tk.Frame(parent, bg='white')
        footer_section.pack(side='bottom', fill='x')
        
        tk.Label(footer_section, text="© 2025 DocFlow Manager", 
               font=('Segoe UI', 9), 
               fg='#9ca3af', bg='white').pack(pady=(10, 0))
        
    def show_config(self):
        """เปิดหน้าตั้งค่า"""
        try:
            from config import ConfigUI
            ConfigUI(self.root)
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถเปิดหน้า Config ได้: {str(e)}")
            print(f"Config error: {e}")
    
    def handle_login(self):
        """จัดการการ Login"""
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showwarning("คำเตือน", "กรุณากรอกข้อมูลให้ครบถ้วน")
            return
        
        user_data = self.auth_service.verify_user(username, password)
        
        if user_data:
            self.on_login_success(user_data)
        else:
            messagebox.showerror("ข้อผิดพลาด", "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")

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