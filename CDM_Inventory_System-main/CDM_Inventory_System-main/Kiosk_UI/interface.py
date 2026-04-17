import sys
import os
from PyQt6.QtCore import QTimer, QDateTime, Qt
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
                             QStackedWidget, QFrame, QGridLayout, QScrollArea, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QLineEdit, QMessageBox, QComboBox, QSizePolicy)
from PyQt6.QtGui import QFont, QPixmap, QColor
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from PyQt6.QtGui import QPainter, QPdfWriter, QPageLayout, QPageSize

# Ensure the database folder is accessible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Updated Imports
try:
    from database.db_manager import get_all_items, add_request, get_available_asset_id
except ImportError:
    print("Error: database/db_manager.py not found. Please ensure your folder structure is correct.")
    
class BorrowersFormWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background-color: white; color: black;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(10)

        # --- HEADER ---
        header = QLabel("COLEGIO DE MONTALBAN\nPROPERTY AND SUPPLY OFFICE\n\nBORROWER'S FORM")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(header)
        layout.addSpacing(20)

        # --- TABLE ---
        self.table = QTableWidget(10, 6)
        self.table.setHorizontalHeaderLabels(["QTY.", "ITEM DESCRIPTION", "PURPOSE", "DATE/TIME\nBORROWED", "DATE/TIME\nRETURNED", "REMARKS"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget { gridline-color: black; border: 1.5px solid black; background-color: white; color: black; }
            QHeaderView::section { background-color: white; color: black; border: 1px solid black; font-weight: bold; }
        """)
        layout.addWidget(self.table)
        layout.addSpacing(30)

        # --- FOOTER SECTION (Names, Signatures, Note) ---
        footer_container = QVBoxLayout()
        footer_container.setSpacing(15)

        lbl_style = "font-weight: bold; font-size: 13px; color: black;"
        in_style = "background: transparent; border: none; border-bottom: 1.5px solid black; color: black; padding: 2px;"

        # Row 1: Borrower Name and Room No
        row1 = QHBoxLayout()
        self.borrower_name = QLineEdit()
        self.room_no = QLineEdit()
        
        row1.addWidget(QLabel("NAME OF BORROWER:", styleSheet=lbl_style))
        row1.addWidget(self.borrower_name, 3)
        self.borrower_name.setStyleSheet(in_style)
        
        row1.addSpacing(30)
        
        row1.addWidget(QLabel("ROOM NO:", styleSheet=lbl_style))
        row1.addWidget(self.room_no, 1)
        self.room_no.setStyleSheet(in_style)
        footer_container.addLayout(row1)

        # Row 2: Borrower Signature Line (Directly below Borrower Name)
        row2 = QHBoxLayout()
        self.borrower_sig = QLineEdit()
        row2.addWidget(QLabel("SIGNATURE:", styleSheet=lbl_style))
        row2.addWidget(self.borrower_sig, 1)
        self.borrower_sig.setStyleSheet(in_style)
        row2.addStretch(1) # Keeps the line from stretching to the right edge
        footer_container.addLayout(row2)

        # Row 3: Instructor Name
        row3 = QHBoxLayout()
        self.instructor_name = QLineEdit()
        row3.addWidget(QLabel("NAME OF INSTRUCTOR:", styleSheet=lbl_style))
        row3.addWidget(self.instructor_name, 1)
        self.instructor_name.setStyleSheet(in_style)
        row3.addStretch(1)
        footer_container.addLayout(row3)

        # Row 4: Instructor Signature Line (Directly below Instructor Name)
        row4 = QHBoxLayout()
        self.instructor_sig = QLineEdit()
        row4.addWidget(QLabel("SIGNATURE:", styleSheet=lbl_style))
        row4.addWidget(self.instructor_sig, 1)
        self.instructor_sig.setStyleSheet(in_style)
        row4.addStretch(1)
        footer_container.addLayout(row4)

        # Add the "PROPERTY & SUPPLY OFFICE" right-aligned text
        layout.addLayout(footer_container)
        layout.addSpacing(20)

        office_tag = QLabel("___________________________\nPROPERTY & SUPPLY OFFICE")
        office_tag.setAlignment(Qt.AlignmentFlag.AlignRight)
        office_tag.setStyleSheet("font-weight: bold; font-size: 13px;")
        layout.addWidget(office_tag)

        # The Bottom Note
        note = QLabel("\nNOTE: The instructor shall receive the items and need to sign the borrower's form. "
                      "Releasing and returning items within school days ONLY from 8:00 am to 5:00 pm.")
        note.setStyleSheet("font-size: 11px; font-style: italic; color: black;")
        note.setWordWrap(True)
        layout.addWidget(note)

        layout.addStretch()
class StudentKiosk(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CDM Kiosk")
        self.showMaximized()
        self.setStyleSheet("background-color: white; color: black;")
        
        self.cart = {} 
        self.cart_brands = {} 
        self.current_cat = "Supplies"
        self.print_buttons = [] 

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.pages = QStackedWidget()
        self.pages.addWidget(self.create_welcome_screen())      # Index 0
        self.pages.addWidget(self.create_category_screen())     # Index 1
        self.pages.addWidget(self.create_selection_screen())    # Index 2
        self.pages.addWidget(self.create_ris_form_page())       # Index 3
        self.pages.addWidget(self.create_waiting_screen())      # Index 4
        self.pages.addWidget(self.create_printing_sub_screen()) # Index 5
        self.pages.addWidget(self.create_borrow_form_page()) # This becomes Index 6

        self.main_layout.addWidget(self.pages)

    # --- SHARED UI COMPONENTS ---
    def create_top_bar(self, title_text, back_to_index):
        bar = QFrame()
        bar.setFixedHeight(100)
        bar.setStyleSheet("background-color: #1B4D2E;")
        layout = QHBoxLayout(bar)
        
        back_btn = QPushButton("BACK")
        back_btn.setFixedSize(120, 50)
        back_btn.setStyleSheet("color: white; border: 1px solid white; font-weight: bold; border-radius: 10px;")
        
        if title_text == "REQUISITION & ISSUANCE SLIP":
            back_btn.clicked.connect(self.handle_back_from_ris)
        else:
            back_btn.clicked.connect(lambda: self.pages.setCurrentIndex(back_to_index))
            
        title = QLabel(title_text)
        title.setFont(QFont("Arial", 26, QFont.Weight.Bold))
        title.setStyleSheet("color: white; border: none; background: transparent;")
        
        layout.addWidget(back_btn)
        layout.addStretch()
        layout.addWidget(title)
        layout.addStretch()
        layout.addSpacing(150)
        return bar

    def handle_back_from_ris(self):
        # Allow user to go back to selection screen to modify their cart
        self.pages.setCurrentIndex(2)

    # --- PAGE 0: WELCOME SCREEN ---
    def create_welcome_screen(self):
        page = QFrame()
        page.setStyleSheet("background-color: #1B4D2E;") 
        
        main_lay = QVBoxLayout(page)
        main_lay.setContentsMargins(60, 60, 60, 60)

        # BReal-time Clock
        top_hbox = QHBoxLayout()
        brand_vbox = QVBoxLayout()
        
        office_title = QLabel("COLEGIO DE MONTALBAN")
        office_title.setStyleSheet("color: white; font-size: 32px; font-weight: bold; background: transparent;")
        subtitle = QLabel("Official Kiosk of the Property and Supply Office")
        subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 20px; background: transparent;")
        
        brand_vbox.addWidget(office_title)
        brand_vbox.addWidget(subtitle)
        
        self.clock_label = QLabel()
        self.clock_label.setStyleSheet("color: white; font-size: 26px; font-weight: bold; background: transparent;")
        self.clock_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop)
        
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)
        self.update_clock()

        top_hbox.addLayout(brand_vbox)
        top_hbox.addStretch()
        top_hbox.addWidget(self.clock_label)
        main_lay.addLayout(top_hbox)

        # Large Center Action
        main_lay.addStretch(1)
        btn = QPushButton("TOUCH TO START")
        btn.setFixedSize(550, 250)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #E0E4D9; color: #1B4D2E; border-radius: 40px; 
                font-size: 48px; font-weight: bold; border: none;
            }
            QPushButton:hover { background-color: white; }
        """)
        btn.clicked.connect(lambda: self.pages.setCurrentIndex(1))
        main_lay.addWidget(btn, alignment=Qt.AlignmentFlag.AlignCenter)
        main_lay.addStretch(1)

        # Minimalist Help Button (Popup)
        help_btn = QPushButton("HELP / HOW TO USE")
        help_btn.setFixedSize(250, 50)
        help_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1); 
                color: white; border-radius: 25px; 
                font-size: 14px; font-weight: bold; border: 1px solid rgba(255, 255, 255, 0.3);
            }
            QPushButton:hover { background-color: rgba(255, 255, 255, 0.2); }
        """)
        help_btn.clicked.connect(self.show_help_popup)
        main_lay.addWidget(help_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        return page

    def update_clock(self):
        self.clock_label.setText(QDateTime.currentDateTime().toString("MMMM dd, yyyy \n hh:mm:ss AP"))

    def show_help_popup(self):
        help_text = (
            "<b>PROCESS TO GET REQUEST:</b><br><br>"
            "1. <b>SELECT CATEGORY:</b> Choose the type of item needed (Equipment, Printing, etc.)<br>"
            "2. <b>SELECT ITEMS:</b> Add multiple items to your cart.<br>"
            "3. <b>FILL RIS FORM:</b> Provide your student details and purpose.<br>"
            "4. <b>PRINT & COLLECT:</b> Collect your printed slip and proceed to the PSO counter."
        )
        msg = QMessageBox(self)
        msg.setWindowTitle("Kiosk Guide")
        msg.setText(help_text)
        msg.setStyleSheet("""
            QMessageBox { background-color: white; }
            QLabel { color: #1B4D2E; font-size: 16px; }
            QPushButton { 
                background-color: #1B4D2E; color: white; 
                padding: 8px 20px; border-radius: 5px; font-weight: bold; 
            }
        """)
        msg.exec()

    # --- PAGE 1: CATEGORY SELECTION (Left/Right Split) ---
    # --- PAGE 1: CATEGORY SELECTION (Side-by-Side & Centered Middle) ---
    def create_category_screen(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        # 1. Top Bar
        lay.addWidget(self.create_top_bar("CDM PROPERTY AND SUPPLY KIOSK", 0))
        
        # 2. TOP STRETCH (The "Spring" pushing from the top)
        lay.addStretch(1)

        # 3. Main Horizontal Container for the Columns
        columns_container = QWidget()
        h_lay = QHBoxLayout(columns_container)
        h_lay.setContentsMargins(50, 0, 50, 0) # No extra top/bottom margin needed
        h_lay.setSpacing(80) # Space between the two sections
        h_lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- LEFT COLUMN: BORROW ---
        borrow_col = QVBoxLayout()
        borrow_col.setSpacing(30)
        
        borrow_title = QLabel("BORROW")
        borrow_title.setFont(QFont("Arial", 38, QFont.Weight.Bold))
        borrow_title.setStyleSheet("color: #1B4D2E;")
        borrow_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        borrow_col.addWidget(borrow_title)
        
        borrow_items_lay = QHBoxLayout()
        borrow_items_lay.addWidget(self.make_category_item("Equipment\nBorrowing", "Equipment"))
        borrow_items_lay.addWidget(self.make_category_item("Sound System\nSetup", "Sound"))
        
        borrow_col.addLayout(borrow_items_lay)
        h_lay.addLayout(borrow_col)

        # --- VERTICAL SEPARATOR LINE ---
        line = QFrame()
        line.setFrameShape(QFrame.Shape.VLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        line.setStyleSheet("background-color: #DDD; min-height: 400px;") # Fixed height for the line
        h_lay.addWidget(line)

        # --- RIGHT COLUMN: REQUEST ---
        request_col = QVBoxLayout()
        request_col.setSpacing(30)
        
        request_title = QLabel("REQUEST")
        request_title.setFont(QFont("Arial", 38, QFont.Weight.Bold))
        request_title.setStyleSheet("color: #1B4D2E;")
        request_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        request_col.addWidget(request_title)
        
        request_items_lay = QHBoxLayout()
        request_items_lay.addWidget(self.make_category_item("Office/School\nSupplies", "Supplies"))
        request_items_lay.addWidget(self.make_category_item("Mass\nPrinting", "Printing"))
        
        request_col.addLayout(request_items_lay)
        h_lay.addLayout(request_col)

        # Add the container to the main layout
        lay.addWidget(columns_container)

        # 4. BOTTOM STRETCH (The "Spring" pushing from the bottom)
        lay.addStretch(1) 
        
        return page

    # Ensure your helper method uses PointingHandCursor for the kiosk feel
    def make_category_item(self, display, code):
        cont = QWidget()
        v = QVBoxLayout(cont)
        v.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        btn = QPushButton()
        btn.setFixedSize(240, 240) # Large visible circles
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet("""
            QPushButton {
                background-color: #4B8B3B; 
                border-radius: 120px; 
                border: 8px solid #E0E4D9;
            }
            QPushButton:hover {
                background-color: #5BA34A;
                border: 8px solid white;
            }
        """)
        btn.clicked.connect(lambda ch, c=code: self.show_filtered(c))
        
        lbl = QLabel(display)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color: black; font-weight: bold; font-size: 22px;")
        
        v.addWidget(btn)
        v.addWidget(lbl)
        return cont
    

    # --- PAGE 2: ITEM SELECTION & CART ---
    def create_selection_screen(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.create_top_bar("SELECT ITEMS", 1))
        
        main_content = QHBoxLayout()
        
        # Sidebar Cart
        self.cart_area = QFrame()
        self.cart_area.setFixedWidth(380)
        self.cart_area.setStyleSheet("background-color: #F4F6F1; border-right: 2px solid #DDD;")
        cart_lay = QVBoxLayout(self.cart_area)
        
        header = QHBoxLayout()
        t = QLabel("SELECTED ITEMS")
        t.setStyleSheet("color: black; font-weight: bold; font-size: 18px;")
        reset_btn = QPushButton("RESET")
        reset_btn.setStyleSheet("color: #A32A2A; font-weight: bold; border: none;")
        reset_btn.clicked.connect(self.reset_cart)
        
        header.addWidget(t)
        header.addStretch()
        header.addWidget(reset_btn)
        cart_lay.addLayout(header)
        
        self.cart_list = QVBoxLayout()
        self.cart_list.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_c = QScrollArea()
        sc_w = QWidget()
        sc_w.setLayout(self.cart_list)
        scroll_c.setWidget(sc_w)
        scroll_c.setWidgetResizable(True)
        scroll_c.setStyleSheet("background: transparent; border: none;")
        cart_lay.addWidget(scroll_c)
        
        checkout_btn = QPushButton("PROCEED TO CHECKOUT")
        checkout_btn.setStyleSheet("""
            QPushButton {
                background-color: #1B4D2E; color: white; 
                padding: 20px; font-weight: bold; border-radius: 10px;
            }
        """)
        checkout_btn.clicked.connect(self.proceed_to_ris_review)
        cart_lay.addWidget(checkout_btn)
        
        # Item Grid
        scroll_g = QScrollArea()
        scroll_g.setWidgetResizable(True)
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        scroll_g.setWidget(self.grid_widget)
        
        main_content.addWidget(self.cart_area)
        main_content.addWidget(scroll_g)
        lay.addLayout(main_content)
        return page

    def add_to_cart_grouped(self, item):
        name, brand = item[1], item[2]
        available_qty = item[3]
        current_qty = self.cart.get(name, 0)

        if current_qty >= available_qty:
            QMessageBox.warning(self, "Stock Limit", f"Cannot add more than {available_qty} {name}(s).")
            return

        self.cart[name] = current_qty + 1
        self.cart_brands[name] = brand
        self.update_cart_display()
        self.refresh_grid()

    def remove_from_cart(self, name):
        if name in self.cart:
            if self.cart[name] > 1:
                self.cart[name] -= 1
            else:
                del self.cart[name]
                if name in self.cart_brands: del self.cart_brands[name]
        self.update_cart_display()
        self.refresh_grid()

    def update_cart_display(self):
        """Refreshes BOTH sidebars (Selection screen and Printing screen)"""
        # List of all cart containers we need to update
        lists_to_update = []
        if hasattr(self, 'cart_list'): lists_to_update.append(self.cart_list)
        if hasattr(self, 'print_cart_list'): lists_to_update.append(self.print_cart_list)

        for cart_container in lists_to_update:
            # Clear current items
            for i in reversed(range(cart_container.count())): 
                w = cart_container.itemAt(i).widget()
                if w: w.setParent(None)
            
            # Add updated items
            for name, qty in self.cart.items():
                f = QFrame()
                f.setStyleSheet("background: white; border-bottom: 1px solid #EEE; border-radius: 5px;")
                l = QHBoxLayout(f)
                
                txt = QLabel(f"{name} x{qty}")
                txt.setStyleSheet("color: black; font-weight: bold; border: none;")
                
                rem = QPushButton("✕")
                rem.setFixedSize(35, 35)
                rem.setStyleSheet("color: red; border: none; font-weight: bold; font-size: 18px;")
                rem.clicked.connect(lambda ch, n=name: self.remove_from_cart(n))
                
                l.addWidget(txt)
                l.addStretch()
                l.addWidget(rem)
                cart_container.addWidget(f)
    def create_borrow_form_page(self):
        page = QWidget(); lay = QVBoxLayout(page); lay.setContentsMargins(0,0,0,0)
        lay.addWidget(self.create_top_bar("BORROWER'S FORM", 2))
        
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        self.borrow_form_widget = BorrowersFormWidget()
        scroll.setWidget(self.borrow_form_widget)
        
        submit_btn = QPushButton("SUBMIT BORROW REQUEST")
        submit_btn.setStyleSheet("background-color: #1B4D2E; color: white; padding: 15px; font-weight: bold;")
        submit_btn.clicked.connect(self.handle_final_submit) # Uses your existing submit logic
        
        lay.addWidget(scroll); lay.addWidget(submit_btn)
        return page

    # --- PAGE 5: MASS PRINTING (Unified Cart) ---
    # --- PAGE 5: MASS PRINTING (Fixed Reset & Centering) ---
    def create_printing_sub_screen(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.create_top_bar("MASS PRINTING SELECTION", 1))
        
        main_content = QHBoxLayout()

        # 1. SIDEBAR WITH RESET BUTTON
        self.print_cart_area = QFrame()
        self.print_cart_area.setFixedWidth(380)
        self.print_cart_area.setStyleSheet("background-color: #F4F6F1; border-right: 2px solid #DDD;")
        print_cart_lay = QVBoxLayout(self.print_cart_area)
        
        # Header with RESET
        h_layout = QHBoxLayout()
        cart_header = QLabel("SELECTED ITEMS")
        cart_header.setStyleSheet("color: black; font-weight: bold; font-size: 18px;")
        
        reset_btn = QPushButton("RESET")
        reset_btn.setStyleSheet("color: #A32A2A; font-weight: bold; border: none; background: transparent;")
        reset_btn.clicked.connect(self.reset_cart) # Connects to your existing reset_cart method
        
        h_layout.addWidget(cart_header)
        h_layout.addStretch()
        h_layout.addWidget(reset_btn)
        print_cart_lay.addLayout(h_layout)

        self.print_cart_list = QVBoxLayout()
        self.print_cart_list.setAlignment(Qt.AlignmentFlag.AlignTop)
        scroll_c = QScrollArea()
        sc_w = QWidget(); sc_w.setLayout(self.print_cart_list)
        scroll_c.setWidget(sc_w); scroll_c.setWidgetResizable(True)
        scroll_c.setStyleSheet("background: transparent; border: none;")
        print_cart_lay.addWidget(scroll_c)
        
        checkout_btn = QPushButton("PROCEED TO CHECKOUT")
        checkout_btn.setStyleSheet("background-color: #1B4D2E; color: white; padding: 20px; font-weight: bold; border-radius: 10px;")
        checkout_btn.clicked.connect(self.proceed_to_ris_review)
        print_cart_lay.addWidget(checkout_btn)

        # 2. CENTERED CONTENT (Form + Buttons)
        # We wrap the right side in a QVBoxLayout with a stretch to center it vertically
        right_side_container = QWidget()
        right_side_lay = QVBoxLayout(right_side_container)
        
        # This is the horizontal layout holding your Form and Buttons
        form_content = QHBoxLayout()
        form_content.setSpacing(40)
        form_content.setAlignment(Qt.AlignmentFlag.AlignCenter) # Center content horizontally

        # Left: Form Panel
        left = QFrame()
        left.setStyleSheet("background-color: #F4F6F1; border-radius: 20px; border: 1px solid #1B4D2E;")
        left.setFixedWidth(400)
        l_lay = QVBoxLayout(left)
        l_lay.setContentsMargins(25, 25, 25, 25)
        
        title = QLabel("PRINT DETAILS")
        title.setStyleSheet("color: black; font-weight: bold; font-size: 26px;")
        
        self.print_item_label = QLabel("Select Category ->")
        self.print_item_label.setStyleSheet("background-color: #E0E4D9; color: black; border-radius: 10px; padding: 15px; font-weight: bold;")
        
        # (Keep your existing QComboBox and QLineEdit setup here...)
        input_style = "background-color: white; color: black; padding: 12px; border: 1px solid #1B4D2E; border-radius: 8px;"
        self.paper_type_in = QComboBox(); self.paper_type_in.addItems(["Regular (70gsm)", "Premium (80gsm)", "Special Paper"]); self.paper_type_in.setStyleSheet(input_style)
        self.paper_size_in = QComboBox(); self.paper_size_in.addItems(["A4", "Long", "Short"]); self.paper_size_in.setStyleSheet(input_style)
        self.print_qty_in = QLineEdit(); self.print_qty_in.setPlaceholderText("Number of pages..."); self.print_qty_in.setStyleSheet(input_style)
        
        add_p = QPushButton("ADD TO CART")
        add_p.setStyleSheet("background-color: #1B4D2E; color: white; font-weight: bold; padding: 20px; border-radius: 30px;")
        add_p.clicked.connect(self.handle_print_proceed)
        
        l_lay.addWidget(title); l_lay.addWidget(self.print_item_label); l_lay.addWidget(QLabel("Paper Type"))
        l_lay.addWidget(self.paper_type_in); l_lay.addWidget(QLabel("Paper Size")); l_lay.addWidget(self.paper_size_in)
        l_lay.addWidget(QLabel("Quantity")); l_lay.addWidget(self.print_qty_in); l_lay.addStretch(); l_lay.addWidget(add_p)
        
        # Right: Category Buttons
        right_buttons_lay = QHBoxLayout()
        self.print_buttons = []
        cats = ["Instructional Materials", "Official Documents", "Examination Materials"]
        for n in cats:
            b = QPushButton(n.replace(" ", "\n"))
            b.setFixedSize(180, 200) # Slightly smaller to ensure they fit nicely
            b.setStyleSheet("background-color: #4B6344; color: white; font-weight: bold; border-radius: 15px;")
            b.clicked.connect(lambda ch, name=n, btn=b: (self.select_print_type(btn), self.print_item_label.setText(name)))
            self.print_buttons.append(b)
            right_buttons_lay.addWidget(b)
            
        form_content.addWidget(left)
        form_content.addLayout(right_buttons_lay)

        # Final assembly with vertical stretches to center the middle part
        right_side_lay.addStretch(1)
        right_side_lay.addLayout(form_content)
        right_side_lay.addStretch(1)

        main_content.addWidget(self.print_cart_area)
        main_content.addWidget(right_side_container, stretch=1)
        
        lay.addLayout(main_content)
        return page

    def select_print_type(self, clicked_button):
        for btn in self.print_buttons:
            btn.setStyleSheet("background-color: #4B6344; color: white; font-weight: bold; border-radius: 15px;")
        clicked_button.setStyleSheet("background-color: #1B4D2E; color: white; font-weight: bold; border: 4px solid #E0E4D9; border-radius: 15px;")

    def handle_print_proceed(self):
        t, q = self.print_item_label.text(), self.print_qty_in.text().strip()
        if t == "Select Category ->" or not q.isdigit():
            QMessageBox.warning(self, "Input Error", "Please select a category and quantity.")
            return
            
        key = f"PRINTING: {t} ({self.paper_size_in.currentText()})"
        self.cart[key] = self.cart.get(key, 0) + int(q)
        
        # We NO LONGER jump back to category automatically, 
        # so the user can see it in the sidebar and add more printing if needed.
        QMessageBox.information(self, "Success", f"Added {t} to your cart.")
        self.update_cart_display()

    # --- CHECKOUT LOGIC ---
    def proceed_to_ris_review(self):
        if not self.cart:
            QMessageBox.warning(self, "Empty Cart", "Please add items first.")
            return
        
        # Check what the user is doing
        if self.current_cat in ["Equipment", "Sound"]:
            # If it's for BORROWING
            self.fill_borrowers_form() # Fills the new table
            self.pages.setCurrentIndex(6) # Opens the new form
        else:
            # If it's for SUPPLIES/PRINTING
            self.fill_ris_form() # Fills the original RIS table
            self.pages.setCurrentIndex(3) # Opens the original RIS form

    def fill_borrowers_form(self):
        table = self.borrow_form_widget.table
        table.setRowCount(0)
        now = QDateTime.currentDateTime().toString("MM/dd/yyyy hh:mm AP")
        for name, qty in self.cart.items():
            row = table.rowCount(); table.insertRow(row)
            table.setItem(row, 0, QTableWidgetItem(str(qty)))
            table.setItem(row, 1, QTableWidgetItem(name))
            table.setItem(row, 3, QTableWidgetItem(now))
            for c in range(6): 
                if table.item(row, c): table.item(row, c).setForeground(QColor("black"))
                
    def handle_borrow_submit(self):
        # 1. Get the data from the new fields
        borrower = self.borrow_form_widget.borrower_name.text().strip()
        instructor = self.borrow_form_widget.instructor_name.text().strip()
        room = self.borrow_form_widget.room_no.text().strip()
        
        # 2. UPDATED VALIDATION: Removed 'purpose' from this check
        if not borrower or not instructor or not room:
            QMessageBox.warning(self, "Required Fields", 
                                "Please fill in Borrower Name, Instructor, and Room No.")
            return

        # 3. Use the first row's purpose from the table for the database record
        # (Assuming the student typed it into the table earlier)
        table = self.borrow_form_widget.table
        table_purpose = table.item(0, 2).text() if table.item(0, 2) else "Borrowing"

        # 4. Submit to database
        final_purpose = f"Room: {room} | Inst: {instructor} | Purpose: {table_purpose}"
        add_request(borrower, self.cart, final_purpose)
        
        # 5. Move to waiting screen
        self.pages.setCurrentIndex(4) 
        QTimer.singleShot(3000, self.reset_to_start)
    def proceed_to_ris(self):
        # Check if any item in the cart belongs to Borrowing categories
        is_borrowing = any(cat in self.cart_brands.values() or "Equipment" in str(name) or "Sound" in str(name) 
                           for name in self.cart.keys())

        if is_borrowing:
            self.fill_borrowers_form()
            self.pages.setCurrentIndex(6) # Switch to Borrower's Form Page
        else:
            self.fill_standard_ris_form()
            self.pages.setCurrentIndex(3) # Switch to standard RIS Form Page

    def fill_borrowers_form(self):
        # CHANGE THIS LINE: 
        # Instead of self.borrow_table, we point to the table inside the form widget
        table = self.borrow_form_widget.table 
        
        table.setRowCount(0)
        now = QDateTime.currentDateTime().toString("MM/dd/yyyy hh:mm AP")
        
        for name, qty in self.cart.items():
            row = table.rowCount()
            table.insertRow(row)
            
            # Use 'table' here too
            table.setItem(row, 0, QTableWidgetItem(str(qty)))
            table.setItem(row, 1, QTableWidgetItem(name))
            table.setItem(row, 3, QTableWidgetItem(now))
            
            # Ensure text is black for visibility
            for c in range(6):
                if table.item(row, c):
                    table.item(row, c).setForeground(QColor("black"))
        
    #bagoforborrowing
    class BorrowersFormWidget(QWidget):
        def __init__(self, parent=None):
            super().__init__(parent)
            self.setStyleSheet("background-color: white; color: black;")
            layout = QVBoxLayout(self)
            layout.setContentsMargins(40, 40, 40, 40)

            # --- HEADER SECTION ---
            header_vbox = QVBoxLayout()
            header_vbox.setSpacing(2)
            
            title1 = QLabel("COLEGIO DE MONTALBAN")
            title2 = QLabel("PROPERTY AND SUPPLY OFFICE")
            title3 = QLabel("\nBORROWER'S FORM")
            
            for lbl in [title1, title2]:
                lbl.setFont(QFont("Arial", 14, QFont.Weight.Bold))
                lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                header_vbox.addWidget(lbl)
                
            title3.setFont(QFont("Arial", 16, QFont.Weight.Bold))
            title3.setAlignment(Qt.AlignmentFlag.AlignCenter)
            header_vbox.addWidget(title3)
            
            layout.addLayout(header_vbox)
            layout.addSpacing(20)

            # --- TABLE SECTION (Matches columns in photo) ---
            self.table = QTableWidget(10, 6) # 10 rows for plenty of space
            self.table.setHorizontalHeaderLabels([
                "QTY.", "ITEM\nDESCRIPTION", "PURPOSE", 
                "DATE/TIME\nBORROWED", "DATE/TIME\nRETURNED", "REMARKS"
            ])
            self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
            self.table.verticalHeader().setVisible(False) # Hide row numbers to look like a form
            self.table.setStyleSheet("""
                QTableWidget { gridline-color: black; border: 1.5px solid black; background-color: white; color: black; }
                QHeaderView::section { 
                    background-color: white; color: black; 
                    font-weight: bold; border: 1.5px solid black;
                    padding: 5px;
                }
            """)
            # Allow editing Purpose and Remarks
            self.table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked | QTableWidget.EditTrigger.AnyKeyPressed)
            layout.addWidget(self.table)
            layout.addSpacing(30)

           # --- FOOTER DETAILS SECTION ---
            footer_container = QVBoxLayout()
            footer_container.setSpacing(15)

            # Row 1: Borrower Name and Room No
            row1 = QHBoxLayout()
            self.borrower_name = QLineEdit()
            self.room_no = QLineEdit()
            
            lbl_style = "font-weight: bold; font-size: 13px; color: black;"
            in_style = "background: transparent; border: none; border-bottom: 1.5px solid black; color: black; padding: 2px;"

            row1.addWidget(QLabel("NAME OF BORROWER:", styleSheet=lbl_style))
            row1.addWidget(self.borrower_name, 3) # The '3' makes this box longer
            self.borrower_name.setStyleSheet(in_style)
            
            row1.addSpacing(40) # Space between name and room
            
            row1.addWidget(QLabel("ROOM NO:", styleSheet=lbl_style))
            row1.addWidget(self.room_no, 1) # The '1' makes this box shorter
            self.room_no.setStyleSheet(in_style)
            footer_container.addLayout(row1)

            # Row 2: Borrower Signature
            row2 = QHBoxLayout()
            self.borrower_sig = QLineEdit()
            row2.addWidget(QLabel("SIGNATURE:", styleSheet=lbl_style))
            row2.addWidget(self.borrower_sig, 1)
            self.borrower_sig.setStyleSheet(in_style)
            row2.addStretch(1) # Pushes the signature line to the left half
            footer_container.addLayout(row2)

            # Row 3: Instructor Name
            row3 = QHBoxLayout()
            self.instructor_name = QLineEdit()
            row3.addWidget(QLabel("NAME OF INSTRUCTOR:", styleSheet=lbl_style))
            row3.addWidget(self.instructor_name, 1)
            self.instructor_name.setStyleSheet(in_style)
            row3.addStretch(1)
            footer_container.addLayout(row3)

            # Row 4: Instructor Signature
            row4 = QHBoxLayout()
            self.instructor_sig = QLineEdit()
            row4.addWidget(QLabel("SIGNATURE:", styleSheet=lbl_style))
            row4.addWidget(self.instructor_sig, 1)
            self.instructor_sig.setStyleSheet(in_style)
            row4.addStretch(1)
            footer_container.addLayout(row4)

            # Final Footer Labels
            footer_container.addSpacing(20)
            
            office_label = QLabel("___________________________\nPROPERTY & SUPPLY OFFICE")
            office_label.setAlignment(Qt.AlignmentFlag.AlignRight)
            office_label.setStyleSheet("font-weight: bold; font-size: 13px; color: black;")
            footer_container.addWidget(office_label)

            note = QLabel("\nNOTE: The instructor shall receive the items and need to sign the borrower's form. "
                        "Releasing and returning items with in school days ONLY from 8:00 am to 5:00 pm.")
            note.setStyleSheet("font-size: 11px; font-style: italic; color: black;")
            note.setWordWrap(True)
            footer_container.addWidget(note)

            layout.addLayout(footer_container)
            layout.addStretch()

    # --- FORM & GRID REFRESH ---
    def create_ris_form_page(self):
        page = QWidget()
        page.setStyleSheet("background-color: white; color: black;")
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.create_top_bar("REQUISITION & ISSUANCE SLIP", 2))
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        container = QWidget()
        container.setStyleSheet("background-color: white;")
        c_lay = QVBoxLayout(container)
        c_lay.setContentsMargins(20, 10, 20, 20)
        
        # Printable RIS form container (excludes submit button)
        self.ris_form_widget = QWidget()
        self.ris_form_widget.setStyleSheet("background-color: white;")
        self.ris_form_widget.setObjectName("ris_form_widget")
        self.ris_form_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        form_lay = QVBoxLayout(self.ris_form_widget)
        form_lay.setContentsMargins(30, 30, 30, 30)
        
        title_label = QLabel("REQUISITION & ISSUANCE SLIP")
        title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title_label.setStyleSheet("color: black; padding-bottom: 10px;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form_lay.addWidget(title_label)
        
        lbl_s = "background-color: #1B4D2E; color: white; padding: 4px; font-weight: bold; font-size: 11px;"
        in_s = "background-color: #E0E4D9; color: black; border-radius: 12px; padding: 5px; border: 1px solid #1B4D2E;"
        
        # Top section with 2 rows of 3 fields each
        top_grid = QGridLayout()
        top_grid.setSpacing(10)
        self.ris_div = QLineEdit("CDM"); self.ris_resp_center = QLineEdit(); self.ris_office = QLineEdit()
        self.ris_code = QLineEdit(); self.ris_date = QLineEdit("2026-04-09"); self.ris_no = QLineEdit()
        
        fields = [("DIVISION:", self.ris_div, 0, 0), ("RESPONSIBLE CENTER:", self.ris_resp_center, 0, 2), 
                  ("DATE:", self.ris_date, 0, 4), ("OFFICE:", self.ris_office, 1, 0), 
                  ("CODE/CL # :", self.ris_code, 1, 2), ("RIS NO:", self.ris_no, 1, 4)]
        
        for txt, w, r, c in fields:
            l = QLabel(txt); l.setStyleSheet(lbl_s); w.setStyleSheet(in_s)
            top_grid.addWidget(l, r, c); top_grid.addWidget(w, r, c+1)
            
        form_lay.addLayout(top_grid)
        form_lay.addSpacing(15)
        
        # Table section
        self.ris_table = QTableWidget(0, 6)
        self.ris_table.setHorizontalHeaderLabels(["STOCK NO", "UNIT", "DESCRIPTION", "REQ QTY", "ISS QTY", "REMARKS"])
        self.ris_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ris_table.setStyleSheet("QHeaderView::section { background-color: #1B4D2E; color: white; border: 1px solid white; }")
        self.ris_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        
        table_container = QWidget()
        table_container_layout = QVBoxLayout(table_container)
        table_container_layout.setContentsMargins(0, 0, 0, 0)
        table_container_layout.addWidget(self.ris_table)
        
        form_lay.addWidget(table_container)
        form_lay.addSpacing(15)
        
        # Purpose section
        purpose_layout = QHBoxLayout()
        purpose_label = QLabel("PURPOSE:")
        purpose_label.setStyleSheet(lbl_s)
        self.purpose_in = QLineEdit()
        self.purpose_in.setStyleSheet(in_s)
        purpose_layout.addWidget(purpose_label)
        purpose_layout.addWidget(self.purpose_in)
        form_lay.addLayout(purpose_layout)
        form_lay.addSpacing(15)
        
        # Signature section - 4 columns, 3 rows
        self.sig_widgets = {}
        sections = ["REQUESTED BY:", "APPROVED BY:", "ISSUED BY:", "RECEIVED BY:"]
        row_labels = ["NAME:", "DATE:", "SIGNATURE:"]
        
        bot_grid = QGridLayout()
        bot_grid.setSpacing(10)
        
        # Header row for sections
        for i, text in enumerate(sections):
            lbl = QLabel(text); lbl.setStyleSheet(lbl_s); lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            bot_grid.addWidget(lbl, 0, i+1)
            
        # Data rows
        for r, txt in enumerate(row_labels):
            label = QLabel(txt)
            label.setStyleSheet("color: black; font-weight: bold;")
            bot_grid.addWidget(label, r+1, 0)
            
            for c in range(4):
                w = QLineEdit()
                w.setStyleSheet(in_s)
                bot_grid.addWidget(w, r+1, c+1)
                self.sig_widgets[f"{txt}_{sections[c]}"] = w
        
        form_lay.addLayout(bot_grid)
        form_lay.addStretch()
        
        next_b = QPushButton("SUBMIT REQUEST  ➡")
        next_b.setStyleSheet("background-color: #1B4D2E; color: white; font-weight: bold; padding: 15px; border-radius: 25px;")
        next_b.clicked.connect(self.handle_final_submit)
        
        c_lay.addWidget(self.ris_form_widget)
        c_lay.addSpacing(20); c_lay.addWidget(next_b)
        
        scroll.setWidget(container); layout.addWidget(scroll)
        return page

    def refresh_grid(self):
        for i in reversed(range(self.grid_layout.count())): 
            widget = self.grid_layout.itemAt(i).widget()
            if widget: widget.setParent(None)
            
        all_items = get_all_items()
        grouped_items = {}
        for item in all_items:
            if item[5] != self.current_cat: continue
            key = f"{item[1]}|{item[2]}" 
            if key not in grouped_items: grouped_items[key] = list(item)
            else: grouped_items[key][3] += item[3]
            
        for idx, (key, item) in enumerate(grouped_items.items()):
            name, brand, total_qty, img_path = item[1], item[2], item[3], item[6]
            card = QFrame(); card.setFixedSize(220, 320); card.setStyleSheet("background: white; border: 2px solid #DDD; border-radius: 10px;")
            l = QVBoxLayout(card)
            
            img_lbl = QLabel(); img_lbl.setFixedSize(200, 140); img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            if img_path and os.path.exists(img_path):
                img_lbl.setPixmap(QPixmap(img_path).scaled(200, 140, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
            else:
                img_lbl.setText("📦"); img_lbl.setStyleSheet("background-color: #EEE; color: #999; font-size: 40px;")
            
            n_lbl = QLabel(f"{name}\n({brand})"); n_lbl.setStyleSheet("color: black; font-weight: bold; font-size: 16px; border: none;")
            current_qty = self.cart.get(name, 0)
            remaining_qty = max(total_qty - current_qty, 0)
            s_lbl = QLabel(f"Available: {remaining_qty}"); s_lbl.setStyleSheet("color: #666; border: none;")
            
            add_btn = QPushButton("ADD")
            add_btn.setEnabled(remaining_qty > 0)
            add_btn.setStyleSheet("background-color: #4B8B3B; color: white; font-weight: bold; border-radius: 5px; padding: 10px;")
            add_btn.clicked.connect(lambda ch, i=item: self.add_to_cart_grouped(i))
            
            l.addWidget(img_lbl); l.addWidget(n_lbl); l.addWidget(s_lbl); l.addWidget(add_btn)
            self.grid_layout.addWidget(card, idx // 4, idx % 4)

    def handle_final_submit(self):
        # 1. Check if we are currently on the Borrow Page (Index 6)
        if self.pages.currentIndex() == 6:
            borrower = self.borrow_form_widget.borrower_name.text().strip()
            instructor = self.borrow_form_widget.instructor_name.text().strip()
            room = self.borrow_form_widget.room_no.text().strip()
            
            # Get purpose from the first row of the table (column index 2)
            table = self.borrow_form_widget.table
            purpose_item = table.item(0, 2)
            table_purpose = purpose_item.text().strip() if purpose_item else ""

            # NEW VALIDATION FOR BORROWING
            if not borrower or not instructor or not room or not table_purpose:
                QMessageBox.warning(self, "Required Fields", 
                                    "Please fill in Borrower Name, Instructor, Room No, and Purpose in the table.")
                return
            
            student_name = borrower
            final_purpose = f"Room: {room} | Inst: {instructor} | Purpose: {table_purpose}"
        
        else:
            # THIS IS YOUR OLD RIS LOGIC (Keep it for supplies)
            name_widget = self.sig_widgets.get("NAME:_REQUESTED BY:")
            student_name = name_widget.text().strip()
            purpose_val = self.purpose_in.text().strip()
            
            if not student_name or not purpose_val:
                QMessageBox.warning(self, "Error", "Please fill in Name and Purpose.")
                return
            student_name = student_name
            final_purpose = purpose_val

        # --- DATABASE SUBMISSION (The same for both) ---
        final_cart_with_ids = {}
        for item_name, qty in self.cart.items():
            brand = self.cart_brands.get(item_name, "")
            asset_id = get_available_asset_id(item_name, brand)
            display_name = f"{item_name} [ID: {asset_id}]" if asset_id != "N/A" else item_name
            final_cart_with_ids[display_name] = qty

        add_request(student_name, final_cart_with_ids, final_purpose)
        self.pages.setCurrentIndex(4) # Go to Waiting Screen
        QTimer.singleShot(5000, self.reset_to_start)

    def create_waiting_screen(self):
        page = QFrame(); page.setStyleSheet("background-color: #1B4D2E;"); lay = QVBoxLayout(page)
        msg = QLabel("WAITING FOR VERIFICATION..."); msg.setStyleSheet("color: white; font-size: 40px; font-weight: bold;")
        sub = QLabel("Please wait while the PSO Admin reviews your request."); sub.setStyleSheet("color: #E0E4D9; font-size: 22px;")
        
        self.print_ris_btn = QPushButton("PRINT RIS FORM NOW")
        self.print_ris_btn.setFixedSize(400, 80); self.print_ris_btn.setStyleSheet("background-color: #E0E4D9; color: #1B4D2E; font-weight: bold; font-size: 20px; border-radius: 15px;")
        self.print_ris_btn.clicked.connect(self.process_ris_document)
        
        lay.addStretch(); lay.addWidget(msg, alignment=Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(sub, alignment=Qt.AlignmentFlag.AlignCenter); lay.addSpacing(30)
        lay.addWidget(self.print_ris_btn, alignment=Qt.AlignmentFlag.AlignCenter); lay.addStretch()
        return page

    def print_current_ris(self):
        # 1. Setup the Printer
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageOrientation(QPageLayout.Orientation.Portrait)
        
        # Open the Print Dialog so the user can choose a printer
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QPrintDialog.DialogCode.Accepted:
            painter = QPainter(printer)
            
            # 2. Capture the RIS Form Page as an Image
            # We target the actual container inside the scroll area to get the full form
            ris_page_widget = self.pages.widget(3) # Index 3 is your RIS Form
            
            # This takes a 'screenshot' of the widget
            pixmap = ris_page_widget.grab()
            
            # 3. Scale the image to fit the paper
            rect = painter.viewport()
            size = pixmap.size()
            size.scale(rect.size(), Qt.AspectRatioMode.KeepAspectRatio)
            
            painter.setViewport(rect.x(), rect.y(), size.width(), size.height())
            painter.setWindow(pixmap.rect())
            
            # 4. Draw the image onto the paper
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            
            QMessageBox.information(self, "Printing", "RIS Form sent to printer.")
            self.print_ris_btn.setEnabled(False)
            self.print_ris_btn.setText("RIS PRINTED")

    def reset_to_start(self):
        self.cart = {}; self.cart_brands = {}; self.ris_table.setRowCount(0)
        self.ris_resp_center.clear(); self.ris_office.clear(); self.ris_code.clear(); self.ris_no.clear(); self.purpose_in.clear()
        for w in self.sig_widgets.values(): w.clear()
        self.update_cart_display(); self.pages.setCurrentIndex(0)

    def reset_cart(self):
        self.cart = {}; self.cart_brands = {}; self.update_cart_display(); self.refresh_grid()

    def show_filtered(self, category_code):
        self.current_cat = category_code
        if category_code == "Printing": self.pages.setCurrentIndex(5)
        else: self.refresh_grid(); self.pages.setCurrentIndex(2)
        
    def process_ris_document(self):
        # --- PART 1: SAVE PDF TO HISTORY FOLDER ---
        # Get path to the history folder inside your project
        project_dir = os.path.dirname(os.path.abspath(__file__))
        history_dir = os.path.join(project_dir, "history_pdfs")
        
        if not os.path.exists(history_dir):
            os.makedirs(history_dir)

        # Name the file with a timestamp to make it unique in history
        timestamp = QDateTime.currentDateTime().toString("yyyyMMdd_hhmmss")
        file_path = os.path.join(history_dir, f"RIS_{timestamp}.pdf")

        # Create PDF via render (high quality) - captures the actual form with user inputs
        pdf_writer = QPdfWriter(file_path)
        pdf_writer.setPageSize(QPageSize(QPageSize.PageSizeId.A5))
        pdf_writer.setPageOrientation(QPageLayout.Orientation.Landscape)
        
        painter_pdf = QPainter(pdf_writer)
        ris_page = self.ris_form_widget
        ris_page.adjustSize()
        
        # Scaling for PDF
        scale_pdf = pdf_writer.logicalDpiX() / 96.0
        painter_pdf.scale(scale_pdf, scale_pdf)
        ris_page.render(painter_pdf)
        painter_pdf.end()

        # --- PART 2: AUTOMATIC PRINTING ---
        # Setup printer for physical output
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A5))
        printer.setPageOrientation(QPageLayout.Orientation.Landscape)
        
        # This opens the dialog so the user can select the actual printer
        print_dialog = QPrintDialog(printer, self)
        if print_dialog.exec() == QPrintDialog.DialogCode.Accepted:
            # Re-apply the A5 Landscape settings after dialog closes to ensure they take effect
            printer.setPageSize(QPageSize(QPageSize.PageSizeId.A5))
            printer.setPageOrientation(QPageLayout.Orientation.Landscape)
            
            painter_print = QPainter(printer)
            
            # Capture the printable RIS form widget with user inputs
            ris_page.adjustSize()
            pixmap = ris_page.grab()
            
            # Fit to paper
            rect = painter_print.viewport()
            size = pixmap.size()
            size.scale(rect.size(), Qt.AspectRatioMode.KeepAspectRatio)
            painter_print.setViewport(rect.x(), rect.y(), size.width(), size.height())
            painter_print.setWindow(pixmap.rect())
            
            painter_print.drawPixmap(0, 0, pixmap)
            painter_print.end()

            QMessageBox.information(self, "Success", 
                f"RIS Form saved to history and sent to printer.\nFile: {os.path.basename(file_path)}")
            
            self.print_ris_btn.setEnabled(False)
            self.print_ris_btn.setText("RIS PROCESSED")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    k = StudentKiosk()
    k.show()
    sys.exit(app.exec())