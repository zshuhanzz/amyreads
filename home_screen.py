"""
AmyReads - Home Screen
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from settings_manager import SettingsManager


class HomeScreen(QMainWindow):
    def __init__(self, settings: SettingsManager):
        super().__init__()
        self.settings = settings
        self._reader_window = None

        self.setWindowTitle("AmyReads")
        self.setMinimumSize(560, 420)
        self.resize(620, 460)

        self._build_ui()
        self._center_window()

    def _center_window(self):
        screen = self.screen().availableGeometry()
        x = (screen.width() - self.width()) // 2
        y = (screen.height() - self.height()) // 2
        self.move(x, y)

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        outer = QVBoxLayout(central)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Top bar — Settings button only
        top_bar = QWidget()
        top_bar.setMaximumHeight(44)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(16, 8, 16, 8)
        top_layout.addStretch()
        settings_btn = QPushButton("Settings")
        settings_btn.setFixedWidth(80)
        settings_btn.clicked.connect(self._open_settings)
        top_layout.addWidget(settings_btn)
        outer.addWidget(top_bar)

        # Content
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(80, 24, 80, 48)
        layout.setSpacing(0)

        # Title
        title_lbl = QLabel("AmyReads")
        title_font = QFont()
        title_font.setPointSize(36)
        title_font.setBold(True)
        title_lbl.setFont(title_font)
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setStyleSheet("color: #4361ee; margin-bottom: 4px;")
        layout.addWidget(title_lbl)

        # Subtitle
        subtitle_lbl = QLabel("Make reading easier for Amy. Fuck PBL!")
        sub_font = QFont()
        sub_font.setPointSize(12)
        sub_font.setItalic(True)
        subtitle_lbl.setFont(sub_font)
        subtitle_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_lbl.setStyleSheet("color: #6c757d; margin-bottom: 28px;")
        layout.addWidget(subtitle_lbl)

        # Divider
        div = QFrame()
        div.setFrameShape(QFrame.Shape.HLine)
        div.setFixedHeight(1)
        div.setStyleSheet("background-color: #dee2e6; margin-bottom: 24px;")
        layout.addWidget(div)

        # Quick Guide card
        guide_frame = self._card_frame()
        guide_layout = QVBoxLayout(guide_frame)
        guide_layout.setContentsMargins(24, 18, 24, 18)
        guide_layout.setSpacing(8)

        guide_title = QLabel("Quick Guide")
        guide_title.setStyleSheet("font-size: 13px; font-weight: bold; margin-bottom: 4px;")
        guide_layout.addWidget(guide_title)

        steps = [
            "1.  Open a PDF textbook.",
            "2.  Choose a reading mode to improve readability.",
            "3.  Adjust contrast, spacing, and reading focus.",
            "4.  Optionally use AI to highlight key concepts or summarize a selected section.",
        ]
        for step in steps:
            lbl = QLabel(step)
            lbl.setWordWrap(True)
            lbl.setStyleSheet("font-size: 12px; color: #495057; padding: 1px 0;")
            guide_layout.addWidget(lbl)

        layout.addWidget(guide_frame)
        layout.addSpacing(28)

        # Open PDF button
        open_btn = QPushButton("Open PDF")
        open_btn.setFixedHeight(48)
        open_btn.setFixedWidth(200)
        open_btn.setStyleSheet("""
            QPushButton {
                background-color: #4361ee;
                color: white;
                font-size: 15px;
                font-weight: bold;
                border: none;
                border-radius: 7px;
            }
            QPushButton:hover  { background-color: #3451d1; }
            QPushButton:pressed { background-color: #2840c0; }
        """)
        open_btn.clicked.connect(self._open_pdf)

        btn_wrapper = QHBoxLayout()
        btn_wrapper.addStretch()
        btn_wrapper.addWidget(open_btn)
        btn_wrapper.addStretch()
        layout.addLayout(btn_wrapper)

        outer.addWidget(content)

    def _card_frame(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        frame.setFrameShape(QFrame.Shape.Box)
        theme = self.settings.get("appearance/theme", "light")
        if theme == "dark":
            frame.setStyleSheet("""
                QFrame#card {
                    background-color: #313244;
                    border: 1px solid #45475a;
                    border-radius: 8px;
                }
            """)
        else:
            frame.setStyleSheet("""
                QFrame#card {
                    background-color: #ffffff;
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                }
            """)
        frame.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        return frame

    def _open_pdf(self):
        from PySide6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, "Open PDF", "", "PDF Files (*.pdf)"
        )
        if path:
            self._launch_reader(path)

    def _launch_reader(self, pdf_path: str):
        from reader_window import ReaderWindow
        if self._reader_window is not None:
            self._reader_window.close()
        self._reader_window = ReaderWindow(pdf_path, self.settings)
        self._reader_window.show()
        self.hide()
        self._reader_window.closed.connect(self._on_reader_closed)

    def _on_reader_closed(self):
        self._reader_window = None
        self.show()

    def _open_settings(self):
        from settings_dialog import SettingsDialog
        from main import apply_theme
        dlg = SettingsDialog(self.settings, self)
        if dlg.exec():
            theme = self.settings.get("appearance/theme", "light")
            from PySide6.QtWidgets import QApplication
            apply_theme(QApplication.instance(), theme)
