import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QScrollArea, QLineEdit, QSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap
from Manager.theme import Colors

class ProductCard(QFrame):
    def __init__(self, product: dict, on_add_callback=None):
        super().__init__()
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.product = product
        self.on_add = on_add_callback
        
        self.setObjectName("ProductCard")
        self.setStyleSheet(f"""
            QFrame#ProductCard {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 12px;
            }}
            QFrame#ProductCard:hover {{
                border-color: {Colors.CYAN};
                background-color: {Colors.BG_HOVER};
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        img_lbl = QLabel()
        img_lbl.setFixedHeight(90)
        img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        img_path = product.get("IconPath") or product.get("image", "")
        
        if img_path and os.path.exists(img_path):
            pix = QPixmap(img_path).scaled(80, 80, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            img_lbl.setPixmap(pix)
        else:
            img_lbl.setText("📦")
            img_lbl.setFont(QFont("Segoe UI Emoji", 36))
            
        name_lbl = QLabel(product.get("ProductName", "منتج"))
        name_lbl.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        name_lbl.setStyleSheet(f"color: {Colors.TEXT_PRIMARY};")
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setWordWrap(True)

        price = float(product.get("Price", 0.0))
        price_lbl = QLabel(f"{price:.2f} ر.س")
        price_lbl.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        price_lbl.setStyleSheet(f"color: {Colors.GREEN};")
        price_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        btn_add = QPushButton("➕ إضافة للسلة")
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.CYAN};
                color: #000000;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 6px;
            }}
            QPushButton:hover {{
                background-color: {Colors.CYAN}DD;
            }}
        """)
        if self.on_add:
            btn_add.clicked.connect(lambda: self.on_add(self.product))

        layout.addWidget(img_lbl)
        layout.addWidget(name_lbl)
        layout.addWidget(price_lbl)
        layout.addWidget(btn_add)

class POSWidget(QWidget):
    def __init__(self, db=None):
        super().__init__()
        self.db = db
        self.cart = []
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        left_layout = QVBoxLayout()
        left_layout.setSpacing(14)
        
        search_bar = QLineEdit()
        search_bar.setPlaceholderText("🔍 ابحث عن منتج بالاسم أو الباركود...")
        search_bar.setFixedHeight(42)
        search_bar.setStyleSheet(f"""
            QLineEdit {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 8px;
                padding: 0 14px;
                color: {Colors.TEXT_PRIMARY};
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {Colors.CYAN};
            }}
        """)
        search_bar.textChanged.connect(self.filter_products)
        left_layout.addWidget(search_bar)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; }")
        
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setSpacing(12)
        
        scroll.setWidget(self.grid_widget)
        left_layout.addWidget(scroll)
        
        main_layout.addLayout(left_layout, 2)
        
        cart_frame = QFrame()
        cart_frame.setFixedWidth(390)
        cart_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {Colors.BG_CARD};
                border: 1px solid {Colors.BORDER};
                border-radius: 14px;
            }}
        """)
        cart_layout = QVBoxLayout(cart_frame)
        cart_layout.setContentsMargins(16, 16, 16, 16)
        cart_layout.setSpacing(12)
        
        cart_title = QLabel("🛒 سلة المشتريات")
        cart_title.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        cart_title.setStyleSheet(f"color: {Colors.CYAN};")
        cart_layout.addWidget(cart_title)
        
        self.cart_table = QTableWidget(0, 4)
        self.cart_table.setHorizontalHeaderLabels(["المنتج", "الكمية", "السعر", "إلغاء"])
        self.cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.cart_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.cart_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.cart_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.cart_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.cart_table.setStyleSheet(f"""
            QTableWidget {{
                background-color: transparent;
                border: none;
                gridline-color: {Colors.BORDER};
                color: {Colors.TEXT_PRIMARY};
            }}
            QHeaderView::section {{
                background-color: {Colors.BG_CARD_LIGHT};
                color: {Colors.TEXT_MUTED};
                border: none;
                padding: 6px;
                font-weight: bold;
            }}
        """)
        cart_layout.addWidget(self.cart_table)
        
        summary_frame = QFrame()
        summary_frame.setStyleSheet(f"background-color: {Colors.BG_CARD_LIGHT}; border-radius: 8px; padding: 10px;")
        s_layout = QVBoxLayout(summary_frame)
        s_layout.setSpacing(6)
        
        self.lbl_subtotal = QLabel("المجموع: 0.00 ر.س")
        self.lbl_subtotal.setFont(QFont("Segoe UI", 11))
        self.lbl_subtotal.setStyleSheet(f"color: {Colors.TEXT_MUTED};")
        
        self.lbl_tax = QLabel("الضريبة (15%): 0.00 ر.س")
        self.lbl_tax.setFont(QFont("Segoe UI", 11))
        self.lbl_tax.setStyleSheet(f"color: {Colors.TEXT_MUTED};")

        self.lbl_total = QLabel("الإجمالي النهائي: 0.00 ر.س")
        self.lbl_total.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.lbl_total.setStyleSheet(f"color: {Colors.GREEN};")

        s_layout.addWidget(self.lbl_subtotal)
        s_layout.addWidget(self.lbl_tax)
        s_layout.addWidget(self.lbl_total)
        
        cart_layout.addWidget(summary_frame)
        
        btn_checkout = QPushButton("💳 إتمام عملية البيع")
        btn_checkout.setFixedHeight(48)
        btn_checkout.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        btn_checkout.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_checkout.setStyleSheet(f"""
            QPushButton {{
                background-color: {Colors.GREEN};
                color: #000000;
                border: none;
                border-radius: 8px;
            }}
            QPushButton:hover {{
                background-color: {Colors.GREEN}EE;
            }}
        """)
        btn_checkout.clicked.connect(self.checkout)
        
        cart_layout.addWidget(btn_checkout)
        
        main_layout.addWidget(cart_frame)
        
        self.load_products()

    def load_products(self):
        products = []
        if self.db and hasattr(self.db, 'get_connection'):
            try:
                conn = self.db.get_connection()
                if conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT ProductId, ProductName, Price, Category, IconPath FROM Products WHERE IsActive=1")
                    cols = [column[0] for column in cursor.description]
                    for r in cursor.fetchall():
                        products.append(dict(zip(cols, r)))
                    conn.close()
            except Exception as e:
                print("Error loading products:", e)
                
        if not products:
            products = [
                {"ProductId": 1, "ProductName": "مشروب الطاقة Red Bull", "Price": 12.00, "Category": "مشروبات"},
                {"ProductId": 2, "ProductName": "بطاطس Pringles كبير", "Price": 10.00, "Category": "وجبات خفيفة"},
                {"ProductId": 3, "ProductName": "قهوة إسبانيول باردة", "Price": 15.00, "Category": "مشروبات"},
                {"ProductId": 4, "ProductName": "ساعة لعب إضافية VIP", "Price": 25.00, "Category": "خدمات"},
                {"ProductId": 5, "ProductName": "وجبة برجر دجاج + كولا", "Price": 22.00, "Category": "وجبات"},
                {"ProductId": 6, "ProductName": "ماء نقي 500مل", "Price": 2.00, "Category": "مشروبات"},
            ]
            
        self.products_data = products
        self.display_products(products)

    def display_products(self, products):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
                
        col_count = 3
        for i, prod in enumerate(products):
            card = ProductCard(prod, on_add_callback=self.add_to_cart)
            row = i // col_count
            col = i % col_count
            self.grid_layout.addWidget(card, row, col)

    def filter_products(self, text):
        filtered = [p for p in self.products_data if text.lower() in p.get("ProductName", "").lower()]
        self.display_products(filtered)

    def add_to_cart(self, product):
        p_id = product.get("ProductId") or product.get("id") or 0
        for item in self.cart:
            if item["product"].get("ProductId") == p_id:
                item["qty"] += 1
                self.update_cart_ui()
                return
        self.cart.append({"product": product, "qty": 1})
        self.update_cart_ui()

    def update_cart_ui(self):
        self.cart_table.setRowCount(0)
        subtotal = 0.0
        
        for row, item in enumerate(self.cart):
            prod = item["product"]
            qty = item["qty"]
            price = float(prod.get("Price", 0.0))
            item_total = price * qty
            subtotal += item_total
            
            self.cart_table.insertRow(row)
            self.cart_table.setItem(row, 0, QTableWidgetItem(prod.get("ProductName", "")))
            self.cart_table.setItem(row, 1, QTableWidgetItem(str(qty)))
            self.cart_table.setItem(row, 2, QTableWidgetItem(f"{item_total:.2f}"))
            
            btn_del = QPushButton("✕")
            btn_del.setStyleSheet(f"color: {Colors.RED}; background: transparent; font-weight: bold; border: none;")
            btn_del.clicked.connect(lambda checked, r=row: self.remove_cart_item(r))
            self.cart_table.setCellWidget(row, 3, btn_del)
            
        tax = subtotal * 0.15
        total = subtotal + tax
        
        self.lbl_subtotal.setText(f"المجموع: {subtotal:.2f} ر.س")
        self.lbl_tax.setText(f"الضريبة (15%): {tax:.2f} ر.س")
        self.lbl_total.setText(f"الإجمالي النهائي: {total:.2f} ر.س")

    def remove_cart_item(self, row):
        if 0 <= row < len(self.cart):
            self.cart.pop(row)
            self.update_cart_ui()

    def checkout(self):
        if not self.cart:
            QMessageBox.warning(self, "السلة فارغة", "برجاء إضافة منتجات للسلة أولاً قبل إتمام الفاتورة.")
            return
        QMessageBox.information(self, "تمت العملية بنجاح", "تم تسجيل الفاتورة وطباعة الإيصال بنجاح!")
        self.cart.clear()
        self.update_cart_ui()