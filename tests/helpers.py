# coding: utf-8

"""Shared bootstrap for the unittest suite.

``SEQUENCES_DB`` must be set before importing ``main`` because the database is
initialized at import time.
"""

import os
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

TEST_DB = os.path.join(
    tempfile.gettempdir(), "deciframe-tests-%s.db" % os.getpid()
)
os.environ["SEQUENCES_DB"] = TEST_DB

import main  # noqa: E402
import custom_sequences  # noqa: E402


def reset_db():
    """Recreate the test catalogue and clear the in-memory match cache."""
    for suffix in ("", "-wal", "-shm"):
        try:
            os.remove(main.DB_PATH + suffix)
        except OSError:
            pass
    custom_sequences.init_db(main.DB_PATH)
    main.MATCHING_INDEX.clear_cache()
    return main.app.test_client()
