import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime, timedelta
from BranchBill_database import BranchBillDatabase
from tkcalendar import DateEntry

class BranchBillHistoryUI:
    def __init__(self, parent, user_data):
        self.parent = parent
        self.user_data = user_data
        self.window = tk.Toplevel(parent)
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
        
        self.selected_billing_doc = None
        self.create_ui()
        self.load_billing_history()
        
    def setup_window(self):
        self.window.title("ประวัติใบวางบิลสาขา - DocFlow Manager")
        self.window.geometry("1400x800")
        self.window.configure(bg='#f8fafc')
        self.center_window()
        self.create_header()
        
    def center_window(self):
        self.window.update_idletasks()
        width = 1400
        height = 800
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_header(self):
        header = tk.Frame(self.window, bg='#1f2937', height=80)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        header_content = tk.Frame(header, bg='#1f2937')
        header_content.pack(fill='both', expand=True, padx=30, pady=15)
        
        left_frame = tk.Frame(header_content, bg='#1f2937')
        left_frame.pack(side='left', fill='y')
        
        tk.Label(left_frame, text="ประวัติใบวางบิลสาขา", 
                font=('Segoe UI', 18, 'bold'), 
                fg='white', bg='#1f2937').pack(anchor='w')
        
        tk.Label(left_frame, text="ดูประวัติและพิมพ์ซ้ำใบวางบิลสาขา", 
                font=('Segoe UI', 9), 
                fg='#d1d5db', bg='#1f2937').pack(anchor='w')
        
        right_frame = tk.Frame(header_content, bg='#1f2937')
        right_frame.pack(side='right', fill='y')
        
        tk.Label(right_frame, text=f"{self.user_data['username']}", 
               font=('Segoe UI', 11), 
               fg='white', bg='#1f2937').pack(anchor='e')
        
        close_btn = tk.Button(right_frame, text="ปิดหน้าต่าง",
                             font=('Segoe UI', 9),
                             bg='#ef4444', fg='white',
                             border=0, padx=15, pady=6,
                             cursor='hand2',
                             command=self.close_window)
        close_btn.pack(anchor='e', pady=(5, 0))
    
    def create_ui(self):
        content = tk.Frame(self.window, bg='#f8fafc')
        content.pack(fill='both', expand=True, padx=20, pady=10)
        
        card = tk.Frame(content, bg='white', padx=20, pady=15)
        card.pack(expand=True, fill='both')
        
        # Search and filter section
        filter_frame = tk.Frame(card, bg='white')
        filter_frame.pack(fill='x', pady=(0, 15))
        
        # Search box
        search_frame = tk.Frame(filter_frame, bg='white')
        search_frame.pack(side='left', fill='x', expand=True)
        
        tk.Label(search_frame, text="ค้นหา:",
                font=('Segoe UI', 10),
                fg='#374151', bg='white').pack(side='left', padx=(0, 5))
        
        search_container = tk.Frame(search_frame, bg='#f9fafb', relief='solid', bd=1)
        search_container.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        self.search_entry = tk.Entry(search_container, font=('Segoe UI', 10),
                                    bg='#f9fafb', fg='#374151',
                                    border=0, insertbackground='#10b981')
        self.search_entry.pack(side='left', fill='x', expand=True, padx=8, pady=6)
        self.search_entry.bind('<KeyRelease>', self.search_history)
        
        search_btn = tk.Button(search_container, text="ค้นหา",
                              font=('Segoe UI', 10),
                              bg='#10b981', fg='white',
                              border=0, padx=8,
                              cursor='hand2',
                              command=self.search_history)
        search_btn.pack(side='right', fill='y')
        
        # Date filter
        date_frame = tk.Frame(filter_frame, bg='white')
        date_frame.pack(side='right')

        tk.Label(date_frame, text="ช่วงวันที่:",
                font=('Segoe UI', 10),
                fg='#374151', bg='white').pack(side='left', padx=(0, 5))

        self.date_from = DateEntry(date_frame, 
                                font=('Segoe UI', 10), 
                                width=12,
                                background='#3b82f6',
                                foreground='white',
                                borderwidth=2,
                                date_pattern='yyyy-mm-dd',
                                locale='th_TH')
        self.date_from.pack(side='left', padx=(0, 5))
        self.date_from.set_date(datetime.now() - timedelta(days=30))

        tk.Label(date_frame, text="ถึง",
                font=('Segoe UI', 10),
                fg='#374151', bg='white').pack(side='left', padx=(5, 5))

        self.date_to = DateEntry(date_frame, 
                                font=('Segoe UI', 10), 
                                width=12,
                                background='#3b82f6',
                                foreground='white',
                                borderwidth=2,
                                date_pattern='yyyy-mm-dd',
                                locale='th_TH')
        self.date_to.pack(side='left', padx=(0, 10))
        self.date_to.set_date(datetime.now())

        refresh_btn = tk.Button(date_frame, text="รีเฟรช",
                            font=('Segoe UI', 9),
                            bg='#3b82f6', fg='white',
                            border=0, padx=10, pady=4,
                            cursor='hand2',
                            command=self.load_billing_history)
        refresh_btn.pack(side='right')        
        
        # Main table
        table_frame = tk.Frame(card, bg='white')
        table_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        # Treeview
        style = ttk.Style()
        style.configure("History.Treeview", 
                       font=('Segoe UI', 10),
                       rowheight=25)
        style.configure("History.Treeview.Heading", 
                       font=('Segoe UI', 11, 'bold'))
        
        columns = ('BillingDocNumber', 'CreateDate', 'BranchName', 'TotalAmount', 'TotalItems', 'CreatedBy', 'Status')
        
        self.history_tree = ttk.Treeview(table_frame, columns=columns, show='headings', 
                                        style="History.Treeview")
        
        # Configure columns
        column_config = {
            'BillingDocNumber': {'text': 'เลขที่เอกสาร', 'width': 120, 'anchor': 'center'},
            'CreateDate': {'text': 'วันที่สร้าง', 'width': 120, 'anchor': 'center'},
            'BranchName': {'text': 'ชื่อสาขา', 'width': 200, 'anchor': 'w'},
            'TotalAmount': {'text': 'ยอดรวม (บาท)', 'width': 100, 'anchor': 'e'},
            'TotalItems': {'text': 'จำนวนรายการ', 'width': 100, 'anchor': 'center'},
            'CreatedBy': {'text': 'ผู้สร้าง', 'width': 100, 'anchor': 'center'},
            'Status': {'text': 'สถานะ', 'width': 80, 'anchor': 'center'}
        }
        
        for col in columns:
            self.history_tree.heading(col, text=column_config[col]['text'], anchor='center')
            self.history_tree.column(col, 
                                   width=column_config[col]['width'], 
                                   minwidth=50,
                                   anchor=column_config[col]['anchor'])
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=self.history_tree.yview)
        h_scrollbar = ttk.Scrollbar(table_frame, orient='horizontal', command=self.history_tree.xview)
        self.history_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        self.history_tree.pack(side='left', fill='both', expand=True)
        v_scrollbar.pack(side='right', fill='y')
        h_scrollbar.pack(side='bottom', fill='x')
        
        # Bind events
        self.history_tree.bind('<Double-1>', self.on_item_double_click)
        self.history_tree.bind('<Button-1>', self.on_item_select)
        
        # Action buttons
        action_frame = tk.Frame(card, bg='white')
        action_frame.pack(fill='x')
        
        left_buttons = tk.Frame(action_frame, bg='white')
        left_buttons.pack(side='left')

        view_btn = tk.Button(left_buttons, text="ดูรายละเอียด",
                            font=('Segoe UI', 10),
                            bg='#3b82f6', fg='white',
                            border=0, padx=15, pady=8,
                            cursor='hand2',
                            command=self.view_details)
        view_btn.pack(side='left', padx=(0, 10))
        
        print_btn = tk.Button(left_buttons, text="พิมพ์ซ้ำ",
                    font=('Segoe UI', 10),
                    bg='#10b981', fg='white',
                    border=0, padx=15, pady=8,
                    cursor='hand2',
                    command=self.reprint_document)
        print_btn.pack(side='left', padx=(0, 10))

        cancel_btn = tk.Button(left_buttons, text="ยกเลิกใบวางบิล",
                            font=('Segoe UI', 10),
                            bg='#ef4444', fg='white',
                            border=0, padx=15, pady=8,
                            cursor='hand2',
                            command=self.cancel_document)
        cancel_btn.pack(side='left')
        
        self.status_label = tk.Label(action_frame, text="เลือกรายการเพื่อดูรายละเอียด",
                                   font=('Segoe UI', 10),
                                   fg='#6b7280', bg='white')
        self.status_label.pack(side='right')
    
    def load_billing_history(self):
        """โหลดประวัติใบวางบิล"""
        try:
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            
            date_from = self.date_from.get_date().strftime('%Y-%m-%d') + ' 00:00:00'
            date_to = self.date_to.get_date().strftime('%Y-%m-%d') + ' 23:59:59'
            
            billing_history = self.db.get_billing_history(date_from, date_to)
            
            for billing in billing_history:
                create_date = billing.get('CreateDate', '')
                if isinstance(create_date, datetime):
                    create_date_str = create_date.strftime('%d/%m/%Y')
                else:
                    create_date_str = str(create_date)[:10] if create_date else ''
                
                try:
                    amount = float(billing.get('TotalAmount', 0))
                    amount_str = f"{amount:,.2f}"
                except:
                    amount_str = str(billing.get('TotalAmount', '0'))
                
                status = billing.get('Status', '')
                
                item_id = self.history_tree.insert('', 'end', values=(
                    billing.get('BillingDocNumber', ''),
                    create_date_str,
                    billing.get('BranchName', ''),
                    amount_str,
                    billing.get('TotalItems', ''),
                    billing.get('CreatedBy', ''),
                    status
                ))
                
                if status == 'InActive':
                    self.history_tree.item(item_id, tags=('cancelled',))
            
            self.history_tree.tag_configure('cancelled', foreground='#ef4444')
            
            self.status_label.config(text=f"โหลดข้อมูล {len(billing_history)} รายการ")
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถโหลดประวัติได้: {str(e)}")

    def search_history(self, event=None):
        """ค้นหาประวัติ"""
        search_term = self.search_entry.get().strip()
        
        try:
            date_from = self.date_from.get_date().strftime('%Y-%m-%d') + ' 00:00:00'
            date_to = self.date_to.get_date().strftime('%Y-%m-%d') + ' 23:59:59'
            
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
            
            billing_history = self.db.search_billing_history(search_term, date_from, date_to)
            
            for billing in billing_history:
                create_date = billing.get('CreateDate', '')
                if isinstance(create_date, datetime):
                    create_date_str = create_date.strftime('%d/%m/%Y')
                else:
                    create_date_str = str(create_date)[:10] if create_date else ''
                
                try:
                    amount = float(billing.get('TotalAmount', 0))
                    amount_str = f"{amount:,.2f}"
                except:
                    amount_str = str(billing.get('TotalAmount', '0'))
                
                status = billing.get('Status', '')
                
                item_id = self.history_tree.insert('', 'end', values=(
                    billing.get('BillingDocNumber', ''),
                    create_date_str,
                    billing.get('BranchName', ''),
                    amount_str,
                    billing.get('TotalItems', ''),
                    billing.get('CreatedBy', ''),
                    status
                ))
                
                if status == 'InActive':
                    self.history_tree.item(item_id, tags=('cancelled',))
            
            self.history_tree.tag_configure('cancelled', foreground='#ef4444')
            
            self.status_label.config(text=f"พบข้อมูล {len(billing_history)} รายการ")
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถค้นหาได้: {str(e)}")
                                    
    def on_item_select(self, event):
        """เมื่อเลือกรายการ"""
        self.history_tree.after(10, self._update_selection)

    def _update_selection(self):
        """อัพเดท selection หลังจากเลือกเสร็จ"""
        selected_item = self.history_tree.selection()
        if selected_item:
            values = self.history_tree.item(selected_item[0])['values']
            if values:
                billing_doc_number = values[0]
                branch_name = values[2]
                self.selected_billing_doc = billing_doc_number
                self.status_label.config(text=f"เลือก: {billing_doc_number} - {branch_name}")    
                
    def on_item_double_click(self, event):
        """เมื่อดับเบิลคลิก"""
        self.view_details()
    
    def view_details(self):
        """ดูรายละเอียดใบวางบิล"""
        if not self.selected_billing_doc:
            messagebox.showwarning("คำเตือน", "กรุณาเลือกรายการที่ต้องการดู")
            return
        
        try:
            billing_detail = self.db.get_billing_detail(self.selected_billing_doc)
            billing_items = self.db.get_billing_items(self.selected_billing_doc)
            
            self.show_detail_window(billing_detail, billing_items)
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถดูรายละเอียดได้: {str(e)}")
    
    def show_detail_window(self, billing_detail, billing_items):
        """แสดงหน้าต่างรายละเอียด"""
        detail_window = tk.Toplevel(self.window)
        detail_window.title(f"รายละเอียดใบวางบิลสาขา - {billing_detail.get('BillingDocNumber', '')}")
        detail_window.geometry("900x600")
        detail_window.configure(bg='white')
        
        # Header
        header_frame = tk.Frame(detail_window, bg='#f0f9ff', padx=20, pady=15)
        header_frame.pack(fill='x')
        
        tk.Label(header_frame, text=f"เลขที่เอกสาร: {billing_detail.get('BillingDocNumber', '')}",
                font=('Segoe UI', 14, 'bold'),
                fg='#1f2937', bg='#f0f9ff').pack(anchor='w')
        
        tk.Label(header_frame, text=f"สาขา: {billing_detail.get('BranchName', '')}",
                font=('Segoe UI', 11),
                fg='#374151', bg='#f0f9ff').pack(anchor='w', pady=(5, 0))
        
        # Items table
        content_frame = tk.Frame(detail_window, bg='white', padx=20, pady=15)
        content_frame.pack(fill='both', expand=True)
        
        tk.Label(content_frame, text="รายการใบเบิกโอน",
                font=('Segoe UI', 12, 'bold'),
                fg='#1f2937', bg='white').pack(anchor='w', pady=(0, 10))
        
        # Items treeview
        items_columns = ('ItemOrder', 'WithdrawalNumber', 'WithdrawalDate', 'TotalAmount')
        items_tree = ttk.Treeview(content_frame, columns=items_columns, show='headings', height=10)
        
        items_tree.heading('ItemOrder', text='ลำดับ', anchor='center')
        items_tree.heading('WithdrawalNumber', text='เลขที่ใบเบิกโอน', anchor='center')
        items_tree.heading('WithdrawalDate', text='วันที่เบิกโอน', anchor='center')
        items_tree.heading('TotalAmount', text='ยอดรวม', anchor='center')
        
        items_tree.column('ItemOrder', width=60, anchor='center')
        items_tree.column('WithdrawalNumber', width=150, anchor='center')
        items_tree.column('WithdrawalDate', width=120, anchor='center')
        items_tree.column('TotalAmount', width=120, anchor='e')
        
        # Insert items
        for item in billing_items:
            withdrawal_date = str(item.get('WithdrawalDate', ''))[:10] if item.get('WithdrawalDate') else ''
            
            try:
                amount = float(item.get('TotalAmount', 0))
                amount_str = f"{amount:,.2f}"
            except:
                amount_str = str(item.get('TotalAmount', '0'))
            
            items_tree.insert('', 'end', values=(
                item.get('ItemOrder', ''),
                item.get('WithdrawalNumber', ''),
                withdrawal_date,
                amount_str
            ))
        
        items_tree.pack(fill='both', expand=True, pady=(0, 15))
        
        # Summary
        summary_frame = tk.Frame(content_frame, bg='#fef3c7', padx=15, pady=10)
        summary_frame.pack(fill='x', pady=(0, 15))
        
        total_amount = billing_detail.get('TotalAmount', 0)
        total_items = billing_detail.get('TotalItems', 0)
        
        tk.Label(summary_frame, text=f"รวม {total_items} รายการ | ยอดรวม {total_amount:,.2f} บาท",
                font=('Segoe UI', 12, 'bold'),
                fg='#dc2626', bg='#fef3c7').pack()
        
        # Close button
        tk.Button(content_frame, text="ปิด",
                 font=('Segoe UI', 10),
                 bg='#6b7280', fg='white',
                 border=0, padx=20, pady=8,
                 command=detail_window.destroy).pack()
        
    def reprint_document(self):
            """พิมพ์ซ้ำเอกสาร"""
            if not self.selected_billing_doc:
                messagebox.showwarning("คำเตือน", "กรุณาเลือกรายการที่ต้องการพิมพ์ซ้ำ")
                return
            
            try:
                billing_detail = self.db.get_billing_detail(self.selected_billing_doc)
                
                if not billing_detail:
                    messagebox.showerror("ข้อผิดพลาด", "ไม่พบข้อมูลเอกสาร")
                    return
                
                status = billing_detail.get('Status', '')
                if status == 'InActive':
                    messagebox.showwarning(
                        "ไม่สามารถพิมพ์ได้", 
                        f"เอกสาร {self.selected_billing_doc} ถูกยกเลิกแล้ว\n\nไม่สามารถพิมพ์ซ้ำเอกสารที่ยกเลิกได้"
                    )
                    return
                
                billing_items = self.db.get_billing_items(self.selected_billing_doc)
                
                template_data = self.prepare_reprint_data(billing_detail, billing_items)
                
                from billing_note_generator import BillingNoteGenerator
                BillingNoteGenerator.Preview_Template_With_Data(template_data, 'branch')
                
            except ImportError:
                messagebox.showerror("ข้อผิดพลาด", "ไม่พบ BillingNoteGenerator")
            except Exception as e:
                messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถพิมพ์ซ้ำได้: {str(e)}")
                import traceback
                traceback.print_exc()
                    
    def prepare_reprint_data(self, billing_detail, billing_items):
        """เตรียมข้อมูลสำหรับพิมพ์ซ้ำ"""
        
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
        
        total_amount = billing_detail.get('TotalAmount', 0)
        
        additional_items = []
        first_item = None
        
        for i, item in enumerate(billing_items):
            withdrawal_date = str(item.get('WithdrawalDate', ''))[:10] if item.get('WithdrawalDate') else ''
            
            if withdrawal_date:
                try:
                    date_obj = datetime.strptime(withdrawal_date, '%Y-%m-%d')
                    withdrawal_date = date_obj.strftime('%d/%m/%Y')
                except:
                    pass
            
            try:
                amount = float(item.get('TotalAmount', 0))
                amount_str = f"{amount:,.2f}"
            except:
                amount_str = "0.00"
            
            item_data = {
                'order': i + 1,
                'type': 'ใบเบิกโอน',
                'withdrawalNo': item.get('WithdrawalNumber', ''),
                'date': withdrawal_date,
                'total': amount_str
            }
            
            if i == 0:
                first_item = item_data
            else:
                additional_items.append(item_data)
        
        doc_date = str(billing_detail.get('CreateDate', ''))[:10] if billing_detail.get('CreateDate') else ''
        if doc_date:
            try:
                date_obj = datetime.strptime(doc_date, '%Y-%m-%d')
                doc_date = date_obj.strftime('%d/%m/%Y')
            except:
                pass
        
        thai_baht_text = self.number_to_thai(total_amount)
        
        template_data = {
            'DocumentTitle': 'ใบวางบิลสาขา',
            
            'Companyname': company_data.get('Companyname', ''),
            'SiteAddress': company_data.get('SiteAddress', ''),
            'PhoneNumber': company_data.get('PhoneNumber', ''),
            'TaxId': company_data.get('TaxId', ''),
            'SitePicture': company_data.get('SitePicture', ''),
            
            'BranchName': billing_detail.get('BranchName', ''),
            'BranchAddress': billing_detail.get('BranchAddress', ''),
            'PhoneMobile': billing_detail.get('BranchPhone', ''),
            
            'DocNo': billing_detail.get('BillingDocNumber', ''),
            'DocDate': doc_date,
            
            'WithdrawalNumber': first_item['withdrawalNo'] if first_item else '',
            'WithdrawalDate': first_item['date'] if first_item else '',
            'Total': first_item['total'] if first_item else '0.00',
            
            'TotalAmount': f"{total_amount:,.2f}",
            'TextThaiBaht': thai_baht_text,
            
            'additionalItems': additional_items
        }
        
        return template_data

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
            
    def cancel_document(self):
        """ยกเลิกใบวางบิล"""
        if not self.selected_billing_doc:
            messagebox.showwarning("คำเตือน", "กรุณาเลือกรายการที่ต้องการยกเลิก")
            return
        
        response = messagebox.askyesno(
            "ยืนยันการยกเลิก",
            f"คุณต้องการยกเลิกใบวางบิลสาขา {self.selected_billing_doc} หรือไม่?\n\n"
            f"การยกเลิกจะทำให้:\n"
            f"• เอกสารใบวางบิลถูกปิดการใช้งาน\n"
            f"• รายการใบเบิกโอนกลับมาเป็นสถานะ 'ยังไม่ได้วางบิล'\n\n"
            f"⚠️ การดำเนินการนี้ไม่สามารถย้อนกลับได้",
            icon='warning'
        )
        
        if not response:
            return
        
        try:
            success, message = self.db.cancel_billing_document(self.selected_billing_doc)
            
            if success:
                messagebox.showinfo("สำเร็จ", message)
                self.load_billing_history()
                self.selected_billing_doc = None
                self.status_label.config(text="เลือกรายการเพื่อดูรายละเอียด")
            else:
                messagebox.showerror("ข้อผิดพลาด", message)
                
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถยกเลิกได้: {str(e)}")
            
    def close_window(self):
        try:
            self.db.close_connection()
        except:
            pass
        self.window.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    
    user_data = {"username": "admin", "role": "admin"}
    app = BranchBillHistoryUI(root, user_data)
    
    root.mainloop()