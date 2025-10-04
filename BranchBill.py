import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from BranchBill_database import BranchBillDatabase

class BranchBillUI:
    def __init__(self, parent, user_data):
        self.parent = parent
        self.user_data = user_data
        self.window = tk.Toplevel(parent)
        
        # Initialize variables first
        self.current_step = 1
        self.selected_branch = None
        self.selected_withdrawals = set()  
        self.selected_withdrawal_numbers = set() 
        
        self.setup_window()
        
        # Initialize database
        try:
            self.db = BranchBillDatabase()
            if not self.db.test_connection():
                messagebox.showerror("ข้อผิดพลาด", "ไม่สามารถเชื่อมต่อฐานข้อมูลได้")
                self.window.destroy()
                return
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ข้อผิดพลาดฐานข้อมูล: {str(e)}")
            self.window.destroy()
            return
        
        self.show_step1()
        
    def setup_window(self):
        self.window.title("ระบบใบวางบิลสาขา - DocFlow Manager")
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
        
        tk.Label(left_frame, text="🏢 ระบบใบวางบิลสาขา", 
                font=('Segoe UI', 18, 'bold'), 
                fg='white', bg='#1f2937').pack(anchor='w')
        
        tk.Label(left_frame, text="จัดการใบวางบิลการโอนสินค้าไปสาขา", 
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
            {"num": 2, "text": "ค้นหาสาขา"},
            {"num": 3, "text": "เลือกใบเบิกโอน"},
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
                
    def sync_selected_withdrawals(self):
        """ซิงค์ข้อมูลการเลือกให้เป็นปัจจุบัน"""
        if not hasattr(self, 'selected_withdrawal_numbers'):
            self.selected_withdrawal_numbers = set()
        else:
            self.selected_withdrawal_numbers.clear()
        
        for item_id in self.selected_withdrawals:
            if item_id in self.withdrawal_items:
                withdrawal_number = self.withdrawal_items[item_id].get('WithdrawalNumber', '')
                if withdrawal_number:
                    self.selected_withdrawal_numbers.add(withdrawal_number)
        
        print(f"Synced selected withdrawals: {self.selected_withdrawal_numbers}")
    
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
        tk.Label(card, text="เริ่มสร้างใบวางบิลสาขา",
                font=('Segoe UI', 20, 'bold'),
                fg='#1f2937', bg='white').pack(pady=(0, 10))
        
        tk.Label(card, text="เลือกการดำเนินการที่ต้องการ",
                font=('Segoe UI', 12),
                fg='#6b7280', bg='white').pack(pady=(0, 40))
        
        # Icon
        icon_frame = tk.Frame(card, bg='#10b981', width=120, height=120)
        icon_frame.pack(pady=(0, 40))
        icon_frame.pack_propagate(False)
        
        tk.Label(icon_frame, text="🏢",
                font=('Segoe UI Emoji', 48),
                fg='white', bg='#10b981').pack(expand=True)
        
        # Buttons container
        buttons_frame = tk.Frame(card, bg='white')
        buttons_frame.pack()
        
        # Start button
        start_btn = tk.Button(buttons_frame, text="สร้างใบวางบิลสาขา",
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
            from BranchBill_History import BranchBillHistoryUI
            BranchBillHistoryUI(self.window, self.user_data)
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถเปิดหน้าประวัติได้: {str(e)}")
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
        tk.Label(card, text="ค้นหาสาขา",
                font=('Segoe UI', 16, 'bold'),
                fg='#1f2937', bg='white').pack(pady=(0, 5))
        
        tk.Label(card, text="ป้อนชื่อสาขาที่ต้องการ",
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
        self.search_entry.bind('<KeyRelease>', self.search_branches)
        self.search_entry.bind('<Return>', self.search_branches)
        
        search_btn = tk.Button(search_container, text="ค้นหา",
                            font=('Segoe UI', 10),
                            bg='#10b981', fg='white',
                            border=0, padx=12,
                            cursor='hand2',
                            command=self.search_branches)
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
        
        # Load initial branches
        self.search_branches()
                            
    def search_branches(self, event=None):
        """ค้นหาสาขา"""
        search_term = self.search_entry.get().strip()
        
        # Show loading
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        loading_label = tk.Label(self.results_frame, text="🔄 กำลังค้นหา...",
                            font=('Segoe UI', 12),
                            fg='#6b7280', bg='white')
        loading_label.pack(expand=True)
        
        self.window.update_idletasks()
        
        try:
            branches = self.db.search_branches(search_term)
            
            print(f"🔍 Search term: '{search_term}' -> Found: {len(branches)} branches")
            
            self.display_branches(branches)
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถค้นหาสาขาได้: {str(e)}")
            self.display_branches([])
        
    def select_branch(self, branch):
        """เลือกสาขา"""
        self.selected_branch = branch
        
        branch_name = branch.get('BranchName', '').strip()
        if not branch_name:
            branch_name = "สาขา (ไม่ระบุชื่อ)"
        
        print(f"Selected branch: {branch_name}")
        self.show_step3()
        
    def display_branches(self, branches):
        # Clear results
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        
        print(f"🔍 Display branches: แสดงผล {len(branches)} รายการ")
        
        if not branches:
            tk.Label(self.results_frame, text="ไม่พบสาขาที่ค้นหา",
                    font=('Segoe UI', 14),
                    fg='#6b7280', bg='white').pack(expand=True)
            return
        
        # Results title
        search_term = self.search_entry.get().strip()
        if search_term:
            title_text = f"ผลการค้นหา '{search_term}': พบ {len(branches)} สาขา"
        else:
            title_text = f"สาขาทั้งหมดที่มียอดค้างวางบิล: {len(branches)} สาขา"
        
        title_label = tk.Label(self.results_frame, text=title_text,
                            font=('Segoe UI', 14, 'bold'),
                            fg='#1f2937', bg='white')
        title_label.pack(anchor='w', pady=(0, 20))
        
        # Container for scrollable content
        container = tk.Frame(self.results_frame, bg='white')
        container.pack(fill='both', expand=True)
        
        # Canvas and scrollbar
        canvas = tk.Canvas(container, bg='white', highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='white')
        
        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        
        scrollable_frame.bind("<Configure>", on_frame_configure)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        canvas_window = canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        def on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)
        
        canvas.bind('<Configure>', on_canvas_configure)
        
        # Create branch cards
        for i, branch in enumerate(branches):
            print(f"🃏 Creating card {i+1} for branch: {branch.get('BranchName')}")
            try:
                self.create_branch_card(scrollable_frame, branch)
                print(f"✅ Card {i+1} created successfully")
            except Exception as e:
                print(f"❌ Error creating card {i+1}: {str(e)}")
        
        self.window.update_idletasks()
        
        print(f"🎯 Display complete: {len(branches)} cards should be visible")
              
    def create_branch_card(self, parent, branch):
        """สร้างการ์ดแสดงข้อมูลสาขา"""
        card = tk.Frame(parent, bg='#f8fafc', relief='solid', bd=1, padx=15, pady=8)
        card.pack(fill='x', pady=3)
        
        header_frame = tk.Frame(card, bg='#f8fafc')
        header_frame.pack(fill='x')
        
        # Branch info
        branch_name = branch.get('BranchName', '')
        withdrawal_count = branch.get('WithdrawalCount', 0)
        total_amount = branch.get('TotalAmount', 0)
        
        display_name = branch_name if branch_name else "สาขา (ไม่ระบุชื่อ)"
        
        # Left side
        info_frame = tk.Frame(header_frame, bg='#f8fafc')
        info_frame.pack(side='left', fill='x', expand=True)
        
        tk.Label(info_frame, text=display_name,
                font=('Segoe UI', 12, 'bold'),
                fg='#1f2937', bg='#f8fafc').pack(anchor='w')
        
        details = f"มี {withdrawal_count} ใบเบิกโอน | ยอดรวม: {total_amount:,.2f} บาท"
        
        tk.Label(info_frame, text=details,
                font=('Segoe UI', 9),
                fg='#6b7280', bg='#f8fafc').pack(anchor='w')
        
        # Right side
        select_btn = tk.Button(header_frame, text="เลือก",
                            font=('Segoe UI', 10, 'bold'),
                            bg='#10b981', fg='white',
                            border=0, padx=15, pady=6,
                            cursor='hand2',
                            command=lambda: self.select_branch(branch))
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
        card.bind("<Button-1>", lambda e: self.select_branch(branch))
    
    def show_step3(self):
        self.current_step = 3
        self.create_step_indicator()
        self.clear_content()
        
        content = tk.Frame(self.window, bg='#f8fafc')
        content.pack(fill='both', expand=True, padx=20, pady=10)
        content._content = True
        
        card = tk.Frame(content, bg='white', padx=20, pady=15)
        card.pack(expand=True, fill='both')
        
        # Title
        branch_name = self.selected_branch.get('BranchName', '').strip()
        if not branch_name:
            branch_name = "สาขา (ไม่ระบุชื่อ)"
        
        tk.Label(card, text=f"ใบเบิกโอนของ {branch_name}",
                font=('Segoe UI', 14, 'bold'),
                fg='#1f2937', bg='white').pack(anchor='w', pady=(0, 10))
        
        # Load withdrawals
        self.load_branch_withdrawals()
                        
    def load_branch_withdrawals(self):
        try:
            branch_name = self.selected_branch.get('BranchName')
            print(f"Loading withdrawals for branch: {branch_name}")
            
            withdrawals = self.db.get_branch_withdrawals(branch_name)
            print(f"Found {len(withdrawals)} withdrawals")
            
            self.display_withdrawals(withdrawals)
        except Exception as e:
            print(f"Error loading withdrawals: {str(e)}")
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถโหลดใบเบิกโอนได้: {str(e)}")
                
    def display_withdrawals(self, withdrawals):
        # Find the card widget
        card = None
        for widget in self.window.winfo_children():
            if hasattr(widget, '_content'):
                card = widget.winfo_children()[0]
                break
        
        if not withdrawals:
            tk.Label(card, text="ไม่พบใบเบิกโอนที่ค้างวางบิลสำหรับสาขานี้",
                    font=('Segoe UI', 14),
                    fg='#6b7280', bg='white').pack(expand=True)
            return
        
        # Create treeview for withdrawals
        tree_frame = tk.Frame(card, bg='white')
        tree_frame.pack(fill='both', expand=True, pady=(0, 20))
        
        style = ttk.Style()
        style.configure("Withdrawal.Treeview", 
                    font=('Segoe UI', 10),
                    rowheight=25)
        style.configure("Withdrawal.Treeview.Heading", 
                    font=('Segoe UI', 11, 'bold'))
        
        columns = ('Select', 'WithdrawalNumber', 'WithdrawalDate', 'Total')
        
        self.withdrawal_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', 
                                        height=12, style="Withdrawal.Treeview")
        
        # Configure columns
        column_config = {
            'Select': {'text': 'เลือก', 'width': 50, 'anchor': 'center'},
            'WithdrawalNumber': {'text': 'เลขที่ใบเบิกโอน', 'width': 150, 'anchor': 'center'},
            'WithdrawalDate': {'text': 'วันที่เบิกโอน', 'width': 120, 'anchor': 'center'},
            'Total': {'text': 'ยอดรวม (บาท)', 'width': 120, 'anchor': 'center'}
        }
            
        for col in columns:
            self.withdrawal_tree.heading(col, text=column_config[col]['text'], anchor='center')
            self.withdrawal_tree.column(col, 
                                width=column_config[col]['width'], 
                                minwidth=50,
                                anchor=column_config[col]['anchor'])
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.withdrawal_tree.yview)
        self.withdrawal_tree.configure(yscrollcommand=scrollbar.set)
        
        self.withdrawal_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Insert data
        self.withdrawal_items = {}
        self.selected_withdrawals = set()
        
        if not hasattr(self, 'selected_withdrawal_numbers'):
            self.selected_withdrawal_numbers = set()
        
        print(f"Displaying withdrawals with pre-selected: {self.selected_withdrawal_numbers}")
        
        for withdrawal in withdrawals:
            withdrawal_number = withdrawal.get('WithdrawalNumber', '')
            is_selected = withdrawal_number in self.selected_withdrawal_numbers
            checkbox = '✓' if is_selected else ''
            
            total = withdrawal.get('Total', 0)
            try:
                total_float = float(str(total).replace(',', ''))
                formatted_total = f"{total_float:,.2f}"
            except:
                formatted_total = str(total)
            
            item_id = self.withdrawal_tree.insert('', 'end', values=(
                checkbox,
                withdrawal_number,
                withdrawal.get('WithdrawalDate', ''),
                formatted_total
            ))
            
            self.withdrawal_items[item_id] = withdrawal
            
            if is_selected:
                self.selected_withdrawals.add(item_id)
        
        # Bind click event
        self.withdrawal_tree.bind('<Button-1>', self.on_withdrawal_click)
        self.withdrawal_tree.bind('<Double-Button-1>', self.on_withdrawal_click)
        
        # Control buttons
        control_frame = tk.Frame(card, bg='white')
        control_frame.pack(fill='x', pady=(10, 0))
        
        left_buttons = tk.Frame(control_frame, bg='white')
        left_buttons.pack(side='left')
        
        select_all_btn = tk.Button(left_buttons, text="เลือกทั้งหมด",
                                font=('Segoe UI', 10),
                                bg='#3b82f6', fg='white',
                                padx=15, pady=8,
                                command=self.select_all_withdrawals)
        select_all_btn.pack(side='left', padx=(0, 10))
        
        clear_all_btn = tk.Button(left_buttons, text="ยกเลิกทั้งหมด",
                                font=('Segoe UI', 10),
                                bg='#ef4444', fg='white',
                                padx=15, pady=8,
                                command=self.clear_all_withdrawals)
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
        
        self.update_selected_count()

    def on_withdrawal_click(self, event):
            item_id = self.withdrawal_tree.identify_row(event.y)
            if not item_id or item_id not in self.withdrawal_items:
                return
            
            values = list(self.withdrawal_tree.item(item_id)['values'])
            withdrawal_number = values[1]
            
            is_currently_selected = item_id in self.selected_withdrawals
            
            # Toggle selection
            if is_currently_selected:
                self.selected_withdrawals.remove(item_id)
                values[0] = ''
                if hasattr(self, 'selected_withdrawal_numbers'):
                    self.selected_withdrawal_numbers.discard(withdrawal_number)
            else:
                self.selected_withdrawals.add(item_id)
                values[0] = '✓'
                if not hasattr(self, 'selected_withdrawal_numbers'):
                    self.selected_withdrawal_numbers = set()
                self.selected_withdrawal_numbers.add(withdrawal_number)
            
            self.withdrawal_tree.item(item_id, values=values)
            
            print(f"Clicked {withdrawal_number}: selected={not is_currently_selected}")
            print(f"Current selected_withdrawal_numbers: {self.selected_withdrawal_numbers}")
            
            self.update_selected_count()
            
    def select_all_withdrawals(self):
        if not hasattr(self, 'selected_withdrawal_numbers'):
            self.selected_withdrawal_numbers = set()
            
        for item_id in self.withdrawal_items:
            self.selected_withdrawals.add(item_id)
            values = list(self.withdrawal_tree.item(item_id)['values'])
            values[0] = '✓'
            self.withdrawal_tree.item(item_id, values=values)
            withdrawal_number = values[1]
            self.selected_withdrawal_numbers.add(withdrawal_number)
        self.update_selected_count()

    def clear_all_withdrawals(self):
        self.selected_withdrawals.clear()
        if hasattr(self, 'selected_withdrawal_numbers'):
            self.selected_withdrawal_numbers.clear()
            
        for item_id in self.withdrawal_items:
            values = list(self.withdrawal_tree.item(item_id)['values'])
            values[0] = ''
            self.withdrawal_tree.item(item_id, values=values)
        self.update_selected_count()
        
    def update_selected_count(self):
        if not isinstance(self.selected_withdrawals, set):
            self.selected_withdrawals = set(self.selected_withdrawals) if self.selected_withdrawals else set()
        
        selected_count = len(self.selected_withdrawals)
        
        # Calculate total amount
        total_amount = 0.0
        for item_id in self.selected_withdrawals:
            withdrawal = self.withdrawal_items[item_id]
            try:
                amount_str = str(withdrawal.get('Total', '0')).replace(',', '')
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
        
    def show_step4(self):
        self.current_step = 4
        self.create_step_indicator()
        self.sync_selected_withdrawals()
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
        
        # Branch info
        branch_detail = self.get_branch_detail()
        
        branch_frame = tk.Frame(card, bg='#f0f9ff', padx=15, pady=8, relief='solid', bd=1)
        branch_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(branch_frame, text="ข้อมูลสาขา",
                font=('Segoe UI', 12, 'bold'),
                fg='#1f2937', bg='#f0f9ff').pack(anchor='w', pady=(0, 3))
        
        if branch_detail:
            info_text = f"ชื่อ: {branch_detail.get('Name', '')}"
            tk.Label(branch_frame, text=info_text,
                    font=('Segoe UI', 9),
                    fg='#374151', bg='#f0f9ff',
                    wraplength=1000).pack(anchor='w')
        
        # Withdrawal table header
        tk.Label(card, text="รายการใบเบิกโอนที่เลือก",
                font=('Segoe UI', 12, 'bold'),
                fg='#1f2937', bg='white').pack(anchor='w', pady=(0, 5))
        
        # Table frame
        tree_frame = tk.Frame(card, bg='white')
        tree_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        style = ttk.Style()
        style.configure("Summary.Treeview", 
                    font=('Segoe UI', 10),
                    rowheight=25)
        style.configure("Summary.Treeview.Heading", 
                    font=('Segoe UI', 11, 'bold'))
        
        columns = ('No', 'WithdrawalNumber', 'WithdrawalDate', 'Total')
        
        summary_tree = ttk.Treeview(tree_frame, columns=columns, show='headings', 
                        style="Summary.Treeview")
        
        # Configure columns
        column_config = {
            'No': {'text': 'ลำดับ', 'width': 50, 'anchor': 'center'},
            'WithdrawalNumber': {'text': 'เลขที่ใบเบิกโอน', 'width': 150, 'anchor': 'center'},
            'WithdrawalDate': {'text': 'วันที่เบิกโอน', 'width': 120, 'anchor': 'center'},
            'Total': {'text': 'ยอดรวม (บาท)', 'width': 120, 'anchor': 'center'}
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
        
        summary_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Insert data
        total_amount = 0.0
        count = 0
        
        for item_id in self.selected_withdrawals:
            if item_id in self.withdrawal_items:
                withdrawal = self.withdrawal_items[item_id]
                count += 1
                
                try:
                    amount = float(str(withdrawal.get('Total', '0')).replace(',', ''))
                    total_amount += amount
                    formatted_amount = f"{amount:,.2f}"
                except:
                    formatted_amount = str(withdrawal.get('Total', '0'))
                
                summary_tree.insert('', 'end', values=(
                    count,
                    withdrawal.get('WithdrawalNumber', ''),
                    withdrawal.get('WithdrawalDate', ''),
                    formatted_amount
                ))
        
        # Summary section
        summary_frame = tk.Frame(card, bg='#fef3c7', padx=15, pady=10, relief='solid', bd=1)
        summary_frame.pack(fill='x', pady=(10, 15))
        
        summary_left = tk.Frame(summary_frame, bg='#fef3c7')
        summary_left.pack(side='left')
        
        tk.Label(summary_left, text=f"เลือกแล้ว: {count} รายการ",
                font=('Segoe UI', 11, 'bold'),
                fg='#10b981', bg='#fef3c7').pack(side='left')
        
        summary_right = tk.Frame(summary_frame, bg='#fef3c7')
        summary_right.pack(side='right')
        
        tk.Label(summary_right, text=f"ยอดรวม: {total_amount:,.2f} บาท",
                font=('Segoe UI', 11, 'bold'),
                fg='#dc2626', bg='#fef3c7').pack(side='right')
        
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
                            
    def get_branch_detail(self):
        """ดึงข้อมูลสาขาแบบละเอียด"""
        try:
            branch_name = self.selected_branch.get('BranchName')
            return self.db.get_branch_detail(branch_name)
        except Exception as e:
            print(f"Error getting branch detail: {str(e)}")
            return {}
    
    def create_billing_document(self):
        try:
            branch_name = self.selected_branch.get('BranchName')
            created_by = self.user_data.get('username', 'Unknown')
            
            # ดึงเลขที่ใบเบิกโอนจริงจาก selected_withdrawals
            actual_withdrawal_numbers = []
            for item_id in self.selected_withdrawals:
                if item_id in self.withdrawal_items:
                    withdrawal_number = self.withdrawal_items[item_id].get('WithdrawalNumber', '')
                    if withdrawal_number:
                        actual_withdrawal_numbers.append(str(withdrawal_number))
            
            if not actual_withdrawal_numbers:
                messagebox.showerror("ข้อผิดพลาด", "ไม่พบรายการใบเบิกโอนที่เลือก", parent=self.window)
                return
            
            print(f"Creating billing for Branch: {branch_name}")
            print(f"Withdrawal numbers: {actual_withdrawal_numbers}")
            print(f"Created by: {created_by}")
            
            #เพิ่มการยืนยันก่อนสร้าง
            confirm = messagebox.askyesno(
                "ยืนยันการสร้างเอกสาร",
                f"ต้องการสร้างใบวางบิลขายสาขาหรือไม่?\n\n"
                f"ชื่อสาขา: {self.selected_branch.get('BranchName', '')}\n"
                f"จำนวนรายการ: {len(actual_withdrawal_numbers)} รายการ\n\n"
                f"กดยืนยันเพื่อดำเนินการต่อ",
                icon='question',
                parent=self.window
            )
            
            if not confirm:  # ถ้ากด No ให้หยุดทำงาน
                return

            
            billing_doc_no = self.db.create_billing_document(
                branch_name=branch_name,
                withdrawal_numbers=actual_withdrawal_numbers,
                created_by=created_by
            )
            
            if billing_doc_no:
                response = messagebox.askyesno(
                    "สำเร็จ", 
                    f"สร้างใบวางบิลสาขาเรียบร้อยแล้ว\nเลขที่เอกสาร: {billing_doc_no}\n\nคุณต้องการแสดงตัวอย่างใบวางบิลหรือไม่?",
                    icon='question',
                    parent=self.window
                )
                
                if response:
                    self.show_billing_template(billing_doc_no, branch_name, actual_withdrawal_numbers)
                
                self.reset_form()
            else:
                messagebox.showerror("ข้อผิดพลาด", "ไม่สามารถสร้างใบวางบิลสาขาได้", parent=self.window)
                
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"เกิดข้อผิดพลาด: {str(e)}", parent=self.window)
            print(f"Error in create_billing_document: {str(e)}")
            import traceback
            traceback.print_exc()
            
    def show_billing_template(self, billing_doc_no, branch_name, withdrawal_numbers):
            """แสดงตัวอย่างใบวางบิลด้วยข้อมูลจริง"""
            try:
                from billing_note_generator import BillingNoteGenerator
                
                template_data = self.prepare_template_data(billing_doc_no, branch_name, withdrawal_numbers)
                
                generator = BillingNoteGenerator(template_type='branch')
                generator.preview_in_browser(template_data)
                
            except ImportError as e:
                messagebox.showerror("ข้อผิดพลาด", f"ไม่พบ BillingNoteGenerator: {str(e)}")
            except Exception as e:
                messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถแสดงตัวอย่างได้: {str(e)}")
                print(f"Error showing template: {str(e)}")
                import traceback
                traceback.print_exc()
                        
    def prepare_template_data(self, billing_doc_no, branch_name, withdrawal_numbers):
        """เตรียมข้อมูลสำหรับ template"""
        try:
            branch_detail = self.db.get_branch_detail(branch_name)
            
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
            
            total_amount = 0.0
            first_item = None
            additional_items = []
            
            order = 1
            for item_id in self.selected_withdrawals:
                if item_id in self.withdrawal_items:
                    withdrawal = self.withdrawal_items[item_id]
                    
                    withdrawal_date = withdrawal.get('WithdrawalDate', '')[:10] if len(withdrawal.get('WithdrawalDate', '')) > 10 else withdrawal.get('WithdrawalDate', '')
                    if withdrawal_date:
                        try:
                            date_obj = datetime.strptime(withdrawal_date, '%Y-%m-%d')
                            withdrawal_date = date_obj.strftime('%d/%m/%Y')
                        except:
                            pass
                    
                    try:
                        amount = float(str(withdrawal.get('Total', '0')).replace(',', ''))
                        total_amount += amount
                        formatted_amount = f"{amount:,.2f}"
                    except:
                        amount = 0.0
                        formatted_amount = "0.00"
                    
                    item_data = {
                        'order': order,
                        'type': 'ใบเบิกโอน',
                        'withdrawalNo': withdrawal.get('WithdrawalNumber', ''),
                        'date': withdrawal_date,
                        'total': formatted_amount
                    }
                    
                    if order == 1:
                        first_item = item_data
                    else:
                        additional_items.append(item_data)
                    
                    order += 1
            
            thai_baht_text = self.number_to_thai(total_amount)
            
            template_data = {
                'DocumentTitle': 'ใบวางบิลสาขา',
                
                'Companyname': company_data.get('Companyname', 'ไม่พบข้อมูล'),
                'SiteAddress': company_data.get('SiteAddress', 'ไม่พบข้อมูล'),
                'PhoneNumber': company_data.get('PhoneNumber', 'ไม่พบข้อมูล'),
                'TaxId': company_data.get('TaxId', 'ไม่พบข้อมูล'),
                'SitePicture': company_data.get('SitePicture', ''),
                
                'BranchName': branch_detail.get('Name', ''),
                'BranchAddress': branch_detail.get('full_address', ''),
                'PhoneMobile': branch_detail.get('PhoneMobile', ''),
                
                'DocNo': billing_doc_no,
                'DocDate': datetime.now().strftime('%d/%m/%Y'),
                
                'WithdrawalNumber': first_item['withdrawalNo'] if first_item else '',
                'WithdrawalDate': first_item['date'] if first_item else '',
                'Total': first_item['total'] if first_item else '0.00',
                
                'TotalAmount': f"{total_amount:,.2f}",
                'TextThaiBaht': thai_baht_text,
                
                'additionalItems': additional_items
            }

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
            baht = int(amount)
            satang = int(round((amount - baht) * 100))
            
            ones = ['', 'หนึ่ง', 'สอง', 'สาม', 'สี่', 'ห้า', 'หก', 'เจ็ด', 'แปด', 'เก้า']
            
            def convert_group(num):
                result = ''
                hundred = num // 100
                if hundred > 0:
                    result += ones[hundred] + 'ร้อย'
                
                ten = (num % 100) // 10
                if ten > 0:
                    if ten == 1:
                        result += 'สิบ'
                    elif ten == 2:
                        result += 'ยี่สิบ'
                    else:
                        result += ones[ten] + 'สิบ'
                
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
                
                million = baht // 1000000
                if million > 0:
                    result += convert_group(million) + 'ล้าน'
                
                hundred_thousand = (baht % 1000000) // 100000
                if hundred_thousand > 0:
                    result += convert_group(hundred_thousand) + 'แสน'
                
                ten_thousand = (baht % 100000) // 10000
                if ten_thousand > 0:
                    result += convert_group(ten_thousand) + 'หมื่น'
                
                thousand = (baht % 10000) // 1000
                if thousand > 0:
                    result += convert_group(thousand) + 'พัน'
                
                remainder = baht % 1000
                if remainder > 0:
                    result += convert_group(remainder)
                
                result += 'บาท'
            
            if satang > 0:
                result += convert_group(satang) + 'สตางค์'
            else:
                result += 'ถ้วน'
            
            return result
            
        except Exception as e:
            return f'(จำนวนเงิน {amount:,.2f} บาท)'
                            
    def reset_form(self):
        self.selected_branch = None
        self.selected_withdrawals = set()
        self.selected_withdrawal_numbers = set()
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
    root.withdraw()
    
    user_data = {"username": "admin", "role": "admin"}
    app = BranchBillUI(root, user_data)
    
    root.mainloop()