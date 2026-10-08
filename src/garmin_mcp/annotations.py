"""MCP tool annotations for every Garmin tool, derived from the tool's verb.

Tools are named ``<verb>_<object>`` (``get_sleep_data``, ``delete_workout``), and
the verb says what the tool does to the account:

- ``get``/``search``/``count``/``download``: read only.
- ``add``/``create``/``log``/``schedule``/``upload``/``upsert``: add data; repeating
  a call adds it again (not idempotent).
- ``set``/``update``: overwrite existing values (destructive, idempotent).
- ``delete``/``remove``/``unschedule``: remove data (destructive, idempotent).

``OVERRIDES`` covers the tools that don't follow their verb. Every tool talks to
Garmin Connect (open world) except purely local settings. A tool whose verb has
no rule gets the most cautious annotations, and a unit test fails so the new
verb gets classified.
"""

from __future__ import annotations

from mcp.types import ToolAnnotations

READ_VERBS = {"get", "search", "count", "download"}
ADDITIVE_VERBS = {"add", "create", "log", "schedule", "upload", "upsert"}
OVERWRITE_VERBS = {"set", "update"}
REMOVE_VERBS = {"delete", "remove", "unschedule"}

# (readOnly, destructive, idempotent, openWorld)
_READ = (True, False, True, True)
_ADDITIVE = (False, False, False, True)
_OVERWRITE = (False, True, True, True)
_REMOVE = (False, True, True, True)
_CAUTIOUS = (False, True, False, True)

OVERRIDES: dict[str, tuple[bool, bool, bool, bool]] = {
    # Save files on the server's disk (same file each time), besides reading Garmin.
    "download_activity_file": (False, False, True, True),
    "download_course_gpx": (False, False, True, True),
    # Local setting only; never reaches Garmin.
    "set_fit_download_dir": (False, False, True, False),
    # Asks Garmin to reprocess a day's data; repeating it changes nothing more.
    "request_reload": (False, False, True, True),
    # Linking the same gear again is a no-op.
    "add_gear_to_activity": (False, False, True, True),
}

_ACRONYMS = {"hrv": "HRV", "rhr": "RHR", "spo2": "SpO2", "vo2max": "VO2 max", "gpx": "GPX",
             "fit": "FIT", "z2": "Z2", "id": "ID", "ids": "IDs"}


def classify(name: str) -> tuple[bool, bool, bool, bool] | None:
    """(readOnly, destructive, idempotent, openWorld), or None if no rule matches."""
    if name in OVERRIDES:
        return OVERRIDES[name]
    verb = name.split("_", 1)[0]
    for verbs, hints in ((READ_VERBS, _READ), (ADDITIVE_VERBS, _ADDITIVE),
                         (OVERWRITE_VERBS, _OVERWRITE), (REMOVE_VERBS, _REMOVE)):
        if verb in verbs:
            return hints
    return None


def title_for(name: str) -> str:
    """'get_hrv_data' -> 'Get HRV data'."""
    words = [_ACRONYMS.get(w, w) for w in name.split("_")]
    return " ".join([words[0].capitalize(), *words[1:]])


def annotations_for(name: str) -> ToolAnnotations:
    read_only, destructive, idempotent, open_world = classify(name) or _CAUTIOUS
    return ToolAnnotations(
        title=title_for(name),
        readOnlyHint=read_only,
        destructiveHint=destructive,
        idempotentHint=idempotent,
        openWorldHint=open_world,
    )
