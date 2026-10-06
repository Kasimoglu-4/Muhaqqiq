"""Compatibility shim — prefer muhaqqiq.services.match_service."""

from muhaqqiq.services import match_service as _ms
from muhaqqiq.services.match_service import match  # noqa: F401

# Used by calibrate / debug scripts (star-import skips leading underscore names)
_match_one = _ms._match_one
_score = _ms._score
_STATUS_RANK = _ms._STATUS_RANK
decide = _ms.decide
MIN_FUZZY_CANDIDATE_CHARS = _ms.MIN_FUZZY_CANDIDATE_CHARS
MIN_CONTAINMENT_QUERY_CHARS = _ms.MIN_CONTAINMENT_QUERY_CHARS
