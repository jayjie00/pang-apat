import sys
import smtplib
import ssl
import random
import datetime
from database.db_manager import (
    verify_admin,
    get_user_by_email,
    store_reset_code,
    verify_reset_code,
    reset_password_by_email,
    get_reset_code_info,
)
from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, 
                             QLineEdit, QPushButton, QLabel, QFrame, QDialog, QMessageBox)
from PyQt6.QtGui import QFont, QAction
from PyQt6.QtCore import Qt, pyqtSignal, QTimer

# SMTP configuration: update these values with your SMTP provider settings.
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "cdmsupply123@gmail.com"
SMTP_PASSWORD = "rqipqeofkwcsrstk"
SMTP_FROM = SMTP_USERNAME
SMTP_USE_TLS = True


def send_reset_code_email(email, code):
    subject = "CDM Inventory Password Reset"
    body = f"Your reset code is: {code}\n\nIf you did not request this, please ignore this email."
    message = f"Subject: {subject}\n\n{body}"
    try:
        if SMTP_PORT == 465:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context, timeout=10) as server:
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.sendmail(SMTP_FROM, [email], message)
        else:
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
                if SMTP_USE_TLS:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                server.login(SMTP_USERNAME, SMTP_PASSWORD)
                server.sendmail(SMTP_FROM, [email], message)
        return True
    except Exception as e:
        print(f"SMTP send error: {e}")
        return False


class ForgotPasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Forgot Password")
        self.setFixedSize(360, 380)
        self.setStyleSheet("background-color: #F5F5F5;")

        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)
        self.countdown_remaining = 0

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Reset Password")
        title.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        title.setStyleSheet("color: #1B4D2E;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Enter email")
        self.email_input.setStyleSheet("padding: 10px; border: 1px solid #CCC; border-radius: 5px; background-color: white;")

        self.send_code_btn = QPushButton("SEND RESET CODE")
        self.send_code_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.send_code_btn.setStyleSheet("QPushButton { background-color: #1B4D2E; color: white; padding: 11px; border-radius: 5px; } QPushButton:hover { background-color: #2D5A27; }")
        self.send_code_btn.clicked.connect(self.handle_send_reset_code)

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Enter the 6-digit code")
        self.code_input.setStyleSheet("padding: 10px; border: 1px solid #CCC; border-radius: 5px; background-color: white;")

        self.new_password_input = QLineEdit()
        self.new_password_input.setPlaceholderText("Enter new password")
        self.new_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password_input.setStyleSheet("padding: 10px; border: 1px solid #CCC; border-radius: 5px; background-color: white;")

        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setPlaceholderText("Re-enter new password")
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setStyleSheet("padding: 10px; border: 1px solid #CCC; border-radius: 5px; background-color: white;")

        self.reset_btn = QPushButton("UPDATE PASSWORD")
        self.reset_btn.setFont(QFont("Arial", 11, QFont.Weight.Bold))
        self.reset_btn.setStyleSheet("QPushButton { background-color: #C78D1C; color: white; padding: 11px; border-radius: 5px; } QPushButton:hover { background-color: #a67514; }")
        self.reset_btn.clicked.connect(self.handle_reset_password)

        layout.addWidget(title)
        layout.addWidget(self.email_input)
        layout.addWidget(self.send_code_btn)
        layout.addWidget(self.code_input)
        layout.addWidget(self.new_password_input)
        layout.addWidget(self.confirm_password_input)
        layout.addWidget(self.reset_btn)

        self.setLayout(layout)

    def handle_send_reset_code(self):
        email = self.email_input.text().strip()
        if not email:
            QMessageBox.warning(self, "Incomplete Data", "Please enter your email address.")
            return

        user = get_user_by_email(email)
        if not user:
            QMessageBox.warning(self, "Email Not Found", "No account is registered with this email.")
            return

        info = get_reset_code_info(email)
        if info:
            _, expiry, sent_at = info
            if sent_at:
                try:
                    sent_dt = datetime.datetime.fromisoformat(sent_at)
                    if sent_dt + datetime.timedelta(minutes=1) > datetime.datetime.utcnow():
                        wait = 60 - int((datetime.datetime.utcnow() - sent_dt).total_seconds())
                        QMessageBox.warning(self, "Wait Before Retry", f"Please wait {wait} second(s) before requesting a new reset code.")
                        return
                except Exception:
                    pass

        code = f"{random.randint(100000, 999999):06d}"
        expiry = (datetime.datetime.utcnow() + datetime.timedelta(minutes=10)).isoformat()
        sent_at = datetime.datetime.utcnow().isoformat()
        if not store_reset_code(email, code, expiry, sent_at):
            QMessageBox.critical(self, "Error", "Failed to store reset code. Please try again.")
            return

        if send_reset_code_email(email, code):
            QMessageBox.information(self, "Reset Code Sent", "A reset code was sent to " + email + ".")
            self.send_code_btn.setEnabled(False)
            self.countdown_remaining = 60
            self.send_code_btn.setText(f"RESEND IN {self.countdown_remaining}s")
            self.countdown_timer.start(1000)
        else:
            QMessageBox.warning(self, "Email Failed", "Could not send the email. Check SMTP settings in the code.")

    def update_countdown(self):
        self.countdown_remaining -= 1
        self.send_code_btn.setText(f"RESEND IN {self.countdown_remaining}s")
        if self.countdown_remaining <= 0:
            self.enable_send_button()

    def handle_reset_password(self):
        email = self.email_input.text().strip()
        code = self.code_input.text().strip()
        new_password = self.new_password_input.text().strip()
        confirm_password = self.confirm_password_input.text().strip()

        if not email or not code or not new_password or not confirm_password:
            QMessageBox.warning(self, "Incomplete Data", "Please complete all fields before updating your password.")
            return

        if new_password != confirm_password:
            QMessageBox.warning(self, "Password Mismatch", "New password and confirmation do not match.")
            return

        if not verify_reset_code(email, code):
            QMessageBox.warning(self, "Invalid Code", "The reset code is incorrect or has expired.")
            return

        if reset_password_by_email(email, new_password):
            QMessageBox.information(self, "Success", "Your password has been updated. You may now log in.")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", "Unable to update password. Please try again later.")

    def enable_send_button(self):
        self.countdown_timer.stop()
        self.send_code_btn.setEnabled(True)
        self.send_code_btn.setText("SEND RESET CODE")
        self.countdown_remaining = 0


class AdminLogin(QWidget):
    # This signal carries a string (the user's role: 'Admin' or 'Staff')
    login_success = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CDM PSO - Admin Login")
        self.setGeometry(100, 100, 1000, 600)
        self.setStyleSheet("background-color: #F5F5F5;")

        # Track password visibility state
        self.password_visible = False

        # Main Layout
        self.layout = QVBoxLayout()
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Container Frame (The Login Card)
        self.card = QFrame()
        self.card.setFixedSize(320, 460)
        self.card.setStyleSheet("background-color: white; border-radius: 15px; border: 1px solid #DDD;")

        self.card_layout = QVBoxLayout(self.card)
        self.card_layout.setContentsMargins(30, 40, 30, 40)
        self.card_layout.setSpacing(20)

        # Title
        self.title = QLabel("ADMIN LOGIN")
        self.title.setFont(QFont("Arial", 20, QFont.Weight.Bold))
        self.title.setStyleSheet("color: #1B4D2E; border: none;")
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Username Input
        self.username = QLineEdit()
        self.username.setPlaceholderText("Username")
        self.username.setStyleSheet("""
            QLineEdit {
                padding: 10px; border: 1px solid #CCC; border-radius: 5px; 
                color: black; background-color: white;
            }
        """)

        # Password Input
        self.password = QLineEdit()
        self.password.setPlaceholderText("Password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.password.setStyleSheet("""
            QLineEdit {
                padding: 10px; padding-right: 35px; border: 1px solid #CCC; border-radius: 5px; 
                color: black; background-color: white;
            }
        """)

        # --- Password Toggle Action ---
        self.toggle_password_action = QAction(self)
        self.toggle_password_action.setText("👁")
        self.password.addAction(self.toggle_password_action, QLineEdit.ActionPosition.TrailingPosition)
        self.toggle_password_action.triggered.connect(self.toggle_password_visibility)

        # Login Button
        self.login_btn = QPushButton("LOGIN")
        self.login_btn.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #1B4D2E; color: white; padding: 12px; border-radius: 5px;
            }
            QPushButton:hover { background-color: #2D5A27; }
        """)
        self.login_btn.clicked.connect(self.check_login)

        # Forgot Password Button
        self.forgot_btn = QPushButton("Forgot Password?")
        self.forgot_btn.setFont(QFont("Arial", 10))
        self.forgot_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent; color: #1B4D2E; text-decoration: underline; border: none;
            }
            QPushButton:hover { color: #2D5A27; }
        """)
        self.forgot_btn.clicked.connect(self.show_forgot_password)

        # Status Message
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: red; border: none;")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.card_layout.addWidget(self.title)
        self.card_layout.addWidget(self.username)
        self.card_layout.addWidget(self.password)
        self.card_layout.addWidget(self.login_btn)
        self.card_layout.addWidget(self.forgot_btn)
        self.card_layout.addWidget(self.status_label)

        self.layout.addWidget(self.card)
        self.setLayout(self.layout)

    def toggle_password_visibility(self):
        """Switches the password field between dots and plain text."""
        if self.password_visible:
            self.password.setEchoMode(QLineEdit.EchoMode.Password)
            self.toggle_password_action.setText("👁")
            self.password_visible = False
        else:
            self.password.setEchoMode(QLineEdit.EchoMode.Normal)
            self.toggle_password_action.setText("🔒")
            self.password_visible = True

    def show_forgot_password(self):
        dialog = ForgotPasswordDialog(self)
        dialog.exec()

    def check_login(self):
        username = self.username.text().strip()
        password = self.password.text().strip()

        success, role = verify_admin(username, password)

        if success:
            self.status_label.setStyleSheet("color: green; border: none;")
            self.status_label.setText("Login Successful!")
            self.login_success.emit(role)
        else:
            self.status_label.setStyleSheet("color: red; border: none;")
            self.status_label.setText("Invalid Credentials")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AdminLogin()
    window.show()
    sys.exit(app.exec())