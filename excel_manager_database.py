import pyodbc
import json
from datetime import datetime
from typing import List, Dict, Tuple, Optional

class ExcelManagerDatabase:
    """จัดการฐานข้อมูลสำหรับ Import Excel - ReceiveItem"""
    
    def __init__(self):
        """Initialize database connection"""
        self.connection = None
        self.cursor = None
        self.connect()
    
    def connect(self):
        """เชื่อมต่อฐานข้อมูลจาก config.json"""
        try:
            # อ่าน config.json
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # ดึงค่า connection string จาก config
            db_config = config.get('database', {})
            
            # ดึงค่าต่างๆ
            server = db_config.get('server', 'localhost')
            port = db_config.get('port', '')
            database = db_config.get('database', '')
            username = db_config.get('username', '')
            password = db_config.get('password', '')
            driver = db_config.get('driver', 'SQL Server')
            
            # สร้าง server string พร้อม port (ถ้ามี)
            server_string = f"{server},{port}" if port else server
            
            # สร้าง connection string
            connection_string = (
                f"DRIVER={{{driver}}};"
                f"SERVER={server_string};"
                f"DATABASE={database};"
                f"UID={username};"
                f"PWD={password}"
            )
            
            self.connection = pyodbc.connect(connection_string)
            self.cursor = self.connection.cursor()
            
        except FileNotFoundError:
            raise Exception("ไม่พบไฟล์ config.json")
        except json.JSONDecodeError:
            raise Exception("ไฟล์ config.json ไม่ถูกต้อง")
        except Exception as e:
            raise Exception(f"Database connection failed: {str(e)}")
    
    def test_connection(self) -> bool:
        """ทดสอบการเชื่อมต่อ"""
        try:
            self.cursor.execute("SELECT 1")
            return True
        except:
            return False
    
    def get_user_id_by_username(self, username: str) -> Optional[int]:
        """
        ดึง UserId จาก Username
        
        Args:
            username: ชื่อผู้ใช้
            
        Returns:
            UserId หรือ None ถ้าไม่พบ
        """
        try:
            query = "SELECT UserId FROM Users WHERE Username = ?"
            self.cursor.execute(query, username)
            row = self.cursor.fetchone()
            
            if row:
                return row[0]
            
            return None
            
        except Exception as e:
            print(f"Failed to get UserId: {str(e)}")
            return None
    
    def get_next_lot_number(self) -> str:
        """
        สร้างเลขที่ Lot
        Format: U-01ddmmyy001 (เช่น U-01051224001) - ไม่เว้นวรรค
        รีเซ็ทตามวัน
        """
        try:
            current_date = datetime.now()
            buddhist_year = current_date.year + 543  
            year_str = str(buddhist_year)[-2:]       
            # สร้าง date string
            date_str = current_date.strftime('%d%m') + year_str  
            prefix = f'U-01{date_str}'  
            
            # หา running number ล่าสุดของวันนี้
            query = """
                SELECT TOP 1 Lot 
                FROM Receive 
                WHERE Lot LIKE ? AND Lot IS NOT NULL
                ORDER BY Lot DESC
            """
            
            self.cursor.execute(query, f'{prefix}%')
            row = self.cursor.fetchone()
            
            if row and row[0]:
                try:
                    # ดึง running number จาก format U-01051224001
                    # เอา 3 ตัวสุดท้าย
                    lot_str = row[0].strip()
                    if len(lot_str) >= 3:
                        last_number = lot_str[-3:]  # เอา 3 ตัวสุดท้าย
                        running = int(last_number) + 1
                    else:
                        running = 1
                except (ValueError, IndexError) as e:
                    print(f"Warning: ไม่สามารถ parse Lot number '{row[0]}' ได้ เริ่มใหม่ที่ 001")
                    running = 1
            else:
                running = 1
            
            # สร้างเลขที่ Lot (ไม่เว้นวรรค)
            lot_number = f"{prefix}{running:03d}"
            
            return lot_number
            
        except Exception as e:
            print(f"Warning: ไม่สามารถสร้าง lot number ได้: {str(e)}")
            # ถ้า error ให้ใช้ default
            current_date = datetime.now()
            date_str = current_date.strftime('%d%m%y')
            return f"U-01{date_str}001"
    
    def get_next_receive_number(self) -> str:
        """
        สร้างเลขที่เอกสารรับสินค้า
        Format: RC+yymm/running number 3 digits (เช่น RC6810/001) - yy เป็นปี พ.ศ.
        """
        try:
            current_date = datetime.now()
            
            # คำนวณปี พ.ศ. (พุทธศักราช = ค.ศ. + 543)
            buddhist_year = current_date.year + 543
            year_str = str(buddhist_year)[-2:]  # เอา 2 หลักสุดท้าย เช่น 68
            
            # สร้าง yymm (6810 = ตุลาคม 2568)
            yymm = year_str + current_date.strftime('%m')
            prefix = f'RC{yymm}/'
            
            # หา running number ล่าสุด
            query = """
                SELECT TOP 1 ReceiveNumber 
                FROM Receive 
                WHERE ReceiveNumber LIKE ?
                ORDER BY ReceiveNumber DESC
            """
            
            self.cursor.execute(query, f'{prefix}%')
            row = self.cursor.fetchone()
            
            if row:
                try:
                    # ดึง running number จาก format RC6810/001
                    last_number = row[0].split('/')[-1]
                    running = int(last_number) + 1
                except (ValueError, IndexError) as e:
                    print(f"Warning: ไม่สามารถ parse ReceiveNumber '{row[0]}' ได้ เริ่มใหม่ที่ 001")
                    running = 1
            else:
                running = 1
            
            # สร้างเลขที่เอกสาร
            receive_number = f"{prefix}{running:03d}"
            
            return receive_number
            
        except Exception as e:
            raise Exception(f"Failed to generate receive number: {str(e)}")
            
    def create_receive_document(self, username: str, supplier_id: int = 30) -> Tuple[bool, str, Optional[int]]:
        """
        สร้างเอกสารรับสินค้า
        
        Args:
            username: ชื่อผู้ใช้ (จะแปลงเป็น UserId)
            supplier_id: รหัสซัพพลายเออร์ (default = 30)
            
        Returns:
            (success, message, receive_id)
        """
        try:
            # แปลง username เป็น UserId
            user_id = self.get_user_id_by_username(username)
            
            if not user_id:
                return False, f"ไม่พบผู้ใช้ '{username}' ในระบบ", None
            
            # สร้างเลขที่เอกสาร
            receive_number = self.get_next_receive_number()
            
            # สร้างเลขที่ Lot
            lot_number = self.get_next_lot_number()
            
            current_date = datetime.now()
            
            # Insert ข้อมูลลง Receive
            insert_query = """
                INSERT INTO Receive (
                    ReceiveNumber,
                    ReceiveDate,
                    InsertDate,
                    Active,
                    UserId,
                    PurchaseOrderId,
                    StatusId,
                    InvoiceNumber,
                    InvoiceDate,
                    SupplierId,
                    TaxInvoiceNumber,
                    IsOpenLot,
                    IsSendToHQ,
                    StoreId,
                    TransferId,
                    IsHQPO,
                    Lot
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            self.cursor.execute(
                insert_query,
                receive_number,      # ReceiveNumber
                current_date,        # ReceiveDate
                current_date,        # InsertDate
                1,                   # Active
                user_id,             # UserId (ใช้ UserId จากตาราง Users)
                0,                   # PurchaseOrderId
                1,                   # StatusId
                '-',                 # InvoiceNumber
                current_date,        # InvoiceDate
                supplier_id,         # SupplierId
                '-',                 # TaxInvoiceNumber
                0,                   # IsOpenLot
                0,                   # IsSendToHQ
                0,                   # StoreId
                0,                   # TransferId
                0,                   # IsHQPO
                lot_number           # Lot (U-01 051224 001)
            )
            
            self.connection.commit()
            
            # ดึง ReceiveId ที่สร้าง
            self.cursor.execute("SELECT @@IDENTITY AS ReceiveId")
            receive_id = self.cursor.fetchone()[0]
            
            return True, f"สร้างเอกสาร {receive_number} (Lot: {lot_number}) สำเร็จ", int(receive_id)
            
        except Exception as e:
            self.connection.rollback()
            return False, f"ไม่สามารถสร้างเอกสารได้: {str(e)}", None
    
    def get_item_unit_by_id(self, item_unit_id: int) -> Optional[Dict]:
        """
        ดึงข้อมูลหน่วยจาก ItemUnitId
        
        Args:
            item_unit_id: ItemUnitId
            
        Returns:
            Dict ของข้อมูลหน่วย หรือ None ถ้าไม่พบ
        """
        try:
            query = """
                SELECT ItemUnitId, ItemUnitName, Multiply, UnitType, Active, UnitCode
                FROM ItemUnit
                WHERE ItemUnitId = ? AND Active = 1
            """
            
            self.cursor.execute(query, item_unit_id)
            row = self.cursor.fetchone()
            
            if row:
                columns = [column[0] for column in self.cursor.description]
                return dict(zip(columns, row))
            
            return None
            
        except Exception as e:
            raise Exception(f"Failed to get item unit by id '{item_unit_id}': {str(e)}")
    
    def get_item_by_code(self, item_code: str, ignore_item_id: int = 0) -> Optional[Dict]:
        """
        ดึงข้อมูลสินค้าจาก ItemCode โดยเรียก stored procedure
        
        Args:
            item_code: รหัสสินค้า
            ignore_item_id: ItemId ที่ต้องการข้าม (default = 0)
            
        Returns:
            Dict ของข้อมูลสินค้า หรือ None ถ้าไม่พบ
        """
        try:
            # เรียก stored procedure
            self.cursor.execute(
                "EXEC GetItemByItemCode @ItemCode=?, @IgnoreItemId=?",
                item_code,
                ignore_item_id
            )
            
            # ดึงผลลัพธ์
            row = self.cursor.fetchone()
            
            if row:
                # แปลงเป็น dict
                columns = [column[0] for column in self.cursor.description]
                item_data = dict(zip(columns, row))
                
                # ข้อมูลที่ต้องการ:
                # - CategoryName (จาก ItemCategory)
                # - ItemCode (จาก Items)
                # - ItemDesc (ItemName จาก Items)
                # - RetailPrice (จาก Items)
                # - ItemUnitInStock (UnitsInStock จาก Items)
                # - ItemUnitId2 (จาก Items)
                # - ItemUnitId2Multiply (Multiply จาก Items)
                
                return item_data
            
            return None
            
        except Exception as e:
            raise Exception(f"Failed to get item by code '{item_code}': {str(e)}")
    
    def validate_import_data(self, data: List[Dict]) -> Tuple[bool, List[str], List[Dict]]:
        """
        ตรวจสอบข้อมูลก่อน import และดึงข้อมูลสินค้า
        
        Returns:
            (is_valid, errors, enriched_data)
            - is_valid: True ถ้าข้อมูลถูกต้องทั้งหมด
            - errors: รายการข้อผิดพลาด
            - enriched_data: ข้อมูลที่เติมข้อมูลสินค้าแล้ว
        """
        errors = []
        enriched_data = []
        
        try:
            if not data:
                errors.append("ไม่พบข้อมูลใน Excel file")
                return False, errors, []
            
            # ตรวจสอบคอลัมน์ที่จำเป็น
            required_columns = ['ItemCode', 'QtyReceived', 'UnitCost']
            
            first_row = data[0]
            for col in required_columns:
                if col not in first_row:
                    errors.append(f"ไม่พบคอลัมน์ '{col}' ในไฟล์")
            
            if errors:
                return False, errors, []
            
            # ตรวจสอบแต่ละแถว
            for idx, row in enumerate(data, 1):
                row_errors = []
                
                # ตรวจสอบ ItemCode
                item_code = str(row.get('ItemCode', '')).strip()
                if not item_code:
                    row_errors.append(f"แถวที่ {idx}: ไม่พบรหัสสินค้า")
                    errors.extend(row_errors)
                    continue
                
                # ดึงข้อมูลสินค้าจาก database
                try:
                    item_data = self.get_item_by_code(item_code, 0)
                    
                    if not item_data:
                        row_errors.append(f"แถวที่ {idx}: ไม่พบรหัสสินค้า '{item_code}' ในระบบ")
                    else:
                        # เติมข้อมูลสินค้าลงใน row
                        enriched_row = row.copy()
                        enriched_row['_item_data'] = item_data  # เก็บข้อมูลสินค้า
                        enriched_row['ItemId'] = item_data.get('ItemId')
                        enriched_row['ItemName'] = item_data.get('ItemName')
                        enriched_row['TaxId'] = item_data.get('TaxId')
                        enriched_row['TaxPercent'] = item_data.get('TaxPercent', 0)
                        enriched_row['CategoryName'] = item_data.get('CategoryName')
                        enriched_row['UnitName'] = item_data.get('UnitName')
                        
                        enriched_data.append(enriched_row)
                        
                except Exception as e:
                    row_errors.append(f"แถวที่ {idx}: เกิดข้อผิดพลาดในการตรวจสอบรหัสสินค้า - {str(e)}")
                
                # ตรวจสอบจำนวน
                try:
                    qty = row.get('QtyReceived')
                    if not qty or float(qty) <= 0:
                        row_errors.append(f"แถวที่ {idx}: จำนวนรับต้องมากกว่า 0")
                except (ValueError, TypeError):
                    row_errors.append(f"แถวที่ {idx}: จำนวนรับต้องเป็นตัวเลข")
                
                # ตรวจสอบราคา
                try:
                    cost = row.get('UnitCost')
                    if not cost or float(cost) < 0:
                        row_errors.append(f"แถวที่ {idx}: ราคาต่อหน่วยต้องไม่ติดลบ")
                except (ValueError, TypeError):
                    row_errors.append(f"แถวที่ {idx}: ราคาต่อหน่วยต้องเป็นตัวเลข")
                
                errors.extend(row_errors)
            
            is_valid = len(errors) == 0
            return is_valid, errors, enriched_data
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            return False, errors, []
    
    def import_receive_items(self, receive_id: int, data: List[Dict], 
                            user_id: str) -> Tuple[bool, str, Dict]:
        """นำเข้าข้อมูล ReceiveItem"""
        try:
            # เริ่ม transaction
            self.connection.autocommit = False
            
            success_count = 0
            error_count = 0
            error_details = []
            
            insert_query = """
                INSERT INTO ReceiveItem (
                    ReceiveId, ItemId, QtyReceived, UnitCost, AveCost, RetailPrice,
                    UnitsInStock, InsertDate, PurchaserOrderItemId, TotalCost,
                    Multiply, UnitName, TaxId, Tax, TaxPercent, InitCost,
                    TotalInitCost, DCPercent1, DCAmount1, DCPercent2, DCAmount2,
                    DCPercent3, DCAmount3, TotalDiscount, OrderQty, ExpireDate,
                    RemainQty, LotBalanceQty, ItemDesc, LineNum, Remarks,
                    ManufacturingDate
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            for idx, row in enumerate(data, 1):
                try:
                    # ข้ามแถวที่มี error
                    if row.get('_has_error', False):
                        error_count += 1
                        error_details.append(f"แถวที่ {idx}: ข้ามเนื่องจากไม่พบข้อมูลสินค้า")
                        continue
                    
                    # ฟังก์ชันช่วยแปลงค่าเป็น float อย่างปลอดภัย
                    def safe_float(value, default=0.0):
                        """แปลงค่าเป็น float อย่างปลอดภัย"""
                        if value is None or value == '' or value == 'None':
                            return default
                        try:
                            result = float(value)
                            # ตรวจสอบ NaN และ Infinity
                            if result != result or result == float('inf') or result == float('-inf'):
                                return default
                            return result
                        except (ValueError, TypeError):
                            return default
                    
                    def safe_int(value, default=0):
                        """แปลงค่าเป็น int อย่างปลอดภัย"""
                        if value is None or value == '' or value == 'None':
                            return default
                        try:
                            return int(float(value))
                        except (ValueError, TypeError):
                            return default
                    
                    # ดึงข้อมูลจาก row พร้อมตรวจสอบ
                    item_id = safe_int(row.get('ParentItemId'))
                    if item_id == 0:
                        item_id = safe_int(row.get('ItemId'))
                    qty_received = safe_float(row.get('QtyReceived', 0))
                    retail_price = safe_float(row.get('RetailPrice', 0))
                    item_unit_in_stock = safe_float(row.get('UnitsInStock', 0))
                    tax_percent = safe_float(row.get('TaxPercent', 0))
                    unit_cost = safe_float(row.get('UnitCost', 0))
                    avg_cost = safe_float(row.get('AvgCost', 0))
                    
                    # ตรวจสอบค่าที่จำเป็น
                    if item_id == 0:
                        error_count += 1
                        error_details.append(f"แถวที่ {idx}: ไม่พบ ItemId")
                        continue
                    
                    if qty_received <= 0:
                        error_count += 1
                        error_details.append(f"แถวที่ {idx}: จำนวนรับต้องมากกว่า 0")
                        continue
                    
                    # คำนวณส่วนลด
                    dc_percent1 = safe_float(row.get('DCPercent1', 0))
                    dc_percent2 = safe_float(row.get('DCPercent2', 0))
                    dc_percent3 = safe_float(row.get('DCPercent3', 0))
                    
                    # คำนวณยอดรวมและส่วนลด
                    subtotal = unit_cost * qty_received
                    dc_amount1 = subtotal * (dc_percent1 / 100) if dc_percent1 > 0 else 0
                    dc_amount2 = (subtotal - dc_amount1) * (dc_percent2 / 100) if dc_percent2 > 0 else 0
                    dc_amount3 = (subtotal - dc_amount1 - dc_amount2) * (dc_percent3 / 100) if dc_percent3 > 0 else 0
                    
                    total_discount = dc_amount1 + dc_amount2 + dc_amount3
                    total_cost = subtotal - total_discount
                    
                    # คำนวณภาษี
                    tax_amount = total_cost * (tax_percent / 100)
                    
                    # ข้อมูลอื่นๆ
                    multiply = safe_float(row.get('ItemUnitId2Multiply', 1), default=1.0)
                    unit_name = str(row.get('UnitName', ''))[:50]  # จำกัดความยาว
                    tax_id = safe_int(row.get('TaxId', 1), default=1)
                    item_desc = str(row.get('ItemDesc', ''))[:255]  # จำกัดความยาว
                    remarks = str(row.get('Remarks', ''))[:255]
                    
                    # จัดการวันที่
                    expire_date = row.get('ExpireDate')
                    manufacturing_date = row.get('ManufacturingDate')
                    
                    # ตรวจสอบว่าเป็น None หรือไม่
                    if expire_date == '' or expire_date == 'None':
                        expire_date = None
                    if manufacturing_date == '' or manufacturing_date == 'None':
                        manufacturing_date = None
                        
                    params = [
                        receive_id, item_id, qty_received*multiply, unit_cost/multiply, avg_cost, retail_price,
                        item_unit_in_stock, datetime.now(), 0, total_cost,
                        multiply, unit_name, tax_id, tax_amount, tax_percent, unit_cost/multiply,
                        total_cost, dc_percent1, dc_amount1, dc_percent2, dc_amount2,
                        dc_percent3, dc_amount3, total_discount, 0, expire_date,
                        0, None, item_desc, 0, remarks,
                        manufacturing_date
                    ]

                    print(f"=== Debug แถวที่ {idx} ===")
                    print(f"จำนวน parameters: {len(params)}")
                    print(f"Parameters:")
                    for i, p in enumerate(params, 1):
                        print(f"  {i}. {type(p).__name__}: {p}")
                    print("=" * 50)

                    self.cursor.execute(insert_query, *params)  # ใช้ *params แทน
                    # Insert
                    # self.cursor.execute(
                    #     insert_query,
                    #     receive_id,              # ReceiveId
                    #     item_id,                 # ItemId
                    #     qty_received,            # QtyReceived
                    #     unit_cost,               # UnitCost
                    #     avg_cost,                # AveCost
                    #     retail_price,            # RetailPrice
                    #     item_unit_in_stock,      # UnitsInStock
                    #     datetime.now(),          # InsertDate
                    #     0,                       # PurchaserOrderItemId
                    #     total_cost,              # TotalCost
                    #     multiply,                # Multiply
                    #     unit_name,               # UnitName
                    #     tax_id,                  # TaxId
                    #     tax_amount,              # Tax
                    #     tax_percent,             # TaxPercent
                    #     unit_cost,               # InitCost
                    #     total_cost,              # TotalInitCost
                    #     dc_percent1,             # DCPercent1
                    #     dc_amount1,              # DCAmount1
                    #     dc_percent2,             # DCPercent2
                    #     dc_amount2,              # DCAmount2
                    #     dc_percent3,             # DCPercent3
                    #     dc_amount3,              # DCAmount3
                    #     total_discount,          # TotalDiscount
                    #     0,                       # OrderQty
                    #     expire_date,             # ExpireDate
                    #     item_unit_in_stock,            # RemainQty
                    #     'NULL',                      # LotBalanceQty
                    #     item_desc,               # ItemDesc
                    #     idx,                     # LineNum
                    #     remarks,                 # Remarks
                    #     manufacturing_date       # ManufacturingDate
                    # )
                    
                    success_count += 1
                    
                except Exception as e:
                    error_count += 1
                    error_details.append(f"แถวที่ {idx}: {str(e)}")
            
            # Commit ถ้าสำเร็จ
            if error_count == 0 or success_count > 0:
                self.connection.commit()
                self.connection.autocommit = True
                
                result = {
                    'success_count': success_count,
                    'error_count': error_count,
                    'total': len(data)
                }
                
                if error_count == 0:
                    return True, f"นำเข้าข้อมูลสำเร็จ {success_count} รายการ", result
                else:
                    return True, f"นำเข้าข้อมูลสำเร็จ {success_count} รายการ, มีข้อผิดพลาด {error_count} รายการ", result
            else:
                self.connection.rollback()
                self.connection.autocommit = True
                
                result = {
                    'success_count': success_count,
                    'error_count': error_count,
                    'total': len(data),
                    'errors': error_details
                }
                
                return False, f"เกิดข้อผิดพลาด {error_count} รายการ", result
                
        except Exception as e:
            self.connection.rollback()
            self.connection.autocommit = True
            return False, f"Import failed: {str(e)}", {}
            
    def close_connection(self):
        """ปิดการเชื่อมต่อฐานข้อมูล"""
        try:
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
        except:
            pass