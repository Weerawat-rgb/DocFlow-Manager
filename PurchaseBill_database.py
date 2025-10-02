import pyodbc
import json
from typing import List, Dict, Optional
from datetime import datetime

class PurchaseBillDatabase:
    def __init__(self, config_file='config.json'):
        """Initialize database connection using config file"""
        self.connection = None
        self.cursor = None
        self.config_file = config_file
        self.connect()
    
    def connect(self):
        """Connect to SQL Server using config.json"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
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
            self.cursor = self.connection.cursor()
            print("✅ เชื่อมต่อฐานข้อมูลสำเร็จ (Purchase)")
            
        except Exception as e:
            print(f"❌ เชื่อมต่อฐานข้อมูลไม่สำเร็จ: {str(e)}")
            raise
        
    def search_suppliers(self, search_term: str = "") -> List[Dict]:
        """ค้นหาซัพพลายเออร์และนับจำนวนใบรับสินค้า"""
        try:
            cursor = self.connection.cursor()
            
            if search_term:
                query = """
                SELECT 
                    s.SupplierId,
                    ISNULL(s.SupplierName, '') as [Name],
                    ISNULL(s.Address, '') as Address,
                    ISNULL(s.MobilePhone, '') as MobilePhone,
                    COUNT(r.ReceiveNumber) as ReceiveCount,
                    SUM(r.Total) as TotalAmount
                FROM Receive r
                INNER JOIN Supplier s ON s.SupplierId = r.SupplierId
                WHERE r.SupplierId != 0
                AND (
                    ISNULL(s.SupplierName, '') LIKE ?
                    OR ISNULL(s.Address, '') LIKE ?
                    OR ISNULL(s.MobilePhone, '') LIKE ?
                )
                AND (r.Remarks IS NULL OR r.Remarks != N'วางบิลเรียบร้อยแล้ว')
                GROUP BY s.SupplierId, s.SupplierName, s.Address, s.MobilePhone
                HAVING COUNT(r.ReceiveNumber) > 0
                ORDER BY s.SupplierName
                """
                search_pattern = f"%{search_term}%"
                cursor.execute(query, (search_pattern, search_pattern, search_pattern))
            else:
                query = """
                SELECT 
                    s.SupplierId,
                    ISNULL(s.SupplierName, '') as [Name],
                    ISNULL(s.Address, '') as Address,
                    ISNULL(s.MobilePhone, '') as MobilePhone,
                    COUNT(r.ReceiveNumber) as ReceiveCount,
                    SUM(r.Total) as TotalAmount
                FROM Receive r
                INNER JOIN Supplier s ON s.SupplierId = r.SupplierId
                WHERE r.SupplierId != 0 
                AND (r.Remarks IS NULL OR r.Remarks != N'วางบิลเรียบร้อยแล้ว')
                GROUP BY s.SupplierId, s.SupplierName, s.Address, s.MobilePhone
                HAVING COUNT(r.ReceiveNumber) > 0
                ORDER BY s.SupplierName
                """
                cursor.execute(query)
            
            columns = [desc[0] for desc in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                supplier = dict(zip(columns, row))
                supplier['CustomerId'] = supplier['SupplierId']
                supplier['Acct'] = ''
                results.append(supplier)
            
            print(f"พบซัพพลายเออร์ {len(results)} ราย")
            return results
            
        except Exception as e:
            print(f"ข้อผิดพลาด: {str(e)}")
            return []    
        
    def get_supplier_receives(self, supplier_id):
        try:
            query = """
                SELECT 
                    s.SupplierId,
                    s.SupplierName, 
                    s.Address, 
                    s.MobilePhone,
                    r.ReceiveDate, 
                    r.ReceiveNumber, 
                    r.InvoiceNumber,
                    s.CreditTerm, 
                    DATEADD(day, s.CreditTerm, r.ReceiveDate) as DueDate, 
                    r.Total
                FROM Receive r
                INNER JOIN Supplier s ON s.SupplierId = r.SupplierId
                WHERE r.SupplierId = ?
                    AND r.SupplierId != 0
                    AND (r.Remarks IS NULL OR r.Remarks != N'วางบิลเรียบร้อยแล้ว')
                ORDER BY r.ReceiveDate DESC
            """
            
            self.cursor.execute(query, (supplier_id,))
            rows = self.cursor.fetchall()
            
            receives = []
            for row in rows:
                receives.append({
                    'ReceiveId': row.ReceiveNumber,
                    'ReceiveNumber': row.ReceiveNumber,
                    'InvoiceNumber': row.InvoiceNumber,
                    'ReceiveDate': str(row.ReceiveDate)[:10] if row.ReceiveDate else '',
                    'MaxDueDate': row.CreditTerm or 0,
                    'DueDate': str(row.DueDate)[:10] if row.DueDate else '',
                    'Total': float(row.Total) if row.Total else 0.0,
                    'PaidAmount': 0.0,
                    'UnpaidAmount': float(row.Total) if row.Total else 0.0
                })
            
            print(f"พบใบรับสินค้า {len(receives)} รายการ")
            return receives
            
        except Exception as e:
            print(f"ข้อผิดพลาดในการดึงใบรับสินค้า: {str(e)}")
            return []                                                
    def get_supplier_detail(self, supplier_id: int) -> Dict:
        """ดึงข้อมูลซัพพลายเออร์แบบละเอียด"""
        try:
            cursor = self.connection.cursor()
            
            query = """
            SELECT 
                '' as Acct,
                ISNULL(SupplierName, '') as [Name],
                ISNULL(Address, '') as full_address,
                ISNULL(MobilePhone, '') as PhoneMobile,
                '' as CustomerTaxNum
            FROM Supplier
            WHERE SupplierId = ?
            """
            
            cursor.execute(query, (supplier_id,))
            row = cursor.fetchone()
            
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            
            return {}
            
        except Exception as e:
            print(f"Error getting supplier detail: {str(e)}")
            return {}
    
    def generate_billing_doc_number(self) -> str:
        """สร้างเลขที่เอกสารใบวางบิลซื้อ รูปแบบ PURYYMMnnn"""
        try:
            cursor = self.connection.cursor()
            
            # หาเลขที่ล่าสุดในเดือนปัจจุบัน
            current_year = datetime.now().strftime('%y')
            current_month = datetime.now().strftime('%m')
            prefix = f'PUR{current_year}{current_month}'
            
            cursor.execute("""
                SELECT TOP 1 BillingDocNumber 
                FROM PurchaseBillingDocument 
                WHERE BillingDocNumber LIKE ?
                ORDER BY BillingDocNumber DESC
            """, (f'{prefix}%',))
            
            result = cursor.fetchone()
            
            if result:
                last_number = result[0]
                # ดึงตัวเลข 3 หลักสุดท้าย
                last_seq = int(last_number[-3:])
                new_seq = last_seq + 1
            else:
                new_seq = 1
            
            # สร้างเลขที่ใหม่
            new_doc_no = f'{prefix}{new_seq:03d}'
            
            # ตรวจสอบซ้ำอีกครั้งเพื่อความแน่ใจ
            cursor.execute("""
                SELECT COUNT(*) 
                FROM PurchaseBillingDocument 
                WHERE BillingDocNumber = ?
            """, (new_doc_no,))
            
            count = cursor.fetchone()[0]
            
            # ถ้ายังซ้ำอยู่ ให้เพิ่มเลขต่อไป
            while count > 0:
                new_seq += 1
                new_doc_no = f'{prefix}{new_seq:03d}'
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM PurchaseBillingDocument 
                    WHERE BillingDocNumber = ?
                """, (new_doc_no,))
                count = cursor.fetchone()[0]
            
            print(f"สร้างเลขที่เอกสาร: {new_doc_no}")
            return new_doc_no
            
        except Exception as e:
            print(f"ข้อผิดพลาดในการสร้างเลขที่เอกสาร: {str(e)}")
            # Fallback: ใช้ timestamp
            timestamp = datetime.now().strftime('%y%m%d%H%M%S')
            return f'PUR{timestamp}'
            
    def create_billing_document(self, supplier_id: int, receive_numbers: List[str], 
                            created_by: str) -> Optional[str]:
        """สร้างเอกสารใบวางบิลซื้อ"""
        try:
            cursor = self.connection.cursor()
            
            billing_doc_no = self.generate_billing_doc_number()
            supplier_detail = self.get_supplier_detail(supplier_id)
            
            print(f"รายการใบรับสินค้าที่ได้รับ: {receive_numbers}")
            
            total_unpaid_amount = 0.0
            receive_details = []
            
            for receive_no in receive_numbers:
                receive_no_str = str(receive_no).strip()
                
                print(f"กำลังค้นหาใบรับสินค้า: '{receive_no_str}'")
                
                cursor.execute("""
                    SELECT 
                        r.ReceiveNumber,
                        r.InvoiceNumber,
                        r.ReceiveDate,
                        s.CreditTerm,
                        DATEADD(day, s.CreditTerm, r.ReceiveDate) as DueDate,
                        r.Total
                    FROM Receive r
                    INNER JOIN Supplier s ON s.SupplierId = r.SupplierId
                    WHERE r.ReceiveNumber = ?
                """, (receive_no_str,))
                
                result = cursor.fetchone()
                if result:
                    print(f"พบข้อมูลใบรับสินค้า: {result[0]}, Total: {result[5]}")
                    
                    try:
                        total_amount = float(str(result[5]).replace(',', '')) if result[5] else 0.0
                    except (ValueError, TypeError):
                        total_amount = 0.0
                    
                    total_unpaid_amount += total_amount
                    
                    receive_details.append({
                        'ReceiveNumber': result[0],
                        'InvoiceNumber': result[1],
                        'ReceiveDate': result[2],
                        'CreditTerm': result[3],
                        'DueDate': result[4],
                        'Total': total_amount
                    })
                else:
                    print(f"ไม่พบใบรับสินค้า: '{receive_no_str}'")
            
            if not receive_details:
                print("ไม่มีข้อมูลใบรับสินค้าที่ถูกต้อง")
                return None
            
            # Insert billing document header
            insert_header = """
            INSERT INTO PurchaseBillingDocument 
            (BillingDocNumber, SupplierId, SupplierName, SupplierAddress, SupplierPhone,
            CreateDate, CreatedBy, TotalAmount, TotalItems, Status, Notes)
            VALUES (?, ?, ?, ?, ?, GETDATE(), ?, ?, ?, 'Active', ?)
            """
            
            supplier_name = supplier_detail.get('Name', '')
            supplier_address = supplier_detail.get('full_address', '')
            supplier_phone = supplier_detail.get('PhoneMobile', '')
            notes = f"ใบวางบิลซื้อจำนวน {len(receive_details)} รายการ"
            
            cursor.execute(insert_header, (
                billing_doc_no, supplier_id, supplier_name, supplier_address, 
                supplier_phone, created_by, total_unpaid_amount, len(receive_details), notes
            ))
            
            cursor.execute("SELECT @@IDENTITY")
            billing_doc_id = cursor.fetchone()[0]
            
            # Insert billing document items
            for index, receive_detail in enumerate(receive_details, 1):
                insert_item = """
                INSERT INTO PurchaseBillingDocumentItem 
                (PurchaseBillingDocId, ReceiveNumber, InvoiceNumber, ReceiveDate, 
                CreditTerm, DueDate, Total, PaidAmount, UnpaidAmount, ReceiveAmount, ItemOrder)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                cursor.execute(insert_item, (
                    billing_doc_id,
                    receive_detail['ReceiveNumber'],
                    receive_detail['InvoiceNumber'],
                    receive_detail['ReceiveDate'],
                    receive_detail['CreditTerm'],
                    receive_detail['DueDate'],
                    receive_detail['Total'],
                    0,  # PaidAmount
                    receive_detail['Total'],  # UnpaidAmount
                    receive_detail['Total'],  # ReceiveAmount
                    index
                ))
            
            # Update Receive Remarks
            updated_count = 0
            for receive_detail in receive_details:
                receive_no_str = str(receive_detail['ReceiveNumber']).strip()
                
                cursor.execute("""
                    UPDATE Receive 
                    SET Remarks = N'วางบิลเรียบร้อยแล้ว' 
                    WHERE ReceiveNumber = ? 
                """, (receive_no_str,))
                
                if cursor.rowcount > 0:
                    updated_count += 1
            
            self.connection.commit()
            
            print(f"สร้างเอกสารใบวางบิลซื้อ {billing_doc_no} สำเร็จ")
            print(f"   - ซัพพลายเออร์: {supplier_name}")
            print(f"   - จำนวนรายการ: {len(receive_details)} รายการ")
            print(f"   - ยอดรวม: {total_unpaid_amount:,.2f} บาท")
            print(f"   - อัพเดท Remarks: {updated_count}/{len(receive_details)} รายการ")
            
            return billing_doc_no
            
        except Exception as e:
            self.connection.rollback()
            print(f"ข้อผิดพลาดในการสร้างเอกสารใบวางบิลซื้อ: {str(e)}")
            import traceback
            traceback.print_exc()
            return None
                    
    def get_billing_history(self, date_from, date_to):
        """ดึงประวัติใบวางบิล"""
        try:
            query = """
                SELECT 
                    BillingDocNumber,
                    SupplierName,
                    CreateDate,
                    TotalItems,
                    TotalAmount,
                    Status,
                    CreatedBy
                FROM PurchaseBillingDocument
                WHERE CreateDate >= ? AND CreateDate <= ?
                ORDER BY CreateDate DESC
            """
            
            self.cursor.execute(query, (date_from, date_to))
            rows = self.cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    'BillingDocNumber': row.BillingDocNumber,
                    'SupplierName': row.SupplierName,
                    'CreateDate': row.CreateDate,
                    'TotalItems': row.TotalItems,
                    'TotalAmount': float(row.TotalAmount) if row.TotalAmount else 0.0,
                    'Status': row.Status,
                    'CreatedBy': row.CreatedBy
                })
            
            return results
            
        except Exception as e:
            print(f"Error: {str(e)}")
            return []

    def search_billing_history(self, search_term, date_from, date_to):
        """ค้นหาประวัติใบวางบิล"""
        try:
            query = """
                SELECT 
                    BillingDocNumber,
                    SupplierName,
                    CreateDate,
                    TotalItems,
                    TotalAmount,
                    Status,
                    CreatedBy
                FROM PurchaseBillingDocument
                WHERE CreateDate >= ? AND CreateDate <= ?
                    AND (BillingDocNumber LIKE ? 
                    OR SupplierName LIKE ? 
                    OR CreatedBy LIKE ?)
                ORDER BY CreateDate DESC
            """
            
            search_pattern = f'%{search_term}%'
            self.cursor.execute(query, (date_from, date_to, search_pattern, search_pattern, search_pattern))
            rows = self.cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    'BillingDocNumber': row.BillingDocNumber,
                    'SupplierName': row.SupplierName,
                    'CreateDate': row.CreateDate,
                    'TotalItems': row.TotalItems,
                    'TotalAmount': float(row.TotalAmount) if row.TotalAmount else 0.0,
                    'Status': row.Status,
                    'CreatedBy': row.CreatedBy
                })
            
            return results
            
        except Exception as e:
            print(f"Error: {str(e)}")
            return []
            
    def test_connection(self):
        """ทดสอบการเชื่อมต่อฐานข้อมูล"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            return True
        except:
            return False
        
    def test_data(self):
        """ทดสอบข้อมูลในตาราง"""
        try:
            cursor = self.connection.cursor()
            
            # ตรวจสอบจำนวน Supplier
            cursor.execute("SELECT COUNT(*) FROM Supplier")
            supplier_count = cursor.fetchone()[0]
            print(f"📊 จำนวน Supplier: {supplier_count}")
            
            # ตรวจสอบจำนวน Receive
            cursor.execute("SELECT COUNT(*) FROM Receive WHERE SupplierId != 0")
            receive_count = cursor.fetchone()[0]
            print(f"📊 จำนวน Receive: {receive_count}")
            
            # ตรวจสอบ JOIN
            cursor.execute("""
                SELECT COUNT(*) 
                FROM Supplier s 
                INNER JOIN Receive r ON s.SupplierId = r.SupplierId
                WHERE r.SupplierId != 0
            """)
            join_count = cursor.fetchone()[0]
            print(f"📊 จำนวนข้อมูลที่ JOIN ได้: {join_count}")
            
            # ดูข้อมูลตัวอย่าง 5 รายการแรก
            cursor.execute("""
                SELECT TOP 5
                    s.SupplierId,
                    s.SupplierName,
                    r.ReceiveNumber,
                    r.Total
                FROM Supplier s
                INNER JOIN Receive r ON s.SupplierId = r.SupplierId
                WHERE r.SupplierId != 0
            """)
            
            print("📋 ข้อมูลตัวอย่าง:")
            for row in cursor.fetchall():
                print(f"   ID: {row[0]}, Name: {row[1]}, ReceiveNo: {row[2]}, Total: {row[3]}")
                
        except Exception as e:
            print(f"❌ ข้อผิดพลาดในการทดสอบข้อมูล: {str(e)}")
    
    def close_connection(self):
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            print("✅ ปิดการเชื่อมต่อฐานข้อมูล")
        except Exception as e:
            print(f"❌ ข้อผิดพลาดในการปิดการเชื่อมต่อ: {str(e)}")
            
    def get_billing_history(self, date_from, date_to):
        """ดึงประวัติใบวางบิล"""
        try:
            query = """
                SELECT 
                    BillingDocNumber,
                    SupplierName,
                    CreateDate,
                    TotalItems,
                    TotalAmount,
                    Status,
                    CreatedBy
                FROM PurchaseBillingDocument
                WHERE CreateDate BETWEEN ? AND ?
                ORDER BY CreateDate DESC
            """
            
            self.cursor.execute(query, (date_from, date_to))
            rows = self.cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    'BillingDocNumber': row.BillingDocNumber,
                    'SupplierName': row.SupplierName,
                    'CreateDate': row.CreateDate,
                    'TotalItems': row.TotalItems,
                    'TotalAmount': float(row.TotalAmount) if row.TotalAmount else 0.0,
                    'Status': row.Status,
                    'CreatedBy': row.CreatedBy
                })
            
            return results
            
        except Exception as e:
            print(f"Error: {str(e)}")
            return []


    def get_billing_detail(self, billing_doc_no):
        """ดึงรายละเอียดใบวางบิล"""
        try:
            query = """
                SELECT * 
                FROM PurchaseBillingDocument
                WHERE BillingDocNumber = ?
            """
            
            self.cursor.execute(query, (billing_doc_no,))
            row = self.cursor.fetchone()
            
            if row:
                return {
                    'BillingDocNumber': row.BillingDocNumber,
                    'SupplierName': row.SupplierName,
                    'SupplierAddress': row.SupplierAddress,
                    'SupplierPhone': row.SupplierPhone,
                    'SupplierTaxNum': getattr(row, 'SupplierTaxNum', ''),
                    'CreateDate': row.CreateDate,
                    'TotalAmount': float(row.TotalAmount) if row.TotalAmount else 0.0,
                    'TotalItems': row.TotalItems,
                    'Status': row.Status,
                    'CreatedBy': row.CreatedBy,
                    'Notes': row.Notes
                }
            
            return None
            
        except Exception as e:
            print(f"Error: {str(e)}")
            return None

    def get_billing_items(self, billing_doc_no):
        """ดึงรายการในใบวางบิล"""
        try:
            query = """
                SELECT 
                    i.ReceiveNumber,
                    i.InvoiceNumber,
                    i.ReceiveDate,
                    i.CreditTerm,
                    i.DueDate,
                    i.Total,
                    i.PaidAmount,
                    i.UnpaidAmount,
                    i.ItemOrder
                FROM PurchaseBillingDocumentItem i
                INNER JOIN PurchaseBillingDocument d ON d.PurchaseBillingDocId = i.PurchaseBillingDocId
                WHERE d.BillingDocNumber = ?
                ORDER BY i.ItemOrder
            """
            
            self.cursor.execute(query, (billing_doc_no,))
            rows = self.cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    'ReceiveNumber': row.ReceiveNumber,
                    'InvoiceNumber': row.InvoiceNumber,
                    'ReceiveDate': row.ReceiveDate,
                    'CreditTerm': row.CreditTerm,
                    'DueDate': row.DueDate,
                    'Total': float(row.Total) if row.Total else 0.0,
                    'PaidAmount': float(row.PaidAmount) if row.PaidAmount else 0.0,
                    'UnpaidAmount': float(row.UnpaidAmount) if row.UnpaidAmount else 0.0,
                    'ItemOrder': row.ItemOrder
                })
            
            return results
            
        except Exception as e:
            print(f"Error: {str(e)}")
            return []

    def cancel_billing_document(self, billing_doc_no):
        """ยกเลิกใบวางบิล"""
        try:
            # อัพเดทสถานะเป็น InActive
            query1 = """
                UPDATE PurchaseBillingDocument 
                SET Status = 'InActive', UpdatedDate = GETDATE()
                WHERE BillingDocNumber = ?
            """
            self.cursor.execute(query1, (billing_doc_no,))
            
            # อัพเดท Remarks ของ Receive กลับเป็นว่าง
            query2 = """
                UPDATE Receive 
                SET Remarks = NULL
                WHERE ReceiveNumber IN (
                    SELECT i.ReceiveNumber
                    FROM PurchaseBillingDocumentItem i
                    INNER JOIN PurchaseBillingDocument d ON d.PurchaseBillingDocId = i.PurchaseBillingDocId
                    WHERE d.BillingDocNumber = ?
                )
            """
            self.cursor.execute(query2, (billing_doc_no,))
            
            self.connection.commit()
            
            return True, f"ยกเลิกใบวางบิล {billing_doc_no} สำเร็จ"
            
        except Exception as e:
            self.connection.rollback()
            return False, f"ไม่สามารถยกเลิกได้: {str(e)}"
                

        """ดึงรายการในใบวางบิล"""
        try:
            query = """
                SELECT 
                    ReceiveNumber,
                    InvoiceNumber,
                    ReceiveDate,
                    CreditTerm,
                    DueDate,
                    Total,
                    PaidAmount,
                    UnpaidAmount,
                    ItemOrder
                FROM PurchaseBillingDocumentItem
                WHERE PurchaseBillingDocId = (
                    SELECT PurchaseBillingDocId 
                    FROM PurchaseBillingDocument 
                    WHERE BillingDocNumber = ?
                )
                ORDER BY ItemOrder
            """
            
            self.cursor.execute(query, (billing_doc_id,))
            rows = self.cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    'ReceiveNumber': row.ReceiveNumber,
                    'InvoiceNumber': row.InvoiceNumber,
                    'ReceiveDate': str(row.ReceiveDate) if row.ReceiveDate else '',
                    'CreditTerm': row.CreditTerm,
                    'DueDate': str(row.DueDate) if row.DueDate else '',
                    'Total': float(row.Total) if row.Total else 0.0,
                    'PaidAmount': float(row.PaidAmount) if row.PaidAmount else 0.0,
                    'UnpaidAmount': float(row.UnpaidAmount) if row.UnpaidAmount else 0.0,
                    'ItemOrder': row.ItemOrder
                })
            
            return results
            
        except Exception as e:
            print(f"Error getting billing items: {str(e)}")
            return []