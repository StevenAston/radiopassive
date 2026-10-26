"""Pure-function helper library for the Radiopassive pipeline (Phase 2, step 1).

Contract: docs/LIB_SPEC.md. Background: docs/METHODS.md §10–§11, docs/SCHEMA.md §3, §6.5.
"""

from __future__ import annotations


class LibError(ValueError):
    """Raised for any invalid input to a ``pipeline.lib`` function.

    The message always names the offending input.
    """


__all__ = ["LibError"]
