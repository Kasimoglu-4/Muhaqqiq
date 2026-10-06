"""OCR provider interface and image preprocessing (production-ready providers).

Flow: preprocess → OCR → return editable text. Callers must never auto-verify
without user review of extracted_text.
"""

from __future__ import annotations

import io
import os
import time
from dataclasses import dataclass
from typing import Protocol

MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_EDGE = 1600
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}


@dataclass(frozen=True)
class OcrResult:
    text: str
    confidence: float
    provider: str


class OcrProvider(Protocol):
    name: str

    def extract(self, image_bytes: bytes, content_type: str) -> OcrResult: ...


def preprocess_image(image_bytes: bytes, content_type: str) -> bytes:
    """Strip EXIF, convert RGB, resize max edge. Raises ValueError on bad input."""
    if len(image_bytes) > MAX_IMAGE_BYTES:
        raise ValueError("Image exceeds 5 MB limit")
    ct = (content_type or "").split(";")[0].strip().lower()
    if ct and ct not in ALLOWED_TYPES:
        raise ValueError(f"Unsupported content type: {ct}")
    try:
        from PIL import Image, ImageOps
    except ImportError as e:
        raise ValueError("Pillow is required for OCR image preprocessing") from e

    with Image.open(io.BytesIO(image_bytes)) as im:
        im = ImageOps.exif_transpose(im)
        im = im.convert("RGB")
        w, h = im.size
        scale = min(1.0, MAX_EDGE / max(w, h))
        if scale < 1.0:
            im = im.resize((int(w * scale), int(h * scale)))
        out = io.BytesIO()
        im.save(out, format="PNG")
        return out.getvalue()


class StubOcrProvider:
    """Deterministic stub for tests / when no OCR engine is installed."""

    name = "stub"

    def extract(self, image_bytes: bytes, content_type: str) -> OcrResult:
        preprocess_image(image_bytes, content_type)
        return OcrResult(text="", confidence=0.0, provider=self.name)


def _windows_tesseract_exe() -> str | None:
    for candidate in (
        os.environ.get("TESSERACT_CMD", "").strip(),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ):
        if candidate and os.path.isfile(candidate):
            return candidate
    return None


def _tessdata_dir() -> str | None:
    """Directory containing *.traineddata (ara.traineddata required for Arabic)."""
    for key in ("MUHAQQIQ_TESSDATA", "TESSDATA_DIR"):
        raw = os.environ.get(key, "").strip()
        if raw and os.path.isdir(raw):
            return raw
    local_app = os.environ.get("LOCALAPPDATA", "")
    # Prefer tessdata_best when present (better on calligraphy / tashkeel).
    for name in ("tesseract-tessdata-best", "tesseract-tessdata"):
        local = os.path.join(local_app, name)
        if local and os.path.isfile(os.path.join(local, "ara.traineddata")):
            return local
    return None


def _configure_pytesseract(pytesseract) -> str:
    """Point pytesseract at the binary + tessdata; return config string for CLI."""
    exe = _windows_tesseract_exe()
    if exe:
        pytesseract.pytesseract.tesseract_cmd = exe
    tessdata = _tessdata_dir()
    if not tessdata:
        return ""
    # Do not quote the path — pytesseract forwards it literally and quotes break lookup.
    return f"--tessdata-dir {tessdata}"


def _arabic_ocr_score(text: str) -> float:
    """Prefer dense Arabic orthography over Latin/digit/fragment noise."""
    import re

    if not text:
        return -1.0
    # Letters only (ignore tashkeel noise in scoring density)
    letters = re.findall(r"[\u0621-\u064A]", text)
    ara = len(letters)
    if ara < 8:
        return -1.0
    words = [w for w in re.findall(r"[\u0621-\u064A]{2,}", text)]
    if len(words) < 3:
        return -1.0
    other = len(re.findall(r"[A-Za-z]", text))
    digits = len(re.findall(r"\d", text))
    # Penalize very short fragments (common calligraphy OCR junk)
    short = sum(1 for w in words if len(w) <= 2)
    stems = ("قال", "انما", "إنما", "الله", "الى", "إلى", "اشكو", "حزن", "تعلمون")
    bonus = sum(6.0 for s in stems if s in text)
    # Prefer longer contiguous Arabic (ayah-length)
    length_bonus = min(len(text), 80) * 0.15
    return (
        ara * 1.0
        + len(words) * 2.0
        + bonus
        + length_bonus
        - other * 3.0
        - digits * 1.5
        - short * 1.2
    )


def _clean_ocr_text(text: str) -> str:
    import re

    t = (text or "").replace("\u200e", "").replace("\u200f", "")
    lines: list[str] = []
    for line in t.splitlines():
        line = line.strip()
        if not line:
            continue
        ara = len(re.findall(r"[\u0600-\u06FF]", line))
        if ara >= 2 and ara >= max(1, len(line) // 4):
            lines.append(line)
    t = " ".join(lines) if lines else t
    t = re.sub(r"[^\u0600-\u06FF\s\d\(\)\[\]:：\-–]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _pil_from_gray_u8(arr):
    from PIL import Image

    return Image.fromarray(arr)


def _crop_ink_region(gray_u8, pad: int = 12):
    """Crop to dark-ink bounding box (drops large empty / graphic margins)."""
    import numpy as np

    # Ink is dark on light after invert/normalize.
    ink = gray_u8 < 200
    ys, xs = np.where(ink)
    if len(xs) < 80:
        return gray_u8
    y0, y1 = max(0, int(ys.min()) - pad), min(gray_u8.shape[0], int(ys.max()) + pad)
    x0, x1 = max(0, int(xs.min()) - pad), min(gray_u8.shape[1], int(xs.max()) + pad)
    # Reject tiny/noisy crops
    if (y1 - y0) < 40 or (x1 - x0) < 80:
        return gray_u8
    return gray_u8[y0:y1, x0:x1]


def _scale_for_tesseract(gray_u8, target_min_h: int = 900):
    import cv2

    h, w = gray_u8.shape[:2]
    if h >= target_min_h:
        return gray_u8
    scale = target_min_h / float(h)
    return cv2.resize(gray_u8, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_CUBIC)


def _add_border(gray_u8, px: int = 16):
    import cv2

    return cv2.copyMakeBorder(gray_u8, px, px, px, px, cv2.BORDER_CONSTANT, value=255)


def _tesseract_variants(rgb_im):
    """Yield research-backed preprocess variants for Arabic Tesseract.

    Sources: Tesseract ImproveQuality docs (invert, deskew, adaptive/Sauvola),
    Arabic OCR literature (Sauvola/adaptive binarization), RobustDocOCR-style
    CLAHE + adaptive Gaussian threshold + light denoise.
    """
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageStat

    try:
        import cv2
        import numpy as np
    except ImportError:
        # --- Pillow-only fallback ---
        gray = ImageOps.grayscale(rgb_im)
        mean = float(ImageStat.Stat(gray).mean[0])
        base = ImageOps.invert(gray) if mean < 110 else gray
        base = ImageOps.autocontrast(base)
        yield "pil_base", base
        yield "pil_contrast", ImageEnhance.Contrast(base).enhance(2.0)
        for thr in (110, 125, 140, 160):
            yield f"pil_bin{thr}", base.point(lambda p, t=thr: 255 if p > t else 0)
        yield "pil_dilate", base.point(lambda p: 255 if p > 125 else 0).filter(ImageFilter.MaxFilter(3))
        if max(base.size) < 1400:
            up = base.resize((base.width * 2, base.height * 2), Image.Resampling.LANCZOS)
            yield "pil_up", ImageOps.autocontrast(up)
            yield "pil_up_bin", up.point(lambda p: 255 if p > 125 else 0)
        return

    # --- OpenCV pipeline ---
    arr = np.array(rgb_im.convert("RGB"))
    g = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    if float(g.mean()) < 110:
        g = cv2.bitwise_not(g)

    # Watermark / textured-bg attenuation: subtract large blur, keep local ink.
    blur = cv2.GaussianBlur(g, (0, 0), sigmaX=25)
    flat = cv2.addWeighted(g, 1.6, blur, -0.6, 0)
    flat = cv2.normalize(flat, None, 0, 255, cv2.NORM_MINMAX)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    eq = clahe.apply(flat)
    den = cv2.fastNlMeansDenoising(eq, None, h=8, templateWindowSize=7, searchWindowSize=21)

    # Adaptive Gaussian (RobustDocOCR-style) — good under uneven lighting/watermarks
    adap = cv2.adaptiveThreshold(
        den, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 31, 12
    )
    # Tiny open to drop speckles without erasing Arabic dots/diacritics
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
    adap_clean = cv2.morphologyEx(adap, cv2.MORPH_OPEN, kernel, iterations=1)

    # Otsu as alternate binarization
    _, otsu = cv2.threshold(den, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    for name, img in (
        ("cv_clahe", eq),
        ("cv_adap", adap_clean),
        ("cv_otsu", otsu),
        ("cv_den", den),
    ):
        cropped = _crop_ink_region(img)
        scaled = _add_border(_scale_for_tesseract(cropped))
        yield name, _pil_from_gray_u8(scaled)
        # Also try uncropped (graphics-heavy posters sometimes crop wrong)
        yield f"{name}_full", _pil_from_gray_u8(_add_border(_scale_for_tesseract(img)))


class TesseractOcrProvider:
    """Optional Tesseract Arabic OCR (requires system tesseract + pytesseract)."""

    name = "tesseract"

    def extract(self, image_bytes: bytes, content_type: str) -> OcrResult:
        processed = preprocess_image(image_bytes, content_type)
        try:
            import pytesseract
            from PIL import Image
        except ImportError as e:
            raise ValueError("pytesseract/Pillow not installed for Tesseract OCR") from e

        base_cfg = _configure_pytesseract(pytesseract)
        best_text = ""
        best_score = -1.0

        with Image.open(io.BytesIO(processed)) as rgb:
            rgb = rgb.convert("RGB")
            # Prefer OpenCV-enhanced variants first (CLAHE / adaptive / watermark flatten)
            variants = list(_tesseract_variants(rgb))
            variants.sort(key=lambda x: (0 if x[0].startswith("cv_") else 1, x[0]))
            for name, variant in variants:
                thr_flags = ("",)
                if name.startswith("cv_"):
                    thr_flags = ("", "-c thresholding_method=1", "-c thresholding_method=2")
                for psm in ("6", "4"):
                    for thr in thr_flags:
                        cfg = f"{base_cfg} --oem 1 --psm {psm} {thr}".strip()
                        try:
                            raw = pytesseract.image_to_string(variant, lang="ara", config=cfg) or ""
                        except Exception:
                            continue
                        text = _clean_ocr_text(raw)
                        score = _arabic_ocr_score(text)
                        if score > best_score:
                            best_score = score
                            best_text = text
                # Only early-exit on strong, long Arabic (not stem-spam junk)
                if best_score >= 90 and len(best_text) >= 35:
                    break

        conf = 0.0
        if best_text:
            conf = 0.55 if best_score < 40 else 0.75 if best_score < 80 else 0.85
        return OcrResult(text=best_text, confidence=conf, provider=self.name)


def _windows_ocr_from_png_bytes(png_bytes: bytes) -> str:
    """Run winocr in an isolated thread/event loop (safe under FastAPI)."""
    import asyncio

    import winocr
    from PIL import Image, ImageOps, ImageStat

    async def _recognize(pil_im) -> str:
        result = await winocr.recognize_pil(pil_im, "ar")
        lines_out: list[str] = []
        lines = list(result.lines) if getattr(result, "lines", None) else []
        if lines:
            for line in lines:
                words = list(line.words) if line.words else []
                if not words:
                    t = (line.text or "").strip()
                    if t:
                        lines_out.append(t)
                    continue
                # WinOCR returns Arabic words left-to-right; restore RTL reading order.
                ordered = sorted(words, key=lambda w: w.bounding_rect.x, reverse=True)
                lines_out.append(" ".join(w.text for w in ordered if w.text))
        else:
            lines_out.append((result.text or "").strip())
        return _clean_ocr_text(" ".join(lines_out))

    async def _run() -> str:
        with Image.open(io.BytesIO(png_bytes)) as im:
            im = im.convert("RGB")
            candidates = [im]
            gray = ImageOps.grayscale(im)
            if float(ImageStat.Stat(gray).mean[0]) < 110:
                candidates.append(ImageOps.invert(gray).convert("RGB"))
            best = ""
            best_score = -1.0
            for cand in candidates:
                text = await _recognize(cand)
                score = _arabic_ocr_score(text)
                if score > best_score:
                    best_score = score
                    best = text
            return best

    return asyncio.run(_run())


class WindowsOcrProvider:
    """Windows.Media.Ocr via winocr — strong on posters/calligraphy (Windows only)."""

    name = "windows"

    def extract(self, image_bytes: bytes, content_type: str) -> OcrResult:
        processed = preprocess_image(image_bytes, content_type)
        try:
            import winocr  # noqa: F401
        except ImportError as e:
            raise ValueError("winocr not installed for Windows OCR") from e

        # Call via asyncio.to_thread from the API layer when inside ASGI.
        # Direct asyncio.run is fine in a plain worker thread (no running loop).
        text = _windows_ocr_from_png_bytes(processed)
        conf = 0.8 if text else 0.0
        return OcrResult(text=text, confidence=conf, provider=self.name)


class AzureReadOcrProvider:
    """Azure AI Vision Read API (production default when keys are set).

    Env:
      AZURE_VISION_ENDPOINT — e.g. https://<resource>.cognitiveservices.azure.com
      AZURE_VISION_KEY — subscription key
    """

    name = "azure_read"

    def extract(self, image_bytes: bytes, content_type: str) -> OcrResult:
        endpoint = os.environ.get("AZURE_VISION_ENDPOINT", "").rstrip("/")
        key = os.environ.get("AZURE_VISION_KEY", "").strip()
        if not endpoint or not key:
            raise ValueError("AZURE_VISION_ENDPOINT and AZURE_VISION_KEY required for azure OCR")
        processed = preprocess_image(image_bytes, content_type)

        import httpx

        analyze = f"{endpoint}/vision/v3.2/read/analyze"
        headers = {"Ocp-Apim-Subscription-Key": key, "Content-Type": "application/octet-stream"}
        with httpx.Client(timeout=60.0) as client:
            r = client.post(analyze, content=processed, headers=headers)
            r.raise_for_status()
            op_url = r.headers.get("Operation-Location")
            if not op_url:
                raise ValueError("Azure Read: missing Operation-Location")
            for _ in range(40):
                time.sleep(0.5)
                poll = client.get(op_url, headers={"Ocp-Apim-Subscription-Key": key})
                poll.raise_for_status()
                body = poll.json()
                status = (body.get("status") or "").lower()
                if status == "succeeded":
                    lines: list[str] = []
                    for ar in body.get("analyzeResult", {}).get("readResults", []):
                        for line in ar.get("lines", []):
                            t = (line.get("text") or "").strip()
                            if t:
                                lines.append(t)
                    text = "\n".join(lines).strip()
                    return OcrResult(text=text, confidence=0.85 if text else 0.0, provider=self.name)
                if status == "failed":
                    raise ValueError("Azure Read analysis failed")
        raise ValueError("Azure Read timed out")


_DAILY_SPEND = {"count": 0, "day": ""}


def _check_spend_cap() -> None:
    import datetime as dt

    day = dt.datetime.now(dt.UTC).date().isoformat()
    if _DAILY_SPEND["day"] != day:
        _DAILY_SPEND["day"] = day
        _DAILY_SPEND["count"] = 0
    cap = int(os.environ.get("MUHAQQIQ_OCR_DAILY_CAP", "500"))
    if _DAILY_SPEND["count"] >= cap:
        raise ValueError("Daily OCR spend cap reached; try again tomorrow")
    _DAILY_SPEND["count"] += 1


def _windows_ocr_available() -> bool:
    if os.name != "nt":
        return False
    try:
        import winocr  # noqa: F401
    except ImportError:
        return False
    return True


def get_ocr_provider() -> OcrProvider:
    choice = os.environ.get("MUHAQQIQ_OCR", "stub").strip().lower()
    if choice in {"azure", "azure_read"}:
        return AzureReadOcrProvider()
    if choice in {"windows", "winocr"}:
        return WindowsOcrProvider()
    if choice == "tesseract":
        # On Windows, Media.Ocr beats Tesseract on calligraphy / glow posters.
        if _windows_ocr_available():
            return WindowsOcrProvider()
        return TesseractOcrProvider()
    # Auto-select best available provider
    if choice == "auto":
        if os.environ.get("AZURE_VISION_KEY") and os.environ.get("AZURE_VISION_ENDPOINT"):
            return AzureReadOcrProvider()
        if _windows_ocr_available():
            return WindowsOcrProvider()
        return StubOcrProvider()
    return StubOcrProvider()


def ocr_spend_snapshot() -> dict[str, object]:
    import datetime as dt

    day = dt.datetime.now(dt.UTC).date().isoformat()
    if _DAILY_SPEND["day"] != day:
        return {"day": day, "count": 0, "cap": int(os.environ.get("MUHAQQIQ_OCR_DAILY_CAP", "500"))}
    return {
        "day": _DAILY_SPEND["day"],
        "count": _DAILY_SPEND["count"],
        "cap": int(os.environ.get("MUHAQQIQ_OCR_DAILY_CAP", "500")),
    }


def run_ocr(image_bytes: bytes, content_type: str) -> OcrResult:
    """Extract text for user review — never auto-verify."""
    _check_spend_cap()
    return get_ocr_provider().extract(image_bytes, content_type)
