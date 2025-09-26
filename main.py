import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os

# Import modules
try:
    from module1 import PurchaseBillUI
    from module2 import SalesBillUI  
    from module3 import BranchBillUI
    from module4 import ImportBillUI
    from config import ConfigUI
except ImportError as e:
    print(f"Module import error: {e}")

class UltraModernUI:
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.current_user = None
        self.show_login()
        
    def setup_window(self):
        self.root.title("DocFlow Manager - Ultra Modern Edition")
        self.root.geometry("1200x800")
        self.root.configure(bg='#0a0e27')
        # self.root.state('zoomed')
        self.center_window()
        
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
        self.clear_window()
        
        # Soft gradient background - ละมุนตา
        main_container = tk.Frame(self.root, bg='#f8fafc')
        main_container.pack(fill='both', expand=True)
        
        # Subtle gradient layers - นุ่มนวล
        gradient_layers = [
            {'bg': '#e0e7ff', 'height': 0.4, 'y': 0},
            {'bg': '#c7d2fe', 'height': 0.3, 'y': 0.2},
            {'bg': '#a5b4fc', 'height': 0.2, 'y': 0.4},
        ]
        
        for layer in gradient_layers:
            grad_frame = tk.Frame(main_container, bg=layer['bg'])
            grad_frame.place(x=0, y=0, relwidth=1, relheight=layer['height'], rely=layer['y'])
        
        # Settings button at top right corner
        settings_btn = tk.Button(main_container, text="⚙️",
                               font=('Segoe UI', 14),
                               bg='#f8fafc', fg='#64748b',
                               activebackground='#e2e8f0',
                               activeforeground='#475569',
                               border=0, padx=12, pady=8,
                               cursor='hand2',
                               relief='flat',
                               command=self.show_config)
        settings_btn.place(relx=1.0, rely=0.0, anchor='ne', x=-20, y=20)
        
        # Settings hover effects
        settings_btn.bind("<Enter>", lambda e: settings_btn.config(bg='#e2e8f0', fg='#475569'))
        settings_btn.bind("<Leave>", lambda e: settings_btn.config(bg='#f8fafc', fg='#64748b'))
        
        # Clean login card - เรียบสะอาด
        login_card = tk.Frame(main_container, bg='white', padx=50, pady=50)
        login_card.place(relx=0.5, rely=0.5, anchor='center', width=400, height=520)
        
        # Soft shadow effect
        shadow = tk.Frame(main_container, bg='#e2e8f0', padx=50, pady=50)
        shadow.place(relx=0.5, rely=0.5, anchor='center', width=400, height=520, x=3, y=3)
        login_card.lift()
        
        # === HEADER SECTION ===
        header_section = tk.Frame(login_card, bg='white', height=120)
        header_section.pack(fill='x', pady=(0, 30))
        header_section.pack_propagate(False)
        
        # Simple, clean logo
        logo_container = tk.Frame(header_section, bg='white')
        logo_container.pack(pady=(20, 15))
        
        logo_bg = tk.Frame(logo_container, bg='#6366f1', width=70, height=70)
        logo_bg.pack()
        logo_bg.pack_propagate(False)
        
        tk.Label(logo_bg, text="📊", font=('Segoe UI Emoji', 24), 
                fg='white', bg='#6366f1').pack(expand=True)
        
        tk.Label(header_section, text="DocFlow Manager", 
                font=('Segoe UI', 20, 'bold'), 
                fg='#374151', bg='white').pack(pady=(0, 0))
        
        tk.Label(header_section, text="ระบบจัดการเอกสารบัญชี", 
               font=('Segoe UI', 11), 
               fg='#6b7280', bg='white').pack()
        
        # === FORM SECTION ===
        form_section = tk.Frame(login_card, bg='white')
        form_section.pack(fill='x', pady=(0, 30))
        
        # Username field
        username_container = tk.Frame(form_section, bg='white')
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
        
        def on_username_focus_in(event):
            username_bg.config(bg='#f0f9ff', relief='solid', bd=2)
            self.username_entry.config(bg='#f0f9ff')
            
        def on_username_focus_out(event):
            username_bg.config(bg='#f9fafb', relief='solid', bd=1)
            self.username_entry.config(bg='#f9fafb')
        
        self.username_entry.bind("<FocusIn>", on_username_focus_in)
        self.username_entry.bind("<FocusOut>", on_username_focus_out)
        
        # Password field
        password_container = tk.Frame(form_section, bg='white')
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
        
        def on_password_focus_in(event):
            password_bg.config(bg='#f0f9ff', relief='solid', bd=2)
            self.password_entry.config(bg='#f0f9ff')
            
        def on_password_focus_out(event):
            password_bg.config(bg='#f9fafb', relief='solid', bd=1)
            self.password_entry.config(bg='#f9fafb')
        
        self.password_entry.bind("<FocusIn>", on_password_focus_in)
        self.password_entry.bind("<FocusOut>", on_password_focus_out)
        
        # Login button
        login_btn = tk.Button(form_section, text="เข้าสู่ระบบ",
                            font=('Segoe UI', 12, 'bold'),
                            bg='#6366f1', fg='white',
                            activebackground='#4f46e5',
                            activeforeground='white',
                            border=0, pady=14,
                            cursor='hand2',
                            relief='flat',
                            command=self.handle_login)
        login_btn.pack(fill='x', pady=(25, 0))
        
        login_btn.bind("<Enter>", lambda e: login_btn.config(bg='#4f46e5'))
        login_btn.bind("<Leave>", lambda e: login_btn.config(bg='#6366f1'))
        
        # === FOOTER SECTION ===
        footer_section = tk.Frame(login_card, bg='white')
        footer_section.pack(side='bottom', fill='x')
        
        tk.Label(footer_section, text="© 2025 DocFlow Manager", 
               font=('Segoe UI', 9), 
               fg='#9ca3af', bg='white').pack(pady=(10, 0))
    

        
    def handle_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            messagebox.showwarning("คำเตือน", "กรุณากรอกข้อมูลให้ครบถ้วน")
            return
            
        # Simple validation
        if username == "admin" and password == "123":
            self.current_user = {"username": username, "role": "admin"}
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
        
        tk.Label(left_frame, text="◆ DocFlow Manager", 
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
        
        tk.Label(title_frame, text="🚀 เลือกโมดูลการทำงาน", 
                font=('Segoe UI', 20, 'bold'), 
                fg='#1f2937', bg='#f8fafc').pack(anchor='w')
        
        tk.Label(title_frame, text="คลิกที่โมดูลที่ต้องการใช้งาน", 
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
            PurchaseBillUI(self.root, self.current_user)
        except NameError:
            messagebox.showinfo("ข้อมูล", "จะเปิด Module 1: ใบวางบิลซื้อ ในสเต๊บต่อไป")
    
    def open_module2(self):
        try:
            SalesBillUI(self.root, self.current_user)
        except NameError:
            messagebox.showinfo("ข้อมูล", "จะเปิด Module 2: ใบวางบิลขาย ในสเต๊บต่อไป")
    
    def open_module3(self):
        try:
            BranchBillUI(self.root, self.current_user)
        except NameError:
            messagebox.showinfo("ข้อมูล", "จะเปิด Module 3: ใบวางบิลขาย [สาขา] ในสเต๊บต่อไป")
    
    def open_module4(self):
        try:
            ImportBillUI(self.root, self.current_user)
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