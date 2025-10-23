import json
import pyodbc
import base64
import os
import sys

class DatabaseManager:
    def __init__(self):
        self.config = self.load_config()
    
    def load_config(self):
        """โหลด config.json"""
        try:
            # รองรับทั้งการรันจาก .py และ .exe
            if getattr(sys, 'frozen', False):
                # ถ้ารันจาก .exe
                base_path = os.path.dirname(sys.executable)
            else:
                # ถ้ารันจาก .py
                base_path = os.path.dirname(__file__)
            
            config_path = os.path.join(base_path, 'config.json')
            
            print(f"Loading config from: {config_path}")  # debug
            
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return {}
    
    def get_connection(self):
        """เชื่อมต่อฐานข้อมูล"""
        db_config = self.config.get('database', {})
        
        server = db_config.get('server')
        port = db_config.get('port')
        username = db_config.get('username')
        password = db_config.get('password')
        
        conn_str = f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server},{port};UID={username};PWD={password};TrustServerCertificate=yes;Encrypt=no;"
        
        return pyodbc.connect(conn_str)
    
    def find_sites_table(self):
        """ค้นหาตาราง sites ในทุก database"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # ดู databases ที่เข้าถึงได้
        cursor.execute("SELECT name FROM sys.databases WHERE HAS_DBACCESS(name) = 1")
        databases = [row[0] for row in cursor.fetchall()]
        
        print(f"Checking {len(databases)} databases for 'sites' table...")
        
        for db_name in databases:
            try:
                cursor.execute(f"USE [{db_name}]")
                cursor.execute("SELECT COUNT(*) FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'sites'")
                
                if cursor.fetchone()[0] > 0:
                    print(f"Found 'sites' table in database: {db_name}")
                    cursor.close()
                    conn.close()
                    return db_name
                    
            except Exception:
                continue
        
        cursor.close()
        conn.close()
        return None
    
    def get_company_data(self):
        """ดึงข้อมูลบริษัทจากตาราง sites"""
        try:
            # หา database ที่มีตาราง sites
            database_name = self.find_sites_table()
            if not database_name:
                return self.get_fallback_data()
            
            # เชื่อมต่อและดึงข้อมูล
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute(f"USE [{database_name}]")
            
            query = """
            SELECT companyname, 
                   SiteAddress + ' ' + ISNULL(Tambon, '') + ' ' + ISNULL(Amphur, '') + ' ' + ISNULL(Province, '') + ' ' + ISNULL(ZipCode, '') AS SiteAddress,
                   TaxId,
                   PhoneNumber, 
                   SitePicture
            FROM sites
            """
            
            cursor.execute(query)
            row = cursor.fetchone()
            
            if row:
                # ประมวลผลรูปภาพ
                site_picture = self.process_image(row[4]) if row[4] else ''
                
                result = {
                    'Companyname': row[0] or '',
                    'SiteAddress': (row[1] or '').strip(),
                    'TaxId': f"เลขประจำตัวผู้เสียภาษี: {row[2] or ''}",
                    'PhoneNumber': f"โทร: {row[3] or ''}",
                    'SitePicture': site_picture
                }
                
                cursor.close()
                conn.close()
                return result
            else:
                cursor.close()
                conn.close()
                return self.get_fallback_data()
                
        except Exception as e:
            print(f"Error: {e}")
            return self.get_fallback_data()
    
    def process_image(self, image_data):
        """ประมวลผลรูปภาพจากฐานข้อมูล"""
        if not image_data:
            return ''
        
        try:
            if isinstance(image_data, bytes):
                # แปลง binary เป็น base64
                base64_string = base64.b64encode(image_data).decode('utf-8')
                return f"data:image/jpeg;base64,{base64_string}"
            else:
                return str(image_data)
        except Exception:
            return ''
    
    def get_fallback_data(self):
        """ข้อมูลสำรอง"""
        return {
            'Companyname': 'ไม่พบข้อมูลบริษัท',
            'SiteAddress': '',
            'TaxId': '',
            'PhoneNumber': '',
            'SitePicture': ''
        }

class TableManager:
    """Class สำหรับจัดการตารางฐานข้อมูล"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def check_and_create_tables(self):
        """ตรวจสอบและสร้างตารางที่จำเป็น + อัพเดทคอลัมน์"""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            
            # ค้นหา database ที่ใช้งาน
            database_name = self.db_manager.find_sites_table()
            if database_name:
                cursor.execute(f"USE [{database_name}]")
            
            # รายการตารางที่ต้องตรวจสอบ
            tables_to_check = [
                'BillingDocument',
                'BillingDocumentItem',
                'BranchBillingDocument',
                'BranchBillingDocumentItem',
                'PurchaseBillingDocument',
                'PurchaseBillingDocumentItem'
            ]
            
            results = []
            
            for table_name in tables_to_check:
                # ตรวจสอบว่ามีตารางหรือไม่
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.TABLES 
                    WHERE TABLE_NAME = ?
                """, (table_name,))
                
                exists = cursor.fetchone()[0] > 0
                
                if exists:
                    results.append(f"✅ {table_name} - มีอยู่แล้ว")
                else:
                    # สร้างตาราง
                    if self.create_table(cursor, table_name):
                        results.append(f"✨ {table_name} - สร้างสำเร็จ")
                    else:
                        results.append(f"❌ {table_name} - สร้างไม่สำเร็จ")
            
            # ⭐ เพิ่มส่วนตรวจสอบและเพิ่มคอลัมน์ DiscountAmount และ NetTotal
            results.append("")  # บรรทัดว่าง
            results.append("🔍 ตรวจสอบคอลัมน์เพิ่มเติม...")
            
            # ตรวจสอบว่ามีตาราง BillingDocument หรือไม่
            cursor.execute("""
                SELECT COUNT(*) 
                FROM INFORMATION_SCHEMA.TABLES 
                WHERE TABLE_NAME = 'BillingDocument'
            """)
            
            if cursor.fetchone()[0] > 0:
                # ตรวจสอบคอลัมน์ DiscountAmount
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'BillingDocument' 
                    AND COLUMN_NAME = 'DiscountAmount'
                """)
                has_discount = cursor.fetchone()[0] > 0
                
                # ตรวจสอบคอลัมน์ NetTotal
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'BillingDocument' 
                    AND COLUMN_NAME = 'NetTotal'
                """)
                has_nettotal = cursor.fetchone()[0] > 0
                
                # เพิ่มคอลัมน์ถ้ายังไม่มี
                if not has_discount or not has_nettotal:
                    try:
                        if not has_discount and not has_nettotal:
                            # เพิ่มทั้ง 2 คอลัมน์พร้อมกัน
                            cursor.execute("""
                                ALTER TABLE [dbo].[BillingDocument]
                                ADD [DiscountAmount] DECIMAL(15, 2) NULL DEFAULT 0.00,
                                    [NetTotal] DECIMAL(15, 2) NULL
                            """)
                            results.append("✨ เพิ่มคอลัมน์ DiscountAmount และ NetTotal สำเร็จ")
                        elif not has_discount:
                            # เพิ่มเฉพาะ DiscountAmount
                            cursor.execute("""
                                ALTER TABLE [dbo].[BillingDocument]
                                ADD [DiscountAmount] DECIMAL(15, 2) NULL DEFAULT 0.00
                            """)
                            results.append("✨ เพิ่มคอลัมน์ DiscountAmount สำเร็จ")
                        elif not has_nettotal:
                            # เพิ่มเฉพาะ NetTotal
                            cursor.execute("""
                                ALTER TABLE [dbo].[BillingDocument]
                                ADD [NetTotal] DECIMAL(15, 2) NULL
                            """)
                            results.append("✨ เพิ่มคอลัมน์ NetTotal สำเร็จ")
                        
                        # อัพเดทข้อมูลเก่า
                        cursor.execute("""
                            UPDATE [dbo].[BillingDocument]
                            SET 
                                DiscountAmount = ISNULL(DiscountAmount, 0.00),
                                NetTotal = ISNULL(NetTotal, TotalAmount - ISNULL(DiscountAmount, 0))
                            WHERE DiscountAmount IS NULL OR NetTotal IS NULL
                        """)
                        results.append("📝 อัพเดทข้อมูลเดิมเรียบร้อย")
                        
                    except Exception as e:
                        results.append(f"❌ ไม่สามารถเพิ่มคอลัมน์: {str(e)}")
                else:
                    results.append("✅ คอลัมน์ DiscountAmount และ NetTotal - มีอยู่แล้ว")
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return {
                'success': True,
                'results': results
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
                
    def create_table(self, cursor, table_name):
        """สร้างตารางตามชื่อที่กำหนด"""
        try:
            if table_name == 'BillingDocument':
                cursor.execute("""
                    CREATE TABLE [dbo].[BillingDocument](
                        [BillingDocId] [int] IDENTITY(1,1) NOT NULL PRIMARY KEY,
                        [BillingDocNumber] [nvarchar](20) NULL,
                        [CustomerId] [int] NULL,
                        [CreateDate] [datetime] NULL,
                        [CreatedBy] [nvarchar](50) NULL,
                        [TotalAmount] [decimal](15, 2) NULL,
                        [TotalItems] [int] NULL,
                        [Status] [nvarchar](20) NULL,
                        [Notes] [nvarchar](500) NULL,
                        [CustomerName] [nvarchar](200) NULL,
                        [CustomerAddress] [nvarchar](500) NULL,
                        [CustomerPhone] [nvarchar](50) NULL,
                        [UserId] [nvarchar](50) NULL
                    )
                """)
                
            elif table_name == 'BillingDocumentItem':
                cursor.execute("""
                    CREATE TABLE [dbo].[BillingDocumentItem](
                        [ItemId] [int] IDENTITY(1,1) NOT NULL PRIMARY KEY,
                        [BillingDocId] [int] NULL,
                        [InvoiceNumber] [nvarchar](50) NULL,
                        [InvoiceAmount] [decimal](15, 2) NULL,
                        [ItemOrder] [int] NULL,
                        [InvoiceDate] [datetime] NULL,
                        [MaxDueDate] [int] NULL,
                        [DueDate] [datetime] NULL,
                        [Total] [decimal](15, 2) NULL,
                        [PaidAmount] [decimal](15, 2) NULL,
                        [UnpaidAmount] [decimal](15, 2) NULL
                    )
                """)
                
            elif table_name == 'BranchBillingDocument':
                cursor.execute("""
                    CREATE TABLE [dbo].[BranchBillingDocument](
                        [BranchBillingDocId] [int] IDENTITY(1,1) NOT NULL PRIMARY KEY,
                        [BillingDocNumber] [nvarchar](50) NULL,
                        [BranchName] [nvarchar](200) NULL,
                        [BranchAddress] [nvarchar](500) NULL,
                        [BranchPhone] [nvarchar](50) NULL,
                        [CreateDate] [datetime] NULL,
                        [CreatedBy] [nvarchar](100) NULL,
                        [TotalAmount] [decimal](18, 2) NULL,
                        [TotalItems] [int] NULL,
                        [Status] [nvarchar](20) NULL,
                        [Notes] [nvarchar](500) NULL,
                        [UpdatedDate] [datetime] NULL,
                        [UserId] [nvarchar](50) NULL
                    )
                """)
                
            elif table_name == 'BranchBillingDocumentItem':
                cursor.execute("""
                    CREATE TABLE [dbo].[BranchBillingDocumentItem](
                        [ItemId] [int] IDENTITY(1,1) NOT NULL PRIMARY KEY,
                        [BranchBillingDocId] [int] NULL,
                        [WithdrawalNumber] [nvarchar](50) NULL,
                        [WithdrawalDate] [date] NULL,
                        [TotalAmount] [decimal](18, 2) NULL,
                        [ItemOrder] [int] NULL
                    )
                """)
                
            elif table_name == 'PurchaseBillingDocument':
                cursor.execute("""
                    CREATE TABLE [dbo].[PurchaseBillingDocument](
                        [PurchaseBillingDocId] [int] IDENTITY(1,1) NOT NULL PRIMARY KEY,
                        [BillingDocNumber] [nvarchar](50) NULL,
                        [SupplierId] [int] NULL,
                        [SupplierName] [nvarchar](255) NULL,
                        [SupplierAddress] [nvarchar](500) NULL,
                        [SupplierPhone] [nvarchar](50) NULL,
                        [CreateDate] [datetime] NULL,
                        [CreatedBy] [nvarchar](100) NULL,
                        [TotalAmount] [decimal](18, 2) NULL,
                        [TotalItems] [int] NULL,
                        [Status] [nvarchar](20) NULL,
                        [Notes] [nvarchar](500) NULL,
                        [UpdatedDate] [datetime] NULL,
                        [UserId] [nvarchar](50) NULL
                    )
                """)
                
            elif table_name == 'PurchaseBillingDocumentItem':
                cursor.execute("""
                    CREATE TABLE [dbo].[PurchaseBillingDocumentItem](
                        [ItemId] [int] IDENTITY(1,1) NOT NULL PRIMARY KEY,
                        [PurchaseBillingDocId] [int] NULL,
                        [ReceiveNumber] [nvarchar](50) NULL,
                        [InvoiceNumber] [nvarchar](50) NULL,
                        [ReceiveDate] [datetime] NULL,
                        [CreditTerm] [int] NULL,
                        [DueDate] [datetime] NULL,
                        [Total] [decimal](18, 2) NULL,
                        [PaidAmount] [decimal](18, 2) NULL,
                        [UnpaidAmount] [decimal](18, 2) NULL,
                        [ReceiveAmount] [decimal](18, 2) NULL,
                        [ItemOrder] [int] NULL
                    )
                """)
            
            return True
            
        except Exception as e:
            print(f"Error creating table {table_name}: {e}")
            return False

# ฟังก์ชันง่าย ๆ สำหรับใช้งาน
def get_company_data():
    """ดึงข้อมูลบริษัท"""
    db = DatabaseManager()
    return db.get_company_data()

# ทดสอบ
if __name__ == "__main__":
    print("Testing database connection...")
    
    try:
        db = DatabaseManager()
        conn = db.get_connection()
        print("Connection successful!")
        conn.close()
        
        print("\nGetting company data...")
        data = get_company_data()
        
        for key, value in data.items():
            if key == 'SitePicture' and value:
                print(f"{key}: [Image data - {len(value)} chars]")
            else:
                print(f"{key}: {value}")
                
    except Exception as e:
        print(f"Error: {e}")