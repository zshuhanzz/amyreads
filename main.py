"""
AmyReads - Lightweight AI PDF Reader
Main entry point
"""

import sys
import os

# Fix for PyInstaller single-file mode
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    app_dir = os.path.dirname(sys.executable)
else:
    app_dir = os.path.dirname(os.path.abspath(__file__))

os.chdir(app_dir)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QIcon, QFont

from home_screen import HomeScreen
from settings_manager import SettingsManager


def main():
    # Enable high DPI support
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("AmyReads")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("AmyReads")

    # Initialize settings
    settings = SettingsManager()

    # Apply theme
    theme = settings.get("appearance/theme", "light")
    apply_theme(app, theme)

    # Show home screen
    window = HomeScreen(settings)
    window.show()

    sys.exit(app.exec())


def apply_theme(app: QApplication, theme: str):
    """Apply light or dark theme to the application."""
    if theme == "dark":
        app.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1e1e2e;
                color: #cdd6f4;
            }
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #45475a;
            }
            QPushButton:pressed {
                background-color: #585b70;
            }
            QPushButton:disabled {
                background-color: #2a2a3c;
                color: #6c7086;
            }
            QScrollBar:vertical {
                background: #1e1e2e;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background: #45475a;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QComboBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 5px;
                padding: 4px 8px;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox QAbstractItemView {
                background-color: #313244;
                color: #cdd6f4;
                selection-background-color: #45475a;
            }
            QLabel {
                color: #cdd6f4;
            }
            QLineEdit {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 5px;
                padding: 5px 8px;
            }
            QSpinBox {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 5px;
                padding: 4px;
            }
            QSlider::groove:horizontal {
                background: #45475a;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #89b4fa;
                width: 14px;
                height: 14px;
                border-radius: 7px;
                margin: -5px 0;
            }
            QGroupBox {
                border: 1px solid #45475a;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 8px;
                color: #cdd6f4;
            }
            QGroupBox::title {
                color: #89b4fa;
            }
            QTabWidget::pane {
                border: 1px solid #45475a;
            }
            QTabBar::tab {
                background-color: #313244;
                color: #cdd6f4;
                padding: 8px 16px;
                border: 1px solid #45475a;
            }
            QTabBar::tab:selected {
                background-color: #45475a;
                color: #cdd6f4;
            }
            QCheckBox {
                color: #cdd6f4;
            }
        """)
    else:
        app.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #f8f9fa;
                color: #212529;
            }
            QPushButton {
                background-color: #e9ecef;
                color: #212529;
                border: 1px solid #ced4da;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #dee2e6;
            }
            QPushButton:pressed {
                background-color: #ced4da;
            }
            QPushButton:disabled {
                background-color: #f1f3f5;
                color: #adb5bd;
            }
            QScrollBar:vertical {
                background: #f1f3f5;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background: #adb5bd;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QComboBox {
                background-color: #ffffff;
                color: #212529;
                border: 1px solid #ced4da;
                border-radius: 5px;
                padding: 4px 8px;
            }
            QComboBox QAbstractItemView {
                background-color: #ffffff;
                color: #212529;
                selection-background-color: #e9ecef;
            }
            QLineEdit {
                background-color: #ffffff;
                color: #212529;
                border: 1px solid #ced4da;
                border-radius: 5px;
                padding: 5px 8px;
            }
            QSpinBox {
                background-color: #ffffff;
                color: #212529;
                border: 1px solid #ced4da;
                border-radius: 5px;
                padding: 4px;
            }
            QSlider::groove:horizontal {
                background: #ced4da;
                height: 4px;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #4361ee;
                width: 14px;
                height: 14px;
                border-radius: 7px;
                margin: -5px 0;
            }
            QGroupBox {
                border: 1px solid #dee2e6;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 8px;
            }
            QGroupBox::title {
                color: #4361ee;
            }
            QTabWidget::pane {
                border: 1px solid #dee2e6;
            }
            QTabBar::tab {
                background-color: #f1f3f5;
                color: #495057;
                padding: 8px 16px;
                border: 1px solid #dee2e6;
            }
            QTabBar::tab:selected {
                background-color: #ffffff;
                color: #212529;
            }
        """)


if __name__ == "__main__":
    main()
