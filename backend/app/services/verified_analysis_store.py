from collections import OrderedDict
from copy import deepcopy
from threading import Lock
from time import monotonic
from uuid import uuid4


TTL_SECONDS = 15 * 60
MAX_ENTRIES = 128

_store = OrderedDict()
_lock = Lock()


class CachedAnalysisNotFound(LookupError):
    """The requested verified analysis is unavailable."""


def store_verified_analysis(analysis: dict) -> str:
    """
    Store a verified analysis for temporary reuse.

    Results are held in memory for 15 minutes.
    """
    evaluation = analysis.get("evaluation") or {}

    if evaluation.get("status") != "passed":
        raise ValueError(
            "Only verified analysis results can be stored."
        )

    now = monotonic()

    with _lock:
        # Remove expired entries.
        for key, (expires_at, _) in list(_store.items()):
            if expires_at <= now:
                del _store[key]

        # Keep the store bounded.
        while len(_store) >= MAX_ENTRIES:
            _store.popitem(last=False)

        analysis_id = uuid4().hex

        _store[analysis_id] = (
            now + TTL_SECONDS,
            deepcopy(analysis),
        )

    return analysis_id


def get_verified_analysis(
    analysis_id: str,
    dataset_id: str,
    question: str,
) -> dict:
    """
    Retrieve the original verified analysis.

    Require the dataset and question to match.
    Return a copy to prevent accidental mutation.
    """
    with _lock:
        record = _store.get(analysis_id)

        if (
            record is None
            or record[0] <= monotonic()
        ):
            _store.pop(analysis_id, None)

            raise CachedAnalysisNotFound(
                "Analysis not found or expired. "
                "Please run the analysis again."
            )

        analysis = deepcopy(record[1])

    if (
        analysis.get("dataset_id") != dataset_id
        or analysis.get("question") != question
    ):
        raise ValueError(
            "The analysis ID does not match "
            "the requested dataset and question."
        )

    return analysis