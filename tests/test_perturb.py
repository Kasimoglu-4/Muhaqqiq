from eval.perturb import (
    add_forward_spam,
    delete_middle_word,
    ocr_confusions,
    strip_tashkeel,
    truncate_words,
)


def test_strip_tashkeel():
    assert "َ" not in strip_tashkeel("إِنَّمَا")


def test_ocr_confusions_alef():
    assert "ا" in ocr_confusions("أحمد")


def test_truncate_words():
    assert truncate_words("a b c d e", 3) == "a b c"


def test_delete_middle_word():
    assert delete_middle_word("one two three four") == "one two four"


def test_spam_suffix():
    assert "انشرها" in add_forward_spam("نص")
