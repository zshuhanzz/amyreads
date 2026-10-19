"""
AmyReads - Cache Manager
Stores AI highlights locally to avoid repeat API calls.
Uses a simple JSON file per PDF, keyed by page number.
"""

import os
import json
import hashlib
from typing import Optional, List, Dict


CACHE_DIR = os.path.join(
    os.environ.get("APPDATA", os.path.expanduser("~")),
    "AmyReads", "highlight_cache"
)

# Bump this to invalidate all caches when the prompt changes
CACHE_VERSION = "v2"


class CacheManager:
    def __init__(self):
        os.makedirs(CACHE_DIR, exist_ok=True)

    def _pdf_key(self, pdf_path: str) -> str:
        """Create a safe filename key for a PDF path."""
        abs_path = os.path.abspath(pdf_path)
        return hashlib.sha256(abs_path.encode("utf-8")).hexdigest()[:24]

    def _cache_file(self, pdf_path: str) -> str:
        return os.path.join(CACHE_DIR, f"{self._pdf_key(pdf_path)}.json")

    def _load(self, pdf_path: str) -> dict:
        path = self._cache_file(pdf_path)
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Invalidate if version mismatch
                if data.get("version") != CACHE_VERSION:
                    return {"version": CACHE_VERSION, "pages": {}}
                return data
            except (json.JSONDecodeError, IOError):
                pass
        return {"version": CACHE_VERSION, "pages": {}}

    def _save(self, pdf_path: str, data: dict):
        path = self._cache_file(pdf_path)
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except IOError:
            pass

    def get_highlights(self, pdf_path: str, page: int) -> Optional[List[Dict]]:
        """Return cached highlights for a page, or None if not cached."""
        data = self._load(pdf_path)
        pages = data.get("pages", {})
        return pages.get(str(page))

    def save_highlights(self, pdf_path: str, page: int, highlights: List[Dict]):
        """Save highlights for a page to cache."""
        data = self._load(pdf_path)
        if "pages" not in data:
            data["pages"] = {}
        data["pages"][str(page)] = highlights
        self._save(pdf_path, data)

    def clear_all(self):
        """Remove all cached highlight files."""
        for fname in os.listdir(CACHE_DIR):
            if fname.endswith(".json"):
                try:
                    os.remove(os.path.join(CACHE_DIR, fname))
                except OSError:
                    pass

    def clear_for_pdf(self, pdf_path: str):
        path = self._cache_file(pdf_path)
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass

    def cache_size_kb(self) -> int:
        """Return total cache size in KB."""
        total = 0
        for fname in os.listdir(CACHE_DIR):
            fp = os.path.join(CACHE_DIR, fname)
            if os.path.isfile(fp):
                total += os.path.getsize(fp)
        return total // 1024
