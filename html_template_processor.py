import re
import os
import tempfile
import webbrowser
from datetime import datetime

class HTMLTemplateProcessor:
    def __init__(self):
        pass
    
    def render_template(self, template_content, data):
        """Render HTML template with data using simple string replacement"""
        try:
            print("=== DEBUG: ข้อมูลที่ส่งเข้า Template ===")
            print(f"Keys: {list(data.keys())}")
            if 'additionalItems' in data:
                print(f"additionalItems: {len(data['additionalItems'])} items")
            
            rendered = template_content
            
            # 1. จัดการ {{#if condition}} แบบง่าย
            rendered = self._process_conditionals(rendered, data)
            
            # 2. จัดการ {{#each additionalItems}} 
            rendered = self._process_each_loop(rendered, data)
            
            # 3. แทนที่ตัวแปรปกติ {{ variable }}
            rendered = self._replace_variables(rendered, data)
            
            return rendered
            
        except Exception as e:
            print(f"Error rendering template: {str(e)}")
            import traceback
            traceback.print_exc()
            return template_content
    
    def _process_conditionals(self, html, data):
        """จัดการ {{#if variable}} content {{/if}}"""
        # Pattern สำหรับ if statements
        if_pattern = r'\{\{#if\s+([^}]+)\}\}(.*?)\{\{/if\}\}'
        
        def replace_if(match):
            variable = match.group(1).strip()
            content = match.group(2)
            
            # ตรวจสอบว่าตัวแปรมีค่าหรือไม่
            value = data.get(variable, '')
            if value and str(value).strip() and str(value) != 'null':
                return content
            else:
                return ''
        
        return re.sub(if_pattern, replace_if, html, flags=re.DOTALL)
    
    def _process_each_loop(self, html, data):
        """จัดการ {{#each additionalItems}} content {{/each}}"""
        # Pattern สำหรับ each loop
        each_pattern = r'\{\{#each\s+additionalItems\}\}(.*?)\{\{/each\}\}'
        
        def replace_each(match):
            loop_content = match.group(1)
            
            if 'additionalItems' not in data or not data['additionalItems']:
                return ''
            
            result_html = ''
            for item in data['additionalItems']:
                # แทนที่ตัวแปรใน loop content
                item_html = loop_content
                for key, value in item.items():
                    placeholder = f"{{{{ {key} }}}}"
                    item_html = item_html.replace(placeholder, str(value or ''))
                result_html += item_html
            
            return result_html
        
        return re.sub(each_pattern, replace_each, html, flags=re.DOTALL)
    
    def _replace_variables(self, html, data):
        """แทนที่ตัวแปรปกติ {{ variable }}"""
        for key, value in data.items():
            if key != 'additionalItems':  # ข้าม array เพราะจัดการแล้ว
                placeholder = f"{{{{ {key} }}}}"
                # แปลง None หรือค่าว่างเป็น string ว่าง
                display_value = str(value) if value is not None else ''
                html = html.replace(placeholder, display_value)
        
        # ลบตัวแปรที่เหลือ (ถ้ามี)
        html = re.sub(r'\{\{[^}]+\}\}', '', html)
        
        return html
    
    def preview_in_browser(self, html_content, data=None):
        """แสดงตัวอย่างในเบราว์เซอร์"""
        try:
            if data:
                rendered_html = self.render_template(html_content, data)
            else:
                rendered_html = html_content
            
            # สร้างไฟล์ชั่วคราว
            temp_file = tempfile.NamedTemporaryFile(
                mode='w', suffix='.html', delete=False, encoding='utf-8'
            )
            temp_file.write(rendered_html)
            temp_file.close()
            
            # เปิดในเบราว์เซอร์
            webbrowser.open('file://' + os.path.realpath(temp_file.name))
            
            return temp_file.name
            
        except Exception as e:
            print(f"Error previewing in browser: {str(e)}")
            return None

# ทดสอบการทำงาน
if __name__ == "__main__":
    # ข้อมูลทดสอบ
    test_data = {
        'DocumentTitle': 'ใบวางบิลขายสำหรับลูกค้า',
        'Companyname': 'บริษัท เทสต์ จำกัด',
        'SiteAddress': '123 ถนนเทสต์',
        'PhoneNumber': '02-123-4567',
        'TaxId': 'เลขประจำตัวผู้เสียภาษี: 1234567890123',
        'CustomerName': 'บริษัท ลูกค้าทดสอบ จำกัด',
        'additionalItems': [
            {
                'itemNumber': 2,
                'documentType': 'ใบขาย',
                'InvoiceNumber': 'SAL-001',
                'InvoiceDate': '01/01/2025',
                'MaxDueDate': '30',
                'DueDate': '31/01/2025',
                'Total': '5,000.00',
                'PaidAmount': '0.00',
                'UnpaidAmount': '5,000.00'
            }
        ]
    }
    
    processor = HTMLTemplateProcessor()
    
    # Template ทดสอบ
    test_template = '''
    <html>
    <body>
        <h1>{{ DocumentTitle }}</h1>
        {{#if Companyname}}<p>บริษัท: {{ Companyname }}</p>{{/if}}
        {{#if SiteAddress}}<p>ที่อยู่: {{ SiteAddress }}</p>{{/if}}
        
        <h3>รายการ:</h3>
        {{#each additionalItems}}
        <p>{{ itemNumber }}. {{ documentType }} - {{ InvoiceNumber }}</p>
        {{/each}}
    </body>
    </html>
    '''
    
    result = processor.render_template(test_template, test_data)
    print("ผลลัพธ์:")
    print(result)