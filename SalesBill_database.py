import pyodbc
import json
from typing import List, Dict, Optional

class SalesBillDatabase:
    def __init__(self, config_file='config.json'):
        """Initialize database connection using config file"""
        self.connection = None
        self.config_file = config_file
        self.connect()
    
    def connect(self):
        """Connect to SQL Server using config.json"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # ดึงข้อมูลจาก database section
            db_config = config['database']
            
            connection_string = (
                f"DRIVER={{{db_config['driver']}}};"
                f"SERVER={db_config['server']},{db_config['port']};"
                f"DATABASE={db_config['database']};"
                f"UID={db_config['username']};"
                f"PWD={db_config['password']};"
                f"TrustServerCertificate=yes;"
            )
            
            self.connection = pyodbc.connect(connection_string)
            print("✅ เชื่อมต่อฐานข้อมูลสำเร็จ")
            
        except FileNotFoundError:
            print("❌ ไม่พบไฟล์ config.json")
            raise
        except KeyError as e:
            print(f"❌ ไม่พบค่า configuration: {str(e)}")
            raise
        except Exception as e:
            print(f"❌ เชื่อมต่อฐานข้อมูลไม่สำเร็จ: {str(e)}")
            raise
    
    def search_customers(self, search_term: str = "") -> List[Dict]:
        """ค้นหาลูกค้า - แสดงเฉพาะลูกค้าที่ไม่ซ้ำ"""
        try:
            cursor = self.connection.cursor()
            
            if search_term:
                query = """
                SELECT 
                    c.CustomerId,
                    ISNULL(c.Acct, '') as Acct,
                    ISNULL(c.FirstName, '') + ISNULL(c.LastName, '') as [Name]
                FROM Invoice iv
                INNER JOIN InvoiceItem it ON it.InvoiceId = iv.InvoiceId
                INNER JOIN Customer c ON c.CustomerId = iv.CustomerId
                WHERE it.UnpaidAmount > 0
                AND iv.Status NOT IN (1, 99)
                AND (
                    ISNULL(c.Acct, '') LIKE ?
                    OR ISNULL(c.PhoneMobile, '') LIKE ?
                    OR (ISNULL(c.FirstName, '') + ISNULL(c.LastName, '')) LIKE ?
                )
                GROUP BY c.CustomerId, c.Acct, c.FirstName, c.LastName
                ORDER BY c.CustomerId
                """
                search_pattern = f"%{search_term}%"
                cursor.execute(query, (search_pattern, search_pattern, search_pattern))
            else:
                query = """
                SELECT 
                    c.CustomerId,
                    ISNULL(c.Acct, '') as Acct,
                    ISNULL(c.FirstName, '') + ISNULL(c.LastName, '') as [Name]
                FROM Invoice iv
                INNER JOIN InvoiceItem it ON it.InvoiceId = iv.InvoiceId
                INNER JOIN Customer c ON c.CustomerId = iv.CustomerId
                WHERE it.UnpaidAmount > 0
                AND iv.Status NOT IN (1, 99)
                GROUP BY c.CustomerId, c.Acct, c.FirstName, c.LastName
                ORDER BY c.CustomerId
                """
                cursor.execute(query)
            
            columns = [desc[0] for desc in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                customer = dict(zip(columns, row))
                results.append(customer)
            
            print(f"✅ พบลูกค้าที่มียอดค้างชำระ {len(results)} ราย")
            
            # Debug: แสดงข้อมูลตัวอย่าง
            if results:
                print("📋 ข้อมูลลูกค้าตัวอย่าง:")
                for i, customer in enumerate(results[:3]):
                    print(f"   {i+1}. ID: {customer.get('CustomerId')}, Acct: {customer.get('Acct')}, Name: '{customer.get('Name')}'")
            
            return results
            
        except Exception as e:
            print(f"❌ ข้อผิดพลาดในการค้นหาลูกค้า: {str(e)}")
            return []
        
    def get_customer_invoices(self, customer_id: int) -> List[Dict]:
        """ดึงใบแจ้งหนี้ของลูกค้า - แสดงรายละเอียดทั้งหมด"""
        try:
            cursor = self.connection.cursor()
            
            query = """
            SELECT 
                c.CustomerId,
                ISNULL(c.Acct, '') as Acct,
                ISNULL(c.FirstName, '') + ISNULL(c.LastName, '') as [Name],
                ISNULL(iv.CustomerName, '') as CustomerName,
                ISNULL(iv.CustomerAddress, '') as CustomerAddress,
                ISNULL(c.PhoneMobile, '') as PhoneMobile,
                ISNULL(iv.CustomerTaxNum, '') as CustomerTaxNum,
                iv.InvoiceNumber,
                FORMAT(iv.InvoiceDate, 'yyyy-MM-dd HH:mm:ss.fff') as InvoiceDate,
                iv.MaxDueDate,
                FORMAT(DATEADD(day, iv.MaxDueDate, iv.InvoiceDate), 'yyyy-MM-dd HH:mm:ss.fff') as DueDate,
                FORMAT(it.Total, 'N2') as Total,
                FORMAT(it.PaidAmount, 'N2') as PaidAmount,
                FORMAT(it.UnpaidAmount, 'N2') as UnpaidAmount
            FROM Invoice iv
            INNER JOIN InvoiceItem it ON it.InvoiceId = iv.InvoiceId
            INNER JOIN Customer c ON c.CustomerId = iv.CustomerId
            WHERE c.CustomerId = ?
            AND it.UnpaidAmount > 0
            AND iv.Status NOT IN (1, 99)
            ORDER BY iv.InvoiceDate DESC
            """
            
            cursor.execute(query, (customer_id,))
            columns = [desc[0] for desc in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                invoice = dict(zip(columns, row))
                results.append(invoice)
            
            print(f"✅ พบใบแจ้งหนี้ของลูกค้า ID {customer_id}: {len(results)} ใบ")
            return results
            
        except Exception as e:
            print(f"❌ ข้อผิดพลาดในการดึงใบแจ้งหนี้: {str(e)}")
            return []

    def get_customer_invoices_for_display(self, search_term: str = "") -> List[Dict]:
        """ดึงข้อมูลลูกค้าพร้อมใบแจ้งหนี้สำหรับแสดงในตาราง"""
        try:
            cursor = self.connection.cursor()
            
            if search_term:
                query = """
                SELECT 
                    c.CustomerId,
                    ISNULL(c.Acct, '') as Acct,
                    ISNULL(c.FirstName, '') + ISNULL(c.LastName, '') as [Name],
                    ISNULL(iv.CustomerName, '') as CustomerName,
                    ISNULL(iv.CustomerAddress, '') as CustomerAddress,
                    ISNULL(c.PhoneMobile, '') as PhoneMobile,
                    ISNULL(iv.CustomerTaxNum, '') as CustomerTaxNum,
                    iv.InvoiceNumber,
                    FORMAT(iv.InvoiceDate, 'yyyy-MM-dd HH:mm:ss.fff') as InvoiceDate,
                    iv.MaxDueDate,
                    FORMAT(DATEADD(day, iv.MaxDueDate, iv.InvoiceDate), 'yyyy-MM-dd HH:mm:ss.fff') as DueDate,
                    FORMAT(it.Total, 'N2') as Total,
                    FORMAT(it.PaidAmount, 'N2') as PaidAmount,
                    FORMAT(it.UnpaidAmount, 'N2') as UnpaidAmount
                FROM Invoice iv
                INNER JOIN InvoiceItem it ON it.InvoiceId = iv.InvoiceId
                INNER JOIN Customer c ON c.CustomerId = iv.CustomerId
                WHERE it.UnpaidAmount > 0
                AND iv.Status NOT IN (1, 99)
                AND (
                    ISNULL(c.Acct, '') LIKE ?
                    OR ISNULL(c.PhoneMobile, '') LIKE ?
                    OR ISNULL(iv.CustomerTaxNum, '') LIKE ?
                    OR (ISNULL(c.FirstName, '') + ISNULL(c.LastName, '')) LIKE ?
                    OR ISNULL(iv.CustomerName, '') LIKE ?
                )
                ORDER BY c.CustomerId, iv.InvoiceDate
                """
                search_pattern = f"%{search_term}%"
                cursor.execute(query, (search_pattern, search_pattern, search_pattern, search_pattern, search_pattern))
            else:
                query = """
                SELECT 
                    c.CustomerId,
                    ISNULL(c.Acct, '') as Acct,
                    ISNULL(c.FirstName, '') + ISNULL(c.LastName, '') as [Name],
                    ISNULL(iv.CustomerName, '') as CustomerName,
                    ISNULL(iv.CustomerAddress, '') as CustomerAddress,
                    ISNULL(c.PhoneMobile, '') as PhoneMobile,
                    ISNULL(iv.CustomerTaxNum, '') as CustomerTaxNum,
                    iv.InvoiceNumber,
                    FORMAT(iv.InvoiceDate, 'yyyy-MM-dd HH:mm:ss.fff') as InvoiceDate,
                    iv.MaxDueDate,
                    FORMAT(DATEADD(day, iv.MaxDueDate, iv.InvoiceDate), 'yyyy-MM-dd HH:mm:ss.fff') as DueDate,
                    FORMAT(it.Total, 'N2') as Total,
                    FORMAT(it.PaidAmount, 'N2') as PaidAmount,
                    FORMAT(it.UnpaidAmount, 'N2') as UnpaidAmount
                FROM Invoice iv
                INNER JOIN InvoiceItem it ON it.InvoiceId = iv.InvoiceId
                INNER JOIN Customer c ON c.CustomerId = iv.CustomerId
                WHERE it.UnpaidAmount > 0
                AND iv.Status NOT IN (1, 99)
                ORDER BY c.CustomerId, iv.InvoiceDate
                """
                cursor.execute(query)
            
            columns = [desc[0] for desc in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                invoice = dict(zip(columns, row))
                results.append(invoice)
            
            print(f"✅ ดึงข้อมูลใบแจ้งหนี้สำหรับแสดงผล {len(results)} รายการ")
            return results
            
        except Exception as e:
            print(f"❌ ข้อผิดพลาดในการดึงข้อมูลสำหรับแสดงผล: {str(e)}")
            return []
            
    def get_invoice_details(self, invoice_number: str) -> Dict:
        """ดึงรายละเอียดใบแจ้งหนี้"""
        try:
            cursor = self.connection.cursor()
            
            query = """
            SELECT 
                iv.*,
                it.Total,
                it.PaidAmount,
                it.UnpaidAmount,
                c.FirstName + ' ' + c.LastName as CustomerFullName
            FROM Invoice iv
            INNER JOIN InvoiceItem it ON it.InvoiceId = iv.InvoiceId
            INNER JOIN Customer c ON c.CustomerId = iv.CustomerId
            WHERE iv.InvoiceNumber = ?
            """
            
            cursor.execute(query, (invoice_number,))
            columns = [desc[0] for desc in cursor.description]
            row = cursor.fetchone()
            
            if row:
                invoice = dict(zip(columns, row))
                # Convert dates to string format
                if invoice.get('InvoiceDate'):
                    invoice['InvoiceDate'] = invoice['InvoiceDate'].strftime('%Y-%m-%d')
                if invoice.get('DueDate'):
                    invoice['DueDate'] = invoice['DueDate'].strftime('%Y-%m-%d')
                return invoice
            
            return {}
            
        except Exception as e:
            print(f"❌ ข้อผิดพลาดในการดึงรายละเอียดใบแจ้งหนี้: {str(e)}")
            return {}
        
    def get_customer_detail(self, customer_id: int) -> Dict:
        """ดึงข้อมูลลูกค้าแบบละเอียดพร้อมที่อยู่"""
        try:
            cursor = self.connection.cursor()
            
            query = """
            SELECT 
                c.Acct,
                c.FirstName + c.LastName AS [Name],
                c.Address+' '+
                CASE 
                    WHEN c.state != 1 THEN 
                        'ต.' + d.district_name + ' ' + 
                        'อ.' + a.amphur_name + ' ' + 
                        'จ.' + p.province_name + ' '+
                        c.ZipCode
                    ELSE 
                        d.district_name + ' ' + 
                        a.amphur_name + ' ' + 
                        p.province_name + ' '+
                        c.ZipCode
                END AS full_address,
                c.PhoneMobile
            FROM Customer c
            LEFT JOIN Amphur a ON a.amphur_id = c.City
            LEFT JOIN Province p ON p.province_id = c.State
            LEFT JOIN District d ON d.district_id = c.SubDistrict
            WHERE c.CustomerId = ?
            """
            
            cursor.execute(query, (customer_id,))
            row = cursor.fetchone()
            
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            
            return {}
            
        except Exception as e:
            print(f"Error getting customer detail: {str(e)}")
            return {}
    
    def create_billing_document(self, customer_id: int, invoice_numbers: List[str], 
                               created_by: str) -> Optional[str]:
        """สร้างเอกสารใบวางบิล"""
        try:
            cursor = self.connection.cursor()
            
            # Generate billing document number
            billing_doc_no = self.generate_billing_doc_number()
            
            # Insert billing document header
            insert_header = """
            INSERT INTO BillingDocument 
            (BillingDocNumber, CustomerId, CreateDate, CreatedBy, Status)
            VALUES (?, ?, GETDATE(), ?, 'Active')
            """
            
            cursor.execute(insert_header, (billing_doc_no, customer_id, created_by))
            
            # Get the inserted billing document ID
            cursor.execute("SELECT @@IDENTITY")
            billing_doc_id = cursor.fetchone()[0]
            
            # Insert billing document items
            for invoice_no in invoice_numbers:
                insert_item = """
                INSERT INTO BillingDocumentItem 
                (BillingDocId, InvoiceNumber)
                VALUES (?, ?)
                """
                cursor.execute(insert_item, (billing_doc_id, invoice_no))
            
            self.connection.commit()
            print(f"✅ สร้างเอกสารใบวางบิล {billing_doc_no} สำเร็จ")
            return billing_doc_no
            
        except Exception as e:
            self.connection.rollback()
            print(f"❌ ข้อผิดพลาดในการสร้างเอกสารใบวางบิล: {str(e)}")
            return None
    
    def generate_billing_doc_number(self) -> str:
        """สร้างเลขที่เอกสารใบวางบิล"""
        try:
            cursor = self.connection.cursor()
            
            # Get current year and month
            cursor.execute("SELECT FORMAT(GETDATE(), 'yyyyMM')")
            year_month = cursor.fetchone()[0]
            
            # Get next sequence number
            cursor.execute("""
                SELECT ISNULL(MAX(CAST(RIGHT(BillingDocNumber, 4) AS INT)), 0) + 1
                FROM BillingDocument 
                WHERE LEFT(BillingDocNumber, 8) = ?
            """, (f"BL{year_month}",))
            
            next_seq = cursor.fetchone()[0]
            
            return f"BL{year_month}{next_seq:04d}"
            
        except Exception as e:
            print(f"❌ ข้อผิดพลาดในการสร้างเลขที่เอกสาร: {str(e)}")
            return f"BL{year_month}0001"
    
    def close_connection(self):
        """ปิดการเชื่อมต่อฐานข้อมูล"""
        if self.connection:
            self.connection.close()
            print("✅ ปิดการเชื่อมต่อฐานข้อมูลแล้ว")

    def test_data(self):
        """ทดสอบข้อมูลในตาราง"""
        try:
            cursor = self.connection.cursor()
            
            # ตรวจสอบจำนวน Customer
            cursor.execute("SELECT COUNT(*) FROM Customer")
            customer_count = cursor.fetchone()[0]
            print(f"📊 จำนวน Customer: {customer_count}")
            
            # ตรวจสอบจำนวน Invoice
            cursor.execute("SELECT COUNT(*) FROM Invoice")
            invoice_count = cursor.fetchone()[0]
            print(f"📊 จำนวน Invoice: {invoice_count}")
            
            # ตรวจสอบ JOIN ระหว่าง Customer และ Invoice
            cursor.execute("""
                SELECT COUNT(*) 
                FROM Customer c 
                INNER JOIN Invoice iv ON c.CustomerId = iv.CustomerId
            """)
            join_count = cursor.fetchone()[0]
            print(f"📊 จำนวนข้อมูลที่ JOIN ได้: {join_count}")
            
            # ดูข้อมูลตัวอย่าง 5 รายการแรก
            cursor.execute("""
                SELECT TOP 5
                    c.CustomerId,
                    c.FirstName,
                    c.LastName,
                    iv.CustomerName,
                    iv.CustomerTaxNum
                FROM Customer c
                INNER JOIN Invoice iv ON c.CustomerId = iv.CustomerId
            """)
            
            print("📋 ข้อมูลตัวอย่าง:")
            for row in cursor.fetchall():
                print(f"   ID: {row[0]}, FirstName: {row[1]}, LastName: {row[2]}, CustomerName: {row[3]}, TaxNum: {row[4]}")
                
        except Exception as e:
            print(f"❌ ข้อผิดพลาดในการทดสอบข้อมูล: {str(e)}")

    def test_connection(self) -> bool:
        """ทดสอบการเชื่อมต่อฐานข้อมูล"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            print("✅ การเชื่อมต่อฐานข้อมูลทำงานปกติ")
            return True
        except Exception as e:
            print(f"❌ การเชื่อมต่อฐานข้อมูลมีปัญหา: {str(e)}")
            return False