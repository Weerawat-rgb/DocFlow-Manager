import pyodbc
import json
from typing import List, Dict, Optional
from datetime import datetime

class BranchBillDatabase:
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
            print("✅ เชื่อมต่อฐานข้อมูลสำเร็จ (Branch Bill)")
            
        except Exception as e:
            print(f"❌ เชื่อมต่อฐานข้อมูลไม่สำเร็จ: {str(e)}")
            raise
        
    def search_branches(self, search_term: str = "") -> List[Dict]:
        """ค้นหาสาขาและนับจำนวนใบเบิกโอนที่ยังไม่ได้วางบิล"""
        try:
            cursor = self.connection.cursor()
            
            if search_term:
                query = """
                SELECT 
                    w.TransferToBranchName as BranchName,
                    COUNT(DISTINCT w.WithdrawalNumber) as WithdrawalCount,
                    SUM(wi.TotalCost) as TotalAmount
                FROM Withdrawal w
                INNER JOIN WithdrawalItem wi ON wi.WithdrawalId = w.WithdrawalId
                WHERE w.WithdrawalTypeId = 1 
                    AND w.Active = 1 
                    AND (w.Description IS NULL OR w.Description != N'วางบิลเรียบร้อยแล้ว')
                    AND w.TransferToBranchName LIKE ?
                GROUP BY w.TransferToBranchName
                HAVING COUNT(DISTINCT w.WithdrawalNumber) > 0
                ORDER BY w.TransferToBranchName
                """
                search_pattern = f"%{search_term}%"
                cursor.execute(query, (search_pattern,))
            else:
                query = """
                SELECT 
                    w.TransferToBranchName as BranchName,
                    COUNT(DISTINCT w.WithdrawalNumber) as WithdrawalCount,
                    SUM(wi.TotalCost) as TotalAmount
                FROM Withdrawal w
                INNER JOIN WithdrawalItem wi ON wi.WithdrawalId = w.WithdrawalId
                WHERE w.WithdrawalTypeId = 1 
                    AND w.Active = 1 
                    AND (w.Description IS NULL OR w.Description != N'วางบิลเรียบร้อยแล้ว')
                GROUP BY w.TransferToBranchName
                HAVING COUNT(DISTINCT w.WithdrawalNumber) > 0
                ORDER BY w.TransferToBranchName
                """
                cursor.execute(query)
            
            columns = [desc[0] for desc in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                branch = dict(zip(columns, row))
                results.append(branch)
            
            print(f"พบสาขา {len(results)} สาขา")
            return results
            
        except Exception as e:
            print(f"ข้อผิดพลาด: {str(e)}")
            return []
    
    def get_branch_withdrawals(self, branch_name: str) -> List[Dict]:
        """ดึงรายการใบเบิกโอนของสาขาที่ยังไม่ได้วางบิล"""
        try:
            query = """
            SELECT 
                w.WithdrawalNumber,
                w.WithdrawalDate,
                SUM(wi.TotalCost) as TotalAmount
            FROM Withdrawal w
            INNER JOIN WithdrawalItem wi ON wi.WithdrawalId = w.WithdrawalId
            WHERE w.WithdrawalTypeId = 1 
                AND w.Active = 1 
                AND (w.Description IS NULL OR w.Description != N'วางบิลเรียบร้อยแล้ว')
                AND w.TransferToBranchName = ?
            GROUP BY w.WithdrawalNumber, w.WithdrawalDate
            ORDER BY w.WithdrawalDate DESC
            """
            
            self.cursor.execute(query, (branch_name,))
            rows = self.cursor.fetchall()
            
            withdrawals = []
            for row in rows:
                withdrawals.append({
                    'WithdrawalNumber': row.WithdrawalNumber,
                    'WithdrawalDate': str(row.WithdrawalDate)[:10] if row.WithdrawalDate else '',
                    'Total': float(row.TotalAmount) if row.TotalAmount else 0.0
                })
            
            print(f"พบใบเบิกโอน {len(withdrawals)} รายการ")
            return withdrawals
            
        except Exception as e:
            print(f"ข้อผิดพลาดในการดึงใบเบิกโอน: {str(e)}")
            return []
    
    def get_branch_detail(self, branch_name: str) -> Dict:
        """ดึงข้อมูลสาขา (ในกรณีนี้เป็นข้อมูลพื้นฐาน)"""
        try:
            return {
                'Name': branch_name,
                'full_address': '',  # ถ้ามีตารางสาขาแยกสามารถ JOIN เพิ่ม
                'PhoneMobile': ''
            }
            
        except Exception as e:
            print(f"Error getting branch detail: {str(e)}")
            return {}
    
    def generate_billing_doc_number(self) -> str:
        """สร้างเลขที่เอกสารใบวางบิลสาขา รูปแบบ BRYYMMnnn"""
        try:
            cursor = self.connection.cursor()
            
            current_year = datetime.now().strftime('%y')
            current_month = datetime.now().strftime('%m')
            prefix = f'BR{current_year}{current_month}'
            
            cursor.execute("""
                SELECT TOP 1 BillingDocNumber 
                FROM BranchBillingDocument 
                WHERE BillingDocNumber LIKE ?
                ORDER BY BillingDocNumber DESC
            """, (f'{prefix}%',))
            
            result = cursor.fetchone()
            
            if result:
                last_number = result[0]
                last_seq = int(last_number[-3:])
                new_seq = last_seq + 1
            else:
                new_seq = 1
            
            new_doc_no = f'{prefix}{new_seq:03d}'
            
            cursor.execute("""
                SELECT COUNT(*) 
                FROM BranchBillingDocument 
                WHERE BillingDocNumber = ?
            """, (new_doc_no,))
            
            count = cursor.fetchone()[0]
            
            while count > 0:
                new_seq += 1
                new_doc_no = f'{prefix}{new_seq:03d}'
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM BranchBillingDocument 
                    WHERE BillingDocNumber = ?
                """, (new_doc_no,))
                count = cursor.fetchone()[0]
            
            print(f"สร้างเลขที่เอกสาร: {new_doc_no}")
            return new_doc_no
            
        except Exception as e:
            print(f"ข้อผิดพลาดในการสร้างเลขที่เอกสาร: {str(e)}")
            timestamp = datetime.now().strftime('%y%m%d%H%M%S')
            return f'BR{timestamp}'
    
    def create_billing_document(self, branch_name: str, withdrawal_numbers: List[str], 
                                created_by: str, discount_amount: float = 0.00, 
                                net_total: Optional[float] = None) -> Optional[str]:
            """สร้างเอกสารใบวางบิลสาขา"""
            try:
                cursor = self.connection.cursor()
                
                billing_doc_no = self.generate_billing_doc_number()
                branch_detail = self.get_branch_detail(branch_name)
                
                print(f"รายการใบเบิกโอนที่ได้รับ: {withdrawal_numbers}")
                
                total_amount = 0.0
                withdrawal_details = []
                
                for withdrawal_no in withdrawal_numbers:
                    withdrawal_no_str = str(withdrawal_no).strip()
                    
                    print(f"กำลังค้นหาใบเบิกโอน: '{withdrawal_no_str}'")
                    
                    cursor.execute("""
                        SELECT 
                            w.WithdrawalNumber,
                            w.WithdrawalDate,
                            SUM(wi.TotalCost) as TotalAmount
                        FROM Withdrawal w
                        INNER JOIN WithdrawalItem wi ON wi.WithdrawalId = w.WithdrawalId
                        WHERE w.WithdrawalNumber = ?
                        GROUP BY w.WithdrawalNumber, w.WithdrawalDate
                    """, (withdrawal_no_str,))
                    
                    result = cursor.fetchone()
                    if result:
                        print(f"พบข้อมูลใบเบิกโอน: {result[0]}, Total: {result[2]}")
                        
                        try:
                            amount = float(str(result[2]).replace(',', '')) if result[2] else 0.0
                        except (ValueError, TypeError):
                            amount = 0.0
                        
                        total_amount += amount
                        
                        withdrawal_details.append({
                            'WithdrawalNumber': result[0],
                            'WithdrawalDate': result[1],
                            'Total': amount
                        })
                    else:
                        print(f"ไม่พบใบเบิกโอน: '{withdrawal_no_str}'")
                
                if not withdrawal_details:
                    print("ไม่มีข้อมูลใบเบิกโอนที่ถูกต้อง")
                    return None
                
                # คำนวณ net_total ถ้าไม่ได้ส่งมา
                if net_total is None:
                    net_total = total_amount - discount_amount
                
                # Insert billing document header พร้อม DiscountAmount และ NetTotal
                insert_header = """
                INSERT INTO BranchBillingDocument 
                (BillingDocNumber, BranchName, BranchAddress, BranchPhone,
                CreateDate, CreatedBy, TotalAmount, DiscountAmount, NetTotal, 
                TotalItems, Status, Notes)
                VALUES (?, ?, ?, ?, GETDATE(), ?, ?, ?, ?, ?, 'Active', ?)
                """
                
                branch_address = branch_detail.get('full_address', '')
                branch_phone = branch_detail.get('PhoneMobile', '')
                notes = f"ใบวางบิลสาขาจำนวน {len(withdrawal_details)} รายการ"
                
                cursor.execute(insert_header, (
                    billing_doc_no, branch_name, branch_address, 
                    branch_phone, created_by, total_amount, 
                    discount_amount, net_total,  # เพิ่มตรงนี้
                    len(withdrawal_details), notes
                ))
                
                cursor.execute("SELECT @@IDENTITY")
                billing_doc_id = cursor.fetchone()[0]
                
                # Insert billing document items
                for index, withdrawal_detail in enumerate(withdrawal_details, 1):
                    insert_item = """
                    INSERT INTO BranchBillingDocumentItem 
                    (BranchBillingDocId, WithdrawalNumber, WithdrawalDate, TotalAmount, ItemOrder)
                    VALUES (?, ?, ?, ?, ?)
                    """
                    
                    cursor.execute(insert_item, (
                        billing_doc_id,
                        withdrawal_detail['WithdrawalNumber'],
                        withdrawal_detail['WithdrawalDate'],
                        withdrawal_detail['Total'],
                        index
                    ))
                
                # Update Withdrawal Description
                updated_count = 0
                for withdrawal_detail in withdrawal_details:
                    withdrawal_no_str = str(withdrawal_detail['WithdrawalNumber']).strip()
                    
                    cursor.execute("""
                        UPDATE Withdrawal 
                        SET Description = N'วางบิลเรียบร้อยแล้ว' 
                        WHERE WithdrawalNumber = ? 
                    """, (withdrawal_no_str,))
                    
                    if cursor.rowcount > 0:
                        updated_count += 1
                
                self.connection.commit()
                self.cursor.close()  # ปิด cursor เดิม
                self.cursor = self.connection.cursor()  # สร้างใหม่
                
                print(f"สร้างเอกสารใบวางบิลสาขา {billing_doc_no} สำเร็จ")
                print(f"   - สาขา: {branch_name}")
                print(f"   - จำนวนรายการ: {len(withdrawal_details)} รายการ")
                print(f"   - ยอดรวม: {total_amount:,.2f} บาท")
                print(f"   - ส่วนลด: {discount_amount:,.2f} บาท")
                print(f"   - ยอดสุทธิ: {net_total:,.2f} บาท")
                print(f"   - อัพเดท Description: {updated_count}/{len(withdrawal_details)} รายการ")
                
                return billing_doc_no
                
            except Exception as e:
                self.connection.rollback()
                print(f"ข้อผิดพลาดในการสร้างเอกสารใบวางบิลสาขา: {str(e)}")
                import traceback
                traceback.print_exc()
                return None
                
    def get_billing_history(self, date_from, date_to):
        """ดึงประวัติใบวางบิล"""
        try:
            query = """
                SELECT 
                    BillingDocNumber,
                    BranchName,
                    CreateDate,
                    TotalItems,
                    TotalAmount,
                    DiscountAmount,
                    NetTotal,
                    Status,
                    CreatedBy
                FROM BranchBillingDocument
                WHERE CreateDate BETWEEN ? AND ?
                ORDER BY CreateDate DESC
            """
            
            self.cursor.execute(query, (date_from, date_to))
            rows = self.cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                'BillingDocNumber': row.BillingDocNumber,
                'BranchName': row.BranchName,
                'CreateDate': row.CreateDate,
                'TotalItems': row.TotalItems,
                'TotalAmount': float(row.TotalAmount) if row.TotalAmount else 0.0,
                'DiscountAmount': float(row.DiscountAmount) if row.DiscountAmount else 0.0,  
                'NetTotal': float(row.NetTotal) if row.NetTotal else 0.0,                      
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
                    BranchName,
                    CreateDate,
                    TotalItems,
                    TotalAmount,
                    DiscountAmount,
                    NetTotal,
                    Status,
                    CreatedBy
                FROM BranchBillingDocument
                WHERE CreateDate >= ? AND CreateDate <= ?
                    AND (BillingDocNumber LIKE ? 
                    OR BranchName LIKE ? 
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
                    'BranchName': row.BranchName,
                    'CreateDate': row.CreateDate,
                    'TotalItems': row.TotalItems,
                    'TotalAmount': float(row.TotalAmount) if row.TotalAmount else 0.0,
                    'DiscountAmount': float(row.DiscountAmount) if row.DiscountAmount else 0.0,  
                    'NetTotal': float(row.NetTotal) if row.NetTotal else 0.0,                      
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
                FROM BranchBillingDocument
                WHERE BillingDocNumber = ?
            """
            
            self.cursor.execute(query, (billing_doc_no,))
            row = self.cursor.fetchone()
            
            if row:
                return {
                    'BillingDocNumber': row.BillingDocNumber,
                    'BranchName': row.BranchName,
                    'BranchAddress': row.BranchAddress,
                    'BranchPhone': row.BranchPhone,
                    'CreateDate': row.CreateDate,
                    'TotalAmount': float(row.TotalAmount) if row.TotalAmount else 0.0,
                    'DiscountAmount': float(row.DiscountAmount) if row.DiscountAmount else 0.0,  
                    'NetTotal': float(row.NetTotal) if row.NetTotal else 0.0,                      
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
                    i.WithdrawalNumber,
                    i.WithdrawalDate,
                    i.TotalAmount,
                    i.ItemOrder
                FROM BranchBillingDocumentItem i
                INNER JOIN BranchBillingDocument d ON d.BranchBillingDocId = i.BranchBillingDocId
                WHERE d.BillingDocNumber = ?
                ORDER BY i.ItemOrder
            """
            
            self.cursor.execute(query, (billing_doc_no,))
            rows = self.cursor.fetchall()
            
            results = []
            for row in rows:
                results.append({
                    'WithdrawalNumber': row.WithdrawalNumber,
                    'WithdrawalDate': row.WithdrawalDate,
                    'TotalAmount': float(row.TotalAmount) if row.TotalAmount else 0.0,
                    'ItemOrder': row.ItemOrder
                })
            
            return results
            
        except Exception as e:
            print(f"Error: {str(e)}")
            return []

    def cancel_billing_document(self, billing_doc_no):
        """ยกเลิกใบวางบิล"""
        try:
            query1 = """
                UPDATE BranchBillingDocument 
                SET Status = 'InActive', UpdatedDate = GETDATE()
                WHERE BillingDocNumber = ?
            """
            self.cursor.execute(query1, (billing_doc_no,))
            
            query2 = """
                UPDATE Withdrawal 
                SET Description = NULL
                WHERE WithdrawalNumber IN (
                    SELECT i.WithdrawalNumber
                    FROM BranchBillingDocumentItem i
                    INNER JOIN BranchBillingDocument d ON d.BranchBillingDocId = i.BranchBillingDocId
                    WHERE d.BillingDocNumber = ?
                )
            """
            self.cursor.execute(query2, (billing_doc_no,))
            
            self.connection.commit()
            
            return True, f"ยกเลิกใบวางบิล {billing_doc_no} สำเร็จ"
            
        except Exception as e:
            self.connection.rollback()
            return False, f"ไม่สามารถยกเลิกได้: {str(e)}"
    
    def test_connection(self):
        """ทดสอบการเชื่อมต่อฐานข้อมูล"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT 1")
            cursor.fetchone()
            return True
        except:
            return False
    
    def close_connection(self):
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            print("✅ ปิดการเชื่อมต่อฐานข้อมูล")
        except Exception as e:
            print(f"❌ ข้อผิดพลาดในการปิดการเชื่อมต่อ: {str(e)}")