import json
import pyodbc
import base64

class DatabaseManager:
    def __init__(self):
        self.config = self.load_config()
    
    def load_config(self):
        """โหลด config.json"""
        try:
            with open(r'D:\_project\DocFlow-Manager\config.json', 'r', encoding='utf-8') as f:
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