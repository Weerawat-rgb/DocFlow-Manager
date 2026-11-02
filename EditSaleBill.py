import tkinter as tk
from tkinter import ttk, messagebox
from EditSaleBill_database import EditSaleBillDatabase
import theme

ACCENT  = theme.GREEN
ACCENT_H = theme.GREEN_H
COLOR_BG = theme.BG_PAGE


class EditSaleBillUI:
    """หน้าต่างค้นหาบิลขายและแก้ไขรายการสินค้า"""

    def __init__(self, parent, user_data):
        self.parent    = parent
        self.user_data = user_data
        self.window    = tk.Toplevel(parent)

        # state
        self.selected_sale  = None   # dict ข้อมูล Sale header
        self.sale_items     = []     # list of dict จาก DB
        self._item_rows        = []  # (sale_item_id, desc_var, qty_var, price_var, disc_var, remark_var, total_var, row_frame)
        self._deleted_item_ids  = []  # SaleItemId ที่จะ soft-delete
        self._pending_deleted   = []  # ข้อมูล item ที่ถูกลบ (ใช้แสดงใน step 3)
        self._pending_items     = []  # รายการที่แก้ไข (existing)
        self._pending_new_items = []  # รายการใหม่ที่จะ INSERT
        self._item_info         = {}  # temp_id → {"ItemId": int, ...} สำหรับ new items
        self._new_item_counter  = -1  # negative ID เป็น temp key

        self._build_window()

        try:
            self.db = EditSaleBillDatabase()
            if not self.db.test_connection():
                messagebox.showerror("ข้อผิดพลาด", "ไม่สามารถเชื่อมต่อฐานข้อมูลได้",
                    parent=self.window)
                self.window.destroy()
                return
        except Exception as e:
            messagebox.showerror("ข้อผิดพลาด", f"ข้อผิดพลาดฐานข้อมูล: {str(e)}",
                parent=self.window)
            self.window.destroy()
            return

        self.show_step1()

    # ──────────────────────────────────────────────────────────────
    # Window & header
    # ──────────────────────────────────────────────────────────────
    def _build_window(self):
        theme.setup_toplevel(self.window, "✏️ แก้ไขรายการบิลขาย", 1200, 820)
        theme.configure_styles()

        # Header bar
        self._hdr = tk.Frame(self.window, bg=theme.BG_DARK, height=theme.HDR_H)
        self._hdr.pack(fill="x")
        self._hdr.pack_propagate(False)

        self._accent_bar = tk.Frame(self.window, bg=ACCENT, height=3)
        self._accent_bar.pack(fill="x")

        self._build_header_content()

        # Content frame
        self.content_frame = tk.Frame(self.window, bg=COLOR_BG)
        self.content_frame.pack(fill="both", expand=True,
                                padx=theme.SIDE_PAD, pady=16)

    def _build_header_content(self):
        for w in self._hdr.winfo_children():
            w.destroy()

        inner = tk.Frame(self._hdr, bg=theme.BG_DARK)
        inner.pack(fill="both", expand=True,
                   padx=theme.SIDE_PAD, pady=0)

        left = tk.Frame(inner, bg=theme.BG_DARK)
        left.pack(side="left", fill="y", pady=10)
        tk.Frame(left, bg=ACCENT, width=4).pack(
            side="left", fill="y", pady=5, padx=(0, 12))
        titles = tk.Frame(left, bg=theme.BG_DARK)
        titles.pack(side="left")
        tk.Label(titles, text="✏️ แก้ไขรายการบิลขาย",
                 font=theme.F_H1, fg=theme.TEXT_WHITE,
                 bg=theme.BG_DARK).pack(anchor="w")
        tk.Label(titles, text="ค้นหาบิล → เลือก → แก้ไขรายการสินค้า → บันทึก",
                 font=theme.F_SMALL, fg=theme.TEXT_OFFWHITE,
                 bg=theme.BG_DARK).pack(anchor="w")

        right = tk.Frame(inner, bg=theme.BG_DARK)
        right.pack(side="right", fill="y", pady=12)
        chip = tk.Frame(right, bg=theme.BG_MEDIUM, padx=12, pady=5)
        chip.pack(side="left", anchor="center")
        tk.Label(chip,
                 text=f"  {self.user_data.get('username', '')}",
                 font=theme.F_SMALL, fg=theme.TEXT_OFFWHITE,
                 bg=theme.BG_MEDIUM).pack()
        close_btn = tk.Button(right, text="  ✕  ",
                              font=theme.F_SMALL_B,
                              bg=theme.RED, fg=theme.TEXT_WHITE,
                              border=0, padx=10, pady=6, cursor="hand2",
                              command=self.window.destroy)
        close_btn.pack(side="left", padx=(10, 0), anchor="center")
        theme._hover(close_btn, theme.RED_H, theme.RED)

    def _clear(self):
        for w in self.content_frame.winfo_children():
            w.destroy()

    def _step_bar(self, active: int):
        steps = ["1  ค้นหาบิล", "2  แก้ไขรายการ", "3  ยืนยัน"]
        frame = tk.Frame(self.content_frame, bg=COLOR_BG)
        frame.pack(fill="x", pady=(0, 14))
        for i, lbl in enumerate(steps, 1):
            is_active = (i == active)
            tk.Label(frame, text=lbl,
                     font=(theme.FF, 9, "bold" if is_active else "normal"),
                     bg=ACCENT if is_active else "#e5e7eb",
                     fg="white" if is_active else "#6b7280",
                     padx=16, pady=6).pack(side="left", padx=(0, 4))

    # ──────────────────────────────────────────────────────────────
    # Step 1 – ค้นหาบิล
    # ──────────────────────────────────────────────────────────────
    def show_step1(self):
        self._clear()
        self._step_bar(1)

        # Search bar
        sf = tk.Frame(self.content_frame, bg="white",
                      highlightbackground=theme.BORDER, highlightthickness=1)
        sf.pack(fill="x", pady=(0, 12))
        inner = tk.Frame(sf, bg="white", padx=16, pady=12)
        inner.pack(fill="x")

        tk.Label(inner, text="ค้นหาบิลขาย",
                 font=(theme.FF, 11, "bold"), fg="#374151",
                 bg="white").pack(anchor="w")
        tk.Label(inner, text="ค้นหาจากเลขที่บิล, วันที่ (dd-mm-yyyy) หรือชื่อลูกค้า",
                 font=(theme.FF, 9), fg="#6b7280", bg="white").pack(anchor="w")

        row = tk.Frame(inner, bg="white")
        row.pack(fill="x", pady=(8, 0))
        self._search_var = tk.StringVar()
        entry = tk.Entry(row, textvariable=self._search_var,
                         font=(theme.FF, 11), relief="flat", bd=0,
                         bg="#f3f4f6", fg="#1f2937")
        entry.pack(side="left", fill="x", expand=True,
                   ipady=8, ipadx=10, padx=(0, 10))
        entry.bind("<Return>", lambda e: self._do_search())
        entry.focus()

        tk.Button(row, text="🔍 ค้นหา",
                  font=(theme.FF, 10, "bold"),
                  bg=ACCENT, fg="white", border=0,
                  padx=18, pady=8, cursor="hand2",
                  command=self._do_search).pack(side="left")
        tk.Button(row, text="แสดงทั้งหมด",
                  font=(theme.FF, 10), bg="#6b7280",
                  fg="white", border=0, padx=13, pady=8, cursor="hand2",
                  command=lambda: self._do_search(all_mode=True)
                  ).pack(side="left", padx=(8, 0))

        # Results table
        tf = tk.Frame(self.content_frame, bg="white",
                      highlightbackground=theme.BORDER, highlightthickness=1)
        tf.pack(fill="both", expand=True)

        cols    = ("SaleId", "SaleNum", "SaleDate", "Customer", "Total", "Items")
        headers = {
            "SaleId":    "รหัส",
            "SaleNum":   "เลขที่บิล",
            "SaleDate":  "วันที่",
            "Customer":  "ลูกค้า",
            "Total":     "ยอดรวม",
            "Items":     "รายการ",
        }
        widths = {
            "SaleId": 70, "SaleNum": 130, "SaleDate": 160,
            "Customer": 280, "Total": 120, "Items": 80,
        }

        style = ttk.Style()
        style.configure("EditSale.Treeview",
                        font=(theme.FF, 10), rowheight=32,
                        background="white", fieldbackground="white")
        style.configure("EditSale.Treeview.Heading",
                        font=(theme.FF, 10, "bold"),
                        background="#f3f4f6", foreground="#374151")
        style.map("EditSale.Treeview",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", "white")])

        self._sale_tree = ttk.Treeview(tf, columns=cols,
                                       show="headings", style="EditSale.Treeview")
        for c in cols:
            self._sale_tree.heading(c, text=headers[c])
            self._sale_tree.column(c, width=widths[c], anchor="w")

        vsb = ttk.Scrollbar(tf, orient="vertical", command=self._sale_tree.yview)
        self._sale_tree.configure(yscrollcommand=vsb.set)
        self._sale_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self._sale_tree.bind("<Double-1>", lambda e: self._load_sale())

        # Buttons
        bf = tk.Frame(self.content_frame, bg=COLOR_BG)
        bf.pack(fill="x", pady=(10, 0))
        tk.Button(bf, text="แก้ไขบิลที่เลือก →",
                  font=(theme.FF, 11, "bold"),
                  bg=ACCENT, fg="white", border=0,
                  padx=25, pady=9, cursor="hand2",
                  command=self._load_sale).pack(side="right")

        self._do_search(all_mode=True)

    def _do_search(self, all_mode=False):
        term = "" if all_mode else self._search_var.get().strip()
        self._sale_tree.delete(*self._sale_tree.get_children())
        for r in self.db.search_sales(term):
            raw_date = r.get("SaleDate")
            if hasattr(raw_date, "strftime"):
                date_str = raw_date.strftime("%d/%m/%Y %H:%M")
            else:
                date_str = str(raw_date or "")[:16]
            self._sale_tree.insert("", "end", values=(
                r.get("SaleId",       ""),
                r.get("SaleNum",      ""),
                date_str,
                r.get("CustomerName", ""),
                f"{float(r.get('Total', 0)):,.2f}",
                r.get("ItemCount",    0),
            ))

    def _load_sale(self):
        sel = self._sale_tree.selection()
        if not sel:
            messagebox.showwarning("คำเตือน", "กรุณาเลือกบิลก่อน",
                parent=self.window)
            return
        vals = self._sale_tree.item(sel[0])["values"]
        sale_id = int(vals[0])
        header  = self.db.get_sale_header(sale_id)
        items   = self.db.get_sale_items(sale_id)
        if not header:
            messagebox.showerror("ข้อผิดพลาด", f"ไม่พบข้อมูลบิล #{sale_id}",
                parent=self.window)
            return
        if not items:
            messagebox.showwarning("คำเตือน", "บิลนี้ไม่มีรายการสินค้า",
                parent=self.window)
            return
        self.selected_sale      = header
        self.sale_items         = items
        self._deleted_item_ids  = []
        self._pending_deleted   = []
        self._pending_items     = []
        self._pending_new_items = []
        self._item_info         = {}
        self._new_item_counter  = -1
        self.show_step2()

    # ──────────────────────────────────────────────────────────────
    # Step 2 – แก้ไขรายการ
    # ──────────────────────────────────────────────────────────────
    # column spec: (col_id, header, width, anchor, stretch, editable)
    _ITEM_COLS = [
        ("num",   "#",           48,  "center", False, False),
        ("desc",  "ชื่อสินค้า",  320, "w",      True,  True),
        ("qty",   "จำนวน",        80, "e",      False, True),
        ("price", "ราคา/หน่วย",  110, "e",      False, True),
        ("disc",  "ส่วนลด",       95, "e",      False, True),
        ("total", "รวม",         110, "e",      False, False),
    ]

    def show_step2(self):
        self._clear()
        self._step_bar(2)
        h = self.selected_sale

        # ── Bill info bar ───────────────────────────────────────────
        info = tk.Frame(self.content_frame, bg="#fffbeb",
                        highlightbackground="#fcd34d", highlightthickness=1)
        info.pack(fill="x", pady=(0, 8))
        ii = tk.Frame(info, bg="#fffbeb", padx=18, pady=8)
        ii.pack(fill="x")
        raw = h.get("SaleDate")
        date_disp = raw.strftime("%d/%m/%Y %H:%M") if hasattr(raw, "strftime") \
                    else str(raw or "")[:16]
        tk.Label(ii,
                 text=f"บิลเลขที่  {h['SaleNum']}   วันที่ {date_disp}   "
                      f"ลูกค้า: {h['CustomerName']}",
                 font=(theme.FF, 10, "bold"), fg="#92400e",
                 bg="#fffbeb").pack(side="left")
        self._total_var = tk.StringVar()
        tk.Label(ii, textvariable=self._total_var,
                 font=(theme.FF, 11, "bold"), fg=ACCENT,
                 bg="#fffbeb").pack(side="right")

        # ── Treeview table ──────────────────────────────────────────
        panel = tk.Frame(self.content_frame, bg="white",
                         highlightbackground=theme.BORDER, highlightthickness=1)
        panel.pack(fill="both", expand=True, pady=(0, 4))

        st = ttk.Style()
        st.configure("Items2.Treeview",
                     font=(theme.FF, 10), rowheight=36,
                     background="white", fieldbackground="white")
        st.configure("Items2.Treeview.Heading",
                     font=(theme.FF, 10, "bold"),
                     background="#f3f4f6", foreground="#374151")
        st.map("Items2.Treeview",
               background=[("selected", "#dbeafe")],
               foreground=[("selected", "#1e40af")])

        col_ids = [c[0] for c in self._ITEM_COLS]
        self._tree = ttk.Treeview(panel, columns=col_ids, show="headings",
                                  style="Items2.Treeview", selectmode="browse")
        for cid, hdr, w, anc, stretch, _ in self._ITEM_COLS:
            self._tree.heading(cid, text=hdr)
            self._tree.column(cid, width=w, anchor=anc,
                              stretch=stretch, minwidth=w)

        vsb = ttk.Scrollbar(panel, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self._tree.pack(fill="both", expand=True, padx=1, pady=1)

        self._tree.tag_configure("even", background="#ffffff")
        self._tree.tag_configure("odd",  background="#f8fafc")

        # ── Populate rows ────────────────────────────────────────────
        # ถ้ากลับมาจาก step3 ให้ใช้ค่าที่แก้ไขไว้แล้ว (pending) แทน original
        self._tree_sids = {}
        self._item_rows = []
        pending_map = {it["SaleItemId"]: it for it in (self._pending_items or [])}
        for item in self.sale_items:
            sid = item["SaleItemId"]
            if sid not in self._deleted_item_ids:
                # ใช้ค่า pending ถ้ามี ไม่งั้นใช้ค่า original
                self._insert_tree_row(pending_map.get(sid, item))
        # ใส่รายการใหม่ที่เพิ่งเพิ่มเข้าไป (SaleItemId เป็น negative temp_id)
        for ni in (self._pending_new_items or []):
            if "SaleItemId" in ni:
                self._insert_tree_row(ni)
        self._refresh_total()

        # ── Bindings ─────────────────────────────────────────────────
        self._tree.bind("<Double-Button-1>", self._on_tree_dbl_click)
        self._tree.bind("<Delete>", lambda e: self._delete_selected_tree_row())

        tk.Label(self.content_frame,
                 text="💡 ดับเบิลคลิกที่ช่องเพื่อแก้ไข   |   เลือกแถวแล้วกด Delete หรือปุ่ม 🗑 เพื่อลบ",
                 font=(theme.FF, 9), fg="#6b7280",
                 bg=COLOR_BG).pack(anchor="w", pady=(2, 6))

        # ── Buttons ──────────────────────────────────────────────────
        bf = tk.Frame(self.content_frame, bg=COLOR_BG)
        bf.pack(fill="x")
        tk.Button(bf, text="← ค้นหาใหม่",
                  font=(theme.FF, 10), bg="#6b7280", fg="white",
                  border=0, padx=18, pady=9, cursor="hand2",
                  command=self.show_step1).pack(side="left")
        tk.Button(bf, text="🗑 ลบรายการที่เลือก",
                  font=(theme.FF, 10), bg=theme.RED, fg="white",
                  border=0, padx=18, pady=9, cursor="hand2",
                  command=self._delete_selected_tree_row).pack(side="left", padx=(8, 0))
        tk.Button(bf, text="ถัดไป → ยืนยัน",
                  font=(theme.FF, 11, "bold"),
                  bg=ACCENT, fg="white", border=0,
                  padx=25, pady=9, cursor="hand2",
                  command=self._validate_step2).pack(side="right")
        tk.Button(bf, text="➕ เพิ่มสินค้า",
                  font=(theme.FF, 10), bg="#0ea5e9", fg="white",
                  border=0, padx=18, pady=9, cursor="hand2",
                  command=self._open_add_item_dialog).pack(side="right", padx=(0, 8))

    # ──────────────────────────────────────────────────────────────
    # Treeview helpers (Step 2)
    # ──────────────────────────────────────────────────────────────
    def _insert_tree_row(self, item):
        """Insert one item into self._tree; return iid."""
        idx   = len(self._tree.get_children())
        sid   = item["SaleItemId"]
        qty   = float(item.get("Qty", 0))
        price = float(item.get("UnitPrice", 0))
        disc  = float(item.get("DiscountAmount", 0))
        total = round(qty * price - disc, 2)
        tag   = "even" if idx % 2 == 0 else "odd"
        iid   = self._tree.insert("", "end", tags=(tag,), values=(
            str(idx + 1),
            item.get("ItemDesc", ""),
            f"{qty:g}",
            f"{price:,.2f}",
            f"{disc:,.2f}",
            f"{total:,.2f}",
        ))
        self._tree_sids[iid] = sid
        return iid

    def _recalc_tree_row(self, iid):
        """Recalculate 'รวม' column from qty/price/disc."""
        try:
            qty   = float(self._tree.set(iid, "qty").replace(",", ""))
            price = float(self._tree.set(iid, "price").replace(",", ""))
            disc  = float(self._tree.set(iid, "disc").replace(",", "") or "0")
            self._tree.set(iid, "total",
                           f"{round(qty * price - disc, 2):,.2f}")
        except ValueError:
            pass

    def _on_tree_dbl_click(self, event):
        """Open a floating Entry widget over the double-clicked cell."""
        iid = self._tree.identify_row(event.y)
        col = self._tree.identify_column(event.x)
        if not iid or not col:
            return
        col_idx  = int(col.replace("#", "")) - 1
        if col_idx < 0 or col_idx >= len(self._ITEM_COLS):
            return
        col_id, _, _, _, _, editable = self._ITEM_COLS[col_idx]
        if not editable:
            return
        bbox = self._tree.bbox(iid, col)
        if not bbox:
            return
        x, y, w, h = bbox
        var = tk.StringVar(value=self._tree.set(iid, col_id))
        ent = tk.Entry(self._tree, textvariable=var,
                       font=(theme.FF, 10), relief="solid", bd=1,
                       bg="white", fg="#1f2937",
                       justify="right" if col_id in ("qty", "price", "disc") else "left")
        ent.place(x=x, y=y, width=w, height=h)
        ent.focus_set()
        ent.select_range(0, "end")

        def _commit(e=None):
            val = var.get().strip()
            if col_id in ("qty", "price", "disc"):
                try:
                    num = float(val.replace(",", ""))
                    val = f"{num:g}" if col_id == "qty" else f"{num:,.2f}"
                except ValueError:
                    ent.destroy()
                    return
            self._tree.set(iid, col_id, val)
            ent.destroy()
            self._recalc_tree_row(iid)
            self._refresh_total()

        ent.bind("<Return>",   _commit)
        ent.bind("<Tab>",      _commit)
        ent.bind("<Escape>",   lambda e: ent.destroy())
        ent.bind("<FocusOut>", _commit)

    def _delete_selected_tree_row(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning("คำเตือน", "กรุณาเลือกรายการที่ต้องการลบ",
                                   parent=self.window)
            return
        iid  = sel[0]
        desc = self._tree.set(iid, "desc")
        if not messagebox.askyesno("ยืนยันการลบ",
                                   f"ต้องการลบรายการ\n\"{desc}\" ใช่หรือไม่?",
                                   parent=self.window):
            return
        sid = self._tree_sids.pop(iid, 0)
        if sid > 0:
            self._deleted_item_ids.append(sid)
        elif sid < 0:
            self._item_info.pop(sid, None)
        self._tree.delete(iid)
        # Renumber + recolor
        for i, row_iid in enumerate(self._tree.get_children()):
            self._tree.set(row_iid, "num", str(i + 1))
            self._tree.item(row_iid, tags=("even" if i % 2 == 0 else "odd",))
        self._refresh_total()

    # ──────────────────────────────────────────────────────────────
    # Dialog ค้นหาและเพิ่มสินค้าใหม่
    # ──────────────────────────────────────────────────────────────
    def _open_add_item_dialog(self):
        dlg = tk.Toplevel(self.window)
        dlg.title("ค้นหาสินค้า")
        dlg.configure(bg="white")
        dlg.transient(self.window)
        dlg.grab_set()
        dlg.resizable(False, False)
        W, H = 720, 500
        dlg.update_idletasks()
        px = self.window.winfo_rootx() + (self.window.winfo_width()  - W) // 2
        py = self.window.winfo_rooty() + (self.window.winfo_height() - H) // 2
        dlg.geometry(f"{W}x{H}+{px}+{py}")

        # ── Search bar ─────────────────────────────────────────────
        top = tk.Frame(dlg, bg="white", padx=16, pady=12)
        top.pack(fill="x")
        tk.Label(top, text="ค้นหา:", font=(theme.FF, 10),
                 bg="white").pack(side="left", padx=(0, 6))
        search_var = tk.StringVar()
        search_ent = tk.Entry(top, textvariable=search_var,
                              font=(theme.FF, 11), relief="solid", bd=1, width=30)
        search_ent.pack(side="left", ipady=5, padx=(0, 8))
        search_ent.focus_set()

        results_data = []

        # ── Results treeview ───────────────────────────────────────
        lf = tk.Frame(dlg, bg="white", padx=16)
        lf.pack(fill="both", expand=True)
        cols = ("code", "desc", "price")
        tree = ttk.Treeview(lf, columns=cols, show="headings", height=16)
        tree.heading("code",  text="รหัสสินค้า")
        tree.heading("desc",  text="ชื่อสินค้า")
        tree.heading("price", text="ราคา")
        tree.column("code",  width=110, anchor="w")
        tree.column("desc",  width=440, anchor="w")
        tree.column("price", width=100, anchor="e")
        vsb = ttk.Scrollbar(lf, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        tree.pack(side="left", fill="both", expand=True)

        def do_search(*_):
            kw = search_var.get().strip()
            if not kw:
                return
            cid = self.selected_sale.get("CustomerId", 0)
            rows = self.db.search_items(kw, int(cid or 0))
            results_data.clear()
            tree.delete(*tree.get_children())
            for it in rows:
                results_data.append(it)
                tree.insert("", "end", values=(
                    it["ItemCode"],
                    it["ItemDesc"],
                    f"{it['UnitPrice']:,.2f}",
                ))

        search_ent.bind("<Return>", do_search)
        tk.Button(top, text="🔍 ค้นหา",
                  font=(theme.FF, 10), bg=ACCENT, fg="white",
                  border=0, padx=14, pady=5, cursor="hand2",
                  command=do_search).pack(side="left")

        def confirm(*_):
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("เลือกสินค้า",
                                       "กรุณาเลือกสินค้าก่อน",
                                       parent=dlg)
                return
            idx  = tree.index(sel[0])
            item = results_data[idx]
            dlg.destroy()
            self._add_new_item_row(item)

        tree.bind("<Double-1>", confirm)

        # ── Buttons ────────────────────────────────────────────────
        bf2 = tk.Frame(dlg, bg="white", padx=16, pady=10)
        bf2.pack(fill="x")
        tk.Button(bf2, text="ยกเลิก",
                  font=(theme.FF, 10), bg="#6b7280", fg="white",
                  border=0, padx=18, pady=7, cursor="hand2",
                  command=dlg.destroy).pack(side="left")
        tk.Button(bf2, text="✔ เพิ่มสินค้า",
                  font=(theme.FF, 10, "bold"), bg=ACCENT, fg="white",
                  border=0, padx=18, pady=7, cursor="hand2",
                  command=confirm).pack(side="right")

    def _add_new_item_row(self, item_data: dict):
        """เพิ่ม row ใหม่ลงตาราง Step 2 (new item ที่ยังไม่มี SaleItemId)"""
        temp_id = self._new_item_counter
        self._new_item_counter -= 1
        self._item_info[temp_id] = {
            "ItemId":      item_data["ItemId"],
            "TaxId":       item_data.get("TaxId",       0),
            "CategoryId":  item_data.get("CategoryId",  0),
            "ItemTypeId":  item_data.get("ItemTypeId",  0),
            "EngItemDesc": item_data.get("EngItemDesc", ""),
        }
        iid = self._insert_tree_row({
            "SaleItemId":     temp_id,
            "ItemDesc":       item_data["ItemDesc"],
            "Qty":            1.0,
            "UnitPrice":      item_data["UnitPrice"],
            "DiscountAmount": 0.0,
            "Remark":         "",
        })
        self._tree.selection_set(iid)
        self._tree.see(iid)
        self._refresh_total()

    def _refresh_total(self):
        total = 0.0
        for iid in self._tree.get_children():
            try:
                total += float(self._tree.set(iid, "total").replace(",", ""))
            except ValueError:
                pass
        self._total_var.set(f"ยอดรวมใหม่:  {total:,.2f} บาท")

    def _validate_step2(self):
        existing_items = []   # SaleItemId > 0  (UPDATE)
        new_items      = []   # SaleItemId < 0  (INSERT)

        for iid in self._tree.get_children():
            sid  = self._tree_sids.get(iid, 0)
            desc = self._tree.set(iid, "desc").strip()
            try:
                qty   = float(self._tree.set(iid, "qty").replace(",", ""))
                price = float(self._tree.set(iid, "price").replace(",", ""))
                disc  = float(self._tree.set(iid, "disc").replace(",", "") or "0")
            except ValueError:
                messagebox.showwarning("คำเตือน",
                                       f"รายการ '{desc}': ตัวเลขไม่ถูกต้อง",
                                       parent=self.window)
                return
            if qty <= 0:
                messagebox.showwarning("คำเตือน",
                                       f"รายการ '{desc}': จำนวนต้องมากกว่า 0",
                                       parent=self.window)
                return

            ext = round(qty * price - disc, 2)
            if sid > 0:
                existing_items.append({
                    "SaleItemId":     sid,
                    "ItemDesc":       desc,
                    "Qty":            qty,
                    "UnitPrice":      price,
                    "DiscountAmount": disc,
                    "ExtendedPrice":  ext,
                })
            else:
                info = self._item_info.get(sid, {})
                new_items.append({
                    "SaleItemId":     sid,          # temp_id (negative) สำหรับ restore ตอนกลับ step2
                    "ItemId":         info.get("ItemId",      0),
                    "TaxId":          info.get("TaxId",       0),
                    "CategoryId":     info.get("CategoryId",  0),
                    "ItemTypeId":     info.get("ItemTypeId",  0),
                    "EngItemDesc":    info.get("EngItemDesc", ""),
                    "ItemDesc":       desc,
                    "Qty":            qty,
                    "UnitPrice":      price,
                    "DiscountAmount": disc,
                    "ExtendedPrice":  ext,
                })

        if not existing_items and not new_items:
            messagebox.showwarning("คำเตือน",
                                   "ไม่สามารถบันทึกบิลที่ไม่มีรายการสินค้าเหลืออยู่เลย\n"
                                   "กรุณาเพิ่มรายการอย่างน้อย 1 รายการ",
                                   parent=self.window)
            return

        all_items = existing_items + new_items
        self._pending_items     = existing_items
        self._pending_new_items = new_items
        self._pending_deleted   = [it for it in self.sale_items
                                   if it["SaleItemId"] in self._deleted_item_ids]
        self._pending_total     = sum(i["ExtendedPrice"] for i in all_items)
        self.show_step3(all_items=all_items)

    # ──────────────────────────────────────────────────────────────
    # Step 3 – ยืนยัน
    # ──────────────────────────────────────────────────────────────
    def show_step3(self, all_items=None):
        self._clear()
        self._step_bar(3)
        h = self.selected_sale

        card = tk.Frame(self.content_frame, bg="white",
                        highlightbackground=theme.BORDER, highlightthickness=1)
        card.pack(fill="both", expand=True, pady=(0, 8))
        inner = tk.Frame(card, bg="white", padx=20, pady=16)
        inner.pack(fill="both", expand=True)

        tk.Label(inner,
                 text=f"สรุปการแก้ไขบิล  {h['SaleNum']}",
                 font=(theme.FF, 14, "bold"), fg="#1f2937",
                 bg="white").pack(anchor="w", pady=(0, 4))
        raw3 = h.get("SaleDate")
        date3 = raw3.strftime("%d/%m/%Y %H:%M") if hasattr(raw3, "strftime") \
                else str(raw3 or "")[:16]
        tk.Label(inner,
                 text=f"ลูกค้า: {h['CustomerName']}   วันที่: {date3}",
                 font=(theme.FF, 10), fg="#6b7280",
                 bg="white").pack(anchor="w", pady=(0, 10))

        # ── Treeview summary ────────────────────────────────────────
        tree_frame = tk.Frame(inner, bg="white")
        tree_frame.pack(fill="both", expand=True)

        st3 = ttk.Style()
        st3.configure("Summary3.Treeview",
                      font=(theme.FF, 10), rowheight=34,
                      background="white", fieldbackground="white")
        st3.configure("Summary3.Treeview.Heading",
                      font=(theme.FF, 10, "bold"),
                      background="#f3f4f6", foreground="#374151")
        st3.map("Summary3.Treeview",
                background=[("selected", "#f3f4f6")],
                foreground=[("selected", "#1f2937")])

        col_ids = [c[0] for c in self._ITEM_COLS]
        s3tree  = ttk.Treeview(tree_frame, columns=col_ids, show="headings",
                               style="Summary3.Treeview", selectmode="none",
                               height=9)
        for cid, hdr_t, w, anc, stretch, _ in self._ITEM_COLS:
            s3tree.heading(cid, text=hdr_t)
            s3tree.column(cid, width=w, anchor=anc, stretch=stretch, minwidth=w)

        vsb3 = ttk.Scrollbar(tree_frame, orient="vertical", command=s3tree.yview)
        s3tree.configure(yscrollcommand=vsb3.set)
        vsb3.pack(side="right", fill="y")
        s3tree.pack(fill="both", expand=True)

        s3tree.tag_configure("even",    background="#ffffff")
        s3tree.tag_configure("odd",     background="#f8fafc")
        s3tree.tag_configure("deleted", background="#fef2f2",
                             foreground="#dc2626")
        s3tree.tag_configure("new",     background="#f0fdf4",
                             foreground="#15803d")

        # Determine which descs are new
        new_descs = {ni.get("ItemDesc", "") for ni in self._pending_new_items}

        display_items = all_items if all_items is not None else self._pending_items
        for idx, item in enumerate(display_items):
            desc = item.get("ItemDesc", "") or "(ไม่ระบุ)"
            tag  = "new" if desc in new_descs else ("even" if idx % 2 == 0 else "odd")
            s3tree.insert("", "end", tags=(tag,), values=(
                str(idx + 1),
                desc,
                f"{float(item.get('Qty', 0)):,.2f}",
                f"{float(item.get('UnitPrice', 0)):,.2f}",
                f"{float(item.get('DiscountAmount', 0)):,.2f}",
                f"{float(item.get('ExtendedPrice', 0)):,.2f}",
                item.get("Remark", "") or "-",
            ))

        # Deleted items shown with red tag at bottom
        for it in self._pending_deleted:
            s3tree.insert("", "end", tags=("deleted",), values=(
                "🗑",
                f"[ลบ] {it.get('ItemDesc', '') or '(ไม่ระบุ)'}",
                f"{float(it.get('Qty', 0)):,.2f}",
                f"{float(it.get('UnitPrice', 0)):,.2f}",
                "", "", "",
            ))

        # ── Total bar ───────────────────────────────────────────────
        tot = tk.Frame(inner, bg=ACCENT, padx=16, pady=8)
        tot.pack(fill="x", pady=(8, 0))
        tk.Label(tot, text="ยอดรวมใหม่ทั้งหมด",
                 font=(theme.FF, 10), fg="white", bg=ACCENT).pack(side="left")
        tk.Label(tot, text=f"{self._pending_total:,.2f} บาท",
                 font=(theme.FF, 13, "bold"), fg="white",
                 bg=ACCENT).pack(side="right")

        # ── หมายเหตุการแก้ไข (บังคับกรอก) ─────────────────────────
        note_frame = tk.Frame(self.content_frame, bg="white",
                              highlightbackground="#fcd34d", highlightthickness=1)
        note_frame.pack(fill="x", pady=(8, 0))
        note_inner = tk.Frame(note_frame, bg="white", padx=16, pady=10)
        note_inner.pack(fill="x")

        tk.Label(note_inner,
                 text="หมายเหตุการแก้ไข  *  (บังคับกรอก)",
                 font=(theme.FF, 10, "bold"), fg="#92400e",
                 bg="white").pack(anchor="w")
        tk.Label(note_inner,
                 text="เหตุผลหรือรายละเอียดการแก้ไขบิลนี้",
                 font=(theme.FF, 9), fg="#6b7280",
                 bg="white").pack(anchor="w")

        self._edit_note_var = tk.StringVar()
        note_entry = tk.Entry(note_inner, textvariable=self._edit_note_var,
                              font=(theme.FF, 10), relief="solid", bd=1,
                              bg="#fffbeb", fg="#1f2937")
        note_entry.pack(fill="x", pady=(6, 0), ipady=7)
        note_entry.focus_set()

        # ── Buttons ─────────────────────────────────────────────────
        bf = tk.Frame(self.content_frame, bg=COLOR_BG)
        bf.pack(fill="x", pady=(8, 0))
        tk.Button(bf, text="← แก้ไขต่อ",
                  font=(theme.FF, 10), bg="#6b7280", fg="white",
                  border=0, padx=18, pady=9, cursor="hand2",
                  command=self.show_step2).pack(side="left")
        tk.Button(bf, text="✅ ยืนยันบันทึกการแก้ไข",
                  font=(theme.FF, 11, "bold"),
                  bg=ACCENT, fg="white", border=0,
                  padx=25, pady=9, cursor="hand2",
                  command=self._save).pack(side="right")

    def _save(self):
        # ── ตรวจสอบหมายเหตุการแก้ไข (บังคับกรอก) ──────────────────
        edit_note = self._edit_note_var.get().strip()
        if not edit_note:
            messagebox.showwarning(
                "กรุณากรอกหมายเหตุ",
                "กรุณากรอก 'หมายเหตุการแก้ไข' ก่อนบันทึก",
                parent=self.window,
            )
            return

        sale_id  = self.selected_sale["SaleId"]
        sale_num = self.selected_sale.get("SaleNum", str(sale_id))

        ok = self.db.update_sale_items(
            sale_id     = sale_id,
            items       = self._pending_items,
            updated_by  = self.user_data.get("username", ""),
            user_id     = self.user_data.get("user_id", 0),
            deleted_ids = self._deleted_item_ids,
            new_items   = self._pending_new_items,
            edit_note   = edit_note,
        )
        if ok:
            messagebox.showinfo(
                "บันทึกสำเร็จ",
                f"บันทึกการแก้ไขบิล {sale_num} เรียบร้อยแล้ว\n\n"
                f"หากต้องการพิมพ์ใบเสร็จ สามารถค้นหาบิลเลขที่ {sale_num}\n"
                f"ที่หน้าค้นหาบิลเก่า แล้วทำการพิมพ์ซ้ำได้เลย",
                parent=self.window,
            )
            if messagebox.askyesno(
                "แก้ไขบิลอื่น",
                "ต้องการค้นหาและแก้ไขบิลอื่นต่อหรือไม่?",
                parent=self.window,
            ):
                self.show_step1()
            else:
                self.window.destroy()
        else:
            messagebox.showerror(
                "ข้อผิดพลาด",
                "ไม่สามารถบันทึกข้อมูลได้ กรุณาลองใหม่อีกครั้ง",
                parent=self.window,
            )
