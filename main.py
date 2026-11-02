import tkinter as tk
from tkinter import ttk, messagebox
import sys
import os
from login import AuthService
from login import LoginWindow

import theme

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
        self.root.title("โปรแกรมออกใบวางบิล v1.5")
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
            messagebox.showwarning("คำเตือน", "กรุณากรอกข้อมูลให้ครบถ้วน",
                parent=self.root)
            return
        
        # ตรวจสอบกับฐานข้อมูลผ่าน AuthService
        user_data = self.auth_service.verify_user(username, password)
        
        if user_data:
            self.current_user = user_data
            # ลบบรรทัดนี้ออก: messagebox.showinfo("สำเร็จ", f"ยินดีต้อนรับ {username}")
            self.show_dashboard()
        else:
            messagebox.showerror("ข้อผิดพลาด", "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง",
                parent=self.root)    
                                
    def show_message(self, message, msg_type="info"):
        if msg_type == "error":
            messagebox.showerror("ข้อผิดพลาด", message,
                parent=self.root)
        elif msg_type == "warning":
            messagebox.showwarning("คำเตือน", message,
                parent=self.root)
        else:
            messagebox.showinfo("ข้อมูล", message,
                parent=self.root)
            
    def show_config(self):
        try:
            from config import ConfigUI
            ConfigUI(self.root)
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถเปิดหน้า Config ได้: {str(e)}",
                parent=self.root)
            print(f"Config error: {e}")
    
    def show_dashboard(self):
        self.clear_window()
        theme.configure_styles()

        # ── Header ────────────────────────────────────────────────
        theme.build_header(
            self.root,
            title   = "ระบบวางบิล  DocFlow",
            subtitle= "ระบบจัดการเอกสารบัญชีครบวงจร",
            username= self.current_user["username"],
            accent  = theme.INDIGO,
        )

        # Right side of header: logout button  (inject into header bar)
        hdr = self.root.winfo_children()[-2]   # header frame
        right_extra = tk.Frame(hdr, bg=theme.BG_DARK)
        right_extra.place(relx=1.0, rely=0.5, anchor="e", x=-theme.SIDE_PAD)
        logout_btn = tk.Button(
            right_extra, text="🚪  ออกจากระบบ",
            font=theme.F_SMALL, bg=theme.RED, fg=theme.TEXT_WHITE,
            border=0, padx=12, pady=6, cursor="hand2",
            command=self.logout)
        logout_btn.pack()
        theme._hover(logout_btn, theme.RED_H, theme.RED)

        # ── Page content ──────────────────────────────────────────
        page = tk.Frame(self.root, bg=theme.BG_PAGE)
        page.pack(fill="both", expand=True)

        # Page title
        title_frame = tk.Frame(page, bg=theme.BG_PAGE)
        title_frame.pack(fill="x", padx=theme.SIDE_PAD, pady=(24, 0))

        tk.Label(title_frame, text="เลือกโมดูลการทำงาน",
                 font=theme.F_H1, fg=theme.TEXT_DARK,
                 bg=theme.BG_PAGE).pack(anchor="w")
        tk.Label(title_frame, text="คลิกที่โมดูลด้านล่างเพื่อเริ่มใช้งาน",
                 font=theme.F_SMALL, fg=theme.TEXT_MUTED,
                 bg=theme.BG_PAGE).pack(anchor="w", pady=(4, 0))

        theme.divider(title_frame).pack(fill="x", pady=(14, 0))

        # ── Module grid ───────────────────────────────────────────
        grid_outer = tk.Frame(page, bg=theme.BG_PAGE)
        grid_outer.pack(fill="both", expand=True,
                        padx=theme.SIDE_PAD, pady=20)

        for i in range(3):
            grid_outer.grid_rowconfigure(i, weight=1)
        for i in range(2):
            grid_outer.grid_columnconfigure(i, weight=1)

        modules_data = [
            {"row": 0, "col": 0,
             "title": "📋 ใบวางบิลซื้อ",
             "desc": "จัดการใบวางบิลการซื้อสินค้า",
             "tags": "ค้นหาผู้จัดจำหน่าย · เลือกบิลรับ · ออกเอกสาร",
             "color": theme.BLUE, "hover": theme.BLUE_H,
             "cmd": self.open_module1},

            {"row": 0, "col": 1,
             "title": "🛒 ใบวางบิลขาย",
             "desc": "จัดการใบวางบิลการขายสินค้า",
             "tags": "ค้นหาลูกค้า · เลือกบิลขาย · ออกเอกสาร",
             "color": theme.GREEN, "hover": theme.GREEN_H,
             "cmd": self.open_module2},

            {"row": 1, "col": 0,
             "title": "🏪 ใบวางบิลขาย [สาขา]",
             "desc": "จัดการใบวางบิลขายระหว่างสาขา",
             "tags": "ค้นหาสาขา · เลือกบิลเบิกออก · ออกเอกสาร",
             "color": theme.AMBER, "hover": theme.AMBER_H,
             "cmd": self.open_module3},

            {"row": 1, "col": 1,
             "title": "📤 Import ใบรับเข้าสินค้า",
             "desc": "นำเข้าข้อมูลใบรับจากไฟล์ภายนอก",
             "tags": "รองรับ Excel/CSV · ประมวลผลอัตโนมัติ",
             "color": theme.PURPLE, "hover": theme.PURPLE_H,
             "cmd": self.open_module4},
        ]

        edit_sale_data = {
            "row": 2, "col": 0, "colspan": 2,
            "title": "✏️ ค้นหา / แก้ไขบิลขาย",
            "desc": "ดึงหมายเลขบิลขายและแก้ไขรายการสินค้า อัพเดทกลับฐานข้อมูล",
            "tags": "ค้นหาเลขที่บิล · เลือกบิล · แก้ไขรายการ · บันทึก",
            "color": theme.GREEN, "hover": theme.GREEN_H,
            "cmd": self.open_edit_sale_bill,
        }

        for mod in modules_data:
            self.create_module_card(grid_outer, mod)
        self.create_module_card(grid_outer, edit_sale_data)

    def create_module_card(self, parent, data):
        colspan = data.get("colspan", 1)
        color   = data["color"]
        hover   = data["hover"]

        # Container
        container = tk.Frame(parent, bg=theme.BG_PAGE)
        container.grid(row=data["row"], column=data["col"],
                       columnspan=colspan,
                       padx=10, pady=10, sticky="nsew")

        # Shadow layer
        shadow = tk.Frame(container, bg=theme.BORDER)
        shadow.pack(fill="both", expand=True, padx=(3, 0), pady=(3, 0))

        # Card
        card_frame = tk.Frame(container, bg=theme.BG_CARD, cursor="hand2")
        card_frame.place(x=0, y=0, relwidth=1, relheight=1)

        # Top accent bar
        accent_bar = tk.Frame(card_frame, bg=color, height=5)
        accent_bar.pack(fill="x")

        # Content area
        content = tk.Frame(card_frame, bg=theme.BG_CARD, padx=24, pady=20)
        content.pack(fill="both", expand=True)

        # Icon + title row
        title_row = tk.Frame(content, bg=theme.BG_CARD)
        title_row.pack(fill="x", anchor="w")

        tk.Label(title_row, text=data["title"],
                 font=theme.F_H2, fg=theme.TEXT_DARK,
                 bg=theme.BG_CARD).pack(side="left", anchor="w")

        # Divider
        tk.Frame(content, bg=theme.BORDER, height=1).pack(
            fill="x", pady=(10, 8))

        # Description
        tk.Label(content, text=data["desc"],
                 font=theme.F_BODY, fg=theme.TEXT_MED,
                 bg=theme.BG_CARD, anchor="w").pack(anchor="w")

        # Tags row
        tag_frame = tk.Frame(content, bg=theme.BG_CARD)
        tag_frame.pack(anchor="w", pady=(6, 0))
        for tag in data.get("tags", "").split("·"):
            t = tag.strip()
            if t:
                lbl = tk.Label(tag_frame,
                               text=f"  {t}  ",
                               font=theme.F_CAPTION,
                               bg=theme.BG_INPUT,
                               fg=theme.TEXT_MUTED,
                               padx=2, pady=2)
                lbl.pack(side="left", padx=(0, 4))

        # CTA button
        cta = tk.Button(content, text="เข้าใช้งาน  →",
                        font=theme.F_SMALL_B,
                        bg=color, fg=theme.TEXT_WHITE,
                        border=0, padx=18, pady=8,
                        cursor="hand2",
                        command=data["cmd"])
        cta.pack(anchor="w", pady=(14, 0))

        # Hover effects
        def on_enter(e):
            accent_bar.config(bg=hover)
            cta.config(bg=hover)
        def on_leave(e):
            accent_bar.config(bg=color)
            cta.config(bg=color)

        for w in [card_frame, content, title_row]:
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", lambda e, cmd=data["cmd"]: cmd())


    def open_module1(self):
        try:
            from PurchaseBill import PurchaseBillUI
            PurchaseBillUI(self.root, self.current_user)
        except NameError:
            messagebox.showinfo("ข้อมูล", "จะเปิด Module 1: ใบวางบิลซื้อ ในสเต๊บต่อไป",
                parent=self.root)
    
    def open_module2(self):
        try:
            from SalesBill import SalesBillUI
            SalesBillUI(self.root, self.current_user)
        except NameError:
            messagebox.showinfo("ข้อมูล", "จะเปิด Module 2: ใบวางบิลขาย ในสเต๊บต่อไป",
                parent=self.root)
    
    def open_module3(self):
        try:
            from BranchBill import BranchBillUI
            BranchBillUI(self.root, self.current_user)
        except NameError:
            messagebox.showinfo("ข้อมูล", "จะเปิด Module 3: ใบวางบิลขาย [สาขา] ในสเต๊บต่อไป",
                parent=self.root)
    
    def open_module4(self):
        try:
            ExcelManagerUI(self.root, self.current_user)
        except NameError:
            messagebox.showinfo("ข้อมูล", "จะเปิด Module 4: Import ใบรับเข้าสินค้า ในสเต๊บต่อไป",
                parent=self.root)

    def open_edit_sale_bill(self):
        try:
            from EditSaleBill import EditSaleBillUI
            EditSaleBillUI(self.root, self.current_user)
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถเปิดหน้าแก้ไขบิลได้: {str(e)}",
                parent=self.root)

    def logout(self):
        self.current_user = None
        self.show_login()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = UltraModernUI()
    app.run()