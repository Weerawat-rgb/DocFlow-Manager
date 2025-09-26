import tkinter as tk
from tkinter import ttk, messagebox, filedialog, colorchooser
import json
import os
from datetime import datetime
import math

class ProfessionalFormDesigner:
    def __init__(self, parent, template_type):
        self.window = tk.Toplevel(parent)
        self.template_type = template_type
        self.template_file = f"template_{template_type}.json"
        self.window.title(f"Professional Form Designer - {template_type}")
        self.window.geometry("1400x900")
        self.window.configure(bg='#f8f9fa')
        
        if parent:
            self.window.transient(parent)
            
        self.center_window()
        
        # Designer variables
        self.elements = []
        self.selected_element = None
        self.clipboard = None
        self.zoom_level = 1.0
        self.grid_size = 10
        self.show_grid = True
        self.snap_to_grid = True
        
        # Colors
        self.selection_color = '#007acc'
        self.grid_color = '#e8e8e8'
        
        # Canvas dimensions (A4 at 96 DPI)
        self.canvas_width = 794  # 210mm
        self.canvas_height = 1123  # 297mm
        
        self.create_professional_ui()
        self.create_keyboard_bindings()
        
        # Load existing template after UI is ready
        self.window.after(100, self.load_existing_template)
    
    def center_window(self):
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - 700
        y = (self.window.winfo_screenheight() // 2) - 450
        self.window.geometry(f"1400x900+{x}+{y}")
    
    def create_professional_ui(self):
        # Menu Bar
        self.create_menu_bar()
        
        # Toolbar
        self.create_toolbar()
        
        # Main container
        main_container = tk.PanedWindow(self.window, orient='horizontal', bg='#f8f9fa')
        main_container.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Left Panel - Toolbox & Field Explorer
        self.create_left_panel(main_container)
        
        # Center Panel - Design Surface
        self.create_center_panel(main_container)
        
        # Right Panel - Properties & Report Explorer
        self.create_right_panel(main_container)
        
        # Status Bar
        self.create_status_bar()
    
    def create_menu_bar(self):
        menubar = tk.Menu(self.window)
        self.window.config(menu=menubar)
        
        # File Menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New Template", command=self.new_template)
        file_menu.add_command(label="Open Template...", command=self.open_template)
        file_menu.add_command(label="Save Template", command=self.save_template)
        file_menu.add_command(label="Save As...", command=self.save_as_template)
        file_menu.add_separator()
        file_menu.add_command(label="Export to PDF", command=self.export_pdf)
        file_menu.add_separator()
        file_menu.add_command(label="Close", command=self.window.destroy)
        
        # Edit Menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=self.cut, accelerator="Ctrl+X")
        edit_menu.add_command(label="Copy", command=self.copy, accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste", command=self.paste, accelerator="Ctrl+V")
        edit_menu.add_command(label="Delete", command=self.delete_selected, accelerator="Del")
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All", command=self.select_all, accelerator="Ctrl+A")
        
        # View Menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Zoom In", command=self.zoom_in, accelerator="Ctrl++")
        view_menu.add_command(label="Zoom Out", command=self.zoom_out, accelerator="Ctrl+-")
        view_menu.add_command(label="Zoom to Fit", command=self.zoom_fit, accelerator="Ctrl+0")
        view_menu.add_separator()
        view_menu.add_checkbutton(label="Show Grid", variable=tk.BooleanVar(value=self.show_grid), command=self.toggle_grid)
        view_menu.add_checkbutton(label="Snap to Grid", variable=tk.BooleanVar(value=self.snap_to_grid), command=self.toggle_snap)
        
        # Format Menu
        format_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Format", menu=format_menu)
        format_menu.add_command(label="Align Left", command=lambda: self.align_elements('left'))
        format_menu.add_command(label="Align Center", command=lambda: self.align_elements('center'))
        format_menu.add_command(label="Align Right", command=lambda: self.align_elements('right'))
        format_menu.add_separator()
        format_menu.add_command(label="Same Width", command=self.same_width)
        format_menu.add_command(label="Same Height", command=self.same_height)
        format_menu.add_command(label="Same Size", command=self.same_size)
    
    def create_toolbar(self):
        toolbar = tk.Frame(self.window, bg='#f0f0f0', height=40)
        toolbar.pack(fill='x')
        toolbar.pack_propagate(False)
        
        # Toolbar buttons
        buttons = [
            ("📄", "New", self.new_template),
            ("📁", "Open", self.open_template), 
            ("💾", "Save", self.save_template),
            (None, None, None),  # Separator
            ("✂️", "Cut", self.cut),
            ("📋", "Copy", self.copy),
            ("📋", "Paste", self.paste),
            (None, None, None),  # Separator
            ("↶", "Undo", self.undo),
            ("↷", "Redo", self.redo),
            (None, None, None),  # Separator
            ("🔍+", "Zoom In", self.zoom_in),
            ("🔍-", "Zoom Out", self.zoom_out),
            ("🔍", "Zoom Fit", self.zoom_fit),
        ]
        
        for icon, tooltip, command in buttons:
            if icon is None:
                # Separator
                separator = tk.Frame(toolbar, width=2, bg='#d0d0d0')
                separator.pack(side='left', fill='y', padx=5, pady=5)
            else:
                btn = tk.Button(toolbar, text=icon, font=('Segoe UI', 10),
                              bg='#f0f0f0', relief='flat', padx=8, pady=5,
                              cursor='hand2', command=command)
                btn.pack(side='left', padx=2)
                
                # Tooltip
                self.create_tooltip(btn, tooltip)
    
    def create_left_panel(self, parent):
        left_panel = tk.Frame(parent, bg='white', width=250)
        parent.add(left_panel)
        
        # Notebook for different panels
        notebook = ttk.Notebook(left_panel)
        notebook.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Toolbox Tab
        toolbox_frame = self.create_toolbox_tab(notebook)  # ส่ง notebook เป็น parent
        notebook.add(toolbox_frame, text='Toolbox')
        
        # Field Explorer Tab
        field_frame = self.create_field_explorer_tab(notebook)  # ส่ง notebook เป็น parent
        notebook.add(field_frame, text='Field Explorer')
        
        # Report Explorer Tab
        report_frame = self.create_report_explorer_tab(notebook)  # ส่ง notebook เป็น parent
        notebook.add(report_frame, text='Report Tree')  
          
    def create_toolbox_tab(self, parent):
        frame = tk.Frame(parent, bg='white')
        
        # Toolbox categories
        categories = [
            ("General", [
                ("🔤", "Label", lambda: self.add_element('label')),
                ("📊", "Text Box", lambda: self.add_element('textbox')),
                ("🖼️", "Picture Box", lambda: self.add_element('picturebox')),
                ("➖", "Line", lambda: self.add_element('line')),
                ("▭", "Shape", lambda: self.add_element('shape'))
            ]),
            ("Report Controls", [
                ("📋", "Table", lambda: self.add_element('table')),
                ("📈", "Chart", lambda: self.add_element('chart')),
                ("🔢", "Page Info", lambda: self.add_element('pageinfo')),
                ("📅", "Date Time", lambda: self.add_element('datetime'))
            ]),
            ("Data Controls", [
                ("🗃️", "Data Field", lambda: self.add_element('datafield')),
                ("∑", "Calculated Field", lambda: self.add_element('calculated')),
                ("📊", "Cross Tab", lambda: self.add_element('crosstab')),
                ("📋", "Sub Report", lambda: self.add_element('subreport'))
            ])
        ]
        
        for category_name, tools in categories:
            # Category header
            header = tk.Label(frame, text=category_name, font=('Segoe UI', 10, 'bold'),
                            fg='#2c3e50', bg='#ecf0f1', padx=10, pady=5)
            header.pack(fill='x', pady=(5, 0))
            
            # Tools in category
            tools_frame = tk.Frame(frame, bg='white')
            tools_frame.pack(fill='x', padx=5, pady=2)
            
            for icon, name, command in tools:
                tool_frame = tk.Frame(tools_frame, bg='white', relief='flat', cursor='hand2')
                tool_frame.pack(fill='x', pady=1)
                
                # Icon and label
                tk.Label(tool_frame, text=icon, font=('Segoe UI', 12), bg='white').pack(side='left', padx=5)
                tk.Label(tool_frame, text=name, font=('Segoe UI', 9), bg='white', anchor='w').pack(side='left')
                
                # Bind click
                tool_frame.bind("<Button-1>", lambda e, cmd=command: cmd())
                for child in tool_frame.winfo_children():
                    child.bind("<Button-1>", lambda e, cmd=command: cmd())
        return frame
        
    
    def create_field_explorer_tab(self, parent):
        frame = tk.Frame(parent, bg='white')
        
        tk.Label(frame, text="Database Fields", font=('Segoe UI', 10, 'bold'),
            fg='#2c3e50', bg='white').pack(pady=10)
        
        # Field tree
        self.field_tree = ttk.Treeview(frame, height=15)
        self.field_tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Sample fields
        self.field_tree.insert('', 'end', text='📄 Document Fields', open=True, values=('folder',))
        doc_id = self.field_tree.get_children()[-1]
        
        fields = [
            ('doc_number', '📄 Document Number'),
            ('doc_date', '📅 Document Date'),
            ('customer_id', '👤 Customer ID'),
            ('customer_name', '👤 Customer Name'),
            ('total_amount', '💰 Total Amount')
        ]
        
        for field_id, field_name in fields:
            self.field_tree.insert(doc_id, 'end', text=field_name, values=(field_id,))
        
        # Bind double-click to add field
        self.field_tree.bind('<Double-1>', self.add_field_from_tree)
        
        return frame
    
    def create_report_explorer_tab(self, parent):
        frame = tk.Frame(parent, bg='white')
        
        tk.Label(frame, text="Report Structure", font=('Segoe UI', 10, 'bold'),
                fg='#2c3e50', bg='white').pack(pady=10)
        
        # Report tree
        self.report_tree = ttk.Treeview(frame, height=15)
        self.report_tree.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Report structure
        root_id = self.report_tree.insert('', 'end', text='📊 Report', open=True)
        header_id = self.report_tree.insert(root_id, 'end', text='📋 Report Header', open=True)
        detail_id = self.report_tree.insert(root_id, 'end', text='📄 Detail', open=True) 
        footer_id = self.report_tree.insert(root_id, 'end', text='📋 Report Footer', open=True)
        
        return frame
    
    def create_center_panel(self, parent):
        center_panel = tk.Frame(parent, bg='#f8f9fa')
        parent.add(center_panel)
        
        # Design surface container
        design_container = tk.Frame(center_panel, bg='#f8f9fa')
        design_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Rulers
        self.create_rulers(design_container)
        
        # Canvas with scrollbars
        canvas_frame = tk.Frame(design_container, bg='#f8f9fa')
        canvas_frame.pack(fill='both', expand=True)
        
        self.canvas = tk.Canvas(canvas_frame,
                              bg='white',
                              width=self.canvas_width,
                              height=self.canvas_height,
                              scrollregion=(0, 0, self.canvas_width, self.canvas_height))
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        h_scrollbar = ttk.Scrollbar(canvas_frame, orient="horizontal", command=self.canvas.xview)
        self.canvas.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # Grid
        self.canvas.grid(row=0, column=0, sticky="nsew")
        v_scrollbar.grid(row=0, column=1, sticky="ns")
        h_scrollbar.grid(row=1, column=0, sticky="ew")
        
        canvas_frame.grid_rowconfigure(0, weight=1)
        canvas_frame.grid_columnconfigure(0, weight=1)
        
        # Canvas events
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)
        self.canvas.bind("<Double-Button-1>", self.on_canvas_double_click)
        
        # Draw initial grid and guides
        self.draw_grid()
        self.draw_page_guides()
    
    def create_rulers(self, parent):
        # Top ruler
        self.h_ruler = tk.Canvas(parent, height=25, bg='#f0f0f0')
        self.h_ruler.pack(fill='x', side='top')
        
        # Left ruler  
        self.v_ruler = tk.Canvas(parent, width=25, bg='#f0f0f0')
        self.v_ruler.pack(fill='y', side='left')
        
        self.draw_rulers()
    
    def draw_rulers(self):
        # Clear rulers
        self.h_ruler.delete("all")
        self.v_ruler.delete("all")
        
        # Draw horizontal ruler
        for i in range(0, self.canvas_width, 50):
            self.h_ruler.create_line(i, 20, i, 25, fill='#666')
            self.h_ruler.create_text(i+25, 12, text=str(i//50), font=('Arial', 8))
        
        # Draw vertical ruler
        for i in range(0, self.canvas_height, 50):
            self.v_ruler.create_line(20, i, 25, i, fill='#666')
            self.v_ruler.create_text(12, i+25, text=str(i//50), font=('Arial', 8))
    
    def create_right_panel(self, parent):
        right_panel = tk.Frame(parent, bg='white', width=300)
        parent.add(right_panel)
        
        # Properties panel
        self.create_properties_panel(right_panel)
    
    def create_properties_panel(self, parent):
        # Properties header
        prop_header = tk.Label(parent, text="Properties", font=('Segoe UI', 12, 'bold'),
                              fg='#2c3e50', bg='#ecf0f1', padx=10, pady=8)
        prop_header.pack(fill='x')
        
        # Properties content
        self.props_frame = tk.Frame(parent, bg='white')
        self.props_frame.pack(fill='both', expand=True, padx=5, pady=5)
        
        # Default properties message
        self.show_default_properties()
    
    def show_default_properties(self):
        # Clear properties
        for widget in self.props_frame.winfo_children():
            widget.destroy()
        
        tk.Label(self.props_frame, text="Select an element\nto view properties",
                font=('Segoe UI', 11), fg='#7f8c8d', bg='white',
                justify='center').pack(expand=True)
    
    def create_status_bar(self):
        self.status_bar = tk.Frame(self.window, bg='#34495e', height=25)
        self.status_bar.pack(fill='x', side='bottom')
        self.status_bar.pack_propagate(False)
        
        # Status elements
        self.status_label = tk.Label(self.status_bar, text="Ready", 
                                   font=('Segoe UI', 9), fg='white', bg='#34495e')
        self.status_label.pack(side='left', padx=10)
        
        # Zoom level
        self.zoom_label = tk.Label(self.status_bar, text=f"Zoom: {int(self.zoom_level*100)}%",
                                 font=('Segoe UI', 9), fg='white', bg='#34495e')
        self.zoom_label.pack(side='right', padx=10)
        
        # Position
        self.position_label = tk.Label(self.status_bar, text="X: 0, Y: 0",
                                     font=('Segoe UI', 9), fg='white', bg='#34495e')
        self.position_label.pack(side='right', padx=10)
    
    def create_keyboard_bindings(self):
        self.window.bind('<Control-s>', lambda e: self.save_template())
        self.window.bind('<Control-o>', lambda e: self.open_template())
        self.window.bind('<Control-n>', lambda e: self.new_template())
        self.window.bind('<Control-z>', lambda e: self.undo())
        self.window.bind('<Control-y>', lambda e: self.redo())
        self.window.bind('<Control-c>', lambda e: self.copy())
        self.window.bind('<Control-x>', lambda e: self.cut())
        self.window.bind('<Control-v>', lambda e: self.paste())
        self.window.bind('<Delete>', lambda e: self.delete_selected())
        self.window.bind('<Control-a>', lambda e: self.select_all())
        self.window.bind('<Control-plus>', lambda e: self.zoom_in())
        self.window.bind('<Control-minus>', lambda e: self.zoom_out())
        self.window.bind('<Control-0>', lambda e: self.zoom_fit())
        
    def create_tooltip(self, widget, text):
        def on_enter(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            tk.Label(tooltip, text=text, bg='lightyellow', font=('Arial', 9)).pack()
            widget.tooltip = tooltip
            
        def on_leave(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
                
        widget.bind('<Enter>', on_enter)
        widget.bind('<Leave>', on_leave)
    
    def draw_grid(self):
        if not self.show_grid:
            return
            
        # Remove old grid
        self.canvas.delete("grid")
        
        # Draw grid
        for x in range(0, self.canvas_width, self.grid_size):
            self.canvas.create_line(x, 0, x, self.canvas_height, 
                                  fill=self.grid_color, tags="grid")
        
        for y in range(0, self.canvas_height, self.grid_size):
            self.canvas.create_line(0, y, self.canvas_width, y, 
                                  fill=self.grid_color, tags="grid")
    
    def draw_page_guides(self):
        # Remove old guides
        self.canvas.delete("guide")
        
        # Page margins (20mm = ~75px at 96 DPI)
        margin = 75
        
        # Page border
        self.canvas.create_rectangle(5, 5, self.canvas_width-5, self.canvas_height-5,
                                   outline='#bdc3c7', width=2, tags="guide")
        
        # Margin guides
        self.canvas.create_rectangle(margin, margin, 
                                   self.canvas_width-margin, self.canvas_height-margin,
                                   outline='#e74c3c', width=1, dash=(5, 5), tags="guide")
        
        # Section dividers
        header_y = 150
        footer_y = self.canvas_height - 150
        
        self.canvas.create_line(margin, header_y, self.canvas_width-margin, header_y,
                              fill='#3498db', width=2, tags="guide")
        self.canvas.create_line(margin, footer_y, self.canvas_width-margin, footer_y,
                              fill='#f39c12', width=2, tags="guide")
        
        # Section labels
        self.canvas.create_text(20, 80, text="HEADER", fill='#3498db', 
                              font=('Arial', 10, 'bold'), anchor='w', tags="guide")
        self.canvas.create_text(20, (header_y + footer_y) // 2, text="DETAIL", 
                              fill='#27ae60', font=('Arial', 10, 'bold'), 
                              anchor='w', tags="guide")
        self.canvas.create_text(20, footer_y + 30, text="FOOTER", fill='#f39c12', 
                              font=('Arial', 10, 'bold'), anchor='w', tags="guide")
    
    # Element management methods
    def add_element(self, element_type):
        """Add new element to canvas"""
        x, y = 100, 100  # Default position
        
        if element_type == 'label':
            element = {
                'type': 'label',
                'id': self.generate_id(),
                'x': x, 'y': y, 'width': 100, 'height': 25,
                'text': 'Label',
                'font_family': 'Arial',
                'font_size': 12,
                'font_bold': False,
                'font_italic': False,
                'color': '#000000',
                'background': '#ffffff',
                'border': False,
                'align': 'left'
            }
        elif element_type == 'textbox':
            element = {
                'type': 'textbox',
                'id': self.generate_id(),
                'x': x, 'y': y, 'width': 150, 'height': 25,
                'text': 'Text Box',
                'font_family': 'Arial',
                'font_size': 11,
                'color': '#000000',
                'background': '#ffffff',
                'border': True,
                'multiline': False
            }
        elif element_type == 'picturebox':
            element = {
                'type': 'picturebox',
                'id': self.generate_id(),
                'x': x, 'y': y, 'width': 100, 'height': 100,
                'image_path': '',
                'border': True,
                'stretch': False
            }
        elif element_type == 'line':
            element = {
                'type': 'line',
                'id': self.generate_id(),
                'x': x, 'y': y, 'width': 150, 'height': 2,
                'color': '#000000',
                'thickness': 1,
                'style': 'solid'
            }
        elif element_type == 'shape':
            element = {
                'type': 'shape',
                'id': self.generate_id(),
                'x': x, 'y': y, 'width': 100, 'height': 100,
                'shape_type': 'rectangle',
                'border_color': '#000000',
                'fill_color': '#ffffff',
                'border_width': 1
            }
        elif element_type == 'table':
            element = {
                'type': 'table',
                'id': self.generate_id(),
                'x': x, 'y': y, 'width': 400, 'height': 200,
                'rows': 5,
                'columns': 4,
                'border': True,
                'font_family': 'Arial',
                'font_size': 10
            }
        elif element_type == 'chart':
            element = {
                'type': 'chart',
                'id': self.generate_id(),
                'x': x, 'y': y, 'width': 300, 'height': 200,
                'chart_type': 'bar',
                'data_source': '',
                'title': 'Chart Title'
            }
        elif element_type == 'pageinfo':
            element = {
                'type': 'pageinfo',
                'id': self.generate_id(),
                'x': x, 'y': y, 'width': 100, 'height': 20,
                'info_type': 'page_number',
                'format': 'Page {0}',
                'font_family': 'Arial',
                'font_size': 10
            }
        elif element_type == 'datetime':
            element = {
                'type': 'datetime',
                'id': self.generate_id(),
                'x': x, 'y': y, 'width': 150, 'height': 20,
                'format': 'dd/MM/yyyy',
                'font_family': 'Arial',
                'font_size': 10,
                'color': '#000000'
            }
        elif element_type == 'datafield':
            element = {
                'type': 'datafield',
                'id': self.generate_id(),
                'x': x, 'y': y, 'width': 150, 'height': 25,
                'field_name': 'field_name',
                'text': '[Data Field]',
                'font_family': 'Arial',
                'font_size': 11,
                'color': '#0066cc',
                'format': ''
            }
        elif element_type == 'calculated':
            element = {
                'type': 'calculated',
                'id': self.generate_id(),
                'x': x, 'y': y, 'width': 150, 'height': 25,
                'formula': 'SUM(Amount)',
                'text': '[Calculated]',
                'font_family': 'Arial',
                'font_size': 11,
                'color': '#cc6600'
            }
        elif element_type == 'crosstab':
            element = {
                'type': 'crosstab',
                'id': self.generate_id(),
                'x': x, 'y': y, 'width': 300, 'height': 150,
                'data_source': '',
                'row_fields': [],
                'column_fields': [],
                'data_fields': []
            }
        elif element_type == 'subreport':
            element = {
                'type': 'subreport',
                'id': self.generate_id(),
                'x': x, 'y': y, 'width': 200, 'height': 100,
                'report_path': '',
                'parameters': {}
            }
        else:
            # Default element if type not found
            element = {
                'type': 'label',
                'id': self.generate_id(),
                'x': x, 'y': y, 'width': 100, 'height': 25,
                'text': f'{element_type.title()}',
                'font_family': 'Arial',
                'font_size': 12,
                'color': '#000000',
                'background': '#ffffff'
            }
        
        self.elements.append(element)
        self.redraw_canvas()
        self.select_element(len(self.elements) - 1)
        self.update_status(f"Added {element_type}")
            
    def generate_id(self):
        return f"element_{len(self.elements) + 1}"
    
    def redraw_canvas(self):
        # Clear elements (keep grid and guides)
        self.canvas.delete("element")
        
        # Redraw all elements
        for i, element in enumerate(self.elements):
            self.draw_element(element, i)
    
    def draw_element(self, element, index):
        x, y = element['x'], element['y']
        width, height = element['width'], element['height']
        
        if element['type'] == 'label':
            # Draw text
            self.canvas.create_text(x + 5, y + height//2, 
                                text=element['text'],
                                font=(element['font_family'], element['font_size']),
                                fill=element['color'],
                                anchor='w',
                                tags=("element", f"element_{index}"))
        
        elif element['type'] == 'textbox':
            # Draw textbox background
            self.canvas.create_rectangle(x, y, x + width, y + height,
                                    fill=element['background'], 
                                    outline='#cccccc' if element['border'] else '',
                                    tags=("element", f"element_{index}"))
            # Draw text
            self.canvas.create_text(x + 5, y + height//2,
                                text=element['text'],
                                font=(element['font_family'], element['font_size']),
                                fill=element['color'],
                                anchor='w',
                                tags=("element", f"element_{index}"))
        
        elif element['type'] == 'picturebox':
            # Draw picture placeholder
            self.canvas.create_rectangle(x, y, x + width, y + height,
                                    fill='#f0f0f0',
                                    outline='#cccccc',
                                    tags=("element", f"element_{index}"))
            self.canvas.create_text(x + width//2, y + height//2,
                                text="📷 Picture",
                                font=('Arial', 10),
                                fill='#666666',
                                tags=("element", f"element_{index}"))
        
        elif element['type'] == 'line':
            # Draw line
            self.canvas.create_line(x, y + height//2, x + width, y + height//2,
                                fill=element['color'],
                                width=element.get('thickness', 1),
                                tags=("element", f"element_{index}"))
        
        elif element['type'] == 'shape':
            # Draw shape
            if element.get('shape_type', 'rectangle') == 'rectangle':
                self.canvas.create_rectangle(x, y, x + width, y + height,
                                        fill=element.get('fill_color', '#ffffff'),
                                        outline=element.get('border_color', '#000000'),
                                        tags=("element", f"element_{index}"))
        
        elif element['type'] == 'table':
            # Draw table
            rows = element.get('rows', 5)
            cols = element.get('columns', 4)
            cell_width = width // cols
            cell_height = height // rows
            
            for row in range(rows + 1):
                y_pos = y + (row * cell_height)
                self.canvas.create_line(x, y_pos, x + width, y_pos,
                                    fill='#000000',
                                    tags=("element", f"element_{index}"))
            
            for col in range(cols + 1):
                x_pos = x + (col * cell_width)
                self.canvas.create_line(x_pos, y, x_pos, y + height,
                                    fill='#000000',
                                    tags=("element", f"element_{index}"))
        
        else:
            # Default drawing for unknown types
            self.canvas.create_rectangle(x, y, x + width, y + height,
                                    fill='#f0f0f0',
                                    outline='#cccccc',
                                    tags=("element", f"element_{index}"))
            self.canvas.create_text(x + width//2, y + height//2,
                                text=element['type'].title(),
                                font=('Arial', 10),
                                fill='#666666',
                                tags=("element", f"element_{index}"))
        
        # Draw selection if this element is selected
        if self.selected_element == index:
            self.canvas.create_rectangle(x, y, x + width, y + height,
                                    outline=self.selection_color, width=2,
                                    tags=("element", "selection"))
            
            # Selection handles
            self.draw_selection_handles(x, y, width, height)
                
    def draw_selection_handles(self, x, y, width, height):
        handle_size = 6
        positions = [
            (x, y),  # Top-left
            (x + width//2, y),  # Top-center
            (x + width, y),  # Top-right
            (x, y + height//2),  # Middle-left
            (x + width, y + height//2),  # Middle-right
            (x, y + height),  # Bottom-left
            (x + width//2, y + height),  # Bottom-center
            (x + width, y + height),  # Bottom-right
        ]
        
        for hx, hy in positions:
            self.canvas.create_rectangle(hx - handle_size//2, hy - handle_size//2,
                                       hx + handle_size//2, hy + handle_size//2,
                                       fill='white', outline=self.selection_color,
                                       tags=("element", "handle"))
    
    def select_element(self, index):
        self.selected_element = index
        self.redraw_canvas()
        self.show_element_properties(self.elements[index])
    
    def show_element_properties(self, element):
        # Clear properties
        for widget in self.props_frame.winfo_children():
            widget.destroy()
        
        # Create property editors based on element type
        if element['type'] == 'label':
            self.create_label_properties(element)
    
    def create_label_properties(self, element):
        # Text property
        tk.Label(self.props_frame, text="Text:", font=('Segoe UI', 9, 'bold'),
                bg='white').pack(anchor='w', pady=(5, 0))
        text_var = tk.StringVar(value=element['text'])
        text_entry = tk.Entry(self.props_frame, textvariable=text_var)
        text_entry.pack(fill='x', pady=(0, 10))
        
        # Font properties
        tk.Label(self.props_frame, text="Font:", font=('Segoe UI', 9, 'bold'),
                bg='white').pack(anchor='w')
        
        font_frame = tk.Frame(self.props_frame, bg='white')
        font_frame.pack(fill='x', pady=(0, 10))
        
        # Font family
        font_var = tk.StringVar(value=element['font_family'])
        font_combo = ttk.Combobox(font_frame, textvariable=font_var, 
                                 values=['Arial', 'Helvetica', 'Times New Roman', 'Courier'])
        font_combo.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        # Font size
        size_var = tk.StringVar(value=str(element['font_size']))
        size_entry = tk.Entry(font_frame, textvariable=size_var, width=5)
        size_entry.pack(side='right')
        
        # Color
        tk.Label(self.props_frame, text="Color:", font=('Segoe UI', 9, 'bold'),
                bg='white').pack(anchor='w', pady=(10, 0))
        
        color_frame = tk.Frame(self.props_frame, bg='white')
        color_frame.pack(fill='x', pady=(0, 10))
        
        color_btn = tk.Button(color_frame, text="Choose Color", 
                            bg=element['color'], width=15,
                            command=lambda: self.choose_color(element))
        color_btn.pack(side='left')
        
        # Position and Size
        tk.Label(self.props_frame, text="Position & Size:", font=('Segoe UI', 9, 'bold'),
                bg='white').pack(anchor='w', pady=(10, 0))
        
        pos_frame = tk.Frame(self.props_frame, bg='white')
        pos_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(pos_frame, text="X:", bg='white').grid(row=0, column=0, sticky='w')
        x_var = tk.StringVar(value=str(element['x']))
        tk.Entry(pos_frame, textvariable=x_var, width=8).grid(row=0, column=1, padx=5)
        
        tk.Label(pos_frame, text="Y:", bg='white').grid(row=0, column=2, sticky='w')
        y_var = tk.StringVar(value=str(element['y']))
        tk.Entry(pos_frame, textvariable=y_var, width=8).grid(row=0, column=3, padx=5)
        
        tk.Label(pos_frame, text="W:", bg='white').grid(row=1, column=0, sticky='w')
        w_var = tk.StringVar(value=str(element['width']))
        tk.Entry(pos_frame, textvariable=w_var, width=8).grid(row=1, column=1, padx=5)
        
        tk.Label(pos_frame, text="H:", bg='white').grid(row=1, column=2, sticky='w')
        h_var = tk.StringVar(value=str(element['height']))
        tk.Entry(pos_frame, textvariable=h_var, width=8).grid(row=1, column=3, padx=5)
        
        # Update button
        def update_element():
            element['text'] = text_var.get()
            element['font_family'] = font_var.get()
            element['font_size'] = int(size_var.get())
            element['x'] = int(x_var.get())
            element['y'] = int(y_var.get())
            element['width'] = int(w_var.get())
            element['height'] = int(h_var.get())
            self.redraw_canvas()
        
        tk.Button(self.props_frame, text="Apply Changes", 
                 bg='#3498db', fg='white', command=update_element).pack(pady=20)
    
    def choose_color(self, element):
        color = colorchooser.askcolor(initialcolor=element['color'])[1]
        if color:
            element['color'] = color
            self.redraw_canvas()
    
    # Canvas event handlers
    def on_canvas_click(self, event):
        # Convert screen coordinates to canvas coordinates
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        
        # Find clicked element
        clicked_items = self.canvas.find_overlapping(canvas_x-5, canvas_y-5, 
                                                   canvas_x+5, canvas_y+5)
        
        element_clicked = False
        for item in clicked_items:
            tags = self.canvas.gettags(item)
            if 'element' in tags:
                for tag in tags:
                    if tag.startswith('element_') and tag != 'element':
                        index = int(tag.split('_')[1])
                        self.select_element(index)
                        element_clicked = True
                        break
                if element_clicked:
                    break
        
        if not element_clicked:
            self.selected_element = None
            self.redraw_canvas()
            self.show_default_properties()
        
        # Update status bar
        self.position_label.config(text=f"X: {int(canvas_x)}, Y: {int(canvas_y)}")
    
    def on_canvas_drag(self, event):
        if self.selected_element is not None:
            canvas_x = self.canvas.canvasx(event.x)
            canvas_y = self.canvas.canvasy(event.y)
            
            # Snap to grid if enabled
            if self.snap_to_grid:
                canvas_x = round(canvas_x / self.grid_size) * self.grid_size
                canvas_y = round(canvas_y / self.grid_size) * self.grid_size
            
            element = self.elements[self.selected_element]
            element['x'] = int(canvas_x)
            element['y'] = int(canvas_y)
            
            self.redraw_canvas()
            self.position_label.config(text=f"X: {int(canvas_x)}, Y: {int(canvas_y)}")
    
    def on_canvas_release(self, event):
        pass
    
    def on_canvas_double_click(self, event):
        if self.selected_element is not None:
            element = self.elements[self.selected_element]
            if element['type'] == 'label':
                # Edit text inline
                self.edit_text_inline(element)
    
    def edit_text_inline(self, element):
        # Create temporary entry for inline editing
        x, y = element['x'], element['y']
        entry = tk.Entry(self.canvas, font=(element['font_family'], element['font_size']))
        entry.insert(0, element['text'])
        
        canvas_widget = self.canvas.create_window(x, y, window=entry, anchor='nw')
        
        def finish_edit():
            element['text'] = entry.get()
            self.canvas.delete(canvas_widget)
            self.redraw_canvas()
        
        entry.bind('<Return>', lambda e: finish_edit())
        entry.bind('<FocusOut>', lambda e: finish_edit())
        entry.focus()
    
    def add_field_from_tree(self, event):
        selection = self.field_tree.selection()
        if selection:
            item = selection[0]
            field_id = self.field_tree.item(item, 'values')
            if field_id and field_id[0] != 'folder':
                # Add data field element
                element = {
                    'type': 'datafield',
                    'id': self.generate_id(),
                    'x': 100, 'y': 100, 'width': 150, 'height': 25,
                    'field_name': field_id[0],
                    'text': f'[{field_id[0]}]',
                    'font_family': 'Arial',
                    'font_size': 11,
                    'color': '#0066cc'
                }
                self.elements.append(element)
                self.redraw_canvas()
    
    # File operations
    def new_template(self):
        if self.elements and messagebox.askyesno("New Template", 
                                                "Current template will be lost. Continue?"):
            self.elements = []
            self.selected_element = None
            self.redraw_canvas()
            self.show_default_properties()
            self.update_status("New template created")
    
    def open_template(self):
        file_path = filedialog.askopenfilename(
            title="Open Template",
            filetypes=[("JSON Template", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.elements = data.get('elements', [])
                self.selected_element = None
                self.redraw_canvas()
                self.show_default_properties()
                self.update_status(f"Loaded: {os.path.basename(file_path)}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load template: {str(e)}")
    
    def save_template(self):
        try:
            template_data = {
                'type': self.template_type,
                'created_date': datetime.now().isoformat(),
                'canvas_width': self.canvas_width,
                'canvas_height': self.canvas_height,
                'elements': self.elements
            }
            
            with open(self.template_file, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, ensure_ascii=False, indent=4)
            
            self.update_status(f"Saved: {self.template_file}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save template: {str(e)}")
    
    def save_as_template(self):
        file_path = filedialog.asksaveasfilename(
            title="Save Template As",
            defaultextension=".json",
            filetypes=[("JSON Template", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            self.template_file = file_path
            self.save_template()
    
    def load_existing_template(self):
        if os.path.exists(self.template_file):
            try:
                with open(self.template_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.elements = data.get('elements', [])
                self.redraw_canvas()
                self.update_status(f"Loaded existing template: {self.template_file}")
                
            except Exception as e:
                self.update_status(f"Failed to load existing template: {str(e)}")
        else:
            self.update_status("Creating new template")
    
    # Edit operations
    def copy(self):
        if self.selected_element is not None:
            self.clipboard = self.elements[self.selected_element].copy()
            self.update_status("Element copied")
    
    def cut(self):
        if self.selected_element is not None:
            self.clipboard = self.elements[self.selected_element].copy()
            del self.elements[self.selected_element]
            self.selected_element = None
            self.redraw_canvas()
            self.show_default_properties()
            self.update_status("Element cut")
    
    def paste(self):
        if self.clipboard:
            new_element = self.clipboard.copy()
            new_element['id'] = self.generate_id()
            new_element['x'] += 20  # Offset
            new_element['y'] += 20
            self.elements.append(new_element)
            self.select_element(len(self.elements) - 1)
            self.update_status("Element pasted")
    
    def delete_selected(self):
        if self.selected_element is not None:
            del self.elements[self.selected_element]
            self.selected_element = None
            self.redraw_canvas()
            self.show_default_properties()
            self.update_status("Element deleted")
    
    def select_all(self):
        # TODO: Implement multi-selection
        pass
    
    def undo(self):
        # TODO: Implement undo/redo system
        pass
    
    def redo(self):
        # TODO: Implement undo/redo system
        pass
    
    # View operations
    def zoom_in(self):
        self.zoom_level = min(self.zoom_level * 1.2, 5.0)
        self.apply_zoom()
    
    def zoom_out(self):
        self.zoom_level = max(self.zoom_level / 1.2, 0.1)
        self.apply_zoom()
    
    def zoom_fit(self):
        self.zoom_level = 1.0
        self.apply_zoom()
    
    def apply_zoom(self):
        # TODO: Implement zoom functionality
        self.zoom_label.config(text=f"Zoom: {int(self.zoom_level*100)}%")
    
    def toggle_grid(self):
        self.show_grid = not self.show_grid
        self.draw_grid()
    
    def toggle_snap(self):
        self.snap_to_grid = not self.snap_to_grid
        self.update_status(f"Snap to grid: {'On' if self.snap_to_grid else 'Off'}")
    
    # Format operations
    def align_elements(self, alignment):
        # TODO: Implement alignment
        pass
    
    def same_width(self):
        # TODO: Implement same width
        pass
    
    def same_height(self):
        # TODO: Implement same height
        pass
    
    def same_size(self):
        # TODO: Implement same size
        pass
    
    # Export operations
    def export_pdf(self):
        messagebox.showinfo("Export PDF", "PDF export will be implemented")
    
    def update_status(self, message):
        self.status_label.config(text=message)
        # Auto-clear after 3 seconds
        self.window.after(3000, lambda: self.status_label.config(text="Ready"))

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()
    
    app = ProfessionalFormDesigner(None, "purchase")
    root.mainloop()