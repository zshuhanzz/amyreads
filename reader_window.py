"""
AmyReads - Main Reader Window
PDF viewer with reading modes, navigation, zoom, and AI highlighting.
"""

import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QScrollArea,
    QSizePolicy, QToolBar, QStatusBar, QSpinBox,
    QFrame, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal, QThread, QTimer, QPoint
from PySide6.QtGui import QFont, QKeySequence, QShortcut, QPixmap, QAction

from settings_manager import SettingsManager
from pdf_viewer import PDFViewer
from reading_modes import ReadingModeSelector


class ReaderWindow(QMainWindow):
    closed = Signal()

    def __init__(self, pdf_path: str, settings: SettingsManager):
        super().__init__()
        self.pdf_path = pdf_path
        self.settings = settings

        self.setWindowTitle(f"AmyReads — {os.path.basename(pdf_path)}")
        self.setMinimumSize(900, 700)
        self.resize(1200, 850)

        self._build_ui()
        self._setup_shortcuts()
        self._load_pdf(pdf_path)

    def _build_ui(self):
        # ── Toolbar ──────────────────────────────────────────────────────────
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        toolbar.setFloatable(False)
        toolbar.setStyleSheet("""
            QToolBar {
                spacing: 6px;
                padding: 4px 8px;
                border-bottom: 1px solid #dee2e6;
            }
        """)
        self.addToolBar(toolbar)

        # Navigation
        self.prev_btn = QPushButton("◀ Prev")
        self.prev_btn.setFixedWidth(72)
        self.prev_btn.clicked.connect(self._prev_page)
        toolbar.addWidget(self.prev_btn)

        self.page_spin = QSpinBox()
        self.page_spin.setMinimum(1)
        self.page_spin.setFixedWidth(60)
        self.page_spin.valueChanged.connect(self._go_to_page)
        toolbar.addWidget(self.page_spin)

        self.total_pages_lbl = QLabel("/ 1")
        self.total_pages_lbl.setStyleSheet("padding: 0 4px;")
        toolbar.addWidget(self.total_pages_lbl)

        self.next_btn = QPushButton("Next ▶")
        self.next_btn.setFixedWidth(72)
        self.next_btn.clicked.connect(self._next_page)
        toolbar.addWidget(self.next_btn)

        toolbar.addSeparator()

        # Zoom
        zoom_out_btn = QPushButton("−")
        zoom_out_btn.setFixedWidth(32)
        zoom_out_btn.clicked.connect(self._zoom_out)
        toolbar.addWidget(zoom_out_btn)

        self.zoom_lbl = QLabel("100%")
        self.zoom_lbl.setFixedWidth(48)
        self.zoom_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        toolbar.addWidget(self.zoom_lbl)

        zoom_in_btn = QPushButton("+")
        zoom_in_btn.setFixedWidth(32)
        zoom_in_btn.clicked.connect(self._zoom_in)
        toolbar.addWidget(zoom_in_btn)

        fit_btn = QPushButton("Fit Width")
        fit_btn.setFixedWidth(80)
        fit_btn.clicked.connect(self._fit_width)
        toolbar.addWidget(fit_btn)

        toolbar.addSeparator()

        # Reading mode selector
        mode_lbl = QLabel("Mode:")
        toolbar.addWidget(mode_lbl)
        self.mode_combo = QComboBox()
        self.mode_combo.setFixedWidth(160)
        self.mode_combo.addItems([
            "Original",
            "High Contrast",
            "Line Focus",
            "Bionic Reading",
            "Clean Text",
        ])
        default_mode = self.settings.get("reading/default_mode", "Original")
        idx = self.mode_combo.findText(default_mode)
        if idx >= 0:
            self.mode_combo.setCurrentIndex(idx)
        self.mode_combo.currentTextChanged.connect(self._on_mode_changed)
        toolbar.addWidget(self.mode_combo)

        toolbar.addSeparator()

        # AI button
        self.ai_btn = QPushButton("AI Highlight")
        self.ai_btn.setFixedWidth(120)
        self.ai_btn.setStyleSheet("""
            QPushButton {
                background-color: #7c3aed;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
                font-size: 12px;
            }
            QPushButton:hover { background-color: #6d28d9; }
            QPushButton:pressed { background-color: #5b21b6; }
            QPushButton:disabled { background-color: #c4b5fd; }
        """)
        self.ai_btn.clicked.connect(self._run_ai_highlight)
        toolbar.addWidget(self.ai_btn)

        # Settings button
        toolbar.addSeparator()
        settings_btn = QPushButton("Settings")
        settings_btn.setFixedWidth(70)
        settings_btn.setToolTip("Settings")
        settings_btn.clicked.connect(self._open_settings)
        toolbar.addWidget(settings_btn)

        # ── Central area ─────────────────────────────────────────────────────
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # PDF Viewer
        self.pdf_viewer = PDFViewer(self.settings)
        self.pdf_viewer.page_changed.connect(self._on_page_changed)
        main_layout.addWidget(self.pdf_viewer)

        # Status bar
        self.status_bar = QStatusBar()
        self.status_bar.setMaximumHeight(24)
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Left"), self, self._prev_page)
        QShortcut(QKeySequence("Right"), self, self._next_page)
        QShortcut(QKeySequence("Ctrl+Plus"), self, self._zoom_in)
        QShortcut(QKeySequence("Ctrl+Minus"), self, self._zoom_out)
        QShortcut(QKeySequence("Ctrl+0"), self, self._fit_width)

    def _load_pdf(self, path: str):
        try:
            self.pdf_viewer.load_pdf(path)
            total = self.pdf_viewer.total_pages()
            self.page_spin.setMaximum(total)
            self.total_pages_lbl.setText(f"/ {total}")

            # Restore last page
            if self.settings.get_bool("reading/remember_last_page", True):
                key = f"last_page/{os.path.abspath(path)}"
                last = self.settings.get_int(key, 1)
                if 1 <= last <= total:
                    self.pdf_viewer.go_to_page(last)
                    self.page_spin.setValue(last)

            self._on_mode_changed(self.mode_combo.currentText())
            self.status_bar.showMessage(f"Loaded: {os.path.basename(path)}  ({total} pages)")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Could not load PDF:\n{e}")

    def _prev_page(self):
        current = self.pdf_viewer.current_page()
        if current > 1:
            self.pdf_viewer.go_to_page(current - 1)

    def _next_page(self):
        current = self.pdf_viewer.current_page()
        if current < self.pdf_viewer.total_pages():
            self.pdf_viewer.go_to_page(current + 1)

    def _go_to_page(self, page: int):
        self.pdf_viewer.go_to_page(page)

    def _on_page_changed(self, page: int):
        self.page_spin.blockSignals(True)
        self.page_spin.setValue(page)
        self.page_spin.blockSignals(False)
        self.status_bar.showMessage(f"Page {page} / {self.pdf_viewer.total_pages()}")

        # Save last page
        if self.settings.get_bool("reading/remember_last_page", True):
            key = f"last_page/{os.path.abspath(self.pdf_path)}"
            self.settings.set(key, page)

    def _zoom_in(self):
        self.pdf_viewer.zoom_in()
        self.zoom_lbl.setText(f"{int(self.pdf_viewer.zoom * 100)}%")

    def _zoom_out(self):
        self.pdf_viewer.zoom_out()
        self.zoom_lbl.setText(f"{int(self.pdf_viewer.zoom * 100)}%")

    def _fit_width(self):
        self.pdf_viewer.fit_width()
        self.zoom_lbl.setText(f"{int(self.pdf_viewer.zoom * 100)}%")

    def _on_mode_changed(self, mode: str):
        self.pdf_viewer.set_mode(mode)
        self.zoom_lbl.setText(f"{int(self.pdf_viewer.zoom * 100)}%")
        self.status_bar.showMessage(f"Mode: {mode}")

    def _run_ai_highlight(self):
        api_key = self.settings.get("ai/gemini_api_key", "")
        if not api_key:
            QMessageBox.information(
                self,
                "API Key Required",
                "Please enter your Gemini API key in Settings → AI to use AI highlighting."
            )
            return

        from ai_highlighter import AIHighlighter, AIWorker
        page_text = self.pdf_viewer.get_current_page_text()
        if not page_text.strip():
            QMessageBox.information(
                self, "No Text",
                "No extractable text found on this page.\n"
                "AI highlighting works on text-based PDFs only."
            )
            return

        # Check cache first
        from cache_manager import CacheManager
        cache = CacheManager()
        page_num = self.pdf_viewer.current_page()
        cached = cache.get_highlights(self.pdf_path, page_num)
        if cached is not None:
            self.pdf_viewer.apply_highlights(cached)
            self.status_bar.showMessage("Highlights loaded from cache.")
            return

        self.ai_btn.setEnabled(False)
        self.ai_btn.setText("Processing…")
        self.status_bar.showMessage("Sending page to Gemini AI…")

        self._ai_worker = AIWorker(api_key, page_text)
        self._ai_worker.finished.connect(
            lambda highlights: self._on_ai_done(highlights, page_num, cache)
        )
        self._ai_worker.error.connect(self._on_ai_error)
        self._ai_worker.start()

    def _on_ai_done(self, highlights: list, page_num: int, cache):
        self.pdf_viewer.apply_highlights(highlights)
        cache.save_highlights(self.pdf_path, page_num, highlights)
        self.ai_btn.setEnabled(True)
        self.ai_btn.setText("AI Highlight")
        n = len(highlights)
        if n == 0:
            self.status_bar.showMessage(
                "AI found no highlights to display. "
                "Try a page with more text, or check that the PDF has selectable text."
            )
        else:
            self.status_bar.showMessage(
                f"AI highlighted {n} item(s) — "
                "🔵 key concepts  🟢 definitions  🟡 facts  🟣 examples"
            )

    def _on_ai_error(self, error_msg: str):
        self.ai_btn.setEnabled(True)
        self.ai_btn.setText("AI Highlight")
        self.status_bar.showMessage("AI error — see details.")
        QMessageBox.warning(self, "AI Error", error_msg)

    def _open_settings(self):
        from settings_dialog import SettingsDialog
        from main import apply_theme
        dlg = SettingsDialog(self.settings, self)
        if dlg.exec():
            theme = self.settings.get("appearance/theme", "light")
            from PySide6.QtWidgets import QApplication
            apply_theme(QApplication.instance(), theme)
            # Refresh viewer with new settings
            self.pdf_viewer.refresh_settings()

    def closeEvent(self, event):
        self.closed.emit()
        super().closeEvent(event)
