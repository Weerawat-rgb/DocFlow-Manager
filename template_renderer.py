from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import json
import os
from datetime import datetime
from data_provider import DataProvider, format_currency, format_date_thai

class TemplateRenderer:
    def __init__(self, template_path):
        self.template_path = template_path
        self.template_data = None
        self.data_provider = DataProvider()
        
        # Load template
        self.load_template()
        
        # Register Thai fonts (if available)
        self.register_fonts()
        
    def register_fonts(self):
        """Register Thai fonts"""
        try:
            # ลองใช้ฟอนต์ Thai ที่มีในระบบ
            font_paths = [
                'C:/Windows/Fonts/tahoma.ttf',
                'C:/Windows/Fonts/tahomabd.ttf',
            ]
            
            for font_path in font_paths:
                if os.path.exists(font_path):
                    font_name = os.path.basename(font_path).replace('.ttf', '')
                    pdfmetrics.registerFont(TTFont(font_name, font_path))
                    
        except Exception as e:
            print(f"Font registration warning: {e}")
    
    def load_template(self):
        """Load template from JSON file"""
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                self.template_data = json.load(f)
            return True
        except Exception as e:
            print(f"Error loading template: {e}")
            return False
    
    def render_to_pdf(self, output_path, data_filter=None):
        """Render template to PDF with real data"""
        if not self.template_data:
            print("No template loaded")
            return False
        
        # Connect to database
        if not self.data_provider.connect():
            print("Database connection failed")
            return False
        
        try:
            # Get data based on template type
            template_type = self.template_data.get('type', 'invoice')
            
            if template_type == 'purchase':
                # สำหรับใบวางบิลซื้อ - ดึงข้อมูลจากตารางที่เกี่ยวข้อง
                data = self.get_purchase_data(data_filter)
            elif template_type == 'sales':
                # สำหรับใบวางบิลขาย - ใช้ query ที่ให้มา
                data = self.data_provider.get_invoice_data(
                    invoice_id=data_filter.get('invoice_id') if data_filter else None,
                    customer_id=data_filter.get('customer_id') if data_filter else None
                )
            elif template_type == 'branch':
                # สำหรับใบวางบิลสาขา
                data = self.get_branch_transfer_data(data_filter)
            else:
                data = self.data_provider.get_sample_data()
            
            if not data:
                print("No data found")
                return False
            
            # Create PDF
            self.create_pdf(output_path, data[0] if isinstance(data, list) else data)
            
            self.data_provider.disconnect()
            return True
            
        except Exception as e:
            print(f"Error rendering PDF: {e}")
            self.data_provider.disconnect()
            return False
    
    def get_purchase_data(self, data_filter):
        """Get purchase order data"""
        # ปรับ query ตามโครงสร้างจริงของใบสั่งซื้อ
        query = """
            SELECT 
                po.PurchaseOrderId,
                po.PONumber,
                po.PODate,
                po.DeliveryDate,
                s.SupplierName,
                s.SupplierAddress,
                s.SupplierPhone,
                s.TaxNumber AS SupplierTaxNum,
                po.SubTotal,
                po.Tax,
                po.Total,
                po.Status
            FROM PurchaseOrder po
            INNER JOIN Supplier s ON s.SupplierId = po.SupplierId
            WHERE po.Active = 1
        """
        
        params = []
        if data_filter and data_filter.get('po_id'):
            query += " AND po.PurchaseOrderId = ?"
            params.append(data_filter['po_id'])
        
        result = self.data_provider.execute_query(query, params)
        
        # เพิ่มรายการสินค้า
        if result:
            po_id = result[0]['PurchaseOrderId']
            items_query = """
                SELECT 
                    pod.ItemCode,
                    i.ItemName,
                    pod.Quantity,
                    pod.UnitPrice,
                    pod.Amount,
                    i.Unit
                FROM PurchaseOrderDetail pod
                INNER JOIN Item i ON i.ItemCode = pod.ItemCode
                WHERE pod.PurchaseOrderId = ?
                ORDER BY pod.LineNumber
            """
            result[0]['items'] = self.data_provider.execute_query(items_query, [po_id])
        
        return result
    
    def get_branch_transfer_data(self, data_filter):
        """Get branch transfer data"""
        # ปรับตามโครงสร้างของใบโอนสาขา
        query = """
            SELECT 
                bt.TransferId,
                bt.TransferNumber,
                bt.TransferDate,
                bf.BranchName AS FromBranch,
                bt.BranchName AS ToBranch,
                bt.SubTotal,
                bt.Tax,
                bt.Total,
                bt.Status
            FROM BranchTransfer bt
            INNER JOIN Branch bf ON bf.BranchId = bt.FromBranchId
            WHERE bt.Active = 1
        """
        
        # เพิ่มเงื่อนไขตาม data_filter
        return self.data_provider.execute_query(query)
    
    def create_pdf(self, output_path, data):
        """Create PDF from template and data"""
        # Create canvas
        c = canvas.Canvas(output_path, pagesize=A4)
        width, height = A4
        
        # Get company info
        company_info = self.data_provider.get_company_info()
        
        # Process each element in template
        elements = self.template_data.get('elements', [])
        
        for element in elements:
            self.render_element(c, element, data, company_info)
        
        # Save PDF
        c.save()
        print(f"PDF created: {output_path}")
    
    def render_element(self, canvas, element, data, company_info):
        """Render individual element"""
        x = element['x']
        y = A4[1] - element['y']  # Convert Y coordinate (PDF origin is bottom-left)
        
        element_type = element['type']
        
        if element_type == 'label':
            self.render_text_element(canvas, element, x, y)
            
        elif element_type == 'datafield':
            self.render_data_field(canvas, element, x, y, data, company_info)
            
        elif element_type == 'table' or element_type == 'data_table':
            self.render_data_table(canvas, element, x, y, data)
            
        elif element_type == 'line':
            self.render_line(canvas, element, x, y)
            
        elif element_type == 'calculated':
            self.render_calculated_field(canvas, element, x, y, data)
            
        elif element_type == 'conditional_text':
            self.render_conditional_text(canvas, element, x, y, data)
    
    def render_text_element(self, canvas, element, x, y):
        """Render static text"""
        text = element.get('text', '')
        font_family = element.get('font_family', 'Helvetica')
        font_size = element.get('font_size', 12)
        color = element.get('color', '#000000')
        
        # Set font and color
        canvas.setFont(font_family, font_size)
        if color != '#000000':
            rgb = self.hex_to_rgb(color)
            canvas.setFillColorRGB(*rgb)
        
        canvas.drawString(x, y, text)
    
    def render_data_field(self, canvas, element, x, y, data, company_info):
        """Render database field"""
        field_name = element.get('field_name', element.get('text', ''))
        field_type = element.get('field_type', 'string')
        font_family = element.get('font_family', 'Helvetica')
        font_size = element.get('font_size', 12)
        
        # Get value from data
        value = self.get_field_value(field_name, data, company_info)
        
        # Format value based on type
        if field_type == 'currency':
            formatted_value = format_currency(value)
        elif field_type == 'date':
            formatted_value = format_date_thai(value)
        else:
            formatted_value = str(value) if value is not None else ''
        
        # Set font
        canvas.setFont(font_family, font_size)
        canvas.drawString(x, y, formatted_value)
    
    def render_data_table(self, canvas, element, x, y, data):
        """Render data table"""
        items = data.get('items', [])
        if not items:
            return
        
        # Table properties
        table_width = element.get('width', 400)
        table_height = element.get('height', 200)
        columns = element.get('columns', [
            {'name': 'ItemName', 'label': 'รายการ', 'width': 200},
            {'name': 'Quantity', 'label': 'จำนวน', 'width': 80},
            {'name': 'UnitPrice', 'label': 'ราคา/หน่วย', 'width': 80},
            {'name': 'Amount', 'label': 'รวม', 'width': 80}
        ])
        
        # Calculate column positions
        current_x = x
        row_height = 20
        current_y = y
        
        # Draw headers
        canvas.setFont('Helvetica-Bold', 10)
        for col in columns:
            canvas.drawString(current_x + 5, current_y, col['label'])
            current_x += col['width']
        
        # Draw header line
        canvas.line(x, current_y - 5, x + table_width, current_y - 5)
        current_y -= row_height
        
        # Draw data rows
        canvas.setFont('Helvetica', 10)
        for item in items[:10]:  # Limit to 10 rows for space
            current_x = x
            for col in columns:
                value = item.get(col['name'], '')
                if col['name'] in ['UnitPrice', 'Amount'] and value:
                    value = format_currency(value)
                canvas.drawString(current_x + 5, current_y, str(value))
                current_x += col['width']
            current_y -= row_height
        
        # Draw table borders
        canvas.rect(x, current_y, table_width, y - current_y)
        
        # Draw column separators
        current_x = x
        for col in columns[:-1]:
            current_x += col['width']
            canvas.line(current_x, current_y, current_x, y)
    
    def render_line(self, canvas, element, x, y):
        """Render line"""
        x2 = element.get('x2', x + element.get('width', 100))
        y2 = A4[1] - element.get('y2', element.get('y', 0))
        width = element.get('thickness', 1)
        
        canvas.setLineWidth(width)
        canvas.line(x, y, x2, y2)
    
    def render_calculated_field(self, canvas, element, x, y, data):
        """Render calculated field"""
        formula = element.get('formula', '')
        font_family = element.get('font_family', 'Helvetica')
        font_size = element.get('font_size', 12)
        
        # Simple calculation examples
        value = 0
        if formula == 'SUM(Amount)' and 'items' in data:
            value = sum(item.get('Amount', 0) for item in data['items'])
        elif formula == 'COUNT(items)' and 'items' in data:
            value = len(data['items'])
        elif formula.startswith('FIELD:'):
            field_name = formula.replace('FIELD:', '')
            value = data.get(field_name, 0)
        
        formatted_value = format_currency(value) if 'Amount' in formula else str(value)
        
        canvas.setFont(font_family, font_size)
        canvas.drawString(x, y, formatted_value)
    
    def render_conditional_text(self, canvas, element, x, y, data):
        """Render conditional text"""
        conditions = element.get('conditions', [])
        default_text = element.get('default_text', '')
        font_family = element.get('font_family', 'Helvetica')
        font_size = element.get('font_size', 12)
        
        # Check conditions
        text_to_show = default_text
        color = '#000000'
        
        for condition in conditions:
            field = condition.get('field', '')
            operator = condition.get('operator', '==')
            expected_value = condition.get('value', '')
            condition_text = condition.get('text', '')
            condition_color = condition.get('color', '#000000')
            
            field_value = data.get(field, '')
            
            # Simple condition checking
            if operator == '==' and str(field_value) == str(expected_value):
                text_to_show = condition_text
                color = condition_color
                break
            elif operator == '!=' and str(field_value) != str(expected_value):
                text_to_show = condition_text
                color = condition_color
                break
            elif operator == '>' and float(field_value or 0) > float(expected_value):
                text_to_show = condition_text
                color = condition_color
                break
        
        # Set color and font
        if color != '#000000':
            rgb = self.hex_to_rgb(color)
            canvas.setFillColorRGB(*rgb)
        
        canvas.setFont(font_family, font_size)
        canvas.drawString(x, y, text_to_show)
    
    def get_field_value(self, field_name, data, company_info):
        """Get field value from data or company info"""
        # Remove brackets if present
        field_name = field_name.replace('[', '').replace(']', '')
        
        # Check if it's a company field
        company_fields = {
            'company_name': 'CompanyName',
            'company_address': 'Address',
            'company_phone': 'Phone',
            'company_email': 'Email',
            'company_tax_id': 'TaxNumber'
        }
        
        if field_name in company_fields:
            return company_info.get(company_fields[field_name], '')
        
        # Check in main data
        return data.get(field_name, '')
    
    def hex_to_rgb(self, hex_color):
        """Convert hex color to RGB tuple"""
        hex_color = hex_color.lstrip('#')
        return tuple(int(hex_color[i:i+2], 16)/255.0 for i in (0, 2, 4))

# ===================================
# PDF Preview and Export Functions
# ===================================

class PDFPreviewGenerator:
    def __init__(self, template_path):
        self.renderer = TemplateRenderer(template_path)
    
    def generate_preview(self, output_path, sample_data=None):
        """Generate PDF preview with sample data"""
        if not sample_data:
            # Use sample data from data provider
            sample_data = self.renderer.data_provider.get_sample_data()
        
        return self.renderer.create_pdf(output_path, sample_data)
    
    def generate_with_real_data(self, output_path, data_filter):
        """Generate PDF with real data from database"""
        return self.renderer.render_to_pdf(output_path, data_filter)

# ===================================
# Integration with Form Designer
# ===================================

def export_template_to_pdf(template_file, output_file, data_filter=None):
    """Export template to PDF - main function"""
    try:
        renderer = TemplateRenderer(template_file)
        
        if data_filter:
            # Use real data
            success = renderer.render_to_pdf(output_file, data_filter)
        else:
            # Use sample data for preview
            sample_data = renderer.data_provider.get_sample_data()
            success = renderer.create_pdf(output_file, sample_data)
        
        return success
        
    except Exception as e:
        print(f"Error exporting to PDF: {e}")
        return False

# ===================================
# Template Data Binding Examples
# ===================================

def create_sample_invoice_template():
    """Create a sample invoice template with data binding"""
    template = {
        "type": "sales",
        "created_date": datetime.now().isoformat(),
        "paper_size": "A4",
        "elements": [
            # Header - Company Info
            {
                "type": "datafield",
                "field_name": "company_name",
                "x": 50, "y": 50, "width": 200, "height": 25,
                "font_family": "Helvetica-Bold",
                "font_size": 16
            },
            {
                "type": "datafield", 
                "field_name": "company_address",
                "x": 50, "y": 80, "width": 300, "height": 20,
                "font_size": 10
            },
            
            # Document Header
            {
                "type": "label",
                "text": "ใบแจ้งหนี้ / INVOICE",
                "x": 400, "y": 50, "width": 150, "height": 30,
                "font_family": "Helvetica-Bold",
                "font_size": 18
            },
            {
                "type": "datafield",
                "field_name": "InvoiceNumber", 
                "x": 400, "y": 90, "width": 150, "height": 20,
                "font_size": 12
            },
            {
                "type": "datafield",
                "field_name": "InvoiceDate",
                "field_type": "date",
                "x": 400, "y": 110, "width": 150, "height": 20,
                "font_size": 12
            },
            
            # Customer Info
            {
                "type": "label",
                "text": "ลูกค้า:",
                "x": 50, "y": 150, "width": 50, "height": 20,
                "font_family": "Helvetica-Bold"
            },
            {
                "type": "datafield",
                "field_name": "CustomerName",
                "x": 100, "y": 150, "width": 200, "height": 20
            },
            {
                "type": "datafield",
                "field_name": "CustomerAddress", 
                "x": 100, "y": 170, "width": 300, "height": 40
            },
            
            # Items Table
            {
                "type": "data_table",
                "x": 50, "y": 250, "width": 500, "height": 200,
                "columns": [
                    {"name": "ItemName", "label": "รายการ", "width": 200},
                    {"name": "Quantity", "label": "จำนวน", "width": 80}, 
                    {"name": "UnitPrice", "label": "ราคา/หน่วย", "width": 100},
                    {"name": "Amount", "label": "รวม", "width": 120}
                ]
            },
            
            # Totals
            {
                "type": "label",
                "text": "รวมก่อนภาษี:",
                "x": 350, "y": 480, "width": 100, "height": 20,
                "font_family": "Helvetica-Bold"
            },
            {
                "type": "datafield",
                "field_name": "SubTotal",
                "field_type": "currency", 
                "x": 450, "y": 480, "width": 100, "height": 20,
                "align": "right"
            },
            {
                "type": "label",
                "text": "ภาษี 7%:",
                "x": 350, "y": 500, "width": 100, "height": 20,
                "font_family": "Helvetica-Bold"
            },
            {
                "type": "datafield",
                "field_name": "Tax",
                "field_type": "currency",
                "x": 450, "y": 500, "width": 100, "height": 20,
                "align": "right"
            },
            {
                "type": "label", 
                "text": "รวมทั้งสิ้น:",
                "x": 350, "y": 520, "width": 100, "height": 20,
                "font_family": "Helvetica-Bold",
                "font_size": 14
            },
            {
                "type": "datafield",
                "field_name": "Total",
                "field_type": "currency",
                "x": 450, "y": 520, "width": 100, "height": 20,
                "font_family": "Helvetica-Bold",
                "font_size": 14,
                "align": "right"
            },
            
            # Status
            {
                "type": "conditional_text",
                "x": 50, "y": 600, "width": 200, "height": 20,
                "conditions": [
                    {
                        "field": "Status",
                        "operator": "==",
                        "value": "1",
                        "text": "ชำระเงินแล้ว",
                        "color": "#00aa00"
                    },
                    {
                        "field": "Status", 
                        "operator": "==",
                        "value": "0",
                        "text": "รอการชำระเงิน",
                        "color": "#ff6600"
                    }
                ],
                "default_text": "ไม่ระบุสถานะ"
            },
            
            # Signature
            {
                "type": "line",
                "x": 400, "y": 650, "x2": 500, "y2": 650,
                "thickness": 1
            },
            {
                "type": "label",
                "text": "ผู้อนุมัติ",
                "x": 425, "y": 670, "width": 50, "height": 20,
                "font_size": 10
            }
        ]
    }
    
    return template

# ===================================
# Usage Examples
# ===================================

if __name__ == "__main__":
    # Example 1: Create sample template
    sample_template = create_sample_invoice_template()
    with open('sample_invoice_template.json', 'w', encoding='utf-8') as f:
        json.dump(sample_template, f, ensure_ascii=False, indent=4)
    print("✅ Sample template created: sample_invoice_template.json")
    
    # Example 2: Generate PDF preview
    try:
        success = export_template_to_pdf(
            'sample_invoice_template.json', 
            'preview_invoice.pdf'
        )
        if success:
            print("✅ PDF preview generated: preview_invoice.pdf")
        else:
            print("❌ Failed to generate PDF preview")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Example 3: Generate PDF with real data
    try:
        # Filter for specific invoice
        data_filter = {
            'invoice_id': 1,  # Replace with actual invoice ID
        }
        
        success = export_template_to_pdf(
            'sample_invoice_template.json',
            'real_invoice.pdf', 
            data_filter
        )
        if success:
            print("✅ PDF with real data generated: real_invoice.pdf")
        else:
            print("❌ Failed to generate PDF with real data")
    except Exception as e:
        print(f"❌ Error: {e}")