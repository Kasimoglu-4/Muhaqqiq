from muhaqqiq.decide import Candidate, decide


def test_undetermined_short():
    """Short non-exact inputs always abstain (even mid/high fuzzy scores)."""
    c = Candidate("hadith", 1, 95.0, False, "x", "x", {})
    assert decide(c, None, 2) == "UNDETERMINED"


def test_undetermined_short_close_band():
    """3-word vocab-overlap false positives must not become CLOSE."""
    c = Candidate("hadith", 1, 87.0, False, "x", "x", {})
    assert decide(c, None, 3) == "UNDETERMINED"


def test_supported_exact():
    c = Candidate("hadith", 1, 100.0, True, "x", "x", {})
    assert decide(c, 50.0, 5) == "SUPPORTED"


def test_known_claim_attributed():
    c = Candidate("known_claim", 1, 100.0, True, "x", "x", {}, True, {"grader": "أ"})
    assert decide(c, None, 5) == "ATTRIBUTED_RULING"


def test_close():
    c = Candidate("quran", 1, 80.0, False, "x", "x", {})
    assert decide(c, 70.0, 6) == "CLOSE_WITH_DIFF"


def test_short_but_strong_quote():
    c = Candidate("hadith", 1, 99.0, False, "x", "x", {})
    assert decide(c, 99.0, 3) == "SUPPORTED"


def test_single_token_high_score_undetermined():
    """One word like «خيركم» must not Support via substring score."""
    c = Candidate("hadith", 1, 100.0, False, "x", "x", {})
    assert decide(c, None, 1) == "UNDETERMINED"


def test_single_token_exact_supported():
    c = Candidate("hadith", 1, 100.0, True, "x", "x", {})
    assert decide(c, None, 1) == "SUPPORTED"


def test_quran_fuzzy_high_is_close_not_supported():
    """Tampered verse scoring above T_EXACT but below 99 is Close, not Supported."""
    c = Candidate("quran", 1, 95.65, False, "x", "x", {})
    assert decide(c, 90.0, 4) == "CLOSE_WITH_DIFF"
