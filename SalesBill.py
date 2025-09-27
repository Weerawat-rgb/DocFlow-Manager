import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from SalesBill_database import SalesBillDatabase

class SalesBillUI:
    def __init__(self, parent, user_data):
        self.parent = parent
        self.user_data = user_data
        self.window = tk.Toplevel(parent)
        
        # Initialize variables first
        self.current_step = 1
        self.selected_customer = None
        self.selected_invoices = set()  
        self.selected_invoice_numbers = set() 
        
        self.setup_window()
        
        # Initialize database
        try:
            self.db = SalesBillDatabase()
            if not self.db.test_connection():
                messagebox.showerror("ข้อผิดพลาด", "ไม่สามารถเชื่อมต่อฐานข้อมูลได้")
                self.window.destroy()
                return
            
            # ทดสอบข้อมูล
            print("🔍 ทดสอบข้อมูลในฐานข้อมูล...")
            self.db.test_data()
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ข้อผิดพลาดฐานข้อมูล: {str(e)}")
            self.window.destroy()
            return
        
        self.show_step1()
        
    def setup_window(self):
        self.window.title("ระบบใบวางบิลขาย - DocFlow Manager")
        self.window.geometry("1400x900")
        self.window.configure(bg='#f8fafc')
        self.center_window()
        self.create_header()
        
    def center_window(self):
        self.window.update_idletasks()
        width = 1400
        height = 900
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_header(self):
        header = tk.Frame(self.window, bg='#1f2937', height=80)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        header_content = tk.Frame(header, bg='#1f2937')
        header_content.pack(fill='both', expand=True, padx=30, pady=15)
        
        # Left - Title
        left_frame = tk.Frame(header_content, bg='#1f2937')
        left_frame.pack(side='left', fill='y')
        
        tk.Label(left_frame, text="🛒 ระบบใบวางบิลขาย", 
                font=('Segoe UI', 18, 'bold'), 
                fg='white', bg='#1f2937').pack(anchor='w')
        
        tk.Label(left_frame, text="จัดการใบวางบิลการขายสินค้า", 
                font=('Segoe UI', 9), 
                fg='#d1d5db', bg='#1f2937').pack(anchor='w')
        
        # Right - User info & Close button
        right_frame = tk.Frame(header_content, bg='#1f2937')
        right_frame.pack(side='right', fill='y')
        
        tk.Label(right_frame, text=f"👤 {self.user_data['username']}", 
               font=('Segoe UI', 11), 
               fg='white', bg='#1f2937').pack(anchor='e')
        
        close_btn = tk.Button(right_frame, text="✕ ปิดหน้าต่าง",
                             font=('Segoe UI', 9),
                             bg='#ef4444', fg='white',
                             border=0, padx=15, pady=6,
                             cursor='hand2',
                             command=self.close_window)
        close_btn.pack(anchor='e', pady=(5, 0))
        
        self.create_step_indicator()
    
    def create_step_indicator(self):
        # Clear existing step indicator
        for widget in self.window.winfo_children():
            if hasattr(widget, '_step_indicator'):
                widget.destroy()
        
        step_frame = tk.Frame(self.window, bg='white', height=60)
        step_frame.pack(fill='x', padx=30, pady=(20, 0))
        step_frame.pack_propagate(False)
        step_frame._step_indicator = True
        
        steps_container = tk.Frame(step_frame, bg='white')
        steps_container.pack(expand=True, pady=15)
        
        steps = [
            {"num": 1, "text": "สร้างเอกสาร"},
            {"num": 2, "text": "ค้นหาลูกค้า"},
            {"num": 3, "text": "เลือกใบแจ้งหนี้"},
            {"num": 4, "text": "ตรวจสอบและยืนยัน"}
        ]
        
        for i, step in enumerate(steps):
            step_item = tk.Frame(steps_container, bg='white')
            step_item.pack(side='left', padx=20)
            
            # Circle
            if step["num"] <= self.current_step:
                circle_bg = '#10b981'
                circle_fg = 'white'
                text_fg = '#1f2937'
            else:
                circle_bg = '#e5e7eb'
                circle_fg = '#9ca3af'
                text_fg = '#9ca3af'
            
            circle = tk.Frame(step_item, bg=circle_bg, width=35, height=35)
            circle.pack()
            circle.pack_propagate(False)
            
            tk.Label(circle, text=str(step["num"]), 
                    font=('Segoe UI', 12, 'bold'),
                    fg=circle_fg, bg=circle_bg).pack(expand=True)
            
            tk.Label(step_item, text=step["text"],
                    font=('Segoe UI', 9),
                    fg=text_fg, bg='white').pack(pady=(5, 0))
            
            # Arrow
            if i < len(steps) - 1:
                tk.Label(steps_container, text="→",
                        font=('Segoe UI', 16),
                        fg='#d1d5db', bg='white').pack(side='left', padx=(10, 0))
                
    def sync_selected_invoices(self):
        """ซิงค์ข้อมูลการเลือกให้เป็นปัจจุบัน"""
        if not hasattr(self, 'selected_invoice_numbers'):
            self.selected_invoice_numbers = set()
        else:
            # ล้างข้อมูลเก่า
            self.selected_invoice_numbers.clear()
        
        # เก็บข้อมูลใหม่จากที่เลือกปัจจุบัน
        for item_id in self.selected_invoices:
            if item_id in self.invoice_items:
                invoice_number = self.invoice_items[item_id].get('InvoiceNumber', '')
                if invoice_number:
                    self.selected_invoice_numbers.add(invoice_number)
        
        print(f"Synced selected invoices: {self.selected_invoice_numbers}")
    
    def clear_content(self):
        for widget in self.window.winfo_children():
            if hasattr(widget, '_content'):
                widget.destroy()
    
    def show_step1(self):
        self.current_step = 1
        self.create_step_indicator()
        self.clear_content()
        
        content = tk.Frame(self.window, bg='#f8fafc')
        content.pack(fill='both', expand=True, padx=30, pady=20)
        content._content = True
        
        card = tk.Frame(content, bg='white', padx=40, pady=40)
        card.pack(expand=True, fill='both')
        
        tk.Label(card, text="🚀 เริ่มสร้างใบวางบิลขาย",
                font=('Segoe UI', 20, 'bold'),
                fg='#1f2937', bg='white').pack(pady=(0, 10))
        
        tk.Label(card, text="คลิกปุ่มด้านล่างเพื่อเริ่มกระบวนการสร้างใบวางบิลขายใหม่",
                font=('Segoe UI', 12),
                fg='#6b7280', bg='white').pack(pady=(0, 40))
        
        # Icon
        icon_frame = tk.Frame(card, bg='#10b981', width=120, height=120)
        icon_frame.pack(pady=(0, 40))
        icon_frame.pack_propagate(False)
        
        tk.Label(icon_frame, text="📄",
                font=('Segoe UI Emoji', 48),
                fg='white', bg='#10b981').pack(expand=True)
        
        # Start button
        start_btn = tk.Button(card, text="🛒 สร้างใบวางบิลขาย",
                             font=('Segoe UI', 14, 'bold'),
                             bg='#10b981', fg='white',
                             activebackground='#059669',
                             border=0, padx=40, pady=15,
                             cursor='hand2',
                             command=self.show_step2)
        start_btn.pack()
        
        start_btn.bind("<Enter>", lambda e: start_btn.config(bg='#059669'))
        start_btn.bind("<Leave>", lambda e: start_btn.config(bg='#10b981'))
    
    def show_step2(self):
        self.current_step = 2
        self.create_step_indicator()
        self.clear_content()
        
        content = tk.Frame(self.window, bg='#f8fafc')
        content.pack(fill='both', expand=True, padx=30, pady=20)
        content._content = True
        
        card = tk.Frame(content, bg='white', padx=40, pady=40)
        card.pack(expand=True, fill='both')
        
        tk.Label(card, text="🔍 ค้นหาลูกค้า",
                font=('Segoe UI', 20, 'bold'),
                fg='#1f2937', bg='white').pack(pady=(0, 10))
        
        tk.Label(card, text="ป้อนชื่อบริษัทหรือเลขประจำตัวผู้เสียภาษีเพื่อค้นหาลูกค้า",
                font=('Segoe UI', 12),
                fg='#6b7280', bg='white').pack(pady=(0, 30))
        
        # Search section
        search_frame = tk.Frame(card, bg='white')
        search_frame.pack(fill='x', pady=(0, 30))
        
        search_container = tk.Frame(search_frame, bg='#f9fafb', relief='solid', bd=1)
        search_container.pack(fill='x')
        
        self.search_entry = tk.Entry(search_container, font=('Segoe UI', 12),
                                    bg='#f9fafb', fg='#374151',
                                    border=0, insertbackground='#10b981')
        self.search_entry.pack(side='left', fill='x', expand=True, padx=15, pady=12)
        self.search_entry.bind('<KeyRelease>', self.search_customers)
        self.search_entry.bind('<Return>', self.search_customers)
        
        search_btn = tk.Button(search_container, text="🔍",
                              font=('Segoe UI', 12),
                              bg='#10b981', fg='white',
                              border=0, padx=15,
                              cursor='hand2',
                              command=self.search_customers)
        search_btn.pack(side='right', fill='y')
        
        # Results frame
        self.results_frame = tk.Frame(card, bg='white')
        self.results_frame.pack(fill='both', expand=True)
        
        # Load initial customers
        self.search_customers()
    
    def search_customers(self, event=None):
        search_term = self.search_entry.get().strip()
        
        # Show loading
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        loading_label = tk.Label(self.results_frame, text="🔄 กำลังค้นหา...",
                            font=('Segoe UI', 12),
                            fg='#6b7280', bg='white')
        loading_label.pack(expand=True)
        
        # Update window to show loading
        self.window.update_idletasks()
        
        try:
            customers = self.db.search_customers(search_term)
            
            # แสดงผลตามที่ค้นหาเจอจริง ๆ
            print(f"🔍 Search term: '{search_term}' -> Found: {len(customers)} customers")
            
            self.display_customers(customers)
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถค้นหาลูกค้าได้: {str(e)}")
            self.display_customers([])
            
    def select_from_tree(self):
        """เลือกลูกค้าจากตาราง"""
        selected_item = self.customer_tree.selection()
        if not selected_item:
            messagebox.showwarning("คำเตือน", "กรุณาเลือกลูกค้าจากตาราง")
            return
        
        # Get selected data
        values = self.customer_tree.item(selected_item[0])['values']
        
        # Create customer dict
        customer = {
            'CustomerId': values[0],
            'Acct': values[1],
            'Name': values[2],
            'CustomerName': values[3],
            'CustomerAddress': values[4],
            'PhoneMobile': values[5],
            'CustomerTaxNum': values[6]
        }
        
        self.selected_customer = customer
        
        # แสดงชื่อลูกค้าที่เลือก
        customer_display_name = customer.get('CustomerName', '').strip()
        if not customer_display_name:
            customer_display_name = customer.get('Name', '').strip()
        if not customer_display_name:
            customer_display_name = f"ลูกค้า ID: {customer.get('CustomerId', 'N/A')}"
            
        messagebox.showinfo("สำเร็จ", f"เลือกลูกค้า: {customer_display_name}")
        self.show_step3()
        
    def select_customer(self, customer):
        self.selected_customer = customer
        
        # แสดงชื่อลูกค้าที่เลือก
        customer_display_name = customer.get('Name', '').strip()
        if not customer_display_name:
            customer_display_name = f"ลูกค้า ID: {customer.get('CustomerId', 'N/A')}"
            
        print(f"Selected customer: {customer_display_name}")
        self.show_step3()
        
    def display_customers(self, customers):
        # Clear results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        print(f"🔍 Display customers: แสดงผล {len(customers)} รายการ")
        
        if not customers:
            tk.Label(self.results_frame, text="ไม่พบลูกค้าที่ค้นหา",
                    font=('Segoe UI', 14),
                    fg='#6b7280', bg='white').pack(expand=True)
            return
        
        # Results title
        search_term = self.search_entry.get().strip()
        if search_term:
            title_text = f"ผลการค้นหา '{search_term}': พบ {len(customers)} รายการ"
        else:
            title_text = f"ลูกค้าทั้งหมดที่มียอดค้างชำระ: {len(customers)} รายการ"
        
        title_label = tk.Label(self.results_frame, text=title_text,
                            font=('Segoe UI', 14, 'bold'),
                            fg='#1f2937', bg='white')
        title_label.pack(anchor='w', pady=(0, 20))
        
        print(f"📋 Title label packed: {title_text}")
        
        # Container for scrollable content
        container = tk.Frame(self.results_frame, bg='white')
        container.pack(fill='both', expand=True)
        
        # Canvas and scrollbar
        canvas = tk.Canvas(container, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        # Configure scrolling
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        scrollable_frame.bind("<Configure>", on_frame_configure)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create window in canvas
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # Configure canvas scrolling
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Make canvas responsive to window width
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind('<Configure>', on_canvas_configure)
        
        print(f"📦 Canvas and scrollbar setup complete")
        
        # Create customer cards
        for i, customer in enumerate(customers):
            print(f"🃏 Creating card {i+1} for customer ID: {customer.get('CustomerId')}")
            try:
                self.create_customer_card(scrollable_frame, customer)
                print(f"✅ Card {i+1} created successfully")
            except Exception as e:
                print(f"❌ Error creating card {i+1}: {str(e)}")
        
        # Force update to ensure everything is drawn
        self.window.update_idletasks()
        
        print(f"🎯 Display complete: {len(customers)} cards should be visible")
        
        # Debug: Check if scrollable_frame has children
        children_count = len(scrollable_frame.winfo_children())
        print(f"🔍 Scrollable frame has {children_count} children")  
              
    def create_customer_card(self, parent, customer):
        print(f"🔨 Creating card for customer: {customer}")
        
        # Simple card container
        card = tk.Frame(parent, bg='#f8fafc', relief='ridge', bd=2, padx=15, pady=10)
        card.pack(fill='x', pady=5)
        
        # Customer info
        customer_id = customer.get('CustomerId', 'N/A')
        customer_name = customer.get('Name', '').strip()
        acct = customer.get('Acct', '').strip()
        
        # Display name
        if customer_name:
            display_name = customer_name
        else:
            display_name = f"ลูกค้า ID: {customer_id}"
        
        # Name label
        name_label = tk.Label(card, text=display_name,
                            font=('Segoe UI', 12, 'bold'),
                            fg='#1f2937', bg='#f8fafc')
        name_label.pack(anchor='w')
        
        # Details
        details = f"รหัสลูกค้า: {customer_id}"
        if acct:
            details += f" | บัญชี: {acct}"
        
        details_label = tk.Label(card, text=details,
                            font=('Segoe UI', 9),
                            fg='#6b7280', bg='#f8fafc')
        details_label.pack(anchor='w', pady=(2, 10))
        
        # Select button
        select_btn = tk.Button(card, text="เลือกลูกค้า",
                            font=('Segoe UI', 10, 'bold'),
                            bg='#10b981', fg='white',
                            padx=20, pady=5,
                            command=lambda: self.select_customer(customer))
        select_btn.pack(anchor='w')
        
        print(f"✅ Card created and packed for customer {customer_id}")        
        
    def load_customer_invoices_for_display(self):
        """โหลดข้อมูลจากฐานข้อมูลผ่าน database class"""
        try:
            search_term = self.search_entry.get().strip()
            invoices_data = self.db.get_customer_invoices_for_display(search_term)
            
            # Clear existing data
            for item in self.customer_tree.get_children():
                self.customer_tree.delete(item)
            
            # Insert data
            for invoice in invoices_data:
                values = (
                    invoice.get('CustomerId', ''),
                    invoice.get('Acct', ''),
                    invoice.get('Name', ''),
                    invoice.get('CustomerName', ''),
                    invoice.get('CustomerAddress', ''),
                    invoice.get('PhoneMobile', ''),
                    invoice.get('CustomerTaxNum', ''),
                    invoice.get('InvoiceNumber', ''),
                    invoice.get('InvoiceDate', ''),
                    invoice.get('MaxDueDate', ''),
                    invoice.get('DueDate', ''),
                    invoice.get('Total', ''),
                    invoice.get('PaidAmount', ''),
                    invoice.get('UnpaidAmount', '')
                )
                self.customer_tree.insert('', 'end', values=values)
            
            print(f"✅ แสดงข้อมูลในตาราง {len(invoices_data)} รายการ")
            
        except Exception as e:
            print(f"❌ ข้อผิดพลาดในการโหลดข้อมูล: {str(e)}")
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถโหลดข้อมูลได้: {str(e)}")

    def on_customer_select(self, event):
        """เมื่อ double-click ในตาราง"""
        self.select_from_tree()

    # def select_from_tree(self):
        """เลือกลูกค้าจากตาราง"""
        selected_item = self.customer_tree.selection()
        if not selected_item:
            messagebox.showwarning("คำเตือน", "กรุณาเลือกลูกค้าจากตาราง")
            return
        
        # Get selected data
        values = self.customer_tree.item(selected_item[0])['values']
        
        # Create customer dict
        customer = {
            'CustomerId': values[0],
            'Acct': values[1],
            'Name': values[2],
            'CustomerName': values[3],
            'CustomerAddress': values[4],
            'PhoneMobile': values[5],
            'CustomerTaxNum': values[6]
        }
        
        self.selected_customer = customer
        
        # แสดงชื่อลูกค้าที่เลือก
        customer_display_name = customer.get('CustomerName', '').strip()
        if not customer_display_name:
            customer_display_name = customer.get('Name', '').strip()
        if not customer_display_name:
            customer_display_name = f"ลูกค้า ID: {customer.get('CustomerId', 'N/A')}"
            
        messagebox.showinfo("สำเร็จ", f"เลือกลูกค้า: {customer_display_name}")
        self.show_step3()
    
    def show_step3(self):
        self.current_step = 3
        self.create_step_indicator()
        self.clear_content()
        
        content = tk.Frame(self.window, bg='#f8fafc')
        content.pack(fill='both', expand=True, padx=30, pady=20)
        content._content = True
        
        card = tk.Frame(content, bg='white', padx=40, pady=40)
        card.pack(expand=True, fill='both')
        
        # Title
        title_frame = tk.Frame(card, bg='white')
        title_frame.pack(fill='x', pady=(0, 30))
        
        customer_name = self.selected_customer.get('Name', '').strip()
        if not customer_name:
            customer_name = f"ลูกค้า ID: {self.selected_customer.get('CustomerId', 'N/A')}"
        
        tk.Label(title_frame, text=f"ใบแจ้งหนี้ของ {customer_name}",
                font=('Segoe UI', 18, 'bold'),
                fg='#1f2937', bg='white').pack(anchor='w')
        
        tk.Label(title_frame, text="เลือกใบแจ้งหนี้ที่ต้องการรวมในใบวางบิล",
                font=('Segoe UI', 12),
                fg='#6b7280', bg='white').pack(anchor='w', pady=(5, 0))
        
        # Debug: แสดงรายการที่เลือกไว้
        if hasattr(self, 'selected_invoice_numbers'):
            print(f"Returning to step 3 with selected: {self.selected_invoice_numbers}")
        else:
            print("No selected_invoice_numbers found")
            self.selected_invoice_numbers = set()
        
        # Load invoices for this customer
        self.load_customer_invoices()
                
    def load_customer_invoices(self):
        try:
            customer_id = self.selected_customer.get('CustomerId')
            print(f"Loading invoices for customer ID: {customer_id}")
            
            invoices = self.db.get_customer_invoices(customer_id)
            print(f"Found {len(invoices)} invoices")
            
            self.display_invoices(invoices)
        except Exception as e:
            print(f"Error loading invoices: {str(e)}")
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถโหลดใบแจ้งหนี้ได้: {str(e)}")
                
    def display_invoices(self, invoices):
        # Find the card widget
        card = None
        for widget in self.window.winfo_children():
            if hasattr(widget, '_content'):
                card = widget.winfo_children()[0]
                break
        
        if not invoices:
            tk.Label(card, text="ไม่พบใบแจ้งหนี้ที่ค้างชำระสำหรับลูกค้ารายนี้",
                    font=('Segoe UI', 14),
                    fg='#6b7280', bg='white').pack(expand=True)
            return
        
        # Create treeview for invoices
        tree_frame = tk.Frame(card, bg='white')
        tree_frame.pack(fill='both', expand=True, pady=(0, 20))
        
        # Create Treeview with custom style
        style = ttk.Style()
        style.configure("Custom.Treeview", 
                    font=('Segoe UI', 11),
                    rowheight=30)
        style.configure("Custom.Treeview.Heading", 
                    font=('Segoe UI', 12, 'bold'))
        
        columns = ('Select', 'InvoiceNumber', 'InvoiceDate', 'MaxDueDate', 'DueDate', 'UnpaidAmount')
        
        self.invoice_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', 
                                        height=10, style="Custom.Treeview")
        
        # Define headings and column widths
        column_config = {
            'Select': {'text': 'เลือกรายการ', 'width': 30, 'anchor': 'center'},
            'InvoiceNumber': {'text': 'เลขที่ใบแจ้งหนี้', 'width': 150, 'anchor': 'center'},
            'InvoiceDate': {'text': 'วันที่ออกใบแจ้งหนี้', 'width': 120, 'anchor': 'center'},
            'MaxDueDate': {'text': 'ระยะเวลาชำระ (วัน)', 'width': 100, 'anchor': 'center'},
            'DueDate': {'text': 'วันครบกำหนด', 'width': 120, 'anchor': 'center'},
            'UnpaidAmount': {'text': 'ยอดค้างชำระ (บาท)', 'width': 150, 'anchor': 'center'}
        }
        
        # Configure columns with center alignment
        for col in columns:
            self.invoice_tree.heading(col, text=column_config[col]['text'], anchor='center')
            self.invoice_tree.column(col, 
                                width=column_config[col]['width'], 
                                minwidth=30 if col == 'Select' else 50,
                                anchor=column_config[col]['anchor'])
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.invoice_tree.yview)
        self.invoice_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        self.invoice_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Insert data and track selections  
        self.invoice_items = {}
        
        # รีเซ็ต selected_invoices เป็น set ใหม่
        self.selected_invoices = set()
        
        # ตรวจสอบ selected_invoice_numbers
        if not hasattr(self, 'selected_invoice_numbers'):
            self.selected_invoice_numbers = set()
        
        print(f"Displaying invoices with pre-selected: {self.selected_invoice_numbers}")
        
        for invoice in invoices:
            # Format dates และข้อมูลอื่น ๆ (เหมือนเดิม)
            invoice_date = invoice.get('InvoiceDate', '')
            if len(invoice_date) > 10:
                invoice_date = invoice_date[:10]
                
            due_date = invoice.get('DueDate', '')
            if len(due_date) > 10:
                due_date = due_date[:10]
            
            max_due_date = invoice.get('MaxDueDate', '0')
            
            unpaid_amount = invoice.get('UnpaidAmount', '0')
            if isinstance(unpaid_amount, str) and ',' in unpaid_amount:
                formatted_amount = unpaid_amount
            else:
                try:
                    amount_float = float(str(unpaid_amount).replace(',', ''))
                    formatted_amount = f"{amount_float:,.2f}"
                except:
                    formatted_amount = str(unpaid_amount)
            
            # ตรวจสอบการเลือก
            invoice_number = invoice.get('InvoiceNumber', '')
            is_selected = invoice_number in self.selected_invoice_numbers
            checkbox = '✓' if is_selected else ''
            
            item_id = self.invoice_tree.insert('', 'end', values=(
                checkbox,
                invoice_number,
                invoice_date,
                max_due_date,
                due_date,
                formatted_amount
            ))
            
            self.invoice_items[item_id] = invoice
            
            # เพิ่มเข้า selected_invoices ถ้าถูกเลือกไว้
            if is_selected:
                self.selected_invoices.add(item_id)
                print(f"Restored selection for: {invoice_number}")
                    
        # Bind click event
        self.invoice_tree.bind('<Button-1>', self.on_invoice_click)
        self.invoice_tree.bind('<Double-Button-1>', self.on_invoice_click)
        
        # Control buttons (เหมือนเดิม)
        control_frame = tk.Frame(card, bg='white')
        control_frame.pack(fill='x', pady=(10, 0))
        
        left_buttons = tk.Frame(control_frame, bg='white')
        left_buttons.pack(side='left')
        
        select_all_btn = tk.Button(left_buttons, text="เลือกทั้งหมด",
                                font=('Segoe UI', 10),
                                bg='#3b82f6', fg='white',
                                padx=15, pady=8,
                                command=self.select_all_invoices)
        select_all_btn.pack(side='left', padx=(0, 10))
        
        clear_all_btn = tk.Button(left_buttons, text="ยกเลิกทั้งหมด",
                                font=('Segoe UI', 10),
                                bg='#ef4444', fg='white',
                                padx=15, pady=8,
                                command=self.clear_all_invoices)
        clear_all_btn.pack(side='left')
        
        info_frame = tk.Frame(control_frame, bg='white')
        info_frame.pack(side='right')
        
        self.selected_count_label = tk.Label(info_frame, 
                                        text="เลือกแล้ว: 0 รายการ",
                                        font=('Segoe UI', 11, 'bold'),
                                        fg='#10b981', bg='white')
        self.selected_count_label.pack(side='top', anchor='e')
        
        self.selected_amount_label = tk.Label(info_frame, 
                                            text="ยอดรวม: 0.00 บาท",
                                            font=('Segoe UI', 11, 'bold'),
                                            fg='#dc2626', bg='white')
        self.selected_amount_label.pack(side='top', anchor='e')
        
        action_frame = tk.Frame(card, bg='white')
        action_frame.pack(fill='x', pady=(20, 0))
        
        back_btn = tk.Button(action_frame, text="ย้อนกลับ",
                            font=('Segoe UI', 11),
                            bg='#6b7280', fg='white',
                            padx=20, pady=10,
                            command=self.show_step2)
        back_btn.pack(side='left')
        
        self.continue_btn = tk.Button(action_frame, text="ดำเนินการต่อ",
                                    font=('Segoe UI', 11, 'bold'),
                                    bg='#10b981', fg='white',
                                    padx=20, pady=10,
                                    state='disabled',
                                    command=self.show_step4)
        self.continue_btn.pack(side='right')
        
        # อัพเดทการแสดงผลตามที่เลือกไว้
        self.update_selected_count()

    def get_selected_invoice_numbers(self):
        """ดึงรายการเลขที่ใบแจ้งหนี้ที่เลือกไว้"""
        if not hasattr(self, 'selected_invoice_numbers'):
            self.selected_invoice_numbers = set()
        return self.selected_invoice_numbers

    def on_invoice_click(self, event):
        item_id = self.invoice_tree.identify_row(event.y)
        if not item_id or item_id not in self.invoice_items:
            return
        
        values = list(self.invoice_tree.item(item_id)['values'])
        invoice_number = values[1]  # InvoiceNumber อยู่ที่ index 1
        
        # ตรวจสอบสถานะปัจจุบัน
        is_currently_selected = item_id in self.selected_invoices
        
        # Toggle selection
        if is_currently_selected:
            # ยกเลิกการเลือก
            self.selected_invoices.remove(item_id)
            values[0] = ''
            # ลบจาก selected_invoice_numbers
            if hasattr(self, 'selected_invoice_numbers'):
                self.selected_invoice_numbers.discard(invoice_number)
        else:
            # เลือก
            self.selected_invoices.add(item_id)
            values[0] = '✓'
            # เพิ่มเข้า selected_invoice_numbers
            if not hasattr(self, 'selected_invoice_numbers'):
                self.selected_invoice_numbers = set()
            self.selected_invoice_numbers.add(invoice_number)
        
        # อัพเดทแสดงผลทันที
        self.invoice_tree.item(item_id, values=values)
        
        # Debug
        print(f"Clicked {invoice_number}: selected={not is_currently_selected}")
        print(f"Current selected_invoice_numbers: {self.selected_invoice_numbers}")
        
        self.update_selected_count()
        
    def select_all_invoices(self):
        if not hasattr(self, 'selected_invoice_numbers'):
            self.selected_invoice_numbers = set()
            
        for item_id in self.invoice_items:
            self.selected_invoices.add(item_id)
            values = list(self.invoice_tree.item(item_id)['values'])
            values[0] = '✓'
            self.invoice_tree.item(item_id, values=values)
            # เพิ่มเลขที่ใบแจ้งหนี้เข้า set
            invoice_number = values[1]
            self.selected_invoice_numbers.add(invoice_number)
        self.update_selected_count()

    def clear_all_invoices(self):
        self.selected_invoices.clear()
        if hasattr(self, 'selected_invoice_numbers'):
            self.selected_invoice_numbers.clear()
            
        for item_id in self.invoice_items:
            values = list(self.invoice_tree.item(item_id)['values'])
            values[0] = ''
            self.invoice_tree.item(item_id, values=values)
        self.update_selected_count()
        
    def update_selected_count(self):
        # ตรวจสอบให้แน่ใจว่าเป็น set
        if not isinstance(self.selected_invoices, set):
            self.selected_invoices = set(self.selected_invoices) if self.selected_invoices else set()
        
        selected_count = len(self.selected_invoices)
        
        # Calculate total amount
        total_amount = 0.0
        for item_id in self.selected_invoices:
            invoice = self.invoice_items[item_id]
            try:
                amount_str = str(invoice.get('UnpaidAmount', '0')).replace(',', '')
                total_amount += float(amount_str)
            except:
                pass
        
        # Update labels
        self.selected_count_label.config(text=f"เลือกแล้ว: {selected_count} รายการ")
        self.selected_amount_label.config(text=f"ยอดรวม: {total_amount:,.2f} บาท")
        
        # Enable/disable continue button
        if selected_count > 0:
            self.continue_btn.config(state='normal', bg='#10b981')
        else:
            self.continue_btn.config(state='disabled', bg='#9ca3af')
                                                
    def create_invoice_card(self, parent, invoice):
        card_container = tk.Frame(parent, bg='white')
        card_container.pack(fill='x', pady=(0, 15))
        
        # Shadow
        shadow = tk.Frame(card_container, bg='#e5e7eb')
        shadow.pack(fill='x', padx=(2, 0), pady=(2, 0))
        
        # Main card
        card = tk.Frame(card_container, bg='#f9fafb', relief='solid', bd=1)
        card.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Content
        content_frame = tk.Frame(card, bg='#f9fafb', padx=20, pady=15)
        content_frame.pack(fill='both', expand=True)
        
        # Header with checkbox
        header_frame = tk.Frame(content_frame, bg='#f9fafb')
        header_frame.pack(fill='x', pady=(0, 10))
        
        # Checkbox
        var = tk.BooleanVar()
        self.invoice_vars[invoice['InvoiceNumber']] = var
        
        checkbox = tk.Checkbutton(header_frame, variable=var,
                                 font=('Segoe UI', 12),
                                 bg='#f9fafb', fg='#1f2937',
                                 activebackground='#f9fafb',
                                 command=self.update_selected_invoices)
        checkbox.pack(side='left', padx=(0, 10))
        
        # Invoice info
        info_frame = tk.Frame(header_frame, bg='#f9fafb')
        info_frame.pack(side='left', fill='x', expand=True)
        
        tk.Label(info_frame, text=f"📄 {invoice['InvoiceNumber']}",
                font=('Segoe UI', 13, 'bold'),
                fg='#1f2937', bg='#f9fafb').pack(anchor='w')
        
        tk.Label(info_frame, text=f"📅 วันที่: {invoice['InvoiceDate']} | 📅 ครบกำหนด: {invoice['DueDate']}",
                font=('Segoe UI', 9),
                fg='#6b7280', bg='#f9fafb').pack(anchor='w')
        
        # Amount info
        amount_frame = tk.Frame(header_frame, bg='#f9fafb')
        amount_frame.pack(side='right')
        
        tk.Label(amount_frame, text=f"💰 ยอดค้างชำระ",
                font=('Segoe UI', 9),
                fg='#6b7280', bg='#f9fafb').pack(anchor='e')
        
        tk.Label(amount_frame, text=f"฿ {invoice['UnpaidAmount']:,.2f}",
                font=('Segoe UI', 12, 'bold'),
                fg='#ef4444', bg='#f9fafb').pack(anchor='e')
        
        # Details
        details_frame = tk.Frame(content_frame, bg='#f9fafb')
        details_frame.pack(fill='x')
        
        tk.Label(details_frame, text=f"💵 ยอดรวม: ฿ {invoice['Total']:,.2f} | 💸 ชำระแล้ว: ฿ {invoice['PaidAmount']:,.2f}",
                font=('Segoe UI', 9),
                fg='#6b7280', bg='#f9fafb').pack(anchor='w')
    
    def update_selected_invoices(self):
        self.selected_invoices = [
            invoice_no for invoice_no, var in self.invoice_vars.items() 
            if var.get()
        ]
        
        if hasattr(self, 'selected_count_label'):
            self.selected_count_label.config(text=f"เลือกแล้ว: {len(self.selected_invoices)} รายการ")
        
        self.update_continue_button()
  
    
    def update_continue_button(self):
        if hasattr(self, 'continue_btn'):
            if self.selected_invoices:
                self.continue_btn.config(state='normal', bg='#10b981')
            else:
                self.continue_btn.config(state='disabled', bg='#9ca3af')
    
    def show_step4(self):
        self.current_step = 4
        self.create_step_indicator()
        
        # อัพเดท selected_invoice_numbers ให้เป็นปัจจุบัน
        self.sync_selected_invoices()
        self.clear_content()
        
        # บันทึกรายการที่เลือกไว้ก่อนไป step 4
        self.save_selected_invoices()
        
        content = tk.Frame(self.window, bg='#f8fafc')
        content.pack(fill='both', expand=True, padx=30, pady=20)
        content._content = True
        
        card = tk.Frame(content, bg='white', padx=40, pady=40)
        card.pack(expand=True, fill='both')
        
        # Title
        tk.Label(card, text="✅ ตรวจสอบและยืนยันข้อมูล",
                font=('Segoe UI', 20, 'bold'),
                fg='#1f2937', bg='white').pack(pady=(0, 30))
        
        # Summary frame
        summary_frame = tk.Frame(card, bg='#f0f9ff', padx=30, pady=20, relief='solid', bd=1)
        summary_frame.pack(fill='x', pady=(0, 30))
        
        # Customer info
        tk.Label(summary_frame, text="👤 ข้อมูลลูกค้า",
                font=('Segoe UI', 14, 'bold'),
                fg='#1f2937', bg='#f0f9ff').pack(anchor='w', pady=(0, 10))
        
        tk.Label(summary_frame, text=f"บริษัท: {self.selected_customer.get('CustomerName', 'N/A')}",
                font=('Segoe UI', 11),
                fg='#374151', bg='#f0f9ff').pack(anchor='w')
        
        tk.Label(summary_frame, text=f"เลขประจำตัวผู้เสียภาษี: {self.selected_customer.get('CustomerTaxNum', 'N/A')}",
                font=('Segoe UI', 11),
                fg='#374151', bg='#f0f9ff').pack(anchor='w')
        
        # Invoices info
        tk.Label(summary_frame, text="📋 ใบแจ้งหนี้ที่เลือก",
                font=('Segoe UI', 14, 'bold'),
                fg='#1f2937', bg='#f0f9ff').pack(anchor='w', pady=(20, 10))
        
        for invoice_no in self.selected_invoices:
            tk.Label(summary_frame, text=f"• {invoice_no}",
                    font=('Segoe UI', 11),
                    fg='#374151', bg='#f0f9ff').pack(anchor='w')
        
        tk.Label(summary_frame, text=f"รวม {len(self.selected_invoices)} รายการ",
                font=('Segoe UI', 11, 'bold'),
                fg='#10b981', bg='#f0f9ff').pack(anchor='w', pady=(10, 0))
        
        # Action buttons
        action_frame = tk.Frame(card, bg='white')
        action_frame.pack(fill='x', pady=(30, 0))
        
        back_btn = tk.Button(action_frame, text="← ย้อนกลับ",
                            font=('Segoe UI', 11),
                            bg='#6b7280', fg='white',
                            border=0, padx=20, pady=10,
                            cursor='hand2',
                            command=self.show_step3)
        back_btn.pack(side='left')
        
        confirm_btn = tk.Button(action_frame, text="✅ สร้างใบวางบิล",
                               font=('Segoe UI', 11, 'bold'),
                               bg='#10b981', fg='white',
                               border=0, padx=30, pady=10,
                               cursor='hand2',
                               command=self.create_billing_document)
        confirm_btn.pack(side='right')
        
    def save_selected_invoices(self):
        """บันทึกรายการใบแจ้งหนี้ที่เลือกไว้"""
        if not hasattr(self, 'selected_invoice_numbers'):
            self.selected_invoice_numbers = set()
        
        # เก็บรายการที่เลือกจาก tree ปัจจุบัน
        for item_id in self.selected_invoices:
            if item_id in self.invoice_items:
                invoice_number = self.invoice_items[item_id].get('InvoiceNumber', '')
                if invoice_number:
                    self.selected_invoice_numbers.add(invoice_number)
        
        print(f"Saved selected invoices: {self.selected_invoice_numbers}")
    
    def create_billing_document(self):
        try:
            customer_id = self.selected_customer.get('CustomerId')
            created_by = self.user_data.get('username', 'Unknown')
            
            billing_doc_no = self.db.create_billing_document(
                customer_id=customer_id,
                invoice_numbers=self.selected_invoices,
                created_by=created_by
            )
            
            if billing_doc_no:
                messagebox.showinfo(
                    "สำเร็จ", 
                    f"สร้างใบวางบิลเรียบร้อยแล้ว\nเลขที่เอกสาร: {billing_doc_no}"
                )
                self.reset_form()
            else:
                messagebox.showerror("ข้อผิดพลาด", "ไม่สามารถสร้างใบวางบิลได้")
                
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาด: {str(e)}")
    
    def reset_form(self):
        self.selected_customer = None
        self.selected_invoices = []
        self.show_step1()
    
    def close_window(self):
        try:
            self.db.close_connection()
        except:
            pass
        self.window.destroy()

# สำหรับทดสอบ
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide main window
    
    user_data = {"username": "admin", "role": "admin"}
    app = SalesBillUI(root, user_data)
    
    root.mainloop()