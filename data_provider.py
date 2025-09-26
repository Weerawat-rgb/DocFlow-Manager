import pyodbc
import json
from datetime import datetime, date
from decimal import Decimal

class DataProvider:
    def __init__(self, config_file='config.json'):
        self.config = self.load_config(config_file)
        self.connection = None
        
    def load_config(self, config_file):
        """โหลดการตั้งค่าฐานข้อมูล"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('database', {})
        except:
            # Default config
            return {
                'server': 'localhost',
                'database': 'YourDatabase',
                'username': '',
                'password': '',
                'driver': 'ODBC Driver 17 for SQL Server'
            }
    
    def connect(self):
        """เชื่อมต่อฐานข้อมูล"""
        try:
            if self.config.get('username'):
                # SQL Server Authentication
                conn_str = f"""
                    DRIVER={{{self.config['driver']}}};
                    SERVER={self.config['server']};
                    DATABASE={self.config['database']};
                    UID={self.config['username']};
                    PWD={self.config['password']};
                """
            else:
                # Windows Authentication
                conn_str = f"""
                    DRIVER={{{self.config['driver']}}};
                    SERVER={self.config['server']};
                    DATABASE={self.config['database']};
                    Trusted_Connection=yes;
                """
            
            self.connection = pyodbc.connect(conn_str)
            return True
        except Exception as e:
            print(f"Database connection error: {e}")
            return False
    
    def disconnect(self):
        """ตัดการเชื่อมต่อ"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def execute_query(self, query, params=None):
        """Execute SELECT query"""
        if not self.connection:
            if not self.connect():
                return []
        
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            # Get column names
            columns = [column[0] for column in cursor.description]
            
            # Fetch data
            rows = cursor.fetchall()
            
            # Convert to list of dictionaries
            result = []
            for row in rows:
                row_dict = {}
                for i, value in enumerate(row):
                    # Convert special types to JSON-serializable format
                    if isinstance(value, Decimal):
                        row_dict[columns[i]] = float(value)
                    elif isinstance(value, (date, datetime)):
                        row_dict[columns[i]] = value.isoformat()
                    elif value is None:
                        row_dict[columns[i]] = None
                    else:
                        row_dict[columns[i]] = value
                result.append(row_dict)
            
            cursor.close()
            return result
            
        except Exception as e:
            print(f"Query execution error: {e}")
            return []

    # ==========================================
    # Query Methods สำหรับใบวางบิล
    # ==========================================
    
    def get_invoice_data(self, invoice_id=None, customer_id=None, date_from=None, date_to=None):
        """ดึงข้อมูลใบวางบิลตาม query ที่ให้มา"""
        
        base_query = """
            SELECT 
                c.Acct, 
                c.FirstName + c.LastName AS AccountName, 
                c.PhoneMobile,
                iv.InvoiceId,
                iv.InvoiceDate, 
                iv.InvoiceNumber, 
                iv.CustomerName,
                iv.CustomerAddress,
                iv.CustomerBranch,
                iv.CustomerTaxNum,
                iv.MaxDueDate, 
                iv.Status,
                it.PaidAmount,
                it.UnpaidAmount,
                it.SubTotal,
                it.Tax,
                it.Total,
                it.RefSaleId
            FROM Invoice iv
            INNER JOIN InvoiceItem it ON iv.InvoiceId = it.InvoiceId 
                AND iv.Active = 1 AND iv.Status != 1
            INNER JOIN Customer c ON c.CustomerId = iv.CustomerId 
                AND c.Active = 1
        """
        
        # เพิ่มเงื่อนไข WHERE
        conditions = []
        params = []
        
        if invoice_id:
            conditions.append("iv.InvoiceId = ?")
            params.append(invoice_id)
        
        if customer_id:
            conditions.append("iv.CustomerId = ?")
            params.append(customer_id)
            
        if date_from:
            conditions.append("iv.InvoiceDate >= ?")
            params.append(date_from)
            
        if date_to:
            conditions.append("iv.InvoiceDate <= ?")
            params.append(date_to)
        
        # รวม query
        if conditions:
            query = base_query + " WHERE " + " AND ".join(conditions)
        else:
            query = base_query
            
        query += " ORDER BY iv.InvoiceDate DESC, iv.InvoiceNumber"
        
        return self.execute_query(query, params)
    
    def get_invoice_details(self, invoice_id):
        """ดึงรายการสินค้าในใบแจ้งหนี้"""
        query = """
            SELECT 
                id.ItemCode,
                id.ItemName,
                id.Quantity,
                id.UnitPrice,
                id.Discount,
                id.Amount,
                id.TaxRate,
                id.TaxAmount,
                id.TotalAmount,
                i.Unit,
                i.ItemType
            FROM InvoiceItemDetail id
            INNER JOIN Item i ON i.ItemCode = id.ItemCode
            WHERE id.InvoiceId = ?
            ORDER BY id.LineNumber
        """
        return self.execute_query(query, [invoice_id])
    
    def get_customer_list(self, search_text=''):
        """ดึงรายชื่อลูกค้า"""
        query = """
            SELECT 
                CustomerId,
                Acct as CustomerCode,
                FirstName + LastName AS CustomerName,
                PhoneMobile,
                Email,
                Address,
                TaxNumber
            FROM Customer 
            WHERE Active = 1
        """
        
        if search_text:
            query += " AND (FirstName + LastName LIKE ? OR Acct LIKE ? OR PhoneMobile LIKE ?)"
            search_pattern = f'%{search_text}%'
            return self.execute_query(query, [search_pattern, search_pattern, search_pattern])
        else:
            query += " ORDER BY FirstName + LastName"
            return self.execute_query(query)
    
    def get_supplier_list(self, search_text=''):
        """ดึงรายชื่อผู้จำหน่าย (ถ้ามีตารางแยก)"""
        # ปรับตามโครงสร้างจริง
        query = """
            SELECT 
                SupplierId,
                SupplierCode,
                SupplierName,
                Phone,
                Email,
                Address,
                TaxNumber
            FROM Supplier 
            WHERE Active = 1
        """
        
        if search_text:
            query += " AND (SupplierName LIKE ? OR SupplierCode LIKE ?)"
            search_pattern = f'%{search_text}%'
            return self.execute_query(query, [search_pattern, search_pattern])
        else:
            query += " ORDER BY SupplierName"
            return self.execute_query(query)
    
    def get_company_info(self):
        """ดึงข้อมูลบริษัท"""
        query = """
            SELECT 
                CompanyName,
                Address,
                Phone,
                Email,
                TaxNumber,
                LogoPath
            FROM CompanyInfo 
            WHERE Active = 1
        """
        result = self.execute_query(query)
        return result[0] if result else {}
    
    # ==========================================
    # Methods สำหรับ Form Designer
    # ==========================================
    
    def get_available_fields(self, doc_type='invoice'):
        """ดึงรายชื่อฟิลด์ที่ใช้ได้สำหรับ Form Designer"""
        
        if doc_type == 'invoice':
            return [
                # Header Fields
                {'name': 'InvoiceNumber', 'label': 'เลขที่ใบแจ้งหนี้', 'type': 'string', 'section': 'header'},
                {'name': 'InvoiceDate', 'label': 'วันที่', 'type': 'date', 'section': 'header'},
                {'name': 'MaxDueDate', 'label': 'วันครบกำหนด', 'type': 'date', 'section': 'header'},
                
                # Customer Fields
                {'name': 'CustomerName', 'label': 'ชื่อลูกค้า', 'type': 'string', 'section': 'detail'},
                {'name': 'CustomerAddress', 'label': 'ที่อยู่ลูกค้า', 'type': 'string', 'section': 'detail'},
                {'name': 'CustomerBranch', 'label': 'สาขา', 'type': 'string', 'section': 'detail'},
                {'name': 'CustomerTaxNum', 'label': 'เลขประจำตัวผู้เสียภาษี', 'type': 'string', 'section': 'detail'},
                {'name': 'PhoneMobile', 'label': 'เบอร์โทร', 'type': 'string', 'section': 'detail'},
                
                # Amount Fields
                {'name': 'SubTotal', 'label': 'ยอดก่อนภาษี', 'type': 'currency', 'section': 'footer'},
                {'name': 'Tax', 'label': 'ภาษี', 'type': 'currency', 'section': 'footer'},
                {'name': 'Total', 'label': 'ยอดรวม', 'type': 'currency', 'section': 'footer'},
                {'name': 'PaidAmount', 'label': 'ยอดชำระแล้ว', 'type': 'currency', 'section': 'footer'},
                {'name': 'UnpaidAmount', 'label': 'ยอดค้างชำระ', 'type': 'currency', 'section': 'footer'},
                
                # Status Field
                {'name': 'Status', 'label': 'สถานะ', 'type': 'string', 'section': 'footer'},
            ]
        
        elif doc_type == 'purchase':
            return [
                {'name': 'PurchaseNumber', 'label': 'เลขที่ใบสั่งซื้อ', 'type': 'string', 'section': 'header'},
                {'name': 'PurchaseDate', 'label': 'วันที่สั่งซื้อ', 'type': 'date', 'section': 'header'},
                {'name': 'SupplierName', 'label': 'ชื่อผู้จำหน่าย', 'type': 'string', 'section': 'detail'},
                # ... เพิ่มตามต้องการ
            ]
        
        return []
    
    def get_sample_data(self, doc_type='invoice', limit=1):
        """ดึงข้อมูลตัวอย่างสำหรับ Preview"""
        if doc_type == 'invoice':
            data = self.get_invoice_data()
            if data:
                invoice = data[0]  # เอาแค่รายการแรก
                # เพิ่มรายการสินค้า
                invoice['items'] = self.get_invoice_details(invoice['InvoiceId'])
                return invoice
        
        # Return mock data if no real data
        return {
            'InvoiceNumber': 'INV-2025-001',
            'InvoiceDate': '2025-01-15',
            'CustomerName': 'บริษัท ตัวอย่าง จำกัด',
            'CustomerAddress': '123 ถนนตัวอย่าง เขตตัวอย่าง กรุงเทพฯ 10100',
            'SubTotal': 10000.00,
            'Tax': 700.00,
            'Total': 10700.00,
            'items': [
                {'ItemName': 'สินค้า A', 'Quantity': 2, 'UnitPrice': 2500, 'Amount': 5000},
                {'ItemName': 'สินค้า B', 'Quantity': 1, 'UnitPrice': 5000, 'Amount': 5000}
            ]
        }

# ===================================
# Utility Functions
# ===================================

def format_currency(amount, currency_symbol='฿'):
    """Format number as currency"""
    if amount is None:
        return f"{currency_symbol} 0.00"
    return f"{currency_symbol} {amount:,.2f}"

def format_date_thai(date_str, format_type='short'):
    """Format date in Thai format"""
    if not date_str:
        return ""
    
    try:
        if isinstance(date_str, str):
            date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            date_obj = date_str
        
        thai_months = [
            'มกราคม', 'กุมภาพันธ์', 'มีนาคม', 'เมษายน', 'พฤษภาคม', 'มิถุนายน',
            'กรกฎาคม', 'สิงหาคม', 'กันยายน', 'ตุลาคม', 'พฤศจิกายน', 'ธันวาคม'
        ]
        
        if format_type == 'short':
            return f"{date_obj.day:02d}/{date_obj.month:02d}/{date_obj.year + 543}"
        else:
            return f"{date_obj.day} {thai_months[date_obj.month-1]} {date_obj.year + 543}"
            
    except:
        return str(date_str)

# ===================================
# Test/Example Usage
# ===================================

if __name__ == "__main__":
    # Test connection
    dp = DataProvider()
    
    if dp.connect():
        print("✅ Database connected successfully!")
        
        # Test invoice data
        invoices = dp.get_invoice_data()
        print(f"📄 Found {len(invoices)} invoices")
        
        if invoices:
            # Show first invoice
            invoice = invoices[0]
            print(f"📋 Invoice: {invoice['InvoiceNumber']}")
            print(f"👤 Customer: {invoice['CustomerName']}")
            print(f"💰 Total: {format_currency(invoice['Total'])}")
            
            # Get invoice details
            details = dp.get_invoice_details(invoice['InvoiceId'])
            print(f"📦 Items: {len(details)}")
            
        dp.disconnect()
    else:
        print("❌ Database connection failed!")
        print("📝 Please check your config.json file")