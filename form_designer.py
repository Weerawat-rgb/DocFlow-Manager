import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os

class FormDesigner:
    def __init__(self, parent, template_type):
        self.window = tk.Toplevel(parent)
        self.template_type = template_type
        self.window.title(f"ออกแบบฟอร์ม - {template_type}")
        self.window.geometry("1000x700")
        self.window.configure(bg='#f8fafc')
        
        if parent:
            self.window.transient(parent)
            self.window.grab_set()
        
        # Center window
        self.center_window()
        
        # Form elements data
        self.elements = []
        self.selected_element = None
        
        self.create_designer()
        
    def center_window(self):
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - 500
        y = (self.window.winfo_screenheight() // 2) - 350
        self.window.geometry(f"1000x700+{x}+{y}")
    
    def create_designer(self):
        # Header
        header = tk.Frame(self.window, bg='#6366f1', height=60)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        header_content = tk.Frame(header, bg='#6366f1')
        header_content.pack(expand=True, fill='both', padx=20, pady=15)
        
        tk.Label(header_content, text=f"ออกแบบฟอร์ม: {self.template_type}",
                font=('Segoe UI', 16, 'bold'),
                fg='white', bg='#6366f1').pack(side='left')
        
        # Save button in header
        save_btn = tk.Button(header_content, text="บันทึกฟอร์ม",
                           font=('Segoe UI', 10, 'bold'),
                           bg='#10b981', fg='white',
                           relief='solid', bd=1,
                           padx=20, pady=8,
                           cursor='hand2',
                           command=self.save_template)
        save_btn.pack(side='right')
        
        # Main container
        main_container = tk.Frame(self.window, bg='#f8fafc')
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left panel - Tools
        self.create_tool_panel(main_container)
        
        # Center panel - Canvas
        self.create_canvas_panel(main_container)
        
        # Right panel - Properties
        self.create_properties_panel(main_container)
        
    def create_tool_panel(self, parent):
        # Tools panel
        tools_frame = tk.Frame(parent, bg='white', width=220)
        tools_frame.pack(side='left', fill='y', padx=(0, 5))
        tools_frame.pack_propagate(False)
        
        tk.Label(tools_frame, text="เครื่องมือออกแบบ", 
                font=('Segoe UI', 12, 'bold'),
                fg='#374151', bg='white').pack(pady=15)
        
        # === HEADER TOOLS ===
        header_frame = tk.LabelFrame(tools_frame, text="Header Section", 
                                    font=('Segoe UI', 10, 'bold'),
                                    fg='#3b82f6', bg='white')
        header_frame.pack(fill='x', padx=10, pady=5)
        
        header_tools = [
            ("ชื่อบริษัท", lambda: self.add_field_element("company_name", "header")),
            ("ที่อยู่บริษัท", lambda: self.add_field_element("company_address", "header")),
            ("เบอร์โทร", lambda: self.add_field_element("company_phone", "header")),
            ("โลโก้", lambda: self.add_logo_element("header")),
            ("หัวเอกสาร", lambda: self.add_text_element("header", "ใบวางบิล"))
        ]
        
        for tool_name, command in header_tools:
            btn = tk.Button(header_frame, text=tool_name,
                        font=('Segoe UI', 9),
                        bg='#eff6ff', fg='#1d4ed8',
                        relief='solid', bd=1,
                        padx=10, pady=4,
                        cursor='hand2',
                        command=command)
            btn.pack(fill='x', padx=5, pady=2)
        
        # === DETAIL TOOLS ===
        detail_frame = tk.LabelFrame(tools_frame, text="Detail Section (Database)", 
                                    font=('Segoe UI', 10, 'bold'),
                                    fg='#10b981', bg='white')
        detail_frame.pack(fill='x', padx=10, pady=5)

        detail_tools = [
            ("ข้อมูลคงที่", lambda: self.add_static_field("detail")),
            ("ตารางรายการ", lambda: self.add_data_table("detail")),
            ("สูตรคำนวณ", lambda: self.add_formula_field("detail")),
            ("ข้อความแบบมีเงื่อนไข", lambda: self.add_conditional_text("detail")),
            ("QR Code/Barcode", lambda: self.add_barcode("detail")),
            ("บล็อกข้อมูลลูกค้า", lambda: self.add_customer_block("detail"))
        ]

        for tool_name, command in detail_tools:
            btn = tk.Button(detail_frame, text=tool_name,
                        font=('Segoe UI', 9),
                        bg='#f0fdf4', fg='#166534',
                        relief='solid', bd=1,
                        padx=10, pady=4,
                        cursor='hand2',
                        command=command)
            btn.pack(fill='x', padx=5, pady=2)
        
        # === FOOTER TOOLS ===
        footer_frame = tk.LabelFrame(tools_frame, text="Footer Section", 
                                    font=('Segoe UI', 10, 'bold'),
                                    fg='#f59e0b', bg='white')
        footer_frame.pack(fill='x', padx=10, pady=5)
        
        footer_tools = [
            ("ลายเซ็น", lambda: self.add_signature_element("footer")),
            ("หมายเหตุ", lambda: self.add_text_element("footer", "หมายเหตุ:")),
            ("ข้อมูลติดต่อ", lambda: self.add_field_element("contact_info", "footer")),
            ("เส้นคั่น", lambda: self.add_line_element("footer"))
        ]
        
        for tool_name, command in footer_tools:
            btn = tk.Button(footer_frame, text=tool_name,
                        font=('Segoe UI', 9),
                        bg='#fffbeb', fg='#92400e',
                        relief='solid', bd=1,
                        padx=10, pady=4,
                        cursor='hand2',
                        command=command)
            btn.pack(fill='x', padx=5, pady=2)
                
    def create_canvas_panel(self, parent):
        # Canvas panel
        canvas_frame = tk.Frame(parent, bg='white')
        canvas_frame.pack(side='left', fill='both', expand=True, padx=5)
        
        tk.Label(canvas_frame, text="พื้นที่ออกแบบ - A4 (210×297 มม.)", 
                font=('Segoe UI', 12, 'bold'),
                fg='#374151', bg='white').pack(pady=10)
        
        # Canvas container with scroll
        canvas_container = tk.Frame(canvas_frame, bg='#f0f0f0')
        canvas_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # A4 size in pixels (at 96 DPI: 210mm = 794px, 297mm = 1123px)
        # ปรับให้พอดีหน้าจอ: ใช้ 595×842 (scale down)
        self.canvas = tk.Canvas(canvas_container, 
                            bg='white', 
                            width=595,      # A4 width scaled
                            height=842,     # A4 height scaled  
                            relief='solid', 
                            bd=2,
                            highlightthickness=1,
                            highlightbackground='#666666',
                            scrollregion=(0, 0, 595, 842))
        
        # เพิ่มเส้นขอบ A4 และ margin guides
        self.draw_a4_guides()
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(canvas_container, orient="vertical", command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_container, orient="horizontal", command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid layout for proper scrollbar positioning
        canvas_container.grid_rowconfigure(0, weight=1)
        canvas_container.grid_columnconfigure(0, weight=1)
        
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        # Bind canvas events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)   
            
    def draw_a4_guides(self):
        """วาดเส้นช่วยสำหรับ A4 พร้อม Header/Detail/Footer"""
        width = 595
        height = 842
        margin = 57  # 20mm margin
        
        # เส้นขอบหน้ากระดาษ
        self.canvas.create_rectangle(5, 5, width-5, height-5, 
                                    outline='#cccccc', width=2, tags='guide')
        
        # เส้น margin
        self.canvas.create_rectangle(margin, margin, width-margin, height-margin, 
                                    outline='#e0e0e0', width=1, dash=(5, 5), tags='guide')
        
        # === SECTIONS ===
        # Header section (120px = ~42mm)
        self.header_height = 120
        self.canvas.create_line(margin, margin + self.header_height, 
                            width-margin, margin + self.header_height,
                            fill='#3b82f6', width=2, tags='guide')
        
        # Footer section (100px = ~35mm from bottom)  
        self.footer_height = 100
        footer_start = height - margin - self.footer_height
        self.canvas.create_line(margin, footer_start, width-margin, footer_start,
                            fill='#3b82f6', width=2, tags='guide')
        
        # Detail section (ระหว่าง header กับ footer)
        self.detail_start = margin + self.header_height
        self.detail_end = footer_start
        
        # ป้ายชื่อ sections
        self.canvas.create_text(30, margin + 30, text="HEADER", 
                            font=('Segoe UI', 10, 'bold'), fill='#3b82f6', 
                            anchor='w', tags='guide')
        
        self.canvas.create_text(30, (self.detail_start + self.detail_end) // 2, 
                            text="DETAIL", font=('Segoe UI', 10, 'bold'), 
                            fill='#10b981', anchor='w', tags='guide')
        
        self.canvas.create_text(30, footer_start + 20, text="FOOTER", 
                            font=('Segoe UI', 10, 'bold'), fill='#f59e0b', 
                            anchor='w', tags='guide')
        
        # เส้นกลางแนวตั้ง
        center_x = width // 2
        self.canvas.create_line(center_x, margin, center_x, height-margin, 
                            fill='#f0f0f0', width=1, dash=(3, 3), tags='guide')
        
    def create_properties_panel(self, parent):
        # Properties panel
        props_frame = tk.Frame(parent, bg='white', width=200)
        props_frame.pack(side='right', fill='y', padx=(5, 0))
        props_frame.pack_propagate(False)
        
        tk.Label(props_frame, text="คุณสมบัติ", 
                font=('Segoe UI', 12, 'bold'),
                fg='#374151', bg='white').pack(pady=15)
        
        # Properties content
        self.props_content = tk.Frame(props_frame, bg='white')
        self.props_content.pack(fill='both', expand=True, padx=10)
        
        # Default message
        tk.Label(self.props_content, text="เลือกองค์ประกอบ\nเพื่อแก้ไขคุณสมบัติ",
                font=('Segoe UI', 10),
                fg='#6b7280', bg='white',
                justify='center').pack(expand=True)
    
    def add_text_element(self, section="detail", default_text="ข้อความตัวอย่าง"):
        """เพิ่มข้อความในส่วนที่กำหนด"""
        x, y = self.get_section_position(section)
        
        element = {
            'type': 'text',
            'section': section,
            'x': x,
            'y': y,
            'text': default_text,
            'font_size': 12,
            'color': 'black'
        }
        self.elements.append(element)
        self.redraw_canvas()

    def add_field_element(self, field_type, section="detail"):
        """เพิ่มฟิลด์ข้อมูลในส่วนที่กำหนด"""
        field_names = {
            'company_name': 'ชื่อบริษัท',
            'company_address': 'ที่อยู่บริษัท',
            'company_phone': 'เบอร์โทร',
            'date': 'วันที่',
            'doc_number': 'เลขที่เอกสาร',
            'customer': 'ลูกค้า/ผู้จำหน่าย',
            'total': 'ยอดรวม',
            'contact_info': 'ข้อมูลติดต่อ'
        }
        
        x, y = self.get_section_position(section)
        
        element = {
            'type': 'field',
            'section': section,
            'field_type': field_type,
            'x': x,
            'y': y,
            'text': f'[{field_names.get(field_type, field_type)}]',
            'font_size': 12,
            'color': 'blue'
        }
        self.elements.append(element)
        self.redraw_canvas()

    def add_table_element(self, section="detail"):
        """เพิ่มตารางในส่วนที่กำหนด"""
        x, y = self.get_section_position(section)
        
        element = {
            'type': 'table',
            'section': section,
            'x': x,
            'y': y,
            'width': 480,
            'height': 200,
            'rows': 6,
            'cols': 5,
            'headers': ['ลำดับ', 'รายการ', 'จำนวน', 'ราคา', 'รวม']
        }
        self.elements.append(element)
        self.redraw_canvas()

    def add_signature_element(self, section="footer"):
        """เพิ่มลายเซ็นในส่วนที่กำหนด"""
        x, y = self.get_section_position(section)
        
        element = {
            'type': 'signature',
            'section': section,
            'x': x,
            'y': y,
            'width': 150,
            'height': 60,
            'label': 'ลายเซ็น'
        }
        self.elements.append(element)
        self.redraw_canvas()

    def add_logo_element(self, section="header"):
        """เพิ่มโลโก้ในส่วนที่กำหนด"""
        x, y = self.get_section_position(section)
        
        element = {
            'type': 'logo',
            'section': section,
            'x': x,
            'y': y,
            'width': 80,
            'height': 80,
            'path': '[โลโก้บริษัท]'
        }
        self.elements.append(element)
        self.redraw_canvas()

    def add_line_element(self, section="detail"):
        """เพิ่มเส้นคั่นในส่วนที่กำหนด"""
        x, y = self.get_section_position(section)
        
        element = {
            'type': 'line',
            'section': section,
            'x1': x,
            'y1': y,
            'x2': x + 400,
            'y2': y,
            'width': 1,
            'color': 'black'
        }
        self.elements.append(element)
        self.redraw_canvas()

    def get_section_position(self, section):
        """คำนวณตำแหน่งเริ่มต้นของแต่ละส่วน"""
        margin = 57
        
        if section == "header":
            return margin + 20, margin + 20
        elif section == "detail":
            return margin + 20, self.detail_start + 20
        elif section == "footer":
            return margin + 20, self.detail_end + 20
        else:
            return margin + 20, margin + 20  # default    
        
    def add_static_field(self, section="detail"):
        """เพิ่มฟิลด์ข้อมูลที่ดึงจาก database"""
        x, y = self.get_section_position(section)
        
        # เปิด dialog ให้เลือกฟิลด์
        field_dialog = FieldSelectionDialog(self.window, self.get_database_fields())
        selected_field = field_dialog.result
        
        if selected_field:
            element = {
                'type': 'database_field',
                'section': section,
                'x': x,
                'y': y,
                'field_name': selected_field['name'],
                'field_type': selected_field['type'],
                'label': selected_field['label'],
                'font_size': 12,
                'color': 'black',
                'format': selected_field.get('format', '')
            }
            self.elements.append(element)
            self.redraw_canvas()

    def add_data_table(self, section="detail"):
        """เพิ่มตารางข้อมูลจาก database"""
        x, y = self.get_section_position(section)
        
        element = {
            'type': 'data_table',
            'section': section,
            'x': x,
            'y': y,
            'width': 480,
            'height': 200,
            'data_source': 'bill_items',  # ตาราง database
            'columns': [
                {'name': 'item_code', 'label': 'รหัส', 'width': 80, 'align': 'center'},
                {'name': 'item_name', 'label': 'รายการ', 'width': 200, 'align': 'left'},
                {'name': 'quantity', 'label': 'จำนวน', 'width': 70, 'align': 'center'},
                {'name': 'unit_price', 'label': 'ราคา/หน่วย', 'width': 80, 'align': 'right'},
                {'name': 'total_price', 'label': 'รวม', 'width': 80, 'align': 'right'}
            ],
            'show_header': True,
            'show_borders': True,
            'alternate_rows': True,
            'max_rows': 20
        }
        self.elements.append(element)
        self.redraw_canvas()

    def add_formula_field(self, section="detail"):
        """เพิ่มฟิลด์คำนวณ เช่น ยอดรวม, ภาษี"""
        x, y = self.get_section_position(section)
        
        # เปิด dialog สำหรับสูตรคำนวณ
        formula_dialog = FormulaDialog(self.window)
        formula_result = formula_dialog.result
        
        if formula_result:
            element = {
                'type': 'formula_field',
                'section': section,
                'x': x,
                'y': y,
                'formula': formula_result['formula'],
                'label': formula_result['label'],
                'format': formula_result['format'],  # เช่น currency, percentage
                'font_size': 12,
                'color': 'black',
                'prefix': formula_result.get('prefix', ''),
                'suffix': formula_result.get('suffix', '')
            }
            self.elements.append(element)
            self.redraw_canvas()

    def add_conditional_text(self, section="detail"):
        """เพิ่มข้อความที่แสดงตามเงื่อนไข"""
        x, y = self.get_section_position(section)
        
        element = {
            'type': 'conditional_text',
            'section': section,
            'x': x,
            'y': y,
            'conditions': [
                {
                    'field': 'payment_status',
                    'operator': '==',
                    'value': 'paid',
                    'text': 'ชำระเงินแล้ว',
                    'color': 'green'
                },
                {
                    'field': 'payment_status', 
                    'operator': '==',
                    'value': 'pending',
                    'text': 'รอการชำระเงิน',
                    'color': 'orange'
                }
            ],
            'default_text': 'ไม่ระบุสถานะ',
            'font_size': 12
        }
        self.elements.append(element)
        self.redraw_canvas()

    def add_customer_block(self, section="detail"):
        """เพิ่มบล็อกข้อมูลลูกค้าแบบครบชุด"""
        x, y = self.get_section_position(section)
        
        element = {
            'type': 'customer_block',
            'section': section,
            'x': x,
            'y': y,
            'width': 300,
            'height': 100,
            'fields': [
                {'field': 'customer_name', 'label': 'ลูกค้า:', 'row': 0},
                {'field': 'customer_address', 'label': 'ที่อยู่:', 'row': 1},
                {'field': 'customer_phone', 'label': 'โทร:', 'row': 2},
                {'field': 'customer_tax_id', 'label': 'เลขประจำตัวผู้เสียภาษี:', 'row': 3}
            ],
            'font_size': 10,
            'line_height': 20
        }
        self.elements.append(element)
        self.redraw_canvas()

    def add_barcode(self, section="detail"):
        """เพิ่ม QR Code หรือ Barcode"""
        x, y = self.get_section_position(section)
        
        element = {
            'type': 'barcode',
            'section': section,
            'x': x,
            'y': y,
            'width': 100,
            'height': 100,
            'barcode_type': 'QR',  # QR, Code128, EAN13
            'data_field': 'document_id',  # ฟิลด์ที่จะเอามาสร้าง barcode
            'show_text': True
        }
        self.elements.append(element)
        self.redraw_canvas()

    def get_database_fields(self):
        """ดึงรายชื่อฟิลด์จาก database schema"""
        # ตัวอย่างฟิลด์ที่มีใน database
        return [
            {'name': 'document_no', 'label': 'เลขที่เอกสาร', 'type': 'string'},
            {'name': 'document_date', 'label': 'วันที่', 'type': 'date', 'format': 'dd/mm/yyyy'},
            {'name': 'customer_id', 'label': 'รหัสลูกค้า', 'type': 'string'},
            {'name': 'customer_name', 'label': 'ชื่อลูกค้า', 'type': 'string'},
            {'name': 'subtotal', 'label': 'ยอดก่อนภาษี', 'type': 'currency'},
            {'name': 'tax_amount', 'label': 'ภาษี 7%', 'type': 'currency'},
            {'name': 'total_amount', 'label': 'ยอดรวมทั้งสิ้น', 'type': 'currency'},
            {'name': 'payment_status', 'label': 'สถานะการชำระ', 'type': 'string'}
        ]
    def redraw_canvas(self):
        """วาดองค์ประกอบทั้งหมดใหม่"""
        self.canvas.delete("all")
        
        # วาดเส้นช่วย A4 ใหม่
        self.draw_a4_guides()
        
        # วาดองค์ประกอบต่างๆ (โค้ดเดิม)
        for i, element in enumerate(self.elements):
            if element['type'] == 'text' or element['type'] == 'field':
                self.canvas.create_text(
                    element['x'], element['y'],
                    text=element['text'],
                    font=('Segoe UI', element['font_size']),
                    fill=element['color'],
                    anchor='nw',
                    tags=f'element_{i}'
                )
            
            elif element['type'] == 'table':
                # วาดตาราง
                x, y = element['x'], element['y']
                w, h = element['width'], element['height']
                rows, cols = element['rows'], element['cols']
                
                # วาดเส้นตาราง
                for row in range(rows + 1):
                    y_pos = y + (h / rows * row)
                    self.canvas.create_line(x, y_pos, x + w, y_pos, tags=f'element_{i}')
                
                for col in range(cols + 1):
                    x_pos = x + (w / cols * col)
                    self.canvas.create_line(x_pos, y, x_pos, y + h, tags=f'element_{i}')
            
            elif element['type'] == 'line':
                self.canvas.create_line(
                    element['x1'], element['y1'],
                    element['x2'], element['y2'],
                    width=element['width'],
                    fill=element['color'],
                    tags=f'element_{i}'
                )
            
            elif element['type'] == 'signature':
                # วาดกรอบลายเซ็น
                x, y = element['x'], element['y']
                w, h = element['width'], element['height']
                self.canvas.create_rectangle(x, y, x + w, y + h, outline='gray', tags=f'element_{i}')
                self.canvas.create_text(x + w/2, y + h/2, text=element['label'], 
                                      font=('Segoe UI', 10), tags=f'element_{i}')
    
    def on_canvas_click(self, event):
        """จัดการการคลิกบน canvas"""
        # หาองค์ประกอบที่ถูกคลิก
        clicked_item = self.canvas.find_closest(event.x, event.y)[0]
        tags = self.canvas.gettags(clicked_item)
        
        if tags and tags[0].startswith('element_'):
            element_index = int(tags[0].split('_')[1])
            self.selected_element = element_index
            self.show_properties(self.elements[element_index])
        else:
            self.selected_element = None
            self.clear_properties()
    
    def on_canvas_drag(self, event):
        """จัดการการลากองค์ประกอบ"""
        if self.selected_element is not None:
            element = self.elements[self.selected_element]
            if element['type'] in ['text', 'field']:
                element['x'] = event.x
                element['y'] = event.y
            elif element['type'] == 'table':
                element['x'] = event.x
                element['y'] = event.y
            elif element['type'] == 'signature':
                element['x'] = event.x
                element['y'] = event.y
            
            self.redraw_canvas()
    
    def show_properties(self, element):
        """แสดงคุณสมบัติขององค์ประกอบ"""
        # Clear current properties
        for widget in self.props_content.winfo_children():
            widget.destroy()
        
        tk.Label(self.props_content, text=f"แก้ไข: {element['type']}",
                font=('Segoe UI', 12, 'bold'),
                fg='#374151', bg='white').pack(pady=10)
        
        if element['type'] in ['text', 'field']:
            # Text properties
            tk.Label(self.props_content, text="ข้อความ:",
                    font=('Segoe UI', 10, 'bold'),
                    fg='#374151', bg='white').pack(anchor='w')
            
            text_var = tk.StringVar(value=element['text'])
            text_entry = tk.Entry(self.props_content, textvariable=text_var,
                                font=('Segoe UI', 10))
            text_entry.pack(fill='x', pady=(5, 15))
            
            # Font size
            tk.Label(self.props_content, text="ขนาดตัวอักษร:",
                    font=('Segoe UI', 10, 'bold'),
                    fg='#374151', bg='white').pack(anchor='w')
            
            size_var = tk.IntVar(value=element['font_size'])
            size_entry = tk.Entry(self.props_content, textvariable=size_var,
                                font=('Segoe UI', 10))
            size_entry.pack(fill='x', pady=(5, 15))
            
            # Update button
            def update_element():
                element['text'] = text_var.get()
                element['font_size'] = size_var.get()
                self.redraw_canvas()
            
            tk.Button(self.props_content, text="อัพเดท",
                     font=('Segoe UI', 10, 'bold'),
                     bg='#6366f1', fg='white',
                     relief='solid', bd=1,
                     command=update_element).pack(pady=10)
        
        # Delete button
        tk.Button(self.props_content, text="ลบองค์ประกอบ",
                 font=('Segoe UI', 10),
                 bg='#ef4444', fg='white',
                 relief='solid', bd=1,
                 command=self.delete_selected_element).pack(side='bottom', pady=20)
    
    def clear_properties(self):
        """ล้างพื้นที่คุณสมบัติ"""
        for widget in self.props_content.winfo_children():
            widget.destroy()
        
        tk.Label(self.props_content, text="เลือกองค์ประกอบ\nเพื่อแก้ไขคุณสมบัติ",
                font=('Segoe UI', 10),
                fg='#6b7280', bg='white',
                justify='center').pack(expand=True)
    
    def delete_selected_element(self):
        """ลบองค์ประกอบที่เลือก"""
        if self.selected_element is not None:
            del self.elements[self.selected_element]
            self.selected_element = None
            self.redraw_canvas()
            self.clear_properties()
    
    def save_template(self):
        """บันทึก template"""
        if not self.elements:
            messagebox.showwarning("คำเตือน", "ยังไม่มีองค์ประกอบในฟอร์ม")
            return
        
        # Save to JSON file
        template_data = {
            'type': self.template_type,
            'paper_size': 'A4',
            'dimensions': {
                'width_mm': 210,
                'height_mm': 297, 
                'width_px': 595,
                'height_px': 842
            },
            'elements': self.elements
        }
        
        filename = f"template_{self.template_type}.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, ensure_ascii=False, indent=4)
            
            messagebox.showinfo("สำเร็จ", f"บันทึกเทมเพลต A4: {filename}")
            self.window.destroy()
            
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถบันทึกได้: {str(e)}")
            
class FieldSelectionDialog:
    def __init__(self, parent, fields):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("เลือกฟิลด์ข้อมูล")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # รายการฟิลด์
        tk.Label(self.dialog, text="เลือกฟิลด์จากฐานข้อมูล:",
                font=('Segoe UI', 12, 'bold')).pack(pady=10)
        
        listbox = tk.Listbox(self.dialog, font=('Segoe UI', 10))
        listbox.pack(fill='both', expand=True, padx=20, pady=10)
        
        for field in fields:
            listbox.insert(tk.END, f"{field['label']} ({field['name']})")
        
        def on_select():
            selection = listbox.curselection()
            if selection:
                self.result = fields[selection[0]]
                self.dialog.destroy()
        
        tk.Button(self.dialog, text="เลือก", command=on_select,
                 bg='#6366f1', fg='white', padx=20, pady=5).pack(pady=10)

class FormulaDialog:
    def __init__(self, parent):
        self.result = None
        
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("สูตรคำนวณ")
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # สูตรที่มีให้เลือก
        formulas = [
            {'label': 'ยอดรวมก่อนภาษี', 'formula': 'SUM(bill_items.total_price)', 'format': 'currency'},
            {'label': 'ภาษี 7%', 'formula': 'SUM(bill_items.total_price) * 0.07', 'format': 'currency'},
            {'label': 'ยอดรวมทั้งสิ้น', 'formula': 'SUM(bill_items.total_price) * 1.07', 'format': 'currency'},
            {'label': 'จำนวนรายการทั้งหมด', 'formula': 'COUNT(bill_items.id)', 'format': 'number'}
        ]
        
        tk.Label(self.dialog, text="เลือกสูตรคำนวณ:",
                font=('Segoe UI', 12, 'bold')).pack(pady=10)
        
        listbox = tk.Listbox(self.dialog, font=('Segoe UI', 10))
        listbox.pack(fill='both', expand=True, padx=20, pady=10)
        
        for formula in formulas:
            listbox.insert(tk.END, formula['label'])
        
        def on_select():
            selection = listbox.curselection()
            if selection:
                self.result = formulas[selection[0]]
                self.dialog.destroy()
        
        tk.Button(self.dialog, text="เลือก", command=on_select,
                 bg='#6366f1', fg='white', padx=20, pady=5).pack(pady=10)
            
if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()  # Hide main window
    
    app = FormDesigner(None, "purchase")
    root.mainloop()