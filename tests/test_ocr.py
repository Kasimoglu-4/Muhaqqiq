import io

import pytest
from PIL import Image

from muhaqqiq.ocr import StubOcrProvider, preprocess_image
from muhaqqiq.services.ocr_service import _arabic_ocr_score, _clean_ocr_text, _tesseract_variants


def _png_bytes() -> bytes:
    im = Image.new("RGB", (64, 64), color=(20, 40, 30))
    buf = io.BytesIO()
    im.save(buf, format="PNG")
    return buf.getvalue()


def test_preprocess_png():
    out = preprocess_image(_png_bytes(), "image/png")
    assert out[:8] == b"\x89PNG\r\n\x1a\n"


def test_reject_huge():
    with pytest.raises(ValueError, match="5 MB"):
        preprocess_image(b"x" * (5 * 1024 * 1024 + 1), "image/png")


def test_stub_ocr():
    r = StubOcrProvider().extract(_png_bytes(), "image/png")
    assert r.provider == "stub"
    assert r.text == ""


def test_clean_ocr_keeps_arabic_lines():
    raw = "noise @@\nقال إنما الأعمال\nXYZ"
    assert "قال" in _clean_ocr_text(raw)
    assert "XYZ" not in _clean_ocr_text(raw)


def test_arabic_ocr_score_prefers_arabic():
    assert _arabic_ocr_score("قال إنما الله") > _arabic_ocr_score("hello world 123")


def test_tesseract_variants_yield_images():
    im = Image.new("RGB", (120, 80), color=(240, 240, 240))
    names = [n for n, _ in _tesseract_variants(im)]
    assert names
    assert any(n.startswith("pil_") or n.startswith("cv_") for n in names)
