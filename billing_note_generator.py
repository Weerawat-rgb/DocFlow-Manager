import json
import os
from datetime import datetime
from html_template_processor import HTMLTemplateProcessor

# Import Database Manager
try:
    from database_manager import DatabaseManager, get_company_data
    HAS_DATABASE = True
except ImportError:
    print("Warning: database_manager.py not found. Using mock data.")
    HAS_DATABASE = False

class BillingNoteGenerator:
    def __init__(self, parent_window=None, template_type=None):
        """
        Initialize BillingNoteGenerator
        
        Args:
            parent_window: Tkinter parent window (optional)  
            template_type: Type of template (optional) - 'sales', 'purchase', 'branch'
        """
        self.parent_window = parent_window
        self.template_type = template_type
        self.processor = HTMLTemplateProcessor()
        self.config = self.load_config()
        
        # ถ้าเรียกแบบ BillingNoteGenerator(window, type) ให้แสดง preview เลย
        if parent_window and template_type:
            self.show_preview_immediately()
    
    def load_config(self):
        """โหลด config.json"""
        config_path = r'D:\_project\DocFlow-Manager\config.json'
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"ไม่พบไฟล์ config: {config_path}")
            return {"templates": {
                "purchase_template": "ใบวางบิลซื้อ",
                "sales_template": "ใบวางบิลขายสำหรับลูกค้า", 
                "branch_template": "ใบวางบิลสาขา"
            }}
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการอ่าน config: {str(e)}")
            return {"templates": {
                "purchase_template": "ใบวางบิลซื้อ",
                "sales_template": "ใบวางบิลขายสำหรับลูกค้า",
                "branch_template": "ใบวางบิลสาขา"
            }}
    
    def get_document_title(self, template_type=None):
        """ดึงชื่อเอกสารจาก config.json"""
        if template_type is None:
            template_type = self.template_type or 'sales'
        
        template_key = f"{template_type}_template"
        return self.config.get("templates", {}).get(template_key, "ใบวางบิล")
    
    def show_preview_immediately(self):
        """แสดง preview ทันทีด้วยข้อมูลตัวอย่าง"""
        try:
            sample_data = self.create_sample_data()
            self.preview_in_browser(sample_data)
        except Exception as e:
            print(f"Error showing preview: {str(e)}")
    
    def create_sample_data(self):
        """สร้างข้อมูลตัวอย่างสำหรับใบวางบิล - ใช้ข้อมูลจริงจากฐานข้อมูล"""
        document_title = self.get_document_title()
        
        # ดึงข้อมูลบริษัทจากฐานข้อมูล
        if HAS_DATABASE:
            try:
                company_data = get_company_data()
                print("✅ ใช้ข้อมูลบริษัทจากฐานข้อมูล")
            except Exception as e:
                print(f"❌ เกิดข้อผิดพลาดในการดึงข้อมูลจากฐานข้อมูล: {str(e)}")
                company_data = self.get_mock_company_data()
        else:
            company_data = self.get_mock_company_data()
        
        # รวมข้อมูลทั้งหมด
        data = {
            # หัวข้อเอกสาร
            'DocumentTitle': document_title,
        }
        
        # เพิ่มข้อมูลบริษัท
        data.update(company_data)
        
        # เพิ่มข้อมูลอื่น ๆ
        data.update({
            # ข้อมูลลูกค้า (ยังใช้ mock data)
            'CustomerName': 'บริษัท XYZ จำกัด',
            'CustomerAddress': '456 ถนนรัชดาภิเษก แขวงห้วยขวาง เขตห้วยขวาง กรุงเทพฯ 10310',
            'PhoneMobile': '02-987-6543',
            'CustomerTaxNum': '0987654321012',
            
            # ข้อมูลเอกสาร
            'DocNo': 'BL-2025-001',
            'DocDate': '15/01/2025',
            
            # ข้อมูลใบขาย
            'InvoiceNumber': 'INV-2025-001',
            'InvoiceDate': '10/01/2025',
            'MaxDueDate': '30',
            'DueDate': '09/02/2025',
            'Total': '10,700.00',
            'PaidAmount': '0.00',
            'UnpaidAmount': '10,700.00',
            
            # ข้อมูลสรุป
            'TotalUnpaidAmount': '10,700.00',
            'TextThaiBaht': 'หนึ่งหมื่นเจ็ดร้อยบาทถ้วน',
            
            # รายการเพิ่มเติม (ถ้ามี)
            'additionalItems': [
                {
                    'order': 2,  # เพิ่มลำดับ
                    'type': 'ใบขาย',  # เปลี่ยนเป็น ใบแจ้งหนี้
                    'docNo': 'INV-2025-002',
                    'date': '12/01/2025',
                    'credit': '30',
                    'dueDate': '11/02/2025',
                    'total': '5,350.00',
                    'paidAmount': '0.00',
                    'unpaidAmount': '5,350.00'
                }
            ]
        })
        
        return data
    
    def get_mock_company_data(self):
        """ข้อมูลบริษัทตัวอย่าง (fallback)"""
        return {
            'Companyname': 'บริษัท ABC จำกัด',
            'SiteAddress': '123 ถนนสุขุมวิท แขวงคลองตัน เขตคลองตัน กรุงเทพฯ 10110',
            'PhoneNumber': 'โทร: 02-123-4567 แฟกซ์: 02-123-4568',
            'TaxId': 'เลขประจำตัวผู้เสียภาษี: 0123456789012',
            'SitePicture': ''
        }
    
    def generate_html(self, data):
        """สร้าง HTML จากข้อมูล"""
        template_content = self.get_template()
        return self.processor.render_template(template_content, data)
    
    def generate_pdf(self, data, output_path):
        """สร้าง PDF จากข้อมูล"""
        template_content = self.get_template()
        return self.processor.export_to_pdf(template_content, data, output_path)
    
    def preview_in_browser(self, data):
        """แสดงตัวอย่างในเบราว์เซอร์"""
        template_content = self.get_template()
        return self.processor.preview_in_browser(template_content, data)
    
    def get_template(self):
        """ดึง HTML template จากไฟล์หรือใช้ default"""
        template_path = r'D:\_project\DocFlow-Manager\templates\billing_note_template.html'
        
        try:
            # อ่าน template จากไฟล์
            with open(template_path, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"ไม่พบไฟล์ template: {template_path}")
            print("กำลังใช้ template เริ่มต้น...")
            return self.get_default_template()
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการอ่านไฟล์: {str(e)}")
            print("กำลังใช้ template เริ่มต้น...")
            return self.get_default_template()
    
    def get_default_template(self):
        """Template เริ่มต้นกรณีไม่พบไฟล์"""
        return '''<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <title>{{ DocumentTitle }}</title>
    <style>
        body { font-family: Tahoma, Arial, sans-serif; margin: 20px; }
        .container { max-width: 800px; margin: 0 auto; border: 2px solid #000; }
        .header { padding: 20px; border-bottom: 1px solid #000; text-align: center; }
        h1 { margin: 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{{ DocumentTitle }}</h1>
            <p>{{ Companyname }}</p>
            <p>{{ SiteAddress }}</p>
            <p>{{ PhoneNumber }}</p>
            <p>{{ TaxId }}</p>
        </div>
        <div style="padding: 20px;">
            <p>Template เริ่มต้น - กรุณาสร้างไฟล์ templates/billing_note_template.html</p>
        </div>
    </div>
</body>
</html>'''
    
    def generate_from_database_data(self, database_data):
        """สร้างใบวางบิลจากข้อมูล Database"""
        return self.preview_in_browser(database_data)
    
    def generate_pdf_from_database(self, database_data, output_path):
        """สร้าง PDF จากข้อมูล Database"""
        return self.generate_pdf(database_data, output_path)
    
    @staticmethod
    def Preview_Template(template_type=None):
        """แสดงตัวอย่าง Template - สำหรับเรียกจาก config.py"""
        try:
            generator = BillingNoteGenerator(template_type=template_type)
            sample_data = generator.create_sample_data()
            generator.preview_in_browser(sample_data)
        except Exception as e:
            try:
                import tkinter.messagebox as messagebox
                messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถแสดงตัวอย่างได้: {str(e)}")
            except:
                print(f"Error: {str(e)}")
    
    @staticmethod
    def Preview_Template_With_Data(data, template_type=None):
        """แสดงตัวอย่างด้วยข้อมูลที่ส่งมา"""
        try:
            generator = BillingNoteGenerator(template_type=template_type)
            # เพิ่ม DocumentTitle ถ้ายังไม่มี
            if 'DocumentTitle' not in data:
                data['DocumentTitle'] = generator.get_document_title()
            generator.preview_in_browser(data)
        except Exception as e:
            try:
                import tkinter.messagebox as messagebox
                messagebox.showerror("ข้อผิดพลาด", f"ไม่สามารถแสดงตัวอย่างได้: {str(e)}")
            except:
                print(f"Error: {str(e)}")

# ฟังก์ชันสำหรับใช้งานง่าย ๆ
def create_billing_note_preview():
    """สร้างตัวอย่างใบวางบิลแบบง่าย ๆ"""
    generator = BillingNoteGenerator()
    sample_data = generator.create_sample_data()
    generator.preview_in_browser(sample_data)

def create_billing_note_pdf(output_path="billing_note.pdf"):
    """สร้างใบวางบิล PDF แบบง่าย ๆ"""
    generator = BillingNoteGenerator()
    sample_data = generator.create_sample_data()
    return generator.generate_pdf(sample_data, output_path)

def create_billing_from_data(data):
    """สร้างใบวางบิลจากข้อมูลที่ส่งมา"""
    generator = BillingNoteGenerator()
    generator.preview_in_browser(data)

# ทดสอบการทำงาน
if __name__ == "__main__":
    print("=== Billing Note Generator ===")
    
    # แสดงตัวอย่างในเบราว์เซอร์
    print("1. กำลังแสดงตัวอย่างในเบราว์เซอร์...")
    create_billing_note_preview()
    
    # สร้าง PDF
    print("2. กำลังสร้าง PDF...")
    success = create_billing_note_pdf("sample_billing_note.pdf")
    if success:
        print("✅ สร้าง PDF สำเร็จ: sample_billing_note.pdf")
    else:
        print("❌ เกิดข้อผิดพลาดในการสร้าง PDF")