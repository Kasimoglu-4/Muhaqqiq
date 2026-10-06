from muhaqqiq.segment import segment


def test_single_claim():
    spans = segment("إنما الأعمال بالنيات")
    assert len(spans) == 1
    assert "اعمال" in spans[0].text or "الأعمال" in spans[0].text or "بالنيات" in spans[0].text


def test_strips_forward_spam():
    spans = segment("إنما الأعمال بالنيات انشرها ولا تبخل")
    assert len(spans) >= 1
    joined = " ".join(s.text for s in spans)
    assert "انشرها" not in joined


def test_hadith_tag():
    spans = segment('قال رسول الله صلى الله عليه وسلم: "إنما الأعمال بالنيات"')
    assert any(s.claim_type == "hadith" for s in spans)


def test_verse_tag():
    spans = segment("﴿قل هو الله أحد﴾")
    assert any(s.claim_type == "verse" for s in spans)


def test_multiline_splits():
    text = "قل هو الله احد\nاطلبوا العلم ولو في الصين"
    spans = segment(text)
    assert len(spans) >= 2
