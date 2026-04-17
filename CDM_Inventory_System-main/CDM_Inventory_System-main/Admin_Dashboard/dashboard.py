import sys
import os
import json
from datetime import datetime

# This adds the parent directory to your path so it can find the 'database' folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from PyQt6.QtWidgets import (QApplication, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QLabel, 
                             QFrame, QStackedWidget, QLineEdit, QTableWidget, QTableWidgetItem, 
                             QHeaderView, QMessageBox, QComboBox, QFileDialog, QDialog, QGridLayout) 
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

# Import database functions
from database.db_manager import (get_all_items, add_inventory_item, delete_inventory_item, 
                                 update_inventory_item, get_all_requests, update_request_status,
                                 add_user, update_admin_credentials, deduct_stock, export_to_csv, get_all_users)

# Ensure you have added return_item to your db_manager.py
try:
    from database.db_manager import return_item
except ImportError:
    pass

class EditItemDialog(QDialog):
    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Item")
        self.setFixedWidth(300)
        self.setStyleSheet("background-color: white; color: black;")
        layout = QVBoxLayout(self)

        self.name_in = QLineEdit(str(item_data[1]))
        self.brand_in = QLineEdit(str(item_data[2]))
        self.qty_in = QLineEdit(str(item_data[3]))
        self.cat_in = QComboBox()
        self.cat_in.addItems(["Equipment", "Sound", "Supplies", "Printing"])
        self.cat_in.setCurrentText(str(item_data[5]))

        for w in [self.name_in, self.brand_in, self.qty_in, self.cat_in]:
            w.setStyleSheet("border: 1px solid #CCC; padding: 5px; color: black; background: white;")
            layout.addWidget(w)

        save_btn = QPushButton("SAVE CHANGES")
        save_btn.setStyleSheet("background-color: #1B4D2E; color: white; font-weight: bold; padding: 10px;")
        save_btn.clicked.connect(self.accept)
        layout.addWidget(save_btn)

    def get_values(self):
        return self.name_in.text(), self.brand_in.text(), self.qty_in.text(), self.cat_in.currentText()

class ClickableCard(QFrame):
    clicked = pyqtSignal()
    def __init__(self, title, color):
        super().__init__()
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet("background-color: #E0E4D9; border-radius: 15px;")
        layout = QVBoxLayout(self)
        self.setFixedSize(200, 250)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.label_header = QLabel(title)
        self.label_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.label_header.setFixedHeight(50)
        self.label_header.setStyleSheet(f"background-color: {color}; color: white; border-top-left-radius: 15px; border-top-right-radius: 15px;")
        self.label_header.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        
        self.content_label = QLabel("Click to View Details")
        self.content_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.content_label.setStyleSheet("color: #555; padding: 20px; font-size: 11px;")
        
        layout.addWidget(self.label_header)
        layout.addWidget(self.content_label)

    def mousePressEvent(self, event):
        self.clicked.emit()

class AdminDashboard(QWidget):
    logout_requested = pyqtSignal()

    def __init__(self, user_role="Admin"): 
        super().__init__()
        self.user_role = user_role 
        self.is_refreshing = False
        self.selected_image_path = ""
        self.setWindowTitle("CDM PSO Admin Dashboard")
        self.setGeometry(100, 100, 1100, 700)
        
        self.time_label = QLabel()
        
        self.setStyleSheet("""
            AdminDashboard { background-color: white; }
            QLabel { color: black; }
            QLineEdit { color: black; background-color: white; border: 1px solid #CCC; }
            QComboBox { color: black; background-color: white; border: 1px solid #CCC; }
            QMessageBox { background-color: white; }
            QMessageBox QLabel { color: black; }
            QMessageBox QPushButton { color: black; background-color: #EEE; min-width: 80px; }
        """)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        
        self.setup_top_bar()
        self.pages = QStackedWidget()
        
        self.menu_page = self.create_menu_page()
        self.inventory_page = self.create_inventory_page()
        self.queue_page = self.create_queue_page()
        self.history_page = self.create_history_page() 
        self.returns_page = self.create_returns_page() 
        self.user_mgmt_page = self.create_user_mgmt_page()
        
        self.pages.addWidget(self.menu_page)      
        self.pages.addWidget(self.inventory_page) 
        self.pages.addWidget(self.queue_page)     
        self.pages.addWidget(self.history_page)   
        self.pages.addWidget(self.returns_page)   
        self.pages.addWidget(self.user_mgmt_page) 

        self.main_layout.addWidget(self.top_bar)
        self.main_layout.addWidget(self.pages)
        
        # --- TIMER FOR CLOCK ---
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000) 
        
        self.update_time() 
        self.update_summary_stats()

    def update_time(self):
        # FIX 3: MATCH VARIABLE NAMES EXACTLY
        now = datetime.now()
        date_string = now.strftime("%A, %B %d, %Y") # used date_string
        time_string = now.strftime("%I:%M %p")      # used time_string
        self.time_label.setText(f"{date_string}  |  {time_string}")

    def setup_top_bar(self):
        self.top_bar = QFrame()
        self.top_bar.setFixedHeight(80)
        self.top_bar.setStyleSheet("background-color: #1B4D2E;")
        lay = QHBoxLayout(self.top_bar)
        
        self.back_btn = QPushButton("BACK")
        self.back_btn.setVisible(False)
        self.back_btn.setStyleSheet("color: white; border: 1px solid white; padding: 8px; font-weight: bold; background-color: transparent;")
        self.back_btn.clicked.connect(lambda: self.change_page(0))
        
        self.header = QLabel("PROPERTY AND SUPPLY OFFICE MANAGEMENT SYSTEM")
        self.header.setStyleSheet("color: white; font-weight: bold; font-size: 20px; background-color: transparent;")
        
        self.logout_btn = QPushButton("LOGOUT")
        self.logout_btn.setStyleSheet("background-color: #A32A2A; color: white; padding: 8px 15px; font-weight: bold; border-radius: 5px;")
        self.logout_btn.clicked.connect(self.logout_requested.emit)
        
        self.refresh_btn = QPushButton("⟳")
        self.refresh_btn.setFixedSize(40, 40)
        self.refresh_btn.setStyleSheet("background-color: #1B4D2E; color: white; font-size: 18px; border-radius: 20px; border: 2px solid white;")
        self.refresh_btn.setToolTip("Refresh Data")
        self.refresh_btn.clicked.connect(self.handle_refresh)
        
        lay.addWidget(self.back_btn); lay.addSpacing(20); lay.addWidget(self.header); lay.addStretch(); lay.addWidget(self.refresh_btn); lay.addWidget(self.logout_btn)

    def create_menu_page(self):
        page = QWidget()
        main_vbox = QVBoxLayout(page)
        main_vbox.setContentsMargins(50, 20, 50, 40)

        # --- GREETING SECTION ---
        header_row = QHBoxLayout()
        self.greeting_label = QLabel(f"Hello, {self.user_role}!")
        self.greeting_label.setStyleSheet("font-size: 50px; font-weight: bold; color: #1B4D2E;")
        main_vbox.addWidget(self.greeting_label)
        
        # Stylizing the time label so it's impossible to miss (Dark Grey color)
        self.time_label.setStyleSheet("font-size: 18px; color: #444; font-weight: bold; padding-right: 10px;")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        
        header_row.addWidget(self.greeting_label)
        header_row.addStretch() # This pushes the time label to the right
        header_row.addWidget(self.time_label)
        
        main_vbox.addLayout(header_row)
        
        sub_text = QLabel("Welcome to the Property and Supply Office Dashboard.")
        sub_text.setStyleSheet("font-size: 14px; color: #555; margin-bottom: 20px;")
        main_vbox.addWidget(sub_text)

        # --- STATS SUMMARY ROW ---
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(15)

        self.stat_pending = self.create_stat_widget("PENDING REQUESTS", "0", "#A32A2A")
        self.stat_supplies = self.create_stat_widget("AVAILABLE SUPPLIES", "0", "#1B4D2E") 
        self.stat_equipment = self.create_stat_widget("TOTAL EQUIPMENT", "0", "#2980B9")
        self.stat_low_stock = self.create_stat_widget("LOW STOCK ALERT", "0", "#E67E22")
        self.stat_accounts = self.create_stat_widget("STAFF ACCOUNTS", "0", "#2D5A27")

        stats_layout.addWidget(self.stat_pending)
        stats_layout.addWidget(self.stat_supplies)
        stats_layout.addWidget(self.stat_equipment)
        stats_layout.addWidget(self.stat_low_stock)
        
        # Only add accounts stat if Admin
        if self.user_role == "Admin":
            stats_layout.addWidget(self.stat_accounts)
        
        main_vbox.addLayout(stats_layout)
        main_vbox.addSpacing(40)

        # --- NAVIGATION CATEGORY CARDS ---
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(20)
        cards_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Initialize the cards
        self.card_queue = ClickableCard("REQUEST QUEUES", "#2D5A27")
        self.card_inventory = ClickableCard("STOCKS & INVENTORY", "#2D5A27")
        self.card_history = ClickableCard("TRANSACTION HISTORY", "#2D5A27")
        self.card_returns = ClickableCard("EQUIPMENT RETURNS", "#2D5A27") 
        self.card_users = ClickableCard("STAFF MANAGEMENT", "#1B4D2E")

        # Connect the signals
        self.card_inventory.clicked.connect(lambda: self.change_page(1))
        self.card_queue.clicked.connect(lambda: self.change_page(2))
        self.card_history.clicked.connect(lambda: self.change_page(3))
        self.card_returns.clicked.connect(lambda: self.change_page(4))
        self.card_users.clicked.connect(lambda: self.change_page(5))

        # Create the list of cards to actually add to the UI
        display_cards = [self.card_queue, self.card_inventory, self.card_history, self.card_returns]
        
        # Only add the user management card if the role is Admin
        if self.user_role == "Admin":
            display_cards.append(self.card_users)
        else:
            self.card_users.hide() # Keep it hidden for Staff

        # Add the validated list to the layout
        for card in display_cards:
            cards_layout.addWidget(card)

        main_vbox.addLayout(cards_layout)
        main_vbox.addStretch()
        return page

    def create_stat_widget(self, title, value, color):
        frame = QFrame()
        frame.setStyleSheet(f"background-color: {color}; border-radius: 10px;")
        frame.setFixedHeight(80)
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(10, 5, 10, 5)
        
        tit_label = QLabel(title)
        tit_label.setStyleSheet("color: rgba(255,255,255,0.9); font-size: 10px; font-weight: bold;")
        val_label = QLabel(value)
        val_label.setObjectName("value_label")
        val_label.setStyleSheet("color: white; font-size: 24px; font-weight: bold;")
        
        lay.addWidget(tit_label)
        lay.addWidget(val_label)
        return frame

    def update_summary_stats(self):
        try:
            reqs = get_all_requests()
            items = get_all_items()
            
            # 1. Pending Requests
            pending = len([r for r in reqs if r[4] == 'PENDING'])
            self.stat_pending.findChild(QLabel, "value_label").setText(str(pending))

            # 2. Hybrid Logic split: Supplies vs Equipment
            consumables_qty = sum(i[3] for i in items if i[5] in ["Supplies", "Printing"])
            equipment_qty = sum(i[3] for i in items if i[5] in ["Equipment", "Sound"])
            
            self.stat_supplies.findChild(QLabel, "value_label").setText(str(consumables_qty))
            self.stat_equipment.findChild(QLabel, "value_label").setText(str(equipment_qty))

            # 3. Low Stock Alert (Consumables only)
            low_stock = len([i for i in items if i[5] in ["Supplies", "Printing"] and i[3] < 10])
            self.stat_low_stock.findChild(QLabel, "value_label").setText(str(low_stock))

            if self.user_role == "Admin":
                users = get_all_users()
                self.stat_accounts.findChild(QLabel, "value_label").setText(str(len(users)))
                
        except Exception as e:
            print(f"Stats Update Error: {e}")

    def create_inventory_page(self):
        page = QWidget(); lay = QVBoxLayout(page); lay.setContentsMargins(30, 20, 30, 30)
        self.name_in = QLineEdit(placeholderText="Item Name")
        self.brand_in = QLineEdit(placeholderText="Brand") 
        self.qty_in = QLineEdit(placeholderText="Qty"); self.qty_in.setFixedWidth(50)
        
        self.prop_id_in = QLineEdit(placeholderText="Property ID")
        self.prop_id_in.setVisible(False) 
        
        self.cat_in = QComboBox(); self.cat_in.addItems(["Equipment", "Sound", "Supplies", "Printing"])
        self.cat_in.currentTextChanged.connect(self.toggle_prop_id)
        self.cat_in.currentTextChanged.connect(self.refresh_table)
        
        self.img_btn = QPushButton("IMAGE")
        self.img_btn.setStyleSheet("color: black; background-color: #EEE; border: 1px solid #CCC; padding: 5px;")
        self.img_btn.clicked.connect(self.browse_image)
        
        add_btn = QPushButton("ADD ITEM")
        add_btn.setStyleSheet("background-color: #1B4D2E; color: white; font-weight: bold; padding: 5px;")
        add_btn.clicked.connect(self.handle_add)
        
        down_btn = QPushButton("DOWNLOAD STOCKS")
        down_btn.setStyleSheet("background-color: #4B8B3B; color: white; font-weight: bold; padding: 5px;")
        down_btn.clicked.connect(self.download_inventory)

        input_row = QHBoxLayout()
        for w in [self.name_in, self.brand_in, self.qty_in, self.cat_in, self.prop_id_in, self.img_btn, add_btn, down_btn]:
            input_row.addWidget(w)
        
        self.inv_table = QTableWidget(0, 7) 
        self.inv_table.setHorizontalHeaderLabels(["ID", "Name", "Brand", "Qty", "Status", "Category", "Action"])
        self.inv_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.inv_table.setStyleSheet("QTableWidget { background-color: white; color: black; } QHeaderView::section { color: black; }")
        
        lay.addLayout(input_row); lay.addWidget(self.inv_table); return page

    def toggle_prop_id(self, category):
        is_special = category in ["Equipment", "Sound"]
        self.prop_id_in.setVisible(is_special)
        if not is_special:
            self.prop_id_in.clear()

    def download_inventory(self):
        try:
            items = get_all_items()
            headers = ["ID", "Item Name", "Brand", "Quantity", "Status", "Category", "Image Path", "Property ID"]
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            filename = os.path.join(desktop, "Inventory_Report.csv")
            if export_to_csv(items, filename, headers):
                QMessageBox.information(self, "Download Success", f"File saved to Desktop:\n{filename}")
        except Exception as e:
            QMessageBox.warning(self, "Error", str(e))

    def browse_image(self):
        file_filter = "Image Files (*.png *.jpg *.jpeg *.bmp)"
        path, _ = QFileDialog.getOpenFileName(self, "Select Item Image", "", file_filter)
        if path:
            self.selected_image_path = path; self.img_btn.setText("SET")
            self.img_btn.setStyleSheet("background-color: #4B8B3B; color: white; font-weight: bold;")

    def handle_add(self):
        name = self.name_in.text().strip()
        brand = self.brand_in.text().strip()
        qty = self.qty_in.text().strip()
        cat = self.cat_in.currentText()
        prop_id = self.prop_id_in.text().strip() if self.prop_id_in.isVisible() else "N/A"

        if name and qty.isdigit():
            add_inventory_item(name, brand, int(qty), cat, self.selected_image_path, prop_id)
            self.name_in.clear(); self.brand_in.clear(); self.qty_in.clear(); self.prop_id_in.clear()
            self.selected_image_path = ""; self.img_btn.setText("IMAGE")
            self.refresh_table()
        else: QMessageBox.warning(self, "Error", "Invalid inputs.")

    def refresh_table(self):
        self.is_refreshing = True
        self.inv_table.setRowCount(0)
        
        current_cat = self.cat_in.currentText()
        is_special = current_cat in ["Equipment", "Sound"]

        if is_special:
            self.inv_table.setColumnCount(8)
            self.inv_table.setHorizontalHeaderLabels(["ID", "Name", "Brand", "Qty", "Status", "Category", "Property ID", "Action"])
        else:
            self.inv_table.setColumnCount(7)
            self.inv_table.setHorizontalHeaderLabels(["ID", "Name", "Brand", "Qty", "Status", "Category", "Action"])

        items = get_all_items()
        filtered_items = [item for item in items if item[5] == current_cat]

        for idx, data in enumerate(filtered_items):
            self.inv_table.insertRow(idx)
            for c in range(min(len(data), 6)): 
                it = QTableWidgetItem(str(data[c])); it.setForeground(Qt.GlobalColor.black)
                self.inv_table.setItem(idx, c, it)
            
            if is_special:
                prop_val = data[7] if len(data) > 7 else "N/A"
                prop_it = QTableWidgetItem(str(prop_val)); prop_it.setForeground(Qt.GlobalColor.black)
                self.inv_table.setItem(idx, 6, prop_it)
                action_col = 7
            else:
                action_col = 6
            
            btns_widget = QWidget(); btns_layout = QHBoxLayout(btns_widget); btns_layout.setContentsMargins(2, 2, 2, 2)
            edit_btn = QPushButton("EDIT"); edit_btn.setStyleSheet("background-color: #2D5A27; color: white; font-weight: bold;")
            edit_btn.clicked.connect(lambda ch, d=data: self.handle_edit(d))
            del_btn = QPushButton("DELETE"); del_btn.setStyleSheet("background-color: #A32A2A; color: white; font-weight: bold;")
            del_btn.clicked.connect(lambda ch, id=data[0]: (delete_inventory_item(id), self.refresh_table()))
            btns_layout.addWidget(edit_btn); btns_layout.addWidget(del_btn)
            self.inv_table.setCellWidget(idx, action_col, btns_widget)
            
        self.inv_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.is_refreshing = False

    def handle_edit(self, item_data):
        if len(item_data) < 8 and item_data[5] in ["Equipment", "Sound"]:
             QMessageBox.warning(self, "Data Error", "This item lacks a Property ID. Please delete and re-add it.")
             return
        dialog = EditItemDialog(item_data, self)
        if dialog.exec():
            name, brand, qty, cat = dialog.get_values()
            if name and qty.isdigit():
                img = item_data[6] if len(item_data) > 6 else ""
                pid = item_data[7] if len(item_data) > 7 else "N/A"
                update_inventory_item(item_data[0], name, brand, int(qty), cat, img, pid)
                self.refresh_table()
            else: QMessageBox.warning(self, "Error", "Invalid inputs.")

    def create_queue_page(self):
        page = QWidget(); lay = QVBoxLayout(page); lay.setContentsMargins(30, 20, 30, 30)
        title = QLabel("PENDING REQUESTS"); title.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.que_table = QTableWidget(0, 5); self.que_table.setHorizontalHeaderLabels(["ID", "Student", "Items", "Purpose", "Action"])
        self.que_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.que_table.setStyleSheet("QTableWidget { background-color: white; color: black; } QHeaderView::section { color: black; }")
        ref = QPushButton("REFRESH QUEUE"); ref.setStyleSheet("background-color: #1B4D2E; color: white; font-weight: bold; padding: 10px;"); ref.clicked.connect(self.refresh_queue)
        lay.addWidget(title); lay.addWidget(ref); lay.addWidget(self.que_table); return page

    def refresh_queue(self):
        self.que_table.setRowCount(0); reqs = get_all_requests()
        for data in reqs:
            if data[4] != 'PENDING': continue
            row = self.que_table.rowCount(); self.que_table.insertRow(row)
            def make_black_item(text):
                it = QTableWidgetItem(str(text)); it.setForeground(Qt.GlobalColor.black); return it
            self.que_table.setItem(row, 0, make_black_item(data[0])); self.que_table.setItem(row, 1, make_black_item(data[1]))
            items_dict = json.loads(data[2]); txt = ", ".join([f"{n} (x{q})" for n, q in items_dict.items()])
            self.que_table.setItem(row, 2, make_black_item(txt)); self.que_table.setItem(row, 3, make_black_item(data[3]))
            btns = QWidget(); b_lay = QHBoxLayout(btns); b_lay.setContentsMargins(2,2,2,2)
            app = QPushButton("APPROVE"); rej = QPushButton("REJECT")
            app.setStyleSheet("background-color: green; color: white; font-weight: bold;"); rej.setStyleSheet("background-color: red; color: white; font-weight: bold;")
            app.clicked.connect(lambda ch, id=data[0]: self.handle_update_request(id, "APPROVED"))
            rej.clicked.connect(lambda ch, id=data[0]: self.handle_update_request(id, "REJECTED"))
            b_lay.addWidget(app); b_lay.addWidget(rej); self.que_table.setCellWidget(row, 4, btns)

    def handle_update_request(self, rid, status):
        update_request_status(rid, status)
        if status == "APPROVED":
            reqs = get_all_requests()
            this_req = next((r for r in reqs if r[0] == rid), None)
            if this_req:
                items_dict = json.loads(this_req[2])
                for display_name, qty in items_dict.items():
                    if " [ID: " in display_name:
                        name = display_name.split(" [ID: ")[0]
                        prop_id = display_name.split("ID: ")[1].replace("]", "")
                        deduct_stock(name, qty, prop_id)
                    else:
                        deduct_stock(display_name, qty)
            QMessageBox.information(self, "Success", f"Request #{rid} Approved and Stock Updated.")
        self.refresh_queue(); self.refresh_history(); self.refresh_returns(); self.refresh_table()

    def create_history_page(self):
        page = QWidget(); lay = QVBoxLayout(page); lay.setContentsMargins(30, 20, 30, 30)
        title = QLabel("TRANSACTION HISTORY"); title.setStyleSheet("font-size: 20px; font-weight: bold;")
        btn_row = QHBoxLayout()
        ref = QPushButton("REFRESH HISTORY"); ref.setStyleSheet("background-color: #1B4D2E; color: white; font-weight: bold; padding: 10px;"); ref.clicked.connect(self.refresh_history)
        down_hist = QPushButton("DOWNLOAD HISTORY"); down_hist.setStyleSheet("background-color: #4B8B3B; color: white; font-weight: bold; padding: 10px;"); down_hist.clicked.connect(self.download_history)
        btn_row.addWidget(ref); btn_row.addWidget(down_hist)
        self.hist_table = QTableWidget(0, 7); self.hist_table.setHorizontalHeaderLabels(["ID", "Student", "Items", "Purpose", "Status", "Date", "PDF"])
        self.hist_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); self.hist_table.setStyleSheet("QTableWidget { background-color: white; color: black; } QHeaderView::section { color: black; }")
        lay.addWidget(title); lay.addLayout(btn_row); lay.addWidget(self.hist_table); return page

    def download_history(self):
        try:
            reqs = get_all_requests()
            history_data = [r for r in reqs if r[4] != 'PENDING']
            headers = ["ID", "Student", "Items JSON", "Purpose", "Status", "Date"]
            desktop = os.path.join(os.path.expanduser("~"), "Desktop"); filename = os.path.join(desktop, "Transaction_History.csv")
            if export_to_csv(history_data, filename, headers):
                QMessageBox.information(self, "Success", f"History saved to Desktop:\n{filename}")
        except Exception as e: QMessageBox.warning(self, "Error", str(e))

    def download_pdf_for_request(self, request_id):
        """Downloads the PDF file for a specific request from the history_pdfs folder."""
        try:
            # Get the path to the history_pdfs folder
            project_dir = os.path.dirname(os.path.abspath(__file__))
            history_dir = os.path.join(project_dir, "history_pdfs")
            
            if not os.path.exists(history_dir):
                QMessageBox.warning(self, "Error", "No PDF files found. Please check if any requests have been processed.")
                return
            
            # Find PDF files that match this request ID
            pdf_files = []
            for filename in os.listdir(history_dir):
                if filename.endswith(".pdf") and f"RIS_{request_id}_" in filename:
                    pdf_files.append(filename)
            
            if not pdf_files:
                QMessageBox.warning(self, "Error", f"No PDF file found for Request ID: {request_id}")
                return
            
            # If multiple files found, use the latest one
            pdf_files.sort(reverse=True)  # Sort by name (timestamp)
            pdf_filename = pdf_files[0]
            source_path = os.path.join(history_dir, pdf_filename)
            
            # Ask user where to save the file
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            default_save_path = os.path.join(desktop, pdf_filename)
            
            save_path, _ = QFileDialog.getSaveFileName(
                self, 
                "Save PDF File", 
                default_save_path, 
                "PDF Files (*.pdf)"
            )
            
            if save_path:
                # Copy the file to the user's chosen location
                import shutil
                shutil.copy2(source_path, save_path)
                QMessageBox.information(self, "Success", f"PDF file downloaded successfully:\n{save_path}")
            else:
                QMessageBox.information(self, "Cancelled", "Download cancelled by user.")
                
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to download PDF: {str(e)}")

    def refresh_history(self):
        self.hist_table.setRowCount(0); reqs = get_all_requests()
        for data in reqs:
            if data[4] == 'PENDING': continue
            row = self.hist_table.rowCount(); self.hist_table.insertRow(row)
            def make_item(text, color=Qt.GlobalColor.black):
                it = QTableWidgetItem(str(text)); it.setForeground(color); return it
            self.hist_table.setItem(row, 0, make_item(data[0])); self.hist_table.setItem(row, 1, make_item(data[1]))
            items_dict = json.loads(data[2]); txt = ", ".join([f"{n} (x{q})" for n, q in items_dict.items()])
            self.hist_table.setItem(row, 2, make_item(txt)); self.hist_table.setItem(row, 3, make_item(data[3]))
            st_color = Qt.GlobalColor.darkGreen if data[4] == "APPROVED" else Qt.GlobalColor.red
            if data[4] == "RETURNED": st_color = Qt.GlobalColor.blue
            self.hist_table.setItem(row, 4, make_item(data[4], st_color)); self.hist_table.setItem(row, 5, make_item(data[5]))
            
            # Add PDF download button
            pdf_widget = QWidget(); pdf_layout = QHBoxLayout(pdf_widget); pdf_layout.setContentsMargins(2, 2, 2, 2)
            pdf_btn = QPushButton("DOWNLOAD PDF"); pdf_btn.setStyleSheet("background-color: #1B4D2E; color: white; font-weight: bold; padding: 5px;")
            pdf_btn.clicked.connect(lambda ch, req_id=data[0]: self.download_pdf_for_request(req_id))
            pdf_layout.addWidget(pdf_btn); self.hist_table.setCellWidget(row, 6, pdf_widget)

    def create_returns_page(self):
        page = QWidget(); lay = QVBoxLayout(page); lay.setContentsMargins(30, 20, 30, 30)
        title = QLabel("PENDING RETURNS (Equipment & Sound)"); title.setStyleSheet("font-size: 20px; font-weight: bold;")
        self.ret_table = QTableWidget(0, 5); self.ret_table.setHorizontalHeaderLabels(["ID", "Student", "Items", "Status", "Action"])
        self.ret_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ret_table.setStyleSheet("QTableWidget { background-color: white; color: black; } QHeaderView::section { color: black; }")
        ref = QPushButton("REFRESH RETURNS"); ref.setStyleSheet("background-color: #1B4D2E; color: white; font-weight: bold; padding: 10px;"); ref.clicked.connect(self.refresh_returns)
        lay.addWidget(title); lay.addWidget(ref); lay.addWidget(self.ret_table); return page

    def refresh_returns(self):
        self.ret_table.setRowCount(0); reqs = get_all_requests()
        for data in reqs:
            if data[4] != "APPROVED": continue
            items_dict = json.loads(data[2]); needs_return = False
            for display_name in items_dict.keys():
                if " [ID: " in display_name or any(cat in display_name for cat in ["Equipment", "Sound"]):
                    needs_return = True; break
            if not needs_return: continue
            row = self.ret_table.rowCount(); self.ret_table.insertRow(row)
            def make_item(text):
                it = QTableWidgetItem(str(text)); it.setForeground(Qt.GlobalColor.black); return it
            self.ret_table.setItem(row, 0, make_item(data[0])); self.ret_table.setItem(row, 1, make_item(data[1]))
            txt = ", ".join([f"{n} (x{q})" for n, q in items_dict.items()])
            self.ret_table.setItem(row, 2, make_item(txt)); self.ret_table.setItem(row, 3, make_item("BORROWED"))
            btn = QPushButton("MARK AS RETURNED"); btn.setStyleSheet("background-color: #1B4D2E; color: white; font-weight: bold;")
            btn.clicked.connect(lambda ch, r_id=data[0], items=items_dict: self.handle_return(r_id, items))
            self.ret_table.setCellWidget(row, 4, btn)

    def handle_return(self, rid, items_dict):
        update_request_status(rid, "RETURNED")
        for display_name, qty in items_dict.items():
            if " [ID: " in display_name:
                name = display_name.split(" [ID: ")[0]
                prop_id = display_name.split("ID: ")[1].replace("]", "")
                return_item(name, qty, prop_id)
            else:
                return_item(display_name, qty)
        QMessageBox.information(self, "Success", "Items returned to inventory."); self.refresh_returns(); self.refresh_table(); self.refresh_history()

    def create_user_mgmt_page(self):
        page = QWidget(); main_layout = QVBoxLayout(page); main_layout.setContentsMargins(30, 20, 30, 30); input_row = QHBoxLayout()
        admin_frame = QFrame(); admin_frame.setStyleSheet("background-color: #F4F6F1; border-radius: 10px; border: 1px solid #1B4D2E;")
        admin_lay = QVBoxLayout(admin_frame); self.admin_user_in = QLineEdit(placeholderText="New Admin User"); self.admin_pass_in = QLineEdit(placeholderText="New Admin Pass"); self.admin_pass_in.setEchoMode(QLineEdit.EchoMode.Password); update_admin_btn = QPushButton("UPDATE ADMIN"); update_admin_btn.setStyleSheet("background-color: #1B4D2E; color: white; font-weight: bold; padding: 5px;"); update_admin_btn.clicked.connect(self.handle_update_admin)
        admin_lay.addWidget(QLabel("RENEW ADMIN CREDENTIALS")); admin_lay.addWidget(self.admin_user_in); admin_lay.addWidget(self.admin_pass_in); admin_lay.addWidget(update_admin_btn)
        staff_frame = QFrame(); staff_frame.setStyleSheet("background-color: #E0E4D9; border-radius: 10px; border: 1px solid #1B4D2E;")
        staff_lay = QVBoxLayout(staff_frame); self.new_staff_user = QLineEdit(placeholderText="Username"); self.new_staff_pass = QLineEdit(placeholderText="Password"); add_btn = QPushButton("ADD STAFF"); add_btn.setStyleSheet("background-color: #2D5A27; color: white; font-weight: bold; padding: 5px;"); add_btn.clicked.connect(self.handle_add_staff)
        staff_lay.addWidget(QLabel("CREATE NEW STAFF")); staff_lay.addWidget(self.new_staff_user); staff_lay.addWidget(self.new_staff_pass); staff_lay.addWidget(add_btn); input_row.addWidget(admin_frame); input_row.addWidget(staff_frame); main_layout.addLayout(input_row)
        table_title = QLabel("MANAGED ACCOUNTS"); table_title.setStyleSheet("font-size: 18px; font-weight: bold; margin-top: 20px;"); main_layout.addWidget(table_title)
        self.user_table = QTableWidget(0, 5); self.user_table.setHorizontalHeaderLabels(["ID", "Username", "Email", "Role", "Actions"]); self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch); self.user_table.setStyleSheet("QTableWidget { background-color: white; color: black; }"); main_layout.addWidget(self.user_table); self.refresh_user_table(); return page

    def refresh_user_table(self):
        from database.db_manager import get_user_by_id
        self.user_table.setRowCount(0); users = get_all_users()
        for idx, user in enumerate(users):
            full_user = get_user_by_id(user[0])
            self.user_table.insertRow(idx)
            self.user_table.setItem(idx, 0, QTableWidgetItem(str(full_user[0])))
            self.user_table.setItem(idx, 1, QTableWidgetItem(str(full_user[1])))
            self.user_table.setItem(idx, 2, QTableWidgetItem(str(full_user[4]) if full_user[4] else ""))
            self.user_table.setItem(idx, 3, QTableWidgetItem(str(full_user[3])))
            btn_widget = QWidget(); btn_lay = QHBoxLayout(btn_widget); btn_lay.setContentsMargins(2,2,2,2)
            if user[2] == "Staff":
                edit_btn = QPushButton("EDIT"); edit_btn.setStyleSheet("background-color: #2D5A27; color: white; font-weight: bold;")
                edit_btn.clicked.connect(lambda ch, uid=user[0]: self.handle_edit_staff(uid))
                btn_lay.addWidget(edit_btn)
            del_btn = QPushButton("DELETE"); del_btn.setStyleSheet("background-color: #A32A2A; color: white; font-weight: bold;")
            if user[0] == 1: del_btn.setEnabled(False); del_btn.setStyleSheet("background-color: #CCC; color: white;")
            del_btn.clicked.connect(lambda ch, uid=user[0]: self.handle_delete_user(uid))
            btn_lay.addWidget(del_btn); self.user_table.setCellWidget(idx, 4, btn_widget)

    def handle_delete_user(self, uid):
        from database.db_manager import delete_user
        confirm = QMessageBox.question(self, "Confirm Delete", "Permanently remove this account?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes: delete_user(uid); self.refresh_user_table()

    def handle_update_admin(self):
        u, p = self.admin_user_in.text().strip(), self.admin_pass_in.text().strip()
        if u and p: 
            if update_admin_credentials(u, p): QMessageBox.information(self, "Success", "Admin Account Updated."); self.admin_user_in.clear(); self.admin_pass_in.clear(); self.refresh_user_table()
        else: QMessageBox.warning(self, "Error", "Incomplete fields.")

    def handle_add_staff(self):
        u, p = self.new_staff_user.text().strip(), self.new_staff_pass.text().strip()
        if u and p:
            if add_user(u, p, "Staff"): QMessageBox.information(self, "Success", f"New account '{u}' created."); self.new_staff_user.clear(); self.new_staff_pass.clear(); self.refresh_user_table()
        else: QMessageBox.warning(self, "Error", "Incomplete fields.")

    def handle_edit_staff(self, user_id):
        from database.db_manager import get_user_by_id, update_staff_credentials
        user = get_user_by_id(user_id)
        if not user:
            QMessageBox.warning(self, "Error", "User not found.")
            return
        edit_dlg = QDialog(self)
        edit_dlg.setWindowTitle(f"Edit Staff Account - {user[1]}")
        edit_dlg.setFixedSize(350, 250)
        dlg_lay = QVBoxLayout(edit_dlg)
        dlg_lay.addWidget(QLabel("Username:"))
        user_in = QLineEdit(user[1]); dlg_lay.addWidget(user_in)
        dlg_lay.addWidget(QLabel("Password:"))
        pass_in = QLineEdit(user[2]); dlg_lay.addWidget(pass_in)
        dlg_lay.addWidget(QLabel("Email:"))
        email_in = QLineEdit(user[4] if user[4] else ""); dlg_lay.addWidget(email_in)
        btn_lay = QHBoxLayout()
        save_btn = QPushButton("SAVE"); save_btn.setStyleSheet("background-color: #1B4D2E; color: white;")
        cancel_btn = QPushButton("CANCEL"); cancel_btn.setStyleSheet("background-color: #999; color: white;")
        save_btn.clicked.connect(lambda: self.save_staff_changes(user_id, user_in.text().strip(), pass_in.text().strip(), email_in.text().strip(), edit_dlg))
        cancel_btn.clicked.connect(edit_dlg.reject)
        btn_lay.addWidget(save_btn); btn_lay.addWidget(cancel_btn); dlg_lay.addLayout(btn_lay)
        edit_dlg.exec()

    def save_staff_changes(self, user_id, username, password, email, dialog):
        from database.db_manager import update_staff_credentials
        if not username or not password:
            QMessageBox.warning(self, "Error", "Username and password are required.")
            return
        if update_staff_credentials(user_id, username, password, email):
            QMessageBox.information(self, "Success", "Staff account updated.")
            self.refresh_user_table()
            dialog.accept()
        else:
            QMessageBox.critical(self, "Error", "Failed to update staff account.")

    def handle_refresh(self):
        """Handles the refresh button click - refreshes all data across all pages."""
        try:
            # Show a quick feedback message
            self.refresh_btn.setText("⟳")
            self.refresh_btn.setStyleSheet("background-color: #4B8B3B; color: white; font-size: 18px; border-radius: 20px; border: 2px solid white;")
            
            # Refresh all data
            self.update_summary_stats()
            self.refresh_table()
            self.refresh_queue()
            self.refresh_history()
            self.refresh_returns()
            self.refresh_user_table()
            
            # Reset button style
            self.refresh_btn.setStyleSheet("background-color: #1B4D2E; color: white; font-size: 18px; border-radius: 20px; border: 2px solid white;")
            
            # Show success message
            QMessageBox.information(self, "Refresh Complete", "All data has been refreshed successfully.")
            
        except Exception as e:
            QMessageBox.warning(self, "Refresh Error", f"Failed to refresh data: {str(e)}")
            # Reset button style even on error
            self.refresh_btn.setStyleSheet("background-color: #1B4D2E; color: white; font-size: 18px; border-radius: 20px; border: 2px solid white;")

    def change_page(self, index):
        if index == 5 and self.user_role == "Staff":
            QMessageBox.warning(self, "Access Denied", "Restricted to Admin only."); return
        
        self.pages.setCurrentIndex(index)
        self.back_btn.setVisible(index != 0)
        self.logout_btn.setVisible(index == 0)
        
        # Refresh Logic
        if index == 0: self.update_summary_stats()
        elif index == 1: self.refresh_table()
        elif index == 2: self.refresh_queue()
        elif index == 3: self.refresh_history()
        elif index == 4: self.refresh_returns()
        elif index == 5: self.refresh_user_table()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AdminDashboard(user_role="Admin") # Test as Admin
    window.show()
    sys.exit(app.exec())