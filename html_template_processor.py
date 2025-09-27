import re
import json
import os
import tempfile
import webbrowser
from datetime import datetime
try:
    import pdfkit
    HAS_PDFKIT = True
except ImportError:
    HAS_PDFKIT = False

try:
    from weasyprint import HTML, CSS
    HAS_WEASYPRINT = True
except ImportError:
    HAS_WEASYPRINT = False

class HTMLTemplateProcessor:
    def __init__(self):
        self.template_vars_pattern = r'\{\{\s*([^}]+)\s*\}\}'
        self.loop_pattern = r'\{\{#each\s+(\w+)\}\}(.*?)\{\{/each\}\}'
        self.conditional_pattern = r'\{\{#if\s+([^}]+)\}\}(.*?)(?:\{\{else\}\}(.*?))?\{\{/if\}\}'
        
    def render_template(self, html_template, data):
        """
        Render HTML template with data
        
        Args:
            html_template (str): HTML template string with template variables
            data (dict): Data to fill into template
            
        Returns:
            str: Rendered HTML
        """
        rendered_html = html_template
        
        # Process loops first ({{#each items}} ... {{/each}})
        rendered_html = self.process_loops(rendered_html, data)
        
        # Process conditionals ({{#if condition}} ... {{/if}})
        rendered_html = self.process_conditionals(rendered_html, data)
        
        # Process simple variables ({{ variable_name }})
        rendered_html = self.process_variables(rendered_html, data)
        
        # Process helper functions
        rendered_html = self.process_helpers(rendered_html, data)
        
        return rendered_html
    
    def process_variables(self, html_template, data):
        """Process simple template variables like {{ variable_name }}"""
        def replace_var(match):
            var_name = match.group(1).strip()
            
            # Handle nested properties (e.g., company.name)
            if '.' in var_name:
                return self.get_nested_value(data, var_name)
            
            # Handle array index (e.g., items.0.name)
            if '[' in var_name and ']' in var_name:
                return self.get_array_value(data, var_name)
            
            # Simple variable
            value = data.get(var_name, '')
            return self.format_value(value)
        
        return re.sub(self.template_vars_pattern, replace_var, html_template)
    
    def process_loops(self, html_template, data):
        """Process loop constructs like {{#each items}} ... {{/each}}"""
        def replace_loop(match):
            array_name = match.group(1).strip()
            loop_content = match.group(2)
            
            if array_name not in data or not isinstance(data[array_name], list):
                return ''  # Return empty if array doesn't exist
            
            result_parts = []
            array_data = data[array_name]
            
            for index, item in enumerate(array_data):
                # Create loop context with item data and special variables
                loop_context = {
                    **data,  # Include parent data
                    **item,  # Include current item data
                    '@index': index,
                    '@first': index == 0,
                    '@last': index == len(array_data) - 1,
                    '@length': len(array_data)
                }
                
                # Process the loop content with current context
                processed_content = self.process_variables(loop_content, loop_context)
                processed_content = self.process_helpers(processed_content, loop_context)
                result_parts.append(processed_content)
            
            return ''.join(result_parts)
        
        return re.sub(self.loop_pattern, replace_loop, html_template, flags=re.DOTALL)
    
    def process_conditionals(self, html_template, data):
        """Process conditional constructs like {{#if condition}} ... {{/if}}"""
        def replace_conditional(match):
            condition = match.group(1).strip()
            if_content = match.group(2)
            else_content = match.group(3) if match.group(3) else ''
            
            # Evaluate condition
            if self.evaluate_condition(condition, data):
                return self.process_variables(if_content, data)
            else:
                return self.process_variables(else_content, data)
        
        return re.sub(self.conditional_pattern, replace_conditional, html_template, flags=re.DOTALL)
    
    def process_helpers(self, html_template, data):
        """Process helper functions like {{add @index 1}}"""
        # Helper: {{add value1 value2}}
        def replace_add(match):
            parts = match.group(1).strip().split()
            if len(parts) >= 3 and parts[0] == 'add':
                try:
                    val1 = self.get_value(parts[1], data)
                    val2 = self.get_value(parts[2], data)
                    return str(int(val1) + int(val2))
                except (ValueError, TypeError):
                    return '0'
            return match.group(0)
        
        # Helper: {{formatNumber value}}
        def replace_format_number(match):
            parts = match.group(1).strip().split()
            if len(parts) >= 2 and parts[0] == 'formatNumber':
                try:
                    value = self.get_value(parts[1], data)
                    if isinstance(value, str):
                        # Remove commas and convert to float
                        value = float(value.replace(',', ''))
                    return f"{value:,.2f}"
                except (ValueError, TypeError):
                    return str(value)
            return match.group(0)
        
        # Apply helpers
        html_template = re.sub(self.template_vars_pattern, replace_add, html_template)
        html_template = re.sub(self.template_vars_pattern, replace_format_number, html_template)
        
        return html_template
    
    def evaluate_condition(self, condition, data):
        """Evaluate a simple condition"""
        # Simple equality check
        if '==' in condition:
            left, right = condition.split('==', 1)
            left_val = self.get_value(left.strip(), data)
            right_val = right.strip().strip('"\'')
            return str(left_val) == str(right_val)
        
        # Simple inequality check
        if '!=' in condition:
            left, right = condition.split('!=', 1)
            left_val = self.get_value(left.strip(), data)
            right_val = right.strip().strip('"\'')
            return str(left_val) != str(right_val)
        
        # Simple existence check
        condition = condition.strip()
        value = self.get_value(condition, data)
        return bool(value) and value != '' and value != '0'
    
    def get_value(self, key, data):
        """Get value from data, supporting special variables like @index"""
        key = key.strip()
        
        # Handle special loop variables
        if key.startswith('@'):
            return data.get(key, '')
        
        # Handle nested properties
        if '.' in key:
            return self.get_nested_value(data, key)
        
        # Simple key
        return data.get(key, '')
    
    def get_nested_value(self, data, key_path):
        """Get nested value like 'company.name'"""
        keys = key_path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key, '')
            else:
                return ''
        
        return value
    
    def get_array_value(self, data, key_path):
        """Get array value like 'items[0].name'"""
        # This is a simplified implementation
        # In a real scenario, you might want to use a more robust parser
        try:
            # Extract array name and index
            if '[' in key_path:
                array_part, rest = key_path.split('[', 1)
                index_part, property_part = rest.split(']', 1)
                index = int(index_part)
                
                array_data = data.get(array_part, [])
                if isinstance(array_data, list) and 0 <= index < len(array_data):
                    item = array_data[index]
                    if property_part.startswith('.'):
                        return self.get_nested_value(item, property_part[1:])
                    return item
                    
        except (ValueError, IndexError):
            pass
        
        return ''
    
    def format_value(self, value):
        """Format value for display"""
        if value is None:
            return ''
        
        # Format numbers with commas
        if isinstance(value, (int, float)):
            return f"{value:,.2f}" if isinstance(value, float) else f"{value:,}"
        
        # Format dates
        if isinstance(value, datetime):
            return value.strftime('%d/%m/%Y')
        
        return str(value)
    
    def render_template_file(self, template_path, data, output_path=None):
        """
        Render template file with data
        
        Args:
            template_path (str): Path to HTML template file
            data (dict): Data to fill into template
            output_path (str): Output file path (optional)
            
        Returns:
            str: Rendered HTML or output file path
        """
        try:
            with open(template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
            
            rendered_html = self.render_template(template_content, data)
            
            if output_path:
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(rendered_html)
                return output_path
            else:
                return rendered_html
                
        except Exception as e:
            raise Exception(f"Error rendering template: {str(e)}")
    
    def preview_in_browser(self, html_content, data=None):
        """
        Preview HTML in browser
        
        Args:
            html_content (str): HTML template content
            data (dict): Data to render with (optional)
        """
        try:
            if data:
                rendered_html = self.render_template(html_content, data)
            else:
                rendered_html = html_content
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.html', 
                                                  delete=False, encoding='utf-8')
            temp_file.write(rendered_html)
            temp_file.close()
            
            # Open in browser
            webbrowser.open('file://' + os.path.realpath(temp_file.name))
            
            return temp_file.name
            
        except Exception as e:
            raise Exception(f"Error previewing in browser: {str(e)}")
    
    def export_to_pdf(self, html_content, data, output_path, method='weasyprint'):
        """
        Export rendered HTML to PDF
        
        Args:
            html_content (str): HTML template content
            data (dict): Data to render with
            output_path (str): Output PDF file path
            method (str): PDF generation method ('weasyprint' or 'pdfkit')
            
        Returns:
            bool: Success status
        """
        try:
            # Render template with data
            rendered_html = self.render_template(html_content, data)
            
            if method == 'weasyprint' and HAS_WEASYPRINT:
                return self._export_with_weasyprint(rendered_html, output_path)
            elif method == 'pdfkit' and HAS_PDFKIT:
                return self._export_with_pdfkit(rendered_html, output_path)
            else:
                # Fallback: save as HTML and open in browser
                html_output_path = output_path.replace('.pdf', '.html')
                with open(html_output_path, 'w', encoding='utf-8') as f:
                    f.write(rendered_html)
                
                webbrowser.open('file://' + os.path.realpath(html_output_path))
                print(f"PDF libraries not available. HTML saved to: {html_output_path}")
                print("You can print to PDF from your browser.")
                return True
                
        except Exception as e:
            print(f"Error exporting to PDF: {str(e)}")
            return False
    
    def _export_with_weasyprint(self, html_content, output_path):
        """Export to PDF using WeasyPrint"""
        try:
            # Create CSS for better PDF output
            css_content = '''
                @page {
                    size: A4;
                    margin: 2cm;
                }
                body {
                    font-size: 12pt;
                    line-height: 1.4;
                }
                .page-break {
                    page-break-after: always;
                }
            '''
            
            # Generate PDF
            html_doc = HTML(string=html_content)
            css_doc = CSS(string=css_content)
            html_doc.write_pdf(output_path, stylesheets=[css_doc])
            
            print(f"PDF exported successfully: {output_path}")
            return True
            
        except Exception as e:
            print(f"WeasyPrint export error: {str(e)}")
            return False
    
    def _export_with_pdfkit(self, html_content, output_path):
        """Export to PDF using pdfkit (wkhtmltopdf)"""
        try:
            options = {
                'page-size': 'A4',
                'margin-top': '2cm',
                'margin-right': '2cm',
                'margin-bottom': '2cm',
                'margin-left': '2cm',
                'encoding': "UTF-8",
                'no-outline': None,
                'enable-local-file-access': None
            }
            
            pdfkit.from_string(html_content, output_path, options=options)
            
            print(f"PDF exported successfully: {output_path}")
            return True
            
        except Exception as e:
            print(f"pdfkit export error: {str(e)}")
            return False

# Utility functions
def load_template_data(json_file_path):
    """Load data from JSON file"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading data from {json_file_path}: {str(e)}")
        return {}

def save_template_data(data, json_file_path):
    """Save data to JSON file"""
    try:
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Error saving data to {json_file_path}: {str(e)}")
        return False

# Example usage and testing
if __name__ == "__main__":
    # Sample data for testing
    sample_data = {
        'InvoiceNumber': 'INV-2025-001',
        'InvoiceDate': '15/01/2025',
        'MaxDueDate': '30/01/2025',
        'CustomerName': 'บริษัท ตัวอย่าง จำกัด',
        'CustomerAddress': '123 ถนนตัวอย่าง แขวงตัวอย่าง เขตตัวอย่าง กรุงเทพฯ 10100',
        'PhoneMobile': '02-123-4567',
        'CustomerTaxNum': '0123456789012',
        'SubTotal': '10000.00',
        'Tax': '700.00',
        'Total': '10700.00',
        'company_name': 'บริษัท เอบีซี จำกัด',
        'company_address': '456 ถนนบริษัท แขวงบริษัท เขตบริษัท กรุงเทพฯ 10200',
        'company_phone': '02-987-6543',
        'company_email': 'info@abc.com',
        'company_tax_id': '0987654321012',
        'items': [
            {
                'ItemName': 'สินค้า A',
                'Quantity': '2',
                'UnitPrice': '2500.00',
                'Amount': '5000.00'
            },
            {
                'ItemName': 'สินค้า B', 
                'Quantity': '1',
                'UnitPrice': '5000.00',
                'Amount': '5000.00'
            }
        ]
    }
    
    # Test template processing
    processor = HTMLTemplateProcessor()
    
    # Simple template for testing
    test_template = '''
    <html>
    <body>
        <h1>{{ company_name }}</h1>
        <p>Invoice: {{ InvoiceNumber }}</p>
        <p>Customer: {{ CustomerName }}</p>
        
        <table>
            <tr><th>Item</th><th>Qty</th><th>Price</th></tr>
            {{#each items}}
            <tr>
                <td>{{ ItemName }}</td>
                <td>{{ Quantity }}</td>
                <td>{{ UnitPrice }}</td>
            </tr>
            {{/each}}
        </table>
        
        <p>Total: {{ Total }}</p>
    </body>
    </html>
    '''
    
    # Test rendering
    rendered = processor.render_template(test_template, sample_data)
    print("Rendered HTML:")
    print(rendered)
    
    # Test preview in browser (uncomment to test)
    # processor.preview_in_browser(test_template, sample_data)
    
    # Test PDF export (uncomment to test)
    # processor.export_to_pdf(test_template, sample_data, 'test_invoice.pdf')