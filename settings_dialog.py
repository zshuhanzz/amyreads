"""
AmyReads - Settings Dialog
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QLabel, QPushButton, QComboBox, QSlider, QSpinBox,
    QCheckBox, QLineEdit, QGroupBox, QFormLayout,
    QMessageBox, QSizePolicy, QDoubleSpinBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from settings_manager import SettingsManager
from cache_manager import CacheManager


class SettingsDialog(QDialog):
    def __init__(self, settings: SettingsManager, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Settings — AmyReads")
        self.setMinimumWidth(480)
        self.setMinimumHeight(400)
        self.resize(520, 460)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        tabs = QTabWidget()
        tabs.addTab(self._build_appearance_tab(), "Appearance")
        tabs.addTab(self._build_reading_tab(), "Reading")
        tabs.addTab(self._build_ai_tab(), "AI")
        layout.addWidget(tabs)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        ok_btn = QPushButton("OK")
        ok_btn.setDefault(True)
        ok_btn.clicked.connect(self._save_and_accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(ok_btn)
        layout.addLayout(btn_layout)

    # ── Appearance Tab ────────────────────────────────────────────────────────

    def _build_appearance_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(16)

        # Theme
        theme_group = QGroupBox("Theme")
        tl = QFormLayout(theme_group)
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark"])
        current_theme = self.settings.get("appearance/theme", "light")
        self.theme_combo.setCurrentText(current_theme)
        tl.addRow("Theme:", self.theme_combo)
        layout.addWidget(theme_group)

        # Font & Spacing
        font_group = QGroupBox("Text (Clean Text / Bionic modes)")
        fl = QFormLayout(font_group)

        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 28)
        self.font_size_spin.setValue(self.settings.get_int("appearance/font_size", 13))
        fl.addRow("Font size (pt):", self.font_size_spin)

        self.line_spacing_spin = QDoubleSpinBox()
        self.line_spacing_spin.setRange(1.0, 3.0)
        self.line_spacing_spin.setSingleStep(0.1)
        self.line_spacing_spin.setDecimals(1)
        self.line_spacing_spin.setValue(self.settings.get_float("appearance/line_spacing", 1.6))
        fl.addRow("Line spacing:", self.line_spacing_spin)

        self.column_width_spin = QSpinBox()
        self.column_width_spin.setRange(300, 1200)
        self.column_width_spin.setSingleStep(50)
        self.column_width_spin.setValue(self.settings.get_int("reading/column_width", 700))
        fl.addRow("Column width (px):", self.column_width_spin)

        layout.addWidget(font_group)

        # Contrast
        contrast_group = QGroupBox("Contrast (High Contrast mode)")
        cl = QVBoxLayout(contrast_group)
        contrast_row = QHBoxLayout()
        contrast_lbl = QLabel("Contrast:")
        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setRange(50, 200)
        self.contrast_slider.setValue(int(self.settings.get_float("appearance/contrast", 1.0) * 100))
        self.contrast_val_lbl = QLabel(f"{self.contrast_slider.value()}%")
        self.contrast_slider.valueChanged.connect(
            lambda v: self.contrast_val_lbl.setText(f"{v}%")
        )
        contrast_row.addWidget(contrast_lbl)
        contrast_row.addWidget(self.contrast_slider)
        contrast_row.addWidget(self.contrast_val_lbl)
        cl.addLayout(contrast_row)
        layout.addWidget(contrast_group)

        layout.addStretch()
        return w

    # ── Reading Tab ───────────────────────────────────────────────────────────

    def _build_reading_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(16)

        reading_group = QGroupBox("Reading Preferences")
        rl = QFormLayout(reading_group)

        from reading_modes import ReadingModeSelector
        self.default_mode_combo = QComboBox()
        self.default_mode_combo.addItems(ReadingModeSelector.MODES)
        default_mode = self.settings.get("reading/default_mode", "Original")
        self.default_mode_combo.setCurrentText(default_mode)
        rl.addRow("Default reading mode:", self.default_mode_combo)

        self.ruler_height_spin = QSpinBox()
        self.ruler_height_spin.setRange(16, 80)
        self.ruler_height_spin.setValue(self.settings.get_int("reading/ruler_height", 32))
        self.ruler_height_spin.setSuffix(" px")
        rl.addRow("Line focus ruler height:", self.ruler_height_spin)

        self.remember_page_check = QCheckBox("Remember last page per PDF")
        self.remember_page_check.setChecked(
            self.settings.get_bool("reading/remember_last_page", True)
        )
        rl.addRow(self.remember_page_check)

        layout.addWidget(reading_group)
        layout.addStretch()
        return w

    # ── AI Tab ────────────────────────────────────────────────────────────────

    def _build_ai_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(16)

        ai_group = QGroupBox("Gemini AI")
        al = QVBoxLayout(ai_group)

        key_row = QHBoxLayout()
        key_lbl = QLabel("API Key:")
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("AIza...")
        self.api_key_edit.setText(self.settings.get("ai/gemini_api_key", ""))
        show_btn = QPushButton("👁")
        show_btn.setFixedWidth(30)
        show_btn.setCheckable(True)
        show_btn.toggled.connect(
            lambda checked: self.api_key_edit.setEchoMode(
                QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
            )
        )
        key_row.addWidget(key_lbl)
        key_row.addWidget(self.api_key_edit)
        key_row.addWidget(show_btn)
        al.addLayout(key_row)

        key_hint = QLabel(
            '<a href="https://aistudio.google.com/app/apikey" style="color:#4361ee;">'
            'Get a free Gemini API key</a>'
        )
        key_hint.setOpenExternalLinks(True)
        key_hint.setStyleSheet("font-size: 11px;")
        al.addWidget(key_hint)

        test_btn = QPushButton("Test API Key")
        test_btn.clicked.connect(self._test_api_key)
        al.addWidget(test_btn)

        self.test_result_lbl = QLabel("")
        self.test_result_lbl.setWordWrap(True)
        al.addWidget(self.test_result_lbl)

        layout.addWidget(ai_group)

        # Cache
        cache_group = QGroupBox("Highlight Cache")
        cl = QVBoxLayout(cache_group)
        cache = CacheManager()
        size_kb = cache.cache_size_kb()
        self.cache_size_lbl = QLabel(f"Cache size: {size_kb} KB")
        cl.addWidget(self.cache_size_lbl)
        clear_btn = QPushButton("Clear All Cached Highlights")
        clear_btn.clicked.connect(self._clear_cache)
        cl.addWidget(clear_btn)
        layout.addWidget(cache_group)

        layout.addStretch()
        return w

    def _test_api_key(self):
        api_key = self.api_key_edit.text().strip()
        if not api_key:
            self.test_result_lbl.setText("⚠ Please enter an API key first.")
            return
        self.test_result_lbl.setText("Testing…")
        from PySide6.QtWidgets import QApplication
        QApplication.processEvents()

        from ai_highlighter import test_api_key
        success, msg = test_api_key(api_key)
        if success:
            self.test_result_lbl.setStyleSheet("color: #059669;")
        else:
            self.test_result_lbl.setStyleSheet("color: #dc2626;")
        self.test_result_lbl.setText(msg)

    def _clear_cache(self):
        reply = QMessageBox.question(
            self, "Clear Cache",
            "Clear all cached AI highlights?\nThis cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            CacheManager().clear_all()
            self.cache_size_lbl.setText("Cache size: 0 KB")
            QMessageBox.information(self, "Done", "Highlight cache cleared.")

    # ── Save ──────────────────────────────────────────────────────────────────

    def _save_and_accept(self):
        s = self.settings

        # Appearance
        s.set("appearance/theme", self.theme_combo.currentText())
        s.set("appearance/font_size", self.font_size_spin.value())
        s.set("appearance/line_spacing", self.line_spacing_spin.value())
        s.set("appearance/contrast", self.contrast_slider.value() / 100.0)

        # Reading
        s.set("reading/default_mode", self.default_mode_combo.currentText())
        s.set("reading/ruler_height", self.ruler_height_spin.value())
        s.set("reading/remember_last_page", self.remember_page_check.isChecked())
        s.set("reading/column_width", self.column_width_spin.value())

        # AI
        s.set("ai/gemini_api_key", self.api_key_edit.text().strip())

        self.accept()
