# AmyReads

A lightweight, AI-powered PDF reader designed to make textbooks easier to read.

> **Make reading easier for Amy. Fuck PBL!**

---

## Features

- **5 Reading Modes** — Original, High Contrast, Line Focus, Bionic Reading, Clean Text
- **AI Highlighting** — Gemini 2.5 Flash identifies key concepts, definitions, facts, and examples
- **AI Summarize** — Select any text passage to get an instant AI summary bubble
- **Fast PDF Rendering** — Page-by-page rendering via PyMuPDF (no lag on large textbooks)
- **Customizable** — Font size, line spacing, contrast, column width, ruler height
- **Offline-first** — All reading modes work without internet; only AI features need a connection
- **Highlight Cache** — AI results are cached locally so you never pay twice for the same page
- **Last Page Memory** — Re-opens each PDF at the page you left off
- **Portable EXE** — Ships as a single `.exe` with no Python installation required

---

## Quick Start

### Running from Source

1. **Install Python 3.10+** from [python.org](https://www.python.org/)

2. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```

3. **Run AmyReads:**
   ```
   python main.py
   ```

### Building the Windows EXE

Run the provided build script on Windows:

```
build.bat
```

This installs all dependencies (including PyInstaller) and produces `dist\AmyReads.exe`.

The `.exe` is self-contained — no Python or other software needed.

---

## Reading Modes

| Mode | Description |
|------|-------------|
| **Original** | Normal PDF rendering — preserves diagrams, equations, formatting |
| **High Contrast** | Improves text visibility; inverts colours in dark theme |
| **Line Focus** | Dims the page except for the line under your cursor |
| **Bionic Reading** | Bolds the first half of every word for faster visual tracking |
| **Clean Text** | Extracts plain text into a distraction-free reading layout |

---

## AI Highlighting

### Setup

1. Open **Settings → AI**
2. Paste your [Gemini API key](https://aistudio.google.com/app/apikey) (free)
3. Click **Test API Key** to verify
4. Click **✦ AI Highlight** in the reader toolbar

### Colour Legend

| Colour | Meaning |
|--------|---------|
| 🔵 Blue | Key concepts |
| 🟢 Green | Definitions |
| 🟡 Yellow | Important facts & formulas |
| 🟣 Purple | Examples |

### AI Summarize

1. Click and drag to select any text on the page
2. An **✦ AI Summarize** button appears below the selection
3. Click it to see a concise summary bubble

### Notes

- AI features require an internet connection
- Only the **current page** is sent to the API (never the full textbook)
- Results are cached locally — subsequent views of the same page are instant
- Rate limit and invalid key errors are reported clearly

---

## Settings

Open **Settings** from the home screen or the `⚙` button in the reader.

| Setting | Description |
|---------|-------------|
| Theme | Light or Dark |
| Font size | Text size in Clean Text / Bionic modes |
| Line spacing | Line height multiplier |
| Column width | Max text column width in Clean Text / Bionic modes |
| Contrast | Opacity of contrast overlay (High Contrast mode) |
| Default mode | Starting reading mode when a PDF is opened |
| Ruler height | Height of the Line Focus highlight strip |
| Remember last page | Re-open PDFs at the last viewed page |
| Gemini API key | Your personal API key |
| Clear cache | Remove all cached AI highlights |

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `←` / `→` | Previous / Next page |
| `Ctrl +` | Zoom in |
| `Ctrl -` | Zoom out |
| `Ctrl 0` | Fit to width |

---

## Requirements

- **Python 3.10+**
- **PySide6** ≥ 6.6.0
- **PyMuPDF** ≥ 1.23.0

Optional:
- **Gemini API key** (free at [aistudio.google.com](https://aistudio.google.com/app/apikey))

---

## File Structure

```
AmyReads/
├── main.py               # Entry point, theme management
├── home_screen.py        # Welcome screen
├── reader_window.py      # Main reader window + toolbar
├── pdf_viewer.py         # PDF rendering, overlays, modes
├── reading_modes.py      # Mode constants
├── ai_highlighter.py     # Gemini API + background workers
├── cache_manager.py      # Local highlight cache
├── settings_manager.py   # QSettings wrapper
├── settings_dialog.py    # Settings UI
├── requirements.txt
├── build.bat             # Windows EXE builder
└── README.md
```

---

## Known Limitations

- **Bionic Reading** and **Clean Text** modes work on text-based PDFs only. Scanned image PDFs without embedded text will show empty output in these modes.
- **AI Highlighting** matches phrases by exact text search — it skips phrases it cannot reliably locate in the rendered page.
- The compiled `.exe` is larger than the source (~150–300 MB) due to Qt and PyMuPDF being bundled.

---

## Privacy

- No accounts, no cloud sync, no telemetry.
- Your PDF files never leave your machine (except when you explicitly click AI Highlight, which sends the **current page's text** to Google's Gemini API).
- The original PDF is never modified.
