import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
import html
from SalesBill_database import SalesBillDatabase
from utils import set_window_icon

class SalesBillUI:
    def __init__(self, parent, user_data):
        self.parent = parent
        self.user_data = user_data
        self.window = tk.Toplevel(parent)
        set_window_icon(self.window)
        
        # Initialize variables first
        self.current_step = 1
        self.selected_customer = None
        self.selected_invoices = set()  
        self.selected_invoice_numbers = set() 
        self.discount_amount = 0.0
        self.remark = ''
        
        self.setup_window()
        
        # Initialize database
        try:
            self.db = SalesBillDatabase()
            if not self.db.test_connection():
                messagebox.showerror("ข้อผิดพลาด", "ไม่สามารถเชื่อมต่อฐานข้อมูลได้",
                    parent=self.window)
                self.window.destroy()
                return
            
            # ทดสอบข้อมูล
            print("🔍 ทดสอบข้อมูลในฐานข้อมูล...")
            self.db.test_data()
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ข้อผิดพลาดฐานข้อมูล: {str(e)}",
                parent=self.window)
            self.window.destroy()
            return
        
        self.show_step1()
        
    def setup_window(self):
        import theme
        self.window.title("🛒 ระบบใบวางบิลขาย")
        theme.setup_toplevel(self.window, "🛒 ระบบใบวางบิลขาย", 1400, 900)
        self.create_header()

    def center_window(self):
        self.window.update_idletasks()
        width = 1400
        height = 900
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_header(self):
        import theme
        theme.configure_styles()
        theme.build_header(
            self.window,
            title    = "🛒 ระบบใบวางบิลขาย",
            subtitle = "จัดการใบวางบิลการขายสินค้า",
            username = self.user_data["username"],
            accent   = theme.GREEN,
            on_close = self.close_window,
        )
        self.create_step_indicator()

    def create_step_indicator(self):
        import theme
        steps = ["สร้างเอกสาร", "ค้นหาลูกค้า", "เลือกใบแจ้งหนี้", "ตรวจสอบและยืนยัน"]
        theme.build_step_indicator(
            self.window,
            steps   = steps,
            current = self.current_step,
            accent  = theme.GREEN,
        )

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
        
        # Title
        tk.Label(card, text="เริ่มสร้างใบวางบิลขาย",
                font=('Segoe UI', 20, 'bold'),
                fg='#1f2937', bg='white').pack(pady=(0, 10))
        
        tk.Label(card, text="เลือกการดำเนินการที่ต้องการ",
                font=('Segoe UI', 12),
                fg='#6b7280', bg='white').pack(pady=(0, 40))
        
        # Icon
        icon_frame = tk.Frame(card, bg='#10b981', width=120, height=120)
        icon_frame.pack(pady=(0, 40))
        icon_frame.pack_propagate(False)
        
        tk.Label(icon_frame, text="📄",
                font=('Segoe UI Emoji', 48),
                fg='white', bg='#10b981').pack(expand=True)
        
        # Buttons container
        buttons_frame = tk.Frame(card, bg='white')
        buttons_frame.pack()
        
        # Start button
        start_btn = tk.Button(buttons_frame, text="สร้างใบวางบิลขาย",
                            font=('Segoe UI', 14, 'bold'),
                            bg='#10b981', fg='white',
                            activebackground='#059669',
                            border=0, padx=40, pady=15,
                            cursor='hand2',
                            command=self.show_step2)
        start_btn.pack(side='left', padx=(0, 20))
        
        # History button
        history_btn = tk.Button(buttons_frame, text="ดูประวัติใบวางบิล",
                            font=('Segoe UI', 14, 'bold'),
                            bg='#3b82f6', fg='white',
                            activebackground='#2563eb',
                            border=0, padx=40, pady=15,
                            cursor='hand2',
                            command=self.open_billing_history)
        history_btn.pack(side='left')
        
        # Hover effects
        start_btn.bind("<Enter>", lambda e: start_btn.config(bg='#059669'))
        start_btn.bind("<Leave>", lambda e: start_btn.config(bg='#10b981'))
        
        history_btn.bind("<Enter>", lambda e: history_btn.config(bg='#2563eb'))
        history_btn.bind("<Leave>", lambda e: history_btn.config(bg='#3b82f6'))

    def open_billing_history(self):
        """เปิดหน้าประวัติใบวางบิล"""
        try:
            from SalesBill_History import SalesBillHistoryUI
            SalesBillHistoryUI(self.window, self.user_data)
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถเปิดหน้าประวัติได้: {str(e)}",
                parent=self.window)
            print(f"Error opening history: {str(e)}")
                
    def show_step2(self):
        self.current_step = 2
        self.create_step_indicator()
        self.clear_content()
        
        content = tk.Frame(self.window, bg='#f8fafc')
        content.pack(fill='both', expand=True, padx=20, pady=10)
        content._content = True
        
        card = tk.Frame(content, bg='white', padx=20, pady=20)
        card.pack(expand=True, fill='both')
        
        # Title
        tk.Label(card, text="ค้นหาลูกค้า",
                font=('Segoe UI', 16, 'bold'),
                fg='#1f2937', bg='white').pack(pady=(0, 5))
        
        tk.Label(card, text="ป้อนชื่อบริษัทหรือเลขประจำตัวผู้เสียภาษี",
                font=('Segoe UI', 10),
                fg='#6b7280', bg='white').pack(pady=(0, 15))
        
        # Search section
        search_frame = tk.Frame(card, bg='white')
        search_frame.pack(fill='x', pady=(0, 15))
        
        search_container = tk.Frame(search_frame, bg='#f9fafb', relief='solid', bd=1)
        search_container.pack(fill='x')
        
        self.search_entry = tk.Entry(search_container, font=('Segoe UI', 11),
                                    bg='#f9fafb', fg='#374151',
                                    border=0, insertbackground='#10b981')
        self.search_entry.pack(side='left', fill='x', expand=True, padx=10, pady=8)
        self.search_entry.bind('<KeyRelease>', self.search_customers)
        self.search_entry.bind('<Return>', self.search_customers)
        
        search_btn = tk.Button(search_container, text="ค้นหา",
                            font=('Segoe UI', 10),
                            bg='#10b981', fg='white',
                            border=0, padx=12,
                            cursor='hand2',
                            command=self.search_customers)
        search_btn.pack(side='right', fill='y')
        
        # Results frame
        self.results_frame = tk.Frame(card, bg='white')
        self.results_frame.pack(fill='both', expand=True)
        
        # Back button at bottom
        back_frame = tk.Frame(card, bg='white')
        back_frame.pack(fill='x', pady=(15, 0))
        
        back_btn = tk.Button(back_frame, text="← ย้อนกลับ",
                            font=('Segoe UI', 10),
                            bg='#6b7280', fg='white',
                            border=0, padx=20, pady=8,
                            cursor='hand2',
                            command=self.show_step1)
        back_btn.pack(side='left')
        
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
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถค้นหาลูกค้าได้: {str(e)}",
                parent=self.window)
            self.display_customers([])
            
    def select_from_tree(self):
        """เลือกลูกค้าจากตาราง"""
        selected_item = self.customer_tree.selection()
        if not selected_item:
            messagebox.showwarning("คำเตือน", "กรุณาเลือกลูกค้าจากตาราง",
                parent=self.window)
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
            
        messagebox.showinfo("สำเร็จ", f"เลือกลูกค้า: {customer_display_name}",
            parent=self.window)
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
        card = tk.Frame(parent, bg='#f8fafc', relief='solid', bd=1, padx=15, pady=8)
        card.pack(fill='x', pady=3)  # ลด spacing
        
        # Header row
        header_frame = tk.Frame(card, bg='#f8fafc')
        header_frame.pack(fill='x')
        
        # Customer info
        customer_id = customer.get('CustomerId', '')
        customer_name = customer.get('Name', '').strip()
        acct = customer.get('Acct', '').strip()
        
        display_name = customer_name if customer_name else f"ลูกค้า ID: {customer_id}"
        
        # Left side
        info_frame = tk.Frame(header_frame, bg='#f8fafc')
        info_frame.pack(side='left', fill='x', expand=True)
        
        tk.Label(info_frame, text=display_name,
                font=('Segoe UI', 12, 'bold'),  # ลดขนาด
                fg='#1f2937', bg='#f8fafc').pack(anchor='w')
        
        details = f"ID: {customer_id}"
        if acct:
            details += f" | บัญชี: {acct}"
        
        tk.Label(info_frame, text=details,
                font=('Segoe UI', 9),
                fg='#6b7280', bg='#f8fafc').pack(anchor='w')
        
        # Right side - ปุ่มเล็กลง
        select_btn = tk.Button(header_frame, text="เลือก",
                            font=('Segoe UI', 10, 'bold'),
                            bg='#10b981', fg='white',
                            border=0, padx=15, pady=6,
                            cursor='hand2',
                            command=lambda: self.select_customer(customer))
        select_btn.pack(side='right')
        
        # Hover effects
        def on_enter(event):
            card.config(bg='#f0f9ff', bd=2)
            info_frame.config(bg='#f0f9ff')
            header_frame.config(bg='#f0f9ff')
            for widget in info_frame.winfo_children():
                if widget.winfo_class() == 'Label':
                    widget.config(bg='#f0f9ff')
        
        def on_leave(event):
            card.config(bg='#f8fafc', bd=1)
            info_frame.config(bg='#f8fafc')
            header_frame.config(bg='#f8fafc')
            for widget in info_frame.winfo_children():
                if widget.winfo_class() == 'Label':
                    widget.config(bg='#f8fafc')
        
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)
        card.bind("<Button-1>", lambda e: self.select_customer(customer))
                
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
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถโหลดข้อมูลได้: {str(e)}",
                parent=self.window)

    def on_customer_select(self, event):
        """เมื่อ double-click ในตาราง"""
        self.select_from_tree()

    # def select_from_tree(self):
        """เลือกลูกค้าจากตาราง"""
        selected_item = self.customer_tree.selection()
        if not selected_item:
            messagebox.showwarning("คำเตือน", "กรุณาเลือกลูกค้าจากตาราง",
                parent=self.window)
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
            
        messagebox.showinfo("สำเร็จ", f"เลือกลูกค้า: {customer_display_name}",
            parent=self.window)
        self.show_step3()
    
    def show_step3(self):
        self.current_step = 3
        self.create_step_indicator()
        self.clear_content()
        
        content = tk.Frame(self.window, bg='#f8fafc')
        content.pack(fill='both', expand=True, padx=20, pady=10)
        content._content = True
        
        card = tk.Frame(content, bg='white', padx=20, pady=15)
        card.pack(expand=True, fill='both')
        
        # Title - เล็กลง
        customer_name = self.selected_customer.get('Name', '').strip()
        if not customer_name:
            customer_name = f"ลูกค้า ID: {self.selected_customer.get('CustomerId', 'N/A')}"
        
        tk.Label(card, text=f"ใบแจ้งหนี้ของ {customer_name}",
                font=('Segoe UI', 14, 'bold'),  # ลดขนาด
                fg='#1f2937', bg='white').pack(anchor='w', pady=(0, 10))
        
        # Load invoices
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
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถโหลดใบแจ้งหนี้ได้: {str(e)}",
                parent=self.window)
                
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
        
        # Create Treeview with consistent style
        style = ttk.Style()
        style.configure("Invoice.Treeview", 
                    font=('Segoe UI', 10),  # ฟอนต์เท่ากับ Step 4
                    rowheight=25)
        style.configure("Invoice.Treeview.Heading", 
                    font=('Segoe UI', 11, 'bold'))
        
        columns = ('Select', 'InvoiceNumber', 'InvoiceDate', 'MaxDueDate', 'DueDate', 'UnpaidAmount')
        
        self.invoice_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', 
                                        height=12, style="Invoice.Treeview")  # เพิ่มความสูง
        
        # Configure columns
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
        self.sync_selected_invoices()
        self.clear_content()
        
        content = tk.Frame(self.window, bg='#f8fafc')
        content.pack(fill='both', expand=True, padx=20, pady=10)
        content._content = True
        
        card = tk.Frame(content, bg='white', padx=20, pady=15)
        card.pack(expand=True, fill='both')
        
        # Title
        tk.Label(card, text="ตรวจสอบและยืนยัน",
                font=('Segoe UI', 16, 'bold'),
                fg='#1f2937', bg='white').pack(pady=(0, 15))
        
        # Customer info - กะทัดรัด
        customer_detail = self.get_customer_detail()
        
        customer_frame = tk.Frame(card, bg='#f0f9ff', padx=15, pady=8, relief='solid', bd=1)
        customer_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(customer_frame, text="ข้อมูลลูกค้า",
                font=('Segoe UI', 12, 'bold'),
                fg='#1f2937', bg='#f0f9ff').pack(anchor='w', pady=(0, 3))
        
        if customer_detail:
            info_text = f"ชื่อ: {customer_detail.get('Name', '')} | โทร: {customer_detail.get('PhoneMobile', '')} | ที่อยู่: {customer_detail.get('full_address', '')}"
            tk.Label(customer_frame, text=info_text,
                    font=('Segoe UI', 9),
                    fg='#374151', bg='#f0f9ff',
                    wraplength=1000).pack(anchor='w')
        
        # Invoice table header
        tk.Label(card, text="รายการใบแจ้งหนี้ที่เลือก",
                font=('Segoe UI', 12, 'bold'),
                fg='#1f2937', bg='white').pack(anchor='w', pady=(0, 5))
        
        # Table frame - ใช้พื้นที่เต็มที่
        tree_frame = tk.Frame(card, bg='white')
        tree_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        # Treeview with same style as Step 3
        style = ttk.Style()
        style.configure("Summary.Treeview", 
                    font=('Segoe UI', 10),
                    rowheight=25)
        style.configure("Summary.Treeview.Heading", 
                    font=('Segoe UI', 11, 'bold'))
        
        columns = ('No', 'InvoiceNumber', 'InvoiceDate', 'MaxDueDate', 'DueDate', 'UnpaidAmount')
        
        summary_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', 
                                style="Summary.Treeview")
        
        # Configure columns
        column_config = {
            'No': {'text': 'ลำดับที่', 'width': 60, 'anchor': 'center'},
            'InvoiceNumber': {'text': 'เลขที่ใบแจ้งหนี้', 'width': 150, 'anchor': 'center'},
            'InvoiceDate': {'text': 'วันที่ออกใบแจ้งหนี้', 'width': 120, 'anchor': 'center'},
            'MaxDueDate': {'text': 'ระยะเวลาชำระ (วัน)', 'width': 100, 'anchor': 'center'},
            'DueDate': {'text': 'วันครบกำหนด', 'width': 120, 'anchor': 'center'},
            'UnpaidAmount': {'text': 'ยอดค้างชำระ (บาท)', 'width': 150, 'anchor': 'center'}
        }
        
        for col in columns:
            summary_tree.heading(col, text=column_config[col]['text'], anchor='center')
            summary_tree.column(col, 
                            width=column_config[col]['width'], 
                            minwidth=50,
                            anchor=column_config[col]['anchor'])
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=summary_tree.yview)
        summary_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        summary_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Insert data
        total_amount = 0.0
        count = 0
        
        for item_id in self.selected_invoices:
            if item_id in self.invoice_items:
                invoice = self.invoice_items[item_id]
                count += 1
                
                invoice_date = invoice.get('InvoiceDate', '')[:10] if len(invoice.get('InvoiceDate', '')) > 10 else invoice.get('InvoiceDate', '')
                due_date = invoice.get('DueDate', '')[:10] if len(invoice.get('DueDate', '')) > 10 else invoice.get('DueDate', '')
                
                try:
                    amount_str = str(invoice.get('UnpaidAmount', '0')).replace(',', '')
                    amount = float(amount_str)
                    total_amount += amount
                    formatted_amount = f"{amount:,.2f}"
                except:
                    formatted_amount = str(invoice.get('UnpaidAmount', '0'))
                
                summary_tree.insert('', 'end', values=(
                    count,
                    invoice.get('InvoiceNumber', ''),
                    invoice_date,
                    invoice.get('MaxDueDate', ''),
                    due_date,
                    formatted_amount
                ))
        
        # Summary section - ปรับให้มีส่วนลดและยอดสุทธิ
        summary_frame = tk.Frame(card, bg='white', padx=20, pady=15, relief='solid', bd=1)
        summary_frame.pack(fill='x', pady=(10, 15))

        # ยอดรวม
        total_row = tk.Frame(summary_frame, bg='white')
        total_row.pack(fill='x', pady=5)
        tk.Label(total_row, text=f"เลือกแล้ว: {count} รายการ",
                font=('Segoe UI', 11),
                fg='#6b7280', bg='white').pack(side='left')
        self.summary_total = tk.Label(total_row, text=f"ยอดรวม: {total_amount:,.2f} บาท",
                                    font=('Segoe UI', 11, 'bold'),
                                    fg='#1f2937', bg='white')
        self.summary_total.pack(side='right')

        # ส่วนลด
        discount_row = tk.Frame(summary_frame, bg='white')
        discount_row.pack(fill='x', pady=5)
        tk.Label(discount_row, text="ส่วนลดท้ายบิล:",
                font=('Segoe UI', 11),
                fg='#6b7280', bg='white').pack(side='left')

        discount_input_frame = tk.Frame(discount_row, bg='white')
        discount_input_frame.pack(side='right')

        self.discount_var = tk.StringVar(value="0.00")
        discount_entry = tk.Entry(discount_input_frame, 
                                textvariable=self.discount_var,
                                font=('Segoe UI', 11),
                                width=12,
                                justify='right',
                                bg='#f9fafb',
                                relief='solid',
                                borderwidth=1)
        discount_entry.pack(side='left', padx=(0, 5))
        discount_entry.bind('<KeyRelease>', self.calculate_net_amount)

        tk.Label(discount_input_frame, text="บาท",
                font=('Segoe UI', 11),
                fg='#6b7280', bg='white').pack(side='left')

        # หมายเหตุ (แสดงในใบวางบิล)
        remark_row = tk.Frame(summary_frame, bg='white')
        remark_row.pack(fill='x', pady=5)
        tk.Label(remark_row, text="หมายเหตุ:",
                font=('Segoe UI', 11),
                fg='#6b7280', bg='white').pack(side='left')

        self.remark_var = tk.StringVar(value="")
        remark_entry = tk.Entry(remark_row,
                                textvariable=self.remark_var,
                                font=('Segoe UI', 11),
                                bg='#f9fafb',
                                relief='solid',
                                borderwidth=1)
        remark_entry.pack(side='left', fill='x', expand=True, padx=(10, 0))

        # เส้นแบ่ง
        separator = tk.Frame(summary_frame, bg='#e5e7eb', height=1)
        separator.pack(fill='x', pady=10)

        # ยอดคงเหลือสุทธิ
        net_row = tk.Frame(summary_frame, bg='#f0fdf4', relief='solid', bd=1)
        net_row.pack(fill='x', pady=5)
        net_content = tk.Frame(net_row, bg='#f0fdf4')
        net_content.pack(fill='x', padx=10, pady=8)

        tk.Label(net_content, text="ยอดคงเหลือสุทธิ:",
                font=('Segoe UI', 13, 'bold'),
                fg='#166534', bg='#f0fdf4').pack(side='left')
        self.summary_net = tk.Label(net_content, text=f"{total_amount:,.2f} บาท",
                                font=('Segoe UI', 14, 'bold'),
                                fg='#15803d', bg='#f0fdf4')
        self.summary_net.pack(side='right')
        
        # Action buttons
        action_frame = tk.Frame(card, bg='white')
        action_frame.pack(fill='x')
        
        back_btn = tk.Button(action_frame, text="ย้อนกลับ",
                            font=('Segoe UI', 10),
                            bg='#6b7280', fg='white',
                            border=0, padx=20, pady=8,
                            cursor='hand2',
                            command=self.show_step3)
        back_btn.pack(side='left')
        
        confirm_btn = tk.Button(action_frame, text="สร้างใบวางบิล",
                            font=('Segoe UI', 10, 'bold'),
                            bg='#10b981', fg='white',
                            border=0, padx=25, pady=8,
                            cursor='hand2',
                            command=self.create_billing_document)
        confirm_btn.pack(side='right')
                        
    def get_customer_detail(self):
        """ดึงข้อมูลลูกค้าแบบละเอียดพร้อมที่อยู่"""
        try:
            customer_id = self.selected_customer.get('CustomerId')
            return self.db.get_customer_detail(customer_id)
        except Exception as e:
            
            print(f"Error getting customer detail: {str(e)}")
            return {}
                        
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
        
    def calculate_net_amount(self, event=None):
        """คำนวณยอดคงเหลือหลังหักส่วนลด"""
        try:
            total_text = self.summary_total.cget('text').replace('ยอดรวม: ', '').replace(' บาท', '').replace(',', '')
            total_amount = float(total_text)
            
            discount_text = self.discount_var.get().replace(',', '')
            discount_amount = float(discount_text) if discount_text else 0.0
            
            if discount_amount > total_amount:
                discount_amount = total_amount
                self.discount_var.set(f"{discount_amount:,.2f}")
            
            net_amount = total_amount - discount_amount
            self.discount_amount = discount_amount
            
            self.summary_net.config(text=f"{net_amount:,.2f} บาท")
            
        except ValueError:
            pass
    
    def create_billing_document(self):
        try:
            customer_id = self.selected_customer.get('CustomerId')
            created_by = self.user_data.get('username', 'Unknown')
            user_id = self.user_data.get('username', 'Unknown')  
            
            # ดึงเลขที่ใบแจ้งหนี้จริงจาก selected_invoices
            actual_invoice_numbers = []
            for item_id in self.selected_invoices:
                if item_id in self.invoice_items:
                    invoice_number = self.invoice_items[item_id].get('InvoiceNumber', '')
                    if invoice_number:
                        actual_invoice_numbers.append(str(invoice_number))
            
            if not actual_invoice_numbers:
                messagebox.showerror("ข้อผิดพลาด", "ไม่พบรายการใบแจ้งหนี้ที่เลือก", parent=self.window)
                return
            
            #เพิ่มการยืนยันก่อนสร้าง
            confirm = messagebox.askyesno(
                "ยืนยันการสร้างเอกสาร",
                f"ต้องการสร้างใบวางบิลขายหรือไม่?\n\n"
                f"ชื่อลูกค้า: {self.selected_customer.get('Name', '')}\n"
                f"จำนวนรายการ: {len(actual_invoice_numbers)} รายการ\n\n"
                f"กดยืนยันเพื่อดำเนินการต่อ",
                icon='question',
                parent=self.window
            )
            
            if not confirm:  # ถ้ากด No ให้หยุดทำงาน
                return
            
            # ⭐ ตรวจสอบว่ามี discount_amount หรือไม่
            if not hasattr(self, 'discount_amount'):
                self.discount_amount = 0.0

            print(f"🔍 Discount amount ที่จะบันทึก: {self.discount_amount}")  

            # คอลัมน์ Notes รับได้ 500 ตัวอักษร
            self.remark = self.remark_var.get().strip()[:500] if hasattr(self, 'remark_var') else ''

            billing_doc_no = self.db.create_billing_document(
                customer_id=customer_id,
                invoice_numbers=actual_invoice_numbers,
                created_by=created_by,
                user_id=user_id,
                discount_amount=self.discount_amount,
                remark=self.remark
            )
            
            if billing_doc_no:
                # สอบถามว่าต้องการแสดงตัวอย่างใบวางบิลหรือไม่
                response = messagebox.askyesno(
                    "สำเร็จ", 
                    f"สร้างใบวางบิลเรียบร้อยแล้ว\nเลขที่เอกสาร: {billing_doc_no}\n\nคุณต้องการแสดงตัวอย่างใบวางบิลหรือไม่?",
                    icon='question',
                    parent=self.window
                    
                )
                
                if response:  # ถ้าตอบ Yes
                    self.show_billing_template(billing_doc_no, customer_id, actual_invoice_numbers)
                
                self.reset_form()
            else:
                messagebox.showerror("ข้อผิดพลาด", "ไม่สามารถสร้างใบวางบิลได้", parent=self.window)
                
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาด: {str(e)}", parent=self.window)
            print(f"Error in create_billing_document: {str(e)}")
            
    def show_billing_template(self, billing_doc_no, customer_id, invoice_numbers):
        """แสดงตัวอย่างใบวางบิลด้วยข้อมูลจริง"""
        try:
            # Import BillingNoteGenerator
            from billing_note_generator import BillingNoteGenerator
            
            # เตรียมข้อมูลสำหรับ template
            template_data = self.prepare_template_data(billing_doc_no, customer_id, invoice_numbers)
            
            # แสดงตัวอย่างด้วยข้อมูลจริง
            BillingNoteGenerator.Preview_Template_With_Data(template_data, 'sales')
            
        except ImportError as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่พบ BillingNoteGenerator: {str(e)}",
                parent=self.window)
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถแสดงตัวอย่างใบวางบิลได้: {str(e)}",
                parent=self.window)
            print(f"Error showing template: {str(e)}")

    def prepare_template_data(self, billing_doc_no, customer_id, invoice_numbers):
        """เตรียมข้อมูลสำหรับ template"""
        try:
            # ⭐ ดึงข้อมูลบริษัทจาก database
            try:
                from database_manager import get_company_data
                company_data = get_company_data()
            except:
                company_data = {
                    'Companyname': 'ไม่พบข้อมูลบริษัท',
                    'SiteAddress': '',
                    'PhoneNumber': '',
                    'TaxId': '',
                    'SitePicture': ''
                }
            
            # ดึงข้อมูลลูกค้าแบบละเอียด
            customer_detail = self.db.get_customer_detail(customer_id)
            
            # คำนวณยอดรวมและเตรียมรายการ
            total_amount = 0.0
            first_item = None
            additional_items = []
            
            order = 1
            for item_id in self.selected_invoices:
                if item_id in self.invoice_items:
                    invoice = self.invoice_items[item_id]
                    
                    # แปลงข้อมูลวันที่เป็น dd/mm/yyyy
                    invoice_date = invoice.get('InvoiceDate', '')[:10] if len(invoice.get('InvoiceDate', '')) > 10 else invoice.get('InvoiceDate', '')
                    if invoice_date:
                        try:
                            date_obj = datetime.strptime(invoice_date, '%Y-%m-%d')
                            invoice_date = date_obj.strftime('%d/%m/%Y')
                        except:
                            pass
                    
                    due_date = invoice.get('DueDate', '')[:10] if len(invoice.get('DueDate', '')) > 10 else invoice.get('DueDate', '')
                    if due_date:
                        try:
                            date_obj = datetime.strptime(due_date, '%Y-%m-%d')
                            due_date = date_obj.strftime('%d/%m/%Y')
                        except:
                            pass
                    
                    try:
                        unpaid_amount = float(str(invoice.get('UnpaidAmount', '0')).replace(',', ''))
                        total_amount += unpaid_amount
                        formatted_amount = f"{unpaid_amount:,.2f}"
                    except:
                        unpaid_amount = 0.0
                        formatted_amount = "0.00"
                    
                    item_data = {
                        'order': order,  # ⭐ เพิ่ม order
                        'type': 'ใบขาย',  # แก้เป็น "ใบขาย" ตาม template
                        'docNo': invoice.get('InvoiceNumber', ''),
                        'date': invoice_date,
                        'credit': str(invoice.get('MaxDueDate', '')),
                        'dueDate': due_date,
                        'total': formatted_amount,
                        'paidAmount': '0.00',
                        'unpaidAmount': formatted_amount
                    }
                    
                    if order == 1:
                        first_item = item_data
                    else:
                        additional_items.append(item_data)
                    
                    order += 1
            
                # ⭐ ตรวจสอบว่ามี discount_amount หรือไม่
                if not hasattr(self, 'discount_amount'):
                    self.discount_amount = 0.0

                # คำนวณยอดสุทธิ
                net_amount = total_amount - self.discount_amount

                # แปลงตัวเลขเป็นภาษาไทย (ใช้ยอดสุทธิ)
                thai_baht_text = self.number_to_thai(net_amount)

                # เตรียมข้อมูลสำหรับ template
                template_data = {
                    'DocumentTitle': 'ใบวางบิลขาย',
                    
                    # ⭐ ข้อมูลบริษัท - ระบุชัดเจน
                    'Companyname': company_data.get('Companyname', 'ไม่พบข้อมูล'),
                    'SiteAddress': company_data.get('SiteAddress', 'ไม่พบข้อมูล'),
                    'PhoneNumber': company_data.get('PhoneNumber', 'ไม่พบข้อมูล'),
                    'TaxId': company_data.get('TaxId', 'ไม่พบข้อมูล'),
                    'SitePicture': company_data.get('SitePicture', ''),
                    
                    # ข้อมูลลูกค้า
                    'CustomerName': customer_detail.get('Name', ''),
                    'CustomerAddress': customer_detail.get('full_address', ''),
                    'PhoneMobile': customer_detail.get('PhoneMobile', ''),
                    'CustomerTaxNum': customer_detail.get('CustomerTaxNum', ''),
                    
                    # ข้อมูลเอกสาร
                    'DocNo': billing_doc_no,
                    'DocDate': datetime.now().strftime('%d/%m/%Y'),
                    
                    # ข้อมูลรายการแรก
                    'InvoiceNumber': first_item['docNo'] if first_item else '',
                    'InvoiceDate': first_item['date'] if first_item else '',
                    'MaxDueDate': first_item['credit'] if first_item else '',
                    'DueDate': first_item['dueDate'] if first_item else '',
                    'Total': first_item['total'] if first_item else '0.00',
                    'PaidAmount': '0.00',
                    'UnpaidAmount': first_item['unpaidAmount'] if first_item else '0.00',
                    
                    # ⭐ ข้อมูลสรุป - เพิ่มส่วนลดและยอดสุทธิ
                    'TotalUnpaidAmount': f"{total_amount:,.2f}",
                    'Discount': f"{self.discount_amount:,.2f}",
                    'NetAmount': f"{net_amount:,.2f}",
                    'TextThaiBaht': thai_baht_text,  # ⭐ ใช้ค่าที่แปลงจาก net_amount แล้ว
                    'Remark': html.escape(getattr(self, 'remark', '')),
                    
                    # รายการเพิ่มเติม
                    'additionalItems': additional_items
                }
            # Debug - ตรวจสอบค่าก่อนส่งไปยัง template
            print("\n🔍 Final template_data:")
            print(f"Companyname: {template_data.get('Companyname')}")
            print(f"SiteAddress: {template_data.get('SiteAddress')}")
            print(f"CustomerName: {template_data.get('CustomerName')}")
            print(f"TotalUnpaidAmount: {template_data.get('TotalUnpaidAmount')}")
            print(f"Discount: {template_data.get('Discount')}")  # ⭐ เพิ่ม
            print(f"NetAmount: {template_data.get('NetAmount')}")  # ⭐ เพิ่ม
            print(f"TextThaiBaht: {template_data.get('TextThaiBaht')}")  # ⭐ เพิ่ม
            print()

            return template_data           
        except Exception as e:
            print(f"Error preparing template data: {str(e)}")
            import traceback
            traceback.print_exc()
            return {}
        
    def number_to_thai(self, amount):
        """แปลงตัวเลขเป็นตัวหนังสือภาษาไทย"""
        try:
            amount = float(amount)
            
            # ถ้าเป็นทศนิยม แปลงเป็นจำนวนเต็ม
            baht = int(amount)
            satang = int(round((amount - baht) * 100))
            
            # ตัวเลข
            ones = ['', 'หนึ่ง', 'สอง', 'สาม', 'สี่', 'ห้า', 'หก', 'เจ็ด', 'แปด', 'เก้า']
            
            def convert_group(num):
                """แปลงเลขกลุ่ม 1-999"""
                result = ''
                
                # หลักร้อย
                hundred = num // 100
                if hundred > 0:
                    result += ones[hundred] + 'ร้อย'
                
                # หลักสิบ
                ten = (num % 100) // 10
                if ten > 0:
                    if ten == 1:
                        result += 'สิบ'
                    elif ten == 2:
                        result += 'ยี่สิบ'
                    else:
                        result += ones[ten] + 'สิบ'
                
                # หลักหนึ่ง
                one = num % 10
                if one > 0:
                    if ten > 0 and one == 1:
                        result += 'เอ็ด'
                    else:
                        result += ones[one]
                
                return result
            
            if baht == 0:
                result = 'ศูนย์บาท'
            else:
                result = ''
                
                # ล้าน
                million = baht // 1000000
                if million > 0:
                    result += convert_group(million) + 'ล้าน'
                
                # แสน + หมื่น + พัน
                hundred_thousand = (baht % 1000000) // 100000
                if hundred_thousand > 0:
                    result += convert_group(hundred_thousand) + 'แสน'
                
                ten_thousand = (baht % 100000) // 10000
                if ten_thousand > 0:
                    result += convert_group(ten_thousand) + 'หมื่น'
                
                thousand = (baht % 10000) // 1000
                if thousand > 0:
                    result += convert_group(thousand) + 'พัน'
                
                # ร้อย + สิบ + หนึ่ง
                remainder = baht % 1000
                if remainder > 0:
                    result += convert_group(remainder)
                
                result += 'บาท'
            
            # ส่วนสตางค์
            if satang > 0:
                result += convert_group(satang) + 'สตางค์'
            else:
                result += 'ถ้วน'
            
            return result
            
        except Exception as e:
            return f'(จำนวนเงิน {amount:,.2f} บาท)'
    
        
    # def convert_to_thai_text(self, amount):
    #     """แปลงตัวเลขเป็นตัวอักษรไทย (ตัวอย่างง่าย ๆ)"""
    #     try:
    #         # ตัวอย่างง่าย ๆ - ในการใช้งานจริงอาจต้องใช้ library
    #         amount_int = int(amount)
    #         if amount_int == 0:
    #             return "ศูนยบาทถ้วน"
    #         elif amount_int < 1000:
    #             return f"(จำนวน {amount_int:,.0f} บาท)"
    #         else:
    #             return f"(จำนวน {amount_int:,.0f} บาท)"
    #     except:
    #         return f"(จำนวน {amount:,.0f} บาท)"
                        
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