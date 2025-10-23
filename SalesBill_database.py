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
    
    def generate_billing_doc_number(self) -> str:
        """สร้างเลขที่เอกสารใบวางบิล รูปแบบ DOCYYMM###"""
        try:
            cursor = self.connection.cursor()
            
            # Get current year and month (YY = 2 digit year, MM = month)
            cursor.execute("SELECT FORMAT(GETDATE(), 'yyMM')")
            year_month = cursor.fetchone()[0]
            
            # Get next sequence number (3 digits)
            cursor.execute("""
                SELECT ISNULL(MAX(CAST(RIGHT(BillingDocNumber, 3) AS INT)), 0) + 1
                FROM BillingDocument 
                WHERE LEFT(BillingDocNumber, 7) = ?
            """, (f"DOC{year_month}",))
            
            next_seq = cursor.fetchone()[0]
            
            # Format: DOC + YYMM + running number (3 digits)
            return f"DOC{year_month}{next_seq:03d}"
            
        except Exception as e:
            print(f"❌ ข้อผิดพลาดในการสร้างเลขที่เอกสาร: {str(e)}")
            # Fallback in case of error
            from datetime import datetime
            now = datetime.now()
            return f"DOC{now.strftime('%y%m')}001"

    def create_billing_document(self, customer_id: int, invoice_numbers: List[str], 
                        created_by: str, user_id: str, discount_amount: float = 0.0) -> Optional[str]:
        """สร้างเอกสารใบวางบิล"""
        try:
            cursor = self.connection.cursor()
            
            # Generate billing document number
            billing_doc_no = self.generate_billing_doc_number()
            
            # Get customer detail
            customer_detail = self.get_customer_detail(customer_id)
            
            # Debug: แสดงรายการที่ได้รับ
            print(f"📋 รายการใบแจ้งหนี้ที่ได้รับ: {invoice_numbers}")
            print(f"📋 ประเภทข้อมูล: {[type(inv) for inv in invoice_numbers]}")
            
            # Get invoice data
            total_unpaid_amount = 0.0
            invoice_details = []
            
            for invoice_no in invoice_numbers:
                # แปลงเป็น string และลบช่องว่าง
                invoice_no_str = str(invoice_no).strip()
                
                print(f"🔍 กำลังค้นหาใบแจ้งหนี้: '{invoice_no_str}'")
                
                cursor.execute("""
                    SELECT 
                        iv.InvoiceNumber,
                        iv.InvoiceDate,
                        iv.MaxDueDate,
                        DATEADD(day, iv.MaxDueDate, iv.InvoiceDate) as DueDate,
                        it.Total,
                        it.PaidAmount,
                        it.UnpaidAmount,
                        iv.Status
                    FROM Invoice iv
                    INNER JOIN InvoiceItem it ON it.InvoiceId = iv.InvoiceId
                    WHERE iv.InvoiceNumber = ?
                """, (invoice_no_str,))
                
                result = cursor.fetchone()
                if result:
                    print(f"✅ พบข้อมูลใบแจ้งหนี้: {result[0]}, Status: {result[7]}, UnpaidAmount: {result[6]}")
                    
                    # แปลงข้อมูล
                    try:
                        unpaid_amount = float(str(result[6]).replace(',', '')) if result[6] else 0.0
                        total_amount = float(str(result[4]).replace(',', '')) if result[4] else 0.0
                        paid_amount = float(str(result[5]).replace(',', '')) if result[5] else 0.0
                    except (ValueError, TypeError) as e:
                        print(f"❌ ข้อผิดพลาดในการแปลงตัวเลข: {e}")
                        unpaid_amount = 0.0
                        total_amount = 0.0
                        paid_amount = 0.0
                    
                    total_unpaid_amount += unpaid_amount
                    
                    invoice_details.append({
                        'InvoiceNumber': result[0],
                        'InvoiceDate': result[1],
                        'MaxDueDate': result[2],
                        'DueDate': result[3],
                        'Total': total_amount,
                        'PaidAmount': paid_amount,
                        'UnpaidAmount': unpaid_amount,
                        'Status': result[7]
                    })
                else:
                    print(f"❌ ไม่พบใบแจ้งหนี้: '{invoice_no_str}'")
            
            print(f"💰 ยอดรวมที่คำนวณได้: {total_unpaid_amount}")
            print(f"💸 ส่วนลด: {discount_amount}")
            
            # ⭐ คำนวณยอดสุทธิ
            net_total = total_unpaid_amount - discount_amount
            print(f"💵 ยอดสุทธิ: {net_total}")
            
            if not invoice_details:
                print("❌ ไม่มีข้อมูลใบแจ้งหนี้ที่ถูกต้อง")
                return None
            
            # Insert billing document header - ⭐ เพิ่ม DiscountAmount และ NetTotal
            insert_header = """
            INSERT INTO BillingDocument 
            (BillingDocNumber, CustomerId, CustomerName, CustomerAddress, CustomerPhone,
            CreateDate, CreatedBy, TotalAmount, DiscountAmount, NetTotal, TotalItems, Status, Notes, UserId)
            VALUES (?, ?, ?, ?, ?, GETDATE(), ?, ?, ?, ?, ?, 'Active', ?, ?)
            """
            
            customer_name = customer_detail.get('Name', '')
            customer_address = customer_detail.get('full_address', '')
            customer_phone = customer_detail.get('PhoneMobile', '')
            notes = f"ใบวางบิลจำนวน {len(invoice_details)} รายการ"
            
            cursor.execute(insert_header, (
                billing_doc_no, customer_id, customer_name, customer_address, 
                customer_phone, created_by, total_unpaid_amount, discount_amount, net_total,  # ⭐ เพิ่มตรงนี้
                len(invoice_details), notes, user_id
            ))
            
            # Get billing document ID
            cursor.execute("SELECT @@IDENTITY")
            billing_doc_id = cursor.fetchone()[0]
            
            # Insert billing document items
            for index, invoice_detail in enumerate(invoice_details, 1):
                insert_item = """
                INSERT INTO BillingDocumentItem 
                (BillingDocId, InvoiceNumber, InvoiceDate, MaxDueDate, DueDate, 
                Total, PaidAmount, UnpaidAmount, InvoiceAmount, ItemOrder)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                cursor.execute(insert_item, (
                    billing_doc_id,
                    invoice_detail['InvoiceNumber'],
                    invoice_detail['InvoiceDate'],
                    invoice_detail['MaxDueDate'],
                    invoice_detail['DueDate'],
                    invoice_detail['Total'],
                    invoice_detail['PaidAmount'],
                    invoice_detail['UnpaidAmount'],
                    invoice_detail['UnpaidAmount'],
                    index
                ))
            
            # Update Invoice Status = 99
            updated_count = 0
            for invoice_detail in invoice_details:
                invoice_no_str = str(invoice_detail['InvoiceNumber']).strip()
                
                print(f"🔄 กำลังอัพเดท Status ใบแจ้งหนี้: {invoice_no_str}")
                
                cursor.execute("""
                    UPDATE Invoice 
                    SET Status = 99 
                    WHERE InvoiceNumber = ? AND Status != 99
                """, (invoice_no_str,))
                
                rows_affected = cursor.rowcount
                print(f"📝 อัพเดท {invoice_no_str}: {rows_affected} แถว")
                
                if rows_affected > 0:
                    updated_count += 1
            
            self.connection.commit()
            
            print(f"สร้างเอกสารใบวางบิล {billing_doc_no} สำเร็จ")
            print(f"ข้อมูลที่บันทึก:")
            print(f"   - ลูกค้า: {customer_name}")
            print(f"   - จำนวนรายการ: {len(invoice_details)} รายการ")
            print(f"   - ยอดรวม: {total_unpaid_amount:,.2f} บาท")
            print(f"   - ส่วนลด: {discount_amount:,.2f} บาท")  # ⭐ เพิ่ม
            print(f"   - ยอดสุทธิ: {net_total:,.2f} บาท")  # ⭐ เพิ่ม
            print(f"   - อัพเดท Invoice Status = 99: {updated_count} รายการ")
            
            return billing_doc_no
            
        except Exception as e:
            self.connection.rollback()
            print(f"ข้อผิดพลาดในการสร้างเอกสารใบวางบิล: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
                                    
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
        
    def get_billing_history(self, date_from, date_to):
        """ดึงประวัติใบวางบิลตามช่วงวันที่"""
        try:
            cursor = self.connection.cursor()
            
            query = """
            SELECT 
                bd.BillingDocNumber,
                bd.CreateDate,
                bd.CustomerName,
                bd.TotalAmount,
                COALESCE(bd.DiscountAmount, 0) as DiscountAmount,  
                COALESCE(bd.NetTotal, bd.TotalAmount) as NetTotal,
                bd.TotalItems,
                bd.CreatedBy,
                CASE 
                    WHEN bd.Status = 'InActive' THEN 'ยกเลิกแล้ว'
                    ELSE 'ใช้งาน'
                END as Status
            FROM BillingDocument bd
            WHERE bd.CreateDate >= ? AND bd.CreateDate <= ?
            ORDER BY bd.CreateDate DESC
            """
            
            cursor.execute(query, (date_from, date_to))
            
            columns = [column[0] for column in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            return results
            
        except Exception as e:
            print(f"Error getting billing history: {str(e)}")
            return []
        
    def search_billing_history(self, search_term, date_from, date_to):
        """ค้นหาประวัติใบวางบิล"""
        try:
            cursor = self.connection.cursor()
            
            query = """
            SELECT 
                BillingDocNumber,
                CreateDate,
                CustomerName,
                TotalAmount,
                COALESCE(DiscountAmount, 0) as DiscountAmount,  
                COALESCE(NetTotal, TotalAmount) as NetTotal,     
                TotalItems,
                CreatedBy,
                CASE 
                    WHEN Status = 'InActive' THEN 'ยกเลิกแล้ว'
                    ELSE 'ใช้งาน'
                END as Status
            FROM BillingDocument
            WHERE CreateDate >= ? AND CreateDate <= ?
            AND (BillingDocNumber LIKE ? OR CustomerName LIKE ? OR CreatedBy LIKE ?)
            ORDER BY CreateDate DESC
            """
            
            search_pattern = f"%{search_term}%"
            cursor.execute(query, (date_from, date_to, search_pattern, search_pattern, search_pattern))
            
            columns = [desc[0] for desc in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                billing = dict(zip(columns, row))
                results.append(billing)
            
            return results
            
        except Exception as e:
            print(f"Error searching billing history: {str(e)}")
            return []
                        
    def get_billing_detail(self, billing_doc_number: str) -> Dict:
        """ดึงรายละเอียดใบวางบิล"""
        try:
            cursor = self.connection.cursor()
            
            query = """
            SELECT 
                BillingDocNumber,
                CustomerId,
                CustomerName,
                CustomerAddress,
                CustomerPhone,
                CreateDate,
                CreatedBy,
                TotalAmount,
                ISNULL(DiscountAmount, 0) as DiscountAmount,  
                ISNULL(NetTotal, TotalAmount) as NetTotal,     
                TotalItems,
                Status,
                Notes
            FROM BillingDocument
            WHERE BillingDocNumber = ?
            """
            
            cursor.execute(query, (billing_doc_number,))
            columns = [desc[0] for desc in cursor.description]
            row = cursor.fetchone()
            
            if row:
                return dict(zip(columns, row))
            
            return {}
            
        except Exception as e:
            print(f"ข้อผิดพลาดในการดึงรายละเอียด: {str(e)}")
            return {}
        
    def get_billing_items(self, billing_doc_number: str) -> List[Dict]:
        """ดึงรายการใบแจ้งหนี้ในใบวางบิล"""
        try:
            cursor = self.connection.cursor()
            
            query = """
            SELECT 
                bdi.ItemOrder,
                bdi.InvoiceNumber,
                bdi.InvoiceDate,
                bdi.MaxDueDate,
                bdi.DueDate,
                bdi.Total,
                bdi.PaidAmount,
                bdi.UnpaidAmount,
                bdi.InvoiceAmount
            FROM BillingDocumentItem bdi
            INNER JOIN BillingDocument bd ON bd.BillingDocId = bdi.BillingDocId
            WHERE bd.BillingDocNumber = ?
            ORDER BY bdi.ItemOrder
            """
            
            cursor.execute(query, (billing_doc_number,))
            columns = [desc[0] for desc in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                item = dict(zip(columns, row))
                results.append(item)
            
            return results
            
        except Exception as e:
            print(f"ข้อผิดพลาดในการดึงรายการ: {str(e)}")
            return []
        
    def cancel_billing_document(self, billing_doc_number):
        """ยกเลิกใบวางบิล - เปลี่ยนสถานะเป็น InActive และคืนสถานะ Invoice"""
        try:
            cursor = self.connection.cursor()
            
            # 1. ดึงรายการ Invoice ที่เกี่ยวข้องก่อนยกเลิก
            cursor.execute("""
                SELECT bdi.InvoiceNumber 
                FROM BillingDocumentItem bdi
                INNER JOIN BillingDocument bd ON bd.BillingDocId = bdi.BillingDocId
                WHERE bd.BillingDocNumber = ?
            """, (billing_doc_number,))
            
            invoice_numbers = [row[0] for row in cursor.fetchall()]
            
            if not invoice_numbers:
                return False, "ไม่พบรายการใบแจ้งหนี้ในเอกสารนี้"
            
            # 2. อัพเดทสถานะ BillingDocument เป็น InActive
            cursor.execute("""
                UPDATE BillingDocument 
                SET Status = 'InActive'
                WHERE BillingDocNumber = ?
            """, (billing_doc_number,))
            
            # 3. คืนสถานะ Invoice เป็น 0 (ยังไม่ได้วางบิล)
            placeholders = ','.join(['?' for _ in invoice_numbers])
            cursor.execute(f"""
                UPDATE invoice 
                SET Status = 0
                WHERE InvoiceNumber IN ({placeholders})
            """, invoice_numbers)
            
            # Commit transaction
            self.connection.commit()
            
            updated_count = len(invoice_numbers)
            
            print(f"✅ ยกเลิกใบวางบิล {billing_doc_number} สำเร็จ")
            print(f"   - คืนสถานะ Invoice: {updated_count} รายการ")
            
            return True, f"ยกเลิกสำเร็จ: คืนสถานะ {updated_count} รายการ"
            
        except Exception as e:
            print(f"❌ Error canceling billing document: {str(e)}")
            try:
                self.connection.rollback()
            except:
                pass
            return False, f"เกิดข้อผิดพลาด: {str(e)}"