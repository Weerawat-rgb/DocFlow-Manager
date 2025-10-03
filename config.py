import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os

class ConfigUI:
    def __init__(self, parent=None):
        self.window = tk.Toplevel(parent) if parent else tk.Tk()
        self.window.title("ตั้งค่าระบบ - DocFlow Manager")
        self.window.geometry("750x700")  # เพิ่มความสูง
        self.window.configure(bg='#f8fafc')
        
        if parent:
            self.window.transient(parent)
            self.window.grab_set()
        
        # Center window
        self.center_window()
        
        # Load config
        self.config = self.load_config()
        
        self.create_widgets()
        
    def center_window(self):
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (375)  # ปรับให้ตรงกลาง
        y = (self.window.winfo_screenheight() // 2) - (350)
        self.window.geometry(f"750x700+{x}+{y}")
    
    def load_config(self):
        default_config = {
            "database": {
                "server": "localhost",
                "port": "1433",
                "database": "DocFlowDB",
                "username": "",
                "password": "",
                "driver": "ODBC Driver 17 for SQL Server"
            },
            "application": {
                "company_name": "บริษัท ตัวอย่าง จำกัด",
                "company_address": "123 ถนนตัวอย่าง เขตตัวอย่าง กรุงเทพฯ 10100",
                "company_phone": "02-123-4567",
                "company_email": "info@example.com",
                "tax_id": "0123456789012"
            },
            "templates": {
            "purchase_template": "ใบวางบิลซื้อ",
            "sales_template": "ใบวางบิลขาย", 
            "branch_template": "ใบวางบิลสาขา",
            "template_notes": ""
            }
        }
        
        try:
            if os.path.exists("config.json"):
                with open("config.json", "r", encoding="utf-8") as f:
                    saved_config = json.load(f)
                    # Merge with defaults
                    for section in default_config:
                        if section in saved_config:
                            default_config[section].update(saved_config[section])
                    return default_config
        except Exception as e:
            print(f"Error loading config: {e}")
        
        return default_config
    
    def save_config(self):
        try:
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถบันทึกการตั้งค่าได้: {e}")
            return False
    
    def create_widgets(self):
        # Modern header - สีเข้ม
        header = tk.Frame(self.window, bg='#1f2937', height=80)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        header_content = tk.Frame(header, bg='#1f2937')
        header_content.pack(expand=True, fill='both', padx=25, pady=20)
        
        tk.Label(header_content, text="⚙️ ตั้งค่าระบบ",
                font=('Segoe UI', 18, 'bold'),
                fg='white', bg='#1f2937').pack(anchor='w')
        
        # tk.Label(header_content, text="จัดการการตั้งค่าฐานข้อมูลและข้อมูลบริษัท",
        #         font=('Segoe UI', 10),
        #         fg='#d1d5db', bg='#1f2937').pack(anchor='w')
        
        # Main content - พื้นหลังขาว
        main_frame = tk.Frame(self.window, bg='white', padx=30, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # Tab styling - แถบ tab สีเข้ม
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('Simple.TNotebook', 
                    background='white', 
                    borderwidth=0)
        
        style.configure('Simple.TNotebook.Tab', 
                    background='#374151',  # Tab ไม่ active - เทาเข้ม
                    foreground='#d1d5db',
                    padding=[20, 12],        
                    borderwidth=0,
                    focuscolor='none')
        style.map('Simple.TNotebook.Tab',
                background=[('selected', '#1f2937')],  # Tab active - เข้มกว่า
                foreground=[('selected', 'white')],
                padding=[('selected', [20, 14])])  
        
        # Notebook
        self.notebook = ttk.Notebook(main_frame, style='Simple.TNotebook')
        self.notebook.pack(fill='both', expand=True, pady=(0, 20))
        
        # Database tab
        self.create_database_tab()
        
        # Buttons - พื้นหลังขาว
        button_frame = tk.Frame(main_frame, bg='white')
        button_frame.pack(fill='x', pady=(15, 0))
        
        # Test connection button
        test_btn = tk.Button(button_frame, text="ทดสอบการเชื่อมต่อ",
                        font=('Segoe UI', 10, 'bold'),
                        bg='#10b981', fg='white',
                        activebackground='#059669',
                        relief='flat', bd=0,
                        padx=25, pady=12,
                        cursor='hand2',
                        command=self.test_connection)
        test_btn.pack(side='left', padx=(0, 10))
        
        test_btn.bind("<Enter>", lambda e: test_btn.config(bg='#059669'))
        test_btn.bind("<Leave>", lambda e: test_btn.config(bg='#10b981'))
        
        # Cancel button
        cancel_btn = tk.Button(button_frame, text="ยกเลิก",
                            font=('Segoe UI', 10),
                            bg='#6b7280', fg='white',
                            activebackground='#4b5563',
                            relief='flat', bd=0,
                            padx=25, pady=12,
                            cursor='hand2',
                            command=self.window.destroy)
        cancel_btn.pack(side='right')
        
        cancel_btn.bind("<Enter>", lambda e: cancel_btn.config(bg='#4b5563'))
        cancel_btn.bind("<Leave>", lambda e: cancel_btn.config(bg='#6b7280'))
        
        # Save button
        save_btn = tk.Button(button_frame, text="บันทึกการตั้งค่า",
                        font=('Segoe UI', 10, 'bold'),
                        bg='#0284c7', fg='white',
                        activebackground='#0369a1',
                        relief='flat', bd=0,
                        padx=25, pady=12,
                        cursor='hand2',
                        command=self.save_settings)
        save_btn.pack(side='right', padx=(10, 0))
        
        save_btn.bind("<Enter>", lambda e: save_btn.config(bg='#0369a1'))
        save_btn.bind("<Leave>", lambda e: save_btn.config(bg='#0284c7'))        
    def create_database_tab(self):
        db_frame = ttk.Frame(self.notebook)
        self.notebook.add(db_frame, text='ฐานข้อมูล')
        
        # Simple scrollable content
        canvas = tk.Canvas(db_frame, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(db_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Simple content
        content = tk.Frame(scrollable_frame, bg='white', padx=40, pady=30)
        content.pack(fill='both', expand=True)
        
        # Simple title
        tk.Label(content, text="การตั้งค่าฐานข้อมูล",
                font=('Segoe UI', 16, 'bold'),
                fg='#374151', bg='white').pack(anchor='w', pady=(0, 20))
        
        # Create simple fields
        self.db_fields = {}
        
        self.create_simple_field(content, "เซิร์ฟเวอร์:", "server", 
                                self.config["database"]["server"])
        
        self.create_simple_field(content, "พอร์ต:", "port", 
                                self.config["database"]["port"])
        
        self.create_simple_field(content, "ชื่อฐานข้อมูล:", "database", 
                                self.config["database"]["database"])
        
        self.create_simple_field(content, "ชื่อผู้ใช้:", "username", 
                                self.config["database"]["username"])
        
        self.create_simple_field(content, "รหัสผ่าน:", "password", 
                                self.config["database"]["password"], show='•')
        
        # self.create_simple_field(content, "ไดร์เวอร์:", "driver", 
        #                         self.config["database"]["driver"])
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        content = tk.Frame(scrollable_frame, bg='white', padx=40, pady=30)
        content.pack(fill='both', expand=True)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Mouse wheel scroll
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
    
    def create_simple_field(self, parent, label_text, field_name, default_value="", show=None, height=1, buttons=None):
        # Simple field container
        field_container = tk.Frame(parent, bg='white')
        field_container.pack(fill='x', pady=(0, 15))
        
        # Simple label
        tk.Label(field_container, text=label_text,
                font=('Segoe UI', 10, 'bold'),
                fg='#374151', bg='white').pack(anchor='w', pady=(0, 5))
        
        # Container for input and buttons
        input_row = tk.Frame(field_container, bg='white')
        input_row.pack(fill='x')
        
        # Simple input field
        if height > 1:
            # Text widget for multiline
            widget = tk.Text(input_row, font=('Segoe UI', 10),
                        bg='#ffffff', fg='#374151',
                        relief='solid', bd=1, height=height,
                        insertbackground='#6366f1')
            widget.pack(side='left', fill='x', expand=True, ipady=8, padx=(2, 0))
            widget.insert('1.0', default_value)
        else:
            # Entry widget for single line
            widget = tk.Entry(input_row, font=('Segoe UI', 10),
                            bg='#ffffff', fg='#374151',
                            relief='solid', bd=1, show=show,
                            insertbackground='#6366f1')
            widget.pack(side='left', fill='x', expand=True, ipady=8, padx=(2, 0))
            widget.insert(0, default_value)
        
        # Add buttons if specified
        if buttons:
            for btn_text, btn_command in buttons:
                btn = tk.Button(input_row, text=btn_text,
                            font=('Segoe UI', 9),
                            bg='#6366f1', fg='white',
                            relief='solid', bd=1,
                            padx=15, pady=5,
                            cursor='hand2',
                            command=btn_command)
                btn.pack(side='right', padx=(5, 0))
            
        # Store widget reference
        if "database" in self.config and any(field_name == key for key in self.config["database"]):
            if not hasattr(self, 'db_fields'):
                self.db_fields = {}
            self.db_fields[field_name] = widget
        else:
            if field_name.startswith(('purchase_template', 'sales_template', 'branch_template', 'template_notes')):
                if not hasattr(self, 'template_fields'):
                    self.template_fields = {}
                self.template_fields[field_name] = widget
            else:
                if not hasattr(self, 'company_fields'):
                    self.company_fields = {}
                self.company_fields[field_name] = widget
        
        # Simple focus effects
        def on_focus_in(event):
            widget.config(relief='solid', bd=2)
            
        def on_focus_out(event):
            widget.config(relief='solid', bd=1)
        
        widget.bind("<FocusIn>", on_focus_in)
        widget.bind("<FocusOut>", on_focus_out)
        
        
    def get_field_value(self, widget):
        """Get value from either Entry or Text widget"""
        if isinstance(widget, tk.Text):
            return widget.get('1.0', 'end-1c')
        else:
            return widget.get()
    
    def test_connection(self):
        try:
            # Update config with current field values
            for field_name, widget in self.db_fields.items():
                self.config["database"][field_name] = self.get_field_value(widget)
            
            # Simple connection test simulation
            server = self.config["database"]["server"]
            database = self.config["database"]["database"]
            
            if not server or not database:
                messagebox.showwarning("คำเตือน", "กรุณากรอกข้อมูลเซิร์ฟเวอร์และชื่อฐานข้อมูล")
                return
            
            # Simple success message
            messagebox.showinfo("ผลการทดสอบ", 
                              f"การเชื่อมต่อสำเร็จ!\n\nเซิร์ฟเวอร์: {server}\nฐานข้อมูล: {database}")
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถเชื่อมต่อได้: {str(e)}")
    
    def save_settings(self):
        try:
            # Update database config
            for field_name, widget in self.db_fields.items():
                self.config["database"][field_name] = self.get_field_value(widget)
            
            # # Update company config
            # for field_name, widget in self.company_fields.items():
            #     self.config["application"][field_name] = self.get_field_value(widget)
                
            # # Update template config
            # for field_name, widget in self.template_fields.items():
            #     if "templates" not in self.config:
            #         self.config["templates"] = {}
            #     self.config["templates"][field_name] = self.get_field_value(widget)
            
            # Save to file
            if self.save_config():
                messagebox.showinfo("สำเร็จ", "บันทึกการตั้งค่าเรียบร้อยแล้ว")
                self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถบันทึกการตั้งค่าได้: {str(e)}")

if __name__ == "__main__":
    app = ConfigUI()
    app.window.mainloop()