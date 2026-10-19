"""
AmyReads - PDF Viewer Widget
Handles rendering, navigation, zoom, reading modes, and AI highlight overlays.
"""

import re
from typing import Optional, List, Dict
from PySide6.QtWidgets import (
    QWidget, QScrollArea, QVBoxLayout, QHBoxLayout,
    QLabel, QSizePolicy, QApplication, QRubberBand,
    QPushButton, QFrame
)
from PySide6.QtCore import (
    Qt, Signal, QSize, QRect, QPoint, QTimer, QThread
)
from PySide6.QtGui import (
    QPixmap, QPainter, QColor, QPen, QBrush, QFont,
    QTextDocument, QImage, QPalette, QCursor
)

try:
    import pymupdf as fitz  # PyMuPDF >= 1.24
    FITZ_AVAILABLE = True
except ImportError:
    try:
        import fitz  # Older PyMuPDF
        FITZ_AVAILABLE = True
    except ImportError:
        FITZ_AVAILABLE = False

from settings_manager import SettingsManager


# ─── Highlight colour map ─────────────────────────────────────────────────────
HIGHLIGHT_COLORS = {
    "key_concept": QColor(100, 149, 237, 120),   # Blue
    "definition":  QColor(60,  179, 113, 120),   # Green
    "fact":        QColor(255, 215,   0, 130),   # Yellow
    "example":     QColor(147,  51, 234, 110),   # Purple
}

HIGHLIGHT_LABEL_COLORS = {
    "key_concept": "#4361ee",
    "definition":  "#059669",
    "fact":        "#d97706",
    "example":     "#7c3aed",
}


class PageLabel(QLabel):
    """
    A QLabel that renders a single PDF page and draws highlight overlays.
    Also handles Line Focus mode overlay and text-selection for AI summarize.
    """
    ai_summarize_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMouseTracking(True)

        self._highlights: List[Dict] = []
        self._line_focus_enabled = False
        self._line_focus_height = 32  # px
        self._mouse_y = -1

        # Text selection for AI summarize
        self._selection_start: Optional[QPoint] = None
        self._selection_rect: Optional[QRect] = None
        self._selected_text: str = ""
        self._page_text_blocks: List[Dict] = []  # [{rect, text}]

        # AI summarize bubble
        self._bubble_text: str = ""
        self._bubble_visible: bool = False

        # Contrast overlay
        self._contrast_mode: bool = False
        self._contrast_value: float = 1.0
        self._theme: str = "light"

    def set_highlights(self, highlights: list, page_text_blocks: list):
        self._highlights = highlights
        self._page_text_blocks = page_text_blocks
        self.update()

    def set_line_focus(self, enabled: bool, height: int = 32):
        self._line_focus_enabled = enabled
        self._line_focus_height = height
        self.update()

    def set_contrast_mode(self, enabled: bool, contrast: float, theme: str):
        self._contrast_mode = enabled
        self._contrast_value = contrast
        self._theme = theme
        self.update()

    def show_ai_bubble(self, text: str):
        self._bubble_text = text
        self._bubble_visible = True
        self.update()

    def hide_bubble(self):
        self._bubble_visible = False
        self.update()

    def mouseMoveEvent(self, event):
        self._mouse_y = event.position().y()
        if self._line_focus_enabled:
            self.update()
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._selection_start = event.position().toPoint()
            self._selection_rect = None
            self._selected_text = ""
            self._bubble_visible = False
            self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self._selection_start:
            end = event.position().toPoint()
            self._selection_rect = QRect(self._selection_start, end).normalized()
            self._selected_text = self._extract_text_in_rect(self._selection_rect)
            self._selection_start = None
            self.update()
        super().mouseReleaseEvent(event)

    def _extract_text_in_rect(self, rect: QRect) -> str:
        """Collect text blocks whose rects intersect the drawn selection."""
        words = []
        for block in self._page_text_blocks:
            br = block.get("rect")
            if br and QRect(*br).intersects(rect):
                words.append(block.get("text", ""))
        return " ".join(words)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.pixmap() is None or self.pixmap().isNull():
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        px = self.pixmap()
        # Compute the actual pixmap offset inside the label (centred horizontally)
        px_x = (self.width() - px.width()) // 2
        px_y = 0

        # ── Contrast overlay ─────────────────────────────────────────────────
        if self._contrast_mode and self._theme == "dark":
            painter.fillRect(px_x, px_y, px.width(), px.height(),
                             QColor(0, 0, 0, 80))

        # ── AI highlights ─────────────────────────────────────────────────────
        for h in self._highlights:
            rects = h.get("rects", [])
            htype = h.get("type", "fact")
            color = HIGHLIGHT_COLORS.get(htype, HIGHLIGHT_COLORS["fact"])
            for r in rects:
                draw_r = QRect(
                    int(r[0] + px_x), int(r[1] + px_y),
                    int(r[2] - r[0]), int(r[3] - r[1])
                )
                painter.fillRect(draw_r, color)

        # ── Line focus overlay ────────────────────────────────────────────────
        if self._line_focus_enabled and self._mouse_y >= 0:
            h = self._line_focus_height
            y_center = self._mouse_y
            # Dim above
            if y_center - h // 2 > px_y:
                painter.fillRect(px_x, px_y,
                                 px.width(), y_center - h // 2 - px_y,
                                 QColor(0, 0, 0, 70))
            # Dim below
            bottom = px_y + px.height()
            if y_center + h // 2 < bottom:
                painter.fillRect(px_x, y_center + h // 2,
                                 px.width(), bottom - (y_center + h // 2),
                                 QColor(0, 0, 0, 70))
            # Highlight strip border
            pen = QPen(QColor(255, 200, 0, 180), 1)
            painter.setPen(pen)
            painter.drawRect(px_x, y_center - h // 2,
                             px.width() - 1, h)
            painter.setPen(Qt.PenStyle.NoPen)

        # ── Text selection ─────────────────────────────────────────────────────
        if self._selection_rect:
            sel_color = QColor(66, 135, 245, 60)
            painter.fillRect(self._selection_rect, sel_color)
            painter.setPen(QPen(QColor(66, 135, 245, 180), 1))
            painter.drawRect(self._selection_rect)

            # Show "AI Summarize" button indicator if text was selected
            if self._selected_text.strip():
                btn_rect = QRect(
                    self._selection_rect.right() - 110,
                    self._selection_rect.bottom() + 4,
                    110, 26
                )
                painter.fillRect(btn_rect, QColor(124, 58, 237))
                painter.setPen(QColor(255, 255, 255))
                fnt = QFont()
                fnt.setPointSize(9)
                painter.setFont(fnt)
                painter.drawText(btn_rect, Qt.AlignmentFlag.AlignCenter, "AI Summarize")
                painter.setPen(Qt.PenStyle.NoPen)

        # ── AI Summary bubble ─────────────────────────────────────────────────
        if self._bubble_visible and self._bubble_text:
            self._draw_bubble(painter)

        painter.end()

    def _draw_bubble(self, painter: QPainter):
        margin = 16
        max_w = min(self.width() - 2 * margin, 480)
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        fm = painter.fontMetrics()
        lines = self._wrap_text(self._bubble_text, fm, max_w - 20)
        line_h = fm.height() + 3
        bubble_h = len(lines) * line_h + 20
        bubble_w = min(max(fm.horizontalAdvance(max(lines, key=len)) + 24, 200), max_w)
        bx = (self.width() - bubble_w) // 2
        by = max(margin, self._mouse_y - bubble_h - 12)

        # Shadow
        painter.setBrush(QColor(0, 0, 0, 40))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(bx + 3, by + 3, bubble_w, bubble_h, 8, 8)

        # Bubble background
        painter.setBrush(QColor(30, 30, 50, 230))
        painter.setPen(QPen(QColor(124, 58, 237), 1))
        painter.drawRoundedRect(bx, by, bubble_w, bubble_h, 8, 8)

        # Title
        painter.setPen(QColor(167, 139, 250))
        title_fnt = QFont()
        title_fnt.setPointSize(9)
        title_fnt.setBold(True)
        painter.setFont(title_fnt)
        painter.drawText(bx + 10, by + 14, "AI Summary")

        # Body
        painter.setPen(QColor(220, 220, 240))
        painter.setFont(font)
        y = by + 26
        for line in lines:
            painter.drawText(bx + 10, y + line_h - 4, line)
            y += line_h

        # Close hint
        close_fnt = QFont()
        close_fnt.setPointSize(8)
        painter.setFont(close_fnt)
        painter.setPen(QColor(150, 150, 180))
        painter.drawText(bx + bubble_w - 22, by + 14, "✕")

    def _wrap_text(self, text: str, fm, max_w: int) -> List[str]:
        words = text.split()
        lines = []
        current = ""
        for word in words:
            test = (current + " " + word).strip()
            if fm.horizontalAdvance(test) <= max_w:
                current = test
            else:
                if current:
                    lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines or [""]

    def mouseDoubleClickEvent(self, event):
        """Double-click dismisses the summary bubble."""
        self._bubble_visible = False
        self.update()
        super().mouseDoubleClickEvent(event)


# ─── PDF Viewer ───────────────────────────────────────────────────────────────

class PDFViewer(QScrollArea):
    page_changed = Signal(int)

    def __init__(self, settings: SettingsManager):
        super().__init__()
        self.settings = settings
        self._doc: Optional["fitz.Document"] = None
        self._current_page: int = 1
        self._zoom: float = 1.0
        self._mode: str = "Original"
        self._highlights: List[Dict] = []

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Container for the page label
        container = QWidget()
        container.setObjectName("pdfContainer")
        self._container_layout = QVBoxLayout(container)
        self._container_layout.setContentsMargins(16, 16, 16, 16)
        self._container_layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        self._page_label = PageLabel()
        self._page_label.ai_summarize_requested.connect(self._handle_ai_summarize)
        self._container_layout.addWidget(self._page_label)

        # Clean text view (shown in Clean Text / Bionic Reading modes)
        self._text_view = QLabel()
        self._text_view.setWordWrap(True)
        self._text_view.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self._text_view.setTextFormat(Qt.TextFormat.RichText)
        self._text_view.setVisible(False)
        self._text_view.setObjectName("textView")
        self._container_layout.addWidget(self._text_view)

        self.setWidget(container)

        # Timer for smooth resize
        self._resize_timer = QTimer()
        self._resize_timer.setSingleShot(True)
        self._resize_timer.timeout.connect(self._render_current_page)

        # Mouse tracking for line focus
        self.setMouseTracking(True)
        container.setMouseTracking(True)
        self._page_label.setMouseTracking(True)

        # AI summarize worker reference
        self._ai_worker = None

    @property
    def zoom(self) -> float:
        return self._zoom

    def load_pdf(self, path: str):
        if not FITZ_AVAILABLE:
            self._page_label.setText(
                "PyMuPDF (fitz) is not installed.\n"
                "Run: pip install pymupdf"
            )
            return
        if self._doc:
            self._doc.close()
        self._doc = fitz.open(path)
        self._current_page = 1
        self._highlights = []
        self._render_current_page()

    def total_pages(self) -> int:
        return len(self._doc) if self._doc else 0

    def current_page(self) -> int:
        return self._current_page

    def go_to_page(self, page: int):
        if not self._doc:
            return
        page = max(1, min(page, len(self._doc)))
        if page != self._current_page:
            self._current_page = page
            self._highlights = []  # Clear highlights on page change
            self._render_current_page()
            self.page_changed.emit(page)
            self.verticalScrollBar().setValue(0)

    def zoom_in(self):
        self._zoom = min(self._zoom * 1.2, 5.0)
        self._render_current_page()

    def zoom_out(self):
        self._zoom = max(self._zoom / 1.2, 0.2)
        self._render_current_page()

    def fit_width(self):
        if not self._doc:
            return
        page = self._doc[self._current_page - 1]
        page_w = page.rect.width
        avail_w = self.viewport().width() - 40
        self._zoom = avail_w / page_w
        self._render_current_page()

    def set_mode(self, mode: str):
        self._mode = mode
        self._render_current_page()

    def refresh_settings(self):
        self._render_current_page()

    def get_current_page_text(self) -> str:
        if not self._doc:
            return ""
        page = self._doc[self._current_page - 1]
        return page.get_text("text")

    def apply_highlights(self, highlights: list):
        self._highlights = highlights
        self._render_current_page()

    def _render_current_page(self):
        if not self._doc or not FITZ_AVAILABLE:
            return

        page_idx = self._current_page - 1
        page = self._doc[page_idx]
        mode = self._mode

        # ── Text-only modes ───────────────────────────────────────────────────
        if mode in ("Clean Text", "Bionic Reading"):
            self._page_label.setVisible(False)
            self._text_view.setVisible(True)
            html = self._render_text_mode(page, mode)
            self._text_view.setText(html)
            self._apply_text_view_style()
            return

        # ── Raster modes ──────────────────────────────────────────────────────
        self._page_label.setVisible(True)
        self._text_view.setVisible(False)

        mat = fitz.Matrix(self._zoom, self._zoom)

        # High contrast: invert colours for dark theme
        if mode == "High Contrast":
            contrast = self.settings.get_float("appearance/contrast", 1.0)
            theme = self.settings.get("appearance/theme", "light")
            clip = None
            pixmap = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB, alpha=False)
            img = QImage(
                pixmap.samples, pixmap.width, pixmap.height,
                pixmap.stride, QImage.Format.Format_RGB888
            ).copy()
            if theme == "dark":
                img.invertPixels()
            qpix = QPixmap.fromImage(img)
            self._page_label.set_contrast_mode(True, contrast, theme)
        else:
            pixmap = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB, alpha=False)
            img = QImage(
                pixmap.samples, pixmap.width, pixmap.height,
                pixmap.stride, QImage.Format.Format_RGB888
            ).copy()
            qpix = QPixmap.fromImage(img)
            self._page_label.set_contrast_mode(False, 1.0,
                self.settings.get("appearance/theme", "light"))

        self._page_label.setPixmap(qpix)
        self._page_label.setFixedSize(qpix.size())

        # ── Apply line focus ──────────────────────────────────────────────────
        line_focus = (mode == "Line Focus")
        ruler_h = self.settings.get_int("reading/ruler_height", 32)
        self._page_label.set_line_focus(line_focus, ruler_h)

        # ── Map highlight phrases → pixel rects ───────────────────────────────
        if self._highlights:
            mapped = self._map_highlights_to_rects(page, self._highlights)
            text_blocks = self._get_text_blocks(page)
            self._page_label.set_highlights(mapped, text_blocks)
        else:
            self._page_label.set_highlights([], [])

    def _get_text_blocks(self, page) -> List[Dict]:
        """Return word-level bounding boxes scaled to current zoom."""
        blocks = []
        words = page.get_text("words")
        for w in words:
            x0, y0, x1, y1, text = w[0], w[1], w[2], w[3], w[4]
            blocks.append({
                "rect": (
                    int(x0 * self._zoom), int(y0 * self._zoom),
                    int((x1 - x0) * self._zoom), int((y1 - y0) * self._zoom)
                ),
                "text": text
            })
        return blocks

    def _map_highlights_to_rects(self, page, highlights: list) -> list:
        """Search for highlight phrases in the page and return pixel rects.

        Tries multiple strategies for each phrase:
        1. Exact search (fast, most accurate)
        2. Case-insensitive search
        3. Normalised whitespace search
        4. First-word anchor search (fallback for long phrases)
        """
        mapped = []
        for h in highlights:
            phrase = h.get("text", "").strip()
            htype = h.get("type", "fact")
            if not phrase:
                continue

            rects = self._search_phrase(page, phrase)

            if rects:
                mapped.append({"type": htype, "rects": rects, "text": phrase})
        return mapped

    def _search_phrase(self, page, phrase: str) -> list:
        """Try multiple search strategies, return scaled rect tuples."""
        def scale(r):
            return (r.x0 * self._zoom, r.y0 * self._zoom,
                    r.x1 * self._zoom, r.y1 * self._zoom)

        # Strategy 1: exact match
        try:
            results = page.search_for(phrase)
            if results:
                return [scale(r) for r in results]
        except Exception:
            pass

        # Strategy 2: case-insensitive (quips flag)
        try:
            results = page.search_for(phrase, quads=False)
            if results:
                return [scale(r) for r in results]
        except Exception:
            pass

        # Strategy 3: normalise whitespace (collapse multiple spaces/newlines)
        import re as _re
        normalised = _re.sub(r'\s+', ' ', phrase).strip()
        if normalised != phrase:
            try:
                results = page.search_for(normalised)
                if results:
                    return [scale(r) for r in results]
            except Exception:
                pass

        # Strategy 4: search for the first meaningful chunk (≥3 words)
        words = phrase.split()
        if len(words) >= 4:
            # Try progressively shorter prefixes until we find a match
            for n in range(len(words), 2, -1):
                chunk = " ".join(words[:n])
                try:
                    results = page.search_for(chunk)
                    if results:
                        return [scale(r) for r in results]
                except Exception:
                    pass

        # Strategy 5: single-word fallback for short phrases
        if len(words) == 1 and len(words[0]) > 4:
            try:
                results = page.search_for(words[0])
                if results:
                    return [scale(r) for r in results[:3]]  # cap to avoid over-highlighting
            except Exception:
                pass

        return []

    def _render_text_mode(self, page, mode: str) -> str:
        """Extract text and format as HTML for Clean Text or Bionic Reading."""
        blocks = page.get_text("blocks")
        font_size = self.settings.get_int("appearance/font_size", 13)
        line_spacing = self.settings.get_float("appearance/line_spacing", 1.6)
        theme = self.settings.get("appearance/theme", "light")
        bg = "#1e1e2e" if theme == "dark" else "#fefefe"
        fg = "#cdd6f4" if theme == "dark" else "#212529"

        paragraphs = []
        for b in blocks:
            if b[6] == 0:  # text block
                text = b[4].strip()
                if text:
                    if mode == "Bionic Reading":
                        text = self._apply_bionic(text)
                    else:
                        text = self._escape_html(text)
                    paragraphs.append(f"<p>{text}</p>")

        body = "\n".join(paragraphs)
        column_width = self.settings.get_int("reading/column_width", 700)

        return f"""
        <div style="
            font-family: Georgia, serif;
            font-size: {font_size}pt;
            line-height: {line_spacing};
            color: {fg};
            background: {bg};
            max-width: {column_width}px;
            margin: 0 auto;
            padding: 20px 32px;
        ">
        {body}
        </div>
        """

    def _apply_bionic(self, text: str) -> str:
        """Bold the first half of each word for bionic reading."""
        def bionic_word(word: str) -> str:
            clean = re.sub(r'[^a-zA-Z]', '', word)
            n = max(1, len(clean) // 2)
            if n >= len(word):
                return f"<b>{self._escape_html(word)}</b>"
            return f"<b>{self._escape_html(word[:n])}</b>{self._escape_html(word[n:])}"

        words = text.split()
        return " ".join(bionic_word(w) for w in words)

    def _escape_html(self, text: str) -> str:
        return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>"))

    def _apply_text_view_style(self):
        theme = self.settings.get("appearance/theme", "light")
        bg = "#1e1e2e" if theme == "dark" else "#fefefe"
        self._text_view.setStyleSheet(f"background: {bg}; padding: 20px;")

    def _handle_ai_summarize(self, text: str):
        """Called when the AI summarize overlay button is clicked."""
        api_key = self.settings.get("ai/gemini_api_key", "")
        if not api_key:
            return
        if not text.strip():
            return

        from ai_highlighter import AISummarizeWorker
        self._ai_worker = AISummarizeWorker(api_key, text)
        self._ai_worker.finished.connect(self._page_label.show_ai_bubble)
        self._ai_worker.start()

    def mousePressEvent(self, event):
        # Check if click is on the AI Summarize button (painted in PageLabel)
        if (event.button() == Qt.MouseButton.LeftButton
                and self._page_label.isVisible()
                and self._page_label._selected_text.strip()
                and self._page_label._selection_rect):
            sr = self._page_label._selection_rect
            btn_rect = QRect(
                sr.right() - 110, sr.bottom() + 4, 110, 26
            )
            # Map click pos to page_label coords
            pos_in_label = self._page_label.mapFromGlobal(
                self.mapToGlobal(event.position().toPoint())
            )
            if btn_rect.contains(pos_in_label):
                selected = self._page_label._selected_text
                self._handle_ai_summarize(selected)
                return
        super().mousePressEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._resize_timer.start(150)
