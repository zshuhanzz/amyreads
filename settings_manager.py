"""
Settings Manager - Persistent application settings using QSettings
"""

from PySide6.QtCore import QSettings


class SettingsManager:
    """Thin wrapper around QSettings for easy key/default access."""

    def __init__(self):
        self._settings = QSettings("AmyReads", "AmyReads")

    def get(self, key: str, default=None):
        return self._settings.value(key, default)

    def set(self, key: str, value):
        self._settings.setValue(key, value)
        self._settings.sync()

    def get_bool(self, key: str, default: bool = False) -> bool:
        val = self._settings.value(key, default)
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.lower() in ("true", "1", "yes")
        return bool(val)

    def get_int(self, key: str, default: int = 0) -> int:
        try:
            return int(self._settings.value(key, default))
        except (TypeError, ValueError):
            return default

    def get_float(self, key: str, default: float = 1.0) -> float:
        try:
            return float(self._settings.value(key, default))
        except (TypeError, ValueError):
            return default

    def remove(self, key: str):
        self._settings.remove(key)
        self._settings.sync()
