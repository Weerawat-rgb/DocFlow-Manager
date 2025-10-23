import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
from login import AuthService
from login import LoginWindow

# Import modules
try:
    from PurchaseBill import PurchaseBillUI
    from SalesBill import SalesBillUI  
    from BranchBill import BranchBillUI
    from excel_manager_ui import ExcelManagerUI
    from config import ConfigUI
except ImportError as e:
    print(f"Module import error: {e}")

class UltraModernUI:
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.set_window_icon(self.root)
        self.current_user = None
        self.auth_service = AuthService()
        self.show_login()
        
    def setup_window(self):
        self.root.title("โปรแกรมออกใบวางบิล v1.3")
        self.root.geometry("1200x800")
        self.root.configure(bg='#0a0e27')
        # self.root.state('zoomed')
        self.center_window()
        
    @staticmethod
    def set_window_icon(window):
        """ตั้งค่า icon สำหรับ window ทุกตัว"""
        try:
            if getattr(sys, 'frozen', False):
                window.iconbitmap(sys.executable)
            else:
                icon_path = os.path.join(os.path.dirname(__file__), 'bill.ico')
                window.iconbitmap(icon_path)
        except Exception as e:
            print(f"ไม่สามารถโหลด icon ได้: {e}")
        
    def center_window(self):
        self.root.update_idletasks()
        width = 1200
        height = 800
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
    
    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def show_login(self):
        """แสดงหน้า Login"""
        login_window = LoginWindow(self.root, self.on_login_success)
        login_window.show()
        
    def on_login_success(self, user_data):
        """Callback เมื่อ login สำเร็จ"""
        self.current_user = user_data
        self.show_dashboard()
        
    def handle_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showwarning("คำเตือน", "กรุณากรอกข้อมูลให้ครบถ้วน")
            return
        
        # ตรวจสอบกับฐานข้อมูลผ่าน AuthService
        user_data = self.auth_service.verify_user(username, password)
        
        if user_data:
            self.current_user = user_data
            # ลบบรรทัดนี้ออก: messagebox.showinfo("สำเร็จ", f"ยินดีต้อนรับ {username}")
            self.show_dashboard()
        else:
            messagebox.showerror("ข้อผิดพลาด", "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง")    
                                
    def show_message(self, message, msg_type="info"):
        if msg_type == "error":
            messagebox.showerror("ข้อผิดพลาด", message)
        elif msg_type == "warning":
            messagebox.showwarning("คำเตือน", message)
        else:
            messagebox.showinfo("ข้อมูล", message)
            
    def show_config(self):
        try:
            from config import ConfigUI
            ConfigUI(self.root)
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถเปิดหน้า Config ได้: {str(e)}")
            print(f"Config error: {e}")
    
    def show_dashboard(self):
        self.clear_window()
        
        # Modern header
        header = tk.Frame(self.root, bg='#1f2937', height=80)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        header_content = tk.Frame(header, bg='#1f2937')
        header_content.pack(fill='both', expand=True, padx=30, pady=15)
        
        # Left - Brand
        left_frame = tk.Frame(header_content, bg='#1f2937')
        left_frame.pack(side='left', fill='y')
        
        tk.Label(left_frame, text="ระบบวางบิล", 
                font=('Segoe UI', 18, 'bold'), 
                fg='white', bg='#1f2937').pack(anchor='w')
        
        tk.Label(left_frame, text="ระบบจัดการเอกสารบัญชี", 
                font=('Segoe UI', 9), 
                fg='#d1d5db', bg='#1f2937').pack(anchor='w')
        
        # Right - User info
        right_frame = tk.Frame(header_content, bg='#1f2937')
        right_frame.pack(side='right', fill='y')
        
        tk.Label(right_frame, text=f"👤 {self.current_user['username']}", 
               font=('Segoe UI', 11), 
               fg='white', bg='#1f2937').pack(anchor='e')
        
        logout_btn = tk.Button(right_frame, text="🚪 ออกจากระบบ",
                             font=('Segoe UI', 9),
                             bg='#ef4444', fg='white',
                             border=0, padx=15, pady=6,
                             cursor='hand2',
                             command=self.logout)
        logout_btn.pack(anchor='e', pady=(5, 0))
        
        # Main dashboard
        main_content = tk.Frame(self.root, bg='#f8fafc')
        main_content.pack(fill='both', expand=True, padx=30, pady=30)
        
        # Title
        title_frame = tk.Frame(main_content, bg='#f8fafc')
        title_frame.pack(fill='x', pady=(0, 30))
        
        tk.Label(title_frame, text="เลือกประเภทการวางบิล", 
                font=('Segoe UI', 20, 'bold'), 
                fg='#1f2937', bg='#f8fafc').pack(anchor='w')
        
        tk.Label(title_frame, text="คลิกที่ประเภทเอกสารที่ต้องการใช้งาน", 
                font=('Segoe UI', 11), 
                fg='#6b7280', bg='#f8fafc').pack(anchor='w', pady=(5, 0))
        
        # Modules grid
        modules_grid = tk.Frame(main_content, bg='#f8fafc')
        modules_grid.pack(fill='both', expand=True)
        
        # Configure grid
        for i in range(2):
            modules_grid.grid_rowconfigure(i, weight=1)
            modules_grid.grid_columnconfigure(i, weight=1)
        
        # Create module cards
        modules_data = [
            {"row": 0, "col": 0, "title": "📋 ใบวางบิลซื้อ", 
             "desc": "จัดการใบวางบิลการซื้อสินค้า\nค้นหาผู้จัดจำหน่าย • เลือกบิลรับ • ออกเอกสาร", 
             "color": "#3b82f6", "hover": "#2563eb", "cmd": self.open_module1},
            
            {"row": 0, "col": 1, "title": "🛒 ใบวางบิลขาย", 
             "desc": "จัดการใบวางบิลการขายสินค้า\nค้นหาลูกค้า • เลือกบิลขาย • ออกเอกสาร", 
             "color": "#10b981", "hover": "#059669", "cmd": self.open_module2},
            
            {"row": 1, "col": 0, "title": "🏪 ใบวางบิลขาย [สาขา]", 
             "desc": "จัดการใบวางบิลขายระหว่างสาขา\nค้นหาสาขา • เลือกบิลเบิกออก • ออกเอกสาร", 
             "color": "#f59e0b", "hover": "#d97706", "cmd": self.open_module3},
            
            {"row": 1, "col": 1, "title": "📤 Import ใบรับเข้าสินค้า", 
             "desc": "นำเข้าข้อมูลใบรับจากไฟล์ภายนอก\nรองรับ Excel/CSV • ประมวลผลอัตโนมัติ", 
             "color": "#8b5cf6", "hover": "#7c3aed", "cmd": self.open_module4}
        ]
        
        for module in modules_data:
            self.create_module_card(modules_grid, module)
    
    def create_module_card(self, parent, module_data):
        # Card with shadow
        card_container = tk.Frame(parent, bg='#f8fafc')
        card_container.grid(row=module_data["row"], column=module_data["col"], 
                           padx=15, pady=15, sticky='nsew')
        
        # Shadow
        shadow = tk.Frame(card_container, bg='#e5e7eb')
        shadow.pack(fill='both', expand=True, padx=(4, 0), pady=(4, 0))
        
        # Main card
        card = tk.Frame(card_container, bg='white', cursor='hand2')
        card.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Color accent
        accent = tk.Frame(card, bg=module_data["color"], height=8)
        accent.pack(fill='x')
        
        # Content
        content = tk.Frame(card, bg='white', padx=25, pady=25)
        content.pack(fill='both', expand=True)
        
        # Title
        tk.Label(content, text=module_data["title"],
               font=('Segoe UI', 15, 'bold'),
               fg='#1f2937', bg='white').pack(anchor='w', pady=(0, 15))
        
        # Description
        tk.Label(content, text=module_data["desc"],
               font=('Segoe UI', 10),
               fg='#6b7280', bg='white',
               justify='left').pack(fill='x', anchor='w')
        
        # Action button
        action_btn = tk.Button(content, text="เข้าใช้งาน →",
                             font=('Segoe UI', 10, 'bold'),
                             bg=module_data["color"], fg='white',
                             border=0, padx=20, pady=10,
                             cursor='hand2',
                             command=module_data["cmd"])
        action_btn.pack(anchor='w', pady=(20, 0))
        
        # Hover effects
        def on_enter(event):
            accent.config(bg=module_data["hover"])
            action_btn.config(bg=module_data["hover"])
            
        def on_leave(event):
            accent.config(bg=module_data["color"])
            action_btn.config(bg=module_data["color"])
        
        for widget in [card, content]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)
            widget.bind("<Button-1>", lambda e: module_data["cmd"]())
    
    def open_module1(self):
        try:
            from PurchaseBill import PurchaseBillUI
            PurchaseBillUI(self.root, self.current_user)
        except NameError:
            messagebox.showinfo("ข้อมูล", "จะเปิด Module 1: ใบวางบิลซื้อ ในสเต๊บต่อไป")
    
    def open_module2(self):
        try:
            from SalesBill import SalesBillUI
            SalesBillUI(self.root, self.current_user)
        except NameError:
            messagebox.showinfo("ข้อมูล", "จะเปิด Module 2: ใบวางบิลขาย ในสเต๊บต่อไป")
    
    def open_module3(self):
        try:
            from BranchBill import BranchBillUI
            BranchBillUI(self.root, self.current_user)
        except NameError:
            messagebox.showinfo("ข้อมูล", "จะเปิด Module 3: ใบวางบิลขาย [สาขา] ในสเต๊บต่อไป")
    
    def open_module4(self):
        try:
            ExcelManagerUI(self.root, self.current_user)
        except NameError:
            messagebox.showinfo("ข้อมูล", "จะเปิด Module 4: Import ใบรับเข้าสินค้า ในสเต๊บต่อไป")
    
    def logout(self):
        self.current_user = None
        self.show_login()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = UltraModernUI()
    app.run()