import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import pandas as pd
from typing import Optional
import threading
from excel_manager_database import ExcelManagerDatabase
from utils import set_window_icon

class ExcelManagerUI:
    """UI สำหรับจัดการ Import Excel"""
    
    def __init__(self, parent, user_data, receive_id=None, supplier_id=30):
        self.parent = parent
        self.user_data = user_data
        self.receive_id = receive_id  # ถ้ามี = import เข้า receive ที่มีอยู่, ถ้าไม่มี = สร้างใหม่
        self.supplier_id = supplier_id  # รหัสซัพพลายเออร์ (default = 30)
        self.window = tk.Toplevel(parent)
        set_window_icon(self.window)
        
        # Initialize variables
        self.import_file_path = None
        self.import_data = None
        self.validation_result = None
        
        self.setup_window()
        
        # Initialize database
        try:
            self.db = ExcelManagerDatabase()
            if not self.db.test_connection():
                messagebox.showerror("ข้อผิดพลาด", "ไม่สามารถเชื่อมต่อฐานข้อมูลได้")
                self.window.destroy()
                return
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ข้อผิดพลาดฐานข้อมูล: {str(e)}")
            self.window.destroy()
            return
        
        self.create_ui()
        
    def setup_window(self):
        """ตั้งค่าหน้าต่าง"""
        self.window.title("นำเข้าข้อมูล Excel")
        self.window.state('zoomed')
        self.window.geometry("1200x700")
        self.window.configure(bg='#f8fafc')
        self.center_window()
        self.create_header()
        
    def center_window(self):
        """จัดหน้าต่างให้อยู่กลางจอ"""
        self.window.update_idletasks()
        width = 1200
        height = 700
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f"{width}x{height}+{x}+{y}")
    
    def create_header(self):
        """สร้าง Header"""
        header = tk.Frame(self.window, bg='#1f2937', height=80)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        header_content = tk.Frame(header, bg='#1f2937')
        header_content.pack(fill='both', expand=True, padx=30, pady=15)
        
        # Left side
        left_frame = tk.Frame(header_content, bg='#1f2937')
        left_frame.pack(side='left', fill='y')
        
        if self.receive_id:
            title = f"นำเข้าข้อมูล Excel - ใบรับสินค้า #{self.receive_id}"
        else:
            title = "นำเข้าข้อมูล Excel - สร้างใบรับสินค้าใหม่"
        
        tk.Label(left_frame, text=title, 
                font=('Segoe UI', 18, 'bold'), 
                fg='white', bg='#1f2937').pack(anchor='w')
        
        tk.Label(left_frame, text="นำเข้าข้อมูลจากไฟล์ Excel เข้าสู่ระบบ", 
                font=('Segoe UI', 9), 
                fg='#d1d5db', bg='#1f2937').pack(anchor='w')
        
        # Right side
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
        """สร้าง UI หลัก"""
        # Main content
        content = tk.Frame(self.window, bg='#f8fafc')
        content.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Card container
        card = tk.Frame(content, bg='white', padx=25, pady=20)
        card.pack(expand=True, fill='both')
        
        # Instructions section
        instruction_frame = tk.Frame(card, bg='#eff6ff', padx=20, pady=15)
        instruction_frame.pack(fill='x', pady=(0, 20))
        
        # tk.Label(instruction_frame, text="📋 วิธีการใช้งาน",
        #         font=('Segoe UI', 11, 'bold'),
        #         fg='#1e40af', bg='#eff6ff').pack(anchor='w')
        
        # instructions = [
        #     "1. กดปุ่ม 'ดาวน์โหลด Template' เพื่อดาวน์โหลดไฟล์ตัวอย่าง",
        #     "2. กรอกข้อมูลลงในไฟล์ Excel ตาม Template",
        #     "3. กดปุ่ม 'เลือกไฟล์ Excel' เพื่ออัพโหลดไฟล์",
        #     "4. ตรวจสอบข้อมูลในตารางด้านล่าง",
        #     "5. กดปุ่ม 'ตรวจสอบข้อมูล' เพื่อตรวจสอบความถูกต้อง",
        #     "6. กดปุ่ม 'Import ข้อมูล' เพื่อนำเข้าข้อมูลเข้าระบบ"
        # ]
        
        # for inst in instructions:
        #     tk.Label(instruction_frame, text=inst,
        #             font=('Segoe UI', 9),
        #             fg='#374151', bg='#eff6ff',
        #             justify='left', anchor='w').pack(anchor='w', pady=2)
        
        # File selection section
        file_section = tk.LabelFrame(card, text="เลือกไฟล์ Excel",
                                    font=('Segoe UI', 11, 'bold'),
                                    bg='white', fg='#1f2937',
                                    padx=15, pady=15)
        file_section.pack(fill='x', pady=(0, 15))
        
        file_frame = tk.Frame(file_section, bg='white')
        file_frame.pack(fill='x')
        
        # File path display
        file_display_frame = tk.Frame(file_frame, bg='#f9fafb', relief='solid', bd=1)
        file_display_frame.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        self.import_file_label = tk.Label(file_display_frame,
                                          text="📁 ยังไม่ได้เลือกไฟล์...",
                                          font=('Segoe UI', 10),
                                          fg='#9ca3af', bg='#f9fafb',
                                          anchor='w', padx=15, pady=10)
        self.import_file_label.pack(fill='both', expand=True)
        
        # Download template button
        download_btn = tk.Button(file_frame, text="📥 ดาวน์โหลด Template",
                                font=('Segoe UI', 10),
                                bg='#3b82f6', fg='white',
                                border=0, padx=20, pady=10,
                                cursor='hand2',
                                command=self.download_template)
        download_btn.pack(side='right', padx=(0, 10))
        
        # Browse button
        browse_btn = tk.Button(file_frame, text="📂 เลือกไฟล์",
                              font=('Segoe UI', 10),
                              bg='#10b981', fg='white',
                              border=0, padx=25, pady=10,
                              cursor='hand2',
                              command=self.browse_import_file)
        browse_btn.pack(side='right')
        
        # Preview section
        preview_section = tk.LabelFrame(card, text="ตัวอย่างข้อมูล",
                                       font=('Segoe UI', 11, 'bold'),
                                       bg='white', fg='#1f2937',
                                       padx=15, pady=15)
        preview_section.pack(fill='both', expand=True, pady=(0, 15))
        
        # Info and progress frame
        info_progress_frame = tk.Frame(preview_section, bg='white')
        info_progress_frame.pack(fill='x', pady=(0, 10))
        
        self.preview_info_label = tk.Label(info_progress_frame,
                                           text="เลือกไฟล์เพื่อแสดงตัวอย่างข้อมูล",
                                           font=('Segoe UI', 10),
                                           fg='#6b7280', bg='white')
        self.preview_info_label.pack(side='left')
        
        # Progress bar (ซ่อนไว้ก่อน)
        self.progress_frame = tk.Frame(info_progress_frame, bg='white')
        self.progress_frame.pack(side='right', fill='x', expand=True, padx=(20, 0))
        
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            mode='determinate',
            length=300
        )
        self.progress_bar.pack(side='left', fill='x', expand=True, padx=(0, 10))
        
        self.progress_label = tk.Label(self.progress_frame,
                                       text="0/0",
                                       font=('Segoe UI', 9),
                                       fg='#6b7280', bg='white')
        self.progress_label.pack(side='right')
        
        # ซ่อน progress ตอนเริ่มต้น
        self.progress_frame.pack_forget()
        
        # Preview frame with scrollbar
        preview_container = tk.Frame(preview_section, bg='white')
        preview_container.pack(fill='both', expand=True)
        
        # Treeview for preview
        style = ttk.Style()
        style.configure("Import.Treeview",
                       font=('Segoe UI', 9),
                       rowheight=28)
        style.configure("Import.Treeview.Heading",
                       font=('Segoe UI', 10, 'bold'))
        
        self.import_preview_tree = ttk.Treeview(preview_container,
                                               style="Import.Treeview",
                                               show='headings',
                                               height=12)
        
        v_scrollbar = ttk.Scrollbar(preview_container, orient='vertical',
                                   command=self.import_preview_tree.yview)
        h_scrollbar = ttk.Scrollbar(preview_container, orient='horizontal',
                                   command=self.import_preview_tree.xview)
        
        self.import_preview_tree.configure(yscrollcommand=v_scrollbar.set,
                                          xscrollcommand=h_scrollbar.set)
        
        self.import_preview_tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        preview_container.grid_rowconfigure(0, weight=1)
        preview_container.grid_columnconfigure(0, weight=1)
        
        # Validation result
        validation_frame = tk.Frame(preview_section, bg='white')
        validation_frame.pack(fill='x', pady=(10, 0))
        
        self.import_validation_label = tk.Label(validation_frame,
                                               text="",
                                               font=('Segoe UI', 10),
                                               fg='#374151', bg='white',
                                               justify='left', anchor='w')
        self.import_validation_label.pack(fill='x')
        
        # Action buttons
        action_frame = tk.Frame(card, bg='white')
        action_frame.pack(fill='x', pady=(0, 10))
        
        # Left buttons
        left_buttons = tk.Frame(action_frame, bg='white')
        left_buttons.pack(side='left')
        
        clear_btn = tk.Button(left_buttons, text="🗑️ ล้างข้อมูล",
                             font=('Segoe UI', 10),
                             bg='#6b7280', fg='white',
                             border=0, padx=20, pady=10,
                             cursor='hand2',
                             command=self.clear_data)
        clear_btn.pack(side='left', padx=(0, 10))
        
        validate_btn = tk.Button(left_buttons, text="✓ ตรวจสอบข้อมูล",
                                font=('Segoe UI', 10),
                                bg='#3b82f6', fg='white',
                                border=0, padx=20, pady=10,
                                cursor='hand2',
                                command=self.validate_import_data)
        validate_btn.pack(side='left')
        
        # Right button
        import_btn = tk.Button(action_frame, text="📤 Import ข้อมูล",
                              font=('Segoe UI', 11, 'bold'),
                              bg='#10b981', fg='white',
                              border=0, padx=35, pady=10,
                              cursor='hand2',
                              command=self.import_from_excel)
        import_btn.pack(side='right')
        
    def download_template(self):
        """ดาวน์โหลด template Excel สำหรับ ReceiveItem"""
        try:
            file_path = filedialog.asksaveasfilename(
                parent=self.window,
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                initialfile=f"Template_ReceiveItem_{datetime.now().strftime('%Y%m%d')}.xlsx"
            )
            
            if not file_path:
                return
            
            # Template สำหรับ ReceiveItem - 4 คอลัมน์
            template_data = {
                'ItemCode': ['260131', '260132', '260133'],
                'ItemDesc': ['รายละเอียดสินค้า 1', 'รายละเอียดสินค้า 2', 'รายละเอียดสินค้า 3'],
                'QtyReceived': [10, 20, 15],
                'UnitCost': [100.00, 250.50, 175.00]
            }
            
            df = pd.DataFrame(template_data)
            
            # สร้าง Excel with formatting
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='ReceiveItem')
                
                # Get workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets['ReceiveItem']
                
                # Set column widths
                worksheet.column_dimensions['A'].width = 15  # ItemCode
                worksheet.column_dimensions['B'].width = 35  # ItemDesc
                worksheet.column_dimensions['C'].width = 12  # QtyReceived
                worksheet.column_dimensions['D'].width = 12  # UnitCost
                
                # Add header style
                from openpyxl.styles import Font, PatternFill, Alignment
                
                header_fill = PatternFill(start_color='3b82f6', end_color='3b82f6', fill_type='solid')
                header_font = Font(bold=True, color='FFFFFF')
                
                for cell in worksheet[1]:
                    cell.fill = header_fill
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal='center', vertical='center')
            
            messagebox.showinfo(
                "สำเร็จ", 
                f"ดาวน์โหลด Template สำเร็จ!\n\n"
                f"ไฟล์: {file_path}\n\n"
                "คอลัมน์ที่ต้องกรอก:\n"
                "• ItemCode (รหัสสินค้า) *\n"
                "• ItemDesc (รายละเอียดสินค้า)\n"
                "• QtyReceived (จำนวนรับ) *\n"
                "• UnitCost (ราคาต้นทุน/หน่วย) *\n\n"
                "ระบบจะตรวจสอบ ItemCode กับฐานข้อมูล",
                parent=self.window
            )
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถดาวน์โหลด template ได้: {str(e)}")
    
    def browse_import_file(self):
        """เลือกไฟล์ Excel สำหรับ import"""
        file_path = filedialog.askopenfilename(
            parent=self.window,
            title="เลือกไฟล์ Excel",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            # อ่านไฟล์ Excel
            df = pd.read_excel(file_path)
            
            if df.empty:
                messagebox.showwarning("คำเตือน", "ไฟล์ Excel ไม่มีข้อมูล", parent=self.window)
                return
            
            # ตรวจสอบคอลัมน์ที่จำเป็น - เปลี่ยนเป็น 4 คอลัมน์
            required_columns = ['ItemCode', 'ItemDesc', 'QtyReceived', 'UnitCost']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                messagebox.showerror(
                    "ข้อผิดพลาด",
                    f"ไม่พบคอลัมน์ที่จำเป็น:\n" + "\n".join(missing_columns) + 
                    "\n\nกรุณาใช้ Template ที่ดาวน์โหลดจากระบบ\n"
                    "คอลัมน์ที่ต้องมี: ItemCode, ItemDesc, QtyReceived, UnitCost",
                    parent=self.window
                )
                return
            
            self.import_file_path = file_path
            self.import_data = df.to_dict('records')
            
            # แสดงชื่อไฟล์
            import os
            filename = os.path.basename(file_path)
            self.import_file_label.config(
                text=f"✓ {filename}",
                fg='#10b981'
            )
            
            # เริ่มกระบวนการตรวจสอบข้อมูล
            self.process_import_data()
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถอ่านไฟล์ได้: {str(e)}", parent=self.window)
    
    def process_import_data(self):
        """ประมวลผลและตรวจสอบข้อมูลจาก Excel"""
        # แสดง progress bar
        self.progress_frame.pack(side='right', fill='x', expand=True, padx=(20, 0))
        self.progress_bar['value'] = 0
        self.progress_bar['maximum'] = len(self.import_data)
        
        # แสดงข้อความ
        self.preview_info_label.config(
            text=f"กำลังตรวจสอบข้อมูล...",
            fg='#3b82f6'
        )
        
        # Clear preview
        self.import_preview_tree.delete(*self.import_preview_tree.get_children())
        
        # ใช้ threading เพื่อไม่ให้ UI แฟรีซ
        thread = threading.Thread(target=self.fetch_items_data, daemon=True)
        thread.start()
    
    def fetch_items_data(self):
        """ดึงข้อมูลสินค้าทีละรายการ (ทำงานใน background thread)"""
        enriched_data = []
        errors = []
        total = len(self.import_data)
        
        for idx, row in enumerate(self.import_data, 1):
            item_code = str(row.get('ItemCode', '')).strip()
            
            # อัพเดท progress bar
            self.window.after(0, self.update_progress, idx, total, item_code)
            
            if not item_code:
                errors.append(f"แถวที่ {idx}: ไม่พบรหัสสินค้า")
                row['_has_error'] = True  # ทำเครื่องหมายว่ามี error
                enriched_data.append(row)
                continue
            
            try:
                # ดึงข้อมูลจาก database จริง
                item_data = self.db.get_item_by_code(item_code, 0)
                
                if item_data:
                    # ดึงข้อมูลหน่วยหลักจาก ItemUnit
                    item_unit_id = item_data.get('ItemUnitId')
                    unit_name = ''
                    
                    if item_unit_id:
                        unit_data = self.db.get_item_unit_by_id(item_unit_id)
                        if unit_data:
                            unit_name = unit_data.get('ItemUnitName', '')
                    
                    # ดึงข้อมูลหน่วยรองจาก ItemUnit
                    item_unit_id2 = item_data.get('ItemUnitId2')
                    unit2_name = ''
                    unit2_multiply = 0
                    
                    if item_unit_id2:
                        unit2_data = self.db.get_item_unit_by_id(item_unit_id2)
                        if unit2_data:
                            unit2_name = unit2_data.get('ItemUnitName', '')
                            unit2_multiply = unit2_data.get('Multiply', 0)
                    
                    # เติมข้อมูลสินค้า
                    enriched_row = row.copy()
                    enriched_row.update({
                        'ItemId': item_data.get('ItemId'),
                        'CategoryName': item_data.get('CategoryName', ''),
                        'ItemCode': item_data.get('ItemCode', item_code),
                        # ลองใช้ฟิลด์ที่มีในตาราง Items
                        'ItemDesc': item_data.get('ItemName') or item_data.get('ItemDesc') or item_data.get('Description') or '',
                        'RetailPrice': item_data.get('RetailPrice', 0),
                        'ItemUnitInStock': item_data.get('UnitsInStock', 0),
                        'ItemUnitId': item_unit_id,
                        'ItemUnitId2': item_unit_id2,
                        'ItemUnitId2Name': unit2_name,  # ชื่อหน่วยรอง
                        'ItemUnitId2Multiply': unit2_multiply,  # ตัวคูณ
                        'ItemName': item_data.get('ItemName', ''),
                        'TaxId': item_data.get('TaxId', 1),
                        'TaxPercent': item_data.get('TaxPercent', 0),
                        'UnitName': unit_name,  # ชื่อหน่วยหลักจาก ItemUnit
                        '_has_error': False  # ไม่มี error
                    })
                    enriched_data.append(enriched_row)
                else:
                    errors.append(f"แถวที่ {idx}: ไม่พบรหัสสินค้า '{item_code}' ในระบบ")
                    row['_has_error'] = True  # ทำเครื่องหมายว่ามี error
                    enriched_data.append(row)
                    
            except Exception as e:
                errors.append(f"แถวที่ {idx}: เกิดข้อผิดพลาด - {str(e)}")
                row['_has_error'] = True  # ทำเครื่องหมายว่ามี error
                enriched_data.append(row)
        
        # เสร็จแล้ว อัพเดท UI
        self.window.after(0, self.finish_processing, enriched_data, errors)
    
    def update_progress(self, current, total, item_code):
        """อัพเดท progress bar"""
        self.progress_bar['value'] = current
        self.progress_label.config(text=f"{current}/{total}")
        self.preview_info_label.config(
            text=f"กำลังตรวจสอบ: {item_code} ({current}/{total})",
            fg='#3b82f6'
        )
        self.window.update_idletasks()
    
    def finish_processing(self, enriched_data, errors):
        """เสร็จสิ้นการประมวลผล"""
        # ซ่อน progress bar
        self.progress_frame.pack_forget()
        
        # บันทึกข้อมูลที่เติมแล้ว
        self.import_data = enriched_data
        
        # แสดง info
        if errors:
            self.preview_info_label.config(
                text=f"พบข้อมูล {len(self.import_data)} แถว - พบข้อผิดพลาด {len(errors)} รายการ",
                fg='#ef4444'
            )
            
            # แสดงข้อผิดพลาด
            if len(errors) <= 10:
                messagebox.showwarning(
                    "พบข้อผิดพลาด",
                    "พบข้อผิดพลาดในการตรวจสอบ:\n\n" + "\n".join(errors),
                    parent=self.window
                )
            else:
                messagebox.showwarning(
                    "พบข้อผิดพลาด",
                    f"พบข้อผิดพลาด {len(errors)} รายการ\n\n" + 
                    "\n".join(errors[:10]) + "\n\n...(และอื่นๆ)",
                    parent=self.window
                )
        else:
            self.preview_info_label.config(
                text=f"ตรวจสอบข้อมูลสำเร็จ - พบ {len(self.import_data)} รายการ",
                fg='#10b981'
            )
        
        # แสดง preview
        self.show_import_preview_with_items(enriched_data)
        
        # Clear validation
        self.import_validation_label.config(text="")
        self.validation_result = None
    
    def show_import_preview(self, df):
        """แสดงตัวอย่างข้อมูลที่จะ import (เดิม)"""
        # Clear existing
        self.import_preview_tree.delete(*self.import_preview_tree.get_children())
        
        # Set columns
        columns = list(df.columns)
        self.import_preview_tree['columns'] = columns
        
        for col in columns:
            self.import_preview_tree.heading(col, text=col, anchor='center')
            self.import_preview_tree.column(col, width=150, anchor='w', minwidth=100)
        
        # Insert data (แสดงทั้งหมด หรือ limit ที่ 100 แถวแรก)
        max_rows = min(100, len(df))
        
        for idx, row in df.head(max_rows).iterrows():
            values = [str(row[col]) if pd.notna(row[col]) else '' for col in columns]
            self.import_preview_tree.insert('', 'end', values=values)
        
        if len(df) > max_rows:
            # แสดงข้อความว่ามีข้อมูลเพิ่ม
            self.preview_info_label.config(
                text=f"พบข้อมูล {len(self.import_data)} แถว, {len(df.columns)} คอลัมน์ (แสดง {max_rows} แถวแรก)",
                fg='#374151'
            )
    
    def show_import_preview_with_items(self, data):
        """แสดงตัวอย่างข้อมูลพร้อมข้อมูลสินค้า"""
        # Clear existing
        self.import_preview_tree.delete(*self.import_preview_tree.get_children())
        
        # กำหนดคอลัมน์ที่ต้องการแสดง - เพิ่ม UnitCost
        display_columns = [
            'CategoryName',
            'ItemCode',
            'ItemDesc',
            'UnitCost',             # เพิ่มราคาทุน
            'RetailPrice',
            'ItemUnitInStock',
            'QtyReceived',
            'ItemUnitId2Name',
            'ItemUnitId2Multiply'
        ]
        
        self.import_preview_tree['columns'] = display_columns
        
        # ตั้งค่า column headings
        column_labels = {
            'CategoryName': 'หมวดหมู่',
            'ItemCode': 'รหัสสินค้า',
            'ItemDesc': 'รายละเอียดสินค้า',
            'UnitCost': 'ราคาทุน',           # เพิ่ม
            'RetailPrice': 'ราคาขาย',
            'ItemUnitInStock': 'คงคลัง',
            'QtyReceived': 'จำนวนรับ',
            'ItemUnitId2Name': 'สั่งซื้อ',
            'ItemUnitId2Multiply': 'ตัวคูณ'
        }
        
        column_widths = {
            'CategoryName': 120,
            'ItemCode': 110,
            'ItemDesc': 220,
            'UnitCost': 100,                  # เพิ่ม
            'RetailPrice': 100,
            'ItemUnitInStock': 90,
            'QtyReceived': 90,
            'ItemUnitId2Name': 100,
            'ItemUnitId2Multiply': 90
        }
        
        column_anchors = {
            'CategoryName': 'w',
            'ItemCode': 'center',
            'ItemDesc': 'w',
            'UnitCost': 'e',                  # เพิ่ม - ชิดขวา
            'RetailPrice': 'e',
            'ItemUnitInStock': 'center',
            'QtyReceived': 'center',
            'ItemUnitId2Name': 'center',
            'ItemUnitId2Multiply': 'center'
        }
        
        for col in display_columns:
            self.import_preview_tree.heading(col, text=column_labels.get(col, col), anchor='center')
            self.import_preview_tree.column(
                col, 
                width=column_widths.get(col, 100), 
                anchor=column_anchors.get(col, 'w'),
                minwidth=70
            )
        
        # Insert data
        max_rows = min(100, len(data))
        
        for idx, row in enumerate(data[:max_rows]):
            # จัดรูปแบบข้อมูล
            values = []
            for col in display_columns:
                value = row.get(col, '')
                
                # จัดรูปแบบตัวเลข
                if col in ['RetailPrice', 'UnitCost']:  # เพิ่ม UnitCost
                    try:
                        if pd.notna(value) and value != '':
                            value = f"{float(value):,.2f}"
                        else:
                            value = '0.00'
                    except:
                        value = str(value) if value else '0.00'
                elif col in ['QtyReceived', 'ItemUnitInStock', 'ItemUnitId2Multiply']:
                    try:
                        if pd.notna(value) and value != '':
                            value = f"{int(float(value))}"
                        else:
                            value = '0'
                    except:
                        value = str(value) if value else '0'
                else:
                    value = str(value) if pd.notna(value) and value != '' else ''
                
                values.append(value)
            
            # เพิ่มแถว
            item_id = self.import_preview_tree.insert('', 'end', values=values)
            
            # แสดงสีแดงเฉพาะแถวที่มี error (ไม่พบรหัสสินค้า)
            if row.get('_has_error', False):
                self.import_preview_tree.item(item_id, tags=('error',))
        
        # กำหนดสีแดงสำหรับแถวที่มีปัญหา
        self.import_preview_tree.tag_configure('error', foreground='#ef4444', background='#fef2f2')
        
        if len(data) > max_rows:
            self.preview_info_label.config(
                text=f"พบข้อมูล {len(data)} แถว (แสดง {max_rows} แถวแรก)",
                fg='#374151'
            )
    
    def validate_import_data(self):
        """ตรวจสอบข้อมูลก่อน import"""
        if not self.import_data:
            messagebox.showwarning("คำเตือน", "กรุณาเลือกไฟล์ก่อน", parent=self.window)
            return
        
        try:
            # Validation
            errors = []
            required_columns = ['ItemCode', 'ItemDesc', 'QtyReceived', 'UnitCost']
            
            # ตรวจสอบคอลัมน์
            if self.import_data:
                first_row = self.import_data[0]
                for col in required_columns:
                    if col not in first_row:
                        errors.append(f"ไม่พบคอลัมน์ '{col}' ในไฟล์")
            
            # ตรวจสอบข้อมูลแต่ละแถว
            for idx, row in enumerate(self.import_data, 1):
                # ตรวจสอบ ItemCode
                item_code = str(row.get('ItemCode', '')).strip()
                if not item_code:
                    errors.append(f"แถวที่ {idx}: ไม่พบรหัสสินค้า")
                
                # ตรวจสอบว่าดึงข้อมูลสินค้าได้หรือไม่ (ใช้ _has_error)
                if row.get('_has_error', False):
                    if item_code:
                        errors.append(f"แถวที่ {idx}: ไม่พบรหัสสินค้า '{item_code}' ในระบบ")
                
                # ตรวจสอบจำนวน
                try:
                    qty = row.get('QtyReceived')
                    if not qty or float(qty) <= 0:
                        errors.append(f"แถวที่ {idx}: จำนวนรับต้องมากกว่า 0")
                except (ValueError, TypeError):
                    errors.append(f"แถวที่ {idx}: จำนวนรับต้องเป็นตัวเลข")
                
                # ตรวจสอบราคาต้นทุน
                try:
                    cost = row.get('UnitCost')
                    if cost is None or cost == '':
                        errors.append(f"แถวที่ {idx}: กรุณาระบุราคาต้นทุน")
                    elif float(cost) < 0:
                        errors.append(f"แถวที่ {idx}: ราคาต้นทุนต้องไม่ติดลบ")
                except (ValueError, TypeError):
                    errors.append(f"แถวที่ {idx}: ราคาต้นทุนต้องเป็นตัวเลข")
            
            is_valid = len(errors) == 0
            
            if is_valid:
                self.validation_result = True
                self.import_validation_label.config(
                    text=f"✓ ข้อมูลถูกต้องครบถ้วน พร้อม import {len(self.import_data)} รายการ",
                    fg='#10b981',
                    bg='#f0fdf4',
                    padx=10, pady=8
                )
                
                # คำนวณยอดรวม
                total_qty = sum(float(row.get('QtyReceived', 0)) for row in self.import_data)
                total_cost = sum(
                    float(row.get('QtyReceived', 0)) * float(row.get('UnitCost', 0))
                    for row in self.import_data if not row.get('_has_error', False)
                )
                
                # นับจำนวนหมวดหมู่
                categories = set()
                for row in self.import_data:
                    cat = row.get('CategoryName', '')
                    if cat:
                        categories.add(cat)
                
                messagebox.showinfo(
                    "ผลการตรวจสอบ",
                    f"✓ ข้อมูลถูกต้องครบถ้วน\n\n"
                    f"จำนวนรายการ: {len(self.import_data)} รายการ\n"
                    f"จำนวนรวม: {total_qty:,.0f} หน่วย\n"
                    f"มูลค่ารวม: {total_cost:,.2f} บาท\n"
                    f"จำนวนหมวดหมู่: {len(categories)} หมวด\n\n"
                    f"พร้อมทำการ Import",
                    parent=self.window
                )
            else:
                self.validation_result = False
                error_count = len(errors)
                error_preview = "\n".join(errors[:10])  # แสดง 10 errors แรก
                
                self.import_validation_label.config(
                    text=f"✗ พบข้อผิดพลาด {error_count} รายการ",
                    fg='#ef4444',
                    bg='#fef2f2',
                    padx=10, pady=8
                )
                
                messagebox.showerror(
                    "พบข้อผิดพลาด",
                    f"✗ พบข้อผิดพลาด {error_count} รายการ\n\n"
                    f"{error_preview}\n\n"
                    f"{'...(มีข้อผิดพลาดเพิ่มเติม)' if error_count > 10 else ''}\n\n"
                    f"กรุณาแก้ไขข้อมูลใน Excel และอัพโหลดใหม่",
                    parent=self.window
                )
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถตรวจสอบข้อมูลได้: {str(e)}", parent=self.window)
    
    def import_from_excel(self):
        """Import ข้อมูลจาก Excel"""
        if not self.import_data:
            messagebox.showwarning("คำเตือน", "กรุณาเลือกไฟล์ก่อน", parent=self.window)
            return
        
        if not self.validation_result:
            response = messagebox.askyesno(
                "คำเตือน",
                "ยังไม่ได้ตรวจสอบข้อมูล หรือพบข้อผิดพลาด\n\n"
                "ต้องการดำเนินการ Import ต่อหรือไม่?",
                icon='warning',
                parent=self.window
            )
            if not response:
                return
        
        try:
            # คำนวณยอดรวม
            total_qty = sum(float(row.get('QtyReceived', 0)) for row in self.import_data if not row.get('_has_error', False))
            
            # นับจำนวนหมวดหมู่
            categories = set()
            for row in self.import_data:
                if not row.get('_has_error', False):
                    cat = row.get('CategoryName', '')
                    if cat:
                        categories.add(cat)
            
            # นับจำนวนที่ไม่มี error
            valid_count = sum(1 for row in self.import_data if not row.get('_has_error', False))
            
            if valid_count == 0:
                messagebox.showerror(
                    "ข้อผิดพลาด",
                    "ไม่มีรายการที่ถูกต้องสำหรับ Import\n\n"
                    "กรุณาตรวจสอบข้อมูลและลองใหม่อีกครั้ง",
                    parent=self.window
                )
                return
            
            # สร้างข้อความยืนยัน
            if self.receive_id:
                confirm_msg = (
                    f"ต้องการ Import ข้อมูล {valid_count} รายการ เข้าสู่ใบรับสินค้าที่มีอยู่หรือไม่?\n\n"
                    f"ใบรับสินค้า: #{self.receive_id}\n"
                    f"จำนวนรวม: {total_qty:,.0f} หน่วย\n"
                    f"จำนวนหมวดหมู่: {len(categories)} หมวด\n\n"
                    f"⚠️ การดำเนินการนี้จะเพิ่มข้อมูลเข้าในฐานข้อมูล"
                )
            else:
                confirm_msg = (
                    f"ต้องการสร้างใบรับสินค้าใหม่และ Import ข้อมูล {valid_count} รายการหรือไม่?\n\n"
                    f"จำนวนรวม: {total_qty:,.0f} หน่วย\n"
                    f"จำนวนหมวดหมู่: {len(categories)} หมวด\n"
                    f"ซัพพลายเออร์: {self.supplier_id}\n\n"
                    f"⚠️ ระบบจะสร้างเอกสารใหม่ และเพิ่มข้อมูลเข้าในฐานข้อมูล"
                )
            
            # Confirm
            response = messagebox.askyesno(
                "ยืนยันการ Import",
                confirm_msg,
                parent=self.window
            )
            
            if not response:
                return
            
            # แสดง progress
            self.window.config(cursor="wait")
            self.window.update()
            
            receive_id = self.receive_id
            receive_number = None
            
            # ถ้ายังไม่มี receive_id ให้สร้างเอกสารใหม่
            if not receive_id:
                success, message, receive_id = self.db.create_receive_document(
                    self.user_data['username'],
                    self.supplier_id
                )
                
                if not success:
                    self.window.config(cursor="")
                    messagebox.showerror(
                        "ข้อผิดพลาด",
                        f"ไม่สามารถสร้างเอกสารได้\n\n{message}",
                        parent=self.window
                    )
                    return
                
                receive_number = message.split(' ')[1]  # ดึง receive number จาก message
                
            # Import ข้อมูล
            success, message, result = self.db.import_receive_items(
                receive_id,
                self.import_data,
                self.user_data['username']
            )
            
            self.window.config(cursor="")
            
            if success:
                # Log activity
                try:
                    self.db.log_import_activity(
                        self.user_data['username'],
                        result['success_count'],
                        result['error_count'],
                        self.import_file_path
                    )
                except:
                    pass  # ถ้า log ไม่สำเร็จไม่ต้องแสดง error
                
                success_msg = f"✓ {message}\n\n"
                
                if receive_number:
                    success_msg += f"เอกสาร: {receive_number}\n"
                else:
                    success_msg += f"ใบรับสินค้า: #{receive_id}\n"
                
                success_msg += (
                    f"สำเร็จ: {result['success_count']} รายการ\n"
                    f"ผิดพลาด: {result['error_count']} รายการ\n"
                    f"รวม: {result['total']} รายการ\n"
                    f"จำนวนรวม: {total_qty:,.0f} หน่วย"
                )
                
                messagebox.showinfo(
                    "สำเร็จ",
                    success_msg,
                    parent=self.window
                )
                
                # อัพเดท receive_id ถ้าสร้างใหม่
                if not self.receive_id:
                    self.receive_id = receive_id
                
                # Clear data after successful import
                self.clear_data()
                
            else:
                error_msg = message
                if result.get('errors'):
                    error_preview = "\n".join(result['errors'][:5])
                    error_msg += f"\n\n{error_preview}"
                    if len(result['errors']) > 5:
                        error_msg += f"\n\n... (มีข้อผิดพลาดเพิ่มเติม {len(result['errors']) - 5} รายการ)"
                
                messagebox.showerror("ข้อผิดพลาด", error_msg, parent=self.window)
            
        except Exception as e:
            self.window.config(cursor="")
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถ Import ได้: {str(e)}", parent=self.window)
    
    def clear_data(self):
        """ล้างข้อมูลทั้งหมด"""
        self.import_file_path = None
        self.import_data = None
        self.validation_result = None
        
        self.import_file_label.config(
            text="📁 ยังไม่ได้เลือกไฟล์...",
            fg='#9ca3af'
        )
        
        self.preview_info_label.config(
            text="เลือกไฟล์เพื่อแสดงตัวอย่างข้อมูล",
            fg='#6b7280'
        )
        
        self.import_validation_label.config(text="", bg='white')
        
        # ซ่อน progress bar
        self.progress_frame.pack_forget()
        self.progress_bar['value'] = 0
        self.progress_label.config(text="0/0")
        
        # Clear treeview
        self.import_preview_tree.delete(*self.import_preview_tree.get_children())
        self.import_preview_tree['columns'] = []
    
    def close_window(self):
        """ปิดหน้าต่าง"""
        try:
            self.db.close_connection()
        except:
            pass
        self.window.destroy()


if __name__ == "__main__":
    # Test UI
    root = tk.Tk()
    root.withdraw()
    
    user_data = {"username": "admin", "role": "admin"}
    
    # ตัวอย่าง 1: สร้างใบรับสินค้าใหม่ (ไม่ใส่ receive_id)
    # app = ExcelManagerUI(root, user_data, receive_id=None, supplier_id=30)
    
    # ตัวอย่าง 2: Import เข้าใบรับสินค้าที่มีอยู่
    # receive_id = 12345
    # app = ExcelManagerUI(root, user_data, receive_id=receive_id)
    
    # Default: สร้างใหม่
    app = ExcelManagerUI(root, user_data, receive_id=None, supplier_id=30)
    
    root.mainloop()