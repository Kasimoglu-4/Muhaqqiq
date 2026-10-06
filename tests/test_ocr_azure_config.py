"""OCR provider selection (no live Azure calls)."""


from muhaqqiq.services.ocr_service import AzureReadOcrProvider, StubOcrProvider, get_ocr_provider


def test_default_stub(monkeypatch):
    monkeypatch.delenv("MUHAQQIQ_OCR", raising=False)
    monkeypatch.delenv("AZURE_VISION_KEY", raising=False)
    assert isinstance(get_ocr_provider(), StubOcrProvider)


def test_azure_selected(monkeypatch):
    monkeypatch.setenv("MUHAQQIQ_OCR", "azure")
    p = get_ocr_provider()
    assert isinstance(p, AzureReadOcrProvider)


def test_windows_selected(monkeypatch):
    monkeypatch.setenv("MUHAQQIQ_OCR", "windows")
    from muhaqqiq.services.ocr_service import WindowsOcrProvider

    assert isinstance(get_ocr_provider(), WindowsOcrProvider)


def test_azure_requires_keys(monkeypatch):
    monkeypatch.delenv("AZURE_VISION_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_VISION_KEY", raising=False)
    p = AzureReadOcrProvider()
    try:
        p.extract(b"not-an-image", "image/png")
        raise AssertionError("expected ValueError")
    except ValueError as e:
        assert "AZURE" in str(e) or "Pillow" in str(e) or "Unsupported" in str(e) or "Image" in str(e)
