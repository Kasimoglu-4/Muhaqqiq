from muhaqqiq.normalize import normalize, word_count


def test_tashkeel_stripped():
    a = normalize("إِنَّمَا الْأَعْمَالُ بِالنِّيَّاتِ")
    b = normalize("إنما الأعمال بالنيات")
    assert a == b


def test_alef_variants():
    assert normalize("أحمد") == normalize("احمد")


def test_ya_alef_maqsura():
    assert normalize("على") == normalize("علي")


def test_honorific_removed():
    assert "صلى" not in normalize("قال رسول الله صلى الله عليه وسلم إنما الأعمال بالنيات")


def test_url_and_emoji_removed():
    n = normalize("نص https://x.com/a 😀 هنا")
    assert "http" not in n
    assert "😀" not in n


def test_word_count():
    assert word_count(normalize("إنما الأعمال بالنيات")) >= 3


def test_superscript_alef_becomes_alef():
    # Quran orthography: العَٰلَمِينَ should match typed العالمين
    assert normalize("العَٰلَمِينَ") == normalize("العالمين")


def test_rahman_spelling_folded():
    assert normalize("الرحمن") == normalize("الرحمان")


def test_hamza_removed_for_quran_match():
    assert normalize("القرآن") == normalize("القرءان")


def test_quranic_trailing_waw_alef():
    # Tanzil: أشكوا / قالوا — users often type أشكو / قالو
    assert normalize("أشكوا بثي") == normalize("أشكو بثي")
    assert normalize("قالوا") == normalize("قالو")
