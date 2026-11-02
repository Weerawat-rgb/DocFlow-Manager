import pyodbc
import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Optional


class EditSaleBillDatabase:
    def __init__(self, config_file='config.json'):
        self.connection = None
        if getattr(sys, 'frozen', False):
            base_path = os.path.dirname(sys.executable)
        else:
            base_path = os.path.dirname(__file__)
        self.config_file = os.path.join(base_path, config_file)
        self.connect()

    def connect(self):
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            db = config['database']
            conn_str = (
                f"DRIVER={{{db['driver']}}};"
                f"SERVER={db['server']},{db['port']};"
                f"DATABASE={db['database']};"
                f"UID={db['username']};"
                f"PWD={db['password']};"
                f"TrustServerCertificate=yes;"
            )
            self.connection = pyodbc.connect(conn_str)
            print("✅ EditSaleBill: เชื่อมต่อฐานข้อมูลสำเร็จ")
        except Exception as e:
            print(f"❌ EditSaleBill: เชื่อมต่อไม่สำเร็จ: {e}")
            raise

    def test_connection(self) -> bool:
        try:
            self.connection.cursor().execute("SELECT 1")
            return True
        except Exception:
            return False

    # ──────────────────────────────────────────────────────────
    # ค้นหาบิลขาย  (ใช้ query ของผู้ใช้เป็นฐาน)
    # ──────────────────────────────────────────────────────────
    def search_sales(self, search_term: str = "") -> List[Dict]:
        """
        ค้นหาบิลขายจาก SaleNum หรือวันที่
        ดึง 1 แถวต่อ 1 Sale (DISTINCT ระดับ Sale)
        ตรงกับเงื่อนไข: active=1, isfinalize=1, TranTypeId=1
        """
        try:
            cursor = self.connection.cursor()
            conditions = [
                "s.active   = 1",
                "s.isfinalize = 1",
                "s.TranTypeId = 1",
            ]
            params = []

            if search_term:
                conditions.append("""(
                    CAST(s.SaleNum AS NVARCHAR)  LIKE ?
                    OR CONVERT(NVARCHAR, s.SaleDate, 105) LIKE ?
                    OR ISNULL(s.TmpCustomerName, '') LIKE ?
                )""")
                p = f"%{search_term}%"
                params.extend([p, p, p])

            where = " AND ".join(conditions)
            # ใช้ subquery เพื่อหลีกเลี่ยง "ORDER BY must appear in SELECT" ของ DISTINCT
            cursor.execute(f"""
                SELECT t.SaleId, t.SaleNum, t.SaleDate, t.CustomerName,
                       t.Total, t.SubTotal, t.ItemCount
                FROM (
                    SELECT DISTINCT
                        s.SaleId,
                        s.SaleNum,
                        s.SaleDate,
                        CONVERT(NVARCHAR(20), s.SaleDate, 120)      AS SaleDateFmt,
                        ISNULL(s.TmpCustomerName, 'ลูกค้าทั่วไป')  AS CustomerName,
                        ISNULL(s.Total,    0)                       AS Total,
                        ISNULL(s.SubTotal, 0)                       AS SubTotal,
                        (SELECT COUNT(*) FROM SaleItem si2
                         WHERE si2.SaleId = s.SaleId
                           AND si2.Active = 1)                      AS ItemCount
                    FROM sale s
                    INNER JOIN SaleItem    si ON si.SaleId  = s.SaleId
                    INNER JOIN SalePayment sp ON sp.SaleId  = s.SaleId
                    WHERE {where}
                ) t
                ORDER BY t.SaleDate DESC
            """, params)

            cols = [d[0] for d in cursor.description]
            results = [dict(zip(cols, row)) for row in cursor.fetchall()]
            cursor.close()
            return results
        except Exception as e:
            print(f"❌ ค้นหาบิลไม่สำเร็จ: {e}")
            return []

    # ──────────────────────────────────────────────────────────
    # ดึง SaleItems ทั้งหมดของบิล
    # ──────────────────────────────────────────────────────────
    def get_sale_items(self, sale_id: int) -> List[Dict]:
        """ดึง SaleItem ทั้งหมดของ SaleId ที่ระบุ"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT
                    si.SaleItemId,
                    si.SaleId,
                    si.ItemId,
                    ISNULL(si.ItemDesc, '')          AS ItemDesc,
                    ISNULL(si.Qty, 0)                AS Qty,
                    ISNULL(si.UnitPrice, 0)          AS UnitPrice,
                    ISNULL(si.ExtendedPrice, 0)      AS ExtendedPrice,
                    ISNULL(si.DiscountAmount, 0)     AS DiscountAmount,
                    ISNULL(si.DiscountPercent, 0)    AS DiscountPercent,
                    ISNULL(si.Remark, '')            AS Remark,
                    ISNULL(si.AmountDiscount, 0)     AS AmountDiscount
                FROM SaleItem si
                WHERE si.SaleId = ? AND si.Active = 1
                ORDER BY si.SaleItemId
            """, (sale_id,))
            cols = [d[0] for d in cursor.description]
            results = [dict(zip(cols, row)) for row in cursor.fetchall()]
            cursor.close()
            return results
        except Exception as e:
            print(f"❌ ดึง SaleItem ไม่สำเร็จ: {e}")
            return []

    def get_sale_header(self, sale_id: int) -> Optional[Dict]:
        """ดึงข้อมูล header ของ Sale"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT
                    s.SaleId,
                    s.SaleNum,
                    s.SaleDate,
                    ISNULL(s.TmpCustomerName, 'ลูกค้าทั่วไป') AS CustomerName,
                    ISNULL(s.Total,    0) AS Total,
                    ISNULL(s.SubTotal, 0) AS SubTotal,
                    ISNULL(s.Tax,      0) AS Tax
                FROM sale s
                WHERE s.SaleId = ?
            """, (sale_id,))
            row = cursor.fetchone()
            if not row:
                return None
            cols = [d[0] for d in cursor.description]
            result = dict(zip(cols, row))
            cursor.close()
            return result
        except Exception as e:
            print(f"❌ ดึง Sale header ไม่สำเร็จ: {e}")
            return None

    # ──────────────────────────────────────────────────────────
    # ค้นหาสินค้า + ดึงราคาตาม CustomerType
    # ──────────────────────────────────────────────────────────
    def search_items(self, keyword: str, customer_id: int = 0) -> List[Dict]:
        """ค้นหาสินค้าและดึงราคาตาม CustomerType ของลูกค้า"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT ItemId, ItemCode, ItemDesc, RetailPrice,
                       ISNULL(TaxId,        0)  AS TaxId,
                       ISNULL(CategoryId,   0)  AS CategoryId,
                       ISNULL(ItemTypeId,   0)  AS ItemTypeId,
                       ISNULL(EngItemDesc, '')  AS EngItemDesc
                FROM   items
                WHERE  Active = 1
                  AND  (ItemDesc     LIKE ?
                     OR ItemCode     LIKE ?
                     OR EngItemDesc  LIKE ?)
                ORDER BY ItemDesc
            """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
            rows = cursor.fetchall()
            cursor.close()

            results = []
            for r in rows:
                item_id, item_code, item_desc, retail_price, tax_id, \
                    category_id, item_type_id, eng_desc = r
                price = self.get_item_price(int(item_id), customer_id,
                                            float(retail_price or 0))
                results.append({
                    "ItemId":      int(item_id),
                    "ItemCode":    item_code    or "",
                    "ItemDesc":    item_desc    or "",
                    "UnitPrice":   price,
                    "TaxId":       int(tax_id),
                    "CategoryId":  int(category_id),
                    "ItemTypeId":  int(item_type_id),
                    "EngItemDesc": eng_desc     or "",
                })
            return results
        except Exception as e:
            print(f"❌ ค้นหาสินค้าไม่สำเร็จ: {e}")
            return []

    def get_item_price(self, item_id: int, customer_id: int,
                       fallback_price: float = 0.0) -> float:
        """
        ราคาสินค้าตาม CustomerType ของลูกค้า
        1) หา CustomerTypeId จาก customers
        2) หา itemprice.Price สำหรับ CustomerTypeId นั้น
        3) fallback → items.RetailPrice
        """
        try:
            cursor = self.connection.cursor()

            # 1) CustomerTypeId จาก customers
            customer_type_id = 0
            if customer_id > 0:
                cursor.execute(
                    "SELECT ISNULL(CustomerTypeId, 0) FROM customers WHERE CustomerId = ?",
                    (customer_id,)
                )
                ct = cursor.fetchone()
                if ct:
                    customer_type_id = int(ct[0])

            # 2) ราคาใน itemprice
            price = None
            if customer_type_id > 0:
                cursor.execute("""
                    SELECT TOP 1 Price
                    FROM   itemprice
                    WHERE  ItemId         = ?
                      AND  CustomerTypeId = ?
                      AND  (PriceExpireDate IS NULL OR PriceExpireDate >= GETDATE())
                    ORDER BY InsertDate DESC
                """, (item_id, customer_type_id))
                ip = cursor.fetchone()
                if ip and ip[0] is not None:
                    price = float(ip[0])

            # 3) fallback items.RetailPrice
            if price is None:
                if fallback_price > 0:
                    price = fallback_price
                else:
                    cursor.execute(
                        "SELECT ISNULL(RetailPrice, 0) FROM items WHERE ItemId = ?",
                        (item_id,)
                    )
                    rp = cursor.fetchone()
                    price = float(rp[0]) if rp else 0.0

            cursor.close()
            return price
        except Exception as e:
            print(f"❌ ดึงราคาสินค้าไม่สำเร็จ: {e}")
            return fallback_price

    # ──────────────────────────────────────────────────────────
    # อัพเดท SaleItem + คำนวณยอดรวมของ Sale ใหม่
    # ──────────────────────────────────────────────────────────
    def update_sale_items(self, sale_id: int,
                          items: List[Dict],
                          updated_by: str,
                          user_id: int = 0,
                          deleted_ids: List[int] = None,
                          new_items: List[Dict] = None,
                          edit_note: str = "") -> bool:
        """
        อัพเดท SaleItem แต่ละรายการ แล้วคำนวณ Sale.Total/SubTotal ใหม่
        items       = list of dict: { SaleItemId, ItemDesc, Qty, UnitPrice, DiscountAmount, Remark }
        user_id     = UserId (int) ของ user ที่ login อยู่ ใช้ใน CancelSaleItem
        deleted_ids = list of SaleItemId ที่ต้องการ cancel (INSERT CancelSaleItem → DELETE SaleItem)
        edit_note   = หมายเหตุการแก้ไข (บังคับกรอก) → บันทึกใน sale.Notes
        ExtendedPrice คำนวณอัตโนมัติ = Qty * UnitPrice - DiscountAmount
        """
        try:
            cursor = self.connection.cursor()
            affected_item_ids: set = set()   # รวม ItemId ที่ต้อง recal FIFO

            # ดึง TranTypeId จาก sale (ใช้ใน INSERT SaleItem ใหม่)
            cursor.execute(
                "SELECT ISNULL(TranTypeId, 1) FROM sale WHERE SaleId = ?",
                (sale_id,)
            )
            tr = cursor.fetchone()
            tran_id = int(tr[0]) if tr else 1

            # ── Cancel รายการที่ถูกลบ: INSERT CancelSaleItem → DELETE SaleItem ──
            if deleted_ids:
                for did in deleted_ids:
                    # 1) ดึงข้อมูลจาก SaleItem เพื่อ INSERT ลง CancelSaleItem
                    cursor.execute("""
                        SELECT
                            ISNULL(ItemId,           0)  AS ItemId,
                            ISNULL(ItemDesc,         '') AS ItemDesc,
                            ISNULL(SubItemDesc,      '') AS SubItemDesc,
                            ISNULL(SubItemDescEN,    '') AS SubItemDescEN,
                            ISNULL(EngItemDesc,      '') AS EngItemDesc,
                            ISNULL(Qty,              0)  AS Qty,
                            ISNULL(UnitPrice,        0)  AS UnitPrice,
                            ISNULL(ExtendedPrice,    0)  AS ExtendedPrice,
                            ISNULL(ExtendedPriceTax, 0)  AS ExtendedPriceTax,
                            ISNULL(InitPrice,        0)  AS InitPrice,
                            ISNULL(DiscountAmount,   0)  AS DiscountAmount
                        FROM SaleItem
                        WHERE SaleItemId = ? AND SaleId = ?
                    """, (did, sale_id))
                    row = cursor.fetchone()

                    if row:
                        (item_id, item_desc, sub_desc, sub_desc_en, eng_desc,
                         qty, unit_price, extended, extended_tax, init_price,
                         discount) = row
                        if item_id:
                            affected_item_ids.add(int(item_id))

                        # 2) INSERT ลง CancelSaleItem
                        cursor.execute("""
                            INSERT INTO CancelSaleItem (
                                PrintId, SaleId, SaleItemId, ItemId,
                                ItemDesc, SubItemDesc,
                                Qty, UnitPrice, ExtendedPrice,
                                CancelByUserId, TakingUserId,
                                OrderDate, CancelDate, ReasonId, Notes,
                                SaleTabId, TableId, TableName,
                                ServeBy, OrderTerminalId, CancelTerminalId,
                                BookNo, OrderNo, TakingStaffId,
                                IsMade, SerialNumberId,
                                EngItemDesc, SubItemDescEN,
                                ExtendedPriceTax, PrinterName,
                                KitchenItemId, StatementPrintTime,
                                InitPrice, DiscountAmountWTax,
                                CurrentUserId, CancelByStaffId
                            ) VALUES (
                                0, ?, ?, ?,
                                ?, ?,
                                ?, ?, ?,
                                ?, ?,
                                GETDATE(), GETDATE(), 1, '',
                                0, 0, '',
                                NULL, NULL, 0,
                                0, 0, 0,
                                1, 0,
                                ?, ?,
                                ?, '',
                                0, 0,
                                ?, 0,
                                ?, 0
                            )
                        """, (
                            sale_id, did, item_id,
                            item_desc, sub_desc,
                            qty, unit_price, extended,
                            user_id, user_id,
                            eng_desc, sub_desc_en,
                            extended_tax,
                            init_price,
                            user_id,     # CurrentUserId
                        ))

                    # 3) Soft-delete StoreLog ที่ผูกกับ SaleItemId นี้ (RefId=SaleItemId, LogTypeId=2)
                    cursor.execute("""
                        UPDATE StoreLog
                        SET    Active     = 0,
                               UpdateDate = GETDATE()
                        WHERE  RefId      = ?
                          AND  LogTypeId  = 2
                    """, (did,))

                    # 4) DELETE จาก SaleItem
                    cursor.execute(
                        "DELETE FROM SaleItem WHERE SaleItemId = ? AND SaleId = ?",
                        (did, sale_id)
                    )

            for item in items:
                qty         = float(item.get("Qty",            0))
                unit_price  = float(item.get("UnitPrice",      0))
                discount    = float(item.get("DiscountAmount", 0))
                extended    = round(qty * unit_price - discount, 2)
                item_desc   = item.get("ItemDesc",  "")
                remark      = item.get("Remark",    "")
                sale_item_id = item["SaleItemId"]

                # ดึง ItemId (product catalog ID) เพื่อใช้ใน SP recal
                cursor.execute(
                    "SELECT ISNULL(ItemId, 0) FROM SaleItem WHERE SaleItemId = ? AND SaleId = ?",
                    (sale_item_id, sale_id)
                )
                id_row = cursor.fetchone()
                if id_row and id_row[0]:
                    affected_item_ids.add(int(id_row[0]))

                # ปรับ Qty ใน StoreLog (RefId=SaleItemId, LogTypeId=2)
                cursor.execute("""
                    UPDATE StoreLog
                    SET    Qty        = ?,
                           UpdateDate = GETDATE()
                    WHERE  RefId      = ?
                      AND  LogTypeId  = 2
                      AND  Active     = 1
                """, (qty, sale_item_id))

                cursor.execute("""
                    UPDATE SaleItem SET
                        ItemDesc          = ?,
                        Qty               = ?,
                        UnitPrice         = ?,
                        ExtendedPrice     = ?,
                        ExtendedPriceTax  = ROUND(? * (1.0 + ISNULL(TaxPercent, 0) / 100.0), 2),
                        DiscountAmount    = ?,
                        AmountDiscount    = ?,
                        Remark            = ?,
                        UpdateDate        = GETDATE(),
                        UpdateUserId      = ?
                    WHERE SaleItemId = ? AND SaleId = ?
                """, (item_desc, qty, unit_price, extended,
                      extended,          # ExtendedPriceTax = ExtendedPrice × (1 + Tax%)
                      discount, discount,
                      remark, user_id,
                      sale_item_id, sale_id))

            # ── INSERT รายการสินค้าใหม่ ────────────────────────────────────
            if new_items:
                for ni in new_items:
                    ni_item_id      = int(ni["ItemId"])
                    ni_desc         = ni.get("ItemDesc",       "")
                    ni_qty          = float(ni.get("Qty",            1))
                    ni_price        = float(ni.get("UnitPrice",      0))
                    ni_disc         = float(ni.get("DiscountAmount", 0))
                    ni_ext          = round(ni_qty * ni_price - ni_disc, 2)
                    ni_remark       = ni.get("Remark",         "")
                    ni_tax_id       = int(ni.get("TaxId",       0))
                    ni_category_id  = int(ni.get("CategoryId", 0))
                    ni_item_type_id = int(ni.get("ItemTypeId", 0))
                    ni_eng_desc     = ni.get("EngItemDesc",    "")

                    cursor.execute("""
                        INSERT INTO SaleItem (
                            SaleId, ItemId, Qty, UnitPrice,
                            TaxId, TaxPercent,
                            ExtendedPrice, DiscountPercent, DiscountAmount, AmountDiscount,
                            Tax, ExtendedPriceTax,
                            ItemDesc, TranId,
                            PackageQty, AveCost, UnitsInStock, CustomerPackageQty,
                            CommissionPercent, CommisionAmount,
                            CategoryId, PrintedQty, RentalItemId, IsChecked,
                            Remark,
                            InsertDate, UserId, UpdateDate, UpdateUserId,
                            Active, IsTakeHome, UnitsInStore, IsSplitLineItem,
                            IsDiscount, SubItemDesc, SubItemDescEN,
                            ServiceChargePercent, ServiceChargeAmount, IsServiceCharge,
                            EngItemDesc,
                            PointEarned, PointRedeemed, QtyRedeemed, PointToRedeem,
                            Tax1, Tax2, Tax3, Tax2Percent, Tax3Percent,
                            InitPrice, MbrDisPercent, AmountDiscountMbr,
                            CCDisPercent, AmountDiscountCC,
                            IsSendedToHQ, PermitUserId, AmountDiscountWTax,
                            QtyPrivilege, QtyChecked, QtyWrongSale,
                            RefId, ItemTypeId, IsSelected, AppliedPromotionId,
                            AutoKey, OrgUnitPrice,
                            CustRefNum, RefNum, CheckedTime, IsCooked, CookedTime,
                            AmountDiscountCoupon, CouponDiscountPercent,
                            IsTrackCostWhenReceive, ParentItemId,
                            MultiBarcodeMultiply, DiscountTypeId,
                            ReturnFromSaleId, ReturnFromSaleItemId,
                            UseLoyaltyPoint, RoundDCAmtWTax,
                            IsBuffet, IsModifierPriceNotOverItemPrice,
                            KMQuickRemark, RateId, HRefType, BEBookingId,
                            IsPriceOverride, KitchenItemId,
                            SPDCAvg, SPDCInitAvg, SVCAvg, SVCInitAvg,
                            CNId, UnitCost, InitCost, IsPromotionByCRM,
                            RefSaleId, RefSaleItemId,
                            AmountDiscountCouponNoTax, OrderItemId,
                            IsAppliedCoupon, IsCookingCharge,
                            OrderItemStatus, OrderPickupPointId,
                            SizeId, IsDrinkExchange,
                            CardBalance, PromotionDiscountPercent, PromotionAmountDiscount,
                            MarkerId, GrossProfitPercent, DiscountReasonId
                        ) VALUES (
                            ?, ?, ?, ?,
                            ?, 0,
                            ?, 0, ?, ?,
                            0, ?,
                            ?, ?,
                            0, 0, 0, 0,
                            0, 0,
                            ?, 0, NULL, NULL,
                            ?,
                            GETDATE(), ?, GETDATE(), ?,
                            1, 0, 0, 0,
                            1, '', '',
                            0, 0, 0,
                            ?,
                            0, 0, 0, 0,
                            0, 0, 0, 0, 0,
                            ?, 0, 0,
                            0, 0,
                            NULL, 0, 0,
                            0, NULL, NULL,
                            0, ?, NULL, 0,
                            1, ?,
                            NULL, NULL, NULL, NULL, NULL,
                            0, 0,
                            0, 0,
                            1, 0,
                            0, 0,
                            0, 0,
                            NULL, 0,
                            '', 0, 0, 0,
                            0, 0,
                            NULL, NULL, NULL, NULL,
                            0, 0, 0, 0,
                            0, 0,
                            0, NULL,
                            0, 0,
                            NULL, 0,
                            0, 0,
                            NULL, 0, 0,
                            0, 0, 0
                        )
                    """, (
                        sale_id, ni_item_id, ni_qty, ni_price,   # SaleId, ItemId, Qty, UnitPrice
                        ni_tax_id,                                # TaxId  (TaxPercent=0)
                        ni_ext, ni_disc, ni_disc,                # ExtendedPrice, DiscountAmount, AmountDiscount
                        ni_ext,                                   # ExtendedPriceTax (TaxPercent=0 → same)
                        ni_desc, tran_id,                        # ItemDesc, TranId
                        ni_category_id,                          # CategoryId
                        ni_remark,                               # Remark
                        user_id, user_id,                        # UserId, UpdateUserId
                        ni_eng_desc,                             # EngItemDesc
                        ni_price,                                # InitPrice
                        ni_item_type_id,                         # ItemTypeId
                        ni_price,                                # OrgUnitPrice
                    ))

                    # ดึง SaleItemId ที่เพิ่งสร้าง
                    cursor.execute("SELECT @@IDENTITY")
                    new_sid = int(cursor.fetchone()[0])

                    affected_item_ids.add(ni_item_id)

                    # ── INSERT StoreLog ──────────────────────────────────
                    # หา ReceiveId + ReceiveItemId (FIFO: oldest active lot)
                    cursor.execute("""
                        SELECT TOP 1 ri.ReceiveId, ri.Id AS ReceiveItemId
                        FROM   ReceiveItem ri
                               INNER JOIN Receive r ON ri.ReceiveId = r.ReceiveId
                        WHERE  ri.ItemId   = ?
                          AND  r.Active    = 1
                          AND  r.StatusId  IN (2, 3)
                          AND  r.StoreId   = 0
                        ORDER  BY r.InsertDate ASC, ri.Id ASC
                    """, (ni_item_id,))
                    lot = cursor.fetchone()
                    ni_receive_id      = int(lot[0]) if lot else 0
                    ni_receive_item_id = int(lot[1]) if lot else 0

                    cursor.execute("""
                        INSERT INTO StoreLog (
                            ItemId, StoreId,
                            BeginQty, Qty, BalanceQty,
                            LogTypeId, RefId,
                            InsertDate, UpdateDate,
                            UserId, ReceiveId, ReceiveItemId,
                            Active
                        ) VALUES (
                            ?, 0,
                            0, ?, 0,
                            2, ?,
                            GETDATE(), GETDATE(),
                            ?, ?, ?,
                            1
                        )
                    """, (ni_item_id,
                          ni_qty, new_sid,
                          user_id, ni_receive_id, ni_receive_item_id))

            # คำนวณ SubTotal ใหม่จาก SaleItem ที่ยังใช้งาน
            cursor.execute("""
                UPDATE sale
                SET SubTotal = (
                        SELECT ISNULL(SUM(si.ExtendedPrice), 0)
                        FROM SaleItem si
                        WHERE si.SaleId = ? AND si.Active = 1
                    ),
                    Total = (
                        SELECT ISNULL(SUM(si.ExtendedPrice), 0)
                        FROM SaleItem si
                        WHERE si.SaleId = ? AND si.Active = 1
                    ),
                    UpdateDate = GETDATE()
                WHERE SaleId = ?
            """, (sale_id, sale_id, sale_id))

            # ── ดึง Total ใหม่หลัง UPDATE (ใช้ทั้ง SalePayment และ TransactionLog) ──
            cursor.execute(
                "SELECT ISNULL(Total, 0) FROM sale WHERE SaleId = ?",
                (sale_id,)
            )
            total_row  = cursor.fetchone()
            new_total  = float(total_row[0]) if total_row else 0.0

            # ── UPDATE SalePayment ──────────────────────────────────────────
            # ปรับยอดชำระให้ตรงกับ Total ใหม่ (Active = 1)
            cursor.execute("""
                UPDATE SalePayment
                SET Amount     = ?,
                    AmountNew  = ?,
                    UpdateDate = GETDATE()
                WHERE SaleId = ? AND Active = 1
            """, (new_total, new_total, sale_id))

            # ── Recalculate FIFO stock สำหรับทุก ItemId ที่ถูกกระทบ ──────────
            for aid in affected_item_ids:
                cursor.execute(
                    "EXEC sRecalStock_FIFO_BYITEMID @ItemId=?, @StoreId=0",
                    (aid,)
                )
                print(f"   ♻️  Recal FIFO ItemId={aid}")

            # ── INSERT TransactionLog ──────────────────────────────────────

            # PaymentTransaction reference — รูปแบบ #T0D{YYMMDDHHMMSS} (≤16 chars)
            now     = datetime.now()
            pay_ref = f"#T0D{now.strftime('%y%m%d%H%M%S')}"   # e.g. #T0D260315102800

            obj_text = json.dumps({
                "LogRefId":           sale_id,
                "PaymentTransaction": pay_ref,
                "PaymentGateway":     "POS",
                "PaymentMethod":      "แก้ไขบิล",
                "PaymentAmount":      new_total,
                "SaleItems":          ""
            }, ensure_ascii=False)

            cursor.execute("""
                INSERT INTO TransactionLog (
                    TransactionId, TransactTypeId, ObjectText,
                    TransactionStatus, Remark,
                    InsertDate, TransactionDate,
                    TerminalId, UserId, PaymentTransaction
                ) VALUES (
                    NULL, 'Edit', ?,
                    'Complete', '',
                    GETDATE(), GETDATE(),
                    0, ?, ?
                )
            """, (obj_text, user_id, pay_ref))

            # ── UPDATE sale.Notes (บันทึกหมายเหตุการแก้ไข + ผู้แก้ไข + วันเวลา) ──
            notes_text = (
                f"แก้ไขโดย {updated_by} "
                f"วันที่ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
                + (f": {edit_note}" if edit_note else "")
            )
            cursor.execute(
                "UPDATE sale SET Notes = ? WHERE SaleId = ?",
                (notes_text, sale_id)
            )

            self.connection.commit()
            cursor.close()
            print(f"✅ อัพเดท Sale #{sale_id} สำเร็จ | Notes: {notes_text}")
            return True
        except Exception as e:
            print(f"❌ อัพเดท SaleItem ไม่สำเร็จ: {e}")
            self.connection.rollback()
            return False
