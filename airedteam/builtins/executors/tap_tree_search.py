from __future__ import annotations

from airedteam.builtins.executors.pair import PAIRExecutor


class TAPTreeSearchExecutor(PAIRExecutor):
    """TAP-style tree-search attack executor backed by the PAIR loop."""

    name = "tap_tree_search"
