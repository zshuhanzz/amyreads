"""
AmyReads - AI Highlighter
Sends page text to Gemini 2.5 Flash and returns structured highlights.
"""

import json
import re
from typing import List, Dict, Optional

from PySide6.QtCore import QThread, Signal


# ─── Prompt template ─────────────────────────────────────────────────────────

HIGHLIGHT_PROMPT = """You are a study assistant helping a student highlight a textbook page.

Your task: identify the most important phrases to highlight.

CRITICAL RULES:
- "text" must be COPIED VERBATIM from the source text below — character for character
- Do NOT paraphrase, reword, or summarise
- Keep phrases SHORT: 2–6 words maximum
- Avoid phrases that span line breaks or contain newlines
- Be selective: return 8–15 highlights total
- Skip anything you're not 100% sure matches exactly

Categories:
- "key_concept" — the main topic/concept being introduced (highlight blue)
- "definition"  — text that defines or explains a term (highlight green)
- "fact"        — an important fact, number, formula, or rule (highlight yellow)
- "example"     — an example or case study (highlight purple)

Return ONLY a JSON array. No markdown. No explanation. No code fences.

Example format:
[
  {{"text": "exact phrase here", "type": "key_concept"}},
  {{"text": "another exact phrase", "type": "definition"}}
]

Source text:
---
{page_text}
---

JSON array:"""

SUMMARIZE_PROMPT = """Summarize the following text in 2-3 concise sentences. Focus on the key point.

Text: {text}

Summary:"""


# ─── Worker threads ──────────────────────────────────────────────────────────

class AIWorker(QThread):
    """Background thread for AI page highlighting."""
    finished = Signal(list)
    error = Signal(str)

    def __init__(self, api_key: str, page_text: str):
        super().__init__()
        self.api_key = api_key
        self.page_text = page_text

    def run(self):
        try:
            highlights = call_gemini_highlight(self.api_key, self.page_text)
            self.finished.emit(highlights)
        except Exception as e:
            self.error.emit(str(e))


class AISummarizeWorker(QThread):
    """Background thread for AI text summarization."""
    finished = Signal(str)
    error = Signal(str)

    def __init__(self, api_key: str, text: str):
        super().__init__()
        self.api_key = api_key
        self.text = text

    def run(self):
        try:
            summary = call_gemini_summarize(self.api_key, self.text)
            self.finished.emit(summary)
        except Exception as e:
            self.error.emit(f"AI error: {e}")


# ─── Gemini API calls ─────────────────────────────────────────────────────────

def _gemini_generate(api_key: str, prompt: str, model: str = "gemini-2.5-flash") -> str:
    """Call Gemini generateContent REST API and return the text response."""
    import urllib.request
    import urllib.error

    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={api_key}"
    )
    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 1024,
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            err = json.loads(body)
            msg = err.get("error", {}).get("message", body)
        except Exception:
            msg = body
        raise RuntimeError(f"Gemini API error {e.code}: {msg}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Network error: {e.reason}")

    # Extract text from response
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError) as e:
        raise RuntimeError(f"Unexpected Gemini response format: {data}")


def call_gemini_highlight(api_key: str, page_text: str) -> List[Dict]:
    """Call Gemini and parse highlight JSON response."""
    # Truncate very long pages
    truncated = page_text[:6000] if len(page_text) > 6000 else page_text
    prompt = HIGHLIGHT_PROMPT.format(page_text=truncated)
    raw = _gemini_generate(api_key, prompt)

    # Extract JSON array from response
    raw = raw.strip()
    # Strip markdown code blocks if present
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)
    raw = raw.strip()

    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Try to find array in response
        match = re.search(r'\[.*\]', raw, re.DOTALL)
        if match:
            data = json.loads(match.group(0))
        else:
            raise RuntimeError(f"Could not parse AI response as JSON: {raw[:200]}")

    if not isinstance(data, list):
        raise RuntimeError("AI response was not a JSON array.")

    # Validate and filter
    valid = []
    valid_types = {"key_concept", "definition", "fact", "example"}
    page_text_lower = page_text.lower()
    for item in data:
        if not isinstance(item, dict):
            continue
        text = item.get("text", "").strip()
        htype = item.get("type", "fact")
        if not text or len(text) < 3:
            continue
        if htype not in valid_types:
            htype = "fact"
        # Verify the phrase exists in the source (case-insensitive)
        if text.lower() in page_text_lower:
            valid.append({"text": text, "type": htype})

    return valid


def call_gemini_summarize(api_key: str, text: str) -> str:
    """Call Gemini to summarize selected text."""
    truncated = text[:3000] if len(text) > 3000 else text
    prompt = SUMMARIZE_PROMPT.format(text=truncated)
    result = _gemini_generate(api_key, prompt)
    return result.strip()


def test_api_key(api_key: str) -> tuple[bool, str]:
    """Test if an API key is valid. Returns (success, message)."""
    try:
        result = _gemini_generate(api_key, "Say 'OK' in one word.")
        if result:
            return True, "API key is valid. ✓"
        return False, "Empty response from Gemini."
    except RuntimeError as e:
        msg = str(e)
        if "API_KEY_INVALID" in msg or "400" in msg:
            return False, "Invalid API key. Please check and try again."
        if "quota" in msg.lower() or "429" in msg:
            return False, "Rate limit exceeded. Try again later."
        if "Network error" in msg:
            return False, "No internet connection. AI features require internet."
        return False, f"Error: {msg}"
    except Exception as e:
        return False, f"Unexpected error: {e}"
